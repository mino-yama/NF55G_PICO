"""HOST取り外し時、ATEから明示INFOを反復し親GP12の実送信をオシロ観測する。"""
import json
from pathlib import Path
import time
import serial
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01/scope_ate_repeat_01'
OUT.mkdir()
stop=OUT/'stop.request'
count=0;started=time.monotonic();result={'source':'COM7 ATE HOST_INFO explicit repeat','pin':12,'duration_limit_seconds':600,'host_removed_by_operator':True,'no_firmware_changes':True}
try:
    with serial.Serial('COM7',57600,timeout=.1) as ate,(OUT/'ate.jsonl').open('x',encoding='utf-8') as log:
        assert not ate.in_waiting
        def ask(command):
            sent=time.monotonic();ate.write(command.encode()+b'\r');ate.flush();raw=bytearray()
            while time.monotonic()-sent<12:
                b=ate.read(1);raw.extend(b)
                if b==b'\r':break
            reply=raw.decode('ascii','replace').rstrip('\r')
            log.write(json.dumps({'command':command,'reply':reply,'raw_hex':raw.hex(),'elapsed_ms':round(1000*(time.monotonic()-sent))})+'\n');log.flush()
            assert raw.endswith(b'\r'),reply
            return reply
        assert ask('*IDN?')=='NF55G_PICO_FIXTURE,Rev.0'
        assert ask('COMM_STATUS?')=='OK:state=IDLE'
        while time.monotonic()-started<600 and not stop.exists():
            reply=ask('HOST_INFO? METER')
            assert reply=='ERR:HOST_TIMEOUT',('unexpected HOST response; stop repeating',reply)
            count+=1
            if count==1 or count%30==0:print('GP12_INFO_REPEAT_ACTIVE; count='+str(count),flush=True)
            time.sleep(.05)
        assert ask('COMM_STATUS?')=='OK:state=IDLE'
        result['status']='STOPPED_BY_REQUEST' if stop.exists() else 'TIME_LIMIT_COMPLETE'
except Exception as exc:
    result.update(status='STOPPED_ERROR',error=repr(exc));raise
finally:
    result.update(requests=count,elapsed_seconds=round(time.monotonic()-started,2))
    (OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
