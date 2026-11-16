"""SH-U05Aを識別して起動UARTを受信専用で保存する。無受信180秒、受信後15秒無通信で終了。"""
import json
import time
from pathlib import Path
import serial
from serial.tools import list_ports

out = Path(__file__).resolve().parent
ports = [p for p in list_ports.comports() if p.vid == 0x1A86 and p.pid == 0x5523]
if len(ports) != 1:
    raise SystemExit('SH-U05A candidate count must be exactly one')
p = ports[0]
meta = {'port': p.device, 'vid': p.vid, 'pid': p.pid, 'location': p.location,
        'baud': 115200, 'format': '8N1', 'flow_control': False, 'tx_bytes': 0}
(out / 'adapter.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
received = 0
with (out / 'boot_uart.raw').open('xb') as raw:
    with serial.Serial(port=None, baudrate=115200, timeout=0.1,
                       xonxoff=False, rtscts=False, dsrdtr=False) as uart:
        uart.port = p.device
        uart.dtr = False
        uart.rts = False
        uart.open()
        print('READY: ' + p.device + ' 115200 8N1 RECEIVE ONLY', flush=True)
        started = time.monotonic()
        last_data = None
        while time.monotonic() - started < 180:
            chunk = uart.read(4096)
            if chunk:
                raw.write(chunk)
                raw.flush()
                received += len(chunk)
                last_data = time.monotonic()
                print('RX total=' + str(received), flush=True)
            if last_data is not None and time.monotonic() - last_data >= 15:
                break
meta.update(rx_bytes=received, elapsed_seconds=round(time.monotonic()-started, 3), port_closed=True)
(out / 'capture_result.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
print('CLOSED: bytes=' + str(received), flush=True)

