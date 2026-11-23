# 同じ親runtimeでD1だけを許可し、READ/SD/RTCとの共存を有限時間観測する。
import machine
import rp2
import time
import json
from src.frame import build_frame

link = app.external_link
assert not link.busy and not app._external_pending and not app._comm_busy()
assert link.transport._closed and not link.fault
assert not app.logger.active and not app.logger.test_running
assert app.logger.sd_sink.status == 'OK' and app.logger.sd_sink.mounted
assert app.logger.drop_count == 0 and len(app.logger.queue) == 0
old_nf_uart = app.protocol.uart
assert old_nf_uart is nf_guard and nf_guard.attempts == 0
nonce_before = link.parent_nonce
other_cache = {name: app.cache.metadata(name) for name in app.cache._entries if name != 'STATUS'}


class OnlyD1:
    def __init__(self, actual):
        self.actual = actual
        self.tx = bytearray()
        self.d1_count = 0
        self.rejected = 0

    def any(self):
        return self.actual.any()

    def read(self, count=1):
        return self.actual.read(count)

    def write(self, raw):
        if raw not in (build_frame('D1'), b'\x06', b'\x15'):
            self.rejected += 1
            raise RuntimeError('Only D1/ACK/plain NAK allowed in coexist HIL')
        if raw == build_frame('D1'):
            self.d1_count += 1
        count = self.actual.write(raw)
        self.tx.extend(raw[:count])
        return count


nf_only = OnlyD1(nf_guard.transport)
app.protocol.uart = nf_only
link.transport = CaptureTransport()
sink = app.logger.sd_sink
original_write, original_flush = sink.write_record, sink.flush
sd_stats = {'writes': 0, 'flushes': 0, 'during_comm': 0}


def checked_write(row):
    if app._comm_busy():
        sd_stats['during_comm'] += 1
        raise RuntimeError('SD write during communication')
    sd_stats['writes'] += 1
    return original_write(row)


def checked_flush():
    if app._comm_busy():
        sd_stats['during_comm'] += 1
        raise RuntimeError('SD flush during communication')
    sd_stats['flushes'] += 1
    return original_flush()


sink.write_record, sink.flush = checked_write, checked_flush
print('COEXIST_READY|' + nonce_before.hex())
started = time.ticks_ms()
try:
    while time.ticks_diff(time.ticks_ms(), started) < 110000:
        app.service_once()
        time.sleep_ms(1)
    assert nonce_before == link.parent_nonce
    assert other_cache == {name: app.cache.metadata(name) for name in app.cache._entries if name != 'STATUS'}
    print('COEXIST_DONE|' + json.dumps({
        'parent_nonce': nonce_before.hex(), 'host_info': link.host_info, 'fault': link.fault,
        'frame_errors': link.reader.errors, 'stale_frames': link.stale_frames,
        'nf_d1_count': nf_only.d1_count, 'nf_rejected': nf_only.rejected,
        'nf_tx_hex': nf_only.tx.hex(), 'sd_stats': sd_stats,
        'logger_active': app.logger.active, 'queue': len(app.logger.queue),
        'drop': app.logger.drop_count, 'sd_status': sink.status,
        'log_path': sink.open_filename, 'rtc_check': app.rtc.check(),
        'other_cache_unchanged': True, 'status_cache': app.cache.metadata('STATUS'),
        'external_tx_hex': link.transport.tx.hex(),
    }))
finally:
    if app.logger.active and not app._comm_busy():
        app.logger.log_cont_stop()
    sink.write_record, sink.flush = original_write, original_flush
    app.protocol.uart = old_nf_uart
    link.transport.close()
    machine.Pin(12, machine.Pin.IN)
    machine.Pin(13, machine.Pin.IN)
    print('COEXIST_STOPPED_PIO_INPUT_NF_GUARD_RESTORED')
