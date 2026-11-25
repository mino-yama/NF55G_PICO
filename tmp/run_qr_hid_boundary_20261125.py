from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys


now = datetime.now(timezone(timedelta(hours=9)))
folder = Path('docs/QR_Hardware_Integration_20261123_01/Production_Label_Retest_20261125')
log = folder / f'QR_HID_Boundary_{now:%H%M%S_%f}.log'
base = [sys.executable, '-u', '-m', 'mpremote', 'connect', 'COM6', 'resume']
print(log, flush=True)
try:
    with log.open('x', encoding='utf8') as out, subprocess.Popen(
            base + ['run', 'tmp/qr_hid_boundary_parent.py'], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf8', errors='replace') as process:
        for line in process.stdout:
            out.write(line)
            out.flush()
            print(line.rstrip(), flush=True)
        if process.wait():
            raise RuntimeError('QR diagnostic stopped')
finally:
    subprocess.run(base + ['exec', '--no-follow', "import sys; sys.modules['src.main'].active_app.run()"],
                   check=True, timeout=15)
