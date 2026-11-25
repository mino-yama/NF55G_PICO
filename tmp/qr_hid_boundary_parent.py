import binascii
import json
import struct
import sys
import time


app = sys.modules['src.main'].active_app
session = app.qr_write
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
assert app.logger.sd_sink.status == 'OK'
original = session.transport
baseline = None
trigger = None
complete = None
line = bytearray()


class Tap:
    def any(self):
        return original.any()

    def take_error(self):
        return original.take_error()

    def read(self, count):
        global baseline, trigger, complete, line
        data = original.read(count)
        for byte in data:
            if byte == 10:
                wire = bytes(line).rstrip(b'\r').lstrip(b'\x00')
                line = bytearray()
                if len(wire) != 153 or wire[:1] != b'@':
                    continue
                seq, ms, kind, addr, instance, size, payload = struct.unpack(
                    '<IIBBBB64s', binascii.unhexlify(wire[1:]))
                if kind == 14 and size == 24:
                    loops, frames, drops, qr, hid, flags = struct.unpack('<6I', payload[:24])
                    if baseline is None:
                        assert flags & 1 and not drops
                        baseline = (seq, ms, qr, hid)
                    elif trigger is None and hid > baseline[3] and qr == baseline[2] and complete is None:
                        trigger = (seq, ms, qr, hid, time.ticks_ms())
                elif kind == 12 and complete is None:
                    complete = (seq, ms, payload[:size].decode('ascii'), time.ticks_ms())
            elif len(line) < 157:
                line.append(byte)
        return data


assert app.execute_ate_line('TEST_START') == 'OK'
session.transport = Tap()
token = None
reply = None
preview = None
armed_at = None
try:
    deadline = time.ticks_add(time.ticks_ms(), 5000)
    while baseline is None and time.ticks_diff(deadline, time.ticks_ms()) > 0:
        app.service_once()
        time.sleep_ms(1)
    assert baseline is not None
    print('QR_HID_BOUNDARY_READY|'+json.dumps(baseline))
    deadline = time.ticks_add(time.ticks_ms(), 65000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        app.service_once()
        if token is None and trigger is not None and complete is None:
            result = app.execute_ate_line('QR_SCAN 15000')
            assert result.startswith('OK:QR_ARMED:'), result
            token = result.split(':')[-1]
            armed_at = time.ticks_ms()
            deadline = time.ticks_add(armed_at, 16000)
        if complete is not None or (token is not None and session.state == 'ERROR'):
            break
        time.sleep_ms(1)
    if token is not None:
        reply = app.execute_ate_line('QR_GET? ' + token)
        if reply.startswith('OK:QR_GET:'):
            preview = app.execute_ate_line('QR_DATA? ' + token)
finally:
    session.transport = original
    ended = app.execute_ate_line('TEST_END')
print('QR_HID_RESULT|' + json.dumps({'baseline': baseline, 'trigger': trigger, 'complete': complete,
      'armed_at': armed_at, 'token': token, 'qr_get': reply, 'qr_data': preview, 'test_end': ended}))
