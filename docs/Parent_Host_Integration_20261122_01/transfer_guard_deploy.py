"""完成した診断候補を、対象照合・全Flash退避後に配置。BOOTSELのまま保持する。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
SOURCE = BASE / (sys.argv[1] if len(sys.argv) > 1 else 'Transfer_Guard_Candidate')
OUT = BASE / (sys.argv[2] if len(sys.argv) > 2 else 'Transfer_Guard_Deployment_01')
EXPECTED_CURRENT = sys.argv[3] if len(sys.argv) > 3 else 'meter-host-relay-20261121.1'
OUT.mkdir(exist_ok=False)
PICO = ROOT / 'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
SERIAL = 'BFCF2EDB84B0B37F'
manifest = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
uf2 = SOURCE / manifest['uf2']['file']
if hashlib.sha256(uf2.read_bytes()).hexdigest() != manifest['uf2']['sha256']:
    raise RuntimeError('candidate hash differs')
logs = []
def run(args):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, timeout=60)
    logs.append({'args': [str(x) for x in args], 'code': p.returncode,
                 'stdout': p.stdout.decode('utf-8', 'replace'), 'stderr': p.stderr.decode('utf-8', 'replace')})
    (OUT / 'operations.json').write_text(json.dumps(logs, indent=2), encoding='utf-8')
    print('OP=' + str(len(logs)) + ' code=' + str(p.returncode), flush=True)
    if p.returncode:
        raise RuntimeError('operation failed; no automatic retry')
    return logs[-1]['stdout']

before = run([PICO, 'info', '-a', '--ser', SERIAL])
if '0xbfcf2edb84b0b37f' not in before.lower() or 'bootsel' not in before:
    raise RuntimeError('target identity/mode differs')
if EXPECTED_CURRENT not in before:
    raise RuntimeError('unexpected current firmware; review before write')
(OUT / 'before_info.txt').write_text(before, encoding='utf-8')
run([PICO, 'save', '-a', '-v', OUT / 'host_flash_before.bin', '--ser', SERIAL])
backup = (OUT / 'host_flash_before.bin').read_bytes()
if len(backup) != 2097152:
    raise RuntimeError('unexpected backup size')
result = {'serial': SERIAL, 'before_flash_bytes': len(backup),
          'before_flash_sha256': hashlib.sha256(backup).hexdigest(), 'backup_verified': True,
          'candidate_sha256': manifest['uf2']['sha256'], 'candidate_version': manifest['version']}
(OUT / 'manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
run([PICO, 'load', '-v', uf2, '--ser', SERIAL])
after = run([PICO, 'info', '-a', '--ser', SERIAL])
if manifest['version'] not in after or '0xbfcf2edb84b0b37f' not in after.lower():
    raise RuntimeError('post load identity/version differs')
(OUT / 'after_info.txt').write_text(after, encoding='utf-8')
result.update({'flash_verified': True, 'post_info_verified': True, 'rebooted': False,
               'runtime_verified': False, 'final_state': 'BOOTSEL'})
(OUT / 'manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('TRANSFER_GUARD_DEPLOY_VERIFIED_BOOTSEL', flush=True)
