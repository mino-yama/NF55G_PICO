count=241
first_time='20261125_130131'
last_time='20261125_133633'
expected_session='73dfa50657cdfa87'

import binascii, hashlib, json, machine, os, sys, time
assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
assert binascii.hexlify(app.external_link.parent_nonce).decode() == expected_session
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
last = int(app.logger.last_test_id[1:])
first = last - count + 1
assert first > 0
print('RANGE|' + json.dumps([first,last]))
for bank in ('BANK_A', 'BANK_B'):
    folder = app.logger.sd_sink.root + '/' + bank
    for entry in os.ilistdir(folder):
        name = entry[0]
        if not name.endswith('.csv'):
            continue
        fields = name[:-4].split('_')
        if len(fields) != 3 or not fields[2].startswith('T') or not fields[2][1:].isdigit():
            continue
        number = int(fields[2][1:])
        stamp = fields[0] + '_' + fields[1]
        if not (first <= number <= last and first_time <= stamp <= last_time):
            continue
        path = folder + '/' + name
        print('FILE|' + json.dumps({'path':path,'trial':number,'bytes':os.stat(path)[6]}))
        sha = hashlib.sha256()
        with open(path, 'rb') as f:
            while True:
                b = f.read(128)
                if not b:
                    break
                sha.update(b)
                print('DATA|' + binascii.b2a_base64(b).decode().strip())
                time.sleep_ms(15)
        print('HASH|' + binascii.hexlify(sha.digest()).decode())
print('EXPORT_END')
