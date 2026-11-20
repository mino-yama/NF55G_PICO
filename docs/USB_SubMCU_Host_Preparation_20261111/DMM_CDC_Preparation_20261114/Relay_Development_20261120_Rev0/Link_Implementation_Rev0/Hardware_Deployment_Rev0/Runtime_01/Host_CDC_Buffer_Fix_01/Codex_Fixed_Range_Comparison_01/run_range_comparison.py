"""ユーザーが電圧を固定しCOM7を解放した状態で、Codexが固定レンジ20/200指定とAUTOで各一回測定。"""
from datetime import datetime, timezone, timedelta
import hashlib
import re
import math
from decimal import Decimal
import json
import os
from pathlib import Path
import time
import serial
from serial.tools import list_ports

BASE=Path(__file__).resolve().parent
PREFIX=chr(92)*2+'?'+chr(92)
OUT=Path(PREFIX+str(BASE)) if os.name=='nt' and not str(BASE).startswith(PREFIX) else BASE
RESULT=OUT/'Capture_Result.json'


def main():
    if RESULT.exists() or (OUT/'ready.json').exists():
        raise RuntimeError('Preserve existing trial')
    ports=[p for p in list_ports.comports() if p.device.upper()=='COM7']
    if len(ports)!=1 or ports[0].vid!=0x056e or ports[0].pid!=0x5004:
        raise RuntimeError('Wrong/missing ATE adapter')
    evidence={'date_jst':'2026-11-20','port':'COM7','adapter':'Elecom USB-Serial Converter 056E:5004',
              'settings':'57600 8N1, flow control off, DTR/RTS off','queries':[],
              'automatic_retry':False,'instrument_commands':['identity/config/error queries','TRIG:SOUR IMM','TRIG:COUN 1','SAMP:COUN 1','TRIG:DEL 0','RANG:AUTO OFF/ON','RANG 20/200','READ? once per mode'],
              'nf55g_commands':False,'result':'READY_FOR_USER_AUTHORIZED_RETEST',
              'user_authorization':'ユーザー: 電圧を固定するのでCodex側で指示送信と受信。シリアルモニター終了/COM7使用可能を回答済み。固定入力を維持して20V指定/200V指定/AUTOを各一回比較。',
              'power_operation_performed':False}
    def save():
        RESULT.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    port=serial.Serial(port=None,baudrate=57600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE,timeout=.1,write_timeout=1,xonxoff=False,rtscts=False,dsrdtr=False)
    port.dtr=False
    port.rts=False
    port.port='COM7'
    rawfile=None
    try:
        port.open()
        rawfile=(OUT/'all_rx.raw').open('xb')
        (OUT/'ready.json').write_text(json.dumps({'port':'COM7','opened':True,'tx_sent':False,
            'date_jst':'2026-11-20','settings':evidence['settings']},indent=2)+'\n',encoding='utf8')
        save()
        print('ATE_RETEST_READY COM7 57600 8N1; queries once each',flush=True)
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
        evidence['executor']='Codex via ATE COM7'
        evidence['input_condition']='user holds voltage and wiring fixed'
        evidence['measurement_count_requested']=3
        evidence['measurement_count_completed']=0
        identity=query('*IDN?',10)
        if identity!='NF55G_PICO_FIXTURE,Rev.0':
            raise RuntimeError('Wrong fixture identity')
        def external(command,timeout_ms=2000):
            reply=query('EXT_QUERY '+str(timeout_ms)+' '+command,timeout_ms/1000+2)
            if not reply.startswith('OK:EXT_RX:'):
                raise RuntimeError('External relay failure '+reply)
            _,_,length,hex_text=reply.split(':')
            raw=bytes.fromhex(hex_text)
            if len(raw)!=int(length) or not 1<=len(raw)<=192 or not raw.endswith(b'\r\n') or raw.find(b'\r\n')!=len(raw)-2:
                raise RuntimeError('External response length/framing mismatch')
            raw.decode('ascii')
            evidence['queries'][-1]['instrument_raw_hex']=raw.hex().upper()
            evidence['queries'][-1]['instrument_ascii']=raw.decode('ascii')
            save()
            return raw
        def setting(command):
            if query('EXT_SEND 2000 '+command,4)!='OK:EXT_TX':
                raise RuntimeError('Setting transport incomplete')
        def complete():
            raw=external('*OPC?',10000)
            if Decimal(raw.decode('ascii').strip())!=1:
                raise RuntimeError('OPC not complete')
        def check_error(label):
            raw=external(':SYST:ERR?')
            evidence[label]=raw.decode('ascii')
            save()
            if Decimal(raw.decode('ascii').split(',',1)[0])!=0:
                raise RuntimeError('Instrument error '+repr(raw))
        def configuration(label):
            raw=external(':CONF?')
            body=raw[:-2].decode('ascii')
            if body.startswith('"') and body.endswith('"'):
                body=body[1:-1]
            num=r'[+-]?(?:[0-9]+(?:[.][0-9]*)?|[.][0-9]+)(?:[Ee][+-]?[0-9]+)?'
            match=re.fullmatch(r'VOLT ('+num+r'),('+num+r')',body)
            if not match or not all(Decimal(x).is_finite() and Decimal(x)>0 for x in match.groups()):
                raise RuntimeError('Malformed configuration response '+repr(raw))
            evidence[label]={'raw_ascii':raw.decode('ascii'),'range_volts':match[1],'resolution_volts':match[2]}
            save()
        if external('*IDN?')!=b'ADC Corp.,7355,246410099,  A02\r\n':
            raise RuntimeError('Wrong instrument identity')
        function=external(':SENS:FUNC?')[:-2].decode('ascii')
        if function not in ('"VOLT:DC"','VOLT:DC'):
            raise RuntimeError('Function is not DC voltage; no automatic function change')
        if Decimal(external(':INIT:CONT?').decode('ascii').strip())!=0:
            raise RuntimeError('Continuous mode is ON; stopped before measurement')
        evidence['auto_before']=external(':SENS:VOLT:DC:RANG:AUTO?').decode('ascii')
        configuration('conf_before_settings')
        check_error('error_before_settings')
        setting(':TRIG:SOUR IMM')
        if external(':TRIG:SOUR?').strip()!=b'IMM':
            raise RuntimeError('Trigger source readback mismatch')
        for command in (':TRIG:COUN 1',':SAMP:COUN 1',':TRIG:DEL 0'):
            setting(command)
            complete()
        evidence['comparisons']=[]
        def capture_mode(label,setting_command,auto_expected):
            setting(setting_command)
            if auto_expected is not None:
                auto=external(':SENS:VOLT:DC:RANG:AUTO?')
                if Decimal(auto.decode('ascii').strip())!=auto_expected:
                    raise RuntimeError('AUTO readback mismatch')
            configuration('conf_before_'+label)
            check_error('error_before_'+label)
            item={'mode':label,'setting_command':setting_command,
                  'conf_before_read':evidence['conf_before_'+label]}
            evidence['comparisons'].append(item)
            save()
            raw=external(':READ?',10000)
            evidence['measurement_count_completed']+=1
            item['measurement_raw_ascii']=raw.decode('ascii')
            item['measurement_raw_hex']=raw.hex().upper()
            save()
            value=Decimal(raw.decode('ascii').strip())
            if not value.is_finite() or abs(value)>Decimal('1E30'):
                raise RuntimeError('Nonfinite/overrange measurement; raw retained')
            item['measurement_volts']=str(value)
            configuration('conf_after_'+label)
            item['conf_after_read']=evidence['conf_after_'+label]
            check_error('error_after_'+label)
            item['error_after']=evidence['error_after_'+label]
            save()
            print('MEASURED '+label+' volts='+str(value)+' range='+item['conf_after_read']['range_volts'],flush=True)
        setting(':SENS:VOLT:DC:RANG:AUTO OFF')
        if Decimal(external(':SENS:VOLT:DC:RANG:AUTO?').decode('ascii').strip())!=0:
            raise RuntimeError('AUTO OFF readback mismatch')
        capture_mode('FIXED_REQUEST_20',':SENS:VOLT:DC:RANG 20',None)
        capture_mode('FIXED_REQUEST_200',':SENS:VOLT:DC:RANG 200',None)
        capture_mode('AUTO',':SENS:VOLT:DC:RANG:AUTO ON',Decimal(1))
        evidence['result']='FIXED_INPUT_RANGE_COMPARISON_SUCCEEDED'
        save()
        print('FIXED_INPUT_RANGE_COMPARISON_SUCCEEDED',flush=True)
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
