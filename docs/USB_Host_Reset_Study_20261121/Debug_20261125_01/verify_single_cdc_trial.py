"""Run one CDC/SD preflight trial with the operator-confirmed 200 mV / 40 mV setup."""

import datetime as dt
import json
from pathlib import Path
import re

import serial

from verify_host_after_flash import HOST_INFO, IDN, exchange


def main():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    path = Path(__file__).with_name(f'ate_single_trial_{now:%Y%m%d_%H%M%S_%f}.json')
    result = {'started': now.isoformat(), 'port': 'COM5', 'baud': 57600,
              'ate_selected_range_mV': 200, 'input_setpoint_mV': 40,
              'events': [], 'meter_responses': {}, 'status': 'STOPPED'}
    try:
        with serial.Serial('COM5', 57600, timeout=0.05, write_timeout=1) as ate:
            initial = ate.read(4096)
            result['initial_hex'] = initial.hex()
            if initial:
                raise RuntimeError('Preexisting ATE output')

            def ask(command):
                return exchange(ate, command, result['events'])

            def expect(command, value):
                if ask(command) != value:
                    raise RuntimeError(f'Unexpected response for {command}')

            def meter(command, timeout_ms):
                reply = ask(f'EXT_QUERY {timeout_ms} {command}')
                match = re.fullmatch(r'OK:EXT_RX:([0-9]+):([0-9A-Fa-f]+)', reply)
                if not match:
                    raise RuntimeError(f'Unsuccessful or ambiguous meter response for {command}')
                raw = bytes.fromhex(match[2])
                if len(raw) != int(match[1]) or not raw.endswith(b'\r\n'):
                    raise RuntimeError(f'Incorrect meter response length or terminator for {command}')
                result['meter_responses'][command] = {'hex': raw.hex(), 'text': raw.decode('ascii')}
                return raw

            expect('*IDN?', 'NF55G_PICO_FIXTURE,Rev.0')
            expect('COMM_STATUS?', 'OK:state=IDLE')
            host = ask('HOST_INFO? METER')
            if not HOST_INFO.fullmatch(host):
                raise RuntimeError('Expected meter HOST .25.1 READY')
            expect('SD_STATUS?', 'OK')
            drops = ask('LOG_DROP_COUNT?')
            if not drops.isdecimal():
                raise RuntimeError('Invalid log drop count')
            if meter('*IDN?', 2000) != IDN:
                raise RuntimeError('Unexpected 7355 identity')
            meter(':CONF?', 2000)
            expect('TEST_START', 'OK')
            meter(':READ?', 10000)
            meter(':SYST:ERR?', 2000)
            expect('TEST_END', 'OK')
            check = ask('PICO_SELF_CHECK?')
            for field in ('TEST_LOGGER=OK', 'TEST_LOG_DROP=OK'):
                if not re.search(r'(?:^|[,:;\s])' + field + r'(?:$|[,:;\s])', check):
                    raise RuntimeError(f'Missing {field} in self check')
            expect('SD_STATUS?', 'OK')
            expect('LOG_DROP_COUNT?', drops)
            expect('COMM_STATUS?', 'OK:state=IDLE')
            expect('HOST_INFO? METER', host)
        result['status'] = 'SUCCESS'
    except Exception as exc:
        result['error'] = repr(exc)
        print(f'STOPPED: {exc}', flush=True)
    finally:
        with path.open('x', encoding='utf8') as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
        print(f"{result['status']}: {path}", flush=True)
    return 0 if result['status'] == 'SUCCESS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
