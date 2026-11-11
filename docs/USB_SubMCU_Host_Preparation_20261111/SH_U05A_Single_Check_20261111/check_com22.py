"""識別したSH-U05Aのポート設定と開閉のみ確認。送信・配線・FW操作なし。"""
import json
import time
from pathlib import Path
import serial
from serial.tools import list_ports

out=Path(__file__).parent
ports=list(list_ports.comports())
rows=[dict(device=p.device,description=p.description,vid=p.vid,pid=p.pid,serial_number=p.serial_number,location=p.location,hwid=p.hwid) for p in ports]
matching=[p for p in ports if p.device.upper()=='COM22' and p.vid==0x1a86 and p.pid==0x5523]
if len(matching)!=1:
    raise SystemExit('Expected exactly one SH-U05A candidate at COM22 with 1A86:5523; no port opened')
r=dict(ports=rows,target='COM22',expected_vid='1A86',expected_pid='5523',transmitted_bytes=0,open_ok=False)
s=serial.Serial(port=None,baudrate=115200,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=0.1,xonxoff=False,rtscts=False,dsrdtr=False)
s.dtr=False
s.rts=False
s.port=matching[0].device
try:
    s.open()
    r['open_ok']=s.is_open
    r['settings']=s.get_settings()
    r['dtr']=s.dtr
    r['rts']=s.rts
    deadline=time.monotonic()+1
    received=0
    while time.monotonic()<deadline:
        received+=len(s.read(256))
    r['received_bytes']=received
finally:
    s.close()
    r['closed']=not s.is_open
    (out/'COM22_Open_Check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(r,ensure_ascii=False,indent=2))
