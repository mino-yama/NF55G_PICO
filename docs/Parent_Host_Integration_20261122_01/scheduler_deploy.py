"""Scheduler単一moduleを、実機原本・全Flash退避とSHA照合後に配置する。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE_OUT = Path(__file__).resolve().parent
OUT = BASE_OUT / 'Scheduler_Fix_01'
OUT.mkdir(exist_ok=False)
PY = ROOT / '.venv/Scripts/python.exe'
PICO = ROOT / 'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
BASE = [str(PY), '-m', 'mpremote', 'connect', 'COM6', 'resume']
UID = '69f7d45962cfdfad'
logs = []
def sha(b):
    return hashlib.sha256(b).hexdigest()
def run(args, disconnect=False):
    try:
        p = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True, timeout=50)
        row = {'args': [str(a) for a in args], 'code': p.returncode,
               'stdout': p.stdout.decode('utf-8', 'replace'), 'stderr': p.stderr.decode('utf-8', 'replace')}
    except subprocess.TimeoutExpired as exc:
        row = {'args': [str(a) for a in args], 'code': 'timeout',
               'stdout': (exc.stdout or b'').decode('utf-8', 'replace'), 'stderr': str(exc)}
    logs.append(row)
    (OUT / 'operations.json').write_text(json.dumps(logs, indent=2), encoding='utf-8')
    print('OP=' + str(len(logs)) + ' code=' + str(row['code']), flush=True)
    if row['code'] != 0 and not disconnect:
        raise RuntimeError('operation failed; no automatic retry')
    return row['stdout']
def probe():
    text = run(BASE + ['exec', "import machine,binascii,hashlib,json; b=open('src/main.py','rb').read(); print('SNAP|'+json.dumps({'uid':binascii.hexlify(machine.unique_id()).decode(),'sha256':binascii.hexlify(hashlib.sha256(b).digest()).decode(),'size':len(b)}))"])
    value = json.loads(next(x.split('SNAP|')[1] for x in text.splitlines() if x.startswith('SNAP|')))
    if value['uid'] != UID:
        raise RuntimeError('wrong parent')
    return value

before = probe()
backup = (BASE_OUT / 'main_before_scheduler_fix.py').read_bytes()
if before['sha256'] != sha(backup):
    raise RuntimeError('saved source backup differs')
(OUT / 'main_before.py').write_bytes(backup)
candidate = (ROOT / 'src/main.py').read_bytes()
(OUT / 'main_candidate.py').write_bytes(candidate)
run(BASE + ['exec', 'import machine; machine.bootloader()'], disconnect=True)
time.sleep(2)
info = run([PICO, 'info', '-a', '--ser', UID.upper()])
if '0x' + UID not in info.lower() or 'bootsel' not in info:
    raise RuntimeError('bootsel identity mismatch')
run([PICO, 'save', '-a', '-v', OUT / 'parent_flash_before.bin', '--ser', UID.upper()])
flash = (OUT / 'parent_flash_before.bin').read_bytes()
manifest = {'uid': UID, 'before': before, 'candidate_sha256': sha(candidate),
            'flash_backup_bytes': len(flash), 'flash_backup_sha256': sha(flash), 'flash_verify': True}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
run([PICO, 'reboot', '--ser', UID.upper()])
time.sleep(3)
if probe() != before:
    raise RuntimeError('source changed before deploy')
run(BASE + ['fs', 'cp', OUT / 'main_candidate.py', ':src/main.new'])
run(BASE + ['exec', "import binascii,hashlib,os; b=open('src/main.new','rb').read(); assert binascii.hexlify(hashlib.sha256(b).digest()).decode()=='" + sha(candidate) + "'; compile(b,'src/main.py','exec'); os.rename('src/main.new','src/main.py'); os.sync(); print('INSTALL_OK')"])
if probe()['sha256'] != sha(candidate):
    raise RuntimeError('post deploy mismatch')
run(BASE + ['exec', 'import machine; machine.reset()'], disconnect=True)
time.sleep(3)
after = probe()
if after['sha256'] != sha(candidate):
    raise RuntimeError('post reboot mismatch')
manifest['after_reboot'] = after
manifest['compile_ok'] = True
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('SCHEDULER_DEPLOY_VERIFIED_REPL_STOPPED', flush=True)
