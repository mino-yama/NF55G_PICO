import csv
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ate_server import ATEServer
from src.frame import build_frame
from src.logger import Logger, LoggerError, MemorySDSink
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockUART, MockNF55GScenario, ScenarioStep
from src.nf55_protocol import NF55Protocol, IDLE
from src.pico_clock import SystemClock
from src.rtc_driver import DS3231RTC, FakeRTCDevice
from src.sd_card import SDCard
from src.sd_sink import FileSDSink, csv_line


class BytePort:
    def __init__(self, rx=b'', max_write=10000):
        self.rx = bytearray(rx)
        self.tx = bytearray()
        self.max_write = max_write

    def any(self):
        return len(self.rx)

    def read(self, count):
        data = bytes(self.rx[:count])
        del self.rx[:count]
        return data

    def write(self, data):
        count = min(self.max_write, len(data))
        self.tx.extend(data[:count])
        return count


class HostFS:
    stat = staticmethod(os.stat)
    mkdir = staticmethod(os.mkdir)
    listdir = staticmethod(os.listdir)
    remove = staticmethod(os.remove)
    rename = staticmethod(os.replace)

    def __init__(self):
        self.capacity = 1000000
        self.free = 900000

    def statvfs(self, path):
        return (1, 1, self.capacity, self.free, self.free, 0, 0, 0, 0, 255)


class RuntimeIntegrationTests(unittest.TestCase):
    def protocol(self, steps=(), clock=None):
        clock = clock or FakeClock()
        uart = MockUART(clock, MockNF55GScenario(steps))
        return NF55Protocol(uart, clock=clock), uart

    def test_pico_ticks_wrap_and_protocol_timeout(self):
        class Timer:
            now = 240
            def ticks_ms(self):
                return self.now % 256
            def ticks_diff(self, new, old):
                return (new - old + 128) % 256 - 128
            def sleep_ms(self, ms):
                self.now += ms
        clock = SystemClock(Timer())
        protocol, _ = self.protocol(clock=clock)
        result = protocol.transact('D1', expected_length=15)
        self.assertEqual(result.error, 'ACK_TIMEOUT')
        self.assertEqual(result.command_retry_count, 1)
        self.assertGreaterEqual(result.elapsed_ms, 400)
        self.assertLess(result.elapsed_ms, 410)
        self.assertEqual(protocol.state, IDLE)

    def test_eb_before_ack_and_response_is_separate_from_status(self):
        event = build_frame('EB', '1' * 10 + '2' * 10)
        protocol, uart = self.protocol([ScenarioStep(((0, event), (5, b'\x06'),
                                                     (10, event), (20, build_frame('D1', '0' * 15))))])
        app = FixtureApp(protocol=protocol)
        app.cache.validate('STATUS', {'PS_ON': True}, 'OLD')
        result = protocol.transact('D1', expected_length=15)
        self.assertTrue(result.ok)
        self.assertEqual(result.elapsed_ms, 20)
        self.assertEqual(result.command_retry_count, 0)
        self.assertEqual(result.response_retry_count, 0)
        self.assertEqual(len(protocol.eb_events), 2)
        self.assertEqual(protocol.eb_events[0]['data'], {'CURRENT_RAW': '1' * 10, 'CHANGE_RAW': '2' * 10})
        self.assertEqual(app.cache.get('STATUS'), {'PS_ON': True})
        self.assertEqual(uart.tx_log[1:], [b'\x06'] * 3)

    def test_eb_does_not_extend_original_t2(self):
        event = build_frame('EB', '0' * 20)
        step = ScenarioStep(((0, b'\x06'), (10, event), (20, event), (29, event)))
        protocol, _ = self.protocol([step, step])
        result = protocol.transact('D1', t2_ms=30, expected_length=15)
        self.assertEqual(result.error, 'RESP_TIMEOUT')
        self.assertEqual(result.command_retry_count, 1)
        self.assertEqual(result.response_retry_count, 0)
        self.assertTrue(result.ambiguous)
        self.assertLessEqual(result.elapsed_ms, 62)
        self.assertEqual(len(protocol.eb_events), 6)

    def test_bad_eb_and_retry_do_not_consume_response_retry(self):
        bad = bytearray(build_frame('EB', '0' * 20))
        bad[-1] = ord('Z')
        good = build_frame('EB', '0' * 20)
        protocol, uart = self.protocol([ScenarioStep(((0, b'\x06'), (1, bad),
                                                      (2, good), (3, build_frame('D1', '0' * 15))))])
        result = protocol.transact('D1', expected_length=15)
        self.assertTrue(result.ok)
        self.assertEqual(result.response_retry_count, 0)
        self.assertEqual(uart.tx_log[1:], [b'\x15', b'\x06', b'\x06'])

    def test_idle_fragmented_eb_bounded_queue_no_status_promotion(self):
        protocol, uart = self.protocol()
        app = FixtureApp(protocol=protocol)
        app.cache.validate('STATUS', {'PS_ON': False}, 'D1')
        raw = build_frame('EB', 'F' * 20)
        uart.enqueue_rx(raw[:4])
        app.service_once()
        self.assertTrue(protocol.communication_busy)
        uart.enqueue_rx(raw[4:])
        app.service_once()
        self.assertFalse(protocol.communication_busy)
        uart.enqueue_rx(raw * 35)
        protocol.service_idle(byte_budget=2000)
        self.assertEqual(len(protocol.eb_events), 32)
        self.assertEqual(protocol.events.drop_count, 4)
        self.assertEqual(app.cache.get('STATUS'), {'PS_ON': False})
        self.assertEqual(uart.tx_log, [b'\x06'] * 36)

    def test_idle_partial_frame_timeout_unblocks_scheduler(self):
        protocol, uart = self.protocol()
        uart.enqueue_rx(b'\x02EB00')
        protocol.service_idle()
        self.assertTrue(protocol.communication_busy)
        protocol.clock.advance_ms(101)
        protocol.service_idle()
        self.assertFalse(protocol.communication_busy)

    def test_busy_reentry_and_fu_never_transmit(self):
        protocol, uart = self.protocol([ScenarioStep.ack_response('D1', '0' * 15, response_delay_ms=5)])
        nested = []
        def pump():
            if not nested:
                nested.append(protocol.transact('D5'))
        protocol.poll_hook = pump
        result = protocol.transact('D1', expected_length=15)
        self.assertTrue(result.ok)
        self.assertEqual(nested[0].error, 'BUSY')
        self.assertFalse(nested[0].ambiguous)
        before = list(uart.tx_log)
        for command in ('FU', b'FU', bytearray(b'FU'), 'fu'):
            self.assertEqual(protocol.transact(command).error, 'FU_DISABLED')
        self.assertEqual(before, uart.tx_log)

    def test_short_uart_write_reports_ambiguous_and_recovers(self):
        protocol, uart = self.protocol()
        original = uart.write
        uart.write = lambda data: 0
        result = protocol.transact('D1', expected_length=15)
        self.assertEqual(result.error, 'UART')
        self.assertTrue(result.ambiguous)
        self.assertFalse(protocol.busy)
        self.assertEqual(protocol.state, IDLE)
        uart.write = original
        uart.scenario.add(ScenarioStep.ack_response('D1', '0' * 15))
        self.assertTrue(protocol.transact('D1', expected_length=15).ok)

    def test_uart_exception_after_retry_preserves_counts(self):
        protocol, uart = self.protocol([ScenarioStep.ack_timeout()])
        original = uart.write
        def write(data):
            if uart.tx_log:
                raise OSError('disconnected')
            return original(data)
        uart.write = write
        result = protocol.transact('D1')
        self.assertEqual(result.command_retry_count, 1)
        self.assertTrue(result.ambiguous)
        self.assertGreaterEqual(result.elapsed_ms, 200)

    def test_nonascii_frame_cmd_uses_nak_not_python_exception(self):
        protocol, uart = self.protocol([ScenarioStep(((0, b'\x06'), (1, build_frame(b'\xff1', '0' * 15))))])
        result = protocol.transact('D1', expected_length=15)
        self.assertEqual(result.error, 'FINAL_BCC_FRAME')
        self.assertTrue(result.ambiguous)
        self.assertIn(b'\x15', uart.tx_log)

    def test_failed_nf_uart_does_not_block_local_ate_diagnostics(self):
        protocol, uart = self.protocol()
        def failed_any():
            raise OSError('UART error')
        uart.any = failed_any
        ate = BytePort(b'*IDN?\r\n')
        app = FixtureApp(protocol=protocol, ate_uart=ate)
        app.service_once()
        self.assertEqual(bytes(ate.tx), b'NF55G_PICO_FIXTURE,Rev.0\r\n')

    def test_fragmented_crlf_and_short_ate_writes(self):
        ate = BytePort(b'*ID', max_write=2)
        app = FixtureApp(ate_uart=ate)
        app.service_once()
        self.assertEqual(ate.tx, b'')
        ate.rx.extend(b'N?\r')
        app.service_once()
        self.assertEqual(ate.tx, b'')
        ate.rx.extend(b'\nFW_UPDATE\r\n')
        for _ in range(60):
            app.service_once()
        self.assertEqual(bytes(ate.tx), b'NF55G_PICO_FIXTURE,Rev.0\r\nERR:FU_DISABLED\r\n')

    def test_overlength_and_non_ascii_recover_at_crlf(self):
        ate = BytePort(b'A' * 513 + b'\r\n\xff\r\n*IDN?\r\n')
        app = FixtureApp(ate_uart=ate)
        for _ in range(20):
            app.service_once()
        self.assertEqual(bytes(ate.tx), b'ERR:LINE_TOO_LONG\r\nERR:ASCII\r\nNF55G_PICO_FIXTURE,Rev.0\r\n')

    def test_command_received_during_transaction_runs_after_response(self):
        protocol, nf = self.protocol([ScenarioStep.ack_response('D1', '0' * 15, response_delay_ms=40)])
        ate = BytePort(b'STATUS_REFRESH\r\n')
        app = FixtureApp(ate_uart=ate, protocol=protocol)
        original = protocol.poll_hook
        injected = []
        def pump():
            if protocol.clock.ticks_ms() >= 10 and not injected:
                ate.rx.extend(b'PS_ON?\r\nFW_UPDATE\r\n')
                injected.append(True)
            original()
        protocol.poll_hook = pump
        for _ in range(5):
            app.service_once()
        self.assertEqual(bytes(ate.tx), b'OK\r\n0\r\nERR:FU_DISABLED\r\n')
        self.assertEqual(len([x for x in nf.tx_log if x.startswith(b'\x02')]), 1)

    def test_sd_never_runs_during_nf_transaction_or_pending_rx(self):
        protocol, nf = self.protocol([ScenarioStep.ack_response('D1', '0' * 15, response_delay_ms=50)])
        sink = MemorySDSink()
        logger = Logger(sink, clock=protocol.clock, flush_record_count=1)
        app = FixtureApp(protocol=protocol, logger=logger)
        logger.test_start()
        original = protocol.poll_hook
        def pump():
            logger.service()
            logger.force_drain()
            self.assertFalse(logger.test_end())
            self.assertEqual(sink.write_count, 0)
            self.assertEqual(sink.flush_count, 0)
            original()
        protocol.poll_hook = pump
        self.assertEqual(app.execute_ate_line('STATUS_REFRESH'), 'OK')
        nf.enqueue_rx(build_frame('EB', '0' * 20)[:4])
        app.service_once()
        self.assertEqual(sink.write_count, 0)
        protocol.clock.advance_ms(101)
        app.service_once()
        self.assertGreater(sink.write_count, 0)

    def test_logger_failure_does_not_stop_ate_or_nf_and_reinit_recovers(self):
        protocol, _ = self.protocol([ScenarioStep.ack_response('D1', '0' * 15)])
        ate = BytePort()
        sink = MemorySDSink()
        logger = Logger(sink, clock=protocol.clock, flush_record_count=1)
        app = FixtureApp(ate_uart=ate, protocol=protocol, logger=logger)
        logger.test_start()
        sink.flush_blocked = True
        logger.log(detail='fault')
        app.service_once()
        self.assertEqual(logger.status(), 'WRITE_ERR')
        ate.rx.extend(b'STATUS_REFRESH\r\nPS_ON?\r\n')
        for _ in range(3):
            app.service_once()
        self.assertEqual(bytes(ate.tx), b'OK\r\n0\r\n')
        sink.flush_blocked = False
        self.assertEqual(app.execute_ate_line('SD_REINIT'), 'OK')
        self.assertFalse(logger.active)
        self.assertTrue(logger.test_start())

    def test_sd_actual_file_csv_timestamp_and_collision(self):
        with tempfile.TemporaryDirectory() as folder:
            sink = FileSDSink(folder, fs=HostFS())
            sink.mount()
            rtc = DS3231RTC(FakeRTCDevice())
            logger = Logger(sink, clock=FakeClock(), rtc=rtc)
            self.assertTrue(logger.test_start())
            logger.log(detail='a,"b"\r\nc')
            self.assertTrue(logger.test_end())
            path = Path(sink.open_filename)
            self.assertEqual(path.name, '20260901_000000.csv')
            with path.open(newline='') as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(rows[1][-1], 'a,"b"\r\nc')
            self.assertFalse(logger.test_start())
            self.assertEqual(logger.status(), 'FILE_EXISTS')
            self.assertEqual(len(list(path.parent.glob('*.csv'))), 1)

    def test_file_sink_busy_guard_blocks_open_write_flush_close_and_reinit(self):
        with tempfile.TemporaryDirectory() as folder:
            busy = [False]
            sink = FileSDSink(folder, fs=HostFS(), busy=lambda: busy[0])
            sink.mount()
            sink.open('20260910_090000.csv')
            busy[0] = True
            for call in (lambda: sink.open('20260910_090001.csv'), lambda: sink.write_record(['x']),
                         sink.flush, sink.close, sink.reinit, sink.usage):
                with self.assertRaisesRegex(LoggerError, 'COMM_BUSY'):
                    call()
            busy[0] = False
            sink.close()

    def test_file_sink_mount_failure_and_unowned_bank_are_not_adopted(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'BANK_A').mkdir()
            existing = Path(folder, 'BANK_A', '20260901_000000.csv')
            existing.write_text('precious')
            sink = FileSDSink(folder, fs=HostFS())
            with self.assertRaises(LoggerError):
                sink.mount()
            self.assertEqual(existing.read_text(), 'precious')

    def test_bank_rotation_and_reserve(self):
        with tempfile.TemporaryDirectory() as folder:
            fs = HostFS()
            sink = FileSDSink(folder, fs=fs)
            sink.mount()
            old = Path(folder, 'BANK_B', '20260901_000000.csv')
            old.write_text('old')
            other = Path(folder, 'BANK_B', 'notes.txt')
            other.write_text('keep')
            sink.bank_bytes['BANK_A'] = fs.capacity * 0.45
            sink.open('20260910_090000.csv')
            self.assertEqual(sink.bank, 'BANK_B')
            self.assertFalse(old.exists())
            self.assertEqual(other.read_text(), 'keep')
            sink.close()
            restarted = FileSDSink(folder, fs=fs)
            restarted.mount()
            self.assertEqual(restarted.bank, 'BANK_B')
            fs.free = 90000
            with self.assertRaisesRegex(LoggerError, 'FULL'):
                sink.open('20260910_090001.csv')

    def test_sd_io_error_latches_and_reinit_recovers(self):
        with tempfile.TemporaryDirectory() as folder:
            sink = FileSDSink(folder, fs=HostFS())
            sink.mount()
            sink.open('20260910_090000.csv')
            sink.file.close()
            class Broken:
                def write(self, data):
                    raise OSError(5, 'injected block failure')
                def close(self):
                    raise OSError(5, 'injected close failure')
            sink.file = Broken()
            logger = Logger(sink, clock=FakeClock())
            logger.active = True
            logger.log(detail='fault')
            self.assertEqual(logger.force_drain(), 0)
            self.assertEqual(logger.status(), 'WRITE_ERR')
            self.assertEqual(logger.drop_count, 1)
            self.assertTrue(logger.reinit())
            self.assertEqual(logger.status(), 'OK')

    def test_sd_csd_capacity_and_ioctl(self):
        csd = bytearray(16)
        csd[0] = 0x40
        csd[8], csd[9] = 0xff, 0xff
        self.assertEqual(SDCard.capacity_sectors(csd), 67108864)
        card = SDCard.__new__(SDCard)
        card.sectors = 67108864
        self.assertEqual(card.ioctl(4, 0), 67108864)
        self.assertEqual(card.ioctl(5, 0), 512)

    def test_sd_busy_wait_is_bounded(self):
        class SPI:
            reads = 0
            def write(self, data):
                pass
            def read(self, size, fill):
                self.reads += 1
                return b'\x05' if self.reads == 1 else b'\x00'
        levels = []
        card = SDCard.__new__(SDCard)
        card.spi = SPI()
        card.cs = levels.append
        card.clock = FakeClock()
        with self.assertRaisesRegex(OSError, 'busy timeout'):
            card.write(0xfe, b'0' * 512)
        self.assertEqual(card.clock.ticks_ms(), 1000)
        self.assertEqual(levels[-1], 1)

    def test_response_at_deadline_is_accepted_and_after_is_not(self):
        for delay, expected in ((100, True), (101, False)):
            protocol, _ = self.protocol([ScenarioStep.ack_response('D1', '0' * 15, response_delay_ms=delay)])
            result = protocol.transact('D1', t2_ms=100, expected_length=15)
            self.assertEqual(result.ok, expected)
            if not expected:
                self.assertTrue(result.ambiguous)

    def test_eb_during_response_retry_preserves_retry_counters(self):
        bad = bytearray(build_frame('D1', '0' * 15))
        bad[-1] = ord('Z')
        step = ScenarioStep(((0, b'\x06'), (1, bad)), response_retry_outputs=(
            (10, build_frame('EB', '0' * 20)), (20, build_frame('D1', '0' * 15))))
        protocol, uart = self.protocol([step])
        result = protocol.transact('D1', expected_length=15)
        self.assertTrue(result.ok)
        self.assertEqual((result.command_retry_count, result.response_retry_count), (0, 1))
        self.assertEqual(uart.tx_log[1:], [b'\x15', b'\x06', b'\x06'])

    def test_wrong_length_and_nonhex_eb_never_enter_event_queue(self):
        protocol, uart = self.protocol()
        uart.enqueue_rx(build_frame('EB', '0' * 19) + build_frame('EB', 'Z' * 20))
        protocol.service_idle(byte_budget=128)
        self.assertEqual(protocol.eb_events, [])
        self.assertEqual(uart.tx_log, [b'\x15', b'\x15'])

    def test_pending_flush_resumes_after_communication(self):
        busy = [False]
        class Sink(MemorySDSink):
            def write_record(self, row):
                super().write_record(row)
                busy[0] = True
        sink = Sink()
        logger = Logger(sink, clock=FakeClock(), busy=lambda: busy[0], flush_record_count=1)
        logger.test_start()
        logger.log(detail='one row')
        self.assertEqual(logger.service(), 1)
        self.assertEqual(logger.queue, [])
        self.assertEqual(sink.flush_count, 0)
        busy[0] = False
        logger.service()
        self.assertEqual(sink.flush_count, 1)

    def test_logger_flush_close_faults_do_not_escape(self):
        class Sink(MemorySDSink):
            def flush(self):
                raise LoggerError('WRITE_ERR')
            def close(self):
                raise LoggerError('WRITE_ERR')
        sink = Sink()
        logger = Logger(sink, clock=FakeClock(), flush_record_count=1)
        app = FixtureApp(logger=logger)
        logger.test_start()
        logger.log(detail='fault')
        app.service_once()
        self.assertEqual(logger.status(), 'WRITE_ERR')
        self.assertEqual(app.execute_ate_line('TEST_END'), 'ERR:WRITE_ERR')
        self.assertEqual(app.execute_ate_line('*IDN?'), 'NF55G_PICO_FIXTURE,Rev.0')

    def test_ate_busy_does_not_service_sd(self):
        ate = BytePort(b'*IDN?\r\n', max_write=0)
        sink = MemorySDSink()
        logger = Logger(sink, clock=FakeClock(), flush_record_count=1)
        app = FixtureApp(ate_uart=ate, logger=logger)
        logger.test_start()
        logger.log(detail='waiting')
        for _ in range(10):
            app.service_once()
        self.assertEqual(sink.write_count, 0)
        ate.max_write = 100
        app.service_once()
        self.assertEqual(sink.write_count, 1)

    def test_rtc_failure_does_not_stop_nf_or_ate(self):
        rtc = DS3231RTC(FakeRTCDevice(present=False))
        protocol, _ = self.protocol([ScenarioStep.ack_response('D1', '0' * 15)])
        app = FixtureApp(protocol=protocol, rtc=rtc)
        app.service_once()
        self.assertEqual(app.logger.timestamp_snapshot, '')
        self.assertEqual(app.execute_ate_line('STATUS_REFRESH'), 'OK')
        self.assertEqual(app.execute_ate_line('FW_UPDATE'), 'ERR:FU_DISABLED')

    def test_cont_rollover_uses_new_rtc_filename_without_losing_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            sink = FileSDSink(folder, fs=HostFS())
            sink.mount()
            rtc = DS3231RTC(FakeRTCDevice())
            logger = Logger(sink, clock=FakeClock(), rtc=rtc, rollover_bytes=1, flush_record_count=1)
            self.assertTrue(logger.log_cont_start())
            first = sink.open_filename
            logger.log(detail='new file')
            self.assertEqual(logger.service(), 0)  # Never overwrite the same second.
            self.assertEqual(len(logger.queue), 1)
            rtc.set_from_ate('20260901_000001')
            self.assertEqual(logger.service(), 1)
            second = sink.open_filename
            self.assertNotEqual(first, second)
            self.assertTrue(logger.test_end())
            with open(second, newline='') as stream:
                self.assertEqual(list(csv.reader(stream))[1][-1], 'new file')


if __name__ == '__main__':
    unittest.main()
