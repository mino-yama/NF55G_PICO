sdroot='/sd/qr_prod_20261128_normal_03'

import sys,time,json,binascii,struct,gc,os
from src.main import FixtureApp
from src.logger import Logger
from src.sd_sink import FileSDSink
original=sys.modules['src.main'].active_app
assert not original.logger.active and not original.logger.test_running and not original._comm_busy()
assert original.qr_write.arm_host and original.ate_uart.any()==0
assert not original.qr_write.active
class TracePort:
    def __init__(self,port):self.port=port;self.line=bytearray();self.events=[];self.drops=0
    def any(self):return self.port.any()
    def write(self,data):return self.port.write(data)
    def take_error(self):return self.port.take_error()
    def read(self,count):
        data=self.port.read(count)
        for b in data:
            if b==10:
                line=bytes(self.line);self.line=bytearray()
                if len(line)!=153 or line[:1]!=b'@':continue
                seq,ms,kind,addr,instance,size,payload=struct.unpack('<IIBBBB64s',binascii.unhexlify(line[1:]))
                event={'seq':seq,'ms':ms,'kind':kind}
                if kind==14 and size==24:event['health']=list(struct.unpack('<6I',payload[:24]))
                elif kind==16 and size==25:event.update(id=payload[:24].decode(),discard=payload[24])
                elif kind==17 and size==59:event.update(id=payload[:24].decode(),text=payload[24:59].decode())
                else:continue
                if len(self.events)<64:self.events.append(event)
                else:self.drops+=1
            elif len(self.line)<155:self.line.append(b)
            else:self.line=bytearray()
        return data
port=TracePort(original.qr_write.transport)
os.mkdir(sdroot)
sink=FileSDSink(sdroot);sink.mount()
candidate=FixtureApp(ate_uart=original.ate_uart,clock=original.clock,rtc=original.rtc,
    logger=Logger(sink,clock=original.clock,rtc=original.rtc),qr_transport=port,qr_host_arm=True)
assert candidate.protocol is None and candidate.nf55_uart is None
print('QR_TEST_READY')
started=time.ticks_ms()
try:
    while time.ticks_diff(time.ticks_ms(),started)<1200000:
        candidate.service_once()
        while port.events:print('QR_TRACE|'+json.dumps(port.events.pop(0)))
        time.sleep_ms(1)
finally:
    if candidate.logger.active or candidate.logger.test_running:candidate.execute_ate_line('TEST_END')
    original.qr_write.line=bytearray();original.qr_write.last_seq=None
    print('QR_TEST_STOP|'+json.dumps({'drop':candidate.logger.drop_count,'trace_drop':port.drops}))
