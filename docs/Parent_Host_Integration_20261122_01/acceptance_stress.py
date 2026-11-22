"""実機CDC中継の反復・ATE順序確認。異常で停止し自動再送しない。"""
import contextlib
import datetime
import json
from pathlib import Path
import statistics
import sys
import time

import serial

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.external_instrument_contract import decode_frame

OUT = Path(__file__).resolve().parent / (sys.argv[1] if len(sys.argv) > 1 else 'Acceptance_01')
EXPECTED = b'ADC Corp.,7355,246410099,  A02\r\n'


def main():
    OUT.mkdir(exist_ok=False)
    records, raw, host_lines = [], {k: bytearray() for k in ('ate', 'host', 'parent')}, bytearray()
    frames, failure = [], None
    start = time.monotonic()
    ports, monitor_errors = {}, {}
    with contextlib.ExitStack() as stack:
        for key, name, baud in [('ate', 'COM7', 57600), ('host', 'COM22', 115200), ('parent', 'COM6', 115200)]:
            port = serial.Serial(port=None, baudrate=baud, timeout=0, write_timeout=1)
            port.port, port.dtr, port.rts = name, False, False
            try:
                port.open()
            except serial.SerialException as exc:
                if key != 'parent':
                    raise
                # 保守USBの占有でATE/Host試験を妨げない。欠測は結果に明記する。
                monitor_errors[key] = str(exc)
                continue
            ports[key] = stack.enter_context(port)

        def poll():
            for key, port in ports.items():
                count = port.in_waiting
                if count:
                    data = port.read(count)
                    raw[key].extend(data)
                    if key == 'host':
                        host_lines.extend(data)
                        while b'\r\n' in host_lines:
                            line, _, rest = host_lines.partition(b'\r\n')
                            host_lines[:] = rest
                            if line:
                                frames.append(decode_frame(bytes(line) + b'\r\n'))

        try:
            # 入力を消去せず旧byteを保存し、要求前の不明なATE残留は拒否する。
            until = time.monotonic() + .3
            while time.monotonic() < until:
                poll()
                time.sleep(.002)
            if raw['ate']:
                raise RuntimeError('ATE residual data before test')
            for index in range(200):
                before = len(raw['ate'])
                began = time.monotonic()
                # 外部待機中にローカル照会を同一burstで送り、応答順序を確認する。
                command = b'EXT_QUERY 2000 *IDN?\rCOMM_STATUS?\r'
                ports['ate'].write(command)
                while time.monotonic() - began < 4:
                    poll()
                    response = bytes(raw['ate'][before:])
                    if response.count(b'\r') >= 2:
                        break
                    time.sleep(.001)
                replies = bytes(raw['ate'][before:]).split(b'\r')
                if len(replies) != 3 or replies[2]:
                    raise RuntimeError('ATE response count/boundary: ' + repr(replies))
                first = replies[0].split(b':')
                if first[:2] != [b'OK', b'EXT_RX'] or int(first[2]) != len(EXPECTED) or bytes.fromhex(first[3].decode()) != EXPECTED:
                    raise RuntimeError('IDN failed: ' + repr(replies[0]))
                if replies[1] != b'OK:state=IDLE':
                    raise RuntimeError('Local reply/order failed: ' + repr(replies[1]))
                records.append({'index': index + 1, 'elapsed_ms': round((time.monotonic() - began) * 1000, 3), 'replies': [s.decode() for s in replies[:2]]})
                if (index + 1) % 25 == 0:
                    print('COMPLETED=' + str(index + 1), flush=True)
            poll()
            reqs = {}
            for f in frames:
                if f['kind'] == 'h':
                    continue
                reqs.setdefault(f['request'], []).append(f)
            if len(reqs) != 200 or any([f['kind'] for f in v] != ['A', 'T', 'R'] for v in reqs.values()):
                raise RuntimeError('Host request/count/order mismatch')
            if len({f['session'] for f in frames}) != 1:
                raise RuntimeError('Unexpected Host session change')
        except Exception as exc:
            failure = repr(exc)
        finally:
            for key, data in raw.items():
                (OUT / (key + '.raw')).write_bytes(data)
            (OUT / 'requests.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
            times = [r['elapsed_ms'] for r in records]
            result = {'date_jst': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
                      'attempted': len(records) + (1 if failure else 0), 'completed': len(records), 'failure': failure,
                      'duration_seconds': round(time.monotonic() - start, 3), 'max_ms': max(times) if times else None,
                      'median_ms': statistics.median(times) if times else None, 'host_frames': len(frames),
                      'monitor_errors': monitor_errors,
                      'automatic_retry': False, 'nf55g_commands': 0, 'instrument_setting_commands': 0}
            (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(result, ensure_ascii=False), flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
