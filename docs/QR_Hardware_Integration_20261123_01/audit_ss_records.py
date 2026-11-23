"""配置元・現在ソース・実機応答・CSV・仕様追記の整合確認。SS送信なし。"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
run=OUT/'SS_HIL_01'
deployment=OUT/'SS_Parent_Deployment_01'
manifest=json.loads((deployment/'manifest.json').read_text(encoding='utf-8'))
expected={x['file']:x['candidate_sha256'] for x in manifest['changes']}
for entry in manifest['changes']:
    path=deployment/'candidate'/entry['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['candidate_sha256']
    if entry['file']!='src/config.py':
        assert hashlib.sha256((ROOT/entry['file']).read_bytes()).hexdigest()==entry['candidate_sha256']
before=(deployment/'before/src/config.py').read_text(encoding='utf-8')
after=(deployment/'candidate/src/config.py').read_text(encoding='utf-8')
assert re.findall(r'^EXTERNAL_INSTRUMENT_ENABLED\s*=\s*(True|False)',before,re.M)==re.findall(r'^EXTERNAL_INSTRUMENT_ENABLED\s*=\s*(True|False)',after,re.M)
assert after.rstrip().endswith('QR_HOST_ENABLED = True')
files=list(expected)
code="import hashlib,binascii,json; ss_audit={}\nfor p in "+repr(files)+":\n f=open(p,'rb'); h=hashlib.sha256()\n while True:\n  b=f.read(512)\n  if not b: break\n  h.update(b)\n f.close(); ss_audit[p]=binascii.hexlify(h.digest()).decode()\nprint('AUDIT|'+json.dumps(ss_audit))"
command=[str(ROOT/'.venv/Scripts/python.exe'),'-m','mpremote','connect','COM6','resume','exec',code]
p=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=35)
(OUT/'Record_Audit_Parent_Hashes.log').write_bytes(p.stdout+p.stderr)
assert p.returncode==0,p.stderr
device=json.loads(next(x.split('|',1)[1] for x in p.stdout.decode().splitlines() if x.startswith('AUDIT|')))
assert device==expected
result=json.loads((run/'result.json').read_text(encoding='utf-8'))
assert result['status']=='SS_WRITE_READBACK_SUCCESS'
assert result['parent']['nf_count']=={'SS':1,'D5':2}
assert result['parent']['drop']==result['parent']['queue']==result['parent']['sd_stats']['during_comm']==0
assert result['parent']['qr_ignored']==1
csv=run/result['csv_export']['local_file']
assert hashlib.sha256(csv.read_bytes()).hexdigest()==result['csv_export']['sha256']
comparison=json.loads((run/'readback_comparison.json').read_text(encoding='utf-8'))
assert comparison['all_bcc_valid'] and comparison['unit_expected_match'] and comparison['fw_adu_bbu_reserve_parameter_unchanged']
docs=['ATE_Command_Master.md','Cache_Master.md','QR_Reader_Requirements.md',
      'Software_Module_Interface.md','Test_Specification.md','Open_Issues.md','CHANGELOG.md']
for file in docs:
    text=(ROOT/'docs'/file).read_text(encoding='utf-8')
    assert '\ufffd' not in text
    assert 'SS_Workflow_Spec_20261123_Rev0.md' in text or 'SS_Write_Readback_Result_20261123_Rev0.md' in text
testlog=(OUT/'SS_Workflow_Final_Host_Mock_Rev0.log').read_text(encoding='utf-8')
assert 'Ran 527 tests' in testlog and 'OK' in testlog
audit=dict(status='RECORDS_AND_DEPLOYMENT_MATCH',source_files=7,
    source_snapshot_and_device_hash_match=True,runtime_config_override='QR_HOST_ENABLED=True; existing external meter setting preserved',
    documents_updated=docs,host_mock_tests=527,ss_count=1,d5_count=2,
    csv_bytes=csv.stat().st_size,csv_rows=result['csv_export']['data_rows'],csv_hash_match=True,
    ss_data_and_readback_match=True,unmodified_fields_verified=True,
    committed=False,pushed=False,
    remaining=['power-cycle persistence','QR HOST in-flight old scan/request boundary','cold-start without manual RST'])
(OUT/'Record_Audit_20261123_Rev0.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=True,indent=2))
