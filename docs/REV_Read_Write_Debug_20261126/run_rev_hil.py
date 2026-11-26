import argparse
import csv
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import subprocess
import sys


FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[1]
sys.path.insert(0, str(ROOT))
from src.frame import build_frame, parse_frame
from src.nf55_command import build_control_command
from src.qr_write_session import serial_data_from_qr


PREFIX = 'US250A-CGXE-009491-101'


def plan(base):
    rev, lot, serial = (base[6:10].decode(), base[10:14].decode(), base[14:20].decode())
    inputs = [('QR-REV', 'A03', lot, serial),
              ('QR-LOT', 'A03', '2602' if lot != '2602' else '2603', serial),
              ('QR-SERIAL', 'A03', '2602' if lot != '2602' else '2603', '000007'),
              ('REV-02', 'B7.', '2604', '000008')]
    cases = []
    for name, code, week, number in inputs:
        label = PREFIX + code + week + number
        data = ('F' * 6 + code + ' ' + week + number + 'F' * 30).encode()
        assert serial_data_from_qr(label) == data
        cases.append((name, 'qr', label, data.hex()))
    diagnostic = [
        ('REV-01', b'F' * 6 + b'T0142605000010' + b'F' * 30),
        ('REV-03', b'F' * 6 + b'T032606000011' + b'F' * 30),
        ('REV-04', b'F' * 6 + b'T042607000012' + b'F' * 31),
        ('REV-05', b'F' * 6 + b'FFFF2608000013' + b'F' * 30),
    ]
    for name, data in diagnostic:
        assert len(data) == (49 if name == 'REV-03' else 50)
        assert parse_frame(build_frame('SS', data), expected_cmd='SS').data == data
        if name == 'REV-04':
            assert (data[6:10], data[10:14], data[14:20]) == (b'T042', b'6070', b'00012F')
        cases.append((name, 'diagnostic', None, data.hex()))
    for name, _, label, data in cases:
        if name != 'REV-03':
            assert build_control_command('SERIAL_SET_RAW', bytes.fromhex(data)).data == bytes.fromhex(data)
    return cases


def collect(directory, phase, baseline, cases):
    source = (FOLDER / 'rev_hil_parent.py').read_text(encoding='utf8')
    script = directory / f'parent_{phase}.py'
    script.write_text(f'REV_BASELINE = {baseline!r}\nREV_CASES = {cases!r}\n' + source, encoding='utf8')
    base = [sys.executable, '-u', '-m', 'mpremote', 'connect', 'COM6', 'resume']
    log = directory / f'{phase}_wire.log'
    print(log, flush=True)
    events = []
    try:
        with log.open('x', encoding='utf8') as file, subprocess.Popen(
                base + ['run', str(script)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf8', errors='replace') as process:
            for line in process.stdout:
                file.write(line)
                file.flush()
                if 'REV_HIL|' in line:
                    event = json.loads(line.split('REV_HIL|', 1)[1])
                    events.append(event)
                    if event['event'] in ('BASELINE', 'CASE', 'RESTORE', 'END'):
                        print(json.dumps(event, ensure_ascii=False), flush=True)
            code = process.wait()
    finally:
        subprocess.run(base + ['exec', '--no-follow', "import sys; sys.modules['src.main'].active_app.run()"],
                       timeout=15, check=True)
    (directory / f'{phase}_events.json').write_text(json.dumps(events, indent=2), encoding='utf8')
    return events, code


def report(directory, events):
    records = [event for event in events if event['event'] == 'CASE']
    keys = ('case', 'mode', 'qr', 'qr_rev_repr', 'ss_rev_visible', 'ss_rev_repr', 'ss_rev_hex', 'ss_rev_width',
            'ss_data_width', 'ss_lot', 'ss_serial', 'd5_rev_visible', 'd5_rev_repr', 'd5_rev_width', 'd5_rev_hex',
            'd5_lot', 'd5_serial', 'unit_comparison', 'other_fields_unchanged', 'ok', 'error', 'nak_reason',
            'ambiguous', 'command_retry', 'response_retry', 'before', 'after', 'ss_hex', 'user_judgment')
    with (directory / 'case_results.csv').open('x', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, keys, extrasaction='ignore')
        writer.writeheader()
        for row in records:
            ss, before, after = [bytes.fromhex(row[key]) for key in ('ss_hex', 'before', 'after')]
            srev = ss[6:9] if row['case'] == 'REV-03' else ss[6:10]
            observed = after[6:10]
            marker = 'not accepted or unknown'
            if row['ok'] and len(ss) == 50:
                marker = 'match' if all(
                    ss[a:b] == after[a:b] if ss[a:b] != b'F' * (b-a) else before[a:b] == after[a:b]
                    for a, b in ((6,10),(10,14),(14,20))) else 'mismatch'
            writer.writerow(dict(row, qr_rev_repr=repr(row['qr'][22:25]) if row['qr'] else '',
                                 ss_rev_visible=srev.decode().replace(' ', '<SP>'), ss_rev_repr=repr(srev.decode()),
                                 ss_rev_hex=srev.hex(), ss_rev_width=len(srev), ss_data_width=len(ss),
                                 ss_lot=ss[10:14].decode() if len(ss) == 50 else '',
                                 ss_serial=ss[14:20].decode() if len(ss) == 50 else '',
                                 d5_rev_visible=observed.decode().replace(' ', '<SP>'), d5_rev_repr=repr(observed.decode()),
                                 d5_rev_width=len(observed), d5_rev_hex=observed.hex(), d5_lot=after[10:14].decode(),
                                 d5_serial=after[14:20].decode(), unit_comparison=marker,
                                 other_fields_unchanged=before[:6]+before[20:]==after[:6]+after[20:]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', type=Path, help='use the previously saved read-only baseline directory')
    args = parser.parse_args()
    if args.execute is None:
        directory = FOLDER / datetime.now(timezone(timedelta(hours=9))).strftime('run_%Y%m%d_%H%M%S_%f')
        directory.mkdir()
        events, code = collect(directory, 'preflight', None, ())
        assert code == 0
        baseline, = [row['hex'] for row in events if row['event'] == 'BASELINE']
        cases = plan(bytes.fromhex(baseline))
        (directory / 'planned_cases.json').write_text(json.dumps({'baseline': baseline, 'cases': cases}, indent=2),
                                                      encoding='utf8')
        print(directory, flush=True)
        return
    directory = args.execute.resolve()
    assert directory.parent == FOLDER and directory.name.startswith('run_')
    saved = json.loads((directory / 'planned_cases.json').read_text(encoding='utf8'))
    assert [list(row) for row in plan(bytes.fromhex(saved['baseline']))] == saved['cases']
    events, code = collect(directory, 'execution', saved['baseline'], saved['cases'])
    report(directory, events)
    if code or not any(row['event'] == 'RESTORE' and row['exact'] for row in events):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
