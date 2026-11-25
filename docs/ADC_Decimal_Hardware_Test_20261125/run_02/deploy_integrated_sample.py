"""Back up, stage and verify the integrated ATE code on the sample fixture."""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCES = ('config.py', 'calibration_measurement.py', 'command_parser.py', 'nf55_protocol.py', 'main.py',
           'calibration_write.py')

DEVICE_CHECK = '''import binascii, hashlib, json, machine, os, sys
assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
assert not app.logger.active and not app.logger.test_running and not app.logger.recovery_pending
assert not app._comm_busy() and app.logger.sd_sink.status == 'OK'
def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as src:
        while True:
            chunk = src.read(512)
            if not chunk:
                break
            h.update(chunk)
    return binascii.hexlify(h.digest()).decode()
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', type=Path, help='apply a previously reviewed local backup/candidate directory')
    parser.add_argument('--port', default='COM6', help='parent Pico USB maintenance port (default: COM6)')
    args = parser.parse_args()
    base = [sys.executable, '-m', 'mpremote', 'connect', args.port, 'resume']
    now = datetime.now(timezone(timedelta(hours=9)))
    out = args.apply.resolve() if args.apply else HERE / f'integrated_{now:%Y%m%d_%H%M%S_%f}'
    if out.parent != HERE or not out.name.startswith('integrated_'):
        parser.error('expected an integrated_* directory inside this run folder')
    if not args.apply:
        out.mkdir()
        (out / 'before').mkdir()
        (out / 'candidate').mkdir()
    print(out, flush=True)

    def run(*command, allow_disconnect=False):
        result = subprocess.run(base + list(command), cwd=ROOT, capture_output=True, timeout=55)
        stdout = result.stdout.decode('utf-8', 'replace')
        with (out / 'operations.jsonl').open('a', encoding='utf-8') as log:
            log.write(json.dumps({'args': command, 'returncode': result.returncode, 'stdout': stdout,
                                  'stderr': result.stderr.decode('utf-8', 'replace')}) + '\n')
        if not allow_disconnect:
            result.check_returncode()
        return stdout

    snapshot = DEVICE_CHECK + f'''
files = os.listdir('/src')
print('HASHES|' + json.dumps({{name: digest('/src/' + name) if name in files else None for name in {SOURCES!r}}}))
'''
    before = json.loads(next(line[7:] for line in run('exec', snapshot).splitlines() if line.startswith('HASHES|')))
    manifest_path = out / 'manifest.json'
    if not args.apply:
        assert all(before[name] is not None for name in SOURCES[:-1])
        candidate = {}
        for name in SOURCES:
            if before[name] is not None:
                backup = out / 'before' / name
                run('fs', 'cp', ':/src/' + name, str(backup))
                previous = backup.read_bytes()
                assert hashlib.sha256(previous).hexdigest() == before[name]
            if name == 'config.py':
                if b'CALIBRATION_SAMPLE_ENABLED' not in previous:
                    data = previous.rstrip() + b'\n\nCALIBRATION_SAMPLE_ENABLED = True\n'
                else:
                    assert b'CALIBRATION_SAMPLE_ENABLED = True' in previous
                    data = previous
            else:
                data = (ROOT / 'src' / name).read_bytes()
            compile(data, name, 'exec')
            (out / 'candidate' / name).write_bytes(data)
            candidate[name] = hashlib.sha256(data).hexdigest()
        manifest_path.write_text(json.dumps({'before': before, 'candidate': candidate}, indent=2), encoding='utf-8')
        run('exec', '--no-follow', DEVICE_CHECK + '\napp.run()')
        return

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if set(manifest['before']) != set(SOURCES) or set(manifest['candidate']) != set(SOURCES):
        raise ValueError('Staging manifest is from an older source set. Prepare a new backup and candidate.')
    assert before == manifest['before']
    suffix = out.name.removeprefix('integrated_')
    stage = '/cal_stage_' + suffix
    rollback = '/cal_before_' + suffix
    run('exec', f'import os; os.mkdir({stage!r})')
    for name, expected in manifest['candidate'].items():
        file = out / 'candidate' / name
        assert hashlib.sha256(file.read_bytes()).hexdigest() == expected
        run('fs', 'cp', str(file), ':' + stage + '/' + name)

    swap = DEVICE_CHECK + f'''
import gc
before = {before!r}
after = {manifest['candidate']!r}
stage_dir = {stage!r}
backup_dir = {rollback!r}
for name in after:
    stage = stage_dir + '/' + name
    assert digest(stage) == after[name]
    gc.collect()
    with open(stage, 'rb') as src:
        compile(src.read(), stage, 'exec')
os.mkdir(backup_dir)
saved = []
installed = []
try:
    for name in after:
        live = '/src/' + name
        if before[name] is not None:
            assert digest(live) == before[name]
            os.rename(live, backup_dir + '/' + name)
            saved.append(name)
        os.rename(stage_dir + '/' + name, live)
        installed.append(name)
        assert digest(live) == after[name]
except (AssertionError, OSError):
    for name in reversed(installed):
        os.rename('/src/' + name, stage_dir + '/' + name)
    for name in reversed(saved):
        os.rename(backup_dir + '/' + name, '/src/' + name)
    raise
print('SOURCE_VERIFIED')
'''
    assert 'SOURCE_VERIFIED' in run('exec', swap)
    run('exec', '--no-follow', 'import machine; machine.reset()', allow_disconnect=True)
    print('Source verified; reset submitted. Check ATE before running the sample.', flush=True)


if __name__ == '__main__':
    main()
