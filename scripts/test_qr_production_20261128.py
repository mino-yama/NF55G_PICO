"""通常ATE/実SD/実スキャナーのQR統合試験。親の製品UARTは割り当てない。"""
import argparse
import hashlib
import json
from pathlib import Path
from queue import Queue,Empty
import subprocess
import sys
from threading import Thread
import time
import serial
import winsound

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/QR_Production_Integration_20261128_Rev0'

PARENT=r'''
import sys,time,json,binascii,struct,gc,os
from src.main import FixtureApp
from src.logger import Logger
from src.sd_sink import FileSDSink
original=sys.modules['src.main'].active_app
assert not original.logger.active and not original.logger.test_running and not original._comm_busy()
assert original.qr_write.arm_host and original.ate_uart.any()==0
assert not original.qr_write.active
class TracePort:
    def __init__(self,port):self.port=port;self.line=bytearray();self.events=[];self.drops=0
    def any(self):return self.port.any()
    def write(self,data):return self.port.write(data)
    def take_error(self):return self.port.take_error()
    def read(self,count):
        data=self.port.read(count)
        for b in data:
            if b==10:
                line=bytes(self.line);self.line=bytearray()
                if len(line)!=153 or line[:1]!=b'@':continue
                seq,ms,kind,addr,instance,size,payload=struct.unpack('<IIBBBB64s',binascii.unhexlify(line[1:]))
                event={'seq':seq,'ms':ms,'kind':kind}
                if kind==14 and size==24:event['health']=list(struct.unpack('<6I',payload[:24]))
                elif kind==16 and size==25:event.update(id=payload[:24].decode(),discard=payload[24])
                elif kind==17 and size==59:event.update(id=payload[:24].decode(),text=payload[24:59].decode())
                else:continue
                if len(self.events)<64:self.events.append(event)
                else:self.drops+=1
            elif len(self.line)<155:self.line.append(b)
            else:self.line=bytearray()
        return data
port=TracePort(original.qr_write.transport)
os.mkdir(sdroot)
sink=FileSDSink(sdroot);sink.mount()
candidate=FixtureApp(ate_uart=original.ate_uart,clock=original.clock,rtc=original.rtc,
    logger=Logger(sink,clock=original.clock,rtc=original.rtc),qr_transport=port,qr_host_arm=True)
assert candidate.protocol is None and candidate.nf55_uart is None
print('QR_TEST_READY')
started=time.ticks_ms()
try:
    while time.ticks_diff(time.ticks_ms(),started)<1200000:
        candidate.service_once()
        while port.events:print('QR_TRACE|'+json.dumps(port.events.pop(0)))
        time.sleep_ms(1)
finally:
    if candidate.logger.active or candidate.logger.test_running:candidate.execute_ate_line('TEST_END')
    original.qr_write.line=bytearray();original.qr_write.last_seq=None
    print('QR_TEST_STOP|'+json.dumps({'drop':candidate.logger.drop_count,'trace_drop':port.drops}))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('normal','late'))
    parser.add_argument('--run',required=True)
    args=parser.parse_args()
    assert args.run.startswith(args.phase+'_') and args.run.replace('_','').isalnum()
    out=CASE/args.run;out.mkdir()
    sdroot='/sd/qr_prod_20261128_'+args.run
    script=out/'parent.py';script.write_text('sdroot='+repr(sdroot)+'\n'+PARENT,encoding='utf-8')
    sample=json.loads((ROOT/'docs/QR_Hardware_Integration_20261123_01/Production_Label_Retest_20261125/expected.json').read_text(encoding='utf-8'))['B']
    records=Queue();wire=[];sets=[]
    base=[sys.executable,'-u','-m','mpremote','connect','COM6','resume']
    def trace(stream,log):
        for line in stream:
            log.write(line);log.flush()
            if line.startswith('QR_TRACE|'):
                item=json.loads(line[len('QR_TRACE|'):]);item['pc_time']=time.monotonic();records.put(item)
            elif line.startswith('QR_TEST_'):records.put({'message':line.strip(),'pc_time':time.monotonic()})
        records.put({'ended':True})
    def wait(timeout,predicate):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            try:r=records.get(timeout=min(1,end-time.monotonic()))
            except Empty:continue
            if r.get('ended'):raise RuntimeError('parent stopped; see parent_wire.log')
            if predicate(r):return r
        raise TimeoutError('expected scanner/HOST event missing')
    def cue(label):
        print('SCAN_'+label,flush=True)
        if label=='A':
            winsound.Beep(500,150);time.sleep(.1);winsound.Beep(500,150)
        else:winsound.Beep(1400,220)
    parent=None;reader=None
    with (out/'parent_wire.log').open('x',encoding='utf-8') as log:
        try:
            parent=subprocess.Popen(base+['run',str(script)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
            reader=Thread(target=trace,args=(parent.stdout,log),daemon=True);reader.start()
            wait(20,lambda r:r.get('message')=='QR_TEST_READY')
            wait(10,lambda r:r.get('kind')==14 and r['health'][-1]&1 and not r['health'][2])
            with serial.Serial('COM7',57600,timeout=.1) as ate:
                assert not ate.in_waiting
                def ask(cmd):
                    start=time.monotonic();ate.write(cmd.encode()+b'\r');ate.flush();raw=bytearray()
                    while time.monotonic()-start<15:
                        b=ate.read(1)
                        if b:
                            raw.extend(b)
                            if b==b'\r':break
                    reply=raw.decode('ascii').rstrip('\r')
                    event={'command':cmd,'reply':reply,'elapsed_ms':(time.monotonic()-start)*1000,'time':time.time()};wire.append(event)
                    with (out/'ate_wire.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\n')
                    assert raw.endswith(b'\r'),event
                    time.sleep(.11);return reply
                def start_scan():
                    response=ask('QR_SCAN 60000');assert response.startswith('OK:QR_PENDING:'),response
                    token=response.split(':')[-1];hostid=token[1:17].upper()+token[-8:]
                    ack=wait(10,lambda r:r.get('kind')==16 and r['id']==hostid)
                    assert ask('QR_GET? '+token)=='ERR:QR_READING'
                    return token,hostid,ack
                assert ask('*IDN?')=='NF55G_PICO_FIXTURE,Rev.0'
                for number in range(1,21 if args.phase=='normal' else 11):
                    assert ask('TEST_START')=='OK'
                    progress=None
                    if args.phase=='normal':
                        token,hostid,ack=start_scan();assert ack['discard']==0,ack
                    else:
                        for attempt in range(1,6):
                            cutoff=time.monotonic()
                            baseline=wait(5,lambda r:r.get('kind')==14 and r['pc_time']>cutoff)
                            completed,hid=baseline['health'][3:5];cue('A')
                            end=time.monotonic()+60
                            while True:
                                h=wait(max(.1,end-time.monotonic()),lambda r:r.get('kind')==14)
                                assert not h['health'][2] and h['health'][-1]&1,h
                                if h['health'][3]!=completed:
                                    completed,hid=h['health'][3:5]
                                    print('A_COMPLETED_BEFORE_ARM; RETRY_A',flush=True);cue('A');continue
                                if h['health'][4]>hid:break
                            progress=h
                            token,hostid,ack=start_scan()
                            if ack['discard']==1:break
                            assert ask('QR_CANCEL')=='OK'
                            print('DISCARD_CONDITION_NOT_CAPTURED; RETRY_A',flush=True)
                        else:raise RuntimeError('late condition not captured after five attempts')
                    cue('B')
                    text=wait(55,lambda r:r.get('kind')==17 and r['id']==hostid)
                    assert text['text']==sample['payload'],text
                    assert ask('QR_GET? '+token)=='OK:QR_GET:'+token+':'+sample['payload']
                    assert ask('QR_DATA? '+token)=='OK:QR_DATA:'+token+':'+sample['ss_data_hex'].lower()
                    assert ask('QR_WRITE '+token)=='ERR:NF55G_NOT_CONNECTED'
                    assert ask('TEST_END')=='OK'
                    assert 'TEST_LOGGER=OK;TEST_LOG_DROP=OK' in ask('PICO_SELF_CHECK?')
                    assert ask('LOG_DROP_COUNT?')=='0'
                    assert ask('QR_GET? '+token)=='ERR:QR_STALE_ID'
                    sets.append({'set':number,'token':token,'host_id':hostid,'progress':progress,'ack':ack,'text':text,'source':'REAL_SCANNER','drop':0})
                    (out/'sets.json').write_text(json.dumps(sets,indent=2),encoding='utf-8')
                    print('SET_OK '+args.phase+' '+str(number)+'/'+str(20 if args.phase=='normal' else 10),flush=True)
                winsound.Beep(1800,150);winsound.Beep(1800,150);winsound.Beep(1800,150)
        finally:
            if parent and parent.poll() is None:
                parent.terminate();parent.wait(timeout=10)
            if reader:reader.join(timeout=3)
            subprocess.run(base+['exec','--no-follow',"import sys;sys.modules['src.main'].active_app.run()"],cwd=ROOT,timeout=20,check=True)
    result={'phase':args.phase,'sets':len(sets),'expected':20 if args.phase=='normal' else 10,'sd_root':sdroot,'product_uart_assigned':False,'max_ate_ms':max(r['elapsed_ms'] for r in wire)}
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    assert result['sets']==result['expected'];print('PHASE_COMPLETE '+args.phase,flush=True)


if __name__=='__main__':main()
