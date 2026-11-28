"""400件CSVのPC実ファイルSHAと、回収後の通常待機・R3・配置を最終確認する。"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import serial
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER
ROOT=Path(__file__).resolve().parents[1];CASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args();assert args.run.replace('_','').isalnum()
out=CASE/args.run
analysis=json.loads((out/'analysis.json').read_text());assert analysis['completed_trials']==400
exports=[d for d in sorted(out.glob('csv_export_*')) if (d/'csv_manifest.json').exists()
         and json.loads((d/'csv_manifest.json').read_text()).get('complete')
         and json.loads((d/'csv_manifest.json').read_text()).get('csv_count')==400]
assert exports,'no complete 400-file export manifest'
export=exports[-1];manifest=json.loads((export/'csv_manifest.json').read_text())
assert manifest['complete'] and manifest['csv_count']==400
for row in manifest['files']:
    assert hashlib.sha256((export/'csv'/row['filename']).read_bytes()).hexdigest()==row['sha256']
state={'csv_count':400,'csv_pc_files_sha_verified':400,'csv_data_rows':sum(r['data_rows'] for r in manifest['files']),
       'csv_manifest':str((export/'csv_manifest.json').relative_to(CASE)),'operations':[]}
with serial.Serial('COM7',57600,timeout=.1) as ate:
    assert not ate.in_waiting
    def ask(command):
        start=time.monotonic();ate.write(command.encode()+b'\r');ate.flush();raw=bytearray()
        while time.monotonic()-start<12:
            b=ate.read(1);raw.extend(b)
            if b==b'\r':break
        reply=raw.decode('ascii','replace').rstrip('\r')
        state['operations'].append({'command':command,'reply':reply,'raw_hex':raw.hex()})
        assert raw.endswith(b'\r'),state['operations'][-1]
        time.sleep(.1);return reply
    assert ask('*IDN?')=='NF55G_PICO_FIXTURE,Rev.0'
    assert ask('COMM_STATUS?')=='OK:state=IDLE'
    assert ask('SD_STATUS?')=='OK';assert ask('LOG_DROP_COUNT?')=='0'
    check=ask('PICO_SELF_CHECK?');assert check.startswith('OK:') and 'TEST_LOGGER=OK;TEST_LOG_DROP=OK' in check,check
    nonce=analysis['result']['session'][16:].upper()
    expected_host='OK:HOST_INFO:73AD3A60D10514E9:meter-host-relay-20261125.2:'+nonce+':READY'
    assert ask('HOST_INFO? METER')==expected_host
    def query(command):
        reply=ask('EXT_QUERY 2500 '+command);f=reply.split(':',3)
        assert f[:2]==['OK','EXT_RX'] and len(f)==4,reply
        raw=bytes.fromhex(f[3]);assert len(raw)==int(f[2]) and raw.endswith(b'\r\n')
        return raw[:-2].decode('ascii')
    for command,wanted in (('*IDN?','ADC Corp.,7355,246410099,  A02'),('F?','F01'),('R?','R3'),('INIC?','INIC1'),('TRS?','TRS0'),('H?','H0'),('ERR?','+0,"No error"')):
        assert query(command)==wanted,command
    assert ask('HOST_INFO? METER')==expected_host
    assert ask('COMM_STATUS?')=='OK:state=IDLE'
expected=json.loads((CASE/'host_replacement_01/parent_after_hashes.json').read_text())
r=SerialTransport('COM6',timeout=2)
try:
    r.enter_raw_repl(soft_reset=False)
    raw,err=r.exec_raw(HEADER+'\nprint(json.dumps({"hashes":{p:digest(p) for p in '+repr(list(expected))+'},"fault":app.external_link.fault,"parent_nonce":binascii.hexlify(app.external_link.parent_nonce).decode(),"uid":app.external_link.expected_chipid,"tx":app.external_link.transport.tx.active(),"rx":app.external_link.transport.rx.active()}))',timeout=45)
    (out/'final_parent_raw.log').write_bytes(raw+b'\nSTDERR\n'+err);assert not err,err
    parent=json.loads(raw.decode().strip());assert parent.pop('hashes')==expected
    assert not parent['fault'] and parent['uid']=='73AD3A60D10514E9' and parent['tx'] and parent['rx']
    assert parent['parent_nonce']==analysis['result']['session'][:16]
    state.update(parent=parent,firmware37_verified=True,status='OK')
finally:
    try:r.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
    finally:r.close()
(out/'acceptance.json').open('x',encoding='utf-8').write(json.dumps(state,indent=2))
print(json.dumps({k:v for k,v in state.items() if k!='operations'}))
