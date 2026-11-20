"""親を切離したHost単体のH/IDN診断。自動再送・レンジ・READなし。"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json,time,secrets,hashlib,sys
import serial
from serial.tools import list_ports
BASE=Path(__file__).resolve().parent
PREFIX=chr(92)*2+'?'+chr(92)
OUT=BASE if str(BASE).startswith(PREFIX) else Path(PREFIX+str(BASE))
ROOT=next(p for p in BASE.parents if (p/'src'/'external_instrument_contract.py').exists())
sys.path.insert(0,str(ROOT))
from src.external_instrument_contract import encode_frame,decode_frame


def main():
    if (OUT/'Result.json').exists() or (OUT/'rx.raw').exists():
        raise RuntimeError('Preserve existing diagnostic')
    ports=[p for p in list_ports.comports() if p.vid==0x1a86 and p.pid==0x5523]
    if len(ports)!=1:
        raise RuntimeError('Expected exactly one CH341 USB-UART adapter')
    result={'time_jst':datetime.now(timezone(timedelta(hours=9))).isoformat(),
            'port':ports[0].device,'adapter':'CH341 1A86:5523','settings':'115200 8N1, no flow, DTR/RTS OFF',
            'automatic_retry':False,'firmware_written':False,'instrument_query_sent_to_uart':False,
            'commands':['*IDN? only after READY and Host identity verified'],'frames':[]}
    s=serial.Serial(port=None,baudrate=115200,timeout=.02,write_timeout=1,xonxoff=False,rtscts=False,dsrdtr=False)
    s.dtr=False
    s.rts=False
    s.port=ports[0].device
    raw=bytearray()
    buffered=bytearray()
    txraw=bytearray()
    def send(frame):
        txraw.extend(frame)
        written=s.write(frame)
        if written!=len(frame):
            raise RuntimeError('Partial UART write; no retry')
    def receive(deadline):
        while time.monotonic()<deadline:
            pos=buffered.find(b'\r\n')
            if pos>=0:
                frame=bytes(buffered[:pos+2])
                del buffered[:pos+2]
                parsed=decode_frame(frame)
                result['frames'].append({'kind':parsed['kind'],'request':parsed['request'],
                    'mode':parsed['mode'],'timeout_ms':parsed['timeout_ms'],
                    'session_hex':parsed['session'].hex().upper(),'payload_hex':parsed['payload'].hex().upper()})
                return parsed
            chunk=s.read(min(64,max(1,s.in_waiting)))
            raw.extend(chunk)
            buffered.extend(chunk)
            if len(buffered)>512:
                raise RuntimeError('X1 frame exceeds limit')
        raise TimeoutError('Host X1 response timeout')
    try:
        s.open()
        time.sleep(.15)
        initial=s.read(s.in_waiting) if s.in_waiting else b''
        raw.extend(initial)
        if initial:
            raise RuntimeError('Unexpected bytes before H; stopped')
        nonce=secrets.token_bytes(8)
        send(encode_frame(nonce+bytes(8),0,'H',0,0,b''))
        h=receive(time.monotonic()+3)
        if (h['kind']!='h' or h['request']!=0 or h['mode']!=0 or h['timeout_ms']!=0
                or h['session'][:8]!=nonce or h['session'][8:]==bytes(8)):
            raise RuntimeError('HELLO correlation mismatch')
        identity,version,state=h['payload'].decode('ascii').split('|')
        result.update(identity=identity,version=version,state=state)
        print('HOST_HELLO '+identity+' '+version+' '+state,flush=True)
        if identity.upper()!='BFCF2EDB84B0B37F' or version!='meter-host-relay-20261120.1':
            raise RuntimeError('Unexpected Host identity/version')
        if state!='READY':
            raise RuntimeError('Host not READY; no instrument query sent')
        session=h['session']
        result['instrument_query_sent_to_uart']=True
        send(encode_frame(session,1,'Q',1,2000,b'*IDN?'))
        deadline=time.monotonic()+3
        accepted=False
        transmitted=False
        while True:
            frame=receive(deadline)
            if (frame['session']!=session or frame['request']!=1 or frame['mode']!=1 or frame['timeout_ms']!=2000):
                raise RuntimeError('Request correlation mismatch')
            kind=frame['kind']
            print('HOST_EVENT '+kind+' '+repr(frame['payload']),flush=True)
            if kind=='A' and not frame['payload'] and not accepted and not transmitted:
                accepted=True
            elif kind=='T' and not frame['payload'] and accepted and not transmitted:
                transmitted=True
            elif kind=='R' and accepted and transmitted:
                response=frame['payload']
                if not response or not response.endswith(b'\r\n') or response.find(b'\r\n')!=len(response)-2:
                    raise RuntimeError('Instrument response framing')
                result.update(success=True,response_hex=response.hex().upper(),response_ascii=response.decode('ascii'))
                print('HOST_IDN_SUCCESS '+repr(result['response_ascii']),flush=True)
                break
            elif kind=='E':
                raise RuntimeError('Host error '+repr(frame['payload']))
            else:
                raise RuntimeError('Unexpected event/order')
    except Exception as error:
        result.update(success=False,error=repr(error))
        print('HOST_DIAGNOSTIC_STOP '+repr(error),flush=True)
    finally:
        s.close()
        result.update(port_closed=True,rx_bytes=len(raw),rx_sha256=hashlib.sha256(raw).hexdigest())
        (OUT/'rx.raw').write_bytes(raw)
        (OUT/'tx.raw').write_bytes(txraw)
        (OUT/'Result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    main()
