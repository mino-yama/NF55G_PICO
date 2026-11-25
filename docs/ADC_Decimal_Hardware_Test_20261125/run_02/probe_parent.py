# サンプルS1.14B専用の校正診断。稼働中の親Picoが持つUARTを一時的に使う。
import binascii
import json
import machine
import sys

from src import config
from src.nf55_decode import decode_ar, decode_manufacturing
from src.nf55_protocol import NF55Protocol

assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
assert not app.logger.recovery_pending and app.protocol is not None
assert not app.server.pending and not app.server.tx

probe = NF55Protocol(app.protocol.uart, clock=app.clock)


def hex_bytes(value):
    return binascii.hexlify(value).decode().upper()


def capture(cmd, data, expected_length, t2_ms):
    events = []
    probe.trace_hook = lambda direction, raw: events.append((direction, hex_bytes(raw)))
    result = probe.transact(cmd, data, expected_length=expected_length, t2_ms=t2_ms)
    print('TRANSACTION|' + json.dumps({
        'cmd': cmd, 'sent_data': data.decode(), 'expected_data_length': expected_length,
        'diagnostic_t2_ms': t2_ms, 'ok': result.ok, 'error': result.error,
        'nak_reason': result.nak_reason, 'ambiguous': result.ambiguous,
        'command_retry_count': result.command_retry_count,
        'response_retry_count': result.response_retry_count,
        'elapsed_ms': result.elapsed_ms, 'raw_response_hex': hex_bytes(result.raw_response),
        'events': events,
    }))
    if not result.ok:
        raise RuntimeError('{} {}'.format(cmd, result.error))
    return result.response_data


words = globals().get('adc_test_words', ())
assert all(len(word) == 8 and all(c in '0123456789ABCDEF' for c in word) for word in words)
original_retry = config.MAX_COMMAND_RETRY
config.MAX_COMMAND_RETRY = 0
try:
    identity = decode_manufacturing(capture('D5', b'', 100, 100)[:50])
    print('IDENTITY|' + json.dumps(identity))
    assert identity['FW_REV'] == 'S1.14B' and identity['UNIT_SERIAL'] == '000001'
    before = decode_ar(capture('AR', b'', 140, 1000))
    print('BEFORE|' + json.dumps(before))
    if words:
        assert before == adc_expected_baseline, 'AR baseline changed before AD'
    for word in words:
        # レビュー版で4=BATT_CHG、1=Point 1。サンプルの実応答でも対象を確認する。
        sent = '41' + word
        try:
            response = capture('AD', sent.encode(), 16, 1000).decode()
        finally:
            app.cache.invalidate_many(('DATA', 'AR'))
        assert response.startswith('41'), 'AD response target/point mismatch'
        assert all(c in '0123456789ABCDEF' for c in response[2:8]), 'AD response ADC is not hex'
        current = decode_ar(capture('AR', b'', 140, 1000))
        changes = {name: (before[name], value) for name, value in current.items()
                   if before[name] != value}
        print('OBSERVATION|' + json.dumps({'value8': word, 'ad_response': response,
              'ad_calculated_value_is_hex': all(c in '0123456789ABCDEF' for c in response[8:]),
              'ar_adc': current['AR_BATT_CHG_P1_ADC'], 'ar_ref8': current['AR_BATT_CHG_P1_REF_RAW'],
              'changes': changes}))
        for name in changes:
            assert name.startswith('AR_BATT_CHG_P1_'), 'unexpected AR field change'
        assert current['AR_BATT_CHG_P1_ADC'] == int(response[2:8], 16), 'ADC readback mismatch'
        before = current
finally:
    config.MAX_COMMAND_RETRY = original_retry
    probe.trace_hook = None

print('PROBE_COMPLETE')
