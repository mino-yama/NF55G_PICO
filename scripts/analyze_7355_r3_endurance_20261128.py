"""保存済みATEログだけから進捗・応答時間・READ原文と終了条件を集計する。"""
import argparse
from collections import Counter
from datetime import datetime,timedelta
from decimal import Decimal
import json
from pathlib import Path
from statistics import median
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--progress',action='store_true');args=p.parse_args()
assert args.run.replace('_','').isalnum()
out=CASE/args.run;rows=[]
for line in (out/'ate.jsonl').read_text(encoding='utf-8').splitlines():
    try:rows.append(json.loads(line))
    except json.JSONDecodeError:
        if not args.progress:raise
trial=[r for r in rows if r['trial']>0]
done=[r for r in trial if r['command']=='COMM_STATUS?' and r['reply']=='OK:state=IDLE']
reads=[r for r in trial if r['command']=='EXT_QUERY 10000 MD?']
errors=[r for r in trial if r['command']=='EXT_QUERY 2500 ERR?']
def payload(r):
    f=r['reply'].split(':',3);assert f[:2]==['OK','EXT_RX'] and len(f)==4
    b=bytes.fromhex(f[3]);assert len(b)==int(f[2]) and b.endswith(b'\r\n')
    return b[:-2].decode('ascii')
values=[Decimal(payload(r))*1000 for r in reads]
starts=[r for r in trial if r['command']=='TEST_START']
intervals=[]
ends={r['trial']:r for r in done}
for r in starts:
    prev=ends.get(r['trial']-1)
    if prev:
        delta=datetime.fromisoformat(r['at'])-(datetime.fromisoformat(prev['at'])+timedelta(milliseconds=prev['elapsed_ms']))
        intervals.append(delta.total_seconds())
frames=[f for r in rows for f in r.get('host_frames',[])]
def timing(selected):
    times=[r['elapsed_ms'] for r in selected]
    return {'min_ms':min(times),'median_ms':median(times),'max_ms':max(times)} if times else None
summary={'completed_trials':len(done),'read_responses':len(reads),'read_min_mV':str(min(values)) if values else None,
         'read_max_mV':str(max(values)) if values else None,'test_start':timing(starts),'read_timing':timing(reads),
         'max_ate_ms':max(r['elapsed_ms'] for r in rows),'meter_errors':dict(Counter(payload(r) for r in errors)),
         'host_frame_kinds':dict(Counter(f['kind'] for f in frames)),
         'session_values':sorted(set(f['session'] for f in frames)),
         'drop_values':sorted(set(r['reply'] for r in trial if r['command']=='LOG_DROP_COUNT?')),
         'sd_values':sorted(set(r['reply'] for r in trial if r['command']=='SD_STATUS?')),
         'inter_trial_min_seconds':min(intervals) if intervals else None,'inter_trial_max_seconds':max(intervals) if intervals else None}
if not args.progress:
    result=json.loads((out/'result.json').read_text())
    assert result['status']=='TRIALS_COMPLETE_CSV_PENDING' and len(done)==result['planned_trials']==400
    assert len(reads)==len(errors)==400 and summary['drop_values']==['0'] and summary['sd_values']==['OK']
    assert summary['host_frame_kinds'].get('E',0)==0 and len(summary['session_values'])==1
    assert len(intervals)==399 and min(intervals)>=result['inter_trial_delay_seconds']
    summary['result']=result
    (out/'analysis.json').open('x',encoding='utf-8').write(json.dumps(summary,indent=2))
print(json.dumps(summary,ensure_ascii=False))
