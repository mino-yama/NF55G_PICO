"""実ATE・実QRのSS照合。D5退避、UNIT限定ガード、読戻し、復元を記録する。"""
import argparse
import json
from pathlib import Path
from queue import Queue, Empty
import subprocess
import sys
from threading import Thread
import time
import serial
import winsound

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT/'docs/QR_Production_Integration_20261128_Rev0'

PARENT = r'''
import sys,time,json,binascii,machine
from src.frame import build_frame
app=sys.modules['src.main'].active_app
assert binascii.hexlify(machine.unique_id())==b'69f7d45962cfdfad'
assert not app.logger.test_running and not app.logger.active and not app._comm_busy()
assert app.logger.sd_status=='OK' and app.qr_write.arm_host
protocol=app.protocol
assert protocol is not None
def hx(v):return binascii.hexlify(v).decode()
def emit(event,**values):print('\nPRODUCT|'+json.dumps(dict(event=event,**values)))
class Guard:
    def __init__(self,inner):self.inner=inner;self.writes=0;self.restore=None;self.mode='READ';self.wire=[]
    def any(self):return self.inner.any()
    def read(self,n=1):
        v=self.inner.read(n)
        if v:self.wire.append(['RX',hx(v)])
        return v
    def write(self,data):
        data=bytes(data)
        if data not in (b'\x06',b'\x15',build_frame('D5',b'')):
            allowed=target if self.mode=='WRITE' else self.restore if self.mode=='RESTORE' else None
            if allowed is None or data!=build_frame('SS',allowed):raise OSError('command outside D5/UNIT SS guard')
            self.mode='READ';self.writes+=1
        self.wire.append(['TX',hx(data)])
        return self.inner.write(data)
original=protocol.uart
guard=Guard(original)
protocol.uart=guard
baseline=None
def result(event):
    tx=protocol.last_result
    emit(event,cmd=tx.cmd,ok=tx.ok,error=tx.error,ambiguous=tx.ambiguous,
         data=hx(tx.response_data),raw=hx(tx.raw_response),wire=guard.wire,
         command_retry=tx.command_retry_count,response_retry=tx.response_retry_count)
    guard.wire=[]
    return tx
def d5(event):
    reply=app.execute_ate_line('INFO_REFRESH');tx=result(event)
    assert tx.cmd=='D5' and tx.ok and len(tx.response_data)==100,reply
    return tx.response_data
try:
    baseline=d5('BASELINE')
    if expected is not None:
        assert hx(baseline)==expected,'product changed after baseline backup'
        guard.restore=b'F'*6+baseline[6:20]+b'F'*30
        assert len(target)==50 and target[:6]==b'F'*6 and target[20:]==b'F'*30
        guard.mode='WRITE'
        emit('READY',baseline=hx(baseline))
        previous=protocol.last_result
        began=False;started=time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(),started)<180000:
            app.service_once()
            if protocol.last_result is not previous:
                previous=protocol.last_result;result('TRANSACTION')
            if app.logger.test_running:began=True
            if began and not app.logger.test_running:break
            time.sleep_ms(1)
        assert began and not app.logger.test_running,'trial did not finish within bound'
finally:
    try:
        if baseline is not None and guard.writes:
            before=d5('BEFORE_RESTORE')
            if before[6:20]!=baseline[6:20]:
                guard.mode='RESTORE'
                protocol.transact('SS',guard.restore,t2_ms=100,expected_length=0,allow_command_retry=False)
                tx=result('RESTORE_SS')
                assert tx.ok and not tx.ambiguous,'restore SS failed'
            after=d5('RESTORED_D5')
            emit('RESTORE',exact=after==baseline,baseline=hx(baseline),actual=hx(after))
            assert after==baseline,'D5 restoration mismatch'
    finally:
        protocol.uart=original
        if app.logger.test_running:emit('END',reply=app.execute_ate_line('TEST_END'))
        emit('FINISHED',writes=guard.writes,drop=app.logger.drop_count)
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('preflight','execute'))
    parser.add_argument('--run',required=True)
    args=parser.parse_args()
    out=CASE/args.run
    assert out.parent==CASE and args.run.replace('_','').isalnum()
    if args.phase=='preflight':out.mkdir()
    sample=json.loads((ROOT/'docs/QR_Hardware_Integration_20261123_01/Production_Label_Retest_20261125/expected.json').read_text())['B']
    target=bytes.fromhex(sample['ss_data_hex'])
    expected=None if args.phase=='preflight' else json.loads((out/'baseline.json').read_text())['data']
    script=out/(args.phase+'_parent.py')
    script.write_text('expected='+repr(expected)+'\ntarget='+repr(target)+'\n'+PARENT,encoding='utf-8')
    base=[sys.executable,'-u','-m','mpremote','connect','COM6','resume']
    records=Queue();events=[]
    def wait(predicate,timeout=25):
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            try:r=records.get(timeout=.5)
            except Empty:continue
            if predicate(r):return r
            if r.get('event')=='PROCESS_END':raise RuntimeError('parent ended; inspect wire log')
        raise TimeoutError('product event timeout')
    with (out/(args.phase+'_wire.log')).open('x',encoding='utf-8') as log:
        proc=subprocess.Popen(base+['run',str(script)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
        def read():
            for line in proc.stdout:
                log.write(line);log.flush()
                if 'PRODUCT|' in line:
                    r=json.loads(line.split('PRODUCT|',1)[1]);events.append(r);records.put(r)
            records.put({'event':'PROCESS_END'})
        reader=Thread(target=read,daemon=True);reader.start()
        try:
            baseline=wait(lambda r:r.get('event')=='BASELINE')
            assert baseline['ok'] and not baseline['ambiguous'] and len(bytes.fromhex(baseline['data']))==100,baseline
            if args.phase=='preflight':
                (out/'baseline.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
                print('BASELINE_SAVED '+bytes.fromhex(baseline['data']).decode('ascii'),flush=True)
                assert proc.wait(timeout=15)==0
            else:
                wait(lambda r:r.get('event')=='READY')
                with serial.Serial('COM7',57600,timeout=.1) as ate:
                    assert not ate.in_waiting
                    def ask(command):
                        ate.write(command.encode()+b'\r');ate.flush();wire=bytearray();until=time.monotonic()+15
                        while time.monotonic()<until:
                            b=ate.read(1);wire.extend(b)
                            if b==b'\r':break
                        response=wire.decode('ascii').rstrip('\r')
                        with (out/'ate_wire.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(command=command,reply=response))+'\n')
                        assert wire.endswith(b'\r'),response
                        time.sleep(.12);return response
                    assert ask('TEST_START')=='OK'
                    pending=ask('QR_SCAN 60000');assert pending.startswith('OK:QR_PENDING:')
                    token=pending.split(':')[-1]
                    until=time.monotonic()+10
                    while True:
                        reply=ask('QR_GET? '+token)
                        if reply=='ERR:QR_READING':break
                        assert reply=='ERR:QR_ARMING' and time.monotonic()<until,reply
                    print('SCAN_B',flush=True);winsound.Beep(1400,220)
                    until=time.monotonic()+55
                    while True:
                        reply=ask('QR_GET? '+token)
                        if reply.startswith('OK:QR_GET:'):break
                        assert reply=='ERR:QR_READING' and time.monotonic()<until,reply
                        time.sleep(.2)
                    assert reply=='OK:QR_GET:'+token+':'+sample['payload'],reply
                    assert ask('QR_DATA? '+token)=='OK:QR_DATA:'+token+':'+target.hex()
                    assert ask('QR_WRITE '+token)=='OK:QR_WRITE:'+token
                    ss=wait(lambda r:r.get('event')=='TRANSACTION' and r.get('cmd')=='SS')
                    assert ss['ok'] and not ss['ambiguous']
                    ask('INFO_REFRESH')
                    after=wait(lambda r:r.get('event')=='TRANSACTION' and r.get('cmd')=='D5')
                    observed=bytes.fromhex(after['data']);before=bytes.fromhex(expected)
                    assert after['ok'] and observed==before[:6]+target[6:20]+before[20:],after
                    print('SS_D5_MATCH; RESTORING',flush=True)
                    assert ask('TEST_END')=='OK'
                restored=wait(lambda r:r.get('event')=='RESTORE')
                assert restored['exact']
                assert proc.wait(timeout=20)==0
                print('RESTORED_100_BYTES',flush=True)
        finally:
            # REPL割込みでも親スクリプトのfinallyでD5照会・復元してから通常処理へ戻す。
            if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
            reader.join(timeout=3)
            subprocess.run(base+['exec','--no-follow',"import sys;sys.modules['src.main'].active_app.run()"],cwd=ROOT,timeout=30,check=True)
            (out/(args.phase+'_events.json')).write_text(json.dumps(events,indent=2),encoding='utf-8')

if __name__=='__main__':main()
