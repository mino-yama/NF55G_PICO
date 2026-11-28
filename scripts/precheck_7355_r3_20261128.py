"""7355 R3受入前のATE状態とHOST診断を保存する。設定・測定・リセットなし。"""
import argparse
import json
from pathlib import Path
import time
import serial
from mpremote.transport_serial import SerialTransport

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--tag',default='initial');args=parser.parse_args()
assert args.tag.replace('_','').isalnum()
assert not (OUT/('ate_'+args.tag+'.json')).exists()
record=[]
with serial.Serial('COM23',115200,timeout=.1) as monitor, serial.Serial('COM7',57600,timeout=12) as ate:
    assert not ate.in_waiting
    before=monitor.read_all()
    for command in ('*IDN?','COMM_STATUS?','SD_STATUS?','LOG_DROP_COUNT?','HOST_INFO? METER'):
        started=time.monotonic();ate.write(command.encode()+b'\r');ate.flush()
        raw=ate.read_until(b'\r')
        record.append(dict(command=command,response=raw.decode('ascii','replace'),elapsed_ms=round(1000*(time.monotonic()-started)),raw_hex=raw.hex()))
        assert raw.endswith(b'\r')
        time.sleep(.1)
    until=time.monotonic()+3
    data=bytearray(before)
    while time.monotonic()<until:data.extend(monitor.read(4096))
    (OUT/('host_monitor_'+args.tag+'.raw')).write_bytes(data)
    (OUT/('ate_'+args.tag+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({'ate':record,'monitor_bytes':len(data)}))
remote=SerialTransport('COM6',timeout=2)
try:
    remote.enter_raw_repl(soft_reset=False)
    code="""import sys,json,binascii,machine
a=sys.modules['src.main'].active_app
e=a.external_link
print(json.dumps({'uid':binascii.hexlify(machine.unique_id()).decode(),'trial':a.logger.test_running,'busy':a._comm_busy(),'external_enabled':e is not None,'transport':type(e.transport).__name__ if e else None,'fault':e.fault if e else None,'parent_nonce':binascii.hexlify(e.parent_nonce).decode() if e else None}))
"""
    out,err=remote.exec_raw(code,timeout=15)
    (OUT/('parent_'+args.tag+'.log')).write_bytes(out+b'\nSTDERR\n'+err)
    print(out.decode())
    if err:raise RuntimeError(err.decode())
finally:
    try:remote.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    finally:remote.close()
