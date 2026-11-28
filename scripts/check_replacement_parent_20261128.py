"""交換後の親実行中IDと保存済み37件の一致を、HOST無応答時にも確認する。"""
import json
from pathlib import Path
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01'
expected=json.loads((OUT/'parent_after_hashes.json').read_text())
uid=json.loads((OUT/'flash_result.json').read_text())['uid']
r=SerialTransport('COM6',timeout=2)
try:
    r.enter_raw_repl(soft_reset=False)
    out,err=r.exec_raw(HEADER+'\nprint(json.dumps({"hashes":{p:digest(p) for p in '+repr(list(expected))+'},"uid":app.external_link.expected_chipid,"fault":app.external_link.fault,"trial":app.logger.test_running,"busy":app._comm_busy(),"parent_nonce":binascii.hexlify(app.external_link.parent_nonce).decode()}))',timeout=45)
    (OUT/'parent_runtime.log').open('xb').write(out+b'\nSTDERR\n'+err)
    assert not err,err
    result=json.loads(out.decode().strip())
    assert result.pop('hashes')==expected
    assert result['uid']==uid and not result['trial'] and not result['busy']
    result['hashes37_match']=True
    (OUT/'parent_runtime_check.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2))
    print(json.dumps(result))
finally:
    try:r.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    finally:r.close()
