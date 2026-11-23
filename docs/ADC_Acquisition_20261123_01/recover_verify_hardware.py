"""誤った最終assertで停止した試験の保持RAMと既存原文を照合。新規取得はしない。"""
import csv
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0,str(ROOT))
from src.external_instrument_link import FrameReader


def run(args):
    p=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,timeout=40)
    with (OUT/'recovery_operations.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'args':[str(x) for x in args],'code':p.returncode,
            'stdout':p.stdout.decode('utf-8','replace'),'stderr':p.stderr.decode('utf-8','replace')})+'\n')
    assert p.returncode==0,p.stderr
    return p.stdout.decode('utf-8')


if __name__=='__main__':
    target=OUT/'hardware_recovered_result.json'
    assert not target.exists() or json.loads(target.read_text())['status']=='ADC_HIL_RECOVERED_CSV_PENDING'
    initial=json.loads((OUT/'hardware_result.json').read_text())
    assert initial['status']=='STOPPED' and 'error' not in initial and len(initial['acquisitions'])==4
    text=(OUT/'hardware_recovered_parent.log').read_text(encoding='utf-8')
    state=json.loads(next(x.split('|',1)[1] for x in text.splitlines() if x.startswith('ADC_RECOVERED|')))
    assert state['product_cache_invalid_after_test_start']
    assert state['nf_write_attempts']==state['drop']==state['queue']==state['measurement_slots']==0
    assert state['sd_stats']['during_comm']==0 and not state['fault']
    assert not state['logger_active'] and not state['test_running']
    reader=FrameReader(); frames=reader.feed(bytes.fromhex(state['tx_hex']))
    commands=[f['payload'].decode('ascii') for f in frames if f['kind']=='Q']
    assert reader.errors==0 and commands==[':SENS:FUNC?',':READ?']*4
    assert Counter(f['kind'] for f in initial['host_frames'])==Counter({'i':1,'A':8,'T':8,'R':8})
    assert initial['host_decode_errors']==0
    for request in (f for f in frames if f['kind']=='Q'):
        replies=[f for f in initial['host_frames'] if f['request']==request['request'] and f['session']==request['session'].hex()]
        assert [f['kind'] for f in replies]==['A','T','R']
    provisional=dict(initial)
    provisional.update(status='ADC_HIL_RECOVERED_CSV_PENDING',parent=state,instrument_commands=commands,
        recovery_reason='TEST_START intentionally invalidates all product caches; original invariance assertion was wrong',
        repeated_acquisitions=0,new_instrument_requests_during_recovery=0)
    target.write_text(json.dumps(provisional,ensure_ascii=False,indent=2),encoding='utf-8')
    base=[ROOT/'.venv/Scripts/python.exe','-m','mpremote','connect','COM6','resume']
    exports=[]; acquired=[]
    for path in state['log_paths']:
        code="import os,hashlib,binascii,json; assert not app.logger.active; p="+repr(path)+"; h=hashlib.sha256(); f=open(p,'rb')\nwhile True:\n b=f.read(512)\n if not b: break\n h.update(b)\nf.close(); print('CSV|'+json.dumps({'path':p,'bytes':os.stat(p)[6],'sha256':binascii.hexlify(h.digest()).decode()}))"
        response=run(base+['exec',code])
        remote=json.loads(next(x.split('|',1)[1] for x in response.splitlines() if x.startswith('CSV|')))
        local=OUT/Path(path).name
        run(base+['fs','cp',':'+path,local])
        raw=local.read_bytes()
        assert len(raw)==remote['bytes'] and hashlib.sha256(raw).hexdigest()==remote['sha256']
        rows=list(csv.reader(io.StringIO(raw.decode('utf-8'))))
        assert len(rows[0])==14 and all(len(row)==14 for row in rows)
        records=[dict(zip(rows[0],row)) for row in rows[1:]]
        acquired.extend(r for r in records if r['category']=='CAL' and r['event']=='ACQUIRED')
        remote.update(local_file=local.name,data_rows=len(records),malformed_rows=0,hash_match=True)
        exports.append(remote)
    assert len(exports)==2 and len(acquired)==4
    for item,row in zip(initial['acquisitions'],acquired):
        assert row['result']=='OK:CAL_MEASURE:'+item['id']
        assert row['detail']==item['snapshot']
        assert bytes.fromhex(row['raw_hex'])==bytes.fromhex(item['snapshot'].split(':')[-1])
    recovered=dict(initial)
    recovered.update(status='ADC_HIL_RECOVERED_SUCCESS',parent=state,instrument_commands=commands,
        csv_exports=exports,cal_acquired_rows=4,
        recovery_reason='original parent diagnostic incorrectly required product cache invariance across TEST_START; existing TEST_START invalidates all caches',
        repeated_acquisitions=0,new_instrument_requests_during_recovery=0)
    target.write_text(json.dumps(recovered,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':recovered['status'],'csv':exports,'acquisitions':4,'commands':commands},indent=2))
