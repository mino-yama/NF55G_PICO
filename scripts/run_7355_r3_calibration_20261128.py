"""R3で校正用取得・V→mV→A・Cache失効を実ATEから照合する。AD/ARは送らない。"""
import argparse
from contextlib import ExitStack
from decimal import Decimal
import json
from pathlib import Path
import time
import serial

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True)
    parser.add_argument('--input-setpoint-mv',required=True)
    parser.add_argument('--host-chipid',default='BFCF2EDB84B0B37F')
    parser.add_argument('--monitor-port')
    args=parser.parse_args();assert args.run.replace('_','').isalnum()
    out=CASE/args.run;out.mkdir()
    operations=[];values=[];started=False;complete=True
    result={'status':'STOPPED','input_setpoint_mV':args.input_setpoint_mv,'nf55_commands_sent':0}
    with ExitStack() as stack:
        ate=stack.enter_context(serial.Serial('COM7',57600,timeout=.1))
        monitor=stack.enter_context(serial.Serial(args.monitor_port,115200,timeout=.05)) if args.monitor_port else None
        result['host_chipid']=args.host_chipid.upper()
        result['external_uart_monitor']=bool(monitor)
        result['cache_query_wire_silence_verified']=bool(monitor)
        rawhost=(out/'host_uart.raw').open('xb')
        try:
            assert not ate.in_waiting
            def ask(command):
                nonlocal complete
                time.sleep(.04);complete=False
                t=time.monotonic();ate.write(command.encode()+b'\r');ate.flush();raw=bytearray()
                while time.monotonic()-t<12:
                    b=ate.read(1);raw.extend(b)
                    if b==b'\r':break
                captured=monitor.read_all() if monitor else b'';rawhost.write(captured);rawhost.flush()
                reply=raw.decode('ascii','replace').rstrip('\r')
                row={'command':command,'reply':reply,'raw_hex':raw.hex(),'elapsed_ms':round(1000*(time.monotonic()-t)),'host_bytes':len(captured)}
                operations.append(row)
                with (out/'ate.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
                complete=raw.endswith(b'\r');assert complete,row
                return reply
            def expect(command,value):
                reply=ask(command);assert reply==value,(command,reply)
            def query(command):
                reply=ask('EXT_QUERY 2500 '+command);parts=reply.split(':',3)
                assert len(parts)==4 and parts[:2]==['OK','EXT_RX'],reply
                raw=bytes.fromhex(parts[3]);assert len(raw)==int(parts[2]) and raw.endswith(b'\r\n')
                return raw[:-2].decode('ascii')
            expect('COMM_STATUS?','OK:state=IDLE');expect('SD_STATUS?','OK')
            drop=ask('LOG_DROP_COUNT?');assert drop.isdecimal()
            host=ask('HOST_INFO? METER')
            assert host.startswith('OK:HOST_INFO:'+args.host_chipid.upper()+':meter-host-relay-20261125.2:') and host.endswith(':READY'),host
            assert query('*IDN?')=='ADC Corp.,7355,246410099,  A02'
            result['host_before']=host
            # 設定変更はATEによる事前工程だけ。耐久本体では設定指令を送らない。
            for setting,question,wanted in [('F1','F?','F01'),('H0','H?','H0'),('INIC1','INIC?','INIC1'),('TRS0','TRS?','TRS0'),('RN0','RN?','RN0,00000'),('R3','R?','R3'),('PR4','PR?','PR4')]:
                expect('EXT_SEND 2500 '+setting,'OK:EXT_TX')
                actual=query(question)
                if question=='RN?':assert actual.startswith('RN0,') and len(actual)==9 and actual[4:].isdigit(),actual
                else:assert actual==wanted,(question,actual)
            result['direct_raw']=query('MD?')
            expect('TEST_START','OK');started=True
            def acquire(target,point):
                reply=ask('CAL_MEASURE_'+target+' '+point+' 4000 MD?')
                assert reply.startswith('OK:CAL_MEASURE:'),reply
                token=reply.split(':')[-1]
                cmd='CAL_MEASUREMENT_'+target+'? '+point
                cached=ask(cmd);fields=cached.split(':')
                assert fields[:5]==['OK','CAL_MEASUREMENT',token,target,point],cached
                assert len(fields)==10 and fields[6]=='mV' and fields[8]=='A',cached
                raw=bytes.fromhex(fields[9]);assert raw.endswith(b'\r\n')
                assert Decimal(raw[:-2].decode())*1000==Decimal(fields[5])==Decimal(fields[7]),cached
                repeated=ask(cmd);assert repeated==cached
                # 診断RXがHOST TXへ戻されている場合、Cache照会でHOST送信がないことも確認。
                if monitor:assert operations[-1]['host_bytes']==0,operations[-1]
                values.append({'target':target,'point':point,'token':token,'cache':cached,'raw':raw.decode()})
                print('CAL_OK '+target+' '+point+' '+fields[7]+' A',flush=True)
                return token
            tokens=[]
            for target in ('DISCHG_I','BATT_CHG'):
                for point in ('A','B'):tokens.append(acquire(target,point))
            old=tokens[0];tokens.append(acquire('DISCHG_I','A'))
            expect('CAL_MEASUREMENT? '+old,'ERR:CAL_MEASUREMENT_INVALID')
            expect('TEST_END','OK');started=False
            for token in tokens:expect('CAL_MEASUREMENT? '+token,'ERR:CAL_MEASUREMENT_INVALID')
            check=ask('PICO_SELF_CHECK?');assert 'TEST_LOGGER=OK;TEST_LOG_DROP=OK' in check,check
            expect('SD_STATUS?','OK');expect('LOG_DROP_COUNT?',drop);expect('COMM_STATUS?','OK:state=IDLE')
            assert ask('HOST_INFO? METER')==host
            assert query('R?')=='R3'
            result.update(status='COMPLETE',acquisitions=len(values),host_after=host,log_drop=drop)
        except Exception as exc:
            result['error']=repr(exc);print('STOPPED '+repr(exc),flush=True)
        finally:
            if started and complete:
                try:result['cleanup_test_end']=ask('TEST_END')
                except Exception as exc:result['cleanup_error']=repr(exc)
            rawhost.close()
            (out/'values.json').write_text(json.dumps(values,indent=2),encoding='utf-8')
            (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return 0 if result['status']=='COMPLETE' else 1

if __name__=='__main__':raise SystemExit(main())
