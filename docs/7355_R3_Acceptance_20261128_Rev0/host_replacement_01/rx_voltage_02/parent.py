HOLD_MS=30000

import sys,time,json,machine
a=sys.modules['src.main'].active_app;e=a.external_link;t=e.transport
assert e.expected_chipid=='73AD3A60D10514E9'
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
assert not a.server.pending and not a.server.tx and not a.ate_uart.any()
assert t.tx.tx_fifo()==0
ctrl=machine.mem32[0x40028064];pad=machine.mem32[0x40038034];active=t.tx.active()
rows=[]
try:
    t.tx.active(0)
    p=machine.Pin(12,machine.Pin.OUT,value=1)
    for value,label in ((0,'LOW'),(1,'HIGH')):
        p.value(value);time.sleep_ms(20)
        observed=p.value();rows.append({'ms':time.ticks_ms(),'set':value,'read':observed})
        assert observed==value,'output readback differs; abort hold'
        print('\nRX_LEVEL|'+label)
        time.sleep_ms(HOLD_MS)
finally:
    machine.Pin(12).value(1)
    machine.mem32[0x40028064]=ctrl;machine.mem32[0x40038034]=pad;t.tx.active(active)
    print('\nRX_LEVEL_RESULT|'+json.dumps({'rows':rows,'ctrl':machine.mem32[0x40028064],'active':t.tx.active()}))
