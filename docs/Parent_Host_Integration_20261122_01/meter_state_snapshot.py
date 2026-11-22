"""READ期限比較前に実機のトリガ条件とエラーを原文保存する。設定は変更しない。"""
import contextlib
from decimal import Decimal
import json
from pathlib import Path
import time
import serial

OUT = Path(__file__).resolve().parent / 'Read_Deadline_State_01'
OUT.mkdir(exist_ok=False)
queries = ['*IDN?', ':INIT:CONT?', ':TRIG:SOUR?', ':TRIG:COUN?', ':SAMP:COUN?',
           ':TRIG:DEL?', ':SENS:FUNC?', ':SYST:ERR?']
raw = {k: bytearray() for k in ('ate', 'host')}
records, values, failure = [], {}, None
with contextlib.ExitStack() as stack:
    ports = {}
    for key, name, baud in [('ate', 'COM7', 57600), ('host', 'COM22', 115200)]:
        p = serial.Serial(port=None, baudrate=baud, timeout=0, write_timeout=1)
        p.port, p.dtr, p.rts = name, False, False
        p.open()
        ports[key] = stack.enter_context(p)
    try:
        for query in queries:
            before = len(raw['ate'])
            began = time.monotonic()
            ports['ate'].write(('EXT_QUERY 2000 ' + query + '\r').encode('ascii'))
            while time.monotonic() - began < 4:
                for key, p in ports.items():
                    if p.in_waiting:
                        raw[key].extend(p.read(p.in_waiting))
                if b'\r' in raw['ate'][before:]:
                    break
                time.sleep(.001)
            reply = bytes(raw['ate'][before:])
            row = {'query': query, 'reply': reply.decode('ascii', 'backslashreplace')}
            records.append(row)
            parts = reply.rstrip(b'\r').split(b':')
            if parts[:2] != [b'OK', b'EXT_RX']:
                raise RuntimeError('state query failed: ' + repr(reply))
            b = bytes.fromhex(parts[3].decode())
            if len(b) != int(parts[2]) or not b.endswith(b'\r\n'):
                raise RuntimeError('state response boundary')
            values[query] = b.decode('ascii').strip()
            print(query + '=' + values[query], flush=True)
        if values['*IDN?'] != 'ADC Corp.,7355,246410099,  A02':
            raise RuntimeError('instrument identity differs')
        if Decimal(values[':SYST:ERR?'].split(',', 1)[0]) != 0:
            raise RuntimeError('instrument error recorded; stop before further READ')
        if (Decimal(values[':INIT:CONT?']) != 0 or values[':TRIG:SOUR?'] != 'IMM' or
                Decimal(values[':TRIG:COUN?']) != 1 or Decimal(values[':SAMP:COUN?']) != 1 or
                Decimal(values[':TRIG:DEL?']) != 0 or values[':SENS:FUNC?'].strip('"') != 'VOLT:DC'):
            raise RuntimeError('READ conditions differ; do not silently adjust settings')
    except Exception as exc:
        failure = repr(exc)
    finally:
        for key, data in raw.items():
            (OUT / (key + '.raw')).write_bytes(data)
        result = {'values': values, 'records': records, 'failure': failure, 'setting_changes': 0,
                  'automatic_retry': False, 'system_error_queue_read_once': ':SYST:ERR?' in values}
        (OUT / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({'failure': failure}), flush=True)
if failure:
    raise SystemExit(1)
