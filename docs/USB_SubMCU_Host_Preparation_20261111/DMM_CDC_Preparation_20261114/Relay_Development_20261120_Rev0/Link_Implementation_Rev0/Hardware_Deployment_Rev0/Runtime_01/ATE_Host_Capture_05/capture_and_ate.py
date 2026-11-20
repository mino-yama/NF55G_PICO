"""Host TXをRX専用COM22で受動採取しながらATE識別中継を各1回実行。"""
from pathlib import Path
import sys,json,threading,runpy,time,hashlib
import serial
from serial.tools import list_ports
BASE=Path(__file__).resolve().parent
PREFIX=chr(92)*2+'?'+chr(92)
OUT=BASE if str(BASE).startswith(PREFIX) else Path(PREFIX+str(BASE))
ROOT=next(p for p in BASE.parents if (p/'src'/'external_instrument_contract.py').exists())
sys.path.insert(0,str(ROOT))
from src.external_instrument_contract import decode_frame
if (OUT/'Host_TX_Capture.json').exists() or (OUT/'host_tx.raw').exists() or (OUT/'Capture_Result.json').exists():
    raise RuntimeError('Preserve previous trial')
ports=[p for p in list_ports.comports() if p.device=='COM22' and p.vid==0x1a86 and p.pid==0x5523]
if len(ports)!=1:
    raise RuntimeError('Expected COM22 passive adapter')
s=serial.Serial(port=None,baudrate=115200,timeout=.02,write_timeout=1,xonxoff=False,rtscts=False,dsrdtr=False)
s.dtr=False
s.rts=False
s.port='COM22'
s.open()
stop=threading.Event()
raw=bytearray()
errors=[]
def capture():
    try:
        while not stop.is_set():
            raw.extend(s.read(min(64,max(1,s.in_waiting))))
    except Exception as error:
        errors.append(repr(error))
t=threading.Thread(target=capture,daemon=True)
t.start()
try:
    print('HOST_TX_PASSIVE_CAPTURE_STARTED; COM22 RX only, no UART writes',flush=True)
    runpy.run_path(str(OUT.parent/'ate_trial_host_capture05.py'),run_name='__main__')
finally:
    time.sleep(.1)
    stop.set()
    t.join(timeout=1)
    if t.is_alive():
        errors.append('Capture thread did not stop')
    s.close()
    frames=[]
    for frame in bytes(raw).splitlines(keepends=True):
        try:
            decoded=decode_frame(frame)
            frames.append({'kind':decoded['kind'],'request':decoded['request'],'session_hex':decoded['session'].hex().upper(),
                'mode':decoded['mode'],'timeout_ms':decoded['timeout_ms'],'payload_hex':decoded['payload'].hex().upper(),
                'payload_ascii':decoded['payload'].decode('ascii')})
        except Exception as error:
            frames.append({'decode_error':repr(error),'raw_hex':frame.hex().upper()})
    (OUT/'host_tx.raw').write_bytes(raw)
    result={'port':'COM22','rx_only':True,'writes_to_host':False,'rx_bytes':len(raw),
            'rx_sha256':hashlib.sha256(raw).hexdigest(),'frames':frames,'capture_errors':errors,'port_closed':True}
    (OUT/'Host_TX_Capture.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('HOST_TX_CAPTURE '+json.dumps(result,ensure_ascii=True),flush=True)
