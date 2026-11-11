"""ATE試験CSV回収後、RAMだけのD4観測を実行し、双方の原本hashを照合する。"""
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import time
import serial
from mpremote.transport_serial import SerialTransport

OUT = Path(__file__).resolve().parent


def main():
    seq = json.loads((OUT/'ate_sequence.json').read_text(encoding='utf-8'))
    assert seq['completed']
    record = dict(started_jst=datetime.now(timezone(timedelta(hours=9))).isoformat(),
                  files=[], completed=False, normal_app_restarted=False)
    def save():
        (OUT/'recovery.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    repl = SerialTransport('COM6',wait=2)
    def checked(command):
        raw,err = repl.exec_raw(command,timeout=30)
        assert not err,err
        return raw
    def chunked(expression):
        meta=json.loads(checked('_blob='+expression+"; print(__import__('json').dumps({'size':len(_blob),'sha256':__import__('binascii').hexlify(__import__('hashlib').sha256(_blob).digest()).decode()}))").decode())
        data=bytearray()
        for offset in range(0,meta['size'],256):
            chunk=bytes.fromhex(checked("print(__import__('binascii').hexlify(_blob["+str(offset)+':'+str(offset+256)+']).decode())').decode().strip())
            assert len(chunk)==min(256,meta['size']-offset)
            data.extend(chunk)
        assert hashlib.sha256(data).hexdigest()==meta['sha256']
        return bytes(data),meta
    def latest_csv(kind):
        paths=json.loads(checked("import os,json; print(json.dumps(['/sd/'+b+'/'+n for b in ('BANK_A','BANK_B') for n in os.listdir('/sd/'+b) if n.endswith('.csv') and '_T' in n]))").decode())
        path=max(paths,key=lambda p:int(p.rsplit('_T',1)[1][:-4]))
        data,meta=chunked('open('+repr(path)+",'rb').read()")
        target=OUT/Path(path).name
        with target.open('xb') as f:f.write(data)
        row=dict(kind=kind,sd_path=path,local=target.name,sd_pc_hash_match=True,**meta)
        record['files'].append(row);save()
        return path
    try:
        repl.enter_raw_repl(soft_reset=False)
        record['unique_id']=repl.eval("__import__('binascii').hexlify(__import__('machine').unique_id()).decode()")
        assert record['unique_id']=='69f7d45962cfdfad'
        record['read_contracts']=repl.eval("__import__('sys').modules['src.nf55_command'].READ_REFRESH_COMMANDS")
        assert record['read_contracts']['D4_MAINT_READ']==('D4','D4',100,212)
        first=latest_csv('ATE_D1_D2_D3_D5')
        assert Path(first).name[:15]>=seq['rtc_before']
        # 通常アプリとSDを終了済みの状態から、新しいRAM計測用インタープリターへ。
        repl.enter_raw_repl(soft_reset=True)
        stdout=checked((OUT/'d4_ram_probe.py').read_text(encoding='utf-8'))
        (OUT/'d4_ram_stdout.txt').write_bytes(stdout)
        data,meta=chunked('timing_json.encode()')
        with (OUT/'d4_observation.json').open('xb') as f:f.write(data)
        result=json.loads(data.decode())
        record['d4_result_sha256']=meta['sha256']
        assert result['completed'] and len(result['rows'])==10,result.get('error')
        second=latest_csv('RAM_D4_OBSERVATION')
        assert second!=first
        record['completed']=True
        print('D4 ACK to full:',[r['ack_to_full_response_ms'] for r in result['rows']],flush=True)
    except Exception as exc:
        record['error']=repr(exc)
        raise
    finally:
        save()
        repl.exit_raw_repl();repl.serial.write(b'\x04');time.sleep(2);repl.close()
    with serial.Serial('COM20',115200,timeout=2,write_timeout=2) as port:
        for command in ('*IDN?','COMM_STATUS?','SD_STATUS?','PICO_SELF_CHECK?','LOG_DROP_COUNT?'):
            time.sleep(0.15);port.write((command+'\r\n').encode());raw=port.read_until(b'\n')
            answer=raw.decode('ascii').rstrip('\r\n')
            record.setdefault('after_restart',[]).append(dict(command=command,response=answer))
            save();print(command,'=>',answer,flush=True)
            assert raw.endswith(b'\r\n')
            if command=='*IDN?':assert answer.startswith('NF55G_PICO_FIXTURE,')
            elif command=='COMM_STATUS?':assert answer=='OK:state=IDLE'
            elif command=='PICO_SELF_CHECK?':assert answer.startswith('OK:')
            elif command=='LOG_DROP_COUNT?':assert answer=='0'
            else:assert answer=='OK'
    record['normal_app_restarted']=True;save()


if __name__=='__main__':main()
