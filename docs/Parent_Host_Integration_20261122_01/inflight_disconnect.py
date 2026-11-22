"""連続IDNまたは現設定でのREAD中に手動抜線し、最初の異常で停止する。

READは先行IDNと機能/設定照合後にだけ選択する。再送・設定変更は行わない。
"""
import contextlib
import datetime
import json
from pathlib import Path
import sys
import time
import serial

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.external_instrument_contract import decode_frame

DELAYED = len(sys.argv) > 1 and sys.argv[1] == 'delayed'
READ_MODE = len(sys.argv) > 1 and sys.argv[1] in ('read', 'delayed')
BODY = b':READ?' if READ_MODE else b'*IDN?'
OUT = Path(__file__).resolve().parent / ('InFlight_Disconnect_Delayed_01' if DELAYED else 'InFlight_Disconnect_READ_01' if READ_MODE else 'InFlight_Disconnect_01')
OUT.mkdir(exist_ok=False)
raw = {k: bytearray() for k in ('ate', 'host')}
lines, frames, requests = bytearray(), [], []
failure = None
with contextlib.ExitStack() as stack:
    ports = {}
    for key, name, baud in [('ate', 'COM7', 57600), ('host', 'COM22', 115200)]:
        p = serial.Serial(port=None, baudrate=baud, timeout=0, write_timeout=1)
        p.port, p.dtr, p.rts = name, False, False
        p.open()
        ports[key] = stack.enter_context(p)

    def poll():
        for key, p in ports.items():
            n = p.in_waiting
            if n:
                b = p.read(n)
                raw[key].extend(b)
                if key == 'host':
                    lines.extend(b)
                    while b'\r\n' in lines:
                        line, _, rest = lines.partition(b'\r\n')
                        lines[:] = rest
                        if line:
                            frames.append(decode_frame(bytes(line) + b'\r\n'))
    try:
        print('DISCONNECT_WINDOW_STARTED: ' + BODY.decode() + ', stop at first failure', flush=True)
        started = time.monotonic()
        while time.monotonic() - started < 120 and len(requests) < 2000:
            before = len(raw['ate'])
            sent_at = time.monotonic()
            ports['ate'].write((b'EXT_QUERY 10000 ' if DELAYED else b'EXT_QUERY 2000 ') + BODY + b'\r')
            while time.monotonic() - sent_at < (12 if DELAYED else 4):
                poll()
                if b'\r' in raw['ate'][before:]:
                    break
                time.sleep(.001)
            reply = bytes(raw['ate'][before:])
            requests.append({'index': len(requests) + 1, 'seconds': time.monotonic() - started,
                             'reply': reply.decode('ascii', 'backslashreplace')})
            if not reply.startswith(b'OK:EXT_RX:'):
                failure = reply.decode('ascii', 'backslashreplace')
                break
            if len(requests) % 25 == 0:
                print('QUERY_OK=' + str(len(requests)), flush=True)
        until = time.monotonic() + .2
        while time.monotonic() < until:
            poll()
            time.sleep(.002)
    except Exception as exc:
        failure = repr(exc)
    finally:
        for key, value in raw.items():
            (OUT / (key + '.raw')).write_bytes(value)
        (OUT / 'requests.json').write_text(json.dumps(requests, indent=2), encoding='utf-8')
        events = [f for f in frames if f['kind'] == 'E']
        result = {'date_jst': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
                  'body': BODY.decode(), 'requests': len(requests), 'stop_reply': failure, 'automatic_retry': False,
                  'last_host_events': [{'request': f['request'], 'kind': f['kind'], 'payload_hex': f['payload'].hex(),
                                        'session': f['session'].hex()} for f in frames[-6:]],
                  'inflight_disconnect_observed': any(f['payload'] == b'DISCONNECTED|1' for f in events)}
        (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False), flush=True)
