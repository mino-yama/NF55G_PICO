# 起動済み親RAMのapp/nonceを保持し、Host起動の切分けにHだけを送る。
# fault解除・通常Q・NF55G・SD操作は行わず、診断後はREPLで停止する。
import time
import binascii
from src.external_instrument_contract import encode_frame
from src.external_instrument_link import FrameReader

link = app.external_link
reader = FrameReader()
print('EXISTING_PARENT=' + binascii.hexlify(link.parent_nonce).decode())
print('PIO_ERROR_BEFORE=' + str(link.transport.take_error()))
started = time.ticks_ms()
next_send = 0
replies = 0
probe_ready_samples = 0
verified_host_session = None
while time.ticks_diff(time.ticks_ms(), started) < 120000:
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
                    frame['payload'].startswith(b'BFCF2EDB84B0B37F|meter-host-relay-20261122.1|')):
                replies += 1
                if frame['payload'].endswith(b'|READY'):
                    probe_ready_samples = probe_ready_samples + 1 if verified_host_session == frame['session'] else 1
                    verified_host_session = frame['session']
                else:
                    probe_ready_samples = 0
    if replies >= 3:
        break
    time.sleep_ms(2)
print('PROBE_FINISHED replies=' + str(replies) + ' errors=' + str(reader.errors))
print('PIO_ERROR_AFTER=' + str(link.transport.take_error()))
