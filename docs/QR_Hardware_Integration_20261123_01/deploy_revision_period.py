"""ID指定・全Flash退避後のQR HOST更新。終了後はBOOTSELを保持する。"""
import hashlib
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
release=ROOT/'firmware/usb_submcu_host_probe/releases/qr-fixed-20261123.1'
tool=ROOT/'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
serial='A06FEA01012EC137'
manifest=json.loads((release/'manifest.json').read_text())
for entry in manifest['files']:
    raw=(release/entry['file']).read_bytes()
    assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],entry
dest=OUT/'Deployment_01'
dest.mkdir(exist_ok=False)

def run(name,*args):
    command=[str(tool),*[str(arg) for arg in args],'--ser',serial]
    p=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=120)
    (dest/(name+'.log')).write_bytes(p.stdout+p.stderr)
    with (dest/'operations.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(dict(args=command,returncode=p.returncode))+'\n')
    assert p.returncode==0,(name,p.stderr.decode('utf-8','replace'))
    return p.stdout.decode('utf-8','replace')

before=run('before_info','info','-a')
assert '0xa06fea01012ec137' in before.lower() and 'qr-fixed-20261114.1' in before
assert '2048K' in before and 'bootsel' in before
backup=dest/'before_flash_2MB.bin'
run('save_all_verified','save','-a','-v',backup)
raw=backup.read_bytes()
assert len(raw)==2097152
run('backup_independent_verify','verify',backup)
backup_hash=hashlib.sha256(raw).hexdigest()
(dest/'backup_hash.txt').write_text(backup_hash+'  '+backup.name+'\n',encoding='ascii')
print('BACKUP_VERIFIED',backup_hash,flush=True)
uf2=release/'usb_submcu_qr_uart_probe.uf2'
assert hashlib.sha256(uf2.read_bytes()).hexdigest()=='cadff2460cc7b1be3ca8c8882c4b120569178371d3092c1182c66eb01bae2b3e'
run('load_verified','load','-v',uf2)
run('independent_verify','verify',uf2)
after=run('after_info','info','-a')
assert '0xa06fea01012ec137' in after.lower() and 'qr-fixed-20261123.1' in after
result=dict(status='FLASH_VERIFIED_RECONNECT_PENDING',serial=serial,version='qr-fixed-20261123.1',
    backup_bytes=len(raw),backup_sha256=backup_hash,uf2_bytes=uf2.stat().st_size,
    uf2_sha256=hashlib.sha256(uf2.read_bytes()).hexdigest(),
    load_verify=True,independent_verify=True,retained_in_bootsel=True,
    power_condition='user confirmed PC-only Type_C1, external 5V/scanner/GP0 disconnected',
    post_update_qr_read_verified=False,nf55g_commands_sent=0)
(dest/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
