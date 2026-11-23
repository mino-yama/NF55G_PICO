# 正常起動済みappを再利用。D5二回と確定SS一回以外の製品送信を拒否する。
import time
import json
import binascii
import machine
from src import main as ss_main
from src.frame import build_frame
from src.qr_write_session import serial_data_from_qr

ss_app=ss_main.active_app
assert ss_app is not None and not ss_app.logger.test_running and not ss_app.logger.active
assert ss_app.qr_write.transport is not None and not ss_app._comm_busy()
ss_expected='US250A-CGXE-009491-101A1.2601000001'
ss_payload=serial_data_from_qr(ss_expected)

class SSFiniteGuard:
    def __init__(self,inner):
        self.inner=inner
        self.tx=[]
        self.rx=[]
        self.count={'SS':0,'D5':0}
    def any(self):
        return self.inner.any()
    def read(self,count=1):
        raw=self.inner.read(count)
        if raw:
            self.rx.append(raw)
        return raw
    def write(self,raw):
        raw=bytes(raw)
        if raw==build_frame('SS',ss_payload):
            key,limit='SS',1
        elif raw==build_frame('D5'):
            key,limit='D5',2
        elif raw in (b'\x06',b'\x15'):
            key=None
        else:
            raise OSError('SS_HIL_FORBIDDEN_TX')
        if key:
            if self.count[key]>=limit:
                raise OSError('SS_HIL_LIMIT')
            self.count[key]+=1
        self.tx.append(raw)
        return self.inner.write(raw)

ss_original_uart=ss_app.protocol.uart
ss_guard=SSFiniteGuard(ss_original_uart)
ss_app.protocol.uart=ss_guard
ss_sink=ss_app.logger.sd_sink
ss_write,ss_flush=ss_sink.write_record,ss_sink.flush
ss_stats={'write':0,'flush':0,'during_comm':0}
def ss_checked_write(row):
    if ss_app.protocol.busy:
        ss_stats['during_comm']+=1
        raise RuntimeError('SD write during SS/D5')
    ss_stats['write']+=1
    return ss_write(row)
def ss_checked_flush():
    if ss_app.protocol.busy:
        ss_stats['during_comm']+=1
        raise RuntimeError('SD flush during SS/D5')
    ss_stats['flush']+=1
    return ss_flush()
ss_sink.write_record,ss_sink.flush=ss_checked_write,ss_checked_flush
ss_history=len(ss_app.logger.test_history)
ss_started=time.ticks_ms()
ss_previous_state=None
ss_previous_ignored=ss_app.qr_write.ignored
ss_acquisition_ignored=ss_previous_ignored
ss_second_reported=None
ss_error=None
print('SS_HIL_READY')
try:
    while time.ticks_diff(time.ticks_ms(),ss_started)<300000:
        ss_app.service_once()
        state=ss_app.qr_write.state
        if state!=ss_previous_state:
            if state=='READING':
                ss_acquisition_ignored=ss_app.qr_write.ignored
            print('SS_HIL_STATE|'+state+'|'+str(ss_app.qr_write.token))
            ss_previous_state=state
        if ss_app.qr_write.ignored!=ss_previous_ignored:
            print('SS_HIL_IGNORED|'+str(ss_app.qr_write.ignored))
            ss_previous_ignored=ss_app.qr_write.ignored
        if state=='READY' and ss_app.qr_write.ignored>ss_acquisition_ignored and ss_second_reported!=ss_app.qr_write.token:
            print('SS_HIL_SECOND|'+ss_app.qr_write.token)
            ss_second_reported=ss_app.qr_write.token
        if len(ss_app.logger.test_history)>ss_history and not ss_app.server.has_work():
            break
        time.sleep_ms(1)
except Exception as exc:
    ss_error=repr(exc)
finally:
    ss_app.protocol.uart=ss_original_uart
    ss_sink.write_record,ss_sink.flush=ss_write,ss_flush
    ss_app.qr_write.transport.close()
    machine.Pin(9,machine.Pin.IN)
    if ss_app.external_link is not None:
        ss_app.external_link.transport.close()
    machine.Pin(12,machine.Pin.IN)
    machine.Pin(13,machine.Pin.IN)

ss_hil_result=dict(error=ss_error,nf_count=ss_guard.count,
    tx_hex=[binascii.hexlify(raw).decode() for raw in ss_guard.tx],
    rx_hex=binascii.hexlify(b''.join(ss_guard.rx)).decode(),sd_stats=ss_stats,
    drop=ss_app.logger.drop_count,queue=len(ss_app.logger.queue),
    logger_active=ss_app.logger.active,test_running=ss_app.logger.test_running,
    history=ss_app.logger.test_history[ss_history:],qr_ignored=ss_app.qr_write.ignored,
    cache={name:ss_app.cache.metadata(name) for name in ss_app.cache._entries},
    duration_ms=time.ticks_diff(time.ticks_ms(),ss_started))
if ss_app.logger.last_test_filename:
    ss_hil_result['csv_path']=ss_sink.root+'/'+ss_sink.bank+'/'+ss_app.logger.last_test_filename
ss_json=json.dumps(ss_hil_result).encode()
for ss_i in range(0,len(ss_json),64):
    print('SS_HIL_RESULT_HEX|'+binascii.hexlify(ss_json[ss_i:ss_i+64]).decode())
    time.sleep_ms(10)
print('SS_HIL_DONE')
