"""切断試験用のトリガ遅延を保存・設定・読戻しし、別工程で復元する。"""
import contextlib
import datetime
from decimal import Decimal
import json
from pathlib import Path
import sys
import time
import serial

BASE = Path(__file__).resolve().parent
PHASE = sys.argv[1]
if PHASE not in ('arm', 'restore'):
    raise ValueError(PHASE)
OUT = BASE / ('Trigger_Delay_' + PHASE)
OUT.mkdir(exist_ok=False)
STATE = BASE / 'trigger_delay_original.json'
records, raw, failure = [], {k: bytearray() for k in ('ate', 'host')}, None
with contextlib.ExitStack() as stack:
    ports = {}
    for key, name, baud in [('ate', 'COM7', 57600), ('host', 'COM22', 115200)]:
        p = serial.Serial(port=None, baudrate=baud, timeout=0, write_timeout=1)
        p.port, p.dtr, p.rts = name, False, False
        p.open()
        ports[key] = stack.enter_context(p)
    def request(command):
        start = len(raw['ate'])
        began = time.monotonic()
        ports['ate'].write(command.encode('ascii') + b'\r')
        while time.monotonic() - began < 4:
            for key, p in ports.items():
                if p.in_waiting:
                    raw[key].extend(p.read(p.in_waiting))
            if b'\r' in raw['ate'][start:]:
                break
            time.sleep(.001)
        reply = bytes(raw['ate'][start:]).decode('ascii')
        row = {'command': command, 'reply': reply, 'elapsed_ms': (time.monotonic() - began) * 1000}
        records.append(row)
        print(json.dumps(row), flush=True)
        if command.startswith('EXT_QUERY'):
            parts = reply.rstrip('\r').split(':')
            if parts[:2] != ['OK', 'EXT_RX']:
                raise RuntimeError(reply)
            value = bytes.fromhex(parts[3])
            if len(value) != int(parts[2]) or not value.endswith(b'\r\n'):
                raise RuntimeError('response frame')
            return value.decode('ascii').strip()
        if reply != 'OK:EXT_TX\r':
            raise RuntimeError(reply)
    try:
        identity = request('EXT_QUERY 2000 *IDN?')
        if identity != 'ADC Corp.,7355,246410099,  A02':
            raise RuntimeError('instrument identity mismatch')
        if PHASE == 'arm':
            original = request('EXT_QUERY 2000 :TRIG:DEL?')
            if not Decimal(original).is_finite():
                raise RuntimeError('non-finite delay')
            state = {'original': original, 'instrument': identity, 'temporary_seconds': '5', 'restored': False,
                     'date_jst': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()}
            with STATE.open('x', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            request('EXT_SEND 2000 :TRIG:DEL 5')
            if Decimal(request('EXT_QUERY 2000 :TRIG:DEL?')) != Decimal('5'):
                raise RuntimeError('temporary delay not confirmed')
        else:
            state = json.loads(STATE.read_text(encoding='utf-8'))
            request('EXT_SEND 2000 :TRIG:DEL ' + state['original'])
            restored = request('EXT_QUERY 2000 :TRIG:DEL?')
            if Decimal(restored) != Decimal(state['original']):
                raise RuntimeError('restore mismatch')
            state['restored'] = True
            state['restored_raw'] = restored
            STATE.write_text(json.dumps(state, indent=2), encoding='utf-8')
    except Exception as exc:
        failure = repr(exc)
    finally:
        for key, b in raw.items():
            (OUT / (key + '.raw')).write_bytes(b)
        result = {'phase': PHASE, 'failure': failure, 'records': records, 'automatic_retry': False}
        (OUT / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({'phase': PHASE, 'failure': failure}), flush=True)
if failure:
    raise SystemExit(1)
