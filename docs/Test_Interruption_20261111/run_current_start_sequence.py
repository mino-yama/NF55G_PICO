"""現行ATE入口の実機観測用。FWを変更せず、明示指定ポートだけを使用する。"""
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
    evidence = {'kind': 'hardware_ate_sequence', 'port': args.port,
                'baudrate': args.baudrate, 'started_jst': datetime.now(JST).isoformat(),
                'commands': [], 'wait': None, 'completed': False}
    output = Path(__file__).parent / ('Hardware_Sequence_' + datetime.now(JST).strftime('%Y%m%d_%H%M%S') + '.json')
    start_time = time.monotonic()

    def save():
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')

    with serial.Serial(args.port, args.baudrate, timeout=0.1, write_timeout=2) as port:
        def query(command):
            time.sleep(0.15)
            row = {'command': command, 'sent_jst': datetime.now(JST).isoformat(),
                   'sent_elapsed_s': time.monotonic() - start_time}
            evidence['commands'].append(row)
            port.write((command + '\r\n').encode('ascii'))
            port.flush()
            received = bytearray()
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                received.extend(port.read(1))
                if received.endswith(b'\n'):
                    break
            row.update(response_hex=received.hex(),
                       response=bytes(received).decode('ascii', errors='backslashreplace').rstrip('\r\n'),
                       received_elapsed_s=time.monotonic() - start_time)
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
            wait_start = time.monotonic()
            time.sleep(10)
            evidence['wait'] = {'requested_s': 10, 'actual_s': time.monotonic() - wait_start}
            query('TEST_START')
            # 自動Refreshを挟まず、再START後に旧DATAが参照可能か観測する。
            for command in ('NF55_DATETIME?', 'VOUT12?', 'COMM_STATUS?', 'SD_STATUS?', 'LOG_DROP_COUNT?'):
                query(command)
            query('TEST_END')
            for command in ('PICO_SELF_CHECK?', 'SD_STATUS?', 'LOG_DROP_COUNT?', 'COMM_STATUS?'):
                query(command)
            evidence['completed'] = True
        except Exception as exc:
            evidence['error'] = repr(exc)
            raise
        finally:
            save()
            print('Evidence:', output, flush=True)


if __name__ == '__main__':
    main()
