"""Read completed endurance CSVs from the parent SD and correlate them to ATE."""
import base64
import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

from prepare_parent_idle_fix import BASE, CASE, ROOT


def main(out, previous_wire=None):
    result = json.loads((out / 'result.json').read_text(encoding='utf8'))
    meter_commands = (('EXT_QUERY 10000 MD?', 'EXT_QUERY 2500 ERR?')
                      if result.get('meter_language') == 'adc' else
                      ('EXT_QUERY 10000 :READ?', 'EXT_QUERY 2000 :SYST:ERR?'))
    count = result['completed_trials']
    failed = result['status'] == 'STOPPED' and result.get('stopped_trial') == count + 1
    if failed:
        if not (out / 'failed_trial_close.json').exists():
            raise RuntimeError('Failed trial closure has not been recorded')
        closed = json.loads((out / 'failed_trial_close.json').read_text(encoding='utf8'))
        if closed['events'][-1].get('reply') != 'OK' or closed['events'][-1]['command'] != 'TEST_END':
            raise RuntimeError('Failed trial closure was not confirmed')
        count += 1
    elif result['status'] != 'TRIALS_COMPLETE_CSV_PENDING' or count != result['planned_trials']:
        raise RuntimeError('Endurance status does not allow export')
    first_time = (dt.datetime.fromisoformat(result['started']) - dt.timedelta(minutes=2)).strftime('%Y%m%d_%H%M%S')
    last_time = (dt.datetime.fromisoformat(result['ended']) + dt.timedelta(minutes=2)).strftime('%Y%m%d_%H%M%S')
    expected_session = result['session'][:16]
    prefix = b''
    prefix_range = None
    start_at = 0
    if previous_wire is not None:
        raw = previous_wire.read_bytes()
        last_hash = raw.rfind(b'\nHASH|')
        end = raw.find(b'\n', last_hash + 1) if last_hash >= 0 else -1
        if end < 0:
            raise RuntimeError('Previous capture has no complete hash line')
        prefix = raw[:end + 1]
        prefix_range, = (json.loads(line[6:]) for line in prefix.splitlines() if line.startswith(b'RANGE|'))
        captured = [json.loads(line[5:])['trial'] for line in prefix.splitlines() if line.startswith(b'FILE|')]
        if captured != list(range(prefix_range[0], prefix_range[0] + len(captured))):
            raise RuntimeError('Previous capture does not cover a contiguous trial prefix')
        start_at = captured[-1] + 1
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    export = out / f'csv_export_{now:%Y%m%d_%H%M%S_%f}'
    export.mkdir()
    script = f'count={count}\nfirst_time={first_time!r}\nlast_time={last_time!r}\nexpected_session={expected_session!r}\nstart_at={start_at}\nprefix_range={prefix_range!r}\n' + '''
import binascii, hashlib, json, machine, os, sys, time
assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
assert binascii.hexlify(app.external_link.parent_nonce).decode() == expected_session
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
last = int(app.logger.last_test_id[1:])
first = last - count + 1
assert first > 0
assert prefix_range is None or prefix_range == [first, last]
print('RANGE|' + json.dumps([first,last]))
for bank in ('BANK_A', 'BANK_B'):
    folder = app.logger.sd_sink.root + '/' + bank
    for entry in os.ilistdir(folder):
        name = entry[0]
        if not name.endswith('.csv'):
            continue
        fields = name[:-4].split('_')
        if len(fields) != 3 or not fields[2].startswith('T') or not fields[2][1:].isdigit():
            continue
        number = int(fields[2][1:])
        stamp = fields[0] + '_' + fields[1]
        if not (max(first, start_at) <= number <= last and first_time <= stamp <= last_time):
            continue
        path = folder + '/' + name
        print('FILE|' + json.dumps({'path':path,'trial':number,'bytes':os.stat(path)[6]}))
        sha = hashlib.sha256()
        with open(path, 'rb') as f:
            while True:
                b = f.read(128)
                if not b:
                    break
                sha.update(b)
                print('DATA|' + binascii.b2a_base64(b).decode().strip())
                time.sleep_ms(15)
        print('HASH|' + binascii.hexlify(sha.digest()).decode())
print('EXPORT_END')
'''
    payload = export / 'export_parent.py'
    with payload.open('x', encoding='utf8') as f:
        f.write(script)
    wire_path = export / 'csv_usb_raw.log'
    with wire_path.open('xb') as wire, (export / 'csv_usb_stderr.log').open('xb') as err:
        wire.write(prefix)
        wire.flush()
        proc = subprocess.run(BASE + ['run', str(payload)], cwd=ROOT, stdout=wire, stderr=err, timeout=300)

    ate = {}
    for line in (out / 'ate.jsonl').read_text(encoding='utf8').splitlines():
        item = json.loads(line)
        if item['trial'] and item['command'] in meter_commands:
            ate[(item['trial'], item['command'])] = item['reply']
    dest = export / 'csv'
    dest.mkdir()
    files = {}
    first, last = None, None
    item, buf = None, None
    complete = False
    for line in wire_path.read_text(encoding='utf8').splitlines():
        if line.startswith('RANGE|'):
            first, last = json.loads(line[6:])
        elif line.startswith('FILE|'):
            if item is not None:
                raise RuntimeError('Previous CSV incomplete')
            item, buf = json.loads(line[5:]), bytearray()
        elif line.startswith('DATA|'):
            buf.extend(base64.b64decode(line[5:], validate=True))
        elif line.startswith('HASH|'):
            sha = hashlib.sha256(buf).hexdigest()
            if sha != line[5:] or len(buf) != item['bytes']:
                raise RuntimeError(f'SD file hash/length mismatch: {item}')
            number = item['trial']
            name = Path(item['path']).name
            if number in files or not name.endswith(f'_T{number:06d}.csv'):
                raise RuntimeError(f'Duplicate or invalid trial file: {item}')
            rows = list(csv.reader(io.StringIO(buf.decode('utf8'))))
            if len(rows) < 2 or any(len(row) != 14 for row in rows):
                raise RuntimeError(f'Invalid CSV shape: {name}')
            records = [dict(zip(rows[0], row)) for row in rows[1:]]
            trial_id = f'T{number:06d}'
            if not any(r['event'] == 'TRIAL_START' and r['detail'] == f'trial_id={trial_id}' for r in records):
                raise RuntimeError(f'Missing trial start record: {name}')
            if not any(r['event'] == 'TRIAL_END_REQUEST' and
                       r['detail'] == f'trial_id={trial_id};reason=TEST_END' for r in records):
                raise RuntimeError(f'Missing trial end record: {name}')
            for command in meter_commands:
                replies = [r['result'] for r in records if r['category'] == 'ATE' and
                           r['event'] == 'RESULT' and r['detail'] == command]
                expected_reply = ate.get((number - first + 1, command))
                if replies != ([] if expected_reply is None else [expected_reply]):
                    raise RuntimeError(f'ATE/CSV response mismatch: {name}, {command}')
            with (dest / name).open('xb') as f:
                f.write(buf)
            files[number] = {**item, 'filename': name, 'sha256': sha, 'data_rows': len(records), 'columns': 14}
            item = buf = None
        elif line == 'EXPORT_END':
            complete = True
    manifest = {'csv_count': len(files), 'planned': count, 'files': list(files.values()),
                'complete': proc.returncode == 0 and complete and item is None and first is not None
                and set(files) == set(range(first, last + 1)) and len(files) == count}
    (export / 'csv_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    if not manifest['complete']:
        raise RuntimeError(f'CSV export incomplete: {len(files)}/{count}; see {wire_path}')
    print(f'CSV_VERIFIED {len(files)}/{count}: {dest}')


if __name__ == '__main__':
    target = (CASE / sys.argv[1]).resolve()
    assert target.parent == CASE.resolve() and target.name.startswith('endurance_')
    previous = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    if previous is not None:
        assert previous.parent.parent == target and previous.name == 'csv_usb_raw.log'
    main(target, previous)
