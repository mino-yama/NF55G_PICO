"""Run one operator-prepared calibration point over ATE on the sample."""

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys

import serial

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'USB_Host_Reset_Study_20261121' / 'Debug_20261125_01'))
from verify_host_after_flash import exchange

HOST_READY = re.compile(r'OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261125\.2:[0-9A-Fa-f]{16}:READY')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator-reading', required=True, help='operator-confirmed 7355 reading or range with unit')
    parser.add_argument('--target', choices=('DISCHG_I', 'BATT_CHG', 'BATT_V'), default='BATT_CHG')
    parser.add_argument('--measurement-point', choices=('A', 'B'), default='A')
    parser.add_argument('--product-point', choices=('P1', 'P2'), default='P1')
    parser.add_argument('--measure-only', action='store_true', help='read and inspect the cache without an AD write')
    args = parser.parse_args()
    stamp = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    path = HERE / f'cache_point_{stamp:%Y%m%d_%H%M%S_%f}.json'
    target, point, destination = args.target, args.measurement_point, args.product_point
    verify_command = f'AD_VERIFY_{target} {destination}'
    result = {'operator_reading': args.operator_reading, 'target': target, 'point': point,
              'product_point': destination, 'measure_only': args.measure_only, 'events': [], 'status': 'STOPPED'}
    try:
        with serial.Serial('COM5', 57600, timeout=0.05, write_timeout=1) as ate:
            if ate.read(4096):
                raise ValueError('Unexpected pending ATE output')

            def ask(command, expected=None):
                reply = exchange(ate, command, result['events'])
                if expected is not None and reply != expected:
                    raise ValueError(f'{command}: {reply}')
                return reply

            ask('*IDN?', 'NF55G_PICO_FIXTURE,Rev.0')
            ask('COMM_STATUS?', 'OK:state=IDLE')
            ask('SD_STATUS?', 'OK')
            if not HOST_READY.fullmatch(ask('HOST_INFO? METER')):
                raise ValueError('Expected matching measurement HOST READY')
            before_drop = ask('LOG_DROP_COUNT?')
            if not before_drop.isdecimal():
                raise ValueError('Invalid initial log drop count')
            ask('INFO_REFRESH', 'OK')
            ask('FW_REV?', 'S1.14B')
            ask('UNIT_SERIAL?', '000001')
            ask(verify_command, 'ERR:CAL_NO_ACTIVE_TRIAL')
            ask('TEST_START', 'OK')
            try:
                # TEST_STARTでINFO Cacheが失効する。現在の試行で対象個体を確認する。
                ask('INFO_REFRESH', 'OK')
                ask('FW_REV?', 'S1.14B')
                ask('UNIT_SERIAL?', '000001')
                ask(verify_command, 'ERR:AD_VERIFY_NO_WRITE')
                measured = ask(f'CAL_MEASURE_{target} {point} 4000 :READ?')
                if not measured.startswith('OK:CAL_MEASURE:'):
                    raise ValueError(measured)
                acquisition = measured.split(':')[-1]
                cached = ask(f'CAL_MEASUREMENT_{target}? {point}')
                if not cached.startswith(f'OK:CAL_MEASUREMENT:{acquisition}:{target}:{point}:'):
                    raise ValueError(cached)
                if not args.measure_only:
                    written = ask(f'CAL_WRITE_{target} {point} {destination}')
                    if not written.startswith('OK:CAL_WRITE:'):
                        raise ValueError(written)
                    verified = ask(verify_command)
                    if not verified.startswith(f'OK:AD_VERIFY:{target}:{destination}:'):
                        raise ValueError(verified)
                    result['verify'] = verified
            finally:
                ask('TEST_END', 'OK')
                check = ask('PICO_SELF_CHECK?')
                fields = set(check.split(':', 1)[-1].split(';'))
                if not {'TEST_LOGGER=OK', 'TEST_LOG_DROP=OK'} <= fields:
                    raise ValueError('Test logger diagnostics were not OK')
                ask('SD_STATUS?', 'OK')
                ask('LOG_DROP_COUNT?', before_drop)
            result['status'] = 'TRIAL_COMPLETE'
    except (OSError, RuntimeError, ValueError) as exc:
        result['error'] = str(exc)
        print(f'STOPPED: {exc}', flush=True)
    finally:
        with path.open('x', encoding='utf-8') as log:
            json.dump(result, log, indent=2)
        print(path)
    return 0 if result['status'] == 'TRIAL_COMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
