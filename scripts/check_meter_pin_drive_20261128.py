"""待機中の親GPIO12の機能選択・出力読戻しを保全し、終了時に元へ戻す。"""
from pathlib import Path
from mpremote.transport_serial import SerialTransport
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/uart_diagnostic_v2'
code=r'''
import sys,time,json,machine
a=sys.modules['src.main'].active_app
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
t=a.external_link.transport
ctrl=machine.mem32[0x40028064];active=t.tx.active()
rows=[]
def snapshot(label):
    return {'label':label,'ctrl':machine.mem32[0x40028064],'value':machine.Pin(12).value(),
            'sio':{hex(i):machine.mem32[0xd0000000+i] for i in range(0x10,0x44,4)}}
try:
    rows.append(snapshot('before'))
    t.tx.active(0)
    p=machine.Pin(12,machine.Pin.OUT,value=1)
    rows.append(snapshot('Pin_OUT'))
    p.value(0);time.sleep_ms(20);rows.append(snapshot('set_low'))
    p.value(1);time.sleep_ms(20);rows.append(snapshot('set_high'))
finally:
    machine.Pin(12).value(1);machine.mem32[0x40028064]=ctrl;t.tx.active(active)
    rows.append(snapshot('restored'))
print(json.dumps(rows))
'''
r=SerialTransport('COM6',timeout=2)
try:
    r.enter_raw_repl(soft_reset=False)
    out,err=r.exec_raw(code,timeout=20)
    (OUT/'pin_drive_check.log').open('xb').write(out+b'\nSTDERR\n'+err)
    print(out.decode('utf-8','replace'))
    if err:raise RuntimeError(err.decode())
finally:
    try:r.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    finally:r.close()
