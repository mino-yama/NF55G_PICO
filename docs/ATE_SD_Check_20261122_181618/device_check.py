import machine,binascii,json,time,hashlib
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
