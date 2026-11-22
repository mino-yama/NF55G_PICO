import contextlib,csv,datetime,hashlib,io,json,os,re,subprocess,sys,time
from pathlib import Path
import serial
import threading
ROOT=Path.cwd()
OUT=ROOT/'docs'/('ATE_SD_Check_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
OUT.mkdir(exist_ok=False)
BASE=[sys.executable,'-B','-m','mpremote','connect','COM6','resume']
records=[]; raw=bytearray(); host_raw=bytearray(); failure=None
code="""import machine,binascii,json,time,hashlib
assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'
assert not app.running and not app._comm_busy() and app.protocol.state=='IDLE'
assert not app.logger.active and not app.logger.test_running and not app.logger.queue
assert not app.server.has_work()
assert app.external_link.fault and not app.external_link._tx and app.external_link._active is None
assert not app.external_link.transport.tx.active() and not app.external_link.transport.rx.active()
assert app.logger.sd_sink.usage()['used_percent']<40
assert app.logger.sd_sink.bank_bytes[app.logger.sd_sink.bank]<app.logger.sd_sink.capacity_bytes*0.4
check_nonce=app.external_link.parent_nonce
check_old=app.logger.sd_sink.open_filename
def check_hash(p):
 h=hashlib.sha256();n=0;f=open(p,'rb')
 while True:
  b=f.read(1024)
  if not b:break
  h.update(b);n+=len(b)
 f.close()
 return {'filename':p,'bytes':n,'sha256':binascii.hexlify(h.digest()).decode()}
check_before=check_hash(check_old)
print('BEFORE|'+json.dumps(check_before))
check_start=time.ticks_ms()
try:
 while time.ticks_diff(time.ticks_ms(),check_start)<30000:
  app.service_once();time.sleep_ms(1)
finally:
 if app.logger.active:app.logger.log_cont_stop()
 print('AFTER|'+json.dumps({'old_log':check_hash(check_old),'new_log':check_hash(app.logger.sd_sink.open_filename),'drop':app.logger.drop_count,'queue':len(app.logger.queue),'active':app.logger.active,'sd_status':app.logger.status(),'nf_state':app.protocol.state,'external_fault':app.external_link.fault,'nonce_preserved':app.external_link.parent_nonce==check_nonce,'sm4':bool(app.external_link.transport.tx.active()),'sm5':bool(app.external_link.transport.rx.active()),'ate_error':app.ate_error,'ate_pending':len(app.server.pending),'ate_tx_bytes':len(app.server.tx),'running':app.running}))
"""
(OUT/'device_check.py').write_text(code,encoding='utf-8')
proc=None
try:
 with contextlib.ExitStack() as stack:
  def port(name,baud):
   p=serial.Serial(port=None,baudrate=baud,timeout=0,write_timeout=1);p.port=name;p.dtr=False;p.rts=False;p.open();return stack.enter_context(p)
  ate=port('COM7',57600);host=port('COM22',115200)
  time.sleep(.15)
  if ate.in_waiting:raise RuntimeError('unexpected pre-existing ATE bytes; no requests sent')
  if host.in_waiting:host_raw.extend(host.read(host.in_waiting))
  proc=subprocess.Popen([sys.executable,'-u']+BASE[1:]+['exec',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT)
  captured=[];ready=threading.Event()
  def collect_stdout():
   for line in iter(proc.stdout.readline,b''):
    captured.append(line)
    if line.startswith(b'BEFORE|'):ready.set()
  reader=threading.Thread(target=collect_stdout,daemon=True);reader.start()
  if not ready.wait(12):
   if proc.poll() is not None:
    reader.join(1)
    (OUT/'device_stdout.raw').write_bytes(b''.join(captured));(OUT/'device_stderr.raw').write_bytes(proc.stderr.read())
   raise RuntimeError('RAM service readiness not confirmed; no ATE requests sent')
  def exchange(cmd,expected):
   if proc.poll() is not None:raise RuntimeError('RAM service stopped before request')
   start=time.monotonic();reply=bytearray();ate.write(cmd)
   while time.monotonic()-start<3:
    if ate.in_waiting:reply.extend(ate.read(ate.in_waiting))
    if host.in_waiting:host_raw.extend(host.read(host.in_waiting))
    if reply.count(13)>=len(expected):break
    time.sleep(.001)
   raw.extend(reply)
   entry={'command_hex':cmd.hex(),'reply_hex':reply.hex(),'elapsed_ms':round((time.monotonic()-start)*1000,3),'expected':[x.decode('ascii') for x in expected]}
   records.append(entry)
   if bytes(reply)!=b'\r'.join(expected)+b'\r':raise RuntimeError('ATE response mismatch '+repr(entry))
  exchange(b'*IDN?\rSD_STATUS?\rRTC_CHECK?\rLOG_DROP_COUNT?\r',[b'NF55G_PICO_FIXTURE,Rev.0',b'OK',b'OK',b'0'])
  exchange(b'LOG_CONT_START\r',[b'OK'])
  for bad,expected in [(b'UNKNOWN_ATE_TEST',b'ERR:UNKNOWN_CMD'),(b'\xff',b'ERR:ASCII'),(b'\x03',b'ERR:FRAME'),(b'X'*513,b'ERR:LINE_TOO_LONG')]:
   exchange(bad+b'\r*IDN?\r',[expected,b'NF55G_PICO_FIXTURE,Rev.0'])
  exchange(b'\r\n*IDN?\r\nSD_STATUS?\n',[b'NF55G_PICO_FIXTURE,Rev.0',b'OK'])
  for index in range(100):
   exchange(b'*IDN?\rSD_STATUS?\rRTC_CHECK?\rLOG_DROP_COUNT?\r',[b'NF55G_PICO_FIXTURE,Rev.0',b'OK',b'OK',b'0'])
  exchange(b'LOG_CONT_STOP\r',[b'OK'])
  exchange(b'LOG_DROP_COUNT?\rSD_STATUS?\r*IDN?\r',[b'0',b'OK',b'NF55G_PICO_FIXTURE,Rev.0'])
  print('ATE_OK bursts=100 malformed=4 recovery=4',flush=True)
  proc.wait(timeout=38);reader.join(2);stdout=b''.join(captured);stderr=proc.stderr.read()
  if host.in_waiting:host_raw.extend(host.read(host.in_waiting))
  (OUT/'device_stdout.raw').write_bytes(stdout);(OUT/'device_stderr.raw').write_bytes(stderr)
  if proc.returncode:raise RuntimeError('RAM service failed: '+stderr.decode('utf-8','replace'))
  lines=stdout.decode('utf-8','replace').splitlines()
  before=json.loads(next(x.split('|',1)[1] for x in lines if x.startswith('BEFORE|')))
  after=json.loads(next(x.split('|',1)[1] for x in lines if x.startswith('AFTER|')))
  (OUT/'device_snapshot.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
  assert before==after['old_log'],'prior log changed'
  assert after['drop']==0 and after['queue']==0 and not after['active'] and after['sd_status']=='OK'
  assert after['external_fault'] and after['nonce_preserved'] and not after['sm4'] and not after['sm5']
  assert after['nf_state']=='IDLE' and after['ate_error'] is None and after['ate_pending']==0 and after['ate_tx_bytes']==0
  assert after['new_log']['filename']!=before['filename'],'no new log created'
  snap=after['new_log'];assert re.fullmatch(r'/sd/BANK_[AB]/[0-9_]+\.csv',snap['filename'])
  dest=OUT/Path(snap['filename']).name
  cp=subprocess.run(BASE+['fs','cp',':'+snap['filename'],str(dest)],capture_output=True,timeout=30)
  (OUT/'export_stdout.raw').write_bytes(cp.stdout);(OUT/'export_stderr.raw').write_bytes(cp.stderr)
  assert cp.returncode==0,'SD export failed'
  data=dest.read_bytes();assert len(data)==snap['bytes'] and hashlib.sha256(data).hexdigest()==snap['sha256'],'SD hash mismatch'
  rows=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
  assert all(None not in r and all(v is not None for v in r.values()) for r in rows),'malformed CSV rows'
  from collections import Counter
  counts=Counter((r['category'],r['event']) for r in rows)
  assert sum(r['category']=='ATE' and r['event']=='REQUEST' and r['detail']=='*IDN?' for r in rows)==105
  assert sum(r['category']=='ATE' and r['event']=='RESULT' and r['detail']=='*IDN?' and r['result']=='NF55G_PICO_FIXTURE,Rev.0' for r in rows)==105
  assert sum(r['category']=='ATE' and r['event']=='RECEIVE_ERROR' for r in rows)==3
  result={'status':'PASS','bursts':100,'malformed_cases':4,'malformed_recovery_pass':4,'exchanges':len(records),'reply_count':sum(len(r['expected']) for r in records),'max_exchange_ms':max(r['elapsed_ms'] for r in records),'csv_rows':len(rows),'csv_bytes':len(data),'device_sha_matches':True,'previous_log_unchanged':True,'category_event_counts':{str(k):v for k,v in counts.items()},'drop':after['drop'],'queue':after['queue'],'host_monitor_bytes':len(host_raw),'nf_commands_sent':0,'external_commands_sent':0,'qr_test_date':'2026-11-23','qr_status':'installation planned by user; not tested','final_state':'parent stopped; SM4/5 stopped; CDC fault preserved'}
except Exception as exc:
 failure=repr(exc);result={'status':'INCOMPLETE','failure':failure,'exchanges':len(records),'qr_test_date':'2026-11-23','qr_status':'installation planned by user; not tested'}
 if proc is not None and proc.poll() is None:
  try:
   proc.wait(timeout=38);reader.join(2);stdout=b''.join(captured);stderr=proc.stderr.read();(OUT/'device_stdout.raw').write_bytes(stdout);(OUT/'device_stderr.raw').write_bytes(stderr)
  except subprocess.TimeoutExpired:result['service_exit']='bounded RAM service did not return; requires inspection'
finally:
 (OUT/'ate.raw').write_bytes(raw);(OUT/'host.raw').write_bytes(host_raw)
 (OUT/'requests.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'Result.md').write_text('# ATE / SD check\n\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n\nQR installation and hardware testing planned for 2026-11-23. CDC .22.3 not deployed by this test.\n',encoding='utf-8')
 print('OUT='+str(OUT),flush=True);print(json.dumps(result,ensure_ascii=False),flush=True)
if failure:sys.exit(1)
