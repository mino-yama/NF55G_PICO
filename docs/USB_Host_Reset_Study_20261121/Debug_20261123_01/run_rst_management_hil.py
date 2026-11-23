"""実ATE入口からINFO/RESET/INFOを各1回。機器向け要求・自動再送なし。"""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
import serial

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
from src.external_instrument_link import FrameReader


if __name__ == '__main__':
    assert not (OUT / 'hil_result.json').exists(), 'result exists; use a new run folder'
    stop = threading.Event()
    captured = bytearray()
    events = []
    result = {'status': 'INCOMPLETE', 'events': events}
    with serial.Serial('COM22', 115200, timeout=0.05) as host, serial.Serial('COM7', 57600, timeout=0.05) as ate:
        def capture():
            while not stop.is_set():
                captured.extend(host.read(4096))
        thread = threading.Thread(target=capture)
        thread.start()
        process = None
        try:
            with (OUT / 'hil_parent.log').open('wb') as log:
                process = subprocess.Popen([str(ROOT / '.venv/Scripts/python.exe'), '-u', '-m',
                    'mpremote', 'connect', 'COM6', 'resume', 'run',
                    str(OUT / 'rst_management_hil_parent.py')], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                deadline = time.monotonic() + 12
                while b'RST_HIL_READY|' not in (OUT / 'hil_parent.log').read_bytes():
                    assert process.poll() is None, 'parent HIL exited before READY'
                    assert time.monotonic() < deadline, 'parent READY timeout'
                    time.sleep(0.05)
                preexisting = ate.read(4096)
                events.append({'preexisting_ate_hex': preexisting.hex()})

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
                    events.append({'command': command, 'raw_hex': raw.hex(), 'response': response})
                    print(command, response, flush=True)
                    return response

                info = request('HOST_INFO? METER')
                prefix = 'OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261123.2:'
                assert info.startswith(prefix), info
                old_nonce = info.split(':')[-2]
                accepted = request('HOST_RESET METER')
                assert accepted == 'OK:HOST_RESET_ACCEPTED:BFCF2EDB84B0B37F:' + old_nonce, accepted
                # 明示再起動後のUART立上り待ち。RSTを再送しない。
                time.sleep(3)
                done = request('HOST_INFO? METER')
                assert done.startswith('OK:HOST_RESET_DONE:BFCF2EDB84B0B37F:' + old_nonce + ':'), done
                assert done.split(':')[-2] != old_nonce
                process.wait(timeout=25)
                assert process.returncode == 0
                parent = (OUT / 'hil_parent.log').read_text(encoding='utf-8')
                assert 'RST_HIL_DONE|' in parent and 'RST_HIL_STOPPED_PIO_INPUT' in parent
                diagnostics = json.loads(next(line.split('|', 1)[1] for line in parent.splitlines() if line.startswith('RST_HIL_DONE|')))
                assert diagnostics['nf_write_attempts'] == 0 and diagnostics['cache_unchanged']
                assert diagnostics['frame_errors'] == 0
                result.update({'status': 'PASS', 'parent': diagnostics})
        except Exception as exc:
            result['error'] = repr(exc)
            if process is not None and process.poll() is None:
                # 有限18秒の親試験がfinallyでPIOを閉じるまで待つ。
                process.wait(timeout=30)
            raise
        finally:
            stop.set()
            thread.join(timeout=2)
            (OUT / 'hil_host.raw').write_bytes(captured)
            reader = FrameReader()
            frames = reader.feed(captured)
            result['passive_host_frames'] = [{'kind': f['kind'], 'request': f['request'],
                'session': f['session'].hex(), 'payload_hex': f['payload'].hex()} for f in frames]
            result['passive_decode_errors'] = reader.errors
            (OUT / 'hil_result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
