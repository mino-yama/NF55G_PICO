"""34文字拒否後35文字への復帰を取得。送信せず、結果2件後5秒無通信で終了する。"""
import json
import time
from pathlib import Path
import serial
from serial.tools import list_ports

out = Path(__file__).resolve().parent
ports = [p for p in list_ports.comports() if p.vid == 0x1A86 and p.pid == 0x5523]
if len(ports) != 1:
    raise SystemExit('SH-U05A candidate count must be exactly one')
p = ports[0]
meta = {'port':p.device,'vid':p.vid,'pid':p.pid,'location':p.location,
        'baud':115200,'format':'8N1','flow_control':False,'tx_bytes':0,
        'stop_policy':'two outcome records (text or error) seen, then 5 seconds idle; total limit 600 seconds'}
(out/'adapter.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
received=0
pending=bytearray()
key_seen=False
text_count=0
error_count=0
last_data=None
with (out/'scan_uart.raw').open('xb') as raw:
    with serial.Serial(port=None,baudrate=115200,timeout=0.1,
                       xonxoff=False,rtscts=False,dsrdtr=False) as uart:
        uart.port=p.device
        uart.dtr=False
        uart.rts=False
        uart.open()
        print('READY: '+p.device+' 115200 8N1 RECEIVE ONLY',flush=True)
        started=time.monotonic()
        while time.monotonic()-started < 600:
            chunk=uart.read(4096)
            if chunk:
                raw.write(chunk)
                raw.flush()
                received+=len(chunk)
                last_data=time.monotonic()
                pending.extend(chunk)
                while b'\n' in pending:
                    line,_,rest=pending.partition(b'\n')
                    pending=bytearray(rest)
                    # 停止時刻の目安だけ。原文は削除せず、厳密検査は採取後に別途実施。
                    if line.startswith(b'\x00@'):
                        line=line[1:]
                    if len(line)==153 and line.startswith(b'@'):
                        try:
                            record=bytes.fromhex(line[1:].decode('ascii'))
                            if record[8] == 12:
                                text_count += 1
                            elif record[8] == 13:
                                error_count += 1
                            key_seen = text_count + error_count >= 2
                        except (ValueError,UnicodeError):
                            pass
                print('RX total='+str(received)+' key_seen='+str(key_seen),flush=True)
            if key_seen and last_data is not None and time.monotonic()-last_data>=5:
                break
meta.update(rx_bytes=received,key_report_seen=key_seen,decoded_text_records=text_count,decoder_error_records=error_count,
            elapsed_seconds=round(time.monotonic()-started,3),port_closed=True)
(out/'capture_result.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
print('CLOSED: bytes='+str(received)+' key_seen='+str(key_seen),flush=True)

