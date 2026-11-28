"""HOST未接続のGP12へ0x55連続出力。RAMだけで10分後に通常処理へ戻る。"""
import json
from pathlib import Path
import time
from mpremote.transport_serial import SerialTransport
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01/scope_pattern_01'
OUT.mkdir()
CODE=r'''
import sys,time,json
a=sys.modules['src.main'].active_app
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
assert not a.server.pending and not a.server.tx and not a.ate_uart.any()
t=a.external_link.transport
assert t.tx.active() and not t._closed
_scope_pattern_state={'running':True,'pin':12,'baud':115200,'pattern_hex':'55','duration_ms':600000,'bytes':0}
pattern=b'\x55\x55\x55\x55'
started=time.ticks_ms();last=started;sent=0
print('SCOPE_READY')
try:
    while time.ticks_diff(time.ticks_ms(),started)<600000:
        sent+=t.write(pattern)
        now=time.ticks_ms()
        if time.ticks_diff(now,last)>=1000:
            _scope_pattern_state['bytes']=sent
            a.qr_write.poll()
            last=now
finally:
    time.sleep_ms(2)
    _scope_pattern_state.update(running=False,bytes=sent,elapsed_ms=time.ticks_diff(time.ticks_ms(),started))
    print('SCOPE_STOPPED|'+json.dumps(_scope_pattern_state))
    a.run()
'''
(OUT/'parent.py').write_text(CODE,encoding='utf-8')
r=SerialTransport('COM6',timeout=2);ack=bytearray()
try:
    r.enter_raw_repl(soft_reset=False)
    r.exec_raw_no_follow(CODE)
    r.serial.timeout=.1
    until=time.monotonic()+5
    while time.monotonic()<until and b'SCOPE_READY' not in ack:
        ack.extend(r.serial.read(1))
    assert b'SCOPE_READY' in ack,ack
    record={'started':True,'pin':12,'pico_physical_pin':16,'baud':115200,'format':'8N1','pattern':'55','limit_seconds':600,'ack':ack.decode('utf-8','replace'),'firmware_files_changed':False}
    (OUT/'started.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('SCOPE_PATTERN_RUNNING; GP12; 115200 8N1; 0x55; 10 minute limit',flush=True)
except Exception:
    r.enter_raw_repl(soft_reset=False)
    r.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    raise
finally:r.close()
