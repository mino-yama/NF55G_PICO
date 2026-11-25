"""Compare 7355 READ/SYST:ERR on PC CDC at the fixture's observed cadence."""
import argparse
import datetime as dt
import json
from pathlib import Path
import time

import serial
from serial.tools import list_ports

from verify_host_after_flash import IDN


JST = dt.timezone(dt.timedelta(hours=9))
INTERVAL = 2.718


def main(count):
    ports = [p for p in list_ports.comports() if (p.vid, p.pid) == (0x1334, 0x0309)
             and p.serial_number == '24641009900']
    if len(ports) != 1:
        raise SystemExit(f'Expected one matching 7355 CDC port, found {len(ports)}')
    now = dt.datetime.now(JST)
    out = Path(__file__).with_name(f'pc_cdc_comparison_{now:%Y%m%d_%H%M%S_%f}')
    out.mkdir()
    result = {'started': now.isoformat(), 'port': ports[0].device, 'hwid': ports[0].hwid,
              'planned': count, 'completed': 0, 'read_interval_s': INTERVAL,
              'status': 'STOPPED'}
    print(f'RECORDS: {out}', flush=True)
    trial = 0
    try:
        with serial.Serial(ports[0].device, 9600, timeout=0.05, write_timeout=1) as port, \
                (out / 'cdc.jsonl').open('x', encoding='utf8') as log:
            port.dtr = port.rts = True
            initial = port.read(4096)
            result['initial_hex'] = initial.hex()
            if initial:
                raise RuntimeError('Preexisting CDC output')

            def query(command, timeout):
                tx = command.encode('ascii') + b'\r\n'
                raw = bytearray()
                at = dt.datetime.now(JST).isoformat()
                start = time.monotonic()
                try:
                    if port.write(tx) != len(tx):
                        raise RuntimeError('Incomplete CDC write')
                    while b'\r\n' not in raw:
                        left = timeout - (time.monotonic() - start)
                        if left <= 0:
                            break
                        # Wait for the first byte; read buffered bytes without adding 50 ms.
                        raw.extend(port.read(port.in_waiting or 1))
                        if len(raw) > 192:
                            break
                    if len(raw) > 192 or not raw.endswith(b'\r\n') or raw.count(b'\r\n') != 1:
                        raise RuntimeError(f'{command}: incomplete or extra CDC response ({len(raw)} bytes)')
                    return raw.decode('ascii')
                finally:
                    log.write(json.dumps({'trial': trial, 'command': command, 'at': at,
                                          'tx_hex': tx.hex(), 'rx_hex': raw.hex(),
                                          'elapsed_ms': round((time.monotonic() - start)*1000, 3)}) + '\n')
                    log.flush()

            if query('*IDN?', 2).encode('ascii') != IDN:
                raise RuntimeError('Unexpected meter identity')
            result['conf'] = query(':CONF?', 2)
            print(f'CONF: {result["conf"].strip()}', flush=True)
            next_read = time.monotonic()
            for trial in range(1, count + 1):
                time.sleep(max(0, next_read - time.monotonic()))
                next_read = time.monotonic() + INTERVAL
                read = query(':READ?', 10)
                time.sleep(0.06)  # Match the fixture runner's UART capture interval.
                error = query(':SYST:ERR?', 2)
                result['completed'] = trial
                if trial == 1 or trial % 20 == 0 or trial == count:
                    print(f'{trial}/{count}: {read.strip()} / {error.strip()}', flush=True)
        result['status'] = 'SUCCESS'
    except (Exception, KeyboardInterrupt) as exc:
        result.update(error=repr(exc), stopped_trial=trial)
        print(f'STOPPED: {exc}', flush=True)
    finally:
        result['ended'] = dt.datetime.now(JST).isoformat()
        (out / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    return 0 if result['status'] == 'SUCCESS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, choices=(1, 400), required=True)
    raise SystemExit(main(parser.parse_args().count))
