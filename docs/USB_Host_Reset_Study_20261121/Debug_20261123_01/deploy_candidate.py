"""個体・全Flash・source hashを照合してRST候補を配置。自動再試行なし。"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PY = ROOT / '.venv/Scripts/python.exe'
PICO = ROOT / 'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
MAN = json.loads((OUT / ('package_manifest_v2.json' if (OUT / 'package_manifest_v2.json').exists() else 'package_manifest.json')).read_text())
BASE = [PY, '-m', 'mpremote', 'connect', 'COM6', 'resume']
OPS = OUT / 'deployment_operations.jsonl'


def run(args, timeout=40, disconnect=False):
    try:
        result = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, timeout=timeout)
        row = {'args': [str(x) for x in args], 'code': result.returncode,
               'stdout': result.stdout.decode('utf-8', 'replace'),
               'stderr': result.stderr.decode('utf-8', 'replace')}
    except subprocess.TimeoutExpired as exc:
        row = {'args': [str(x) for x in args], 'code': 'timeout',
               'stdout': (exc.stdout or b'').decode('utf-8', 'replace'), 'stderr': str(exc)}
    with OPS.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(json.dumps(row, ensure_ascii=False), flush=True)
    if row['code'] != 0 and not disconnect:
        raise RuntimeError('operation failed; no retry')
    return row['stdout']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flash_backup(uid, name, size):
    info = run([PICO, 'info', '-a', '--ser', uid.upper()])
    assert uid.lower() in info.lower() and 'bootsel' in info.lower()
    target = OUT / (name + '_flash_before.bin')
    assert not target.exists(), 'backup already exists'
    run([PICO, 'save', '-a', '-v', target, '--ser', uid.upper()], timeout=90)
    assert target.stat().st_size == size
    record = {'uid': uid, 'bytes': size, 'sha256': sha(target), 'verified': True}
    (OUT / (name + '_flash_backup.json')).write_text(json.dumps(record, indent=2))


def probe_sources(expected):
    code = "import machine,binascii,hashlib,json; assert binascii.hexlify(machine.unique_id()).decode()=='" + MAN['parent_uid'] + "'; result={}\n"
    for path, digest in expected.items():
        code += "b=open(" + repr(path) + ",'rb').read(); h=binascii.hexlify(hashlib.sha256(b).digest()).decode(); assert h==" + repr(digest) + "; result[" + repr(path) + "]=h\n"
    code += "print('PARENT_HASHES_OK|'+json.dumps(result))"
    run(BASE + ['exec', code])


if __name__ == '__main__':
    phase = sys.argv[1]
    if phase == 'host-install':
        uf2 = OUT / 'candidate/usb_submcu_external_meter_relay.uf2'
        assert sha(uf2) == MAN['host_uf2_sha256']
        flash_backup(MAN['host_uid'], 'host', 2 * 1024 * 1024)
        run([PICO, 'load', '-v', uf2, '--ser', MAN['host_uid']], timeout=90)
        run([PICO, 'verify', uf2, '--ser', MAN['host_uid']], timeout=90)
        info = run([PICO, 'info', '-a', '--ser', MAN['host_uid']])
        assert 'meter-host-relay-20261123.1' in info
        print('HOST_INSTALLED_VERIFIED_LEFT_IN_BOOTSEL')
    elif phase == 'host-update':
        record = json.loads((OUT / 'host_flash_backup.json').read_text())
        assert sha(OUT / 'host_flash_before.bin') == record['sha256']
        uf2 = OUT / 'candidate/usb_submcu_external_meter_relay_v2.uf2'
        assert sha(uf2) == MAN['host_uf2_sha256']
        info = run([PICO, 'info', '-a', '--ser', MAN['host_uid']])
        assert 'meter-host-relay-20261123.1' in info and 'bootsel' in info
        run([PICO, 'load', '-v', uf2, '--ser', MAN['host_uid']], timeout=90)
        run([PICO, 'verify', uf2, '--ser', MAN['host_uid']], timeout=90)
        info = run([PICO, 'info', '-a', '--ser', MAN['host_uid']])
        assert 'meter-host-relay-20261123.2' in info
        print('HOST_V2_INSTALLED_VERIFIED_LEFT_IN_BOOTSEL')
    elif phase == 'parent-backup':
        run(BASE + ['exec', 'import rp2,machine; rp2.StateMachine(4).active(0); rp2.StateMachine(5).active(0); machine.Pin(12,machine.Pin.IN); machine.Pin(13,machine.Pin.IN)'])
        probe_sources(MAN['backup_sources'])
        run(BASE + ['exec', 'import machine; machine.bootloader()'], timeout=8, disconnect=True)
        flash_backup(MAN['parent_uid'], 'parent', 4 * 1024 * 1024)
        run([PICO, 'reboot', '--ser', MAN['parent_uid'].upper()])
    elif phase == 'parent-install':
        record = json.loads((OUT / 'parent_flash_backup.json').read_text())
        assert sha(OUT / 'parent_flash_before.bin') == record['sha256']
        probe_sources(MAN['backup_sources'])
        for path, change in MAN['parent_changes'].items():
            source = OUT / 'candidate' / path.lstrip('/')
            assert sha(source) == change['after_sha256']
            temporary = path + '.rst_new'
            run(BASE + ['fs', 'cp', source, ':' + temporary])
            code = "import os,hashlib,binascii; p=" + repr(temporary) + "; b=open(p,'rb').read(); assert binascii.hexlify(hashlib.sha256(b).digest()).decode()==" + repr(change['after_sha256']) + "; compile(b,p,'exec'); os.rename(p," + repr(path) + "); os.sync(); print('INSTALLED|'+p)"
            run(BASE + ['exec', code])
        expected = dict(MAN['backup_sources'])
        expected.update({p: c['after_sha256'] for p, c in MAN['parent_changes'].items()})
        probe_sources(expected)
        run(BASE + ['exec', "import rp2,machine; rp2.StateMachine(4).active(0); rp2.StateMachine(5).active(0); machine.Pin(12,machine.Pin.IN); machine.Pin(13,machine.Pin.IN); print('PARENT_INSTALLED_PIO_STOPPED')"])
    elif phase == 'parent-verify':
        expected = dict(MAN['backup_sources'])
        expected.update({p: c['after_sha256'] for p, c in MAN['parent_changes'].items()})
        probe_sources(expected)
        run(BASE + ['exec', "import rp2,machine; rp2.StateMachine(4).active(0); rp2.StateMachine(5).active(0); machine.Pin(12,machine.Pin.IN); machine.Pin(13,machine.Pin.IN); from src.command_parser import parse_ate_command; from src.external_instrument_link import ExternalInstrumentLink; assert parse_ate_command('HOST_RESET METER').category=='HOST_MANAGEMENT'; assert hasattr(ExternalInstrumentLink,'start_management'); print('PARENT_POST_REBOOT_VERIFIED_PIO_STOPPED')"])
    else:
        raise ValueError(phase)
