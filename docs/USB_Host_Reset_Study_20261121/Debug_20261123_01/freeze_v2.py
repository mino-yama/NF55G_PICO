""".23.1成果物を保持して.23.2候補と対応source hashを別名固定する。"""
import hashlib
import json
import shutil
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    destination = OUT / 'package_manifest_v2.json'
    assert not destination.exists()
    manifest = json.loads((OUT / 'package_manifest.json').read_text())
    build = ROOT / 'tmp/host_reset_build_20261123_02'
    uf2 = build / 'usb_submcu_external_meter_relay.uf2'
    elf = build / 'usb_submcu_external_meter_relay.elf'
    target = OUT / 'candidate/usb_submcu_external_meter_relay_v2.uf2'
    shutil.copyfile(uf2, target)
    manifest.update({'host_version': 'meter-host-relay-20261123.2',
                     'host_uf2_sha256': sha(uf2), 'host_uf2_bytes': uf2.stat().st_size,
                     'host_elf_sha256': sha(elf), 'host_elf_bytes': elf.stat().st_size})
    source_dir = OUT / 'candidate/host_v2_source'
    source_dir.mkdir()
    sources = {}
    folder = ROOT / 'firmware/usb_submcu_external_meter_host'
    for path in sorted(folder.iterdir()):
        if path.is_file() and (path.suffix in ('.c', '.h', '.cmake') or path.name == 'CMakeLists.txt'):
            shutil.copyfile(path, source_dir / path.name)
            sources[path.name] = sha(path)
    manifest['host_source_sha256'] = sources
    destination.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in manifest.items() if k.startswith('host_')}, indent=2))
