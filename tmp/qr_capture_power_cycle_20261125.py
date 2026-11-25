import binascii
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import struct
import subprocess
import sys


now = datetime.now(timezone(timedelta(hours=9)))
folder = Path('docs/QR_Hardware_Integration_20261123_01/Production_Label_Retest_20261125')
destination = folder / f'QR_Power_Cycle_{now:%H%M%S_%f}'
destination.mkdir()
source = Path('tmp/qr_health_snapshot_20261125.py').read_text(encoding='utf8')
program = Path('tmp/qr_health_power_cycle_target.py')
seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 65
assert 2 <= seconds <= 65
program.write_text(source.replace('duration_ms = 2500', f'duration_ms = {seconds * 1000}'), encoding='utf8')
base = [sys.executable, '-u', '-m', 'mpremote', 'connect', 'COM6', 'resume']
lines = []
try:
    with (destination / 'parent_uart.log').open('x', encoding='utf8') as log, \
            subprocess.Popen(base + ['run', str(program)], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding='utf8', errors='replace') as task:
        for line in task.stdout:
            log.write(line)
            log.flush()
            lines.append(line.strip())
            if line.strip() == 'QR_UART_CAPTURE_READY':
                print(line.strip(), flush=True)
        if task.wait() or 'QR_UART_CAPTURE_END' not in lines:
            raise RuntimeError('capture did not finish, see ' + str(destination))
finally:
    subprocess.run(base + ['exec', '--no-follow',
                           "import sys; sys.modules['src.main'].active_app.run()"],
                   timeout=20, check=True)
raw = b''.join(binascii.unhexlify(line.split('|')[1]) for line in lines if line.startswith('QR_UART_DATA|'))
(destination / 'qr_uart.bin').write_bytes(raw)
events = []
for line in raw.splitlines():
    line = line.lstrip(b'\x00')
    if not line.startswith(b'@') or len(line) != 153:
        continue
    seq, uptime, kind, addr, instance, size, payload = struct.unpack(
        '<IIBBBB64s', binascii.unhexlify(line[1:]))
    item = {'sequence': seq, 'uptime_ms': uptime, 'kind': kind, 'payload_hex': payload[:size].hex()}
    if kind in (1, 11, 12):
        item['text'] = payload[:size].decode('ascii')
    if kind == 14 and size == 24:
        item['qr_enabled'] = bool(struct.unpack('<6I', payload[:24])[-1] & 1)
    events.append(item)
(destination / 'events.json').write_text(json.dumps(events, indent=2), encoding='utf8')
print(f'{destination}: {len(events)} events, boot={[(x["sequence"], x["text"]) for x in events if x["kind"] == 1]}, '
      f'last_health={[x for x in events if "qr_enabled" in x][-1:]}', flush=True)
