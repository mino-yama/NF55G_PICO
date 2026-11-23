# ADC追加版の実ATE試験。既存app/sessionを使い、NF送信禁止・SD通信busyを観測する。
import machine
import time
import json
link = app.external_link
assert app.calibration_acquisition.link is link
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
assert app.protocol.uart is nf_guard and nf_guard.attempts == 0
assert link.transport._closed
nonce_before = link.parent_nonce
cache_before = {name:app.cache.metadata(name) for name in app.cache._entries}
link.transport = CaptureTransport()
sink = app.logger.sd_sink
original_write, original_flush = sink.write_record, sink.flush
sd_stats = {'writes':0, 'flushes':0, 'during_comm':0}


def checked_write(row):
    if app._comm_busy():
        sd_stats['during_comm'] += 1
        raise RuntimeError('SD write during acquisition')
    sd_stats['writes'] += 1
    return original_write(row)


def checked_flush():
    if app._comm_busy():
        sd_stats['during_comm'] += 1
        raise RuntimeError('SD flush during acquisition')
    sd_stats['flushes'] += 1
    return original_flush()


sink.write_record, sink.flush = checked_write, checked_flush
old_history = len(app.logger.test_history)
observed_history = old_history
log_paths = []
last_busy = app.clock.ticks_ms()
print('ADC_HIL_READY|' + nonce_before.hex())
started = time.ticks_ms()
try:
    while time.ticks_diff(time.ticks_ms(), started) < 45000:
        app.service_once()
        now = app.clock.ticks_ms()
        if app._comm_busy() or app.server.has_work():
            last_busy = now
        if len(app.logger.test_history) > observed_history:
            observed_history = len(app.logger.test_history)
            log_paths.append(sink.open_filename)
            last_busy = now
        if observed_history - old_history >= 2 and now - last_busy >= 700:
            break
        time.sleep_ms(1)
    assert link.parent_nonce == nonce_before
    assert cache_before == {name:app.cache.metadata(name) for name in app.cache._entries}
    assert nf_guard.attempts == 0
    print('ADC_HIL_DONE|' + json.dumps({'parent_nonce':nonce_before.hex(), 'host_info':link.host_info,
        'fault':link.fault, 'frame_errors':link.reader.errors, 'stale_frames':link.stale_frames,
        'nf_write_attempts':nf_guard.attempts, 'product_cache_unchanged':True,
        'sd_stats':sd_stats, 'drop':app.logger.drop_count, 'queue':len(app.logger.queue),
        'logger_active':app.logger.active, 'test_running':app.logger.test_running,
        'measurement_slots':len(app.measurements._values), 'log_paths':log_paths,
        'tx_hex':link.transport.tx.hex()}))
finally:
    if app.logger.test_running and not app._comm_busy():
        app.execute_ate_line('TEST_END')
    sink.write_record, sink.flush = original_write, original_flush
    link.transport.close()
    machine.Pin(12,machine.Pin.IN)
    machine.Pin(13,machine.Pin.IN)
    print('ADC_HIL_STOPPED_PIO_INPUT')
