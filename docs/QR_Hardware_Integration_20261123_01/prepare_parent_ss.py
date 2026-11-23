"""現親sourceを退避し、既存runtime設定を維持してQR/SS候補を作る。"""
import hashlib
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent/'SS_Parent_Deployment_01'
ROOT=OUT.parents[2]
OUT.mkdir(exist_ok=False)
base=[str(ROOT/'.venv/Scripts/python.exe'),'-m','mpremote','connect','COM6','resume']

def run(args):
    p=subprocess.run(base+args,cwd=ROOT,capture_output=True,timeout=35)
    with (OUT/'operations.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(dict(args=args,code=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace')))+'\n')
    assert p.returncode==0,p.stderr
    return p.stdout.decode()

text=run(['exec',"import machine,binascii,json,os; print('PREP|'+json.dumps({'id':binascii.hexlify(machine.unique_id()).decode(),'files':os.listdir('src')}))"])
info=json.loads(next(x.split('|',1)[1] for x in text.splitlines() if x.startswith('PREP|')))
assert info['id']=='69f7d45962cfdfad'
files=['src/qr_write_session.py','src/qr_reader.py','src/nf55_command.py','src/command_dispatcher.py',
       'src/command_parser.py','src/main.py','src/config.py']
before=OUT/'before';candidate=OUT/'candidate'
(before/'src').mkdir(parents=True);(candidate/'src').mkdir(parents=True)
run(['fs','cp',':main.py',str(before/'main.py')])
for file in files:
    if Path(file).name in info['files']:
        run(['fs','cp',':'+file,str(before/file)])
    raw=(ROOT/file).read_bytes()
    if file=='src/config.py':
        # 既存測定器HOST等の実機設定を保持し、QRだけを有効化する。
        raw=(before/file).read_bytes()+b'\n# QR GP9 hardware integration 2026-11-23\nQR_HOST_ENABLED = True\n'
    (candidate/file).write_bytes(raw)
manifest=dict(parent_id=info['id'],changes=[])
for file in files:
    old=before/file;new=candidate/file
    manifest['changes'].append(dict(file=file,before_sha256=hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else None,
        candidate_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),bytes=new.stat().st_size))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print((before/'main.py').read_text(encoding='utf-8'))
print('CANDIDATE_PREPARED',len(files))
