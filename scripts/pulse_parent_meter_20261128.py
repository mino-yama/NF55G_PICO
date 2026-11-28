"""待機中の親GP12に低速診断パルスを出し、HOSTの入力到達を観測する。"""
import json
from pathlib import Path
import subprocess
import sys
import time
import serial
from serial.tools import list_ports
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/uart_diagnostic_v2/pulse_forward'
OUT.mkdir()
PARENT=r'''
import sys,time,json,machine
a=sys.modules['src.main'].active_app
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
t=a.external_link.transport
assert t.tx.active() and t.tx.tx_fifo()==0
saved=machine.mem32[0x40028064]
assert saved&31==7
values=[]
try:
    t.tx.active(0)
    pin=machine.Pin(12,machine.Pin.OUT,value=1)
    print('\nPULSE_READY')
    time.sleep_ms(1000)
    for value in (0,1,0,1):
        pin.value(value)
        values.append({'ms':time.ticks_ms(),'set':value,'read':pin.value()})
        time.sleep_ms(300)
finally:
    machine.Pin(12).value(1)
    machine.mem32[0x40028064]=saved
    t.tx.active(1)
    print('\nPULSE_RESULT|'+json.dumps({'values':values,'restored_ctrl':machine.mem32[0x40028064],'tx_active':t.tx.active()}))
'''
ports=[p for p in list_ports.comports() if (p.serial_number or '').upper()=='BFCF2EDB84B0B37F']
assert len(ports)==1
script=OUT/'parent.py';script.write_text(PARENT,encoding='utf-8')
base=[sys.executable,'-u','-m','mpremote','connect','COM6','resume']
data=bytearray()
with serial.Serial(ports[0].device,115200,timeout=.1) as host,(OUT/'parent.log').open('x',encoding='utf-8') as log:
    proc=subprocess.Popen(base+['run',str(script)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        while True:
            line=proc.stdout.readline();log.write(line);log.flush();assert line
            if 'PULSE_READY' in line:break
        end=time.monotonic()+5
        while time.monotonic()<end:data.extend(host.read(4096))
        rest,_=proc.communicate(timeout=20);log.write(rest);log.flush();assert proc.returncode==0
    finally:
        if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
        subprocess.run(base+['exec','--no-follow',"import sys;sys.modules['src.main'].active_app.run()"],timeout=25,check=True)
        (OUT/'host_native.log').write_bytes(data)
rows=[{int(k):int(v) for k,v in (p.split(':') for p in l[6:].split(',') if p)} for l in data.decode('ascii','replace').splitlines() if l.startswith('EDGES|')]
summary={'edge_rows':len(rows),'edge_deltas':{k:rows[-1][k]-v for k,v in rows[0].items() if rows[-1][k]!=v} if len(rows)>1 else None}
line=next(l for l in (OUT/'parent.log').read_text().splitlines() if 'PULSE_RESULT|' in l)
summary['parent']=json.loads(line.split('PULSE_RESULT|',1)[1])
(OUT/'result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
