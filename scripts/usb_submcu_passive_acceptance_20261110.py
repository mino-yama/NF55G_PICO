"""Passive USB serial capture: no transmitted bytes, no REPL interrupt or reset."""
import json
import time
from pathlib import Path
import serial

out = Path(__file__).resolve().parents[1] / 'docs' / 'USB_Host_SubMCU_COM6_Passive_20261110.json'
port = serial.Serial()
port.port = 'COM6'
port.baudrate = 115200
port.timeout = 0.2
port.dtr = False
port.rts = False
result = {'port': 'COM6', 'mode': 'passive_no_tx', 'baudrate': 115200, 'baudrate_note': 'USB CDC capture setting, not an accepted inter-MCU UART baud', 'dtr': False, 'rts': False, 'duration_s': 4, 'tx_hex': ''}
try:
    port.open()
    started = time.monotonic()
    chunks = []
    while time.monotonic() - started < 4:
        data = port.read(4096)
        if data:
            chunks.append({'elapsed_s': round(time.monotonic()-started, 3), 'hex': data.hex(), 'text': data.decode('utf-8', errors='replace')})
    result['chunks'] = chunks
    result['rx_bytes'] = sum(len(bytes.fromhex(c['hex'])) for c in chunks)
    result['status'] = 'captured'
except Exception as exc:
    result['status'] = 'error'
    result['error'] = str(exc)
finally:
    port.close()
if out.exists():
    raise SystemExit('Refusing to overwrite existing evidence: ' + str(out))
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=True, indent=2))
