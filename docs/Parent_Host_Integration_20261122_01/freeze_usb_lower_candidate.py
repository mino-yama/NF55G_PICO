"""診断UF2/対応ソースを固定し、ELF内のCDC table参照も照合する。"""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
SOURCE = ROOT / 'firmware/usb_submcu_external_meter_host'
OUT = BASE / 'USB_Lower_Diagnostic_Candidate'
if OUT.exists():
    assert not any(p.is_file() for p in OUT.rglob('*')), 'preserve existing candidate files'
OUT.mkdir(exist_ok=True)
(OUT / 'source').mkdir(exist_ok=True)
PICO = ROOT / 'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
NM = Path(os.environ['LOCALAPPDATA']) / 'Arduino15/packages/rp2040/tools/pqt-gcc/4.1.0-1aec55e/bin/arm-none-eabi-nm.exe'
elf = SOURCE / 'build/usb_submcu_external_meter_relay.elf'
raw = elf.read_bytes()
assert raw[:6] == b'\x7fELF\x01\x01'
assert b'TIMEOUT_RX%u_T%u_C%u_X%s' in raw
symbols = subprocess.run([str(NM), '-S', '-n', str(elf)], capture_output=True, text=True, check=True).stdout
receiver_name = '__wrap_pio_usb_bus_receive_packet_and_handshake'
receiver_symbols = [line.split() for line in symbols.splitlines() if line.split()[-1:] == [receiver_name]]
assert len(receiver_symbols) == 1
receiver_address = int(receiver_symbols[0][0], 16)
assert 0x20000000 <= receiver_address < 0x20100000, 'receiver wrapper must execute from RAM'
objdump = NM.with_name('arm-none-eabi-objdump.exe')
transaction_symbols = [line.split()[-1] for line in symbols.splitlines() if line.split()[-1].startswith('usb_in_transaction')]
assert len(transaction_symbols) == 1
receiver_disassembly = subprocess.run([str(objdump), '-d', '--disassemble=' + transaction_symbols[0], str(elf)],
                                     capture_output=True, text=True, check=True).stdout
assert '<' + receiver_name + '>' in receiver_disassembly, 'bulk IN must call receiver wrapper'
(OUT / 'receiver_disassembly.txt').write_text(receiver_disassembly, encoding='utf-8')
found = {}
for line in symbols.splitlines():
    parts = line.split()
    if len(parts) == 4 and parts[3] in ('__wrap_cdch_xfer_cb', 'cdch_xfer_cb', 'usbh_class_drivers'):
        found[parts[3]] = (int(parts[0], 16), int(parts[1], 16))
table_address, table_size = found['usbh_class_drivers']
section_offset = struct.unpack_from('<I', raw, 32)[0]
entry_size, section_count = struct.unpack_from('<HH', raw, 46)
table = None
for index in range(section_count):
    section = struct.unpack_from('<10I', raw, section_offset + index * entry_size)
    address, offset, size = section[3:6]
    if address <= table_address and table_address + table_size <= address + size:
        table = raw[offset + table_address - address:offset + table_address - address + table_size]
        break
assert table is not None
words = struct.unpack('<' + 'I' * (len(table) // 4), table)
wrap_pointer = found['__wrap_cdch_xfer_cb'][0] | 1
assert wrap_pointer in words
assert (found['cdch_xfer_cb'][0] | 1) not in words
uf2 = SOURCE / 'build/usb_submcu_external_meter_relay.uf2'
info = subprocess.run([str(PICO), 'info', '-a', str(uf2)], capture_output=True, text=True, check=True).stdout
assert 'meter-host-relay-20261122.3' in info and 'RP2350' in info
(OUT / 'uf2_info.txt').write_text(info, encoding='utf-8')
(OUT / 'symbols.txt').write_text(symbols, encoding='utf-8')
sha = lambda b: hashlib.sha256(b).hexdigest()
sources = {}
for name in ('relay_main.c', 'relay_host.c', 'relay_host.h', 'relay_wire.c', 'relay_wire.h',
             'relay_cdc_guard.c', 'relay_cdc_guard.h', 'relay_usb_diag.c', 'relay_usb_diag.h', 'CMakeLists.txt', 'tusb_config.h', 'newlib_malloc_lock.c'):
    data = (SOURCE / name).read_bytes()
    (OUT / 'source' / name).write_bytes(data)
    sources[name] = sha(data)
data = uf2.read_bytes()
filename = 'meter_host_relay_20261122_3.uf2'
(OUT / filename).write_bytes(data)
manifest = {'version': 'meter-host-relay-20261122.3', 'date_jst': '2026-11-22',
            'target_serial': 'BFCF2EDB84B0B37F', 'uf2': {'file': filename, 'bytes': len(data), 'sha256': sha(data)},
            'sources': sources, 'unit_mock': {'count': 467, 'seconds': 19.094, 'result': 'OK'},
            'arm_build': 'success -Wall -Wextra -Werror',
            'wrap_table': {'address': hex(table_address), 'callback_pointer': hex(wrap_pointer), 'verified': True},
            'timeout_snapshot_format_in_elf': True, 'deployed': False, 'runtime_accepted': False}
manifest['receiver_wrap'] = {'address': hex(receiver_address), 'ram': True, 'bulk_in_call_verified': True}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest), flush=True)
