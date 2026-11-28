"""実機configのQR双方向受付だけを有効化。旧設定退避と全体hash照合を行う。"""
import hashlib
import json
from pathlib import Path
import re
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/QR_Production_Integration_20261128_Rev0'
before=json.loads((ROOT/'docs/RTC_Fallback_Log_Deployment_20261128_Rev0/final_hashes.json').read_text(encoding='utf-8'))
remote=SerialTransport('COM6',timeout=2)
try:
    remote.enter_raw_repl(soft_reset=False)
    def execute(code):
        out,err=remote.exec_raw(code,timeout=45)
        with (OUT/'parent_config_operations.jsonl').open('a',encoding='utf-8') as log:log.write(json.dumps({'code':code,'stdout':out.decode('utf-8','replace'),'stderr':err.decode('utf-8','replace')})+'\n')
        if err:raise RuntimeError(err.decode())
        return out.decode()
    execute(HEADER)
    actual=json.loads(execute('print(json.dumps({p:digest(p) for p in '+repr(list(before))+'}))').strip())
    assert actual==before
    data=remote.fs_readfile('/src/config.py')
    backup=OUT/'parent_config_before.py'
    assert not backup.exists()
    assert hashlib.sha256(data).hexdigest()==before['/src/config.py'];backup.write_bytes(data)
    updated,count=re.subn(rb'(?m)^QR_HOST_ARM_ENABLED = False\r?$',b'QR_HOST_ARM_ENABLED = True',data)
    assert count==1
    oldns={};newns={};exec(data,oldns);exec(updated,newns)
    assert {k for k in oldns if not k.startswith('__') and oldns[k]!=newns[k]}=={'QR_HOST_ARM_ENABLED'}
    assert newns['QR_HOST_ENABLED'] and newns['ATE_RESPONSE_TERMINATOR']=='CR'
    (OUT/'parent_config_candidate.py').write_bytes(updated)
    expected=hashlib.sha256(updated).hexdigest()
    remote.fs_writefile('/qr_arm_config_stage_20261128.py',updated)
    execute("with open('/qr_arm_config_stage_20261128.py','rb') as f: compile(f.read(),'config.py','exec')")
    execute("assert maybe_digest('/qr_config_before_20261128.py') is None\nassert digest('/src/config.py')=="+repr(before['/src/config.py'])+"\nassert digest('/qr_arm_config_stage_20261128.py')=="+repr(expected)+"\nos.rename('/src/config.py','/qr_config_before_20261128.py')\ntry:os.rename('/qr_arm_config_stage_20261128.py','/src/config.py')\nexcept Exception:\n os.rename('/qr_config_before_20261128.py','/src/config.py')\n raise")
    readback=remote.fs_readfile('/src/config.py');assert readback==updated
    (OUT/'parent_config_readback.py').write_bytes(readback)
    after=dict(before);after['/src/config.py']=expected
    actual=json.loads(execute('print(json.dumps({p:digest(p) for p in '+repr(list(after))+'}))').strip())
    assert actual==after
    (OUT/'parent_after_hashes.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
    remote.exec_raw_no_follow('import machine;machine.reset()')
    print('QR_ARM_ENABLED; ONE_FLAG_CHANGED; 37_HASHES_VERIFIED; RESET_SUBMITTED',flush=True)
finally:remote.close()
