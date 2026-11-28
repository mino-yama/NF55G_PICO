
import sys,time,json,binascii
a=sys.modules['src.main'].active_app
assert not a.logger.active and not a.logger.test_running and not a._comm_busy()
link=a.external_link;original=link.transport
class Trace:
    def __init__(self):self.events=[]
    def any(self):return original.any()
    def take_error(self):return original.take_error()
    def read(self,n):
        v=original.read(n)
        if v:self.events.append([time.ticks_ms(),'RX',binascii.hexlify(v).decode()])
        return v
    def write(self,v):
        n=original.write(v)
        if n:self.events.append([time.ticks_ms(),'TX',binascii.hexlify(v[:n]).decode()])
        return n
t=Trace();link.transport=t
try:
    print('\nDIAG2_READY')
    start=time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(),start)<15000:
        a.service_once();time.sleep_ms(1)
finally:
    link.transport=original
    print('\nDIAG2_TRACE|'+json.dumps(t.events))
