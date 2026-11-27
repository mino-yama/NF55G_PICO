"""親Picoの校正改版をバックアップ・検証・段階配置する。製品指令は送信しない。"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from mpremote.transport_serial import SerialTransport

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ID = '69f7d45962cfdfad'
CHECK = '''import sys, os, machine, binascii, hashlib, json, gc
assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = getattr(sys.modules.get('src.main'), 'active_app', None)
assert app is not None
assert not app.logger.active and not app.logger.test_running and not app.logger.recovery_pending
assert not app._comm_busy()
def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(512)
            if not b: break
            h.update(b)
    return binascii.hexlify(h.digest()).decode()
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate(folder):
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    for path, expected in manifest['before'].items():
        assert sha((folder / 'backup' / path.lstrip('/')).read_bytes()) == expected
    for path, expected in manifest['candidate'].items():
        data = (folder / 'payload' / path.lstrip('/')).read_bytes()
        assert sha(data) == expected
        compile(data,path,'exec')
    runner = 'import sys,unittest; sys.path.insert(0,' + repr(str(ROOT)) + '); sys.path.insert(0,' + repr(str(folder / 'payload')) + '); import src; print("PAYLOAD_SRC="+src.__file__,flush=True); unittest.main(module=None,argv=["unittest","discover","-s",' + repr(str(ROOT / 'tests')) + '])'
    with (folder / 'host_mock_tests.log').open('w', encoding='utf-8') as log:
        test = subprocess.run([sys.executable,'-c',runner], cwd=folder / 'payload', stdout=log, stderr=subprocess.STDOUT, timeout=120)
    assert test.returncode == 0, 'payload host/mock tests failed'
    (folder / 'prepared.json').write_text(json.dumps({'backup_verified':True,'host_mock_passed':True,'file_count':len(manifest['candidate']),'config_preserved_byte_for_byte':True},indent=2),encoding='utf-8')
    print('PREPARED_AND_TESTED; PICO_FILES_UNCHANGED', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'validate', 'apply', 'inspect'))
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--port', default='COM6')
    args = parser.parse_args()
    folder = args.directory or ROOT / 'docs' / ('Calibration_AB_Pico_Deployment_' + datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M%S'))
    folder = folder.resolve()
    assert folder.parent == ROOT / 'docs' and folder.name.startswith('Calibration_AB_Pico_Deployment_')
    if args.action == 'prepare':
        folder.mkdir()
    assert folder.is_dir()
    print(str(folder), flush=True)
    if args.action == 'validate':
        validate(folder)
        return

    def save(name, obj):
        (folder / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')

    transport = SerialTransport(args.port, timeout=2)
    try:
        transport.enter_raw_repl(soft_reset=False)

        def execute(code):
            out, err = transport.exec_raw(code, timeout=45)
            with (folder / 'operations.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps({'time': datetime.now(timezone.utc).isoformat(), 'code': code,
                                    'stdout': out.decode('utf-8', 'replace'), 'stderr': err.decode('utf-8', 'replace')}, ensure_ascii=False) + '\n')
            if err:
                raise RuntimeError(err.decode('utf-8', 'replace'))
            return out.decode('utf-8')

        def evaluate(expr):
            return json.loads(execute('print(json.dumps(' + expr + '))').strip())

        if args.action == 'inspect':
            code = '''import sys, os, machine, binascii, json
app = getattr(sys.modules.get('src.main'), 'active_app', None)
import calibration_limits
from src import calibration_guard
from src.command_parser import parse_ate_command, ParseError
assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
assert app is not None and app.calibration_write is not None
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
assert calibration_guard.settings is calibration_limits
assert parse_ate_command('AD_4_A_1.85').payload == ('BATT_CHG','A','1.85')
assert parse_ate_command('CAL_WRITE_BATT_CHG A').payload == ('BATT_CHG','A')
try:
    parse_ate_command('AD_4_1_1.85')
    raise AssertionError('old point accepted')
except ParseError:
    pass
from src.calibration_write import encode_ad_value
for target in calibration_guard.TARGETS:
    for point in ('A','B'):
        for suffix in ('LOWER','UPPER'):
            text = str(getattr(calibration_limits, target+'_'+point+'_'+suffix))
            assert calibration_guard.check_value(target,point,text,encode_ad_value(text)) is None
assert calibration_guard.check_value('DISCHG_I','A','0',encode_ad_value('0')) == 'RANGE'
print('BOOT_CHECK|'+json.dumps({'unique_id':binascii.hexlify(machine.unique_id()).decode(),
    'settings_rev':calibration_limits.SETTINGS_REV,'app_present':True,'idle':True,
    'calibration_enabled':app.calibration_write is not None,'boundary_checks':12,'zero_rejected':True}))
'''
            print(execute(code), flush=True)
            execute("print('CONFIG|'+json.dumps({k:getattr(sys.modules['src.config'],k) for k in ('EXTERNAL_INSTRUMENT_ENABLED','QR_HOST_ENABLED','QR_HOST_ARM_ENABLED','CALIBRATION_SAMPLE_ENABLED','ATE_RESPONSE_TERMINATOR','REPL_LOG_ENABLED','T2_AR_MS')}))")
            execute('import hashlib\ndef digest(path):\n h=hashlib.sha256()\n with open(path,"rb") as f:\n  while True:\n   b=f.read(512)\n   if not b: break\n   h.update(b)\n return binascii.hexlify(h.digest()).decode()')
            manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
            after = evaluate('{p:digest(p) for p in ' + repr(list(manifest['candidate'])) + '}')
            assert after == manifest['candidate']
            save('post_boot_hashes.json', after)
            # ハード初期化を重ねず、停止した同じアプリの常駐ループを再開する。
            transport.exec_raw_no_follow('app.run()')
            time.sleep(1)
            pending = transport.serial.read(transport.serial.in_waiting)
            (folder / 'resume_output.bin').write_bytes(pending)
            if b'Traceback' in pending:
                raise RuntimeError(pending.decode('utf-8', 'replace'))
            save('result.json', {'status':'deployed_verified_running','unique_id':EXPECTED_ID,
                                'file_count':len(after),'settings_rev':'20261127-Rev0',
                                'product_commands_sent':False,'boot_checked':True})
            print('BOOT_AND_HASH_VERIFIED; APP_LOOP_RESUMED', flush=True)
            return

        execute(CHECK)
        if args.action == 'prepare':
            paths = evaluate("['/src/'+n for n in os.listdir('/src') if not os.stat('/src/'+n)[0] & 0x4000] + ['/'+n for n in os.listdir('/') if n.endswith(('.py','.mpy')) and not os.stat('/'+n)[0] & 0x4000]")
            before = evaluate('{p:digest(p) for p in ' + repr(paths) + '}')
            for p in paths:
                data = transport.fs_readfile(p)
                assert sha(data) == before[p]
                dest = folder / 'backup' / p.lstrip('/')
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                print('BACKUP ' + p, flush=True)
            assert before == evaluate('{p:digest(p) for p in ' + repr(paths) + '}')
            candidate = {}
            for file in sorted((ROOT / 'src').glob('*.py')):
                p = '/src/' + file.name
                data = (folder / 'backup/src/config.py').read_bytes() if file.name == 'config.py' else file.read_bytes()
                compile(data, p, 'exec')
                dest = folder / 'payload' / p.lstrip('/')
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                candidate[p] = sha(data)
            for source, p in (('calibration_limits.py','/calibration_limits.py'), ('firmware/main.py','/main.py')):
                data = (ROOT / source).read_bytes()
                compile(data, p, 'exec')
                (folder / 'payload' / p.lstrip('/')).write_bytes(data)
                candidate[p] = sha(data)
            config = {}
            exec((folder / 'backup/src/config.py').read_bytes(), config)
            assert config['T2_AR_MS'] == 100
            settings = {k:config[k] for k in ('EXTERNAL_INSTRUMENT_ENABLED','QR_HOST_ENABLED','QR_HOST_ARM_ENABLED','CALIBRATION_SAMPLE_ENABLED','ATE_RESPONSE_TERMINATOR','REPL_LOG_ENABLED','T2_AR_MS')}
            save('manifest.json', {'unique_id':EXPECTED_ID,'port':args.port,'before':before,'candidate':candidate,'preserved_settings':settings})
            # 配置版のsrc・設定を優先importしてHost/Mockを再試験する。
            validate(folder)
            return

        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        assert (folder / 'prepared.json').exists()
        before, after = manifest['before'], manifest['candidate']
        assert before == evaluate('{p:digest(p) for p in ' + repr(list(before)) + '}')
        new_paths = [p for p in after if p not in before]
        execute('for p in ' + repr(new_paths) + ':\n assert not p.rsplit("/",1)[-1] in os.listdir(p.rsplit("/",1)[0] or "/")')
        stage = '/' + folder.name + '_stage'
        rollback = '/' + folder.name + '_before'
        execute('os.mkdir(' + repr(stage) + '); os.mkdir(' + repr(stage + '/src') + ')')
        for p, expected in after.items():
            data = (folder / 'payload' / p.lstrip('/')).read_bytes()
            assert sha(data) == expected
            transport.fs_writefile(stage + p, data)
            assert transport.fs_hashfile(stage + p, 'sha256').hex() == expected
            print('STAGED ' + p, flush=True)
        execute('for p in ' + repr(list(after)) + ':\n gc.collect()\n with open(' + repr(stage) + '+p,"rb") as f: compile(f.read(),p,"exec")\nprint("MICROPYTHON_COMPILE_OK")')
        execute('sys.path.insert(0,' + repr(stage) + '); sys.path.insert(0,' + repr(stage + '/src') + ''')
import calibration_limits, calibration_guard, struct
assert calibration_guard.settings is calibration_limits
for target in calibration_guard.TARGETS:
    for point in ('A','B'):
        for suffix in ('LOWER','UPPER'):
            text = str(getattr(calibration_limits,target+'_'+point+'_'+suffix))
            assert calibration_guard.check_value(target,point,text,struct.pack('>f',float(text))) is None
assert calibration_guard.check_value('DISCHG_I','A','0',struct.pack('>f',0)) == 'RANGE'
print('STAGED_GUARD_RUNTIME_OK')
''')
        # 全候補の転送・構文検査後に切替え、失敗時は元ファイルを戻す。
        ordered = [p for p in after if p != '/main.py'] + ['/main.py']
        swap = CHECK + '\nbefore=' + repr(before) + '\nafter=' + repr(after) + '\nstage=' + repr(stage) + '\nrollback=' + repr(rollback) + '\nordered=' + repr(ordered) + '''
for p in before: assert digest(p) == before[p]
for p in after: assert digest(stage+p) == after[p]
os.mkdir(rollback)
os.mkdir(rollback+'/src')
saved=[]
installed=[]
try:
    for p in ordered:
        if p in before:
            os.rename(p,rollback+p)
            saved.append(p)
        os.rename(stage+p,p)
        installed.append(p)
        assert digest(p) == after[p]
except Exception:
    for p in reversed(installed): os.rename(p,stage+p)
    for p in reversed(saved): os.rename(rollback+p,p)
    raise
print('SWAP_VERIFIED')
'''
        assert 'SWAP_VERIFIED' in execute(swap)
        for p, expected in after.items():
            data = transport.fs_readfile(p)
            assert sha(data) == expected
            dest = folder / 'readback' / p.lstrip('/')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        save('applied.json', {'file_count':len(after),'full_readback_verified':True,'rollback':rollback,'main_installed_last':True})
        transport.exec_raw_no_follow('import machine; machine.reset()')
        print('APPLIED_READBACK_VERIFIED; RESET_SUBMITTED', flush=True)
    finally:
        transport.close()


if __name__ == '__main__':
    main()
