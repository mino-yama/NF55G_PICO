# 旧FW復元後の定期通知を、QRをスキャンせず保守USBから確認する。
import binascii
import struct
import sys
import time


app = sys.modules['src.main'].active_app
session = app.qr_write
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
rx = session.transport
session.transport = None
try:
    rx.close()
    rx.__init__(rx_pin=9, baudrate=115200, sm_id=0, tx_idle_pin=None, buffer_size=2048)
    print('QR_RESTORE_CAPTURE_READY')
    started = time.ticks_ms()
    line = bytearray()
    ready_count = 0
    prior_seq = None
    while time.ticks_diff(time.ticks_ms(), started) < 85000 and ready_count < 3:
        app.service_once()
        fault = rx.take_error()
        if fault:
            print('QR_RESTORE_RX_FAULT', fault)
            line = bytearray()
        for byte in rx.read(min(512, rx.any())):
            if byte != 10:
                if len(line) <= 153:
                    line.append(byte)
                continue
            wire = bytes(line).lstrip(b'\0')
            line = bytearray()
            if len(wire) != 153 or wire[:1] != b'@':
                continue
            seq, ms, kind, _, _, size, payload = struct.unpack('<IIBBBB64s', binascii.unhexlify(wire[1:]))
            if kind in (1, 11, 15):
                print('QR_RESTORE_START', seq, ms, kind, binascii.hexlify(payload[:size]).decode())
            if kind == 14 and size == 24:
                _, _, drops, reads, reports, flags = struct.unpack('<6I', payload[:24])
                print('QR_RESTORE_HEALTH', seq, ms, drops, reads, reports, flags)
                if not drops and flags & 1:
                    ready_count = ready_count + 1 if prior_seq == seq - 1 else 1
                else:
                    ready_count = 0
                prior_seq = seq
        time.sleep_ms(1)
    print('QR_RESTORE_CAPTURE_END', ready_count)
    assert ready_count >= 3
finally:
    session.transport = rx
