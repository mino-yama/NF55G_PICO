"""交換HOSTの通常ATE情報応答、7355 IDN、親のID設定と37件SHAを照合する。"""
import json
import argparse
from contextlib import ExitStack
from types import SimpleNamespace
from pathlib import Path
import time
import serial
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01'
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
assert args.run.replace('_','').isalnum()
OUT=BASE/args.run;OUT.mkdir()
saved=json.loads((BASE/'flash_result.json').read_text());uid=saved['uid']
ops=[];capture=bytearray();result={'uid':uid,'status':'STOPPED','firmware_verified':True}
try:
    with ExitStack() as stack:
        ate=stack.enter_context(serial.Serial('COM7',57600,timeout=.1))
        try:
            monitor=stack.enter_context(serial.Serial('COM23',115200,timeout=.05))
            result['monitor_connected']=True
        except serial.SerialException as exc:
            monitor=SimpleNamespace(read_all=lambda:b'')
            result['monitor_connected']=False
            result['monitor_note']=str(exc)
        assert not ate.in_waiting
        capture.extend(monitor.read_all())
        def ask(cmd):
            start=time.monotonic();ate.write(cmd.encode()+b'\r');ate.flush();raw=bytearray()
            while time.monotonic()-start<12:
                b=ate.read(1);raw.extend(b)
                if b==b'\r':break
            capture.extend(monitor.read_all())
            reply=raw.decode('ascii','replace').rstrip('\r')
            ops.append({'command':cmd,'reply':reply,'raw_hex':raw.hex(),'elapsed_ms':round(1000*(time.monotonic()-start))})
            assert raw.endswith(b'\r'),ops[-1]
            time.sleep(.1);return reply
        assert ask('*IDN?')=='NF55G_PICO_FIXTURE,Rev.0'
        assert ask('COMM_STATUS?')=='OK:state=IDLE'
        assert ask('SD_STATUS?')=='OK';result['drop_before']=ask('LOG_DROP_COUNT?')
        host=ask('HOST_INFO? METER');result['host_info']=host
        assert host.startswith('OK:HOST_INFO:'+uid+':meter-host-relay-20261125.2:') and host.endswith(':READY'),host
        reply=ask('EXT_QUERY 2500 *IDN?');parts=reply.split(':',3)
        assert parts[:2]==['OK','EXT_RX'] and len(parts)==4,reply
        raw=bytes.fromhex(parts[3]);assert len(raw)==int(parts[2])
        assert raw==b'ADC Corp.,7355,246410099,  A02\r\n',raw
        result['meter_idn']=raw.decode()
        assert ask('HOST_INFO? METER')==host
        assert ask('COMM_STATUS?')=='OK:state=IDLE'
        assert ask('SD_STATUS?')=='OK'
        assert ask('LOG_DROP_COUNT?')==result['drop_before']
        result['self_check']=ask('PICO_SELF_CHECK?')
    expected=json.loads((BASE/'parent_after_hashes.json').read_text())
    remote=SerialTransport('COM6',timeout=2)
    try:
        remote.enter_raw_repl(soft_reset=False)
        out,err=remote.exec_raw(HEADER+'\nprint(json.dumps({"hashes":{p:digest(p) for p in '+repr(list(expected))+'},"expected_chipid":app.external_link.expected_chipid,"fault":app.external_link.fault}))',timeout=45)
        (OUT/'parent_final_check.log').write_bytes(out+b'\nSTDERR\n'+err)
        assert not err,err
        state=json.loads(out.decode().strip());assert state['hashes']==expected
        assert state['expected_chipid']==uid and not state['fault']
        result.update(status='OK',parent37_verified=True,active_new_id_verified=True)
    finally:
        try:remote.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
        finally:remote.close()
except Exception as exc:result['error']=repr(exc)
finally:
    (OUT/'normal_ate.json').open('x',encoding='utf-8').write(json.dumps(ops,indent=2))
    (OUT/'normal_monitor.raw').open('xb').write(capture)
    (OUT/'verification.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='OK' else 1)
