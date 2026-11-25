"""Back up the connected parent source and finished trial CSVs before validation."""
import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys


BASE = [sys.executable, '-m', 'mpremote', 'connect', 'COM6', 'resume']
CASE = Path(__file__).resolve().parent
ROOT = CASE.parents[2]
UID = '69f7d45962cfdfad'


def main():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    out = CASE / f'parent_idle_fix_{now:%Y%m%d_%H%M%S_%f}'
    out.mkdir()

    def run(*args):
        p = subprocess.run(BASE + list(args), cwd=ROOT, capture_output=True, timeout=40)
        with (out / 'operations.jsonl').open('a', encoding='utf8') as log:
            log.write(json.dumps({'args': args, 'code': p.returncode,
                                  'stdout': p.stdout.decode('utf8', 'replace'),
                                  'stderr': p.stderr.decode('utf8', 'replace')}) + '\n')
        p.check_returncode()
        return p.stdout.decode('utf8')

    code = '''import os, hashlib, binascii, machine, json, sys
uid = binascii.hexlify(machine.unique_id()).decode()
assert uid == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
def evidence(path):
    with open(path, 'rb') as f:
        digest = hashlib.sha256()
        while True:
            block = f.read(512)
            if not block: break
            digest.update(block)
    return {'path':path, 'bytes':os.stat(path)[6], 'sha256':binascii.hexlify(digest.digest()).decode()}
sink = app.logger.sd_sink
paths = []
for bank in ('BANK_A', 'BANK_B'):
    folder = sink.root + '/' + bank
    paths.extend(folder + '/' + name for name in os.listdir(folder))
trials = app.logger.test_history[-2:]
assert trials
files = []
for item in trials:
    matches = [p for p in paths if p.endswith('/' + item['filename'])]
    assert len(matches) == 1
    files.append(evidence(matches[0]))
print('BACKUP|' + json.dumps({'uid':uid,'trials':trials,'files':[evidence('/src/main.py')] + files}))
'''
    line = next(line for line in run('exec', code).splitlines() if line.startswith('BACKUP|'))
    info = json.loads(line.split('|', 1)[1])
    for item in info['files']:
        file = out / Path(item['path']).name
        run('fs', 'cp', ':' + item['path'], str(file))
        raw = file.read_bytes()
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        if file.suffix == '.csv':
            rows = list(csv.reader(io.StringIO(raw.decode('utf8'))))
            assert len(rows) > 1 and all(len(row) == 14 for row in rows)
            item['data_rows'] = len(rows) - 1
    baseline = subprocess.check_output(['git', 'show', 'HEAD:src/main.py'], cwd=ROOT)
    normalize = lambda b: b.replace(b'\r\n', b'\n')
    info['parent_matches_git_baseline'] = normalize((out / 'main.py').read_bytes()) == normalize(baseline)
    (out / 'manifest.json').write_text(json.dumps(info, indent=2), encoding='utf8')
    print(out)
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
