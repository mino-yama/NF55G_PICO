"""QR統合前の親状態と既設PIOからの受動通知を確認。製品へ送信しない。"""
import json
from pathlib import Path
import struct
import binascii
import sys
from datetime import datetime,timezone
from mpremote.transport_serial import SerialTransport

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/QR_Production_Integration_20261128_Rev0'
OUT.mkdir(exist_ok=True)
tag={'--armed':'_armed','--after-rst':'_after_rst'}.get(sys.argv[1] if len(sys.argv)>1 else '', '')
transport=SerialTransport('COM6',timeout=2)
try:
    transport.enter_raw_repl(soft_reset=False)
    code='''import sys,machine,binascii,json,time
app=sys.modules['src.main'].active_app
assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
assert not app.qr_write.active
print('STATE|'+json.dumps({'sd':app.logger.sd_status,'arm_host':app.qr_write.arm_host,'last_seq':app.qr_write.last_seq,'ignored':app.qr_write.ignored,'transport':str(type(app.qr_write.transport))}))
port=app.qr_write.transport
raw=bytearray();started=time.ticks_ms()
while time.ticks_diff(time.ticks_ms(),started)<3000:
    if port.any():raw.extend(port.read(min(port.any(),512)))
    time.sleep_ms(1)
print('RAW|'+binascii.hexlify(raw).decode())
'''
    output,error=transport.exec_raw(code,timeout=15)
    (OUT/('parent_precheck'+tag+'.log')).write_bytes(output+error)
    if error:raise RuntimeError(error.decode())
    text=output.decode()
    state=json.loads(next(l[6:] for l in text.splitlines() if l.startswith('STATE|')))
    raw=binascii.unhexlify(next(l[4:] for l in text.splitlines() if l.startswith('RAW|')))
    (OUT/('parent_qr_passive'+tag+'.raw')).write_bytes(raw)
    records=[]
    for line in raw.splitlines():
        if len(line)==153 and line[:1]==b'@':
            data=struct.unpack('<IIBBBB64s',binascii.unhexlify(line[1:]))
            records.append({'seq':data[0],'ms':data[1],'kind':data[2],'size':data[5],'payload':data[6][:data[5]].hex()})
    result={'time':datetime.now(timezone.utc).isoformat(),'state':state,'bytes':len(raw),'records':records}
    (OUT/('precheck'+tag+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
finally:
    try:transport.exec_raw_no_follow('app.run()')
    finally:transport.close()
