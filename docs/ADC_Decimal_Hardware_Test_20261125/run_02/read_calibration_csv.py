# 親Picoで閉じた直前の試行CSVを読み出し、AD/ARの実送信と照合するために原文を保全する。
import binascii
import hashlib
import machine
import sys

assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
logger = app.logger
assert not logger.test_running and not logger.active and not logger.recovery_pending and not app._comm_busy()
trial = logger.test_history[-1]
assert trial['reason'] == 'TEST_END' and trial['sd_status'] == 'OK'
sink = logger.sd_sink
path = sink.root + '/' + sink.bank + '/' + trial['filename']
sha = hashlib.sha256()
print('CSV|' + trial['filename'])
with open(path, 'rb') as source:
    while True:
        part = source.read(128)
        if not part:
            break
        sha.update(part)
        print('DATA|' + binascii.b2a_base64(part).decode().strip())
print('SHA256|' + binascii.hexlify(sha.digest()).decode())
