"""既存PIOを再初期化せず、HOST情報照会の送受信だけをRAM監視する。"""
import json
from pathlib import Path
import subprocess
import sys
import time
import serial
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
PARENT=r'''
import sys,json,time,binascii
a=sys.modules['src.main'].active_app
link=a.external_link
original=link.transport
class Trace:
    def __init__(self):self.events=[]
    def any(self):return original.any()
    def take_error(self):return original.take_error()
    def read(self,n):
        v=original.read(n)
        if v:self.events.append(['RX',binascii.hexlify(v).decode()])
        return v
    def write(self,v):
        n=original.write(v)
        if n:self.events.append(['TX',binascii.hexlify(v[:n]).decode()])
        return n
t=Trace();link.transport=t
try:
    print('\nMETER_READY')
    start=time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(),start)<6000:
        a.service_once();time.sleep_ms(1)
finally:
    link.transport=original
    print('\nMETER_TRACE|'+json.dumps(t.events))
'''
script=OUT/'link_trace_ready_parent.py';script.open('x',encoding='utf-8').write(PARENT)
base=[sys.executable,'-u','-m','mpremote','connect','COM6','resume']
with (OUT/'link_trace_ready.log').open('x',encoding='utf-8') as f:
    proc=subprocess.Popen(base+['run',str(script)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        while True:
            line=proc.stdout.readline();f.write(line);f.flush()
            assert line,'parent exited before ready'
            if 'METER_READY' in line:break
        with serial.Serial('COM7',57600,timeout=12) as port:
            assert not port.in_waiting
            port.write(b'HOST_INFO? METER\r');reply=port.read_until(b'\r')
            (OUT/'trace_ready_ate_reply.json').write_text(json.dumps({'reply':reply.decode(),'raw':reply.hex()}))
            print(repr(reply),flush=True)
        rest,_=proc.communicate(timeout=15);f.write(rest);f.flush()
        assert proc.returncode==0
    finally:
        if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
        subprocess.run(base+['exec','--no-follow',"import sys;sys.modules['src.main'].active_app.run()"],timeout=20,check=True)
line=next(l for l in (OUT/'link_trace_ready.log').read_text().splitlines() if 'METER_TRACE|' in l)
events=json.loads(line.split('METER_TRACE|',1)[1])
print(json.dumps({'tx_bytes':sum(len(bytes.fromhex(h)) for d,h in events if d=='TX'),'rx_bytes':sum(len(bytes.fromhex(h)) for d,h in events if d=='RX')}))
