"""親の実配置sourceを照合し、同runtime/sessionと既存周辺資源を保持してADC版へ切替。"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
BASE = [ROOT / '.venv/Scripts/python.exe', '-m', 'mpremote', 'connect', 'COM6', 'resume']
NAMES = ('calibration_acquisition.py', 'calibration_measurement.py', 'command_parser.py', 'main.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    result = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, timeout=35)
    record = {'args': [str(x) for x in args], 'code': result.returncode,
              'stdout': result.stdout.decode('utf-8', 'replace'), 'stderr': result.stderr.decode('utf-8', 'replace')}
    with (OUT / 'deployment_operations.jsonl').open('a', encoding='utf-8') as log:
        log.write(json.dumps(record, ensure_ascii=False) + '\n')
    if result.returncode:
        print(json.dumps(record, ensure_ascii=False), flush=True)
        raise RuntimeError('operation stopped; no automatic retry')
    return record['stdout']


def verify(expected):
    code = "import machine,binascii,hashlib; assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'\n"
    for path, digest in expected.items():
        code += "assert binascii.hexlify(hashlib.sha256(open(" + repr(path) + ",'rb').read()).digest()).decode()==" + repr(digest) + '\n'
    code += "print('SOURCE_HASHES_OK'," + str(len(expected)) + ')'
    print(run(BASE + ['exec', code]), flush=True)


if __name__ == '__main__':
    phase = sys.argv[1]
    manifest_path = OUT / 'deployment_manifest.json'
    if phase == 'prepare':
        assert not manifest_path.exists()
        backup = {('/src/' + p.name): sha(p) for p in (OUT / 'parent_before/src').glob('*.py')}
        assert len(backup) == 30
        verify(backup)
        package = OUT / 'candidate/src'
        package.mkdir(parents=True)
        candidates = {}
        for name in NAMES:
            source = ROOT / 'src' / name
            compile(source.read_bytes(), str(source), 'exec')
            shutil.copyfile(source, package / name)
            candidates['/src/' + name] = sha(source)
        manifest_path.write_text(json.dumps({'parent_uid': '69f7d45962cfdfad',
            'parent_nonce': 'f2caeb2e46c95f01', 'session': 'f2caeb2e46c95f01cbfa8c2c4f42c7ba',
            'before': backup, 'candidate': candidates, 'preserve_config': True,
            'host_firmware_unchanged': 'meter-host-relay-20261123.2'}, indent=2), encoding='utf-8')
        print('CANDIDATE_FIXED', len(candidates), flush=True)
    elif phase == 'deploy':
        manifest = json.loads(manifest_path.read_text())
        verify(manifest['before'])
        print(run(BASE + ['exec', "assert not app._comm_busy() and not app.external_link.busy; assert not app.logger.active and not app.logger.test_running; assert app.external_link.transport._closed; assert app.external_link.parent_nonce.hex()=='" + manifest['parent_nonce'] + "'; assert app.external_link.session.hex()=='" + manifest['session'] + "'; assert app.protocol.uart is nf_guard; print('RUNTIME_QUIESCENT')"]), flush=True)
        for path, digest in manifest['candidate'].items():
            source = OUT / 'candidate/src' / Path(path).name
            assert sha(source) == digest
            temporary = path + '.adc_new'
            run(BASE + ['fs', 'cp', source, ':' + temporary])
            run(BASE + ['exec', "import os,binascii,hashlib; p=" + repr(temporary) + "; b=open(p,'rb').read(); assert binascii.hexlify(hashlib.sha256(b).digest()).decode()==" + repr(digest) + "; compile(b,p,'exec'); os.rename(p," + repr(path) + "); os.sync()"])
            print('INSTALLED', path, flush=True)
        expected = dict(manifest['before'])
        expected.update(manifest['candidate'])
        verify(expected)
    elif phase == 'activate':
        manifest = json.loads(manifest_path.read_text())
        code = """import sys
assert not app._comm_busy() and not app.external_link.busy and not app.logger.active
adc_previous_app = app
adc_old_modules = {name:sys.modules.get(name) for name in ('src.main','src.command_parser','src.calibration_acquisition','src.calibration_measurement')}
for name in adc_old_modules:
 if name in sys.modules: del sys.modules[name]
__import__('src.main')
adc_module = sys.modules['src.main']
adc_adapter = sys.modules['src.calibration_acquisition'].Meter7355Voltage
assert adc_adapter.decode(b'+001.8500E-03\\r\\n','BATT_CHG') == ('+001.8500E+00','mV')
adc_app = adc_module.FixtureApp(ate_uart=adc_previous_app.ate_uart,nf55_uart=adc_previous_app.nf55_uart,protocol=adc_previous_app.protocol,cache=adc_previous_app.cache,logger=adc_previous_app.logger,rtc=adc_previous_app.rtc,clock=adc_previous_app.clock,external_link=adc_previous_app.external_link)
assert adc_app.external_link is adc_previous_app.external_link
assert adc_app.logger.sd_sink is adc_previous_app.logger.sd_sink
assert adc_app.protocol.uart is nf_guard
app = adc_app
print('ADC_RUNTIME_ACTIVATED',app.external_link.parent_nonce.hex(),app.external_link.session.hex(),app.logger.sd_sink.status)
"""
        print(run(BASE + ['exec', code]), flush=True)
    else:
        raise ValueError(phase)
