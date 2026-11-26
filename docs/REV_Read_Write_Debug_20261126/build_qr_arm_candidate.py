"""Build and identify the RP2350 QR diagnostic UF2 without touching the fixture."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


case = Path(__file__).resolve().parent
root = case.parents[1]
name = sys.argv[1] if len(sys.argv) == 2 else 'qr_arm_candidate_02'
if not name.startswith('qr_arm_candidate_') or not name.removeprefix('qr_arm_candidate_').isdigit():
    raise SystemExit('Expected qr_arm_candidate_<number>')
out = case / name
build = root / 'tmp' / ('qra' + name.rsplit('_', 1)[1])
out.mkdir(exist_ok=True)
tools = root / 'tools/usb_submcu'
gcc = Path(os.environ['LOCALAPPDATA']) / 'Arduino15/packages/rp2040/tools/pqt-gcc/4.1.0-1aec55e'
cmake = root / '.venv/Scripts/cmake.exe'
picotool = tools / 'picotool-2.2.0/picotool'
version = 'qr-arm-diag-20261126.1'


def run(stage, args):
    log = out / (stage + '.log')
    print(log, flush=True)
    with log.open('x', encoding='utf8') as file:
        subprocess.run(args, cwd=root, stdout=file, stderr=subprocess.STDOUT, check=True, timeout=300)
    return log.read_text(encoding='utf8', errors='replace')


run('configure', [cmake, '-S', 'firmware/usb_submcu_host_probe', '-B', build, '-G', 'Ninja',
                  '-DCMAKE_MAKE_PROGRAM=' + str(root / '.venv/Scripts/ninja.exe'),
                  '-DPICO_SDK_PATH=' + str(tools / 'pico-sdk-2.2.0'),
                  '-DPICO_TOOLCHAIN_PATH=' + str(gcc),
                  '-Dpioasm_DIR=' + str(tools / 'sdk-tools-2.2.0/pioasm'),
                  '-Dpicotool_DIR=' + str(picotool), '-DCMAKE_BUILD_TYPE=Release',
                  '-DPROBE_UART_TX_PIN=0', '-DPROBE_CONTINUOUS=ON', '-DPROBE_QR_ARM=ON'])
run('build', [cmake, '--build', build, '--parallel', '8'])
uf2 = build / 'usb_submcu_host_probe.uf2'
info = run('uf2_info', [picotool / 'picotool.exe', 'info', '-a', uf2])
if version not in info or 'RP2350' not in info:
    raise RuntimeError('Wrong RP2350 UF2 metadata')
shutil.copyfile(uf2, out / uf2.name)
(out / 'manifest.json').write_text(json.dumps({'version': version, 'file': uf2.name,
                                              'sha256': hashlib.sha256(uf2.read_bytes()).hexdigest()},
                                             indent=2) + '\n', encoding='utf8')
