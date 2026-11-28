
import sys,time,json
a=sys.modules['src.main'].active_app
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
assert not a.server.pending and not a.server.tx and not a.ate_uart.any()
t=a.external_link.transport
assert t.tx.active() and not t._closed
_scope_pattern_state={'running':True,'pin':12,'baud':115200,'pattern_hex':'55','duration_ms':600000,'bytes':0}
pattern=b'\x55\x55\x55\x55'
started=time.ticks_ms();last=started;sent=0
print('SCOPE_READY')
try:
    while time.ticks_diff(time.ticks_ms(),started)<600000:
        sent+=t.write(pattern)
        now=time.ticks_ms()
        if time.ticks_diff(now,last)>=1000:
            _scope_pattern_state['bytes']=sent
            a.qr_write.poll()
            last=now
finally:
    time.sleep_ms(2)
    _scope_pattern_state.update(running=False,bytes=sent,elapsed_ms=time.ticks_diff(time.ticks_ms(),started))
    print('SCOPE_STOPPED|'+json.dumps(_scope_pattern_state))
    a.run()
