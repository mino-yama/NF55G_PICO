"""Check ATE startup and meter HOST management with the SD card removed."""
import datetime as dt
import json
from pathlib import Path
import re

import serial

from verify_host_after_flash import exchange


def main():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    path = Path(__file__).with_name(f'parent_no_sd_{now:%Y%m%d_%H%M%S_%f}.json')
    result = {'started': now.isoformat(), 'port': 'COM5', 'user_reported_sd_removed': True,
              'events': [], 'status': 'STOPPED'}
    try:
        with serial.Serial('COM5', 57600, timeout=0.05, write_timeout=1) as ate:
            initial = ate.read(4096)
            result['initial_hex'] = initial.hex()
            if initial:
                raise RuntimeError('Unexpected input before ATE query')
            def ask(command):
                return exchange(ate, command, result['events'])
            if ask('*IDN?') != 'NF55G_PICO_FIXTURE,Rev.0':
                raise RuntimeError('Unexpected fixture identity')
            if ask('COMM_STATUS?') != 'OK:state=IDLE':
                raise RuntimeError('Expected parent IDLE')
            result['sd_status'] = ask('SD_STATUS?')
            result['host_info'] = ask('HOST_INFO? METER')
            if result['sd_status'] == 'OK':
                raise RuntimeError('Parent reports SD OK despite SD removal')
            if not re.fullmatch(r'OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261125\.2:'
                                r'[0-9A-Fa-f]{16}:READY', result['host_info']):
                raise RuntimeError('Meter HOST .25.2 READY not confirmed')
        result['status'] = 'SUCCESS'
    except Exception as exc:
        result['error'] = repr(exc)
        print(f'STOPPED: {exc}', flush=True)
    finally:
        with path.open('x', encoding='utf8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"{result['status']}: {path}", flush=True)
    return 0 if result['status'] == 'SUCCESS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
