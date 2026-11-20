"""ATEの受信を先行し、ユーザー電源投入通知後に識別Queryを各一回送る。"""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import time
import serial
from serial.tools import list_ports

BASE=Path(__file__).resolve().parent/'ATE_Capture_03'
PREFIX=chr(92)*2+'?'+chr(92)
OUT=Path(PREFIX+str(BASE)) if os.name=='nt' and not str(BASE).startswith(PREFIX) else BASE
RESULT=OUT/'Capture_Result.json'


def main():
    if RESULT.exists() or (OUT/'ready.json').exists():
        raise RuntimeError('Preserve existing trial')
    ports=[p for p in list_ports.comports() if p.device.upper()=='COM5']
    if len(ports)!=1 or ports[0].vid!=0x056e or ports[0].pid!=0x5004:
        raise RuntimeError('Wrong/missing ATE adapter')
    evidence={'date_jst':'2026-11-20','port':'COM5','adapter':'Elecom USB-Serial Converter 056E:5004',
              'settings':'57600 8N1, flow control off, DTR/RTS off','queries':[],
              'automatic_retry':False,'instrument_commands':['*IDN? only after fixture identity verified'],
              'nf55g_commands':False,'result':'READY_FOR_USER_AUTHORIZED_RETEST',
              'user_authorization':'7355 USB-B抜けをユーザー確認。デバッグを止めて最初の中継テストへ戻す指示。接続復帰通知後に実行。',
              'power_operation_performed':False}
    def save():
        RESULT.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    port=serial.Serial(port=None,baudrate=57600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE,timeout=.1,write_timeout=1,xonxoff=False,rtscts=False,dsrdtr=False)
    port.dtr=False
    port.rts=False
    port.port='COM5'
    rawfile=None
    try:
        port.open()
        rawfile=(OUT/'all_rx.raw').open('xb')
        (OUT/'ready.json').write_text(json.dumps({'port':'COM5','opened':True,'tx_sent':False,
            'date_jst':'2026-11-20','settings':evidence['settings']},indent=2)+'\n',encoding='utf8')
        save()
        print('ATE_RETEST_READY COM5 57600 8N1; queries once each',flush=True)
        time.sleep(.2)
        if port.in_waiting:
            data=port.read(port.in_waiting)
            rawfile.write(data)
            raise RuntimeError('Unexpected ATE bytes before query; raw retained')
        def query(command,timeout):
            tx=command.encode('ascii')+b'\r'
            row={'command':command,'tx_hex':tx.hex().upper(),
                 'time_jst':datetime.now(timezone(timedelta(hours=9))).isoformat()}
            evidence['queries'].append(row)
            save()
            start=time.monotonic()
            written=port.write(tx)
            row['tx_written']=written
            if written!=len(tx):
                raise RuntimeError('Partial ATE write; not retried')
            answer=bytearray()
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                data=port.read(1)
                if data:
                    answer.extend(data)
                    rawfile.write(data)
                    if data==b'\r':
                        break
                if len(answer)>1024:
                    break
            rawfile.flush()
            raw=bytes(answer)
            row['elapsed_ms']=round((time.monotonic()-start)*1000,3)
            row['rx_hex']=raw.hex().upper()
            row['rx_ascii']=raw.decode('ascii',errors='backslashreplace')
            save()
            print(command,'=>',repr(row['rx_ascii']),flush=True)
            if not raw.endswith(b'\r') or len(raw)>1024:
                raise RuntimeError('ATE response incomplete/timeout; not retried')
            time.sleep(.15)
            if port.in_waiting:
                extra=port.read(port.in_waiting)
                rawfile.write(extra)
                row['extra_hex']=extra.hex().upper()
                save()
                raise RuntimeError('Unexpected extra ATE bytes; raw retained')
            return raw[:-1].decode('ascii')
        identity=query('*IDN?',10)
        if identity!='NF55G_PICO_FIXTURE,Rev.0':
            raise RuntimeError('Wrong ATE fixture identity')
        response=query('EXT_QUERY 2000 *IDN?',5)
        if not response.startswith('OK:EXT_RX:'):
            raise RuntimeError('External instrument relay returned error: '+response)
        _,_,length,hex_text=response.split(':')
        instrument=bytes.fromhex(hex_text)
        if len(instrument)!=int(length) or not instrument.endswith(b'\r\n'):
            raise RuntimeError('Relay response length/ending mismatch')
        evidence['instrument_response_ascii']=instrument.decode('ascii')
        evidence['instrument_response_hex']=instrument.hex().upper()
        evidence['instrument_model_match']=instrument.startswith(b'ADC Corp.,7355,')
        evidence['instrument_identity_matches_previous']=instrument==b'ADC Corp.,7355,246410099,  A02\r\n'
        if not evidence['instrument_model_match']:
            raise RuntimeError('Unexpected instrument model')
        evidence['result']='IDENTIFICATION_RELAY_SUCCEEDED'
        save()
        print('IDENTIFICATION_RELAY_SUCCEEDED',repr(evidence['instrument_response_ascii']),flush=True)
    except Exception as error:
        evidence['result']='STOPPED'
        evidence['error']=repr(error)
        save()
        print('TRIAL_STOPPED',repr(error),flush=True)
        raise
    finally:
        if rawfile:
            rawfile.flush()
            rawfile.close()
        port.close()
        if (OUT/'all_rx.raw').exists():
            raw=(OUT/'all_rx.raw').read_bytes()
            evidence['all_rx_bytes']=len(raw)
            evidence['all_rx_sha256']=hashlib.sha256(raw).hexdigest()
        evidence['port_closed']=True
        save()


if __name__=='__main__':
    main()
