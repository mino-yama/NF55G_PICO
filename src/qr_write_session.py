# QR HOSTレコードから、現試行の最初の完成QRを固定する。
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
    def __init__(self, clock, nonce, transport=None, arm_host=False):
        self.clock, self.nonce, self.transport = clock, nonce, transport
        self.arm_host = arm_host
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
        self.host_id = None
        self.arm_request = b''
        self.arm_discarded = None

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
        self.arm_request = b''

    def start(self, timeout_ms):
        if not self.active:
            raise QRWriteError('NO_TRIAL')
        if self.transport is None:
            raise QRWriteError('DISABLED')
        if not 100 <= timeout_ms <= 60000:
            raise QRWriteError('TIMEOUT_RANGE')
        if self.state in ('ARMING', 'READING'):
            raise QRWriteError('BUSY')
        self.cancel()
        if not self.arm_host:
            # 旧HOSTの受信済みの値・断片は新取得に流用しない。
            self.line = bytearray()
            for _ in range(32):
                if not self.transport.any():
                    break
                self.transport.read(min(128, self.transport.any()))
            if self.transport.any():
                raise QRWriteError('INPUT_BUSY')
        if self.transport.take_error():
            self.line = bytearray()
            raise QRWriteError('UART')
        self.sequence += 1
        self.token = 'Q{}-{:08X}-{:08X}'.format(self.nonce, self.generation, self.sequence)
        self.last_seq = None
        self.deadline = self.clock.ticks_ms() + timeout_ms
        if self.arm_host:
            # 先頭LFで送信中断時の旧要求断片をHOST側で破棄する。
            self.host_id = ('{}{:08X}'.format(self.nonce.upper(), self.sequence)).encode('ascii')
            self.arm_request = b'\nA' + self.host_id + b'\n'
            self.state = 'ARMING'
        else:
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
        if self.state in ('ARMING', 'READING') and self.clock.ticks_ms() >= self.deadline:
            self.fail('TIMEOUT')
        fault = self.transport.take_error()
        if fault:
            self.line = bytearray()
            if self.state in ('ARMING', 'READING'):
                self.fail(fault)
        if self.arm_request:
            try:
                written = self.transport.write(self.arm_request)
                self.arm_request = self.arm_request[written:]
            except OSError:
                self.fail('UART')
        raw = self.transport.read(min(512, self.transport.any()))
        for value in raw:
            if value == 10:
                line, self.line = bytes(self.line), bytearray()
                self._record(line.rstrip(b'\r').lstrip(b'\0'))
            elif len(self.line) < 155:
                self.line.append(value)
            else:
                if self.state in ('ARMING', 'READING'):
                    self.fail('FRAME')
                self.line = bytearray()

    def _record(self, line):
        try:
            if len(line) != 153 or line[:1] != b'@':
                raise QRWriteError('FRAME')
            seq, ms, kind, addr, instance, size, payload = struct.unpack(
                '<IIBBBB64s', binascii.unhexlify(line[1:]))
            if size > 64 or kind not in range(1, 18 if self.arm_host else 16):
                raise QRWriteError('FRAME')
            if kind in (1, 3, 8):
                self.last_seq = seq
                if self.arm_host and self.state == 'READY':
                    self.fail('HOST_RESTART_OR_DISCONNECT')
                    return
                raise QRWriteError('HOST_RESTART_OR_DISCONNECT')
            if self.last_seq is not None and seq != ((self.last_seq + 1) & 0xffffffff):
                self.last_seq = seq
                raise QRWriteError('SEQUENCE')
            self.last_seq = seq
            payload = payload[:size]
            if kind in (7, 9, 10, 13):
                raise QRWriteError('HOST_ERROR')
            if kind == 14:
                if size != 24:
                    raise QRWriteError('HOST_DROP')
                _, _, drops, _, _, flags = struct.unpack('<6I', payload)
                if drops or flags & ~15:
                    raise QRWriteError('HOST_DROP')
                if self.arm_host and self.state == 'READING' and not flags & 1:
                    raise QRWriteError('HOST_RESTART_OR_DISCONNECT')
            if kind == 16:
                if size != 25 or payload[-1] not in (0, 1):
                    raise QRWriteError('FRAME')
                if self.state == 'ARMING' and not self.arm_request and payload[:24] == self.host_id:
                    self.arm_discarded = payload[-1]
                    self.state = 'READING'
                return
            if kind == 17:
                if size != 59:
                    raise QRWriteError('FRAME')
                if payload[:24] != self.host_id:
                    self.ignored += 1
                    return
                payload = payload[24:]
            if kind == 17 or kind == 12:
                if kind == 12 and self.arm_host:
                    self.ignored += 1
                    return
                if self.state != 'READING':
                    self.ignored += 1
                    return
                raw = payload.decode('ascii')
                data = serial_data_from_qr(raw)
                self.raw, self.data = raw, data
                self.state = 'READY'
        except (ValueError, UnicodeError) as exc:
            if self.state in ('ARMING', 'READING'):
                self.fail(str(exc))
