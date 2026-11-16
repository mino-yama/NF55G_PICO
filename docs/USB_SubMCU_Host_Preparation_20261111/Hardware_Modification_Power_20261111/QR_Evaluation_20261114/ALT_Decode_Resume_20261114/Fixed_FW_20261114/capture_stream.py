"""固定QR連続送信の原文を保存する。シリアルへは送信しない。"""
import argparse,datetime,hashlib,json,time
from pathlib import Path
import serial
from serial.tools import list_ports
p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
p.add_argument('--texts',type=int,default=20)
p.add_argument('--seconds',type=int,default=1200)
a=p.parse_args()
if a.texts<1 or a.seconds<1: p.error('positive counts required')
a.output.mkdir(parents=True,exist_ok=False)
ports=[x for x in list_ports.comports() if x.vid==0x1A86 and x.pid==0x5523]
if len(ports)!=1: raise SystemExit('SH-U05A candidate count must be exactly one')
dev=ports[0]; out=a.output
meta=dict(port=dev.device,location=dev.location,baud=115200,format='8N1',flow_control=False,tx_bytes=0,requested_texts=a.texts,total_seconds=a.seconds,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(out/'adapter.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
texts=errors=received=0; pending=bytearray(); reached=None; reason='time_limit'
with (out/'scan_uart.raw').open('xb') as raw,(out/'chunks.jsonl').open('x',encoding='utf-8') as timing:
    with serial.Serial(port=None,baudrate=115200,timeout=0.1,xonxoff=False,rtscts=False,dsrdtr=False) as uart:
        uart.port=dev.device; uart.dtr=False; uart.rts=False; uart.open()
        started=time.monotonic()
        print('READY: '+dev.device+' 115200 8N1 RECEIVE ONLY',flush=True)
        while time.monotonic()-started<a.seconds:
            chunk=uart.read(4096)
            if chunk:
                raw.write(chunk); raw.flush()
                timing.write(json.dumps(dict(elapsed_seconds=round(time.monotonic()-started,6),offset=received,size=len(chunk)))+'\n'); timing.flush()
                received+=len(chunk); pending.extend(chunk)
                while b'\n' in pending:
                    line,_,rest=pending.partition(b'\n'); pending=bytearray(rest)
                    if line.startswith(b'\x00@'): line=line[1:]
                    if len(line)==153 and line.startswith(b'@'):
                        try:
                            rec=bytes.fromhex(line[1:].decode('ascii'))
                            if rec[8]==12: texts+=1; print('TEXT records='+str(texts),flush=True)
                            if rec[8]==13: errors+=1; print('DECODE ERROR records='+str(errors),flush=True)
                        except (ValueError,UnicodeError): pass
            if texts>=a.texts and reached is None: reached=time.monotonic()
            if reached is not None and time.monotonic()-reached>=3: reason='target_reached_plus_3_seconds'; break
            if (out/'stop.request').exists(): reason='explicit_stop_marker'; break
meta.update(rx_bytes=received,text_records=texts,error_records=errors,stop_reason=reason,elapsed_seconds=round(time.monotonic()-started,3),port_closed=True,source_sha256=hashlib.sha256((out/'scan_uart.raw').read_bytes()).hexdigest())
(out/'capture_result.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print('CLOSED: '+json.dumps(meta),flush=True)
