"""D1単独確認後、既存のREAD/D1/SD/RTC50burstを実行。設定・リトライなし。"""
import json
from pathlib import Path
import subprocess
import time
import serial

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
PY = ROOT / '.venv/Scripts/python.exe'


if __name__ == '__main__':
    assert not (OUT / 'result.json').exists()
    result = {'status': 'INCOMPLETE', 'precheck': []}
    with (OUT / 'parent.log').open('wb') as parent_log:
        parent = subprocess.Popen([str(PY), '-u', '-m', 'mpremote', 'connect', 'COM6', 'resume',
            'run', str(OUT / 'parent_coexist.py')], cwd=ROOT, stdout=parent_log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 10
            while b'COEXIST_READY|' not in (OUT / 'parent.log').read_bytes():
                assert parent.poll() is None, 'parent exited before READY'
                assert time.monotonic() < deadline, 'parent READY timeout'
                time.sleep(0.05)
            with serial.Serial('COM7', 57600, timeout=0.02) as ate:
                assert not ate.read(4096), 'preexisting ATE response'
                for command, expected in [('HOST_INFO? METER', 'OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261123.2:CBFA8C2C4F42C7BA:READY'),
                    ('SD_STATUS?', 'OK'), ('RTC_CHECK?', 'OK'), ('LOG_DROP_COUNT?', '0'),
                    ('STATUS_REFRESH', 'OK'), ('RETRY_COUNT?', 'OK:cmd=0,rsp=0')]:
                    ate.write(command.encode('ascii') + b'\r')
                    raw = bytearray()
                    deadline = time.monotonic() + 4
                    while time.monotonic() < deadline:
                        raw.extend(ate.read(4096))
                        if raw.endswith(b'\r'):
                            break
                    reply = raw.decode('ascii').strip()
                    result['precheck'].append({'command': command, 'response': reply, 'raw_hex': raw.hex()})
                    print(command, reply, flush=True)
                    assert reply == expected, (command, reply)
            with (OUT / 'burst_execution.log').open('wb') as burst_log:
                run = subprocess.run([str(PY), '-u', '-B', str(ROOT / 'docs/Parent_Host_Integration_20261122_01/logger_coexist_check.py'),
                    'nf', str(OUT / 'Burst_01'), '50', '2000'], cwd=ROOT, stdout=burst_log, stderr=subprocess.STDOUT, timeout=95)
            result['burst_exit_code'] = run.returncode
            assert run.returncode == 0, 'burst failed; inspect burst logs; no retry'
            result['burst'] = json.loads((OUT / 'Burst_01/result.json').read_text())
            assert result['burst']['completed_reads'] == 50 and not result['burst']['failure']
            result['status'] = 'COEXIST50_SUCCESS'
        except Exception as exc:
            result['status'] = 'STOPPED'
            result['error'] = repr(exc)
            print('STOPPED', repr(exc), flush=True)
        finally:
            parent.wait(timeout=125)
            result['parent_exit_code'] = parent.returncode
            parent_text = (OUT / 'parent.log').read_text(encoding='utf-8')
            try:
                result['parent'] = json.loads(next(line.split('|', 1)[1] for line in parent_text.splitlines() if line.startswith('COEXIST_DONE|')))
                assert parent.returncode == 0 and 'COEXIST_STOPPED_PIO_INPUT_NF_GUARD_RESTORED' in parent_text
                assert not result['parent']['logger_active'] and result['parent']['queue'] == 0
                assert result['parent']['drop'] == 0 and result['parent']['sd_stats']['during_comm'] == 0
                if result['status'] == 'COEXIST50_SUCCESS':
                    assert result['parent']['nf_d1_count'] == 51 and result['parent']['nf_rejected'] == 0
            except Exception as exc:
                result['status'] = 'STOPPED'
                result['cleanup_error'] = repr(exc)
            (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            print('RESULT', result['status'], flush=True)
    if result['status'] != 'COEXIST50_SUCCESS':
        raise SystemExit(1)
