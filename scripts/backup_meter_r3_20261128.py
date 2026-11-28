"""既知測定器HOSTの全Flashを退避・照合する。書込みは行わない。"""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_backup'
OUT.mkdir()
TOOL=ROOT/'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
UID='BFCF2EDB84B0B37F'
def run(label,*args):
    p=subprocess.run([str(TOOL),*map(str,args),'--ser',UID],capture_output=True,timeout=90)
    (OUT/(label+'.log')).write_bytes(p.stdout+p.stderr)
    assert p.returncode==0,(label,p.stdout,p.stderr)
    return p.stdout.decode('utf-8','replace')
info=run('info','info','-a')
assert UID.lower() in info.lower() and 'meter-host-relay-20261125.2' in info and '2048K' in info
backup=OUT/'before_flash_2MB.bin'
run('save','save','-a','-v',backup)
assert backup.stat().st_size==2097152
run('verify','verify',backup)
manifest={'uid':UID,'version':'meter-host-relay-20261125.2','size':backup.stat().st_size,'sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'independent_verify':True,'flash_write_performed':False}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest))
