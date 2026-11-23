"""退避sourceのhash照合とRST配置候補の固定。実機への書込みは行わない。"""
import hashlib
import json
import shutil
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    raw = (OUT / 'parent_inventory.log').read_bytes()
    inventory = raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
    backup = {}
    for line in inventory.splitlines():
        if not line.startswith('SHA256|/src/'):
            continue
        _, path, expected = line.split('|')
        local = OUT / 'parent_before' / path.lstrip('/')
        assert digest(local) == expected, path
        backup[path] = expected
    assert len(backup) > 20
    candidate = OUT / 'candidate'
    (candidate / 'src').mkdir(parents=True, exist_ok=True)
    changes = {}
    for name in ('main.py', 'command_parser.py', 'external_instrument_contract.py',
                 'external_instrument_link.py'):
        source = ROOT / 'src' / name
        compile(source.read_bytes(), str(source), 'exec')
        target = candidate / 'src' / name
        shutil.copyfile(source, target)
        changes['/src/' + name] = {'before_sha256': backup['/src/' + name],
                                  'after_sha256': digest(target)}
    uf2 = ROOT / 'tmp/host_reset_build_20261123/usb_submcu_external_meter_relay.uf2'
    expected = '9c32948fa4df986ac53e377925535608b60f5d2b870ffb7eaf31c0a2c53c6427'
    assert digest(uf2) == expected
    shutil.copyfile(uf2, candidate / uf2.name)
    manifest = {'parent_uid': '69f7d45962cfdfad', 'host_uid': 'BFCF2EDB84B0B37F',
                'backup_sources': backup, 'parent_changes': changes,
                'host_uf2_sha256': expected, 'host_uf2_bytes': uf2.stat().st_size,
                'preserve_deployed_config': True, 'hardware_deployed': False}
    (OUT / 'package_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('BACKUP_HASHES_VERIFIED', len(backup))
    print('CANDIDATE_PARENT_FILES', len(changes))
    print('HOST_UF2_VERIFIED', expected)
