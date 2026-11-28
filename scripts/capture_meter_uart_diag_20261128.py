"""native USBでHOSTの起動・UART受信／送信を観測し、ATE情報要求と照合する。"""
import json
from pathlib import Path
import time
import serial
from serial.tools import list_ports
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/uart_diagnostic'
ports=[{'device':p.device,'vid':p.vid,'pid':p.pid,'serial':p.serial_number} for p in list_ports.comports()]
(OUT/'native_ports.json').write_text(json.dumps(ports,indent=2),encoding='utf-8')
matches=[p for p in ports if (p['serial'] or '').upper()=='BFCF2EDB84B0B37F']
assert len(matches)==1,ports
data=bytearray()
with serial.Serial(matches[0]['device'],115200,timeout=.1) as host,serial.Serial('COM7',57600,timeout=12) as ate:
    def capture(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:data.extend(host.read(4096))
    capture(3)
    assert not ate.in_waiting
    ate.write(b'HOST_INFO? METER\r');ate.flush()
    reply=ate.read_until(b'\r')
    capture(3)
(OUT/'native_capture.log').write_bytes(data)
record={'native_port':matches[0]['device'],'ate_reply':reply.decode('ascii','replace'),'native_bytes':len(data),'native_text':data.decode('utf-8','replace')}
(OUT/'native_result.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
