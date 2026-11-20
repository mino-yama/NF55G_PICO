"""新コードを親MicroPythonのRAMのみで確認。GPIO/UARTインスタンスを生成しない。"""
import json
from pathlib import Path
from mpremote.transport_serial import SerialTransport

OUT = Path(__file__).resolve().parent
ROOT = next(path for path in OUT.parents if (path/'AGENTS.md').is_file())


def main():
    contract = (ROOT/'src/external_instrument_contract.py').read_text(encoding='utf8')
    core = (ROOT/'src/external_instrument_relay.py').read_text(encoding='utf8')
    link = (ROOT/'src/external_instrument_link.py').read_text(encoding='utf8')
    pio = (ROOT/'src/external_instrument_pio.py').read_text(encoding='utf8')
    link = link[link.index('class FrameReader:'):]
    tests = '''
request=parse_monitor_request(b'EXT_QUERY 2000 *IDN?')
assert request['command']==b'*IDN?'
assert parse_monitor_request(b'EXT_SEND 2000 :x  ')['command']==b':x  '
for ending in (b'',b'\\r',b'\\n',b'\\r\\n'):
 assert parse_monitor_request(b'EXT_QUERY 2000 *IDN?'+ending)['timeout_ms']==2000
wire=encode_frame(b'PARENT01HOSTNONC',1,'Q',1,2000,b'*IDN?')
assert decode_frame(wire)['payload']==b'*IDN?'
class Clock:
 def ticks_ms(self): return 0
class Port:
 def __init__(self): self.rx=b''; self.tx=b''
 def write(self,data): self.tx+=data; return len(data)
 def any(self): return len(self.rx)
 def read(self,n):
  raw=self.rx[:n]; self.rx=self.rx[n:]; return raw
port=Port()
link=ExternalInstrumentLink(port,Clock(),b'PARENT01','BFCF2EDB84B0B37F')
link.start(request)
for i in range(20): link.poll()
assert decode_frame(port.tx)['kind']=='H'
port.tx=b''
port.rx=encode_frame(b'PARENT01HOSTNONC',0,'h',0,0,b'BFCF2EDB84B0B37F|meter-host-relay-20261120.1|READY')
for i in range(20): link.poll()
assert decode_frame(port.tx)['payload']==b'*IDN?'
port.rx=encode_frame(b'PARENT01HOSTNONC',1,'T',1,2000,b'')+encode_frame(b'PARENT01HOSTNONC',1,'R',1,2000,b'1\\r\\n')
for i in range(20): link.poll()
assert link.take_reply()=='OK:EXT_RX:3:310D0A'
print('RAM_PARSER_CODEC_LINK_OK')
'''
    command = "import machine,binascii; assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'; _relay_ram={'__name__':'relay_ram_check'}; "
    command += 'exec('+repr(contract)+',_relay_ram);exec('+repr(core)+',_relay_ram);exec('+repr(link)+',_relay_ram);exec('+repr(tests)+',_relay_ram);exec('+repr(pio)+',_relay_ram);'
    command += "print('PIO_ASSEMBLED_TX='+str(len(_relay_ram['_transmit'][0]))); print('PIO_ASSEMBLED_RX='+str(len(_relay_ram['_receive'][0]))); import rp2; print('PIO4_ACTIVE='+str(rp2.StateMachine(4).active())); print('PIO5_ACTIVE='+str(rp2.StateMachine(5).active()))"
    transport = SerialTransport('COM6',wait=2)
    result = {'device_files_written':False,'gpio_uart_started':False}
    try:
        transport.enter_raw_repl(soft_reset=False)
        stdout,stderr=transport.exec_raw(command,timeout=30)
        (OUT/'RAM_Validation.log').write_bytes(stdout+b'\nSTDERR\n'+stderr)
        result['stdout']=stdout.decode()
        result['stderr']=stderr.decode()
        result['passed']=not stderr
        (OUT/'RAM_Validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(stdout.decode())
        if stderr:
            raise RuntimeError(stderr.decode())
    finally:
        transport.exit_raw_repl()
        transport.close()


if __name__=='__main__':
    main()
