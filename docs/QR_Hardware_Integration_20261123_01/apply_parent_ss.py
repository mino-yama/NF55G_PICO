"""退避済みsourceの一致を確認後、候補配置・hash照合・親再起動。"""
import hashlib
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent/'SS_Parent_Deployment_01'
ROOT=OUT.parents[2]
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
base=[str(ROOT/'.venv/Scripts/python.exe'),'-m','mpremote','connect','COM6','resume']

def run(args,allow_reset=False):
    p=subprocess.run(base+args,cwd=ROOT,capture_output=True,timeout=35)
    with (OUT/'apply_operations.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(dict(args=args,code=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace')))+'\n')
    assert allow_reset or p.returncode==0,p.stderr
    return p.stdout.decode('utf-8')

files=[item['file'] for item in manifest['changes']]
code="import machine,binascii,hashlib,json,os; assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'; ss_hashes={}\nfor p in "+repr(files)+":\n try:\n  f=open(p,'rb'); h=hashlib.sha256()\n  while True:\n   b=f.read(512)\n   if not b: break\n   h.update(b)\n  f.close(); ss_hashes[p]=binascii.hexlify(h.digest()).decode()\n except OSError:\n  ss_hashes[p]=None\nprint('HASH|'+json.dumps(ss_hashes))"
def hashes():
    text=run(['exec',code])
    return json.loads(next(x.split('|',1)[1] for x in text.splitlines() if x.startswith('HASH|')))
before=hashes()
assert before=={item['file']:item['before_sha256'] for item in manifest['changes']}
for item in manifest['changes']:
    local=OUT/'candidate'/item['file']
    assert hashlib.sha256(local.read_bytes()).hexdigest()==item['candidate_sha256']
    run(['fs','cp',str(local),':'+item['file']])
after=hashes()
assert after=={item['file']:item['candidate_sha256'] for item in manifest['changes']}
(OUT/'deployed_hashes.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
print('SOURCE_DEPLOYED_HASH_MATCH',len(after),flush=True)
run(['exec','import machine; machine.reset()'],allow_reset=True)
print('PARENT_RESET_REQUESTED',flush=True)
