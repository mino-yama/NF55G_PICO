"""親の配置とGPIO/PIO現在値を読取り、配線変更前にソフト状態を保全する。"""
import json
from pathlib import Path
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
expected=json.loads((ROOT/'docs/QR_Production_Integration_20261128_Rev0/parent_after_hashes.json').read_text())
remote=SerialTransport('COM6',timeout=2)
try:
    remote.enter_raw_repl(soft_reset=False)
    def run(code):
        out,err=remote.exec_raw(code,timeout=45)
        with (OUT/'parent_config_check_operations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'code':code,'out':out.decode('utf-8','replace'),'err':err.decode('utf-8','replace')})+'\n')
        if err:raise RuntimeError(err.decode())
        return json.loads(out.decode().strip())
    remote.exec_raw(HEADER,timeout=20)
    hashes=run('print(json.dumps({p:digest(p) for p in '+repr(list(expected))+'}))')
    state=run("""e=app.external_link
t=e.transport
print(json.dumps({'hashes_checked':37,'gpio_ctrl':{str(n):machine.mem32[0x40028000+8*n+4] for n in (0,1,8,9,12,13)},'pio1_ctrl':machine.mem32[0x50300000],'tx_active':t.tx.active(),'rx_active':t.rx.active(),'tx_fifo':t.tx.tx_fifo(),'rx_fifo':t.rx.rx_fifo(),'parent_nonce':binascii.hexlify(e.parent_nonce).decode(),'closed':t._closed,'fault':e.fault,'management':e._management,'pending':app._external_pending,'calibration_pending':app._calibration_pending,'transport_shared':app.calibration_acquisition.link is e,'expected_chipid':e.expected_chipid}))
""")
    state['hashes_match']=hashes==expected
    state['hash_differences']=[p for p in expected if hashes.get(p)!=expected[p]]
    (OUT/'parent_config_check.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
    (OUT/'parent_verified_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps(state))
finally:
    try:remote.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    finally:remote.close()
