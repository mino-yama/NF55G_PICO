# 親RAM上だけのRST診断。H照合のみを送り、7355向けQ/SCPIは送信しない。
# 診断後も同じ親nonce・PIOを使用し、親再起動による再bind故障を避ける。
import time
import binascii
from src.main import create_fixture_app
from src.external_instrument_contract import encode_frame
from src.external_instrument_link import FrameReader

app = create_fixture_app()
link = app.external_link
if link is None:
    raise RuntimeError('external link unavailable: ' + str(app.external_error))
reader = FrameReader()
print('RST_PROBE_STARTED parent=' + binascii.hexlify(link.parent_nonce).decode())
started = time.ticks_ms()
next_send = 0
ready_count = 0
last_boot = None
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
            # 管理診断のみ。READYを連続観測してから同じnonceで通常処理へ渡す。
            # この確認だけで、計測器内の遅着応答が全て排除されたとは扱わない。
            if (frame['kind'] == 'h' and frame['session'][:8] == link.parent_nonce and
                    frame['payload'].startswith(b'BFCF2EDB84B0B37F|meter-host-relay-') and
                    frame['payload'].endswith(b'|READY')):
                boot = frame['session'][8:]
                ready_count = ready_count + 1 if boot == last_boot else 1
                last_boot = boot
            else:
                ready_count = 0
    if ready_count >= 10:
        print('READY_STABLE samples=' + str(ready_count))
        break
    time.sleep_ms(2)
print('RST_PROBE_FINISHED errors=' + str(reader.errors))
print('NORMAL_RUNTIME_STARTED same_parent_nonce=1')
app.run()
