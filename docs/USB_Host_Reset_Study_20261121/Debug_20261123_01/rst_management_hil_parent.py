# 配置済み親コードの実ATE/UART経由RST検証。NF送信はRAM guardで禁止する。
import machine
import rp2
import time
import binascii
import json
from src.main import create_fixture_app

assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
rp2.StateMachine(4).active(0)
rp2.StateMachine(5).active(0)
machine.Pin(12, machine.Pin.IN)
machine.Pin(13, machine.Pin.IN)


class NoNFWrite:
    def __init__(self, transport):
        self.transport = transport
        self.attempts = 0

    def any(self):
        return self.transport.any()

    def read(self, count=1):
        return self.transport.read(count)

    def write(self, data):
        self.attempts += 1
        raise RuntimeError('NF write forbidden in RST management HIL')


app = create_fixture_app(enable_hardware=True)
assert app.external_link is not None, app.external_error
assert not app.logger.active and not app.logger.test_running
nf_guard = NoNFWrite(app.protocol.uart)
app.protocol.uart = nf_guard
parent_nonce_before = app.external_link.parent_nonce
cache_before = {name: app.cache.metadata(name) for name in app.cache._entries}
print('RST_HIL_READY|' + binascii.hexlify(parent_nonce_before).decode())
started = time.ticks_ms()
try:
    while time.ticks_diff(time.ticks_ms(), started) < 18000:
        app.service_once()
        time.sleep_ms(1)
    assert parent_nonce_before == app.external_link.parent_nonce
    assert cache_before == {name: app.cache.metadata(name) for name in app.cache._entries}
    assert nf_guard.attempts == 0
    print('RST_HIL_DONE|' + json.dumps({
        'parent_nonce': binascii.hexlify(parent_nonce_before).decode(),
        'nf_write_attempts': nf_guard.attempts,
        'cache_unchanged': True, 'fault': app.external_link.fault,
        'host_info': app.external_link.host_info,
        'frame_errors': app.external_link.reader.errors,
        'logger_active': app.logger.active,
    }))
finally:
    app.external_link.transport.close()
    machine.Pin(12, machine.Pin.IN)
    machine.Pin(13, machine.Pin.IN)
    print('RST_HIL_STOPPED_PIO_INPUT')
