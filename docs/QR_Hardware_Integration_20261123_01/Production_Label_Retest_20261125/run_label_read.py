"""Compare physical scans to the approved test payloads through COM5."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time

import serial


def run(port, expected, record):
    def ask(command):
        port.write(command.encode('ascii') + b'\r')
        raw = port.read_until(b'\r')
        row = {'command': command, 'raw_hex': raw.hex()}
        record['operations'].append(row)
        if not raw.endswith(b'\r'):
            raise TimeoutError(command)
        row['reply'] = raw[:-1].decode('ascii')
        return row['reply']

    def check(actual, wanted):
        if actual != wanted:
            raise RuntimeError(f'{actual!r}; expected {wanted!r}')

    check(ask('*IDN?'), 'NF55G_PICO_FIXTURE,Rev.0')
    check(ask('COMM_STATUS?'), 'OK:state=IDLE')
    check(ask('SD_STATUS?'), 'OK')
    initial_drops = ask('LOG_DROP_COUNT?')
    if not initial_drops.isdecimal():
        raise RuntimeError(initial_drops)
    previous = None
    for name, sample in expected.items():
        check(ask('TEST_START'), 'OK')
        try:
            if previous is not None:
                check(ask('QR_GET? ' + previous), 'ERR:QR_STALE_ID')
            armed = ask('QR_SCAN 60000')
            if not armed.startswith('OK:QR_ARMED:'):
                raise RuntimeError(armed)
            token = armed.split(':')[-1]
            record['armed_label'] = name
            print(f'SCAN {name} NOW ({token})', flush=True)
            deadline = time.monotonic() + 62
            while time.monotonic() < deadline:
                reply = ask('QR_GET? ' + token)
                if reply != 'ERR:QR_READING':
                    break
                time.sleep(.5)
            record['scan_reply'] = reply
            if reply == 'ERR:QR_TIMEOUT':
                raise TimeoutError(f'QR {name}: no payload within the acceptance window')
            check(reply, f'OK:QR_GET:{token}:{sample["payload"]}')
            check(ask('QR_DATA? ' + token), f'OK:QR_DATA:{token}:{sample["ss_data_hex"]}')
            record['verified'].append({'label': name, 'token': token, 'payload': sample['payload']})
            print(f'{name}: QR and SS preview matched', flush=True)
        finally:
            check(ask('TEST_END'), 'OK')
        check(ask('QR_GET? ' + token), 'ERR:QR_STALE_ID')
        previous = token
    check(ask('LOG_DROP_COUNT?'), initial_drops)
    check(ask('SD_STATUS?'), 'OK')
    check(ask('COMM_STATUS?'), 'OK:state=IDLE')
    record['result'] = 'COMPLETE'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', choices=('A', 'B'), help='check only the selected label')
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    expected = json.loads((folder / 'expected.json').read_text(encoding='utf8'))
    if args.label:
        expected = {args.label: expected[args.label]}
    now = datetime.now(timezone(timedelta(hours=9)))
    output = folder / f'ATE_QR_Read_{now:%Y%m%d_%H%M%S_%f}.json'
    record = {'started': now.isoformat(), 'port': 'COM5', 'labels': list(expected),
              'operations': [], 'verified': []}
    try:
        with serial.Serial('COM5', 57600, timeout=12) as port:
            port.reset_input_buffer()
            run(port, expected, record)
    except Exception as error:
        record['result'] = 'STOPPED'
        record['error'] = repr(error)
        raise
    finally:
        with output.open('x', encoding='utf8') as file:
            json.dump(record, file, ensure_ascii=False, indent=2)
            file.write('\n')
        print(output, flush=True)


if __name__ == '__main__':
    main()
