"""停止済み連続ログをSHA照合して退避し、同じ親RAM runtimeを再開する。"""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import serial

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / sys.argv[1] / 'File_Export'
OUT.mkdir(exist_ok=False)
BASE = [sys.executable, '-m', 'mpremote', 'connect', 'COM6', 'resume']
operations = []
def run(args):
    p = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True, timeout=90)
    text = p.stdout.decode('utf-8', 'replace')
    operations.append({'args': [str(a) for a in args], 'code': p.returncode,
                       'stdout': text, 'stderr': p.stderr.decode('utf-8', 'replace')})
    (OUT / 'operations.json').write_text(json.dumps(operations, indent=2), encoding='utf-8')
    if p.returncode:
        raise RuntimeError('export operation failed; no retry')
    return text
try:
    code = """import json,hashlib,binascii
assert not app._comm_busy()
assert not app.logger.active
p=app.logger.sd_sink.open_filename
h=hashlib.sha256()
f=open(p,'rb')
size=0
while True:
 b=f.read(1024)
 if not b: break
 h.update(b)
 size+=len(b)
f.close()
print('LOG_SNAP|'+json.dumps({'filename':p,'bytes':size,'sha256':binascii.hexlify(h.digest()).decode(),'drop':app.logger.drop_count,'queue':len(app.logger.queue),'active':app.logger.active,'nf_state':app.protocol.state,'link_fault':app.external_link.fault,'frame_errors':app.external_link.reader.errors}))
"""
    text = run(BASE + ['exec', code])
    snap = json.loads(next(s.split('LOG_SNAP|', 1)[1] for s in text.splitlines() if s.startswith('LOG_SNAP|')))
    (OUT / 'device_snapshot.json').write_text(json.dumps(snap, indent=2), encoding='utf-8')
    if not re.fullmatch(r'/sd/BANK_[AB]/[0-9_]+\.csv', snap['filename']):
        raise RuntimeError('unexpected log filename')
    destination = OUT / Path(snap['filename']).name
    run(BASE + ['fs', 'cp', ':' + snap['filename'], destination])
    raw = destination.read_bytes()
    if len(raw) != snap['bytes'] or hashlib.sha256(raw).hexdigest() != snap['sha256']:
        raise RuntimeError('export hash differs')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    result = {'device_sha_matches': True, 'bytes': len(raw), 'rows': len(rows),
              'malformed_rows': sum(None in row for row in rows),
              'd1_transactions': sum(row['category'] == 'NF55' and row['event'] == 'TRANSACTION' and row['cmd'] == 'D1' for row in rows),
              'nf_raw_records': sum(row['category'] == 'NF55' and row['event'] == 'RAW' for row in rows),
              'drop': snap['drop'], 'queue': snap['queue'], 'link_fault': snap['link_fault']}
    (OUT / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
finally:
    # soft resetせず、退避前と同じapp/接続nonceで再開する。
    with serial.Serial('COM6', 115200, timeout=.1) as port:
        port.dtr = False
        port.rts = False
        port.write(b'\x01')
        time.sleep(.1)
        data = port.read(port.in_waiting or 1)
        port.write(b'app.run()\x04')
        time.sleep(.3)
        data += port.read(port.in_waiting or 1)
    (OUT / 'resume_runtime.raw').write_bytes(data)
    print('RESUME=' + repr(data), flush=True)
