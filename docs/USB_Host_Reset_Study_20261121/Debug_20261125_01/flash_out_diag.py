"""Write and verify .25.2 on the identified meter HOST; leave it in BOOTSEL."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from build_out_diag_from_graph import CASE, PICOTOOL, REL


SERIAL = 'BFCF2EDB84B0B37F'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(candidate):
    manifest = json.loads((candidate / 'manifest.json').read_text(encoding='utf-8-sig'))
    assert manifest['version'] == 'meter-host-relay-20261125.2'
    uf2 = candidate / f'{REL}.uf2'
    entry = next(f for f in manifest['files'] if f['name'] == uf2.name)
    assert entry['bytes'] == uf2.stat().st_size and entry['sha256'].lower() == sha(uf2)
    backup = CASE / 'host_out_diag_preflight' / 'flash_before.bin'
    assert backup.stat().st_size == 2 * 1024 * 1024
    checked_backup = backup.with_name('manifest.json')

    def run(step, *args):
        p = subprocess.run([PICOTOOL, *args], capture_output=True, timeout=90)
        with (candidate / f'flash_{step}.log').open('xb') as out:
            out.write(p.stdout + p.stderr)
        p.check_returncode()
        return p.stdout.decode('utf8')

    def identify(text, version):
        for label, value in (('chipid', '0x' + SERIAL), ('boot type', 'bootsel'),
                             ('flash size', '2048K'), ('version', version)):
            assert re.search(r'(?im)^\s*' + label + r':\s*' + re.escape(value) + r'\s*$', text)

    identify(run('before', 'info', '-a', '--ser', SERIAL), 'meter-host-relay-20261125.1')
    run('verify_backup', 'verify', backup, '--ser', SERIAL)
    checked_backup.write_text(json.dumps({'chipid': SERIAL, 'bytes': backup.stat().st_size,
                                           'sha256': sha(backup)}, indent=2), encoding='utf8')
    run('load', 'load', '-v', uf2, '--ser', SERIAL)
    run('verify', 'verify', uf2, '--ser', SERIAL)
    identify(run('after', 'info', '-a', '--ser', SERIAL), 'meter-host-relay-20261125.2')
    print(f'FLASH VERIFIED {SERIAL} .25.2; BOOTSEL retained: {candidate}', flush=True)


if __name__ == '__main__':
    folder = (CASE / sys.argv[1]).resolve()
    assert folder.parent == CASE.resolve() and folder.name.startswith('candidate_')
    main(folder)
