REV_BASELINE = None
REV_CASES = ()
"""Bounded on-device diagnostic for the sample-only REV read/write plan."""
import binascii
import json
import machine
import struct
import time

from src import main
from src.frame import build_frame
from src.nf55_command import build_control_command


app = main.active_app
protocol = app.protocol
session = app.qr_write
assert binascii.hexlify(machine.unique_id()) == b'69f7d45962cfdfad'
assert app.logger.sd_sink.status == 'OK' and not app.logger.test_running and not app._comm_busy()


def hx(raw):
    return binascii.hexlify(raw).decode()


def emit(event, **fields):
    print('REV_HIL|' + json.dumps(dict(event=event, parent_ms=time.ticks_ms(), **fields)))


class Guard:
    def __init__(self, inner):
        self.inner = inner
        self.allowed = None
        self.sent = False
        self.writes = 0

    def any(self):
        return self.inner.any()

    def read(self, count=1):
        return self.inner.read(count)

    def write(self, value):
        raw = bytes(value)
        if raw == self.allowed and not self.sent:
            self.sent = True
            if raw[1:3] == b'SS':
                self.writes += 1
        elif raw not in (b'\x06', b'\x15'):
            raise OSError('unexpected or repeated command')
        return self.inner.write(value)


class InjectedQR:
    def __init__(self):
        self.wire = b''

    def any(self):
        return len(self.wire)

    def read(self, count):
        prefix, self.wire = self.wire[:count], self.wire[count:]
        return prefix

    def take_error(self):
        return None


original_uart, original_trace = protocol.uart, protocol.trace_hook
original_qr = session.transport
guard = Guard(original_uart)
injected = InjectedQR()
events = []
case = 'BASE'


def trace(direction, raw):
    events.append((time.ticks_ms(), direction, hx(raw)))
    if original_trace:
        original_trace(direction, raw)


def exchange(cmd, data, action):
    guard.allowed, guard.sent = build_frame(cmd, data), False
    try:
        reply = action()
        tx = protocol.last_result
        emit('TRANSACTION', case=case, command=cmd, data_hex=hx(data),
             wire=events, ok=tx.ok, error=tx.error, nak_reason=tx.nak_reason,
             command_retry=tx.command_retry_count, response_retry=tx.response_retry_count,
             ambiguous=tx.ambiguous, elapsed_ms=tx.elapsed_ms,
             response_hex=hx(tx.raw_response), response_data_hex=hx(tx.response_data),
             ate_reply=reply if isinstance(reply, str) else None)
        return tx
    finally:
        guard.allowed = None
        del events[:]


def d5():
    tx = exchange('D5', b'', lambda: app.execute_ate_line('INFO_REFRESH'))
    assert tx.cmd == 'D5' and tx.ok and len(tx.response_data) == 100
    return tx.response_data


def write(data, action=None):
    if action is None:
        action = lambda: protocol.transact('SS', data, t2_ms=100, expected_length=0, allow_command_retry=False)
    return exchange('SS', data, action)


def write_qr(label, ss_data, seq):
    armed = app.execute_ate_line('QR_SCAN 5000')
    assert armed.startswith('OK:QR_ARMED:'), armed
    token = armed.split(':')[-1]
    first = label.encode('ascii')
    frame = b'@' + binascii.hexlify(struct.pack('<IIBBBB64s', seq, 1, 12, 1, 0, len(first), first)) + b'\n'
    # A distinct second record arrives in the same poll; the first record remains the write source.
    wrong = first[:29] + b'999999'
    frame += b'@' + binascii.hexlify(struct.pack('<IIBBBB64s', seq + 1, 2, 12, 1, 0, len(wrong), wrong)) + b'\n'
    injected.wire = frame
    app.service_once()
    get = app.execute_ate_line('QR_GET? ' + token)
    data = app.execute_ate_line('QR_DATA? ' + token)
    emit('QR', case=case, token=token, qr_text=label, qr_get=get, qr_data=data)
    assert get == 'OK:QR_GET:' + token + ':' + label
    assert data == 'OK:QR_DATA:' + token + ':' + hx(ss_data)
    return write(ss_data, lambda: app.execute_ate_line('QR_WRITE ' + token))


protocol.uart, protocol.trace_hook = guard, trace
baseline = None
opened = False
restored = None
try:
    baseline = d5()
    emit('BASELINE', hex=hx(baseline), ascii=baseline.decode('ascii'))
    if REV_BASELINE is not None:
        assert hx(baseline) == REV_BASELINE, 'product changed since baseline acquisition'
        assert baseline[:6] == b'S1.14B' and baseline[14:20] == b'000001'
        assert app.execute_ate_line('TEST_START') == 'OK'
        opened = True
        session.transport = injected
        for index, (case, mode, label, ss_hex) in enumerate(REV_CASES):
            before = d5()
            ss_data = binascii.unhexlify(ss_hex)
            tx = write_qr(label, ss_data, index * 2 + 1) if mode == 'qr' else write(ss_data)
            after = d5()
            emit('CASE', case=case, mode=mode, qr=label, ss_hex=ss_hex, before=hx(before), after=hx(after),
                 ok=tx.ok, error=tx.error, nak_reason=tx.nak_reason, ambiguous=tx.ambiguous,
                 command_retry=tx.command_retry_count, response_retry=tx.response_retry_count)
            if tx.ambiguous or (not tx.ok and case != 'REV-03') or before[:6] + before[20:] != after[:6] + after[20:]:
                raise RuntimeError('stop after communication or unexpected other-field change')
finally:
    try:
        if baseline is not None and guard.writes:
            case = 'REV-06'
            before = d5()
            ss_data = b'F' * 6 + baseline[6:20] + b'F' * 30
            if before[6:20] != baseline[6:20]:
                tx = write(ss_data)
                after = d5()
                emit('CASE', case=case, mode='restore', qr=None, ss_hex=hx(ss_data), before=hx(before), after=hx(after),
                     ok=tx.ok, error=tx.error, nak_reason=tx.nak_reason, ambiguous=tx.ambiguous,
                     command_retry=tx.command_retry_count, response_retry=tx.response_retry_count)
            else:
                after = before
            restored = after == baseline
            emit('RESTORE', target_hex=hx(baseline), actual_hex=hx(after), exact=restored)
    finally:
        protocol.uart, protocol.trace_hook = original_uart, original_trace
        session.transport = original_qr
        if opened:
            emit('END', reply=app.execute_ate_line('TEST_END'), drops=app.logger.drop_count, restored=restored)
