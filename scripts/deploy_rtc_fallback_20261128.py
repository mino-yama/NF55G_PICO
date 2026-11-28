"""RTCログ改修4件の段階配置と、隔離した実SD領域でのデバッグ。製品通信なし。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from mpremote.transport_serial import SerialTransport

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'docs/RTC_Fallback_Log_Implementation_20261128_Rev0'
OUT = ROOT / 'docs/RTC_Fallback_Log_Deployment_20261128_Rev0'
UID = '69f7d45962cfdfad'
DEBUG_ROOT = '/sd/rtc_debug_20261128_rev0'
HEADER = '''import sys, os, gc, json, machine, binascii, hashlib
assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = getattr(sys.modules.get('src.main'), 'active_app', None)
assert app is not None
assert not app.logger.active and not app.logger.test_running and not app.logger.recovery_pending
assert not app._comm_busy()
assert app.logger.sd_status == 'OK'
def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        while True:
            b=f.read(512)
            if not b: break
            h.update(b)
    return binascii.hexlify(h.digest()).decode()
def maybe_digest(path):
    try: return digest(path)
    except OSError as e:
        if e.args[0] == 2: return None
        raise
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','apply','debug','after-reset'))
    parser.add_argument('--port',default='COM6')
    args=parser.parse_args()
    if args.action=='prepare':OUT.mkdir()
    assert OUT.is_dir()
    transport=SerialTransport(args.port,timeout=2)
    try:
        transport.enter_raw_repl(soft_reset=False)
        def execute(code):
            out,err=transport.exec_raw(code,timeout=60)
            with (OUT/'operations.jsonl').open('a',encoding='utf-8') as log:
                log.write(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'code':code,
                                      'stdout':out.decode('utf-8','replace'),'stderr':err.decode('utf-8','replace')},ensure_ascii=False)+'\n')
            if err:raise RuntimeError(err.decode('utf-8','replace'))
            return out.decode('utf-8')
        def evaluate(expr):
            return json.loads(execute('print(json.dumps('+expr+'))').strip())
        execute(HEADER)
        if args.action=='prepare':
            source=json.loads((CANDIDATE/'manifest.json').read_text(encoding='utf-8'))
            for f in source['files']:
                data=(CANDIDATE/'payload'/f['target'].lstrip('/')).read_bytes()
                assert sha(data)==f['sha256']
                assert data==(ROOT/f['source']).read_bytes()
                assert evaluate('maybe_digest('+repr(f['target'])+')')==f['expected_before'],f['target']
            for p,expected in source['expected_dependencies'].items():
                assert evaluate('digest('+repr(p)+')')==expected
            paths=evaluate("['/src/'+n for n in os.listdir('/src') if not os.stat('/src/'+n)[0]&0x4000]+['/main.py','/calibration_limits.py']")
            before=evaluate('{p:digest(p) for p in '+repr(paths)+'}')
            # 保存対象は変更前3件と実機固有設定・依存RTC・起動・校正設定。全体hashも残す。
            backups=[f['target'] for f in source['files'] if f['expected_before'] is not None]
            backups+=['/src/config.py','/src/rtc_driver.py','/main.py','/calibration_limits.py']
            for p in backups:
                data=transport.fs_readfile(p)
                assert sha(data)==before[p]
                target=OUT/'backup'/p.lstrip('/')
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                print('BACKUP '+p,flush=True)
            after=dict(before)
            for f in source['files']:
                data=(CANDIDATE/'payload'/f['target'].lstrip('/')).read_bytes()
                p=OUT/'payload'/f['target'].lstrip('/')
                p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                after[f['target']]=f['sha256']
            cfg={};exec((OUT/'backup/src/config.py').read_bytes(),cfg)
            save('manifest.json',{'unique_id':UID,'before':before,'after':after,'files':source['files'],
                 'preserved_config':{k:cfg[k] for k in ('EXTERNAL_INSTRUMENT_ENABLED','QR_HOST_ENABLED','QR_HOST_ARM_ENABLED','CALIBRATION_SAMPLE_ENABLED','ATE_RESPONSE_TERMINATOR','T2_AR_MS','REPL_LOG_ENABLED')},
                 'debug_root':DEBUG_ROOT,'host_mock_tests':source['host_mock_tests']})
            print('PREPARED; IDLE; BACKUP_HASH_VERIFIED',flush=True)
            return

        manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
        if args.action=='apply':
            assert evaluate('{p:digest(p) for p in '+repr(list(manifest['before']))+'}')==manifest['before']
            stage='/rtc_log_stage_20261128_rev0';rollback='/rtc_log_before_20261128_rev0'
            execute('os.mkdir('+repr(stage)+');os.mkdir('+repr(stage+'/src')+')')
            for f in manifest['files']:
                p=f['target'];data=(OUT/'payload'/p.lstrip('/')).read_bytes()
                assert sha(data)==f['sha256']
                transport.fs_writefile(stage+p,data)
                assert transport.fs_hashfile(stage+p,'sha256').hex()==f['sha256']
                execute('gc.collect()\nwith open('+repr(stage+p)+',"rb") as f: compile(f.read(),'+repr(p)+',"exec")')
                print('STAGED '+p,flush=True)
            execute('sys.path.insert(0,"/src");sys.path.insert(0,'+repr(stage+'/src')+''')
for n in ('logger','sd_sink','log_filename','rtc_driver'): sys.modules.pop(n,None)
import logger as staged_logger, sd_sink as staged_sd
mem=staged_logger.MemorySDSink()
probe=staged_logger.Logger(mem)
assert probe.test_start() and probe.current_filename=='NO_RTC_T000001.csv'
assert probe.set_serial('000001') and probe.test_end()
assert '000001_NO_RTC_T000001.csv' in mem.files
assert staged_sd.FileSDSink._log_name('000001_NO_RTC_T000001.csv')
print('MICROPYTHON_STAGE_RUNTIME_OK')
''')
            changed={f['target']:f['sha256'] for f in manifest['files']}
            execute(HEADER+'\nbefore='+repr(manifest['before'])+'\nafter='+repr(changed)+'\nstage='+repr(stage)+'\nrollback='+repr(rollback)+'''
for p in before: assert digest(p)==before[p]
for p in after:
    assert digest(stage+p)==after[p]
    if p not in before: assert maybe_digest(p) is None
os.mkdir(rollback);os.mkdir(rollback+'/src')
saved=[];installed=[]
try:
    for p in after:
        if p in before:
            os.rename(p,rollback+p);saved.append(p)
        os.rename(stage+p,p);installed.append(p)
        assert digest(p)==after[p]
except Exception:
    for p in reversed(installed):os.rename(p,stage+p)
    for p in reversed(saved):os.rename(rollback+p,p)
    raise
print('SWAP_VERIFIED')
''')
            for p,h in changed.items():
                data=transport.fs_readfile(p);assert sha(data)==h
                dest=OUT/'readback'/p.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            all_hashes=evaluate('{p:digest(p) for p in '+repr(list(manifest['after']))+'}')
            assert all_hashes==manifest['after'];save('after_apply_hashes.json',all_hashes)
            save('applied.json',{'changed_files':4,'whole_app_files':len(all_hashes),'rollback':rollback,'verified':True})
            transport.exec_raw_no_follow('import machine;machine.reset()')
            print('APPLIED; 4_READBACK_AND_ALL_HASHES_OK; RESET_SUBMITTED',flush=True)
            return

        assert evaluate('{p:digest(p) for p in '+repr(list(manifest['after']))+'}')==manifest['after']
        if args.action=='debug':
            code='debug_root='+repr(DEBUG_ROOT)+'''
from src.logger import Logger
from src.sd_sink import FileSDSink
try: os.stat(debug_root)
except OSError as e:
    if e.args[0]!=2: raise
else: raise AssertionError('debug folder already exists; preserve prior results')
os.mkdir(debug_root)
def new_sink():
    sink=FileSDSink(debug_root,busy=app._comm_busy);sink.mount();return sink
sink=new_sink()
for name in ('000001_NO_RTC_T000040.csv','NO_RTC_C000041.csv'):
    with open(debug_root+'/BANK_B/'+name,'wb') as f: f.flush()
sink=new_sink()
assert sink.log_high_watermark==41
probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert probe.test_start() and probe.current_filename=='NO_RTC_T000042.csv'
probe.log(category='HIL',event='RTC_NONE',detail='ISOLATED DEBUG; no product commands')
assert probe.timestamp_snapshot==''
assert probe.set_serial('000001') and probe.test_end()
assert probe.last_test_filename=='000001_NO_RTC_T000042.csv'
assert probe.log_cont_start() and probe.current_filename=='NO_RTC_C000043.csv'
probe.log(category='HIL',event='CONT_NONE');assert probe.log_cont_stop()
class BrokenRTC:
    def datetime(self):raise OSError('RTC HIL simulated failure')
probe.rtc=BrokenRTC()
assert probe.test_start() and probe.current_filename=='NO_RTC_T000044.csv'
assert probe.rtc_filename_status=='READ_ERROR'
probe.log(category='HIL',event='RTC_READ_ERROR');assert probe.test_end()
class InvalidRTC:
    def datetime(self):return '20260230_250000'
probe.rtc=InvalidRTC()
assert probe.test_start() and probe.current_filename=='NO_RTC_T000045.csv'
assert probe.rtc_filename_status=='INVALID'
probe.log(category='HIL',event='RTC_INVALID');assert probe.test_end()
probe=Logger(sink,clock=app.clock,busy=app._comm_busy,flush_record_count=1,rollover_bytes=1)
assert probe.log_cont_start() and probe.current_filename=='NO_RTC_C000046.csv'
probe.log(category='HIL',event='ROLLOVER_NONE')
assert probe.service()==1 and probe.current_filename=='NO_RTC_C000047.csv'
probe.log(category='HIL',event='BUSY_DEFER')
probe.busy=lambda:True
assert probe.service()==0 and not probe.test_end()
probe.busy=app._comm_busy
assert probe.log_cont_stop()
assert probe.drop_count==0
if hasattr(os,'sync'):os.sync()
paths=[debug_root+'/'+bank+'/'+n for bank in ('BANK_A','BANK_B') for n in os.listdir(debug_root+'/'+bank) if n.endswith('.csv')]
print('HIL_BEFORE|'+json.dumps({'max_id':sink.log_high_watermark,'hashes':{p:digest(p) for p in paths},'cases':['RTC_NONE_TEST_SN','RTC_NONE_CONT','RTC_READ_ERROR','RTC_INVALID','CONT_ROLLOVER','COMM_BUSY_DEFER','BOTH_BANK_ZERO_BYTES'],'product_commands_sent':False}))
'''
            result=execute(code);print(result,flush=True)
            data=json.loads(next(l[11:] for l in result.splitlines() if l.startswith('HIL_BEFORE|')))
            save('hil_before_reset.json',data)
            for p,h in data['hashes'].items():
                raw=transport.fs_readfile(p);assert sha(raw)==h
                dest=OUT/'sd_csv_before_reset'/Path(p).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
            transport.exec_raw_no_follow('import machine;machine.reset()')
            print('HIL_BEFORE_RESET_OK; RESET_SUBMITTED',flush=True)
            return

        prior=json.loads((OUT/'hil_before_reset.json').read_text(encoding='utf-8'))
        code='debug_root='+repr(DEBUG_ROOT)+'\nexpected_max='+repr(prior['max_id'])+'\nold_hashes='+repr(prior['hashes'])+'''
from src.logger import Logger
from src.sd_sink import FileSDSink
for p in old_hashes:assert digest(p)==old_hashes[p]
sink=FileSDSink(debug_root,busy=app._comm_busy);sink.mount()
assert sink.log_high_watermark==expected_max
probe=Logger(sink,clock=app.clock,busy=app._comm_busy)
assert probe.test_start()
assert probe.trial_number==expected_max+1
assert probe.current_filename=='NO_RTC_T{:06d}.csv'.format(expected_max+1)
probe.log(category='HIL',event='AFTER_HARD_RESET',detail='ISOLATED DEBUG')
assert probe.set_serial('000002') and probe.test_end()
for p in old_hashes:assert digest(p)==old_hashes[p]
assert app.logger.rtc is app.rtc
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
if hasattr(os,'sync'):os.sync()
new_path=debug_root+'/'+sink.bank+'/'+probe.last_test_filename
print('HIL_AFTER|'+json.dumps({'filename':probe.last_test_filename,'number':probe.trial_number,'path':new_path,'sha256':digest(new_path),'original_logs_preserved':True,'sd_status':probe.last_test_sd_status,'drop_count':probe.drop_count,'real_rtc':app.rtc.datetime() if app.rtc else None}))
'''
        result=execute(code);print(result,flush=True)
        data=json.loads(next(l[10:] for l in result.splitlines() if l.startswith('HIL_AFTER|')))
        save('hil_after_reset.json',data)
        raw=transport.fs_readfile(data['path']);assert sha(raw)==data['sha256']
        (OUT/'sd_csv_after_reset').mkdir(exist_ok=True)
        (OUT/'sd_csv_after_reset'/Path(data['path']).name).write_bytes(raw)
        all_hashes=evaluate('{p:digest(p) for p in '+repr(list(manifest['after']))+'}')
        assert all_hashes==manifest['after'];save('final_hashes.json',all_hashes)
        transport.exec_raw_no_follow('app.run()');time.sleep(1)
        output=transport.serial.read(transport.serial.in_waiting)
        (OUT/'resume_output.bin').write_bytes(output)
        assert b'Traceback' not in output
        save('result.json',{'status':'deployed_hil_verified_running','unique_id':UID,'changed_files':4,'verified_files':len(all_hashes),'real_sd_hil':True,'hardware_reset_verified':True,'physical_power_off_test':False,'product_commands_sent':False,'original_rtc_config_unchanged':True})
        print('DEPLOYMENT_AND_REAL_SD_HIL_COMPLETE; APP_RESUMED',flush=True)
    finally:
        transport.close()


if __name__=='__main__':main()
