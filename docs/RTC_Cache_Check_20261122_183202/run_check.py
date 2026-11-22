import contextlib,datetime,hashlib,json,subprocess,sys,threading,time
from pathlib import Path
import serial
ROOT=Path.cwd();OUT=ROOT/'docs'/('RTC_Cache_Check_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));OUT.mkdir(exist_ok=False)
BASE=[sys.executable,'-u','-B','-m','mpremote','connect','COM6','resume']
code="""import machine,binascii,json,time,hashlib
from src.nf55_command import STATUS_QUERY_FIELDS
assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'
assert not app.running and not app._comm_busy() and app.protocol.state=='IDLE'
assert not app.logger.active and not app.logger.test_running and not app.logger.queue
assert not app.server.has_work()
assert app.external_link.fault and not app.external_link._tx and app.external_link._active is None
assert not app.external_link.transport.tx.active() and not app.external_link.transport.rx.active()
def rtc_cache_hash(p):
 h=hashlib.sha256();n=0;f=open(p,'rb')
 while True:
  b=f.read(1024)
  if not b:break
  h.update(b);n+=len(b)
 f.close()
 return {'bytes':n,'sha256':binascii.hexlify(h.digest()).decode()}
rc_nonce=app.external_link.parent_nonce
rc_oldlog=app.logger.sd_sink.open_filename
rc_oldhash=rtc_cache_hash(rc_oldlog)
rc_other={n:(app.cache.metadata(n),app.cache.get(n)) for n in app.cache._entries if n!='STATUS'}
rc_before_status=app.cache.metadata('STATUS')
rc_status_reg=app.rtc.device.read_status()
rc_source={n:rtc_cache_hash('src/'+n+'.py') for n in ('cache_manager','command_dispatcher','rtc_driver','nf55_command')}
rc_original_protocol=app.dispatcher.protocol
class RTCCacheProtocolObserver:
 def __init__(self,original):self.original=original;self.calls=[]
 def __getattr__(self,n):return getattr(self.original,n)
 def transact(self,cmd,**kw):
  self.calls.append({'cmd':cmd,'target_invalid_before_tx':not app.cache.is_valid('STATUS')})
  assert cmd=='D1' and len(self.calls)==1 and not app.cache.is_valid('STATUS')
  result=self.original.transact(cmd,**kw)
  self.calls[-1].update({'ok':result.ok,'error':result.error,'ambiguous':result.ambiguous,'elapsed_ms':result.elapsed_ms,'cmd_retry':result.command_retry_count,'rsp_retry':result.response_retry_count})
  return result
rc_observer=RTCCacheProtocolObserver(rc_original_protocol)
app.dispatcher.protocol=rc_observer
app.cache.invalidate('STATUS')
print('READY|'+json.dumps({'queries':[q+'?' for q in STATUS_QUERY_FIELDS],'rtc_status':rc_status_reg,'source':rc_source,'before_status':rc_before_status}))
rc_start=time.ticks_ms();rc_first_valid=None
try:
 while time.ticks_diff(time.ticks_ms(),rc_start)<32000:
  app.service_once()
  if rc_first_valid is None and app.cache.is_valid('STATUS'):rc_first_valid=app.cache.metadata('STATUS')
  time.sleep_ms(1)
finally:
 app.dispatcher.protocol=rc_original_protocol
 print('FINAL|'+json.dumps({'calls':rc_observer.calls,'status_metadata':app.cache.metadata('STATUS'),'first_valid_metadata':rc_first_valid,'status_data':app.cache.get('STATUS'),'other_caches_unchanged':all(rc_other[n]==(app.cache.metadata(n),app.cache.get(n)) for n in rc_other),'rtc_status_before':rc_status_reg,'rtc_status_after':app.rtc.device.read_status(),'old_log_unchanged':rc_oldhash==rtc_cache_hash(rc_oldlog),'external_fault':app.external_link.fault,'nonce_preserved':app.external_link.parent_nonce==rc_nonce,'sm4':bool(app.external_link.transport.tx.active()),'sm5':bool(app.external_link.transport.rx.active()),'nf_state':app.protocol.state,'log_active':app.logger.active,'log_drop':app.logger.drop_count,'queue':len(app.logger.queue),'ate_error':app.ate_error,'ate_pending':len(app.server.pending),'ate_tx_bytes':len(app.server.tx),'running':app.running,'dispatcher_protocol_restored':app.dispatcher.protocol is rc_original_protocol}))
"""
(OUT/'device_check.py').write_text(code,encoding='utf-8')
records=[];raw=bytearray();host_raw=bytearray();captured=[];proc=None;reader=None;failure=None;rtc_samples=[];valid_queries=[]
try:
 with contextlib.ExitStack() as stack:
  def port(name,baud):
   p=serial.Serial(port=None,baudrate=baud,timeout=0,write_timeout=1);p.port=name;p.dtr=False;p.rts=False;p.open();return stack.enter_context(p)
  ate=port('COM7',57600);host=port('COM22',115200)
  if ate.in_waiting:raise RuntimeError('unexpected ATE input before test')
  ready=threading.Event()
  proc=subprocess.Popen(BASE+['exec',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  def collect():
   for line in iter(proc.stdout.readline,b''):
    captured.append(line)
    if line.startswith(b'READY|'):ready.set()
  reader=threading.Thread(target=collect,daemon=True);reader.start()
  if not ready.wait(12):raise RuntimeError('RAM readiness not confirmed; no ATE requests sent')
  pre=json.loads(next(l.split(b'|',1)[1] for l in captured if l.startswith(b'READY|')))
  for name,snap in pre['source'].items():
   data=(ROOT/'src'/(name+'.py')).read_bytes();assert len(data)==snap['bytes'] and hashlib.sha256(data).hexdigest()==snap['sha256'],'local/device source mismatch '+name
  def exchange(commands,expected=None):
   start=time.monotonic();wall=datetime.datetime.now();wire=b''.join(c.encode('ascii')+b'\r' for c in commands);reply=bytearray()
   if proc.poll() is not None:raise RuntimeError('RAM service stopped')
   ate.write(wire)
   while time.monotonic()-start<4:
    if ate.in_waiting:reply.extend(ate.read(ate.in_waiting))
    if host.in_waiting:host_raw.extend(host.read(host.in_waiting))
    if reply.count(13)>=len(commands):break
    time.sleep(.001)
   raw.extend(reply);parts=bytes(reply).split(b'\r');elapsed=time.monotonic()-start
   record={'commands':commands,'reply_hex':reply.hex(),'elapsed_ms':round(elapsed*1000,3),'pc_time_start':wall.isoformat(),'pc_time_end':datetime.datetime.now().isoformat()};records.append(record)
   assert len(parts)==len(commands)+1 and parts[-1]==b'','reply boundary mismatch'
   values=[p.decode('ascii') for p in parts[:-1]];record['replies']=values
   if expected is not None:assert values==expected,'response content mismatch '+repr(record)
   return values
  queries=pre['queries'];assert len(queries)==37
  for i in range(0,len(queries),4):exchange(queries[i:i+4],['ERR:CACHE_INVALID']*len(queries[i:i+4]))
  exchange(['STATUS_REFRESH'],['OK'])
  for cycle in range(2):
   values={}
   for i in range(0,len(queries),4):
    batch=queries[i:i+4];answers=exchange(batch)
    assert all(v in ('0','1') for v in answers),'status value outside expected boolean representation'
    values.update(zip(batch,answers))
   valid_queries.append(values)
  assert valid_queries[0]==valid_queries[1],'cache queries changed without refresh'
  replies=exchange(['RTC_DATE?','RTC_TIME?','RTC_DATETIME?','RTC_CHECK?'])
  assert replies[3]=='OK'
  for text,fmt in zip(replies[:3],['%Y%m%d','%H%M%S','%Y%m%d_%H%M%S']):datetime.datetime.strptime(text,fmt)
  for i in range(6):
   start=time.monotonic();wall0=datetime.datetime.now();value=exchange(['RTC_DATETIME?'],None)[0];wall1=datetime.datetime.now();dt=datetime.datetime.strptime(value,'%Y%m%d_%H%M%S')
   rtc_samples.append({'rtc':value,'pc_start':wall0.isoformat(),'pc_end':wall1.isoformat(),'monotonic':start,'offset_from_pc_midpoint_seconds':(dt-(wall0+(wall1-wall0)/2)).total_seconds()})
   if i<5:time.sleep(1)
  span=(datetime.datetime.strptime(rtc_samples[-1]['rtc'],'%Y%m%d_%H%M%S')-datetime.datetime.strptime(rtc_samples[0]['rtc'],'%Y%m%d_%H%M%S')).total_seconds()
  elapsed=rtc_samples[-1]['monotonic']-rtc_samples[0]['monotonic'];assert span>0 and abs(span-elapsed)<=1.5,'RTC did not advance as expected'
  print('RTC_PROGRESS_OK cache_invalid=37 cache_valid=74',flush=True)
  proc.wait(timeout=38);reader.join(2);stdout=b''.join(captured);stderr=proc.stderr.read()
  (OUT/'device_stdout.raw').write_bytes(stdout);(OUT/'device_stderr.raw').write_bytes(stderr)
  assert proc.returncode==0,'RAM execution failed'
  final=json.loads(next(l.split(b'|',1)[1] for l in captured if l.startswith(b'FINAL|')))
  (OUT/'device_snapshot.json').write_text(json.dumps(final,indent=2),encoding='utf-8')
  assert len(final['calls'])==1 and final['calls'][0]['cmd']=='D1' and final['calls'][0]['ok'] and final['calls'][0]['target_invalid_before_tx']
  assert final['status_metadata']['valid'] and final['status_metadata']['source_cmd']=='D1' and final['status_metadata']==final['first_valid_metadata']
  for query,value in valid_queries[0].items():assert str(int(final['status_data'][query[:-1]]))==value
  for key in ['other_caches_unchanged','old_log_unchanged','external_fault','nonce_preserved','dispatcher_protocol_restored']:assert final[key],key
  for key in ['running','sm4','sm5','log_active','log_drop','queue','ate_pending','ate_tx_bytes']:assert not final[key],key
  assert final['nf_state']=='IDLE' and final['ate_error'] is None
  result={'status':'PASS','rtc_samples':rtc_samples,'rtc_advance_seconds':span,'pc_elapsed_seconds':round(elapsed,3),'rtc_osf_before':bool(pre['rtc_status']&128),'rtc_osf_after':bool(final['rtc_status_after']&128),'invalid_status_queries':37,'valid_status_queries':74,'real_nf_transactions':final['calls'],'query_triggered_nf_transactions':0,'metadata_unchanged_by_query':True,'other_caches_unchanged':True,'rtc_settings_written':False,'host_monitor_bytes':len(host_raw),'local_device_source_sha_matches':True,'final_state':'parent stopped; CDC fault and SM4/5 stopped preserved; STATUS valid from actual D1'}
except Exception as exc:
 failure=repr(exc);result={'status':'INCOMPLETE','failure':failure,'exchanges':len(records)}
 if proc is not None:
  if proc.poll() is None:
   try:proc.wait(timeout=38)
   except subprocess.TimeoutExpired:result['runtime_exit']='requires inspection'
  if reader:reader.join(2)
  (OUT/'device_stdout.raw').write_bytes(b''.join(captured))
  if proc.poll() is not None:(OUT/'device_stderr.raw').write_bytes(proc.stderr.read())
finally:
 (OUT/'ate.raw').write_bytes(raw);(OUT/'host.raw').write_bytes(host_raw)
 (OUT/'requests.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('OUT='+str(OUT),flush=True);print(json.dumps(result,ensure_ascii=False),flush=True)
if failure:sys.exit(1)
modules=['tests.test_rtc_driver','tests.test_read_cache_integration','tests.test_control_cache_integration','tests.test_frame_cache_decode']
p=subprocess.run([sys.executable,'-B','-m','unittest','-v']+modules,capture_output=True,timeout=50)
(OUT/'Host_RTC_Cache_Unit.log').write_bytes(p.stdout+p.stderr)
print('HOST_UNIT_EXIT='+str(p.returncode),flush=True);print((p.stdout+p.stderr).decode('utf-8','replace')[-250:],flush=True)
if p.returncode:sys.exit(p.returncode)
