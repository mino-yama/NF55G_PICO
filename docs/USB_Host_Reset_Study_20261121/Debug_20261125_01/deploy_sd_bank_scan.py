"""Stage and verify the parent-only SD scan update with a rollback copy."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import subprocess

from prepare_parent_idle_fix import BASE, CASE, ROOT, UID


def main():
    now = datetime.now(timezone(timedelta(hours=9)))
    out = CASE / f'sd_bank_scan_deploy_{now:%Y%m%d_%H%M%S_%f}'
    out.mkdir()
    print(out, flush=True)

    def run(*args):
        proc = subprocess.run(BASE + list(args), cwd=ROOT, capture_output=True, timeout=45)
        stdout = proc.stdout.decode('utf8', 'replace')
        with (out / 'operations.jsonl').open('a', encoding='utf8') as log:
            log.write(json.dumps({'args': args, 'returncode': proc.returncode, 'stdout': stdout,
                                  'stderr': proc.stderr.decode('utf8', 'replace')}) + '\n')
        proc.check_returncode()
        return stdout

    check = f'''import binascii, gc, hashlib, machine, os, sys
assert binascii.hexlify(machine.unique_id()).decode() == {UID!r}
app = sys.modules['src.main'].active_app
logger = app.logger
assert not logger.active and not logger.test_running and not logger.recovery_pending and not app._comm_busy()
assert logger.last_test_id == 'T000320' and not app.external_link.fault
assert logger.sd_sink.status == 'OK' and logger.sd_sink.mounted
assert 'sd_sink_bank_stage.py' not in os.listdir('/src')
assert 'sd_sink_before_bank_scan.py' not in os.listdir('/')
def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            data = f.read(512)
            if not data:
                break
            h.update(data)
    return binascii.hexlify(h.digest()).decode()
print('CURRENT|' + digest('/src/sd_sink.py'))
'''
    old_hash = next(line[8:] for line in run('exec', check).splitlines() if line.startswith('CURRENT|'))
    old = out / 'sd_sink_before.py'
    run('fs', 'cp', ':/src/sd_sink.py', str(old))
    old_content = old.read_bytes()
    assert hashlib.sha256(old_content).hexdigest() == old_hash
    baseline = subprocess.check_output(['git', 'show', 'HEAD:src/sd_sink.py'], cwd=ROOT)
    assert old_content.replace(b'\r\n', b'\n') == baseline.replace(b'\r\n', b'\n')

    source = (ROOT / 'src' / 'sd_sink.py').read_bytes()
    compile(source, 'sd_sink.py', 'exec')
    new_hash = hashlib.sha256(source).hexdigest()
    assert new_hash != old_hash
    candidate = out / 'sd_sink_candidate.py'
    candidate.write_bytes(source)
    run('fs', 'cp', str(candidate), ':/src/sd_sink_bank_stage.py')
    swap = f'''assert digest('/src/sd_sink.py') == {old_hash!r}
assert digest('/src/sd_sink_bank_stage.py') == {new_hash!r}
gc.collect()
with open('/src/sd_sink_bank_stage.py') as f:
    compile(f.read(), 'sd_sink_bank_stage.py', 'exec')
gc.collect()
os.rename('/src/sd_sink.py', '/sd_sink_before_bank_scan.py')
try:
    os.rename('/src/sd_sink_bank_stage.py', '/src/sd_sink.py')
    assert digest('/src/sd_sink.py') == {new_hash!r}
except (OSError, AssertionError):
    if 'sd_sink.py' in os.listdir('/src'):
        os.rename('/src/sd_sink.py', '/src/sd_sink_bank_stage.py')
    os.rename('/sd_sink_before_bank_scan.py', '/src/sd_sink.py')
    raise
assert digest('/sd_sink_before_bank_scan.py') == {old_hash!r}
print('PARENT_SOURCE_VERIFIED')
'''
    assert 'PARENT_SOURCE_VERIFIED' in run('exec', swap)
    (out / 'manifest.json').write_text(json.dumps({'uid': UID, 'before_sha256': old_hash,
                                                   'candidate_sha256': new_hash}, indent=2), encoding='utf8')
    run('exec', '--no-follow', 'import machine; machine.reset()')
    print(f'PARENT_SOURCE_VERIFIED {new_hash}', flush=True)


if __name__ == '__main__':
    main()
