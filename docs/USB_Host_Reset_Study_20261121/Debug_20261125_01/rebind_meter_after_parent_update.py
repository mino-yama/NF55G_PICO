"""Confirm parent ATE startup and restart the identified meter HOST once."""
import argparse
import json
from pathlib import Path
import re
import time

import serial

from verify_host_after_flash import HOST_INFO, exchange


def main(path, host_version='20261125.1'):
    ready_pattern = HOST_INFO.pattern.replace(r'20261125\.1', re.escape(host_version))
    before_pattern = ready_pattern.removesuffix('READY') + '(?:READY|FAULT)'
    events = []
    result = {'events': events, 'status': 'STOPPED'}
    with path.open('x', encoding='utf8') as log:
        try:
            with serial.Serial('COM5', 57600, timeout=0.05, write_timeout=1) as ate:
                if ate.read(4096):
                    raise RuntimeError('Preexisting ATE output')
                def ask(command):
                    return exchange(ate, command, events)
                if ask('*IDN?') != 'NF55G_PICO_FIXTURE,Rev.0' or ask('COMM_STATUS?') != 'OK:state=IDLE':
                    raise RuntimeError('Parent not ready')
                if ask('SD_STATUS?') != 'OK':
                    raise RuntimeError('Parent SD not ready')
                old = ask('HOST_INFO? METER')
                if not re.fullmatch(before_pattern, old):
                    raise RuntimeError('Unexpected HOST before restart')
                uid, nonce = old.split(':')[2], old.split(':')[-2]
                if ask('HOST_RESET METER') != f'OK:HOST_RESET_ACCEPTED:{uid}:{nonce}':
                    raise RuntimeError('HOST reset not acknowledged')
                time.sleep(4)
                done = ask('HOST_INFO? METER')
                verified = re.fullmatch(f'OK:HOST_RESET_DONE:{uid}:{nonce}:([0-9A-Fa-f]{{16}}):READY', done)
                if verified is None or verified[1].lower() == nonce.lower():
                    raise RuntimeError('New HOST nonce or READY not confirmed')
                new = ask('HOST_INFO? METER')
                if not re.fullmatch(ready_pattern, new) or new.split(':')[-2].lower() != verified[1].lower():
                    raise RuntimeError('Unexpected HOST version or nonce after reset')
            result['status'] = 'SUCCESS'
        except Exception as exc:
            result['error'] = repr(exc)
            print(f'STOPPED: {exc}', flush=True)
        finally:
            json.dump(result, log, ensure_ascii=False, indent=2)
    return 0 if result['status'] == 'SUCCESS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--host-version', choices=('20261125.1', '20261125.2'), default='20261125.1')
    args = parser.parse_args()
    raise SystemExit(main(args.log, args.host_version))
