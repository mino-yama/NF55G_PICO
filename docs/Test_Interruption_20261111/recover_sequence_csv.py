import hashlib
import json
import time
from pathlib import Path
from mpremote.transport_serial import SerialTransport
import serial
import sys

folder = Path('docs/Test_Interruption_20261111')
repl = SerialTransport('COM6', wait=2)
try:
    repl.enter_raw_repl(soft_reset=False)
    payload = '''
import machine, os, binascii, hashlib, json
assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
names = sorted(n for n in os.listdir('/sd/BANK_A') if n.endswith('.csv'))
print('NAMES=' + repr(names[-4:]))
if '__FILE_PREFIX__':
    names = [name for name in names if name.startswith('__FILE_PREFIX__')]
    assert len(names) == 1, names
path = '/sd/BANK_A/' + names[-1]
with open(path, 'rb') as file:
    data = file.read()
print('PATH=' + path)
print('META=' + json.dumps({'size':len(data), 'sha256':binascii.hexlify(hashlib.sha256(data).digest()).decode()}))
'''.replace('__FILE_PREFIX__', sys.argv[2] if len(sys.argv) > 2 else '')
    stdout, stderr = repl.exec_raw(payload, timeout=40)
    if stderr:
        raise RuntimeError(stderr.decode())
    parts = {}
    for line in stdout.decode().splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            parts[key] = value
    print('NAMES=' + parts['NAMES'])
    print('PATH=' + parts['PATH'])
    meta = json.loads(parts['META'])
    data = bytearray()
    for offset in range(0, meta['size'], 256):
        block, error = repl.exec_raw('print(binascii.hexlify(data[' + str(offset) + ':' + str(offset + 256) + ']).decode())', timeout=20)
        if error:
            raise RuntimeError(error.decode())
        chunk = bytes.fromhex(block.decode().strip())
        assert len(chunk) == min(256, meta['size'] - offset), 'incomplete chunk'
        data.extend(chunk)
    assert hashlib.sha256(data).hexdigest() == meta['sha256'], 'device/PC hash mismatch'
    prefix = sys.argv[1] if len(sys.argv) > 1 else 'focused'
    target = folder / (prefix + '_' + Path(parts['PATH']).name.replace('.csv', '_verified.csv'))
    if target.exists():
        assert target.read_bytes() == data, 'refusing to overwrite different evidence'
    else:
        target.write_bytes(data)
    print('SAVED=' + str(target) + ' bytes=' + str(len(data)) + ' sha256=' + hashlib.sha256(data).hexdigest())
    repl.exit_raw_repl()
    repl.serial.write(b'\x04')
    time.sleep(2)
finally:
    repl.close()
with serial.Serial('COM20', 115200, timeout=2, write_timeout=1) as ate:
    ate.dtr = False
    ate.rts = False
    ate.reset_input_buffer()
    ate.write(b'*IDN?\r\n')
    print('ATE_RESTART=' + repr(ate.read_until(b'\n')))
