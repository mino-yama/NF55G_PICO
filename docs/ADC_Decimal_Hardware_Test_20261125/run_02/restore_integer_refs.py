"""Apply the two operator-approved integer references to sample UNIT 000001."""

import binascii
import json
import machine
import sys

from src.nf55_decode import decode_ar, decode_manufacturing
from src.nf55_protocol import NF55Protocol


assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
assert not app.logger.active and not app.logger.test_running and not app._comm_busy()
assert not app.logger.recovery_pending and not app.server.pending and not app.server.tx
probe = NF55Protocol(app.protocol.uart, clock=app.clock)


def exchange(name, data, length, timeout):
    trace = []
    probe.trace_hook = lambda direction, raw: trace.append((direction, binascii.hexlify(raw).decode()))
    result = probe.transact(name, data, t2_ms=timeout, expected_length=length, allow_command_retry=False)
    print('TXN|' + json.dumps({'cmd': name, 'data': data.decode(), 'ok': result.ok, 'error': result.error,
                              'ambiguous': result.ambiguous, 'events': trace}))
    if not result.ok:
        raise RuntimeError('{} {}'.format(name, result.error))
    return result.response_data


identity = decode_manufacturing(exchange('D5', b'', 100, 100)[:50])
print('IDENTITY|' + json.dumps(identity))
assert (identity['FW_REV'], identity['UNIT_SERIAL']) == ('S1.14B', '000001')
before = decode_ar(exchange('AR', b'', 140, 1000))
print('BEFORE|' + json.dumps(before))

# 8.0 V -> IEEE754 41000000、1.0 A -> IEEE754 3F800000。書込先はどちらもP1。
for target, payload, expected in (('BATT_V', b'2141000000', '00000008'),
                                  ('BATT_CHG', b'413F800000', '00000001')):
    reply = exchange('AD', payload, 16, 1000)
    assert reply[:2] == payload[:2] and all(c in b'0123456789ABCDEF' for c in reply[2:8])
    current = decode_ar(exchange('AR', b'', 140, 1000))
    prefix = 'AR_' + target + '_P1_'
    print('CHECK|' + json.dumps({'target': target, 'adc': current[prefix + 'ADC'],
          'ref8': current[prefix + 'REF_RAW'], 'ad_adc': int(reply[2:8], 16)}))
    assert current[prefix + 'REF_RAW'] == expected and current[prefix + 'ADC'] == int(reply[2:8], 16)
    assert all(current[name] == value for name, value in before.items() if not name.startswith(prefix))
    before = current

print('AFTER|' + json.dumps(before))
print('INTEGER_RESTORE_COMPLETE')
