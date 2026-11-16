"""電源投入前から診断UARTを受信。送信・リセット操作なし。"""
import json,time,hashlib
from pathlib import Path
import serial
from serial.tools import list_ports
out=Path(__file__).resolve().parent
ports=[p for p in list_ports.comports() if p.vid==0x1A86 and p.pid==0x5523]
if len(ports)!=1: raise SystemExit('SH-U05A candidate count must be exactly one')
p=ports[0]
meta=dict(port=p.device,vid=p.vid,pid=p.pid,location=p.location,baud=115200,format='8N1',tx_bytes=0,flow_control=False,stop_policy='15 seconds after first received byte, or 600 seconds total')
(out/'adapter.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
received=0; first=None; started=time.monotonic()
with (out/'scan_uart.raw').open('xb') as raw, (out/'chunks.jsonl').open('x',encoding='utf-8') as timing:
    with serial.Serial(port=None,baudrate=115200,timeout=0.1,xonxoff=False,rtscts=False,dsrdtr=False) as uart:
        uart.port=p.device; uart.dtr=False; uart.rts=False; uart.open()
        started=time.monotonic()
        print('READY: '+p.device+' 115200 8N1 RECEIVE ONLY; no QR; power ON only, no RST',flush=True)
        while time.monotonic()-started<600:
            chunk=uart.read(4096)
            if chunk:
                now=time.monotonic()
                if first is None: first=now
                raw.write(chunk); raw.flush()
                timing.write(json.dumps(dict(elapsed_seconds=round(now-started,6),offset=received,size=len(chunk)))+'\n'); timing.flush()
                received+=len(chunk)
                print('RX total='+str(received),flush=True)
            if first is not None and time.monotonic()-first>=15: break
meta.update(rx_bytes=received,first_rx_seconds=None if first is None else round(first-started,3),elapsed_seconds=round(time.monotonic()-started,3),port_closed=True,source_sha256=hashlib.sha256((out/'scan_uart.raw').read_bytes()).hexdigest())
(out/'capture_result.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print('CLOSED: bytes='+str(received),flush=True)
