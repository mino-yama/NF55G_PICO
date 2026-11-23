# QR HOST診断レコードから、現試行の最初の完成QRを固定する。
# 照会済み取得IDの明示SSだけに渡し、次のQRで確認済み値を置き換えない。
import binascii
import struct

try:
    from .qr_reader import decode_nf55g_label
except ImportError:  # pragma: no cover
    from qr_reader import decode_nf55g_label


class QRWriteError(ValueError):
    pass


def serial_data_from_qr(raw):
    fields = decode_nf55g_label(raw)
    # 2026-11-23承認：REV右空白、YYWW→LOT、号機→SERIAL。
    # r1の最大値指定でFW/ADU/BBU/予約を変更しない。
    data = ('F'*6 + fields['product_rev'] + ' ' +
            fields['manufacture_year'] + fields['manufacture_week'] +
            fields['serial'] + 'F'*30).encode('ascii')
    assert len(data) == 50
    return data


class QRWriteSession:
    def __init__(self, clock, nonce, transport=None):
        self.clock, self.nonce, self.transport = clock, nonce, transport
        self.generation = self.sequence = 0
        self.active = False
        self.line = bytearray()
        self.last_seq = None
        self.ignored = 0
        self.cancel()

    def cancel(self):
        self.state, self.token, self.raw, self.data = 'IDLE', None, None, None
        self.reviewed = False
        self.error = None

    def start_trial(self):
        self.generation += 1
        self.active = True
        self.cancel()

    def end_trial(self):
        self.active = False
        self.cancel()

    def fail(self, error):
        self.state, self.error = 'ERROR', error
        self.raw = self.data = None
        self.reviewed = False

    def start(self, timeout_ms):
        if not self.active:
            raise QRWriteError('NO_TRIAL')
        if self.transport is None:
            raise QRWriteError('DISABLED')
        if not 100 <= timeout_ms <= 60000:
            raise QRWriteError('TIMEOUT_RANGE')
        if self.state == 'READING':
            raise QRWriteError('BUSY')
        # 開始前に親UARTに到着済みの値・断片は新取得に流用しない。
        self.cancel()
        self.line = bytearray()
        for _ in range(32):
            if not self.transport.any():
                break
            self.transport.read(min(128, self.transport.any()))
        if self.transport.any():
            raise QRWriteError('INPUT_BUSY')
        if self.transport.take_error():
            raise QRWriteError('UART')
        self.sequence += 1
        self.token = 'Q{}-{:08X}-{:08X}'.format(self.nonce, self.generation, self.sequence)
        self.last_seq = None
        self.deadline = self.clock.ticks_ms() + timeout_ms
        self.state = 'READING'
        return self.token

    def require(self, token):
        if not self.active or token != self.token:
            raise QRWriteError('STALE_ID')
        if self.state != 'READY':
            raise QRWriteError(self.error or self.state)

    def get(self, token, review=False):
        self.require(token)
        if review:
            self.reviewed = True
        return self.raw, self.data

    def write_data(self, token):
        self.require(token)
        if not self.reviewed:
            raise QRWriteError('NOT_REVIEWED')
        return self.data

    def consume(self):
        self.raw = self.data = None
        self.reviewed = False
        self.state = 'CONSUMED'

    def poll(self):
        if self.transport is None:
            return
        if self.state == 'READING' and self.clock.ticks_ms() >= self.deadline:
            self.fail('TIMEOUT')
        fault = self.transport.take_error()
        if fault and self.state == 'READING':
            self.fail(fault)
        raw = self.transport.read(min(512, self.transport.any()))
        for value in raw:
            if value == 10:
                line, self.line = bytes(self.line), bytearray()
                self._record(line.rstrip(b'\r').lstrip(b'\0'))
            elif len(self.line) < 155:
                self.line.append(value)
            else:
                if self.state == 'READING':
                    self.fail('FRAME')
                self.line = bytearray()

    def _record(self, line):
        try:
            if len(line) != 153 or line[:1] != b'@':
                raise QRWriteError('FRAME')
            seq, ms, kind, addr, instance, size, payload = struct.unpack(
                '<IIBBBB64s', binascii.unhexlify(line[1:]))
            if size > 64 or kind not in range(1, 16):
                raise QRWriteError('FRAME')
            if self.last_seq is not None and seq != self.last_seq + 1:
                raise QRWriteError('SEQUENCE')
            self.last_seq = seq
            payload = payload[:size]
            if kind in (1, 3, 8):
                raise QRWriteError('HOST_RESTART_OR_DISCONNECT')
            if kind in (7, 9, 10, 13):
                raise QRWriteError('HOST_ERROR')
            if kind == 14 and (size != 24 or struct.unpack('<6I', payload)[2] or
                               struct.unpack('<6I', payload)[5] & ~15):
                raise QRWriteError('HOST_DROP')
            if kind == 12:
                if self.state != 'READING':
                    self.ignored += 1
                    return
                raw = payload.decode('ascii')
                data = serial_data_from_qr(raw)
                self.raw, self.data = raw, data
                self.state = 'READY'
        except (ValueError, UnicodeError) as exc:
            if self.state == 'READING':
                self.fail(str(exc))
