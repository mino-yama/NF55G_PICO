"""実SD異常系とPCシリアル経由の通常ATEサーバー試験。NF55G UARTは使わない。"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time

import serial
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/RTC_Fallback_Log_Extended_Test_20261128_Rev0'
SDROOT='/sd/rtc_extended_20261128_rev0'


def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('faults','ate','prepare-power','after-power'))
    parser.add_argument('--port',default='COM6')
    parser.add_argument('--ate-port',default='COM7')
    args=parser.parse_args()
    if args.action=='faults':OUT.mkdir()
    assert OUT.is_dir()
    expected=json.loads((ROOT/'docs/RTC_Fallback_Log_Deployment_20261128_Rev0/final_hashes.json').read_text(encoding='utf-8'))
    remote=SerialTransport(args.port,timeout=2)
    try:
        remote.enter_raw_repl(soft_reset=False)
        def execute(code):
            out,err=remote.exec_raw(code,timeout=60)
            with (OUT/'operations.jsonl').open('a',encoding='utf-8') as log:
                log.write(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'code':code,'stdout':out.decode('utf-8','replace'),'stderr':err.decode('utf-8','replace')},ensure_ascii=False)+'\n')
            if err:raise RuntimeError(err.decode('utf-8','replace'))
            return out.decode('utf-8')
        def evaluate(expr):return json.loads(execute('print(json.dumps('+expr+'))').strip())
        def export_csv(directory,hashes):
            dest=OUT/directory;dest.mkdir(exist_ok=True)
            for p,h in hashes.items():
                raw=remote.fs_readfile(p)
                assert hashlib.sha256(raw).hexdigest()==h
                (dest/Path(p).name).write_bytes(raw)
        def resume():
            remote.exec_raw_no_follow('app.run()');time.sleep(1)
            out=remote.serial.read(remote.serial.in_waiting)
            assert b'Traceback' not in out,out
        execute(HEADER)
        actual=evaluate('{p:digest(p) for p in '+repr(list(expected))+'}')
        assert actual==expected
        save('firmware_verified.json',actual)
        if args.action=='faults':
            code='root='+repr(SDROOT)+'''
from src.logger import Logger, LoggerError
from src.sd_sink import FileSDSink
os.mkdir(root)
def newsink(name,fs=None):
    path=root+'/'+name
    os.mkdir(path)
    sink=FileSDSink(path,fs=fs,busy=app._comm_busy);sink.mount()
    return sink
def absent(path):
    try:os.stat(path)
    except OSError as e:
        if e.args[0]==2:return True
        raise
    return False
results=[]
sink=newsink('collision')
old={}
for n in range(1,9):
    path=sink.root+'/BANK_B/NO_RTC_T{:06d}.csv'.format(n)
    with open(path,'wb') as f:f.write(b'EXISTING FIXTURE');f.flush()
    old[path]=digest(path)
probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert not probe.test_start() and probe.status()=='FILE_EXISTS'
assert sink.log_high_watermark==8 and not probe.active
for p in old:assert digest(p)==old[p]
assert len([n for n in os.listdir(sink.root+'/BANK_A') if n.endswith('.csv')])==0
probe.test_end()
results.append({'case':'eight_collisions','status':'FILE_EXISTS','preserved':8})
sink=newsink('rename_collision');probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert probe.test_start();probe.log(category='HIL',event='KEEP_SOURCE');probe.force_drain()
source=sink.open_filename;original=digest(source)
target=sink.root+'/BANK_B/000001_'+probe.current_filename
with open(target,'wb') as f:f.write(b'KEEP TARGET');f.flush()
target_hash=digest(target)
assert probe.set_serial('000001') and not probe.test_end()
assert probe.last_test_sd_status=='FILE_EXISTS'
assert digest(source)==original and digest(target)==target_hash
results.append({'case':'rename_collision_other_bank','status':'FILE_EXISTS','both_preserved':True})
class FaultFS:
    bad_stat=False
    bad_list=False
    bad_rename=False
    def stat(self,p):
        if self.bad_stat and p.endswith('NO_RTC_T000001.csv'):raise OSError(5)
        return os.stat(p)
    def listdir(self,p):
        if self.bad_list and p.endswith('BANK_B'):raise OSError(5)
        return os.listdir(p)
    def statvfs(self,p):return os.statvfs(p)
    def mkdir(self,p):return os.mkdir(p)
    def remove(self,p):return os.remove(p)
    def rename(self,a,b):
        if self.bad_rename and '/000001_' in b:raise OSError(5)
        return os.rename(a,b)
fs=FaultFS();sink=newsink('stat_error',fs);fs.bad_stat=True
probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert not probe.test_start() and probe.status()=='OPEN_ERR'
assert absent(sink.root+'/BANK_A/NO_RTC_T000001.csv')
probe.test_end();results.append({'case':'stat_io_error','status':'OPEN_ERR','created':False})
fs=FaultFS();sink=newsink('scan_error',fs)
path=sink.root+'/BANK_B/NO_RTC_C000009.csv'
with open(path,'wb') as f:f.write(b'KEEP SCAN FIXTURE');f.flush()
old_hash=digest(path);fs.bad_list=True
try:sink.mount();raise AssertionError('scan unexpectedly passed')
except LoggerError:pass
assert not sink.namespace_ready
probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert not probe.test_start() and digest(path)==old_hash
probe.test_end();results.append({'case':'partial_scan_error','namespace_ready':False,'preserved':True})
fs=FaultFS();sink=newsink('rename_error',fs);probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert probe.test_start();probe.log(category='HIL',event='RENAME_FAIL');probe.force_drain()
path=sink.open_filename;old_hash=digest(path);fs.bad_rename=True
probe.set_serial('000001');assert not probe.test_end()
assert probe.last_test_sd_status=='WRITE_ERR' and digest(path)==old_hash
results.append({'case':'rename_io_error','status':'WRITE_ERR','original_preserved':True})
sink=newsink('rotation')
old=sink.root+'/BANK_B/NO_RTC_C000009.csv'
foreign=sink.root+'/BANK_B/keep.txt'
directory=sink.root+'/BANK_B/NO_RTC_C000999.csv'
with open(old,'wb') as f:f.write(b'OLD OWNED FIXTURE')
with open(foreign,'wb') as f:f.write(b'KEEP FOREIGN')
os.mkdir(directory);sink.mount();assert sink.log_high_watermark==9
sink.bank_bytes['BANK_A']=sink.capacity_bytes
probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert probe.test_start() and probe.trial_id=='T000010' and sink.bank=='BANK_B'
assert absent(old) and not absent(foreign) and os.stat(directory)[0]&0x4000
assert probe.test_end()
results.append({'case':'rotation_threshold_injected','bank':'BANK_B','foreign_preserved':True,'directory_preserved':True})
if hasattr(os,'sync'):os.sync()
print('FAULT_RESULTS|'+json.dumps(results))
'''
            out=execute(code);print(out,flush=True)
            data=json.loads(next(l[len('FAULT_RESULTS|'):] for l in out.splitlines() if l.startswith('FAULT_RESULTS|')))
            save('fault_results.json',data);resume();return

        if args.action=='ate':
            code='ate_root='+repr(SDROOT+'/ate')+'''
from src.logger import Logger
from src.sd_sink import FileSDSink
from src.main import FixtureApp
assert app.ate_uart.any()==0
os.mkdir(ate_root)
ate_sink=FileSDSink(ate_root);ate_sink.mount()
test_app=FixtureApp(ate_uart=app.ate_uart,clock=app.clock,rtc=None,
    logger=Logger(ate_sink,clock=app.clock),nf55_uart=None,protocol=None)
assert test_app.protocol is None and test_app.nf55_uart is None
print('ATE_TEST_READY')
'''
            assert 'ATE_TEST_READY' in execute(code)
            remote.exec_raw_no_follow('test_app.run()')
            wire=[]
            try:
                with serial.Serial(args.ate_port,57600,bytesize=8,parity='N',stopbits=1,timeout=0.1) as port:
                    assert port.in_waiting==0,'unexpected previous ATE data'
                    def request(cmd):
                        started=time.perf_counter();port.write(cmd.encode()+b'\r');port.flush()
                        data=bytearray()
                        while time.perf_counter()-started<15:
                            part=port.read(1)
                            if part:
                                data.extend(part)
                                if part==b'\r':break
                        row={'command':cmd,'response':bytes(data).decode('ascii','replace'),'elapsed_ms':(time.perf_counter()-started)*1000}
                        wire.append(row)
                        with (OUT/'ate_wire.jsonl').open('a',encoding='utf-8') as log:log.write(json.dumps(row)+'\n')
                        assert data.endswith(b'\r'),row
                        time.sleep(0.11)
                        return bytes(data).rstrip(b'\r').decode()
                    assert request('*IDN?')=='NF55G_PICO_FIXTURE,Rev.0'
                    for n in range(30):
                        for cmd,expected_reply in (('TEST_START','OK'),('*IDN?','NF55G_PICO_FIXTURE,Rev.0'),('SD_STATUS?','OK')):
                            assert request(cmd)==expected_reply
                        check=request('PICO_SELF_CHECK?')
                        assert 'RTC=UNAVAILABLE' in check and 'LOGGER=OK' in check
                        assert request('TEST_END')=='OK'
                        assert request('PICO_SELF_CHECK?').endswith('TEST_LOGGER=OK;TEST_LOG_DROP=OK')
                        assert request('LOG_DROP_COUNT?')=='0'
                        print('ATE_TRIAL '+str(n+1)+'/30 OK',flush=True)
                    for cmd in ('LOG_CONT_START','*IDN?','SD_STATUS?','LOG_CONT_STOP'):
                        reply=request(cmd)
                        assert reply==('NF55G_PICO_FIXTURE,Rev.0' if cmd=='*IDN?' else 'OK')
            finally:
                remote.enter_raw_repl(soft_reset=False)
            out=execute('''assert not test_app.logger.active and not test_app.logger.test_running
assert test_app.protocol is None and test_app.nf55_uart is None
assert test_app.logger.drop_count==0
if hasattr(os,'sync'):os.sync()
paths=[ate_root+'/'+b+'/'+n for b in ('BANK_A','BANK_B') for n in os.listdir(ate_root+'/'+b) if n.endswith('.csv')]
assert len(paths)==31
print('ATE_RESULT|'+json.dumps({'trials':30,'cont_sessions':1,'drop':0,'nf55g_uart':False,'hashes':{p:digest(p) for p in paths}}))
''')
            data=json.loads(next(l[len('ATE_RESULT|'):] for l in out.splitlines() if l.startswith('ATE_RESULT|')))
            export_csv('ate_csv',data['hashes']);save('ate_result.json',data)
            save('ate_timing.json',{'requests':len(wire),'max_ms':max(r['elapsed_ms'] for r in wire),'max_test_start_ms':max(r['elapsed_ms'] for r in wire if r['command']=='TEST_START'),'max_test_end_ms':max(r['elapsed_ms'] for r in wire if r['command']=='TEST_END')})
            resume();print('ATE_30_TRIALS_AND_CONT_COMPLETE',flush=True);return

        if args.action=='prepare-power':
            code='power_root='+repr(SDROOT+'/power')+'''
from src.logger import Logger
from src.sd_sink import FileSDSink
os.mkdir(power_root)
sink=FileSDSink(power_root,busy=app._comm_busy);sink.mount()
probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert probe.test_start();probe.log(category='HIL',event='BEFORE_POWER_OFF')
assert probe.set_serial('000001') and probe.test_end()
if hasattr(os,'sync'):os.sync()
path=power_root+'/'+sink.bank+'/'+probe.last_test_filename
power_cycle_sentinel='rtc-physical-cycle-20261128'
print('POWER_READY|'+json.dumps({'root':power_root,'max_id':sink.log_high_watermark,'path':path,'hash':digest(path),'rtc':app.rtc.datetime() if app.rtc else None,'rtc_status':app.rtc.device.read_status() if app.rtc and hasattr(app.rtc.device,'read_status') else None}))
'''
            out=execute(code);data=json.loads(next(l[len('POWER_READY|'):] for l in out.splitlines() if l.startswith('POWER_READY|')))
            data['host_utc']=datetime.now(timezone.utc).isoformat();save('power_ready.json',data)
            export_csv('power_before',{data['path']:data['hash']});resume();print('POWER_OFF_READY; FILES_CLOSED; APP_IDLE',flush=True);return

        before=json.loads((OUT/'power_ready.json').read_text(encoding='utf-8'))
        out=execute('power_root='+repr(before['root'])+'\nold_path='+repr(before['path'])+'\nold_hash='+repr(before['hash'])+'\nold_max='+repr(before['max_id'])+'''
assert 'power_cycle_sentinel' not in globals(),'RAM state did not restart'
from src.logger import Logger
from src.sd_sink import FileSDSink
assert digest(old_path)==old_hash
sink=FileSDSink(power_root,busy=app._comm_busy);sink.mount()
assert sink.log_high_watermark==old_max
probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert probe.test_start() and probe.trial_number==old_max+1
probe.log(category='HIL',event='AFTER_PHYSICAL_POWER_OFF')
assert probe.set_serial('000002') and probe.test_end()
assert digest(old_path)==old_hash
if hasattr(os,'sync'):os.sync()
path=power_root+'/'+sink.bank+'/'+probe.last_test_filename
print('POWER_RESULT|'+json.dumps({'filename':probe.last_test_filename,'path':path,'hash':digest(path),'old_preserved':True,'number':probe.trial_number,'sd':'OK','drop':probe.drop_count,'rtc':app.rtc.datetime() if app.rtc else None,'rtc_status':app.rtc.device.read_status() if app.rtc and hasattr(app.rtc.device,'read_status') else None}))
''')
        data=json.loads(next(l[len('POWER_RESULT|'):] for l in out.splitlines() if l.startswith('POWER_RESULT|')))
        data['host_utc']=datetime.now(timezone.utc).isoformat();save('power_result.json',data)
        export_csv('power_after',{data['path']:data['hash']});resume();print('POWER_CYCLE_CHECK_COMPLETE; APP_RESUMED',flush=True)
    finally:remote.close()


if __name__=='__main__':main()
