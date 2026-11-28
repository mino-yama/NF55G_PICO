"""HOST未接続のオシロ診断後、親のローカルATE応答だけを照合する。"""
import json
from pathlib import Path
import time
import serial
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/host_replacement_01/scope_ate_repeat_01'
rows=[]
try:
    with serial.Serial('COM7',57600,timeout=.1) as ate:
        assert not ate.in_waiting
        for cmd,expected in (('*IDN?','NF55G_PICO_FIXTURE,Rev.0'),('COMM_STATUS?','OK:state=IDLE'),('SD_STATUS?','OK'),('LOG_DROP_COUNT?','0')):
            start=time.monotonic();ate.write(cmd.encode()+b'\r');ate.flush();raw=bytearray()
            while time.monotonic()-start<3:
                b=ate.read(1);raw.extend(b)
                if b==b'\r':break
            reply=raw.decode('ascii','replace').rstrip('\r')
            rows.append({'command':cmd,'reply':reply,'raw_hex':raw.hex(),'elapsed_ms':round(1000*(time.monotonic()-start))})
            assert raw.endswith(b'\r') and reply==expected,rows[-1]
            time.sleep(.1)
    print('ATE_RESTORED; IDLE; SD_OK; DROP_0',flush=True)
finally:
    (OUT/'after_parent_rst.json').open('x',encoding='utf-8').write(json.dumps(rows,indent=2))
    print(json.dumps(rows))
