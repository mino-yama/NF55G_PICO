import binascii
import sys
import time


app = sys.modules['src.main'].active_app
session = app.qr_write
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
original = session.transport
captured = bytearray()
duration_ms = 2500


class ObservedTransport:
    def any(self):
        return original.any()

    def take_error(self):
        return original.take_error()

    def read(self, count):
        data = original.read(count)
        if data and len(captured) < 16384:
            captured.extend(data)
        return data


session.transport = ObservedTransport()
start = time.ticks_ms()
print('QR_UART_CAPTURE_READY')
try:
    while time.ticks_diff(time.ticks_ms(), start) < duration_ms:
        session.poll()
        time.sleep_ms(2)
finally:
    session.transport = original
for offset in range(0, len(captured), 96):
    print('QR_UART_DATA|' + binascii.hexlify(captured[offset:offset + 96]).decode())
    time.sleep_ms(15)
print('QR_UART_CAPTURE_END')
