"""退避済み既知HOSTだけを一時診断版へ切替え、終了後は全Flashを復元する。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
OUT=CASE/'uart_diagnostic'
TOOL=ROOT/'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
UID='BFCF2EDB84B0B37F'
parser=argparse.ArgumentParser();parser.add_argument('action',choices=('diagnose','restore'))
parser.add_argument('--already-bootsel',action='store_true');parser.add_argument('--tag',default='')
args=parser.parse_args();assert not args.tag or args.tag.replace('_','').isalnum()
logs=OUT/(args.action+args.tag);logs.mkdir()
def run(label,*options):
    p=subprocess.run([str(TOOL),*map(str,options),'--ser',UID],capture_output=True,timeout=90)
    (logs/(label+'.log')).write_bytes(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(label+': '+(p.stdout+p.stderr).decode('utf-8','replace'))
    return p.stdout.decode('utf-8','replace')
backup=CASE/'host_backup/before_flash_2MB.bin'
saved=json.loads((CASE/'host_backup/manifest.json').read_text())
assert hashlib.sha256(backup.read_bytes()).hexdigest()==saved['sha256']
if args.action=='restore' and not args.already_bootsel:
    run('enter_bootsel','reboot','-u','-f');time.sleep(2)
for before_attempt in range(6):
    try:
        info=run('before_'+str(before_attempt),'info','-a')
        break
    except RuntimeError:
        if args.action!='restore' or before_attempt==5:raise
        time.sleep(1)
assert UID.lower() in info.lower() and '2048K' in info and 'bootsel' in info.lower()
if args.action=='diagnose':
    assert 'meter-host-relay-20261125.2' in info
    manifest=json.loads((OUT/'manifest.json').read_text())
    image=ROOT/manifest['uf2']
    assert hashlib.sha256(image.read_bytes()).hexdigest()==manifest['sha256']
else:image=backup
try:
    run('load','load','-v',image)
    run('verify','verify',image)
    after=run('after','info','-a')
    assert ('meter-host-relay-uartdiag-20261128.1' if args.action=='diagnose' else 'meter-host-relay-20261125.2') in after
except Exception:
    if args.action=='diagnose':
        run('failure_restore','load','-v',backup);run('failure_restore_verify','verify',backup)
    raise
run('reboot','reboot')
(logs/'result.json').write_text(json.dumps({'action':args.action,'uid':UID,'load_verified':True,'normal_boot_requested':True,'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest()},indent=2),encoding='utf-8')
print(args.action.upper()+'_VERIFIED_AND_BOOTED',flush=True)
