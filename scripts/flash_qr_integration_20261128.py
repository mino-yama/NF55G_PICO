"""既知QR HOSTだけを退避・verify後に双方向候補へ切替える。"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/QR_Production_Integration_20261128_Rev0/host_flash'
SOURCE=ROOT/'docs/REV_Read_Write_Debug_20261126/qr_arm_candidate_02'
TOOL=ROOT/'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
UID='A06FEA01012EC137'
OUT.mkdir(exist_ok=True)
assert not (OUT/'before_flash_2MB.bin').exists(), 'existing backup must not be overwritten'
def run(name,*args):
    p=subprocess.run([str(TOOL),*map(str,args),'--ser',UID],cwd=ROOT,capture_output=True,timeout=90)
    (OUT/(name+'.log')).write_bytes(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(name+': '+(p.stdout+p.stderr).decode('utf-8','replace'))
    return p.stdout.decode('utf-8','replace')
def info(name,version):
    text=run(name,'info','-a')
    assert UID.lower() in text.lower() and '2048K' in text and version in text and 'bootsel' in text.lower(),text
    return text
manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
image=SOURCE/manifest['file']
assert hashlib.sha256(image.read_bytes()).hexdigest()==manifest['sha256']
info('before','qr-fixed-20261123.1')
backup=OUT/'before_flash_2MB.bin'
run('backup','save','-a','-v',backup)
assert backup.stat().st_size==2097152
run('backup_verify','verify',backup)
(OUT/'backup.sha256').write_text(hashlib.sha256(backup.read_bytes()).hexdigest()+'\n',encoding='ascii')
try:
    run('candidate_load','load','-v',image)
    run('candidate_verify','verify',image)
    info('after',manifest['version'])
except Exception:
    run('failure_restore','load','-v',backup)
    run('failure_restore_verify','verify',backup)
    raise
(OUT/'result.json').write_text(json.dumps({'unique_id':UID,'candidate':manifest,'backup_verified':True,'flash_verified':True,'left_in_bootsel':True},indent=2),encoding='utf-8')
print('QR_HOST_BACKUP_AND_CANDIDATE_VERIFY_OK; BOOTSEL',flush=True)
