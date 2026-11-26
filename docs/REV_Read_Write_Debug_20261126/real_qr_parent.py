import binascii
import json
import machine
import time

from src import main


app = main.active_app
session = app.qr_write
assert binascii.hexlify(machine.unique_id()) == b'69f7d45962cfdfad'
assert not app.logger.test_running and not app._comm_busy() and app.logger.sd_sink.status == 'OK'
assert session.transport is not None


def ask(command):
    return app.execute_ate_line(command)


def emit(event, **fields):
    print('REAL_QR|' + json.dumps(dict(event=event, parent_ms=time.ticks_ms(), **fields)))


for label, raw, data in REAL_LABELS:
    assert ask('TEST_START') == 'OK'
    try:
        response = ask('QR_SCAN 60000')
        assert response.startswith('OK:QR_ARMED:'), response
        token = response.split(':')[-1]
        emit('SCAN_' + label, token=token)
        initial_ignored = session.ignored
        deadline = time.ticks_add(time.ticks_ms(), 62000)
        first = None
        duplicate_observed = False
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            app.service_once()
            if session.state == 'READY' and first is None:
                first = ask('QR_GET? ' + token)
                assert first == 'OK:QR_GET:' + token + ':' + raw, first
                emit('READ_' + label, reply=first)
                if label != 'A':
                    break
            if first and session.ignored > initial_ignored:
                duplicate_observed = True
                break
            if session.state == 'ERROR':
                break
            time.sleep_ms(1)
        final = ask('QR_GET? ' + token)
        preview = ask('QR_DATA? ' + token)
        emit('RESULT', label=label, token=token, first=first, final=final, preview=preview,
             duplicate_observed=duplicate_observed)
        assert final == 'OK:QR_GET:' + token + ':' + raw
        assert preview == 'OK:QR_DATA:' + token + ':' + data
    finally:
        emit('END', label=label, reply=ask('TEST_END'), drops=app.logger.drop_count)
    assert ask('QR_GET? ' + token) == 'ERR:QR_STALE_ID'
