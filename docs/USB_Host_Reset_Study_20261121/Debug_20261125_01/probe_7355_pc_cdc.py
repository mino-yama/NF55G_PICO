"""Identify the same meter once after moving only its USB cable to the PC."""
import datetime as dt
import json
from pathlib import Path
import time

import serial
from serial.tools import list_ports

from verify_host_after_flash import IDN


def main():
    ports = [p for p in list_ports.comports() if (p.vid, p.pid) == (0x1334, 0x0309)]
    if len(ports) != 1:
        raise SystemExit(f'Expected one ADCMT USB CDC device, found {len(ports)}; no command sent')
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    path = Path(__file__).with_name(f'pc_cdc_idn_{now:%Y%m%d_%H%M%S_%f}.json')
    result = {'timestamp': now.isoformat(), 'port': ports[0].device, 'hwid': ports[0].hwid,
              'baud': 9600, 'dtr': True, 'rts': True, 'status': 'STOPPED'}
    raw = bytearray()
    try:
        with serial.Serial(ports[0].device, 9600, timeout=0.05, write_timeout=1) as meter:
            meter.dtr = True
            meter.rts = True
            before = meter.read(4096)
            result['preexisting_hex'] = before.hex()
            if before:
                raise RuntimeError('Preexisting CDC output, retained as evidence')
            command = b'*IDN?\r\n'
            result['tx_hex'] = command.hex()
            started = time.monotonic()
            if meter.write(command) != len(command):
                raise RuntimeError('Incomplete CDC write')
            while not raw.endswith(b'\r\n') and time.monotonic() - started < 2:
                raw.extend(meter.read(4096))
            result['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
            if raw != IDN:
                raise RuntimeError('Expected IDN and CRLF did not match')
        result['status'] = 'SUCCESS'
    except Exception as exc:
        result['error'] = repr(exc)
    finally:
        result['rx_hex'] = raw.hex()
        with path.open('x', encoding='utf8') as out:
            json.dump(result, out, ensure_ascii=False, indent=2)
        print(f"{result['status']}: {path}", flush=True)
    return 0 if result['status'] == 'SUCCESS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
