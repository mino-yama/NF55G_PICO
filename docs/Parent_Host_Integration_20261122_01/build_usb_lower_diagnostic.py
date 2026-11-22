"""CMakeのPython起動経路を避け、同じ固定SDK/targetを直接buildする。"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'firmware/usb_submcu_external_meter_host'
CMAKE = ROOT / '.venv/Lib/site-packages/cmake/data/bin/cmake.exe'
NINJA = ROOT / '.venv/Scripts/ninja.exe'
for tool in (CMAKE, NINJA):
    if not tool.is_file():
        raise RuntimeError('native build tool missing: ' + str(tool))
with (OUT / 'USB_Lower_Diagnostic_Build_Retry.log').open('xb') as log:
    for args in ([str(CMAKE), '-S', str(SOURCE), '-B', str(SOURCE / 'build'),
                  '-DCMAKE_MAKE_PROGRAM=' + str(NINJA)],
                 [str(CMAKE), '--build', str(SOURCE / 'build'), '--target',
                  'usb_submcu_external_meter_relay', '--parallel', '8']):
        p = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        log.flush()
        print('BUILD_STAGE_EXIT=' + str(p.returncode), flush=True)
        if p.returncode:
            raise SystemExit(p.returncode)
