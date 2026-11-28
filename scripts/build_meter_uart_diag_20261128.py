"""元FWを変更せず、native USB観測付きUART単体診断候補をビルドする。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0/uart_diagnostic'
source=OUT/'source';original=ROOT/'firmware/usb_submcu_external_meter_host'
for name in ('relay_host.c','relay_host.h','relay_wire.c','relay_wire.h','boards/waveshare_rp2350_usb_a_host_eval.h'):
    dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True)
    assert not dest.exists()
    shutil.copyfile(original/name,dest)
toolchain=Path(os.environ['LOCALAPPDATA'])/'Arduino15/packages/rp2040/tools/pqt-gcc/4.1.0-1aec55e'
cmake=ROOT/'.venv/Scripts/cmake.exe'
args=[str(cmake),'-S',str(source),'-B',str(OUT/'build'),'-G','Ninja',
      '-DPICO_SDK_PATH='+str(ROOT/'tools/usb_submcu/pico-sdk-2.2.0'),
      '-DPICO_TOOLCHAIN_PATH='+str(toolchain),
      '-DCMAKE_MAKE_PROGRAM='+str(ROOT/'.venv/Scripts/ninja.exe'),
      '-Dpicotool_DIR='+str(ROOT/'tools/usb_submcu/picotool-2.2.0/picotool'),'-DCMAKE_BUILD_TYPE=Release']
for name,cmd in [('configure',args),('build',[str(cmake),'--build',str(OUT/'build'),'--parallel','8'])]:
    p=subprocess.run(cmd,capture_output=True,timeout=240)
    (OUT/(name+'.log')).write_bytes(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(name+' failed; inspect '+str(OUT/(name+'.log')))
image=OUT/'build/meter_uart_diagnostic.uf2'
manifest={'version':'meter-host-relay-uartdiag-20261128.1','uf2':str(image.relative_to(ROOT)),'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'source_hashes':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()},'purpose':'UART-only diagnosis; meter USB not initialized','deployed':False}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest))
