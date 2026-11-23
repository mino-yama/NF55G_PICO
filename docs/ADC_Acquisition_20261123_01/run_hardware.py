"""実ATEで2試行/4取得とCache照会・旧ID拒否を確認。電流実配線の評価は行わない。"""
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import serial

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0,str(ROOT))
from src.external_instrument_link import FrameReader


if __name__ == '__main__':
    assert not (OUT/'hardware_result.json').exists()
    result = {'status':'INCOMPLETE','events':[],'acquisitions':[]}
    stop = threading.Event()
    raw_host = bytearray()
    with serial.Serial('COM22',115200,timeout=0.02) as host, serial.Serial('COM7',57600,timeout=0.02) as ate:
        def capture():
            while not stop.is_set(): raw_host.extend(host.read(4096))
        thread = threading.Thread(target=capture)
        thread.start()
        with (OUT/'hardware_parent.log').open('wb') as log:
            parent = subprocess.Popen([str(ROOT/'.venv/Scripts/python.exe'),'-u','-m','mpremote',
                'connect','COM6','resume','run',str(OUT/'hardware_parent.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            running = False
            try:
                deadline = time.monotonic()+10
                while b'ADC_HIL_READY|' not in (OUT/'hardware_parent.log').read_bytes():
                    assert parent.poll() is None,'parent failed before READY'
                    assert time.monotonic()<deadline,'parent READY timeout'
                    time.sleep(0.05)
                assert not ate.read(4096),'preexisting ATE output'

                def request(command,expected=None):
                    began=time.monotonic()
                    ate.write(command.encode('ascii')+b'\r')
                    raw=bytearray()
                    while time.monotonic()-began<5:
                        raw.extend(ate.read(4096))
                        if raw.endswith(b'\r'): break
                    reply=raw.decode('ascii').strip()
                    result['events'].append({'command':command,'response':reply,'raw_hex':raw.hex(),
                        'elapsed_ms':round((time.monotonic()-began)*1000,3)})
                    if expected is not None: assert reply==expected,(command,reply,expected)
                    return reply

                def acquire(point):
                    reply=request('CAL_MEASURE BATT_V '+point+' 2000 :READ?')
                    assert reply.startswith('OK:CAL_MEASURE:'),reply
                    identity=reply.split(':',2)[2]
                    snapshot=request('CAL_MEASUREMENT? '+identity)
                    fields=snapshot.split(':')
                    assert len(fields)==10 and fields[:2]==['OK','CAL_MEASUREMENT'],snapshot
                    assert fields[2:5]==[identity,'BATT_V',point]
                    assert fields[6]==fields[8]=='V' and fields[5]==fields[7]
                    assert bytes.fromhex(fields[9])==(fields[5]+'\r\n').encode()
                    result['acquisitions'].append({'id':identity,'point':point,'snapshot':snapshot})
                    print('ACQUIRED',identity,fields[5],'V',flush=True)
                    return identity,snapshot

                request('HOST_INFO? METER','OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261123.2:CBFA8C2C4F42C7BA:READY')
                request('CAL_MEASURE BATT_V A 2000 :READ?','ERR:CAL_NO_ACTIVE_TRIAL')
                request('TEST_START','OK'); running=True
                first,first_value=acquire('A')
                second,second_value=acquire('B')
                for _ in range(3):
                    request('CAL_MEASUREMENT? '+first,first_value)
                    request('CAL_MEASUREMENT? '+second,second_value)
                replacement,replacement_value=acquire('A')
                assert replacement!=first
                request('CAL_MEASUREMENT? '+first,'ERR:CAL_MEASUREMENT_INVALID')
                request('CAL_MEASURE BATT_V A 2000 :CONF?','ERR:CAL_MEASUREMENT_COMMAND')
                request('CAL_MEASUREMENT? '+replacement,replacement_value)
                request('TEST_END','OK'); running=False
                for identity in (second,replacement):
                    request('CAL_MEASUREMENT? '+identity,'ERR:CAL_MEASUREMENT_INVALID')
                request('TEST_START','OK'); running=True
                request('CAL_MEASUREMENT? '+replacement,'ERR:CAL_MEASUREMENT_INVALID')
                newest,_=acquire('A')
                assert newest.split('-')[0]!=first.split('-')[0]
                request('TEST_END','OK'); running=False
                request('CAL_MEASUREMENT? '+newest,'ERR:CAL_MEASUREMENT_INVALID')
                result['status']='ADC_HIL_SUCCESS'
            except Exception as exc:
                result['status']='STOPPED';result['error']=repr(exc)
                print('STOPPED',repr(exc),flush=True)
            finally:
                if running and parent.poll() is None:
                    try: request('TEST_END','OK')
                    except Exception as exc: result['cleanup_error']=repr(exc)
                parent.wait(timeout=50)
                result['parent_exit_code']=parent.returncode
                try:
                    text=(OUT/'hardware_parent.log').read_text(encoding='utf-8')
                    result['parent']=json.loads(next(line.split('|',1)[1] for line in text.splitlines() if line.startswith('ADC_HIL_DONE|')))
                    assert parent.returncode==0 and 'ADC_HIL_STOPPED_PIO_INPUT' in text
                    state=result['parent']
                    assert state['nf_write_attempts']==state['drop']==state['queue']==state['measurement_slots']==0
                    assert not state['logger_active'] and not state['test_running']
                    assert state['sd_stats']['during_comm']==0 and state['product_cache_unchanged']
                    reader=FrameReader(); frames=reader.feed(bytes.fromhex(state['tx_hex']))
                    assert reader.errors==0
                    commands=[f['payload'].decode() for f in frames if f['kind']=='Q']
                    result['instrument_commands']=commands
                    if result['status']=='ADC_HIL_SUCCESS':
                        assert commands==[':SENS:FUNC?',':READ?']*4
                except Exception as exc:
                    result['status']='STOPPED';result['parent_validation_error']=repr(exc)
                stop.set();thread.join(timeout=2)
                (OUT/'hardware_host.raw').write_bytes(raw_host)
                reader=FrameReader(); frames=reader.feed(raw_host)
                result['host_frames']=[{'kind':f['kind'],'request':f['request'],'session':f['session'].hex(),
                    'payload_text':f['payload'].decode('ascii','replace')} for f in frames]
                result['host_decode_errors']=reader.errors
                (OUT/'hardware_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
                print('RESULT',result['status'],flush=True)
    if result['status']!='ADC_HIL_SUCCESS': raise SystemExit(1)
