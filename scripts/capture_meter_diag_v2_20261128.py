"""固定配線の入力到達先と戻り通信を、両マイコンの観測で照合する。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import serial
from serial.tools import list_ports
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/uart_diagnostic_v2'
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
assert args.run.replace('_','').isalnum()
OUT=OUT/args.run;OUT.mkdir()
PARENT=r'''
import sys,time,json,binascii,machine
a=sys.modules['src.main'].active_app
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
link=a.external_link;original=link.transport
class Trace:
    def __init__(self):self.events=[]
    def any(self):return original.any()
    def take_error(self):return original.take_error()
    def read(self,n):
        v=original.read(n)
        if v:self.events.append([time.ticks_ms(),'RX',binascii.hexlify(v).decode()])
        return v
    def write(self,v):
        n=original.write(v)
        if n:self.events.append([time.ticks_ms(),'TX',binascii.hexlify(v[:n]).decode()])
        return n
t=Trace();link.transport=t
pin13=machine.Pin(13);last_pin13=pin13.value();pin13_edges=0
try:
    print('\nDIAG2_READY')
    start=time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(),start)<15000:
        a.service_once()
        current=pin13.value()
        if current!=last_pin13:pin13_edges+=1;last_pin13=current
        time.sleep_ms(1)
finally:
    link.transport=original
    print('\nDIAG2_TRACE|'+json.dumps(t.events))
    print('\nDIAG2_PIN13|'+json.dumps({'edges':pin13_edges,'last':last_pin13}))
'''
ports=[p for p in list_ports.comports() if (p.serial_number or '').upper()=='BFCF2EDB84B0B37F']
assert len(ports)==1,ports
script=OUT/'parent_trace.py';script.open('x',encoding='utf-8').write(PARENT)
base=[sys.executable,'-u','-m','mpremote','connect','COM6','resume']
native=bytearray();result={'native_port':ports[0].device,'selftest_origin':'native USB; diagnostic session; not normal ATE acceptance'}
with (OUT/'parent_trace.log').open('x',encoding='utf-8') as log,serial.Serial(ports[0].device,115200,timeout=.1) as host:
    def capture(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:native.extend(host.read(4096))
    proc=subprocess.Popen(base+['run',str(script)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        while True:
            line=proc.stdout.readline();log.write(line);log.flush();assert line,'parent not ready'
            if 'DIAG2_READY' in line:break
        result['parent_ready_at']=time.monotonic()
        result['selftest_sent_at']=time.monotonic();host.write(b'T');host.flush()
        capture(2)
        result['info_sent_at']=time.monotonic()
        with serial.Serial('COM7',57600,timeout=12) as ate:
            assert not ate.in_waiting
            ate.write(b'HOST_INFO? METER\r');ate.flush();reply=ate.read_until(b'\r')
            result['ate_reply']=reply.decode('ascii','replace')
        capture(2)
        rest,_=proc.communicate(timeout=20);log.write(rest);log.flush();assert proc.returncode==0
    finally:
        if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
        subprocess.run(base+['exec','--no-follow',"import sys;sys.modules['src.main'].active_app.run()"],timeout=25,check=True)
        (OUT/'native_capture.log').write_bytes(native)
line=next(l for l in (OUT/'parent_trace.log').read_text().splitlines() if 'DIAG2_TRACE|' in l)
events=json.loads(line.split('DIAG2_TRACE|',1)[1]);result['parent_events']=events
pin_line=next(l for l in (OUT/'parent_trace.log').read_text().splitlines() if 'DIAG2_PIN13|' in l)
result['parent_pin13']=json.loads(pin_line.split('DIAG2_PIN13|',1)[1])
result['parent_tx_bytes']=sum(len(bytes.fromhex(h)) for _,d,h in events if d=='TX')
result['parent_rx_bytes']=sum(len(bytes.fromhex(h)) for _,d,h in events if d=='RX')
edge_rows=[{int(k):int(v) for k,v in (item.split(':') for item in l[6:].split(',') if item)} for l in native.decode('ascii','replace').splitlines() if l.startswith('EDGES|')]
if len(edge_rows)>1:result['observed_edge_deltas']={k:edge_rows[-1][k]-v for k,v in edge_rows[0].items() if edge_rows[-1][k]!=v}
result['health']=[l for l in native.decode('ascii','replace').splitlines() if l.startswith('DIAG|')]
(OUT/'capture_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='parent_events'}))
