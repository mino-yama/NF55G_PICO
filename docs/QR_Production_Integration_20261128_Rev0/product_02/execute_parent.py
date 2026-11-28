expected='53312e31344230303031303030313030303030313030303030303030303030303030303030303030303030303030303030303130323030304630463332313332343234303030343135303535353530323637303030303030303030303030303030303030'
target=b'FFFFFFA03 2601000002FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'

import sys,time,json,binascii,machine
from src.frame import build_frame
app=sys.modules['src.main'].active_app
assert binascii.hexlify(machine.unique_id())==b'69f7d45962cfdfad'
assert not app.logger.test_running and not app.logger.active and not app._comm_busy()
assert app.logger.sd_status=='OK' and app.qr_write.arm_host
protocol=app.protocol
assert protocol is not None
def hx(v):return binascii.hexlify(v).decode()
def emit(event,**values):print('\nPRODUCT|'+json.dumps(dict(event=event,**values)))
class Guard:
    def __init__(self,inner):self.inner=inner;self.writes=0;self.restore=None;self.mode='READ';self.wire=[]
    def any(self):return self.inner.any()
    def read(self,n=1):
        v=self.inner.read(n)
        if v:self.wire.append(['RX',hx(v)])
        return v
    def write(self,data):
        data=bytes(data)
        if data not in (b'\x06',b'\x15',build_frame('D5',b'')):
            allowed=target if self.mode=='WRITE' else self.restore if self.mode=='RESTORE' else None
            if allowed is None or data!=build_frame('SS',allowed):raise OSError('command outside D5/UNIT SS guard')
            self.mode='READ';self.writes+=1
        self.wire.append(['TX',hx(data)])
        return self.inner.write(data)
original=protocol.uart
guard=Guard(original)
protocol.uart=guard
baseline=None
def result(event):
    tx=protocol.last_result
    emit(event,cmd=tx.cmd,ok=tx.ok,error=tx.error,ambiguous=tx.ambiguous,
         data=hx(tx.response_data),raw=hx(tx.raw_response),wire=guard.wire,
         command_retry=tx.command_retry_count,response_retry=tx.response_retry_count)
    guard.wire=[]
    return tx
def d5(event):
    reply=app.execute_ate_line('INFO_REFRESH');tx=result(event)
    assert tx.cmd=='D5' and tx.ok and len(tx.response_data)==100,reply
    return tx.response_data
try:
    baseline=d5('BASELINE')
    if expected is not None:
        assert hx(baseline)==expected,'product changed after baseline backup'
        guard.restore=b'F'*6+baseline[6:20]+b'F'*30
        assert len(target)==50 and target[:6]==b'F'*6 and target[20:]==b'F'*30
        guard.mode='WRITE'
        emit('READY',baseline=hx(baseline))
        previous=protocol.last_result
        began=False;started=time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(),started)<180000:
            app.service_once()
            if protocol.last_result is not previous:
                previous=protocol.last_result;result('TRANSACTION')
            if app.logger.test_running:began=True
            if began and not app.logger.test_running:break
            time.sleep_ms(1)
        assert began and not app.logger.test_running,'trial did not finish within bound'
finally:
    try:
        if baseline is not None and guard.writes:
            before=d5('BEFORE_RESTORE')
            if before[6:20]!=baseline[6:20]:
                guard.mode='RESTORE'
                protocol.transact('SS',guard.restore,t2_ms=100,expected_length=0,allow_command_retry=False)
                tx=result('RESTORE_SS')
                assert tx.ok and not tx.ambiguous,'restore SS failed'
            after=d5('RESTORED_D5')
            emit('RESTORE',exact=after==baseline,baseline=hx(baseline),actual=hx(after))
            assert after==baseline,'D5 restoration mismatch'
    finally:
        protocol.uart=original
        if app.logger.test_running:emit('END',reply=app.execute_ate_line('TEST_END'))
        emit('FINISHED',writes=guard.writes,drop=app.logger.drop_count)
