"""配線修正後の既知HOSTを正式RESETで1回再起動し、USB READYとIDNを照合する。"""
import argparse
import json
from pathlib import Path
import time
import serial
from serial.tools import list_ports
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args();assert args.run.replace('_','').isalnum()
OUT=CASE/args.run;OUT.mkdir()
uid='73AD3A60D10514E9';prefix='OK:HOST_INFO:'+uid+':meter-host-relay-20261125.2:'
ops=[];result={'status':'STOPPED','uid':uid,'reset_requested':False}
ports=[{'device':p.device,'vid':p.vid,'pid':p.pid,'serial':p.serial_number} for p in list_ports.comports()]
(OUT/'ports.json').write_text(json.dumps(ports,indent=2))
matches=[p['device'] for p in ports if p['vid']==0x1a86]
monitor=serial.Serial(matches[0],115200,timeout=.05) if len(matches)==1 else None
result['monitor_port']=matches[0] if monitor else None
rawhost=bytearray()
try:
    with serial.Serial('COM7',57600,timeout=.1) as ate:
        assert not ate.in_waiting
        def ask(cmd):
            start=time.monotonic();ate.write(cmd.encode()+b'\r');ate.flush();raw=bytearray()
            while time.monotonic()-start<5:
                b=ate.read(1);raw.extend(b)
                if b==b'\r':break
            if monitor:rawhost.extend(monitor.read_all())
            reply=raw.decode('ascii','replace').rstrip('\r')
            ops.append({'command':cmd,'reply':reply,'raw_hex':raw.hex(),'elapsed_ms':round(1000*(time.monotonic()-start))})
            with (OUT/'ate.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(ops[-1])+'\n')
            assert raw.endswith(b'\r'),ops[-1]
            print(cmd+' => '+reply,flush=True);time.sleep(.1);return reply
        assert ask('COMM_STATUS?')=='OK:state=IDLE'
        before=ask('HOST_INFO? METER');assert before.startswith(prefix),before
        result['before']=before
        response=ask('HOST_RESET METER');result['reset_requested']=True
        assert response.startswith('OK:HOST_RESET_ACCEPTED:'+uid+':'),response
        old=response.split(':')[-1]
        time.sleep(2)
        done=ask('HOST_INFO? METER')
        assert done.startswith('OK:HOST_RESET_DONE:'+uid+':'+old+':'),done
        result['reset_done']=done;result['new_nonce']=done.split(':')[-2]
        assert result['new_nonce']!=old
        info=None
        for _ in range(5):
            info=ask('HOST_INFO? METER');assert info.startswith(prefix),info
            if info.endswith(':READY'):break
            assert info.endswith(':NOT_READY'),info
            time.sleep(2)
        result['host_info']=info
        assert info.endswith(':READY'),info
        reply=ask('EXT_QUERY 2500 *IDN?');parts=reply.split(':',3)
        assert parts[:2]==['OK','EXT_RX'] and len(parts)==4,reply
        raw=bytes.fromhex(parts[3]);assert len(raw)==int(parts[2]) and raw==b'ADC Corp.,7355,246410099,  A02\r\n',raw
        result['meter_idn']=raw.decode()
        assert ask('COMM_STATUS?')=='OK:state=IDLE'
        assert ask('SD_STATUS?')=='OK';result['drop']=ask('LOG_DROP_COUNT?')
        result['status']='OK'
except Exception as exc:result['error']=repr(exc)
finally:
    if monitor:rawhost.extend(monitor.read_all());monitor.close()
    (OUT/'host_uart.raw').write_bytes(rawhost)
    (OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='OK' else 1)
