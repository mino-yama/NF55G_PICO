"""親単体でPIO RXを同じTX端子へ割当て、実ドライバの送受信を照合する。外部接続なし専用。"""
from pathlib import Path
import json
from mpremote.transport_serial import SerialTransport
BASE=Path(__file__).resolve().parent
PREFIX=chr(92)*2+'?'+chr(92)
OUT=BASE if str(BASE).startswith(PREFIX) else Path(PREFIX+str(BASE))
if (OUT/'PIO_Internal_Result.json').exists():
    raise RuntimeError('Preserve previous diagnostic')
t=SerialTransport('COM6',wait=2)
result={'external_connections':'user reported isolated','firmware_files_written':False,'instrument_queries_sent':False}
try:
    t.enter_raw_repl(soft_reset=False)
    uid=t.eval("__import__('binascii').hexlify(__import__('machine').unique_id()).decode()")
    if uid!='69f7d45962cfdfad':
        raise RuntimeError('Wrong parent')
    result['unique_id']=uid
    t.enter_raw_repl(soft_reset=True)
    code="""
import time,rp2
from machine import Pin
from src.external_instrument_pio import ExternalPioUART,_receive
from src.external_instrument_contract import encode_frame
p=ExternalPioUART()
try:
 p.rx.active(0)
 p.rx.init(_receive,freq=115200*8,in_base=Pin(12),jmp_pin=Pin(12))
 p.rx.irq(p._irq,hard=True)
 p.rx.active(1)
 raw=encode_frame(b'12345678'+bytes(8),0,'H',0,0,b'')
 offset=0
 received=b''
 start=time.ticks_ms()
 while time.ticks_diff(time.ticks_ms(),start)<1000:
  if offset<len(raw):
   offset+=p.write(raw[offset:])
  if p.any():
   received+=p.read(64)
  if len(received)>=len(raw):
   break
  time.sleep_ms(1)
 print('TX_HEX='+raw.hex())
 print('RX_HEX='+received.hex())
 print('TX_ACCEPTED='+str(offset))
 print('UART_ERROR='+repr(p.take_error()))
 print('PIO_INTERNAL_MATCH='+str(raw==received))
finally:
 p.close()
"""
    stdout,stderr=t.exec_raw(code,timeout=5)
    (OUT/'PIO_Internal.log').write_bytes(stdout+b'\nSTDERR\n'+stderr)
    result.update(stdout=stdout.decode(),stderr=stderr.decode(),match=b'PIO_INTERNAL_MATCH=True' in stdout and not stderr)
    print(stdout.decode(),flush=True)
    if stderr:
        print(stderr.decode(),flush=True)
finally:
    t.enter_raw_repl(soft_reset=True)
    result['final_state']='raw soft reset; friendly REPL stopped'
    (OUT/'PIO_Internal_Result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    t.exit_raw_repl()
    t.close()
