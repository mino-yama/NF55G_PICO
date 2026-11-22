import machine,binascii,json,time,hashlib
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
