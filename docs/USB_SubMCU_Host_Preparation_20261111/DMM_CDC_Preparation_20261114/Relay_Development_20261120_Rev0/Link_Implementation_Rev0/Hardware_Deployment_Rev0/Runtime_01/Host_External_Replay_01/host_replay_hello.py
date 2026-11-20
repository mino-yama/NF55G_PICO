"""外部給電のHostをPCの3.3V UARTから照合。H一回だけ、Q/SCPI/自動再送なし。"""
from pathlib import Path
import json,time,secrets,hashlib
import serial
from serial.tools import list_ports
BASE=Path(__file__).resolve().parent
PREFIX=chr(92)*2+'?'+chr(92)
OUT=BASE if str(BASE).startswith(PREFIX) else Path(PREFIX+str(BASE))
ROOT=next(p for p in BASE.parents if (p/'src'/'external_instrument_contract.py').exists())
import sys
sys.path.insert(0,str(ROOT))
from src.external_instrument_contract import encode_frame,decode_frame
if (OUT/'Host_UART_Result.json').exists():
    raise RuntimeError('Preserve previous capture')
ports=[p for p in list_ports.comports() if p.device=='COM22' and p.vid==0x1a86 and p.pid==0x5523]
if len(ports)!=1:
    raise RuntimeError('Expected COM22 CH341 adapter absent')
result={'port':'COM22','settings':'115200 8N1, no flow, DTR/RTS OFF','Q_sent':False,'SCPI_sent':False,'automatic_retry':False,'firmware_written':False,'power_source':'external supply; PC USB-C disconnected','instrument_USB_B':'disconnected','reported_power_volts':[5.0,3.2]}
s=serial.Serial(port=None,baudrate=115200,timeout=.02,write_timeout=1,xonxoff=False,rtscts=False,dsrdtr=False)
s.dtr=False
s.rts=False
s.port='COM22'
received=b''
try:
    s.open()
    time.sleep(.15)
    initial=s.read(s.in_waiting) if s.in_waiting else b''
    (OUT/'before_H.raw').write_bytes(initial)
    if initial:
        raise RuntimeError('Unexpected initial bytes; stopped before H')
    frame=(ROOT/'docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01'/'ATE_Host_NoUSB_07'/'host_rx.raw').read_bytes()
    captured=decode_frame(frame)
    if captured['kind']!='H' or captured['request'] or captured['mode'] or captured['timeout_ms'] or captured['payload'] or captured['session'][8:]!=bytes(8):
        raise RuntimeError('Not an isolated HELLO capture')
    nonce=captured['session'][:8]
    result['replayed_parent_H']=True
    (OUT/'H_tx.raw').write_bytes(frame)
    result['tx_written']=s.write(frame)
    if result['tx_written']!=len(frame):
        raise RuntimeError('Partial UART write; no retry')
    start=time.monotonic()
    while time.monotonic()-start<3 and not received.endswith(b'\r\n'):
        received+=s.read(min(64,max(1,s.in_waiting)))
        if len(received)>512:
            raise RuntimeError('Frame too long')
    result['elapsed_ms']=round((time.monotonic()-start)*1000)
    if not received:
        raise TimeoutError('Host HELLO: no bytes within 3000ms')
    if not received.endswith(b'\r\n'):
        raise TimeoutError('Host HELLO: incomplete response within 3000ms')
    parsed=decode_frame(received)
    if parsed['kind']!='h' or parsed['request'] or parsed['mode'] or parsed['timeout_ms'] or parsed['session'][:8]!=nonce or parsed['session'][8:]==bytes(8):
        raise RuntimeError('HELLO correlation mismatch')
    identity,version,state=parsed['payload'].decode('ascii').split('|')
    result.update(identity=identity,version=version,state=state)
    if identity.upper()!='BFCF2EDB84B0B37F' or version!='meter-host-relay-20261120.1':
        raise RuntimeError('Unexpected Host identity/version')
    result['hello_ok']=True
    print('HOST_HELLO_OK '+identity+' '+version+' '+state,flush=True)
except Exception as error:
    result.update(hello_ok=False,error=repr(error))
    print('HOST_DIAGNOSTIC_STOP '+repr(error),flush=True)
finally:
    (OUT/'H_rx.raw').write_bytes(received)
    result.update(rx_hex=received.hex().upper(),rx_sha256=hashlib.sha256(received).hexdigest())
    s.close()
    result['port_closed']=True
    (OUT/'Host_UART_Result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
