# COM5で実装候補を検証する。製品UARTのないFixtureAppをRAMだけで動かす。
import binascii
import struct
import sys
import time


class TracedQR(QR_PORT):
    def __init__(self):
        super().__init__()
        self.trace_line = bytearray()

    def read(self, count):
        data = super().read(count)
        for byte in data:
            if byte != 10:
                if len(self.trace_line) <= 153:
                    self.trace_line.append(byte)
                continue
            line, self.trace_line = bytes(self.trace_line), bytearray()
            if len(line) != 153 or line[:1] != b'@':
                continue
            seq, ms, kind, _, _, size, payload = struct.unpack('<IIBBBB64s', binascii.unhexlify(line[1:]))
            if kind == 14 and size == 24:
                _, _, drops, reads, hid, flags = struct.unpack('<6I', payload[:24])
                print('QR_ATE_HEALTH|{}|{}|{}|{}|{}|{}'.format(seq, ms, drops, reads, hid, flags))
            if kind == 16 and size == 25:
                print('QR_ATE_ACK|{}|{}|{}|{}'.format(seq, ms, payload[:24].decode(), payload[24]))
            if kind == 17 and size == 59:
                print('QR_ATE_TEXT|{}|{}|{}'.format(seq, ms, payload[:24].decode()))
        return data


original = sys.modules['src.main'].active_app
assert not original.logger.test_running and not original.logger.active and not original._comm_busy()
orig_rx = original.qr_write.transport
assert orig_rx is not None and original.logger.sd_sink.status == 'OK'
candidate = port = None
orig_rx.close()
try:
    port = TracedQR()
    # 実機UARTの照合を保守USBのCSV出力と分離する。COM5とHOSTの原文はPCに採取。
    logger = type(original.logger)(clock=original.clock)
    candidate = CANDIDATE_APP(ate_uart=original.ate_uart, logger=logger, clock=original.clock,
                              qr_transport=port)
    candidate.qr_write = QR_SESSION(candidate.clock, candidate.qr_write.nonce, port, arm_host=True)
    assert candidate.protocol is None and candidate.dispatcher.protocol is None
    print('QR_ATE_PARENT_READY')
    start = time.ticks_ms()
    seen_trial = False
    while time.ticks_diff(time.ticks_ms(), start) < 260000:
        candidate.service_once()
        if candidate.logger.test_running:
            seen_trial = True
        if seen_trial and not candidate.logger.test_running and not candidate.server.has_work():
            break
        time.sleep_ms(1)
    print('QR_ATE_PARENT_END', seen_trial, candidate.logger.drop_count)
finally:
    if candidate is not None and candidate.logger.test_running:
        candidate.execute_ate_line('TEST_END')
    if port is not None:
        port.close()
    orig_rx.__init__(rx_pin=9, baudrate=115200, sm_id=0, tx_idle_pin=None, buffer_size=2048)
