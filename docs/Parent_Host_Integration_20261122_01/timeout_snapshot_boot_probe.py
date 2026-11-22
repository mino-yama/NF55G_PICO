# 新FW起動後のH照合だけを行う保守診断。機器Qは送らずREPLへ戻す。
# 旧transportを閉じた停止状態から、外部linkだけを再構築する。
import time
import binascii
import rp2
from src.external_instrument_link import ExternalInstrumentLink
from src.external_instrument_pio import ExternalPioUART
from src.external_instrument_contract import encode_frame
from src.external_instrument_link import FrameReader

assert not app.running
assert not app.logger.active
assert not app._comm_busy()
assert not rp2.StateMachine(4).active()
assert not rp2.StateMachine(5).active()
old_link = app.external_link
link = ExternalInstrumentLink(ExternalPioUART(), old_link.clock, old_link.parent_nonce, old_link.expected_chipid)
app.external_link = link
reader = FrameReader()
started = time.ticks_ms()
next_send = 0
ready_count = 0
verified_host_session = None
print('SNAPSHOT_PROBE_PARENT=' + binascii.hexlify(link.parent_nonce).decode())
while time.ticks_diff(time.ticks_ms(), started) < 30000:
    elapsed = time.ticks_diff(time.ticks_ms(), started)
    if elapsed >= next_send:
        wire = encode_frame(link.parent_nonce + bytes(8), 0, 'H', 0, 0, b'')
        offset = 0
        deadline = time.ticks_ms()
        while offset < len(wire) and time.ticks_diff(time.ticks_ms(), deadline) < 200:
            n = link.transport.write(wire[offset:])
            if n:
                offset += n
            time.sleep_ms(1)
        print('H_SENT ms=' + str(elapsed) + ' bytes=' + str(offset))
        next_send = elapsed + 1000
    if link.transport.any():
        for frame in reader.feed(link.transport.read(64) or b''):
            print('H_REPLY ms=' + str(elapsed) + ' session=' + binascii.hexlify(frame['session']).decode() + ' payload=' + repr(frame['payload']))
            if (frame['kind'] == 'h' and frame['session'][:8] == link.parent_nonce and
                    frame['payload'] == b'BFCF2EDB84B0B37F|meter-host-relay-20261122.2|READY'):
                ready_count = ready_count + 1 if verified_host_session == frame['session'] else 1
                verified_host_session = frame['session']
            else:
                ready_count = 0
    if ready_count >= 3:
        break
    time.sleep_ms(2)
print('SNAPSHOT_PROBE_FINISHED ready=' + str(ready_count) + ' errors=' + str(reader.errors))
assert ready_count >= 3
assert not reader.errors
assert link.transport.take_error() is None
# app.run()はPC側で開始する。HによりHostをbindした親nonceを維持する。
