"""ビルド成功後だけ実行し、旧配布物を上書きせずhash付き新版を保存する。"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
version='qr-fixed-20261123.1'
source=ROOT/'firmware/usb_submcu_host_probe'
target=source/'releases'/version
assert not target.exists(), 'existing release must be preserved'
build=source/'build_uart_continuous'
assert version.encode() in (build/'usb_submcu_host_probe.bin').read_bytes(), 'stale build'
target.mkdir()
for suffix in ('uf2','bin','elf'):
    shutil.copy2(build/('usb_submcu_host_probe.'+suffix),target/('usb_submcu_qr_uart_probe.'+suffix))
paths=list(source.glob('*.c'))+list(source.glob('*.h'))+[source/'CMakeLists.txt']
paths+=list((source/'boards').glob('*.h'))
paths+=[p for p in (source/'vendor').rglob('*') if p.is_file()]
paths += [ROOT/p for p in ('scripts/build_usb_submcu_host_probe.ps1','scripts/usb_submcu_probe_log.py',
    'src/qr_reader.py','tests/test_usb_submcu_qr_alt_decoder.py','tests/test_qr_label_profile.py',
    'tests/test_qr_integration_capture.py')]
for path in paths:
    destination=target/'source'/path.relative_to(ROOT)
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,destination)
tool=ROOT/'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
p=subprocess.run([str(tool),'info','-a',str(target/'usb_submcu_qr_uart_probe.uf2')],capture_output=True,timeout=30)
assert p.returncode==0,p.stderr
(target/'UF2_Info.txt').write_bytes(p.stdout+p.stderr)
files=[]
for path in sorted(target.rglob('*')):
    if path.is_file():
        raw=path.read_bytes()
        files.append(dict(file=path.relative_to(target).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
manifest=dict(date_jst='2026-11-23',version=version,operational_target_usb_serial='A06FEA01012EC137',
    built=True,flashed=False,hardware_acceptance=False,host_mock_tests=516,skipped=0,
    sdk='2.2.0',platform='rp2350-arm-s',change='allow period only at revision positions 23..25',files=files)
(target/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([item for item in files if item['file'].endswith('.uf2')],indent=2))
