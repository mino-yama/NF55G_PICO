# QR側のGP9/115200診断出力を受動採取する。SS/ATE/校正Cacheへは渡さない。
import machine
import rp2
import time
import binascii
import hashlib
import json
import gc
from src.qr_pio_rx import QRPioRx

assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'
assert not rp2.StateMachine(0).active(), 'QR SM0 already active'
# REPL停止後の単独試験。測定器経路を入力化し、QRと混在させない。
rp2.StateMachine(4).active(0)
rp2.StateMachine(5).active(0)
machine.Pin(12,machine.Pin.IN)
machine.Pin(13,machine.Pin.IN)
QR_DURATION_MS=180000
# 連続runでは前回RAMを再利用。受信開始前の確保で失敗時にPIOを残さない。
qr_raw=None
gc.collect()
if 'qr_capture' not in globals() or len(qr_capture)<65536:
    qr_capture=bytearray(65536)
qr_rx=QRPioRx(rx_pin=9,baudrate=115200,sm_id=0,tx_idle_pin=None,buffer_size=2048)
qr_size=0
qr_fault=None
print('QR_CAPTURE_READY|GP9|115200|'+str(QR_DURATION_MS//1000)+'s')
qr_started=time.ticks_ms()
try:
    while time.ticks_diff(time.ticks_ms(),qr_started)<QR_DURATION_MS:
        qr_fault=qr_rx.take_error()
        if qr_fault: break
        chunk=qr_rx.read(min(128,qr_rx.any()))
        if chunk:
            if qr_size+len(chunk)>len(qr_capture):
                qr_fault='CAPTURE_FULL'
                break
            qr_capture[qr_size:qr_size+len(chunk)]=chunk
            qr_size+=len(chunk)
        time.sleep_ms(1)
finally:
    qr_rx.close()
    machine.Pin(9,machine.Pin.IN)
qr_raw=bytes(qr_capture[:qr_size])
print('QR_CAPTURE_META|'+json.dumps({'bytes':qr_size,'fault':qr_fault,
    'sha256':binascii.hexlify(hashlib.sha256(qr_raw).digest()).decode(),
    'duration_ms':time.ticks_diff(time.ticks_ms(),qr_started),'baudrate':115200,'rx_pin':9,
    'qr_sm_active':rp2.StateMachine(0).active(),'meter_sm4_active':rp2.StateMachine(4).active(),
    'meter_sm5_active':rp2.StateMachine(5).active()}))
# USB REPLの一括出力欠落を避け、原文hash照合可能な速度で回収する。
for qr_offset in range(0,qr_size,64):
    print('QR_CAPTURE_HEX|'+binascii.hexlify(qr_raw[qr_offset:qr_offset+64]).decode())
    time.sleep_ms(20)
print('QR_CAPTURE_DONE_PIO_INPUT')
