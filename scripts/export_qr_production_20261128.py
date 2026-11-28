"""終了済みQR統合試験の実SD CSVをハッシュ付きで回収・照合する。"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/QR_Production_Integration_20261128_Rev0'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');a=p.parse_args()
    out=CASE/a.run;assert out.is_dir() and out.parent==CASE
    result=json.loads((out/'result.json').read_text(encoding='utf-8'))
    sets=json.loads((out/'sets.json').read_text(encoding='utf-8'))
    expected=json.loads((CASE/'parent_after_hashes.json').read_text(encoding='utf-8'))
    remote=SerialTransport('COM6',timeout=2)
    try:
        remote.enter_raw_repl(soft_reset=False)
        def execute(code):
            stdout,stderr=remote.exec_raw(code,timeout=45)
            with (out/'export_operations.jsonl').open('a',encoding='utf-8') as log:log.write(json.dumps({'code':code,'stdout':stdout.decode('utf-8','replace'),'stderr':stderr.decode('utf-8','replace')})+'\n')
            if stderr:raise RuntimeError(stderr.decode())
            return stdout.decode()
        execute(HEADER)
        actual=json.loads(execute('print(json.dumps({p:digest(p) for p in '+repr(list(expected))+'}))').strip())
        assert actual==expected
        hashes=json.loads(execute('root='+repr(result['sd_root'])+"\npaths=[root+'/'+b+'/'+n for b in ('BANK_A','BANK_B') for n in os.listdir(root+'/'+b) if n.endswith('.csv')]\nprint(json.dumps({p:digest(p) for p in paths}))").strip())
        assert len(hashes)==result['expected']
        (out/'csv').mkdir()
        summaries=[]
        for name,h in hashes.items():
            data=remote.fs_readfile(name);assert hashlib.sha256(data).hexdigest()==h
            dest=out/'csv'/Path(name).name;dest.write_bytes(data)
            assert dest.name.startswith('000002_'),dest
            with dest.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
            assert all(None not in r and len(r)==14 for r in rows)
            assert sum(r['event']=='TRIAL_START' for r in rows)==1
            assert sum(r['event']=='TRIAL_END_REQUEST' for r in rows)==1
            accepted=[r for r in rows if r['category']=='QR' and r['event']=='RECEIVED']
            assert len(accepted)==1 and accepted[0]['detail']=='US250A-CGXE-009491-101A032601000002'
            assert not any(r['category']=='NF55' and r['direction']=='TX' for r in rows)
            summaries.append({'file':dest.name,'sha256':h,'rows':len(rows),'columns':14,'accepted_B_only':True})
        (out/'csv_verification.json').write_text(json.dumps({'files':summaries,'sets':len(sets),'sd_pc_hashes_match':True,'result':'OK'},indent=2),encoding='utf-8')
        print('CSV_VERIFIED '+a.run+' '+str(len(summaries)),flush=True)
    finally:
        try:remote.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
        finally:remote.close()


if __name__=='__main__':main()
