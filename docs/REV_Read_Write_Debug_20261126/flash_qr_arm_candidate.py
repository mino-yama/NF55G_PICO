"""Back up and verify the QR HOST before a diagnostic write; retain BOOTSEL."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess


CASE = Path(__file__).resolve().parent
ROOT = CASE.parents[1]
TOOL = ROOT / 'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
SERIAL = 'A06FEA01012EC137'
STABLE = 'qr-fixed-20261123.1'
CANDIDATE = 'qr-arm-diag-20261126.1'
FLASH_SIZE = 2 * 1024 * 1024


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    args = argparse.ArgumentParser(description=__doc__)
    mode = args.add_mutually_exclusive_group(required=True)
    mode.add_argument('--candidate', type=Path, help='directory containing the verified candidate manifest')
    mode.add_argument('--restore', type=Path, help='the flash-run directory containing the original 2 MB backup')
    options = args.parse_args()
    run_dir = CASE / f'qr_arm_flash_{datetime.now():%Y%m%d_%H%M%S_%f}'
    run_dir.mkdir()

    def run(step, *command):
        result = subprocess.run([TOOL, *[str(part) for part in command], '--ser', SERIAL],
                                cwd=ROOT, capture_output=True, timeout=120)
        (run_dir / f'{step}.log').write_bytes(result.stdout + result.stderr)
        check(result.returncode == 0, f'{step} failed, see {run_dir}')
        return result.stdout.decode('utf8', 'replace')

    def identify(step, version):
        info = run(step, 'info', '-a')
        check('0x' + SERIAL.lower() in info.lower() and 'bootsel' in info.lower()
              and '2048K' in info and version in info, f'Unexpected device in {run_dir}')

    def load(step, image):
        run(step + '_load', 'load', '-v', image)
        run(step + '_verify', 'verify', image)

    print(run_dir, flush=True)
    if options.restore:
        source = options.restore.resolve()
        backup = source / 'before_flash_2MB.bin'
        expected = (source / 'backup.sha256').read_text(encoding='ascii').strip()
        check(backup.stat().st_size == FLASH_SIZE and digest(backup) == expected, 'Invalid flash backup')
        identify('restore_before', CANDIDATE)
        load('restore', backup)
        identify('restore_after', STABLE)
        return

    source = options.candidate.resolve()
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf8'))
    image = source / 'usb_submcu_host_probe.uf2'
    check(manifest['version'] == CANDIDATE and manifest['file'] == image.name
          and digest(image) == manifest['sha256'], 'Invalid candidate image')
    identify('before', STABLE)
    backup = run_dir / 'before_flash_2MB.bin'
    run('backup', 'save', '-a', '-v', backup)
    check(backup.stat().st_size == FLASH_SIZE, 'Invalid backup size')
    run('backup_verify', 'verify', backup)
    (run_dir / 'backup.sha256').write_text(digest(backup) + '\n', encoding='ascii')
    try:
        load('candidate', image)
        identify('after', CANDIDATE)
    except Exception:
        load('failure_restore', backup)
        identify('failure_restore_after', STABLE)
        raise


if __name__ == '__main__':
    main()
