"""再START修正版の3試行実機検証。指定ATEポートで期待応答を照合する。"""
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import time

import serial

JST = timezone(timedelta(hours=9))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    parser.add_argument('--baudrate', type=int, required=True)
    args = parser.parse_args()
    evidence = {'kind': 'restart_fix_three_trials', 'port': args.port,
                'baudrate': args.baudrate, 'started_jst': datetime.now(JST).isoformat(),
                'commands': [], 'wait': None, 'completed': False}
    output = Path(__file__).parent / ('Restart_Fix_Sequence_' + datetime.now(JST).strftime('%Y%m%d_%H%M%S') + '.json')
    start_time = time.perf_counter()

    def save():
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')

    with serial.Serial(args.port, args.baudrate, timeout=0.1, write_timeout=2) as port:
        def query(command):
            time.sleep(0.15)
            row = {'command': command, 'sent_jst': datetime.now(JST).isoformat(),
                   'sent_elapsed_s': time.perf_counter() - start_time}
            evidence['commands'].append(row)
            port.write((command + '\r\n').encode('ascii'))
            port.flush()
            received = bytearray()
            deadline = time.perf_counter() + 5
            while time.perf_counter() < deadline:
                received.extend(port.read(1))
                if received.endswith(b'\n'):
                    break
            row.update(response_hex=received.hex(),
                       response=bytes(received).decode('ascii', errors='backslashreplace').rstrip('\r\n'),
                       received_elapsed_s=time.perf_counter() - start_time)
            row['response_seconds'] = row['received_elapsed_s'] - row['sent_elapsed_s']
            save()
            print(command, '=>', row['response'], flush=True)
            if not received.endswith(b'\n'):
                raise RuntimeError('ATE response timeout; no automatic command retry')
            return row['response']

        try:
            if not query('*IDN?').startswith('NF55G_PICO_FIXTURE,'):
                raise RuntimeError('Unexpected fixture identity')
            for command in ('COMM_STATUS?', 'RTC_DATETIME?', 'SD_STATUS?', 'PICO_SELF_CHECK?', 'LOG_DROP_COUNT?'):
                query(command)
            if query('TEST_START') != 'OK':
                raise RuntimeError('Initial TEST_START rejected; existing session left unchanged')
            # SC日時は送信直前の日本時間。過去の固定試験日時を再利用しない。
            clock_command = 'CLOCK_SYNC ' + datetime.now(JST).strftime('%y%m%d%H%M%S')
            if query(clock_command) != 'OK':
                raise RuntimeError('SC failed; no automatic retry or additional product command')
            if query('DATA_REFRESH') != 'OK':
                raise RuntimeError('DATA_REFRESH failed')
            for command in ('NF55_DATETIME?', 'VOUT12?', 'IOUT12?', 'BATT_VOLT?'):
                query(command)
            wait_start = time.perf_counter()
            time.sleep(10)
            evidence['wait'] = {'requested_s': 10, 'actual_s': time.perf_counter() - wait_start}
            for attempt in (2, 3):
                assert query('TEST_START') == 'OK', 'Restart rejected'
                for command in ('NF55_DATETIME?', 'VOUT12?'):
                    assert query(command) == 'ERR:CACHE_INVALID', 'Old DATA inherited'
                assert query('DATA_REFRESH') == 'OK', 'New DATA_REFRESH failed'
                for command in ('NF55_DATETIME?', 'VOUT12?', 'IOUT12?', 'BATT_VOLT?'):
                    assert not query(command).startswith('ERR:'), 'New query failed'
                assert query('SD_STATUS?') == 'OK', 'SD failure'
                assert query('LOG_DROP_COUNT?') == '0', 'Log dropped'
            assert query('TEST_END') == 'OK', 'TEST_END failed'
            for command in ('PICO_SELF_CHECK?', 'SD_STATUS?', 'LOG_DROP_COUNT?', 'COMM_STATUS?'):
                answer = query(command)
                if command == 'PICO_SELF_CHECK?':
                    assert answer.startswith('OK:'), 'Self check failed'
                elif command == 'LOG_DROP_COUNT?':
                    assert answer == '0', 'Final drops'
                elif command == 'COMM_STATUS?':
                    assert answer == 'OK:state=IDLE', 'Not IDLE'
                else:
                    assert answer == 'OK', 'SD failure'
            evidence['completed'] = True
        except Exception as exc:
            evidence['error'] = repr(exc)
            raise
        finally:
            save()
            print('Evidence:', output, flush=True)


if __name__ == '__main__':
    main()
