"""オシロ観測向けHOST情報要求を最大20回に限定。正常応答と無応答を区別して保存。"""
import argparse
import json
from pathlib import Path
import time
import serial
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--count',type=int,choices=range(1,21),default=10);args=p.parse_args()
assert args.run.replace('_','').isalnum()
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01'/args.run;OUT.mkdir()
rows=[];done=0;seen=[];result={'planned_requests':args.count,'status':'STOPPED','firmware_changed':False}
try:
    with serial.Serial('COM7',57600,timeout=.1) as ate:
        assert not ate.in_waiting
        def ask(command):
            start=time.monotonic();ate.write(command.encode()+b'\r');ate.flush();raw=bytearray()
            while time.monotonic()-start<3:
                b=ate.read(1);raw.extend(b)
                if b==b'\r':break
            reply=raw.decode('ascii','replace').rstrip('\r')
            row={'command':command,'reply':reply,'raw_hex':raw.hex(),'elapsed_ms':round(1000*(time.monotonic()-start))};rows.append(row)
            with (OUT/'ate.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
            assert raw.endswith(b'\r'),row
            return reply
        assert ask('*IDN?')=='NF55G_PICO_FIXTURE,Rev.0'
        assert ask('COMM_STATUS?')=='OK:state=IDLE'
        for i in range(args.count):
            reply=ask('HOST_INFO? METER')
            identified=reply.startswith('OK:HOST_INFO:73AD3A60D10514E9:meter-host-relay-20261125.2:')
            assert identified or reply=='ERR:HOST_TIMEOUT',reply
            if identified:seen.append(reply)
            done+=1;print('SCOPE_BURST '+str(done)+'/'+str(args.count)+' '+reply,flush=True)
            time.sleep(.2)
        assert ask('COMM_STATUS?')=='OK:state=IDLE'
        result.update(status='COMPLETE',host_info_received=bool(seen),host_replies=seen)
except Exception as exc:result['error']=repr(exc);raise
finally:
    result['completed_requests']=done
    (OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
