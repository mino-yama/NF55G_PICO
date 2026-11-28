"""親GP12を低／高各15秒へ一時固定し、HOST GP1の手動電圧実測を支援する。"""
from pathlib import Path
import argparse
import subprocess
import sys
import json
import winsound
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
parser.add_argument('--hold-seconds',type=int,choices=(15,30),default=30);args=parser.parse_args()
assert args.run.replace('_','').isalnum()
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01'/args.run
OUT.mkdir()
CODE=r'''
import sys,time,json,machine
a=sys.modules['src.main'].active_app;e=a.external_link;t=e.transport
assert e.expected_chipid=='73AD3A60D10514E9'
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
assert not a.server.pending and not a.server.tx and not a.ate_uart.any()
assert t.tx.tx_fifo()==0
ctrl=machine.mem32[0x40028064];pad=machine.mem32[0x40038034];active=t.tx.active()
rows=[]
try:
    t.tx.active(0)
    p=machine.Pin(12,machine.Pin.OUT,value=1)
    for value,label in ((0,'LOW'),(1,'HIGH')):
        p.value(value);time.sleep_ms(20)
        observed=p.value();rows.append({'ms':time.ticks_ms(),'set':value,'read':observed})
        assert observed==value,'output readback differs; abort hold'
        print('\nRX_LEVEL|'+label)
        time.sleep_ms(HOLD_MS)
finally:
    machine.Pin(12).value(1)
    machine.mem32[0x40028064]=ctrl;machine.mem32[0x40038034]=pad;t.tx.active(active)
    print('\nRX_LEVEL_RESULT|'+json.dumps({'rows':rows,'ctrl':machine.mem32[0x40028064],'active':t.tx.active()}))
'''
script=OUT/'parent.py';script.write_text('HOLD_MS='+str(args.hold_seconds*1000)+'\n'+CODE,encoding='utf-8')
base=[sys.executable,'-u','-m','mpremote','connect','COM6','resume']
with (OUT/'parent.log').open('x',encoding='utf-8') as log:
    p=subprocess.Popen(base+['run',str(script)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        for line in p.stdout:
            log.write(line);log.flush()
            if line.strip()=='RX_LEVEL|LOW':
                print('LOW_'+str(args.hold_seconds)+'_SECONDS',flush=True);winsound.Beep(500,300)
            elif line.strip()=='RX_LEVEL|HIGH':
                print('HIGH_'+str(args.hold_seconds)+'_SECONDS',flush=True);winsound.Beep(1400,300)
            elif 'RX_LEVEL_RESULT|' in line:print(line.strip(),flush=True)
        assert p.wait(timeout=10)==0
    finally:
        if p.poll() is None:p.terminate();p.wait(timeout=10)
        # 低レベル試験で残り得るHOST内の断片は、管理要求を再開する前に改行だけで区切る。
        subprocess.run(base+['exec','--no-follow',"import sys;a=sys.modules['src.main'].active_app;a.external_link.transport.write(b'\\r\\n');a.run()"],timeout=30,check=True)
winsound.Beep(1800,150);winsound.Beep(1800,150);winsound.Beep(1800,150)
print('LEVEL_TEST_COMPLETE; PIO_RESTORED',flush=True)
