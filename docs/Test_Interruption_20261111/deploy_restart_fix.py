"""既存治具への4ファイル配置。全退避とSHA-256照合後に通常起動する。"""
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import time
import serial
from mpremote.transport_serial import SerialTransport

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / ('deployment_' + datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M%S'))
TARGETS = ('src/logger.py', 'src/sd_sink.py', 'src/command_dispatcher.py', 'src/main.py')


def main():
    OUT.mkdir()
    evidence = {'preflight': [], 'files': [], 'deployed': False}
    def save():
        (OUT / 'deployment.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    with serial.Serial('COM20', 115200, timeout=2, write_timeout=2) as port:
        for cmd in ('*IDN?', 'COMM_STATUS?', 'TEST_END', 'SD_STATUS?', 'PICO_SELF_CHECK?', 'LOG_DROP_COUNT?'):
            time.sleep(0.15)
            port.write((cmd + '\r\n').encode())
            raw = port.read_until(b'\n')
            answer = raw.decode('ascii').strip()
            evidence['preflight'].append({'command': cmd, 'response': answer})
            save()
            print(cmd, '=>', answer, flush=True)
            if not raw.endswith(b'\n'):
                raise RuntimeError('Preflight timeout')
            if cmd == '*IDN?' and not answer.startswith('NF55G_PICO_FIXTURE,'):
                raise RuntimeError('Fixture ID mismatch')
            if cmd == 'COMM_STATUS?' and answer != 'OK:state=IDLE':
                raise RuntimeError('Communication is not IDLE')
            if cmd == 'TEST_END' and answer != 'OK':
                raise RuntimeError('Cannot finish recording')
            if cmd == 'SD_STATUS?' and answer != 'OK':
                raise RuntimeError('SD not ready')
            if cmd == 'PICO_SELF_CHECK?' and not answer.startswith('OK:'):
                raise RuntimeError('Self check not ready')
    repl = SerialTransport('COM6', wait=2)
    backups = {}
    changed = []
    try:
        repl.enter_raw_repl(soft_reset=False)
        uid = repl.eval("__import__('binascii').hexlify(__import__('machine').unique_id()).decode()")
        evidence['unique_id'] = uid
        assert uid == '69f7d45962cfdfad', 'Wrong Pico'
        names = repl.eval("__import__('os').listdir('/src')")
        paths = ['main.py'] + ['src/' + name for name in names if name.endswith('.py')]
        if 'boot.py' in repl.eval("__import__('os').listdir('/')"):
            paths.append('boot.py')
        for name in paths:
            data = bytes(repl.fs_readfile('/' + name))
            backup = OUT / 'backup' / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(data)
            backups[name] = data
            row = {'path': name, 'before_sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}
            if (ROOT / name).exists():
                row['workspace_sha256'] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            evidence['files'].append(row)
        save()
        assert all(name in backups for name in TARGETS), 'Missing deployed target'
        print('Backup complete:', len(backups), 'files', flush=True)
        for name in TARGETS:
            data = (ROOT / name).read_bytes()
            changed.append(name)
            repl.fs_writefile('/' + name, data)
            digest = repl.eval("__import__('binascii').hexlify(__import__('hashlib').sha256(open('/" + name + "','rb').read()).digest()).decode()")
            expected = hashlib.sha256(data).hexdigest()
            assert digest == expected, 'Deployment hash mismatch: ' + name
            next(row for row in evidence['files'] if row['path'] == name)['after_sha256'] = digest
            save()
            print('Verified:', name, digest, flush=True)
        evidence['deployed'] = True
    except Exception as exc:
        evidence['error'] = repr(exc)
        for name in changed:
            repl.fs_writefile('/' + name, backups[name])
        evidence['restored_after_failure'] = list(changed)
        raise
    finally:
        save()
        repl.exit_raw_repl()
        repl.serial.write(b'\x04')
        time.sleep(2)
        repl.close()
        print('Evidence:', OUT, flush=True)


if __name__ == '__main__':
    main()
