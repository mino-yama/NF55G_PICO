"""実ATEでQR二連続→照会→確定SS一回→明示D5照合。各応答を保存する。"""
import json
from pathlib import Path
import subprocess
import time
import serial
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
from src.qr_write_session import serial_data_from_qr

RUN=OUT/'SS_HIL_01'
RUN.mkdir(exist_ok=False)
log=(RUN/'parent.log').open('wb')
p=subprocess.Popen([str(ROOT/'.venv/Scripts/python.exe'),'-u','-m','mpremote','connect','COM6','resume','run',str(OUT/'ss_hil_parent.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
result={'status':'RUNNING','operations':[]}

def save():
    (RUN/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

def parent_text():
    return (RUN/'parent.log').read_text(encoding='utf-8',errors='replace')

def await_parent(marker,seconds):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if marker in parent_text():
            return
        assert p.poll() is None,parent_text()[-1200:]
        time.sleep(.2)
    raise TimeoutError(marker)

try:
    await_parent('SS_HIL_READY',20)
    with serial.Serial('COM7',57600,timeout=.2) as port:
        assert not port.read_all(),'unexpected pending ATE input'
        def command(text):
            port.write(text.encode()+b'\r');port.flush()
            raw=bytearray();deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                raw.extend(port.read(256))
                if raw.endswith(b'\r'):
                    break
            assert raw.endswith(b'\r'),(text,raw)
            reply=bytes(raw[:-1]).decode('ascii')
            result['operations'].append({'command':text,'reply':reply,'raw_hex':bytes(raw).hex()})
            save()
            return reply
        assert command('TEST_START')=='OK'
        assert command('INFO_REFRESH')=='OK'
        fields=('FW_REV','UNIT_REV','UNIT_LOT','UNIT_SERIAL','ADU_REV','ADU_LOT','ADU_SERIAL','BBU_REV','BBU_LOT','BBU_SERIAL')
        before={key:command(key+'?') for key in fields}
        # 読出し済み実機を再確認。対象が変わっていた場合はSS前に停止。
        assert before['FW_REV']=='S1.14B' and before['UNIT_REV']=='A5. '
        assert before['UNIT_LOT']=='2610' and before['UNIT_SERIAL']=='000832'
        result['before']=before
        armed=command('QR_SCAN 60000')
        assert armed.startswith('OK:QR_ARMED:')
        token=armed.split(':')[-1];result['acquisition_id']=token
        save()
        (RUN/'READ_QR_NOW.txt').write_text('QR_SCAN accepted; read same QR twice now.\n',encoding='ascii')
        print('READ_QR_TWICE_NOW',token,flush=True)
        await_parent('SS_HIL_STATE|READY|'+token,65)
        # 2件目を実受信しても保持値が差し替わらないことを確認してから書く。
        await_parent('SS_HIL_SECOND|'+token,60)
        expected='US250A-CGXE-009491-101A1.2601000001'
        assert command('QR_GET? '+token)=='OK:QR_GET:'+token+':'+expected
        data_reply=command('QR_DATA? '+token)
        assert data_reply=='OK:QR_DATA:'+token+':'+serial_data_from_qr(expected).hex()
        result['verified_ss_data_hex']=data_reply.split(':')[-1]
        assert command('QR_WRITE '+token)=='OK:QR_WRITE:'+token
        assert command('UNIT_SERIAL?')=='ERR:CACHE_INVALID'
        assert command('QR_WRITE '+token)=='ERR:QR_CONSUMED'
        assert command('INFO_REFRESH')=='OK'
        after={key:command(key+'?') for key in fields}
        expected_after=dict(before,UNIT_REV='A1. ',UNIT_LOT='2601',UNIT_SERIAL='000001')
        assert after==expected_after,(after,expected_after)
        result['after']=after
        assert command('TEST_END')=='OK'
        await_parent('SS_HIL_DONE',20)
        assert p.wait(timeout=5)==0,parent_text()[-1200:]
        text=parent_text()
        parent=json.loads(b''.join(bytes.fromhex(line.split('|',1)[1]) for line in text.splitlines() if line.startswith('SS_HIL_RESULT_HEX|')))
        result['parent']=parent
        assert parent['error'] is None and parent['nf_count']=={'SS':1,'D5':2}
        assert parent['drop']==parent['queue']==parent['sd_stats']['during_comm']==0
        assert not parent['logger_active'] and not parent['test_running'] and parent['qr_ignored']>=1
        result['status']='SS_WRITE_READBACK_SUCCESS_CSV_PENDING'
        save()
        print(json.dumps({key:result[key] for key in ('status','before','after')},ensure_ascii=False,indent=2),flush=True)
except Exception as exc:
    result['status']='STOPPED';result['error']=repr(exc);save()
    print('SS_HIL_STOPPED',repr(exc),flush=True)
    # 成否不明を自動再送しない。親有限guardもSS二回目を拒否する。
    raise
finally:
    log.close()
