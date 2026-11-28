"""待機中のみ親UART0をGP12/13へ一時割当て、PIOを介さずHOST INFOを1件照会。"""
import json
import argparse
from pathlib import Path
import serial
from mpremote.transport_serial import SerialTransport
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
assert args.run.replace('_','').isalnum()
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01'/args.run
OUT.mkdir()
CODE=r'''
import sys,time,json,machine,binascii
from src.external_instrument_contract import encode_frame
from src import config
a=sys.modules['src.main'].active_app;e=a.external_link;t=e.transport;u=a.ate_uart.uart
assert e.expected_chipid=='73AD3A60D10514E9'
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
assert not a.server.pending and not a.server.tx and not u.any()
assert e._management is None and e._active is None and t.tx.tx_fifo()==0
ctrl={n:machine.mem32[0x40028000+8*n+4] for n in (0,1,12,13)}
pads={n:machine.mem32[0x40038000+4+4*n] for n in (0,1,12,13)}
txactive=t.tx.active();rxactive=t.rx.active()
req=e._next_management_id()
challenge=('{:08X}{:08X}'.format(req,time.ticks_ms()&0xffffffff)).encode()
wire=encode_frame(e.parent_nonce+bytes(8),req,'I',0,1000,e.expected_chipid.encode()+b'|'+challenge)
received=bytearray();restored=False
try:
    t.tx.active(0);t.rx.active(0);t.rx.irq(None)
    machine.Pin(0,machine.Pin.IN,machine.Pin.PULL_UP)
    machine.Pin(1,machine.Pin.IN,machine.Pin.PULL_UP)
    u.init(baudrate=115200,bits=8,parity=None,stop=1,tx=machine.Pin(12),rx=machine.Pin(13),rxbuf=4096,timeout=0,timeout_char=0)
    machine.Pin(0,machine.Pin.IN,machine.Pin.PULL_UP)
    machine.Pin(1,machine.Pin.IN,machine.Pin.PULL_UP)
    if u.any():raise RuntimeError('preexisting input on hardware UART')
    written=u.write(wire);assert written==len(wire)
    u.flush()
    started=time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(),started)<1500:
        if u.any():received.extend(u.read(min(512,u.any())) or b'')
        time.sleep_ms(1)
finally:
    u.init(baudrate=config.ATE_BAUDRATE,bits=config.ATE_BITS,parity=config.ATE_PARITY,stop=config.ATE_STOP_BITS,
           tx=machine.Pin(0),rx=machine.Pin(1),rxbuf=4096,timeout=0,timeout_char=0)
    for n in (0,1,12,13):
        machine.mem32[0x40028000+8*n+4]=ctrl[n]
        machine.mem32[0x40038000+4+4*n]=pads[n]
    t.rx.irq(t._irq,hard=True);t.rx.active(rxactive);t.tx.active(txactive)
    restored=True
    print(json.dumps({'uid':e.expected_chipid,'request':req,'challenge':challenge.decode(),
        'tx_hex':binascii.hexlify(wire).decode(),'rx_hex':binascii.hexlify(received).decode(),
        'restored':restored,'gpio_ctrl':{str(n):machine.mem32[0x40028000+8*n+4] for n in (0,1,12,13)},
        'tx_active':t.tx.active(),'rx_active':t.rx.active()}))
'''
remote=SerialTransport('COM6',timeout=2)
try:
    remote.enter_raw_repl(soft_reset=False)
    out,err=remote.exec_raw(CODE,timeout=30)
    (OUT/'parent.log').write_bytes(out+b'\nSTDERR\n'+err)
    if err:raise RuntimeError(err.decode())
    result=json.loads(out.decode().strip())
    (OUT/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
finally:
    try:remote.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    finally:remote.close()
with serial.Serial('COM7',57600,timeout=3) as ate:
    extra=ate.read_all()
    ate.write(b'*IDN?\r');ate.flush();reply=ate.read_until(b'\r')
    record={'preexisting_hex':extra.hex(),'reply':reply.decode('ascii','replace')}
    (OUT/'ate_restored.json').write_text(json.dumps(record,indent=2))
    assert reply==b'NF55G_PICO_FIXTURE,Rev.0\r',record
print('ATE_RESTORED',flush=True)
