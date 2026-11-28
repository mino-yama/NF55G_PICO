"""退避済みHOSTをPC USB単独給電で通常起動し、診断とINFO応答を採取する。"""
import json
from pathlib import Path
import subprocess
import time
import serial
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
TOOL=ROOT/'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
with serial.Serial('COM23',115200,timeout=.1) as monitor:
    data=bytearray(monitor.read_all())
    p=subprocess.run([str(TOOL),'reboot','--ser','BFCF2EDB84B0B37F'],capture_output=True,timeout=20)
    (OUT/'host_pc_usb_reboot.log').write_bytes(p.stdout+p.stderr)
    assert p.returncode==0
    until=time.monotonic()+3
    while time.monotonic()<until:data.extend(monitor.read(4096))
    with serial.Serial('COM7',57600,timeout=12) as ate:
        assert not ate.in_waiting
        ate.write(b'HOST_INFO? METER\r');ate.flush();reply=ate.read_until(b'\r')
    until=time.monotonic()+2
    while time.monotonic()<until:data.extend(monitor.read(4096))
    (OUT/'host_pc_usb_start.raw').write_bytes(data)
    result={'host_info':reply.decode('ascii','replace'),'monitor_bytes':len(data),'power':'PC USB only; external power removed by operator','flash_write_performed':False}
    (OUT/'host_pc_usb_start.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
