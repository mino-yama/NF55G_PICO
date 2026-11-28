"""SS実機試験のSDログ、最終D5、配置ハッシュを独立照合する。"""
import csv
import hashlib
import io
import json
from pathlib import Path
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/QR_Production_Integration_20261128_Rev0'
OUT=CASE/'product_02'
expected=json.loads((CASE/'parent_after_hashes.json').read_text())
baseline=json.loads((OUT/'baseline.json').read_text())['data']
events=json.loads((OUT/'execute_events.json').read_text())
saved=bytes.fromhex(baseline)
ss=next(e for e in events if e['event']=='TRANSACTION' and e['cmd']=='SS')
d5=next(e for e in events if e['event']=='TRANSACTION' and e['cmd']=='D5')
assert ss['ok'] and not ss['ambiguous'] and not ss['command_retry']
data=bytes.fromhex(d5['data'])
assert data==saved[:6]+b'A03 2601000002'+saved[20:]
assert any(e['event']=='RESTORE' and e['exact'] for e in events)
remote=SerialTransport('COM6',timeout=2)
try:
    remote.enter_raw_repl(soft_reset=False)
    def execute(code):
        out,err=remote.exec_raw(code,timeout=45)
        with (OUT/'final_operations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'code':code,'out':out.decode('utf-8','replace'),'err':err.decode('utf-8','replace')})+'\n')
        if err:raise RuntimeError(err.decode())
        return out.decode()
    execute(HEADER)
    actual=json.loads(execute('print(json.dumps({p:digest(p) for p in '+repr(list(expected))+'}))').strip())
    assert actual==expected
    code="""app.execute_ate_line('INFO_REFRESH')
t=app.protocol.last_result
assert t.ok and not t.ambiguous and len(t.response_data)==100
print(json.dumps({'data':binascii.hexlify(t.response_data).decode(),'file':app.logger.sd_sink.open_filename,'drop':app.logger.drop_count,'check':app.execute_ate_line('PICO_SELF_CHECK?'),'busy':app._comm_busy(),'active':app.logger.test_running}))
"""
    status=json.loads(execute(code).strip())
    assert status['data']==baseline and status['drop']==0 and not status['busy'] and not status['active']
    assert status['check'].startswith('OK:'),status
    name=status['file'];assert Path(name).name.startswith('000002_')
    h=execute('print(digest('+repr(name)+'))').strip()
    raw=remote.fs_readfile(name);assert hashlib.sha256(raw).hexdigest()==h
    (OUT/Path(name).name).write_bytes(raw)
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    assert all(None not in r and len(r)==14 for r in rows)
    qr=[r for r in rows if r['category']=='QR' and r['event']=='RECEIVED']
    assert len(qr)==1 and qr[0]['detail']=='US250A-CGXE-009491-101A032601000002'
    ssrows=[r for r in rows if r['category']=='NF55' and r['direction']=='TX' and r['raw_hex'].startswith('025353')]
    assert len(ssrows)==1
    assert sum(r['event']=='TRIAL_START' for r in rows)==1 and sum(r['event']=='TRIAL_END_REQUEST' for r in rows)==1
    summary={'status':status,'firmware37_match':True,'sd_pc_sha256':h,'csv':Path(name).name,'csv_rows':len(rows),'columns':14,'ss_frames':len(ssrows),'written_unit':data[6:20].decode(),'other86_bytes_unchanged':True,'final100_bytes_restored':True,'result':'OK'}
    (OUT/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
finally:
    try:remote.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    finally:remote.close()
