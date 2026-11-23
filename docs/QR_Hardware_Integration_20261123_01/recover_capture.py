"""受信済みRAMを低速で再回収する。QRの再採取や機器送信は行わない。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from capture_and_inspect import inspect, ROOT

out = Path(sys.argv[1])
original = (out / 'parent.log').read_text(encoding='utf-8')
meta = json.loads(next(x.split('|', 1)[1] for x in original.splitlines()
                       if x.startswith('QR_CAPTURE_META|')))
code = "import time,binascii\nfor i in range(0,len(qr_raw),64):\n print('RECOVER_HEX|'+binascii.hexlify(qr_raw[i:i+64]).decode())\n time.sleep_ms(20)\nprint('RECOVER_DONE')"
p = subprocess.run([str(ROOT / '.venv/Scripts/python.exe'), '-u', '-m',
    'mpremote', 'connect', 'COM6', 'resume', 'exec', code],
    cwd=ROOT, capture_output=True, timeout=35)
(out / 'recovery.log').write_bytes(p.stdout + p.stderr)
assert p.returncode == 0 and b'RECOVER_DONE' in p.stdout, p.stderr
raw = b''.join(bytes.fromhex(x.split('|', 1)[1])
    for x in p.stdout.decode().splitlines() if x.startswith('RECOVER_HEX|'))
assert len(raw) == meta['bytes']
assert hashlib.sha256(raw).hexdigest() == meta['sha256']
(out / 'qr_host.raw').write_bytes(raw)
result = inspect(raw, nf55g_profile=True)
result.update(capture=meta, recovery='same RAM capture, paced USB output; length and SHA256 verified')
if meta['fault']:
    result['status'] = 'CAPTURE_ERRORS'
(out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k not in ('records', 'health')}, ensure_ascii=False, indent=2))
print('health_last', result['health'][-1:] if result['health'] else [])
