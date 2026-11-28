"""交換後HOSTのUSB未接続時の管理応答をATE経由で記録する。"""
import json
import argparse
from pathlib import Path
import time
import serial
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
assert args.run.replace('_','').isalnum()
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01'/args.run
OUT.mkdir()
uid='73AD3A60D10514E9';rows=[]
with serial.Serial('COM7',57600,timeout=.1) as ate:
    initial=ate.read_all();assert not initial,initial
    for command in ('*IDN?','COMM_STATUS?','HOST_INFO? METER','SD_STATUS?','LOG_DROP_COUNT?'):
        start=time.monotonic();ate.write(command.encode()+b'\r');ate.flush();raw=bytearray()
        while time.monotonic()-start<12:
            b=ate.read(1);raw.extend(b)
            if b==b'\r':break
        rows.append({'command':command,'reply':raw.decode('ascii','replace').rstrip('\r'),'elapsed_ms':round(1000*(time.monotonic()-start)),'raw_hex':raw.hex()})
        assert raw.endswith(b'\r'),rows[-1]
        time.sleep(.1)
reply=next(r['reply'] for r in rows if r['command']=='HOST_INFO? METER')
prefix='OK:HOST_INFO:'+uid+':meter-host-relay-20261125.2:'
result={'uid':uid,'meter_usb':'operator reports disconnected; HOST reset','host_reply':reply,
        'management_identity_verified':reply.startswith(prefix),'operations':rows}
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
