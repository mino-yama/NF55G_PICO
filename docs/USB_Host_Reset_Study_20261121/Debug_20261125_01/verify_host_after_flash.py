"""Verify .25.1 startup and one 7355 IDN through the ATE port."""

import datetime as dt
import json
from pathlib import Path
import re
import time

import serial


HOST_INFO = re.compile(
    r'OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261125\.1:[0-9A-Fa-f]{16}:READY'
)
IDN = b'ADC Corp.,7355,246410099,  A02\r\n'


def exchange(ate, command, events, verbose=True):
    tx = command.encode('ascii') + b'\r'
    raw = bytearray()
    started = time.monotonic()
    event = {'command': command, 'tx_hex': tx.hex()}
    events.append(event)
    try:
        if ate.write(tx) != len(tx):
            raise RuntimeError('Incomplete ATE write')
        while b'\r' not in raw and time.monotonic() - started < 12:
            raw.extend(ate.read(4096))
    finally:
        event['raw_hex'] = raw.hex()
        event['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
    if raw.count(b'\r') != 1 or not raw.endswith(b'\r'):
        raise RuntimeError(f'Missing or extra ATE response for {command}')
    reply = raw[:-1].decode('ascii')
    event['reply'] = reply
    if verbose:
        print(f'{command} -> {reply}', flush=True)
    return reply


def main():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    path = Path(__file__).with_name(f'ate_after_flash_{now:%Y%m%d_%H%M%S_%f}.json')
    result = {'started': now.isoformat(), 'port': 'COM5', 'baud': 57600,
              'events': [], 'status': 'STOPPED'}
    try:
        with serial.Serial('COM5', 57600, timeout=0.05, write_timeout=1) as ate:
            initial = ate.read(4096)
            result['initial_hex'] = initial.hex()
            if initial:
                raise RuntimeError('Preexisting ATE output')

            def ask(command):
                return exchange(ate, command, result['events'])

            if ask('*IDN?') != 'NF55G_PICO_FIXTURE,Rev.0':
                raise RuntimeError('Unexpected fixture identity')
            if ask('COMM_STATUS?') != 'OK:state=IDLE':
                raise RuntimeError('Fixture not IDLE')
            host = ask('HOST_INFO? METER')
            if not HOST_INFO.fullmatch(host):
                raise RuntimeError('Expected meter HOST .25.1 READY')
            if ask('SD_STATUS?') != 'OK':
                raise RuntimeError('SD not ready')
            before_drop = ask('LOG_DROP_COUNT?')
            if not before_drop.isdecimal():
                raise RuntimeError('Invalid log drop count')
            if ask('EXT_QUERY 2000 *IDN?') != f'OK:EXT_RX:{len(IDN)}:{IDN.hex().upper()}':
                raise RuntimeError('7355 IDN or CRLF mismatch')
            if ask('HOST_INFO? METER') != host:
                raise RuntimeError('Meter HOST state or boot nonce changed')
            if ask('COMM_STATUS?') != 'OK:state=IDLE':
                raise RuntimeError('Fixture not IDLE after IDN')
            if ask('LOG_DROP_COUNT?') != before_drop:
                raise RuntimeError('Log drop count changed')
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
