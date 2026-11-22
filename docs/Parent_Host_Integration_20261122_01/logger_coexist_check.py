"""実機SDログを有効にしてREAD・RTC・ATE順序と不正行後の継続を確認する。"""
import contextlib
import datetime
import json
from pathlib import Path
import re
import sys
import time
import serial

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.external_instrument_contract import decode_frame

NF_MODE = len(sys.argv) > 1 and sys.argv[1] == 'nf'
OUT = Path(__file__).resolve().parent / (sys.argv[2] if len(sys.argv) > 2 else 'NF_Coexist_01' if NF_MODE else 'Logger_Coexist_01')
OUT.mkdir(exist_ok=False)
READ_COUNT = int(sys.argv[3]) if len(sys.argv) > 3 else 50
READ_TIMEOUT_MS = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
if not 1 <= READ_COUNT <= 10000 or not 1 <= READ_TIMEOUT_MS <= 10000:
    raise ValueError('test count/timeout outside supported bounds')
raw = {k: bytearray() for k in ('ate', 'host')}
records, failure, recording = [], None, False
host_lines, host_frames = bytearray(), []
test_started = time.monotonic()
completed_reads = 0
with contextlib.ExitStack() as stack:
    ports = {}
    for key, name, baud in [('ate', 'COM7', 57600), ('host', 'COM22', 115200)]:
        p = serial.Serial(port=None, baudrate=baud, timeout=0, write_timeout=1)
        p.port, p.dtr, p.rts = name, False, False
        p.open()
        ports[key] = stack.enter_context(p)

    def exchange(command, count=1):
        start = len(raw['ate'])
        began = time.monotonic()
        ports['ate'].write(command)
        while time.monotonic() - began < max(5, READ_TIMEOUT_MS / 1000 + 3):
            for key, p in ports.items():
                if p.in_waiting:
                    data = p.read(p.in_waiting)
                    raw[key].extend(data)
                    if key == 'host':
                        host_lines.extend(data)
                        while b'\r\n' in host_lines:
                            line, _, rest = host_lines.partition(b'\r\n')
                            host_lines[:] = rest
                            if line:
                                frame = decode_frame(bytes(line) + b'\r\n')
                                host_frames.append({'seconds': time.monotonic() - test_started,
                                                    'request': frame['request'], 'kind': frame['kind'],
                                                    'session': frame['session'].hex(),
                                                    'payload_hex': frame['payload'].hex()})
            if raw['ate'][start:].count(13) >= count:
                break
            time.sleep(.001)
        data = bytes(raw['ate'][start:])
        records.append({'command_hex': command.hex(), 'reply': data.decode('ascii', 'backslashreplace'),
                        'elapsed_ms': (time.monotonic() - began) * 1000})
        parts = data.split(b'\r')
        if len(parts) != count + 1 or parts[-1]:
            raise RuntimeError('ATE count/boundary mismatch: ' + repr(data))
        return parts[:-1]

    def check_query(reply, expected=None):
        parts = reply.split(b':')
        if parts[:2] != [b'OK', b'EXT_RX']:
            raise RuntimeError('external response: ' + repr(reply))
        b = bytes.fromhex(parts[3].decode())
        if len(b) != int(parts[2]) or not b.endswith(b'\r\n') or (expected is not None and b != expected):
            raise RuntimeError('external boundary/content mismatch')
        return b
    try:
        if exchange(b'LOG_CONT_START\r') != [b'OK']:
            raise RuntimeError('logger start rejected')
        recording = True
        for bad, expected in ([] if NF_MODE else [(b'EXT_QUERY 0 *IDN?', b'ERR:EXT_TIMEOUT:AMBIGUOUS=0'),
                              (b'EXT_QUERY 2000 \x03*IDN?', b'ERR:FRAME'),
                              (b'EXT_QUERY 2000 \xff', b'ERR:ASCII'),
                              (b'X' * 513, b'ERR:LINE_TOO_LONG')]):
            replies = exchange(bad + b'\rEXT_QUERY 2000 *IDN?\r', 2)
            if replies[0] != expected:
                raise RuntimeError('unexpected parser error: ' + repr(replies[0]))
            check_query(replies[1], b'ADC Corp.,7355,246410099,  A02\r\n')
        for index in range(READ_COUNT):
            # NF55Gは既存D1読取りのみ。外部READ待ち中に受信した要求の順序も確認。
            command = (b'EXT_QUERY 2000 :READ?\rSTATUS_REFRESH\rRETRY_COUNT?\rSD_STATUS?\rRTC_CHECK?\rLOG_DROP_COUNT?\r'
                       if NF_MODE else b'EXT_QUERY 2000 :READ?\rSD_STATUS?\rRTC_CHECK?\rLOG_DROP_COUNT?\r')
            command = command.replace(b'EXT_QUERY 2000 ', ('EXT_QUERY ' + str(READ_TIMEOUT_MS) + ' ').encode())
            replies = exchange(command, 6 if NF_MODE else 4)
            value = check_query(replies[0])
            if not re.fullmatch(rb'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?\r\n', value):
                raise RuntimeError('single numeric measurement required')
            expected = [b'OK', b'OK:cmd=0,rsp=0', b'OK', b'OK', b'0'] if NF_MODE else [b'OK', b'OK', b'0']
            if replies[1:] != expected:
                raise RuntimeError('SD/RTC/drop failure: ' + repr(replies[1:]))
            completed_reads += 1
            if (index + 1) % 10 == 0:
                print('LOGGER_READ_OK=' + str(index + 1), flush=True)
    except Exception as exc:
        failure = repr(exc)
    finally:
        if recording:
            try:
                if exchange(b'LOG_CONT_STOP\r') != [b'OK']:
                    raise RuntimeError('logger stop rejected')
                if exchange(b'LOG_DROP_COUNT?\rSD_STATUS?\r', 2) != [b'0', b'OK']:
                    raise RuntimeError('final logger status')
            except Exception as exc:
                failure = (failure or '') + '; cleanup: ' + repr(exc)
        for key, b in raw.items():
            (OUT / (key + '.raw')).write_bytes(b)
        (OUT / 'requests.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
        (OUT / 'host_frames.json').write_text(json.dumps(host_frames, indent=2), encoding='utf-8')
        result = {'date_jst': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
                  'failure': failure, 'bursts': len(records), 'automatic_retry': False, 'setting_changes': 0,
                  'planned_reads': READ_COUNT, 'completed_reads': completed_reads, 'read_timeout_ms': READ_TIMEOUT_MS,
                  'nf55g_read_only_d1_requested': NF_MODE, 'sd_log_recording_requested': recording}
        (OUT / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result), flush=True)
if failure:
    raise SystemExit(1)
