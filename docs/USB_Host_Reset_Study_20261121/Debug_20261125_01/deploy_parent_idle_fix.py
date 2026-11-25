"""Install the verified parent source with an on-device rollback copy."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from prepare_parent_idle_fix import BASE, CASE, ROOT, UID


def main(out):
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf8'))
    assert manifest['uid'] == UID and manifest['parent_matches_git_baseline']
    old = manifest['files'][0]['sha256']
    assert hashlib.sha256((out / 'main.py').read_bytes()).hexdigest() == old
    candidate = ROOT / 'src' / 'main.py'
    raw = candidate.read_bytes()
    compile(raw, str(candidate), 'exec')
    assert b'SD_RECOVERY_IDLE_MS = 250' in raw
    new = hashlib.sha256(raw).hexdigest()
    frozen = out / 'main_candidate.py'
    with frozen.open('xb') as f:
        f.write(raw)

    def run(*args):
        p = subprocess.run(BASE + list(args), cwd=ROOT, capture_output=True, timeout=40)
        with (out / 'deployment.jsonl').open('a', encoding='utf8') as log:
            log.write(json.dumps({'args': args, 'code': p.returncode,
                                  'stdout': p.stdout.decode('utf8', 'replace'),
                                  'stderr': p.stderr.decode('utf8', 'replace')}) + '\n')
        p.check_returncode()
        return p.stdout.decode('utf8')

    verify = '''import os, machine, binascii, hashlib, sys
assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(512)
            if not b: break
            h.update(b)
    return binascii.hexlify(h.digest()).decode()
assert digest('/src/main.py') == ''' + repr(old) + '''
assert 'main_idle_stage.py' not in os.listdir('/src')
assert 'main_before_sd_idle.py' not in os.listdir('/')
'''
    run('exec', verify)
    run('fs', 'cp', str(frozen), ':/src/main_idle_stage.py')
    swap = '''assert digest('/src/main.py') == ''' + repr(old) + '''
assert digest('/src/main_idle_stage.py') == ''' + repr(new) + '''
with open('/src/main_idle_stage.py', 'r') as f:
    compile(f.read(), 'main_idle_stage.py', 'exec')
import gc
gc.collect()
os.rename('/src/main.py', '/main_before_sd_idle.py')
try:
    os.rename('/src/main_idle_stage.py', '/src/main.py')
except OSError:
    os.rename('/main_before_sd_idle.py', '/src/main.py')
    raise
assert digest('/src/main.py') == ''' + repr(new) + '''
assert digest('/main_before_sd_idle.py') == ''' + repr(old) + '''
print('PARENT_SOURCE_VERIFIED')
'''
    assert 'PARENT_SOURCE_VERIFIED' in run('exec', swap)
    print(f'PARENT_SOURCE_VERIFIED {new}', flush=True)
    run('exec', 'import machine; print("PARENT_RESET_REQUESTED"); machine.reset()')


if __name__ == '__main__':
    target = (CASE / sys.argv[1]).resolve()
    assert target.parent == CASE.resolve() and target.name.startswith('parent_idle_fix_')
    main(target)
