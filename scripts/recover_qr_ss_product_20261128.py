"""保存済み開始値とD5を照合し、UNIT3欄だけを元へ戻す。"""
import json
from pathlib import Path
from mpremote.transport_serial import SerialTransport

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/QR_Production_Integration_20261128_Rev0/product_01'
baseline=json.loads((OUT/'baseline.json').read_text())['data']
code=r'''
import sys,json,binascii
from src.frame import build_frame
a=sys.modules['src.main'].active_app
p=a.protocol
def hx(v):return binascii.hexlify(v).decode()
saved=binascii.unhexlify(BASELINE)
restore=b'F'*6+saved[6:20]+b'F'*30
original=p.uart
class Guard:
    def __init__(self):self.sent=False;self.wire=[]
    def any(self):return original.any()
    def read(self,n=1):
        v=original.read(n)
        if v:self.wire.append(['RX',hx(v)])
        return v
    def write(self,v):
        raw=bytes(v)
        if raw not in (b'\x06',b'\x15',build_frame('D5',b'')):
            assert not self.sent and raw==build_frame('SS',restore)
            self.sent=True
        self.wire.append(['TX',hx(raw)])
        return original.write(v)
g=Guard();p.uart=g
def d5():
    a.execute_ate_line('INFO_REFRESH');t=p.last_result
    assert t.ok and not t.ambiguous and t.cmd=='D5' and len(t.response_data)==100
    return t.response_data
try:
    before=d5()
    print('RECOVERY|'+json.dumps({'event':'BEFORE','data':hx(before)}))
    assert before[:6]+before[20:]==saved[:6]+saved[20:],'other fields differ'
    if before[6:20]!=saved[6:20]:
        t=p.transact('SS',restore,t2_ms=100,expected_length=0,allow_command_retry=False)
        print('RECOVERY|'+json.dumps({'event':'RESTORE_SS','ok':t.ok,'ambiguous':t.ambiguous}))
        assert t.ok and not t.ambiguous
    after=d5()
    print('RECOVERY|'+json.dumps({'event':'RESTORED','exact':after==saved,'data':hx(after),'wire':g.wire}))
    assert after==saved
finally:
    p.uart=original
    if a.logger.test_running:print('END|'+a.execute_ate_line('TEST_END'))
    print('DROP|'+str(a.logger.drop_count))
'''
remote=SerialTransport('COM6',timeout=2)
try:
    remote.enter_raw_repl(soft_reset=False)
    out,err=remote.exec_raw('BASELINE='+repr(baseline)+'\n'+code,timeout=45)
    (OUT/'recovery_wire.log').write_bytes(out+b'\nSTDERR\n'+err)
    print(out.decode('utf-8','replace'))
    if err:raise RuntimeError(err.decode())
finally:
    try:remote.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    finally:remote.close()
