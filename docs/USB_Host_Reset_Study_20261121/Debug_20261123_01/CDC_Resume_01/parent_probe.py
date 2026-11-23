# 前回の親app/nonce/fault/管理連番を保持し、閉じたPIO transportだけを再開する。
import machine
import rp2
import time
import binascii
import json
from src.external_instrument_pio import ExternalPioUART

assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
link = app.external_link
assert not link.busy and not app._external_pending
assert not app.logger.active and not app.logger.test_running
assert link.transport._closed
assert not rp2.StateMachine(4).active() and not rp2.StateMachine(5).active()
assert nf_guard.attempts == 0
nonce_before = link.parent_nonce
cache_before = {name: app.cache.metadata(name) for name in app.cache._entries}


class CaptureTransport:
    def __init__(self):
        self.actual = ExternalPioUART()
        self.tx = bytearray()
        self._closed = False

    def any(self):
        return self.actual.any()

    def read(self, size=64):
        return self.actual.read(size)

    def write(self, data):
        written = self.actual.write(data)
        self.tx.extend(data[:written])
        return written

    def take_error(self):
        return self.actual.take_error()

    def close(self):
        self.actual.close()
        self._closed = True


link.transport = CaptureTransport()
print('CDC_PROBE_READY|' + nonce_before.hex())
started = time.ticks_ms()
try:
    while time.ticks_diff(time.ticks_ms(), started) < 12000:
        app.service_once()
        time.sleep_ms(1)
    assert nonce_before == link.parent_nonce
    assert nf_guard.attempts == 0
    assert cache_before == {name: app.cache.metadata(name) for name in app.cache._entries}
    print('CDC_PROBE_DONE|' + json.dumps({
        'parent_nonce': nonce_before.hex(), 'fault': link.fault,
        'host_info': link.host_info, 'session': link.session.hex() if link.session else None,
        'nf_write_attempts': nf_guard.attempts, 'cache_unchanged': True,
        'frame_errors': link.reader.errors, 'stale_frames': link.stale_frames,
        'tx_hex': binascii.hexlify(link.transport.tx).decode(),
    }))
finally:
    link.transport.close()
    machine.Pin(12, machine.Pin.IN)
    machine.Pin(13, machine.Pin.IN)
    print('CDC_PROBE_STOPPED_PIO_INPUT')
