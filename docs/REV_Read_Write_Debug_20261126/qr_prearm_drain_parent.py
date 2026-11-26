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
if RECOVER_RX:
    # Rebind the same receiver after the maintenance REPL interrupts its hard IRQ.
    original.close()
    original.__init__(rx_pin=9, baudrate=115200, sm_id=0, tx_idle_pin=None, buffer_size=2048)
    print('QR_DRAIN_RX_REBOUND')
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
ignored_before = session.ignored
try:
    deadline = time.ticks_add(time.ticks_ms(), 5000)
    while baseline is None and time.ticks_diff(deadline, time.ticks_ms()) > 0:
        app.service_once()
        time.sleep_ms(1)
    assert baseline is not None
    print('QR_HID_BOUNDARY_READY|'+json.dumps(baseline))
    deadline = time.ticks_add(time.ticks_ms(), 65000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0 and complete is None:
        app.service_once()
        time.sleep_ms(1)
    assert complete is not None and complete[2] == LATE_A, complete
    assert session.state == 'IDLE' and session.token is None and session.raw is None
    assert session.ignored == ignored_before + 1, session.ignored
    print('QR_DRAINED|' + json.dumps({'baseline': baseline, 'in_progress': trigger, 'completed': complete,
          'ignored_before': ignored_before, 'ignored_after': session.ignored}))

    armed = app.execute_ate_line('QR_SCAN 60000')
    assert armed.startswith('OK:QR_ARMED:'), armed
    token = armed.split(':')[-1]
    armed_at = time.ticks_ms()
    print('QR_DRAIN_SCAN_B|' + token)
    deadline = time.ticks_add(armed_at, 62000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0 and session.state == 'READING':
        app.service_once()
        time.sleep_ms(1)
    received = app.execute_ate_line('QR_GET? ' + token)
    assert received == 'OK:QR_GET:' + token + ':' + EXPECTED_B, received
    preview = app.execute_ate_line('QR_DATA? ' + token)
    assert preview == 'OK:QR_DATA:' + token + ':' + EXPECTED_B_HEX, preview
    print('QR_DRAIN_B_VERIFIED|' + json.dumps({'get': received, 'preview': preview, 'armed_at': armed_at}))
finally:
    session.transport = original
    ended = app.execute_ate_line('TEST_END')
    print('QR_DRAIN_END|' + json.dumps({'test_end': ended, 'drops': app.logger.drop_count}))
