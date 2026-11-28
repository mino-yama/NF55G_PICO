
import sys,time,json,machine
a=sys.modules['src.main'].active_app
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
t=a.external_link.transport
assert t.tx.active() and t.tx.tx_fifo()==0
saved=machine.mem32[0x40028064]
assert saved&31==7
values=[]
try:
    t.tx.active(0)
    pin=machine.Pin(12,machine.Pin.OUT,value=1)
    print('\nPULSE_READY')
    time.sleep_ms(1000)
    for value in (0,1,0,1):
        pin.value(value)
        values.append({'ms':time.ticks_ms(),'set':value,'read':pin.value()})
        time.sleep_ms(300)
finally:
    machine.Pin(12).value(1)
    machine.mem32[0x40028064]=saved
    t.tx.active(1)
    print('\nPULSE_RESULT|'+json.dumps({'values':values,'restored_ctrl':machine.mem32[0x40028064],'tx_active':t.tx.active()}))
