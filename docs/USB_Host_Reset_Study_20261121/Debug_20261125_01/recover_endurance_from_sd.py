"""Copy and verify trial CSVs from the card without writing to it."""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import re


CASE = Path(__file__).resolve().parent
RUN = CASE / 'endurance_20261125_095202_514101'
ANCHOR = CASE / 'parent_idle_fix_20261125_094745_260223' / '20261125_093855_T000243.csv'
FIRST = 245
LAST = 547
QUERIES = ('EXT_QUERY 10000 :READ?', 'EXT_QUERY 2000 :SYST:ERR?')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main(card, run=RUN, anchor=ANCHOR, first=FIRST, last=LAST):
    if sha((card / 'BANK_A' / anchor.name).read_bytes()) != sha(anchor.read_bytes()):
        raise RuntimeError('SD identity check failed')
    result = json.loads((run / 'result.json').read_text(encoding='utf8'))
    count = result['completed_trials']
    stopped = result['status'] == 'STOPPED'
    if stopped:
        closure = json.loads((run / 'failed_trial_close.json').read_text(encoding='utf8'))['events'][-1]
        if result['stopped_trial'] != count + 1 or closure['command'] != 'TEST_END' or closure['reply'] != 'OK':
            raise RuntimeError('Failed trial closure was not confirmed')
        count += 1
    elif result['status'] != 'TRIALS_COMPLETE_CSV_PENDING':
        raise RuntimeError('Unexpected endurance result')
    if first < 1 or last - first + 1 != count:
        raise RuntimeError('Trial range does not match endurance result')
    first_time = (dt.datetime.fromisoformat(result['started']) - dt.timedelta(minutes=2)).strftime('%Y%m%d_%H%M%S')
    last_time = (dt.datetime.fromisoformat(result['ended']) + dt.timedelta(minutes=2)).strftime('%Y%m%d_%H%M%S')
    ate = {}
    for line in (run / 'ate.jsonl').read_text(encoding='utf8').splitlines():
        row = json.loads(line)
        if row['trial'] and row['command'] in QUERIES:
            ate[(row['trial'], row['command'])] = row['reply']
    stamp = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    out = run / f'pc_card_recovery_{stamp:%Y%m%d_%H%M%S_%f}'
    out.mkdir()
    found = {}
    for folder in (card / 'BANK_A', card / 'BANK_B'):
        for path in folder.glob('*_T*.csv'):
            m = re.fullmatch(r'(\d{8}_\d{6})_T(\d{6,})\.csv', path.name)
            if m and first_time <= m[1] <= last_time and first <= int(m[2]) <= last:
                found.setdefault(int(m[2]), []).append(path)

    files, errors = [], []
    for number in range(first, last + 1):
        trial_id = f'T{number:06d}'
        paths = found.get(number, [])
        if len(paths) != 1:
            errors.append(f'{trial_id}: expected one CSV, found {len(paths)}')
            continue
        src = paths[0]
        try:
            raw = src.read_bytes()
            dst = out / src.name
            with dst.open('xb') as f:
                f.write(raw)
            digest = sha(raw)
            if sha(dst.read_bytes()) != digest or sha(src.read_bytes()) != digest:
                raise ValueError('Source and copy SHA-256 mismatch')
            rows = list(csv.reader(io.StringIO(raw.decode('utf8'))))
            if len(rows) < 2 or any(len(row) != 14 for row in rows):
                raise ValueError('Invalid CSV shape')
            records = [dict(zip(rows[0], row)) for row in rows[1:]]
            markers = {(r['event'], r['detail']) for r in records}
            if ('TRIAL_START', f'trial_id={trial_id}') not in markers or (
                    'TRIAL_END_REQUEST', f'trial_id={trial_id};reason=TEST_END') not in markers:
                raise ValueError('Missing trial start or end')
            for command in QUERIES:
                replies = [r['result'] for r in records if r['category'] == 'ATE' and
                           r['event'] == 'RESULT' and r['detail'] == command]
                expected = ate.get((number - first + 1, command))
                if replies != ([] if expected is None else [expected]):
                    raise ValueError(f'ATE/CSV response mismatch for {command}')
            files.append({'trial_id': trial_id, 'name': src.name, 'bank': src.parent.name,
                          'bytes': len(raw), 'sha256': digest, 'data_rows': len(records),
                          'outcome': 'timeout' if stopped and number == last else 'completed'})
        except (OSError, UnicodeError, ValueError, KeyError, csv.Error) as exc:
            errors.append(f'{trial_id}: {exc}')
    report = {'source': str(card), 'copied_count': len(list(out.glob('*.csv'))),
              'verified_count': len(files), 'expected_count': count,
              'files': files, 'errors': errors}
    (out / 'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}, ensure_ascii=False))
    print(out)
    return 1 if errors else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('card', type=Path)
    parser.add_argument('--run', type=Path, default=RUN)
    parser.add_argument('--anchor', type=Path, default=ANCHOR)
    parser.add_argument('--first', type=int, default=FIRST)
    parser.add_argument('--last', type=int, default=LAST)
    args = parser.parse_args()
    raise SystemExit(main(args.card, args.run, args.anchor, args.first, args.last))
