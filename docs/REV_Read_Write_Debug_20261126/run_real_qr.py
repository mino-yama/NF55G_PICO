import json
from pathlib import Path
import subprocess
import sys


folder = Path(__file__).resolve().parent
directory = Path(sys.argv[1]).resolve()
assert directory.parent == folder
labels = json.loads((folder.parent / 'QR_Hardware_Integration_20261123_01' / 'Production_Label_Retest_20261125' /
                     'expected.json').read_text(encoding='utf8'))
mode = sys.argv[2:]
if mode in (['--arm-candidate'], ['--arm-link'], ['--arm-repeat']):
    source_name = 'qr_arm_candidate_parent.py'
    params = f"EXPECTED_B={labels['B']['payload']!r}\nEXPECTED_B_HEX={labels['B']['ss_data_hex']!r}\n"
    params += f"LINK_ONLY={mode == ['--arm-link']!r}\n"
    params += f"ARM_CASES={3 if mode == ['--arm-repeat'] else 1}\n"
    log_name = 'qr_arm_candidate_wire.log'
elif mode in (['--late-guard'], ['--prearm-drain'], ['--prearm-drain-recover-rx']):
    prearm = mode != ['--late-guard']
    source_name = 'qr_prearm_drain_parent.py' if prearm else 'qr_late_guard_parent.py'
    params = f"LATE_A={labels['A']['payload']!r}\nEXPECTED_B={labels['B']['payload']!r}\nEXPECTED_B_HEX={labels['B']['ss_data_hex']!r}\n"
    params += f"RECOVER_RX={mode == ['--prearm-drain-recover-rx']!r}\n"
    log_name = 'qr_prearm_drain_wire.log' if prearm else 'qr_late_guard_wire.log'
else:
    assert not mode, mode
    source_name = 'real_qr_parent.py'
    params = f"REAL_LABELS = {tuple((key, item['payload'], item['ss_data_hex']) for key, item in labels.items())!r}\n"
    log_name = 'real_qr_wire.log'
script = directory / ('parent_' + source_name)
script.write_text(params + (folder / source_name).read_text(encoding='utf8'), encoding='utf8')
base = [sys.executable, '-u', '-m', 'mpremote', 'connect', 'COM6', 'resume']
try:
    with (directory / log_name).open('x', encoding='utf8') as log, subprocess.Popen(
            base + ['run', str(script)], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf8', errors='replace') as p:
        for line in p.stdout:
            log.write(line)
            log.flush()
            if any(prefix in line for prefix in ('REAL_QR|', 'QR_HID_', 'QR_LATE_', 'QR_DRAIN', 'Error')):
                print(line.rstrip(), flush=True)
        code = p.wait()
finally:
    subprocess.run(base + ['exec', '--no-follow', "import sys; sys.modules['src.main'].active_app.run()"],
                   timeout=15, check=True)
raise SystemExit(code)
