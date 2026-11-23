"""設定読戻し、既存AUTO ONの明示確認、単発READ10回。異常後は再送しない。"""
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import serial

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT))
from src.external_instrument_link import FrameReader


if __name__ == '__main__':
    assert not (OUT / 'result.json').exists(), 'result exists'
    result = {'status': 'INCOMPLETE', 'events': [], 'before': {}, 'after': {}, 'reads': [],
              'planned_reads': 10, 'automatic_retry': False, 'setting_commands': []}
    captured = bytearray()
    stop = threading.Event()
    process = None
    with serial.Serial('COM22', 115200, timeout=0.02) as host, serial.Serial('COM7', 57600, timeout=0.02) as ate:
        def capture():
            while not stop.is_set():
                captured.extend(host.read(4096))
        thread = threading.Thread(target=capture)
        thread.start()
        try:
            with (OUT / 'parent.log').open('wb') as log:
                process = subprocess.Popen([str(ROOT / '.venv/Scripts/python.exe'), '-u', '-m', 'mpremote',
                    'connect', 'COM6', 'resume', 'run', str(OUT / 'parent_probe.py')], cwd=ROOT,
                    stdout=log, stderr=subprocess.STDOUT)
                deadline = time.monotonic() + 10
                while b'CDC_PROBE_READY|' not in (OUT / 'parent.log').read_bytes():
                    assert process.poll() is None, 'parent exited before READY'
                    assert time.monotonic() < deadline, 'parent READY timeout'
                    time.sleep(0.05)
                result['preexisting_ate_hex'] = ate.read(4096).hex()
                assert not result['preexisting_ate_hex'], 'preexisting ATE output'

                def request(command):
                    began = time.monotonic()
                    ate.write(command.encode('ascii') + b'\r\n')
                    ate.flush()
                    raw = bytearray()
                    while time.monotonic() - began < 4:
                        raw.extend(ate.read(4096))
                        if raw.endswith((b'\r', b'\n')):
                            break
                    reply = raw.decode('ascii').strip()
                    row = {'command': command, 'response': reply, 'raw_hex': raw.hex(),
                           'elapsed_ms': round((time.monotonic() - began) * 1000, 3)}
                    result['events'].append(row)
                    if not reply.startswith('OK:'):
                        raise RuntimeError('request failed; no retry: ' + reply)
                    return row

                def query(command):
                    row = request('EXT_QUERY 2000 ' + command)
                    parts = row['response'].split(':', 3)
                    assert parts[:2] == ['OK', 'EXT_RX'], row
                    raw = bytes.fromhex(parts[3])
                    assert len(raw) == int(parts[2]) and raw.endswith(b'\r\n'), row
                    row['instrument_raw_hex'] = raw.hex()
                    row['instrument_text'] = raw.decode('ascii')
                    return raw.decode('ascii').strip(), row

                info = request('HOST_INFO? METER')['response']
                assert info == 'OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261123.2:CBFA8C2C4F42C7BA:READY', info
                queries = ['*IDN?', ':SENS:FUNC?', ':CONF?', ':SENS:VOLT:DC:RANG:AUTO?',
                           ':INIT:CONT?', ':TRIG:SOUR?', ':TRIG:COUN?', ':SAMP:COUN?', ':TRIG:DEL?', ':SYST:ERR?']
                for command in queries:
                    result['before'][command] = query(command)[0]
                before = result['before']
                print('SETTINGS_BEFORE', json.dumps(before), flush=True)
                assert before['*IDN?'] == 'ADC Corp.,7355,246410099,  A02'
                assert before[':SENS:FUNC?'].strip('"') == 'VOLT:DC'
                assert Decimal(before[':SYST:ERR?'].split(',', 1)[0]) == 0
                assert Decimal(before[':INIT:CONT?']) == 0
                assert before[':TRIG:SOUR?'] == 'IMM'
                assert Decimal(before[':TRIG:COUN?']) == 1 and Decimal(before[':SAMP:COUN?']) == 1
                assert Decimal(before[':TRIG:DEL?']) == 0
                assert Decimal(before[':SENS:VOLT:DC:RANG:AUTO?']) == 1, 'fixed range requires explicit ATE test condition'
                setting = 'EXT_SEND 2000 :SENS:VOLT:DC:RANG:AUTO ON'
                result['setting_commands'].append(setting)
                assert request(setting)['response'] == 'OK:EXT_TX'
                result['after'][':SENS:VOLT:DC:RANG:AUTO?'] = query(':SENS:VOLT:DC:RANG:AUTO?')[0]
                result['after'][':CONF?'] = query(':CONF?')[0]
                assert Decimal(result['after'][':SENS:VOLT:DC:RANG:AUTO?']) == 1
                for index in range(10):
                    text, row = query(':READ?')
                    assert re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?', text), text
                    number = Decimal(text)
                    assert number.is_finite()
                    result['reads'].append({'index': index + 1, 'text': text, 'elapsed_ms': row['elapsed_ms']})
                    print('READ', index + 1, text, row['elapsed_ms'], flush=True)
                for command in (':SENS:VOLT:DC:RANG:AUTO?', ':INIT:CONT?', ':TRIG:SOUR?',
                                ':TRIG:COUN?', ':SAMP:COUN?', ':TRIG:DEL?', ':SYST:ERR?'):
                    result['after'][command] = query(command)[0]
                for command in (':SENS:VOLT:DC:RANG:AUTO?', ':INIT:CONT?', ':TRIG:COUN?', ':SAMP:COUN?', ':TRIG:DEL?'):
                    assert Decimal(result['after'][command]) == Decimal(before[command]), command
                assert result['after'][':TRIG:SOUR?'] == before[':TRIG:SOUR?']
                assert Decimal(result['after'][':SYST:ERR?'].split(',', 1)[0]) == 0
                result['status'] = 'READ10_SUCCESS'
        except Exception as exc:
            result['error'] = repr(exc)
            result['status'] = 'STOPPED'
            print('STOPPED', repr(exc), flush=True)
        finally:
            if process is not None:
                try:
                    process.wait(timeout=45)
                    result['parent_exit_code'] = process.returncode
                    parent = (OUT / 'parent.log').read_text(encoding='utf-8-sig')
                    result['parent'] = json.loads(next(line.split('|', 1)[1] for line in parent.splitlines() if line.startswith('CDC_PROBE_DONE|')))
                    assert process.returncode == 0 and 'CDC_PROBE_STOPPED_PIO_INPUT' in parent
                    assert result['parent']['nf_write_attempts'] == 0 and result['parent']['cache_unchanged']
                    reader = FrameReader()
                    sent = reader.feed(bytes.fromhex(result['parent']['tx_hex']))
                    result['sent_frames'] = [{'kind': f['kind'], 'request': f['request'], 'session': f['session'].hex(),
                        'payload_text': f['payload'].decode('ascii')} for f in sent]
                    assert not any(f['kind'] == 'S' for f in sent)
                    assert reader.errors == 0
                except Exception as exc:
                    result['cleanup_error'] = repr(exc)
                    result['status'] = 'STOPPED'
            stop.set()
            thread.join(timeout=2)
            (OUT / 'host.raw').write_bytes(captured)
            reader = FrameReader()
            frames = reader.feed(captured)
            result['host_frames'] = [{'kind': f['kind'], 'request': f['request'], 'session': f['session'].hex(),
                'payload_text': f['payload'].decode('ascii', 'replace')} for f in frames]
            result['host_decode_errors'] = reader.errors
            (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            print('RESULT', result['status'], 'READS', len(result['reads']), flush=True)
    if result['status'] != 'READ10_SUCCESS':
        raise SystemExit(1)
