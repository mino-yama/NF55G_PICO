"""終了済み試行CSVを原文回収し、実機hash・SS行・NFフレームを照合する。"""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

OUT=Path(__file__).resolve().parent/'SS_HIL_01'
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from src.frame import parse_frame

target=OUT/'result.json'
result=json.loads(target.read_text(encoding='utf-8'))
assert result['status']=='SS_WRITE_READBACK_SUCCESS_CSV_PENDING'
path=result['parent']['csv_path']
base=[str(ROOT/'.venv/Scripts/python.exe'),'-m','mpremote','connect','COM6','resume']

def run(args):
    p=subprocess.run(base+args,cwd=ROOT,capture_output=True,timeout=35)
    with (OUT/'csv_export_operations.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(dict(args=args,code=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace')))+'\n')
    assert p.returncode==0,p.stderr
    return p.stdout.decode('utf-8')

code="import os,hashlib,binascii,json; assert not ss_app.logger.active and not ss_app.protocol.busy; p="+repr(path)+"; h=hashlib.sha256(); f=open(p,'rb')\nwhile True:\n b=f.read(512)\n if not b: break\n h.update(b)\nf.close(); print('SS_CSV|'+json.dumps({'path':p,'bytes':os.stat(p)[6],'sha256':binascii.hexlify(h.digest()).decode()}))"
text=run(['exec',code])
remote=json.loads(next(x.split('|',1)[1] for x in text.splitlines() if x.startswith('SS_CSV|')))
local=OUT/Path(path).name
assert not local.exists()
run(['fs','cp',':'+path,str(local)])
raw=local.read_bytes()
assert len(raw)==remote['bytes'] and hashlib.sha256(raw).hexdigest()==remote['sha256']
rows=list(csv.reader(io.StringIO(raw.decode('utf-8'))))
assert len(rows[0])==14 and all(len(row)==14 for row in rows)
records=[dict(zip(rows[0],row)) for row in rows[1:]]
write=[r for r in records if r['category']=='QR' and r['event']=='WRITE']
assert len(write)==1 and write[0]['result']=='OK' and write[0]['raw_hex']==result['verified_ss_data_hex']
transactions=[r for r in records if r['category']=='NF55' and r['event']=='TRANSACTION']
assert [r['cmd'] for r in transactions]==['D5','SS','D5']
frames=[parse_frame(bytes.fromhex(x)) for x in result['parent']['tx_hex'] if x.startswith('02')]
assert [x.cmd for x in frames]==['D5','SS','D5']
assert frames[1].data.hex()==result['verified_ss_data_hex']
shutil.copy2(target,OUT/'result_before_csv.json')
result.update(status='SS_WRITE_READBACK_SUCCESS',csv_export=dict(remote,local_file=local.name,data_rows=len(records),columns=14,hash_match=True),ss_csv_rows=1)
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(status=result['status'],csv=result['csv_export']),indent=2))
