"""SPI SD block driver derived from the repository HIL driver."""

try:
    from .pico_clock import SystemClock
except ImportError:
    from pico_clock import SystemClock

class SDCard:
    CMD0_PRE_DUMMY = True  # Diagnostic override; normal behavior retained.
    CMD_TIMEOUT = 100
    R1_IDLE_STATE = 1
    R1_ILLEGAL_COMMAND = 4
    TOKEN_CMD25 = 0xfc
    TOKEN_STOP_TRAN = 0xfd
    TOKEN_DATA = 0xfe

    def __init__(self, spi, cs, baudrate=100000, clock=None):
        self.spi = spi
        self.clock = clock or SystemClock()
        self.cs = cs
        self.cmdbuf = bytearray(6)
        self.dummybuf = bytearray(512)
        self.tokenbuf = bytearray(1)
        self.cs.init(self.cs.OUT, value=1)
        self.init_spi(baudrate)
        for _ in range(16):
            self.spi.write(b"\xff")
        r = self.cmd(0, 0, 0x95)
        if r != self.R1_IDLE_STATE:
            raise OSError("CMD0 failed: {}".format(r))
        r = self.cmd(8, 0x01AA, 0x87, 4)
        if r == self.R1_IDLE_STATE:
            if bytes(self.last_extra[2:]) != b'\x01\xaa':
                raise OSError('CMD8 echo mismatch')
            self.init_card_v2()
        elif r == (self.R1_IDLE_STATE | self.R1_ILLEGAL_COMMAND):
            self.init_card_v1()
        else:
            raise OSError("unsupported SD card")
        if self.cmd(16, 512, 0x15) != 0:
            raise OSError("CMD16 failed")
        if self.cmd(9, 0, 0, release=False) != 0:
            raise OSError("CSD request failed")
        csd = bytearray(16)
        self.readinto(csd)
        self.sectors = self.capacity_sectors(csd)
        self.init_spi(25000000)

    @staticmethod
    def capacity_sectors(csd):
        version = csd[0] >> 6
        if version == 1:
            size = ((csd[7] & 63) << 16) | (csd[8] << 8) | csd[9]
            return (size + 1) * 1024
        if version == 0:
            size = ((csd[6] & 3) << 10) | (csd[7] << 2) | (csd[8] >> 6)
            mult = ((csd[9] & 3) << 1) | (csd[10] >> 7)
            return ((size + 1) * (1 << (mult + 2)) * (1 << (csd[5] & 15))) // 512
        raise OSError("unsupported CSD")

    def init_spi(self, baudrate):
        self.spi.init(baudrate=baudrate, phase=0, polarity=0)

    def init_card_v1(self):
        for _ in range(self.CMD_TIMEOUT):
            self.clock.sleep_ms(50)
            self.cmd(55, 0, 0)
            if self.cmd(41, 0, 0) == 0:
                self.cdv = 512
                return
        raise OSError("timeout waiting for v1 card")

    def init_card_v2(self):
        for _ in range(self.CMD_TIMEOUT):
            self.clock.sleep_ms(50)
            self.cmd(58, 0, 0, 4)
            self.cmd(55, 0, 0)
            if self.cmd(41, 0x40000000, 0) == 0:
                if self.cmd(58, 0, 0, 4) != 0:
                    raise OSError("OCR read failed")
                self.cdv = 1 if self.last_extra[0] & 0x40 else 512
                return
        raise OSError("timeout waiting for v2 card")

    def cmd(self, cmd, arg, crc, final=0, release=True, skip1=False):
        self.cs(0)
        self.cmdbuf[0] = 0x40 | cmd
        self.cmdbuf[1] = (arg >> 24) & 0xff
        self.cmdbuf[2] = (arg >> 16) & 0xff
        self.cmdbuf[3] = (arg >> 8) & 0xff
        self.cmdbuf[4] = arg & 0xff
        self.cmdbuf[5] = crc
        if cmd != 0 or self.CMD0_PRE_DUMMY:
            self.spi.write(b"\xff")
        self.spi.write(self.cmdbuf)
        if skip1:
            self.spi.readinto(self.tokenbuf, 0xff)
        for _ in range(self.CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xff)
            response = self.tokenbuf[0]
            if not (response & 0x80):
                self.last_extra = bytearray()
                for _ in range(final):
                    self.spi.readinto(self.tokenbuf, 0xff)
                    self.last_extra.append(self.tokenbuf[0])
                if release:
                    self.cs(1)
                    self.spi.write(b"\xff")
                return response
        self.cs(1)
        self.spi.write(b"\xff")
        return -1

    def readinto(self, buf):
        self.cs(0)
        deadline = self.clock.ticks_ms() + 1000
        while self.clock.ticks_ms() < deadline:
            self.spi.readinto(self.tokenbuf, 0xff)
            if self.tokenbuf[0] == self.TOKEN_DATA:
                break
            self.clock.sleep_ms(1)
        else:
            self.cs(1)
            raise OSError("timeout waiting for data token")
        self.spi.readinto(buf, 0xff)
        self.spi.write(b"\xff\xff")
        self.cs(1)
        self.spi.write(b"\xff")

    def write(self, token, buf):
        self.cs(0)
        self.spi.write(bytes([token]))
        self.spi.write(buf)
        self.spi.write(b"\xff\xff")
        if (self.spi.read(1, 0xff)[0] & 0x1f) != 0x05:
            self.cs(1)
            raise OSError("write rejected")
        deadline = self.clock.ticks_ms() + 1000
        while self.spi.read(1, 0xff)[0] == 0:
            if self.clock.ticks_ms() >= deadline:
                self.cs(1)
                raise OSError("SD write busy timeout")
            self.clock.sleep_ms(1)
        self.cs(1)
        self.spi.write(b"\xff")

    def readblocks(self, block_num, buf):
        nblocks = len(buf) // 512
        assert nblocks and not len(buf) % 512
        for index in range(nblocks):
            if self.cmd(17, (block_num + index) * self.cdv, 0, release=False) != 0:
                raise OSError("read failed")
            self.readinto(memoryview(buf)[index * 512:(index + 1) * 512])

    def writeblocks(self, block_num, buf):
        nblocks = len(buf) // 512
        assert nblocks and not len(buf) % 512
        for index in range(nblocks):
            if self.cmd(24, (block_num + index) * self.cdv, 0) != 0:
                raise OSError("write setup failed")
            self.write(self.TOKEN_DATA, memoryview(buf)[index * 512:(index + 1) * 512])

    def ioctl(self, op, arg):
        if op == 1:  # initialize (constructor already completed it)
            return 0
        if op == 2:  # deinitialize
            self.cs(1)
            self.spi.deinit()
            return 0
        if op == 3:  # sync: each write waits for card ready
            return 0
        if op == 4:
            return self.sectors
        if op == 5:
            return 512
        return None

    @staticmethod
    def _r1_bit_names(r1):
        """Analyze R1 response byte and return list of set bit names."""
        bits = {
            0: "In Idle State",
            1: "Erase Reset",
            2: "Illegal Command",
            3: "Command CRC Error",
            4: "Erase Sequence Error",
            5: "Address Error",
            6: "Parameter Error",
            7: "Reserved",
        }
        names = []
        for bit_pos in range(8):
            if r1 & (1 << bit_pos):
                names.append(bits.get(bit_pos, "Unknown"))
        return names

    def diagnose_cmd0_multi(self, attempts=10, delay_ms=10):
        """Execute multiple CMD0 attempts and log R1 responses with bit analysis.

        Args:
            attempts: Number of CMD0 attempts
            delay_ms: Delay between attempts in milliseconds

        Returns:
            List of tuples: (attempt, r1_hex, r1_dec, bits_set, is_valid)
            where is_valid = (r1_hex == 0x01)
        """
        if not isinstance(attempts, int) or not 1 <= attempts <= 20:
            raise ValueError('attempts must be 1..20')
        if not isinstance(delay_ms, int) or not 0 <= delay_ms <= 1000:
            raise ValueError('delay_ms must be 0..1000')
        # Diagnostic only: caller must ensure no mounted filesystem uses this card.
        results = []
        for attempt in range(1, attempts + 1):
            if attempt > 1:
                self.clock.sleep_ms(delay_ms)
            r = self.cmd(0, 0, 0x95)
            r1_hex = "0x{:02x}".format(r) if r >= 0 else "TIMEOUT"
            r1_dec = r if r >= 0 else -1
            bit_names = self._r1_bit_names(r) if r >= 0 else []
            is_valid = (r == self.R1_IDLE_STATE)
            results.append((attempt, r1_hex, r1_dec, bit_names, is_valid))
        return results
