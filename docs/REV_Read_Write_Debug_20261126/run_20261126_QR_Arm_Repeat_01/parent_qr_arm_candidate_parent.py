EXPECTED_B='US250A-CGXE-009491-101A032601000002'
EXPECTED_B_HEX='4646464646464130332032363031303030303032464646464646464646464646464646464646464646464646464646464646'
LINK_ONLY=False
ARM_CASES=3
# 保守接続で実行する双方向診断。受信したQRからSS候補を照合する。
import binascii
import struct
import sys
import time

from machine import Pin
import rp2
from src.external_instrument_link import new_nonce
from src.external_instrument_pio import _transmit
from src.qr_write_session import serial_data_from_qr


def records(app, rx):
    line = bytearray()
    synced = False
    while True:
        app.service_once()
        fault = rx.take_error()
        assert not fault, fault
        for byte in rx.read(min(512, rx.any())):
            if byte == 10:
                wire = bytes(line)
                line = bytearray()
                if len(wire) != 153 or wire[:1] != b'@':
                    assert not synced, wire
                    continue
                seq, ms, kind, _, _, size, payload = struct.unpack(
                    '<IIBBBB64s', binascii.unhexlify(wire[1:]))
                assert size <= 64, size
                synced = True
                yield seq, ms, kind, payload[:size]
            else:
                line.append(byte)
                if len(line) > 153:
                    assert not synced
                    line = bytearray()
        yield None
        time.sleep_ms(1)


def wait_for(stream, timeout, accept):
    start = time.ticks_ms()
    for record in stream:
        if time.ticks_diff(time.ticks_ms(), start) >= timeout:
            raise RuntimeError('QR_HOST_TIMEOUT')
        if record is not None and accept(record):
            return record


def health(record):
    if record[2] != 14:
        return False
    _, _, drops, _, _, flags = struct.unpack('<6I', record[3])
    assert not drops, drops
    return bool(flags & 1)


def send_request(tx, observe_pad=False):
    local = None
    request_id = binascii.hexlify(new_nonce()).upper() + b'00000001'
    request = b'\nA' + request_id + b'\n'
    try:
        if observe_pad:
            local = type(rx)(rx_pin=8, baudrate=115200, sm_id=2, tx_idle_pin=None, buffer_size=128)
        if not tx.active():
            pin = Pin(8, Pin.OUT, value=1)
            tx.init(_transmit, freq=115200 * 8, out_base=pin, sideset_base=pin)
            tx.active(1)
        for byte in request:
            tx.put(byte)
        print('QR_HID_ARM_REQUEST|', request_id.decode())
        if local is not None:
            time.sleep_ms(5)
            observed = local.read(local.any())
            fault = local.take_error()
            print('QR_HID_ARM_LOCAL_TX|', binascii.hexlify(observed).decode(), fault)
            assert not fault and observed == request, 'GP8 waveform differs from request'
        return request_id
    finally:
        if local is not None:
            local.close()


def wait_ack(stream, request_id):
    def matching_ack(record):
        assert record[2] not in (1, 3, 8, 10), record[:3]
        if record[2] in (13, 14, 16):
            print('QR_HID_ARM_RX|', record[:3], binascii.hexlify(record[3]).decode())
        return record[2] == 16 and record[3][:-1] == request_id

    return wait_for(stream, 8000, matching_ack)


def run_case(stream, tx, baseline, case_number):
    _, _, _, old_qr, old_hid, _ = struct.unpack('<6I', baseline[3])

    def in_progress(record):
        nonlocal old_qr, old_hid
        if not health(record):
            return False
        _, _, _, count, hid, _ = struct.unpack('<6I', record[3])
        if count != old_qr:
            print('QR_HID_ARM_A_COMPLETED_BEFORE_REQUEST|', record[:2], count, hid)
            old_qr, old_hid = count, hid
            return False
        return hid > old_hid

    print('QR_HID_ARM_SCAN_A|', case_number, baseline[:2], old_qr, old_hid)
    observed = wait_for(stream, 65000, in_progress)
    print('QR_HID_ARM_OLD_IN_PROGRESS|', case_number, observed[:2])
    request_id = send_request(tx)
    ack = wait_ack(stream, request_id)
    last_seq = ack[0]
    assert ack[3] == request_id + b'\x01', ('A_NOT_DRAINED_DURING_ARM', ack)
    print('QR_HID_ARM_SCAN_B|', case_number, ack[:2], request_id.decode())

    def matching_qr(record):
        nonlocal last_seq
        assert record[0] == (last_seq + 1) & 0xffffffff, ('SEQUENCE', record[:3])
        last_seq = record[0]
        assert record[2] not in (1, 3, 7, 8, 9, 10, 13), record[:3]
        if record[2] == 14:
            assert health(record), record[:3]
        return record[2] == 17 and record[3][:24] == request_id

    result = wait_for(stream, 60000, matching_qr)
    raw = result[3][24:].decode('ascii')
    assert raw == EXPECTED_B, raw
    data = binascii.hexlify(serial_data_from_qr(raw)).decode().upper()
    assert data == EXPECTED_B_HEX.upper(), data
    print('QR_HID_ARM_B_VERIFIED|', case_number, result[:2], raw, data)


app = sys.modules['src.main'].active_app
session = app.qr_write
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
assert app.logger.sd_sink.status == 'OK'
rx = session.transport
tx = rp2.StateMachine(1)
assert not tx.active()
assert app.execute_ate_line('TEST_START') == 'OK'
session.transport = None
try:
    rx.close()
    rx.__init__(rx_pin=9, baudrate=115200, sm_id=0, tx_idle_pin=None, buffer_size=2048)
    stream = records(app, rx)
    if LINK_ONLY:
        wait_for(stream, 6000, health)
        request_id = send_request(tx, observe_pad=True)
        ack = wait_ack(stream, request_id)
        assert ack[3] == request_id + b'\x00', ack
        print('QR_HID_ARM_LINK_OK|', ack[:2], request_id.decode())
    else:
        for case_number in range(1, ARM_CASES + 1):
            run_case(stream, tx, wait_for(stream, 6000, health), case_number)
finally:
    tx.active(0)
    session.transport = rx
    ended = app.execute_ate_line('TEST_END')
    print('QR_HID_ARM_END|', ended, app.logger.drop_count)
    assert ended == 'OK' and app.logger.drop_count == 0
