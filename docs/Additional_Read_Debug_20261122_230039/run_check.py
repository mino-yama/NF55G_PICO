import contextlib,csv,datetime,hashlib,io,json,subprocess,sys,threading,time
from pathlib import Path
import serial
ROOT=Path.cwd();OUT=ROOT/'docs'/('Additional_Read_Debug_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));OUT.mkdir(exist_ok=False)
BASE=[sys.executable,'-u','-B','-m','mpremote','connect','COM6','resume']
code="""import machine,binascii,json,time,hashlib
from src.nf55_command import DATA_QUERY_FIELDS,INFO_QUERY_FIELDS
assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'
assert not app.running and not app._comm_busy() and app.protocol.state=='IDLE'
assert not app.logger.active and not app.logger.test_running and not app.logger.queue and not app.server.has_work()
assert app.external_link.fault and not app.external_link._tx and app.external_link._active is None
assert not app.external_link.transport.tx.active() and not app.external_link.transport.rx.active()
assert app.logger.sd_sink.usage()['used_percent']<40
assert app.logger.sd_sink.bank_bytes[app.logger.sd_sink.bank]<app.logger.sd_sink.capacity_bytes*0.4
def more_hash(p):
 h=hashlib.sha256();n=0;f=open(p,'rb')
 while True:
  b=f.read(1024)
  if not b:break
  h.update(b);n+=len(b)
 f.close()
 return {'filename':p,'bytes':n,'sha256':binascii.hexlify(h.digest()).decode()}
more_old=more_hash(app.logger.sd_sink.open_filename)
more_nonce=app.external_link.parent_nonce
more_status=(app.cache.metadata('STATUS'),app.cache.get('STATUS'))
more_other={n:(app.cache.metadata(n),app.cache.get(n)) for n in app.cache._entries if n not in ('DATA','STATUS','INFO')}
app.cache.invalidate('DATA');app.cache.invalidate('INFO')
more_original=app.dispatcher.protocol
class MoreReadObserver:
 def __init__(self,p):self.p=p;self.calls=[];self.snapshots=[];self.query_metadata_same=None
 def __getattr__(self,n):return getattr(self.p,n)
 def transact(self,cmd,**kw):
  target={'D0':'DATA','D1':'STATUS','D5':'INFO'}[cmd]
  if len(self.calls)==2:self.query_metadata_same=all(app.cache.metadata(n)==self.snapshots[1]['metadata'][n] for n in ('DATA','INFO','STATUS'))
  assert len(self.calls)<62 and not app.cache.is_valid(target)
  r=self.p.transact(cmd,**kw)
  self.calls.append({'cmd':cmd,'ok':r.ok,'error':r.error,'elapsed_ms':r.elapsed_ms,'ambiguous':r.ambiguous,'cmd_retry':r.command_retry_count,'rsp_retry':r.response_retry_count,'response_length':len(r.response_data),'target_invalid_before_tx':True,'response_data_hex':binascii.hexlify(r.response_data).decode()})
  return r
more_observer=MoreReadObserver(more_original)
app.dispatcher.protocol=more_observer
more_seen=0
print('READY|'+json.dumps({'data_queries':DATA_QUERY_FIELDS,'info_queries':list(INFO_QUERY_FIELDS),'old_log':more_old}))
more_start=time.ticks_ms()
try:
 while time.ticks_diff(time.ticks_ms(),more_start)<40000:
  app.service_once()
  if len(more_observer.calls)>more_seen:
   more_seen=len(more_observer.calls)
   if more_seen<=2:
    more_observer.snapshots.append({'call':more_seen,'metadata':{n:app.cache.metadata(n) for n in ('DATA','STATUS','INFO')},'data':app.cache.get('DATA'),'info':app.cache.get('INFO'),'status_preserved':more_status==(app.cache.metadata('STATUS'),app.cache.get('STATUS'))})
  time.sleep_ms(1)
finally:
 if app.logger.active:app.logger.log_cont_stop()
 app.dispatcher.protocol=more_original
 print('FINAL|'+json.dumps({'calls':more_observer.calls,'initial_snapshots':more_observer.snapshots,'initial_query_metadata_same':more_observer.query_metadata_same,'other_caches_unchanged':all(more_other[n]==(app.cache.metadata(n),app.cache.get(n)) for n in more_other),'metadata':{n:app.cache.metadata(n) for n in ('DATA','STATUS','INFO')},'old_log_unchanged':more_old==more_hash(more_old['filename']),'new_log':more_hash(app.logger.sd_sink.open_filename),'external_fault':app.external_link.fault,'nonce_preserved':app.external_link.parent_nonce==more_nonce,'sm4':bool(app.external_link.transport.tx.active()),'sm5':bool(app.external_link.transport.rx.active()),'nf_state':app.protocol.state,'log_active':app.logger.active,'log_drop':app.logger.drop_count,'queue':len(app.logger.queue),'ate_error':app.ate_error,'ate_pending':len(app.server.pending),'ate_tx_bytes':len(app.server.tx),'running':app.running,'protocol_restored':app.dispatcher.protocol is more_original}))
"""
(OUT/'device_check.py').write_text(code,encoding='utf-8')
records=[];raw=bytearray();host_raw=bytearray();captured=[];proc=None;reader=None;failure=None;cycles=0;query_cycles=[]
try:
 with contextlib.ExitStack() as stack:
  def port(n,b):
   p=serial.Serial(port=None,baudrate=b,timeout=0,write_timeout=1);p.port=n;p.dtr=False;p.rts=False;p.open();return stack.enter_context(p)
  ate=port('COM7',57600);host=port('COM22',115200)
  if ate.in_waiting:raise RuntimeError('unexpected ATE bytes before test')
  ready=threading.Event();proc=subprocess.Popen(BASE+['exec',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  def collect():
   for line in iter(proc.stdout.readline,b''):
    captured.append(line)
    if line.startswith(b'READY|'):ready.set()
  reader=threading.Thread(target=collect,daemon=True);reader.start()
  if not ready.wait(12):raise RuntimeError('RAM readiness not confirmed; no ATE requests sent')
  pre=json.loads(next(x.split(b'|',1)[1] for x in captured if x.startswith(b'READY|')))
  def exchange(commands,expected=None):
   if proc.poll() is not None:raise RuntimeError('RAM service stopped')
   reply=bytearray();t=time.monotonic();ate.write(b''.join(c.encode('ascii')+b'\r' for c in commands))
   while time.monotonic()-t<5:
    if ate.in_waiting:reply.extend(ate.read(ate.in_waiting))
    if host.in_waiting:host_raw.extend(host.read(host.in_waiting))
    if reply.count(13)>=len(commands):break
    time.sleep(.001)
   raw.extend(reply);entry={'commands':commands,'reply_hex':reply.hex(),'elapsed_ms':round((time.monotonic()-t)*1000,3)};records.append(entry)
   parts=bytes(reply).split(b'\r');assert len(parts)==len(commands)+1 and not parts[-1],'ATE boundary mismatch'
   values=[x.decode('ascii') for x in parts[:-1]];entry['replies']=values
   if expected is not None:assert values==expected,'ATE content mismatch '+repr(entry)
   return values
  exchange(['*IDN?','RTC_CHECK?','SD_STATUS?','LOG_DROP_COUNT?'],['NF55G_PICO_FIXTURE,Rev.0','OK','OK','0'])
  exchange(['LOG_CONT_START'],['OK'])
  dmap=pre['data_queries'];imap={q+'?':q for q in pre['info_queries']};all_queries=list(dmap)+list(imap)
  for i in range(0,len(all_queries),4):exchange(all_queries[i:i+4],['ERR:CACHE_INVALID']*len(all_queries[i:i+4]))
  exchange(['DATA_REFRESH'],['OK']);exchange(['INFO_REFRESH'],['OK'])
  for cycle in range(2):
   values={}
   for i in range(0,len(all_queries),4):
    batch=all_queries[i:i+4];answers=exchange(batch);assert all(not a.startswith('ERR:') for a in answers)
    values.update(zip(batch,answers))
   query_cycles.append(values)
  assert query_cycles[0]==query_cycles[1],'cached values changed without refresh'
  for cycle in range(20):
   exchange(['DATA_REFRESH','STATUS_REFRESH','INFO_REFRESH','RTC_CHECK?','SD_STATUS?','LOG_DROP_COUNT?'],['OK','OK','OK','OK','OK','0']);cycles+=1
  exchange(['LOG_CONT_STOP'],['OK'])
  exchange(['LOG_DROP_COUNT?','SD_STATUS?'],['0','OK'])
  print('READ_MIX_OK cycles='+str(cycles)+' DATA/INFO_fields='+str(len(all_queries)),flush=True)
  proc.wait(timeout=47);reader.join(2);stderr=proc.stderr.read()
  (OUT/'device_stdout.raw').write_bytes(b''.join(captured));(OUT/'device_stderr.raw').write_bytes(stderr)
  assert proc.returncode==0,'RAM execution failed'
  final=json.loads(next(x.split(b'|',1)[1] for x in captured if x.startswith(b'FINAL|')))
  (OUT/'device_snapshot.json').write_text(json.dumps(final,indent=2),encoding='utf-8')
  calls=final['calls'];assert len(calls)==62 and all(c['ok'] and c['cmd_retry']==0 and c['rsp_retry']==0 for c in calls)
  assert [c['cmd'] for c in calls]==['D0','D5']+['D0','D1','D5']*20
  snapshots=final['initial_snapshots'];assert len(snapshots)==2 and all(s['status_preserved'] for s in snapshots)
  assert not snapshots[0]['metadata']['INFO']['valid'],'D0 promoted INFO'
  assert snapshots[0]['metadata']['DATA']==snapshots[1]['metadata']['DATA'],'D5 updated DATA metadata'
  for q,field in {**dmap,**imap}.items():
   value=snapshots[1]['data' if q in dmap else 'info'][field]
   expected=str(int(value)) if isinstance(value,bool) else str(value)
   assert query_cycles[0][q]==expected,'query differs from stored field '+q
  for key in ['initial_query_metadata_same','other_caches_unchanged','old_log_unchanged','external_fault','nonce_preserved','protocol_restored']:assert final[key],key
  for key in ['running','sm4','sm5','log_active','log_drop','queue','ate_pending','ate_tx_bytes']:assert not final[key],key
  assert final['nf_state']=='IDLE' and final['ate_error'] is None
  snap=final['new_log'];dest=OUT/Path(snap['filename']).name
  cp=subprocess.run(BASE+['fs','cp',':'+snap['filename'],str(dest)],capture_output=True,timeout=40)
  (OUT/'export_stdout.raw').write_bytes(cp.stdout);(OUT/'export_stderr.raw').write_bytes(cp.stderr);assert cp.returncode==0,'export failed'
  data=dest.read_bytes();assert len(data)==snap['bytes'] and hashlib.sha256(data).hexdigest()==snap['sha256'],'CSV hash mismatch'
  rows=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))));assert all(None not in r and all(v is not None for v in r.values()) for r in rows)
  expected=[]
  for item in records[1:-1]:
   for cmd,reply in zip(item['commands'],item['replies']):
    expected.append(('REQUEST','',cmd))
    if cmd!='LOG_CONT_STOP':expected.append(('RESULT',reply,cmd))
  actual=[(r['event'],r['result'],r['detail']) for r in rows if r['category']=='ATE'];assert actual==expected,'ATE log sequence mismatch'
  transactions=[r for r in rows if r['category']=='NF55' and r['event']=='TRANSACTION'];assert len(transactions)==62
  assert all(r['result']=='OK' and r['cmd_retry']=='0' and r['rsp_retry']=='0' for r in transactions)
  result={'status':'PASS','mixed_cycles':cycles,'invalid_data_queries':len(dmap),'invalid_info_queries':len(imap),'valid_data_info_queries':len(all_queries)*2,'real_transactions':len(calls),'D0':21,'D1':20,'D5':21,'all_retries_zero':True,'query_added_transactions':0,'D0_did_not_promote_status_info':True,'D5_did_not_update_data_status':True,'csv_bytes':len(data),'csv_rows':len(rows),'ate_events_matched':len(actual),'nf_transaction_records':len(transactions),'device_sha_matches':True,'old_log_unchanged':True,'drop':0,'queue':0,'host_monitor_bytes':len(host_raw),'max_exchange_ms':max(r['elapsed_ms'] for r in records),'tomorrow':'2026-11-23: user requested fixes, plus QR installation and tests; CDC .22.3 not deployed today','final_state':'parent stopped; CDC fault and PIO stop preserved; DATA/STATUS/INFO valid from actual refreshes'}
except Exception as exc:
 failure=repr(exc);result={'status':'INCOMPLETE','failure':failure,'completed_mixed_cycles':cycles,'exchanges':len(records)}
 if proc is not None:
  if proc.poll() is None:
   try:proc.wait(timeout=47)
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
