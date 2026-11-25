"""Read fixture state after the completed single measurement. No new trial."""

import datetime as dt
import json
from pathlib import Path

import serial

from verify_host_after_flash import HOST_INFO, exchange


def main():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    path = Path(__file__).with_name(f'ate_post_state_{now:%Y%m%d_%H%M%S_%f}.json')
    result = {'started': now.isoformat(), 'port': 'COM5', 'events': [], 'status': 'STOPPED'}
    try:
        with serial.Serial('COM5', 57600, timeout=0.05, write_timeout=1) as ate:
            initial = ate.read(4096)
            result['initial_hex'] = initial.hex()
            if initial:
                raise RuntimeError('Preexisting ATE output')
            statuses = {'COMM_STATUS?': 'OK:state=IDLE', 'SD_STATUS?': 'OK', 'LOG_DROP_COUNT?': '0'}
            for command, expected in statuses.items():
                if exchange(ate, command, result['events']) != expected:
                    raise RuntimeError(f'Unexpected response for {command}')
            host = exchange(ate, 'HOST_INFO? METER', result['events'])
            if not HOST_INFO.fullmatch(host):
                raise RuntimeError('Expected meter HOST .25.1 READY')
            check = exchange(ate, 'PICO_SELF_CHECK?', result['events'])
            fields = set(check.split(':', 1)[-1].split(';'))
            if not {'TEST_LOGGER=OK', 'TEST_LOG_DROP=OK'} <= fields:
                raise RuntimeError('Missing test logger status in self check')
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
