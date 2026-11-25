"""Replay CMake/Ninja compiler and link commands when Ninja cannot launch children."""
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


CASE = Path(__file__).resolve().parent
ROOT = CASE.parents[2]
REL = 'usb_submcu_external_meter_relay'
ORIGINAL = ROOT / 'tmp' / 'usb_host_build' / '20261125_090518_376'
PICOTOOL = ROOT / 'tools' / 'usb_submcu' / 'picotool-2.2.0' / 'picotool' / 'picotool.exe'


def main():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    stamp = now.strftime('%Y%m%d_%H%M%S_%f')
    work = ROOT / 'tmp' / 'usb_host_build' / now.strftime('g%H%M%S')
    out = CASE / f'candidate_{stamp}'
    out.mkdir()
    ninja = ROOT / '.venv' / 'Scripts' / 'ninja.exe'
    raw = subprocess.check_output([ninja, '-C', ORIGINAL, '-t', 'compdb', '-x'], cwd=ROOT, timeout=30)
    graph = json.loads(raw)
    objects = [row for row in graph if row.get('output', '').replace('\\', '/').startswith(
        f'CMakeFiles/{REL}.dir/') and row['output'].endswith('.obj') and ' -c ' in row['command']]
    link_rows = [row for row in graph if row.get('output') == f'{REL}.elf']
    assert len(link_rows) == 1 and len(objects) >= 80
    assert any('relay_main.c' in row['file'] and '20261125.2' in row['command'] for row in objects)
    link = link_rows[0]['command'].split(' && ')[1]
    assert 'arm-none-eabi-g++.exe ' in link and '--wrap=pio_usb_bus_wait_handshake' in link and '.rsp' not in link
    # Reuse only generated inputs and the unchanged boot-stage configuration, then compile every relay object.
    shutil.copytree(ORIGINAL / 'generated', work / 'generated')
    shutil.copytree(ORIGINAL / 'pico-sdk' / 'src' / 'rp2350' / 'boot_stage2',
                    work / 'pico-sdk' / 'src' / 'rp2350' / 'boot_stage2')
    shutil.copytree(ORIGINAL / 'pico-sdk' / 'src' / 'rp2_common' / 'tinyusb',
                    work / 'pico-sdk' / 'src' / 'rp2_common' / 'tinyusb')
    shutil.copy2(ORIGINAL / 'pico_flash_region.ld', work / 'pico_flash_region.ld')
    for row in objects:
        (work / row['output']).parent.mkdir(parents=True, exist_ok=True)

    def relocate(command):
        return command.replace(ORIGINAL.as_posix(), work.as_posix()).replace(str(ORIGINAL), str(work))

    def compile_one(row):
        command = relocate(row['command'])
        # Dependency files are unnecessary when every target object is compiled explicitly.
        if ' -MD -MT ' in command:
            flags, rest = command.split(' -MD -MT ', 1)
            command = flags + ' -o ' + rest.split(' -o ', 1)[1]
        p = subprocess.run(command, cwd=work, capture_output=True, timeout=75)
        if p.returncode:
            raise RuntimeError(row['file'] + '\n' + p.stderr.decode(errors='replace'))
        assert (work / row['output']).is_file(), row['output']

    (out / 'graph_build.json').write_text(json.dumps({'original': str(ORIGINAL), 'objects': objects, 'link': link},
                                                    indent=2), encoding='utf8')
    print(f'Compiling {len(objects)} relay objects in {work}', flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index, _ in enumerate(pool.map(compile_one, objects), 1):
            if index % 16 == 0 or index == len(objects):
                print(f'Compiled {index}/{len(objects)}', flush=True)
    subprocess.run(relocate(link), cwd=work, check=True, timeout=75)
    elf, uf2 = work / f'{REL}.elf', work / f'{REL}.uf2'
    subprocess.run([PICOTOOL, 'uf2', 'convert', '--quiet', elf, uf2, '--family', 'rp2350-arm-s'],
                   cwd=work, check=True, timeout=30)
    info = subprocess.check_output([PICOTOOL, 'info', '-a', uf2], cwd=work, timeout=30)
    assert b'meter-host-relay-20261125.2' in info and b'RP2350' in info
    (out / 'uf2_info.log').write_bytes(info)
    files = []
    for file in (uf2, elf):
        dest = out / file.name
        shutil.copy2(file, dest)
        files.append({'name': dest.name, 'bytes': dest.stat().st_size,
                      'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
    (out / 'manifest.json').write_text(json.dumps({'version': 'meter-host-relay-20261125.2', 'files': files},
                                                  indent=2), encoding='utf8')
    print(f'Candidate verified: {out}', flush=True)


if __name__ == '__main__':
    main()
