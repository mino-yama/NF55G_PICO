"""再接続の識別・既存設定・測定の原文確認。設定を書かず異常で停止する。"""
import contextlib
import datetime
import json
from pathlib import Path
import re
import time
import serial

OUT = Path(__file__).resolve().parent / 'Readback_01'
OUT.mkdir(exist_ok=False)
raw = {k: bytearray() for k in ('ate', 'host')}
records, failure = [], None
commands = [b'EXT_QUERY 2000 *IDN?', b'EXT_QUERY 2000 :SENS:FUNC?', b'EXT_QUERY 2000 :CONF?',
            b'SD_STATUS?', b'RTC_CHECK?', b'LOG_DROP_COUNT?']
commands += [b'EXT_QUERY 2000 :READ?'] * 100
with contextlib.ExitStack() as stack:
    ports = {}
    for key, name, baud in [('ate', 'COM7', 57600), ('host', 'COM22', 115200)]:
        p = serial.Serial(port=None, baudrate=baud, timeout=0, write_timeout=1)
        p.port, p.dtr, p.rts = name, False, False
        p.open()
        ports[key] = stack.enter_context(p)
    try:
        for command in commands:
            before = len(raw['ate'])
            began = time.monotonic()
            ports['ate'].write(command + b'\r')
            while time.monotonic() - began < 4:
                for key, p in ports.items():
                    n = p.in_waiting
                    if n:
                        raw[key].extend(p.read(n))
                if b'\r' in raw['ate'][before:]:
                    break
                time.sleep(.001)
            reply = bytes(raw['ate'][before:])
            record = {'command': command.decode(), 'reply': reply.decode('ascii', 'backslashreplace'),
                      'elapsed_ms': round((time.monotonic() - began) * 1000, 3)}
            records.append(record)
            if command.startswith(b'EXT_QUERY'):
                parts = reply.rstrip(b'\r').split(b':')
                if parts[:2] != [b'OK', b'EXT_RX']:
                    raise RuntimeError('query failed: ' + repr(reply))
                value = bytes.fromhex(parts[3].decode())
                record['raw_hex'] = value.hex()
                if int(parts[2]) != len(value) or not value.endswith(b'\r\n'):
                    raise RuntimeError('response boundary')
                if command.endswith(b':SENS:FUNC?') and value.strip().strip(b'"') != b'VOLT:DC':
                    raise RuntimeError('current mode is not expected DCV; stop before READ')
                if command.endswith(b':READ?') and not re.fullmatch(rb'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?\r\n', value):
                    raise RuntimeError('measurement is not a complete single decimal')
            if len(records) <= 6 or len(records) % 25 == 6:
                print(json.dumps(record), flush=True)
    except Exception as exc:
        failure = repr(exc)
    finally:
        for key, value in raw.items():
            (OUT / (key + '.raw')).write_bytes(value)
        (OUT / 'requests.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
        result = {'date_jst': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
                  'requests': len(records), 'read_count': sum(r['command'].endswith(':READ?') for r in records),
                  'failure': failure, 'automatic_retry': False, 'setting_changes': 0, 'product_judgement': False}
        (OUT / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result), flush=True)
if failure:
    raise SystemExit(1)
