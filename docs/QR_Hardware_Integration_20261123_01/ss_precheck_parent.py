# 書込み前の読取専用退避。SS等の変更コマンドはこの経路で拒否する。
import machine
import binascii
import json
from src.nf55_uart import create_nf55_uart
from src.nf55_protocol import NF55Protocol
from src.nf55_decode import decode_manufacturing
from src.frame import build_frame

assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'
assert globals().get('app') is None, 'unexpected active test context'

class SSPrecheckReadOnly:
    def __init__(self, inner):
        self.inner=inner
        self.tx=[]
        self.rx=[]
    def any(self):
        return self.inner.any()
    def read(self,count=1):
        raw=self.inner.read(count)
        if raw:
            self.rx.append(raw)
        return raw
    def write(self,raw):
        raw=bytes(raw)
        assert raw in (build_frame('D5'),b'\x06',b'\x15'), 'read-only D5 guard'
        self.tx.append(raw)
        return self.inner.write(raw)

ss_precheck_uart=SSPrecheckReadOnly(create_nf55_uart())
ss_precheck_protocol=NF55Protocol(ss_precheck_uart)
ss_precheck_result=ss_precheck_protocol.transact('D5',t2_ms=100,expected_length=100)
ss_precheck_data={key:getattr(ss_precheck_result,key) for key in (
    'ok','cmd','error','nak_reason','command_retry_count','response_retry_count','ambiguous','elapsed_ms')}
ss_precheck_data.update(
    response_data_hex=binascii.hexlify(ss_precheck_result.response_data).decode(),
    raw_response_hex=binascii.hexlify(ss_precheck_result.raw_response).decode(),
    tx_hex=[binascii.hexlify(x).decode() for x in ss_precheck_uart.tx],
    rx_hex=binascii.hexlify(b''.join(ss_precheck_uart.rx)).decode(),
    ss_commands_sent=0,fu_commands_sent=0)
if ss_precheck_result.ok:
    ss_precheck_data['manufacturing']=decode_manufacturing(ss_precheck_result.response_data[:50])
print('SS_PRECHECK_RESULT|'+json.dumps(ss_precheck_data))
