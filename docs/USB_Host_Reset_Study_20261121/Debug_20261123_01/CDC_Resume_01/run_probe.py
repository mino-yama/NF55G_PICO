"""INFOでREADY確認後に明示IDNを一回だけ送る。RESET・再送・設定なし。"""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
import serial

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT))
from src.external_instrument_link import FrameReader


if __name__ == '__main__':
    assert not (OUT / 'result.json').exists(), 'result exists'
    captured = bytearray()
    stop = threading.Event()
    result = {'status': 'INCOMPLETE', 'events': []}
    process = None
    with serial.Serial('COM22', 115200, timeout=0.05) as host, serial.Serial('COM7', 57600, timeout=0.05) as ate:
        def capture():
            while not stop.is_set():
                captured.extend(host.read(4096))
        thread = threading.Thread(target=capture)
        thread.start()
        try:
            with (OUT / 'parent.log').open('wb') as log:
                process = subprocess.Popen([str(ROOT / '.venv/Scripts/python.exe'), '-u', '-m', 'mpremote',
                    'connect', 'COM6', 'resume', 'run', str(OUT / 'parent_probe.py')],
                    cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                deadline = time.monotonic() + 10
                while b'CDC_PROBE_READY|' not in (OUT / 'parent.log').read_bytes():
                    assert process.poll() is None, 'parent exited before READY'
                    assert time.monotonic() < deadline, 'parent READY timeout'
                    time.sleep(0.05)
                result['preexisting_ate_hex'] = ate.read(4096).hex()

                def request(command):
                    ate.write(command.encode('ascii') + b'\r\n')
                    ate.flush()
                    raw = bytearray()
                    deadline = time.monotonic() + 4
                    while time.monotonic() < deadline:
                        raw.extend(ate.read(4096))
                        if raw.endswith((b'\r', b'\n')):
                            break
                    response = raw.decode('ascii').strip()
                    result['events'].append({'command': command, 'response': response, 'raw_hex': raw.hex()})
                    print(command, response, flush=True)
                    return response

                info = request('HOST_INFO? METER')
                assert info.startswith('OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261123.2:'), info
                if info.endswith(':READY'):
                    response = request('EXT_QUERY 2000 *IDN?')
                    result['status'] = 'QUERY_FAILED'
                    if response.startswith('OK:EXT_RX:'):
                        _, _, count, encoded = response.split(':', 3)
                        raw = bytes.fromhex(encoded)
                        assert int(count) == len(raw)
                        result['instrument_raw_hex'] = raw.hex()
                        result['instrument_text'] = raw.decode('ascii')
                        assert raw == b'ADC Corp.,7355,246410099,  A02\r\n', repr(raw)
                        result['status'] = 'IDN_SUCCESS'
                else:
                    result['status'] = 'HOST_NOT_READY_NO_QUERY'
                process.wait(timeout=20)
                assert process.returncode == 0
                parent = (OUT / 'parent.log').read_text(encoding='utf-8')
                result['parent'] = json.loads(next(line.split('|', 1)[1] for line in parent.splitlines() if line.startswith('CDC_PROBE_DONE|')))
                reader = FrameReader()
                sent = reader.feed(bytes.fromhex(result['parent']['tx_hex']))
                result['sent_kinds'] = [frame['kind'] for frame in sent]
                assert reader.errors == 0
                assert sum(frame['kind'] == 'Q' for frame in sent) <= 1
                assert not any(frame['kind'] == 'S' for frame in sent)
                assert 'CDC_PROBE_STOPPED_PIO_INPUT' in parent
        except Exception as exc:
            result['error'] = repr(exc)
            if process is not None and process.poll() is None:
                process.wait(timeout=25)
            raise
        finally:
            stop.set()
            thread.join(timeout=2)
            (OUT / 'host.raw').write_bytes(captured)
            reader = FrameReader()
            frames = reader.feed(captured)
            result['host_frames'] = [{'kind': f['kind'], 'request': f['request'],
                'session': f['session'].hex(), 'payload_hex': f['payload'].hex(),
                'payload_text': f['payload'].decode('ascii', 'replace')} for f in frames]
            result['host_decode_errors'] = reader.errors
            (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
