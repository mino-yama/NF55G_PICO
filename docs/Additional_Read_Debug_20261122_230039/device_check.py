import machine,binascii,json,time,hashlib
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
