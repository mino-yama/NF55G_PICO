"""再STARTのファイル分離・QR失効・保存異常・通信優先を確認する。"""
import csv
from pathlib import Path
import tempfile
import unittest

from src.logger import Logger, MemorySDSink, LoggerError
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockUART, MockNF55GScenario, ScenarioStep
from src.nf55_protocol import NF55Protocol
from src.rtc_driver import DS3231RTC, FakeRTCDevice
from src.sd_sink import FileSDSink
from tests.test_runtime_integration import HostFS
from tests.test_decoder_complete import d0_payload

QR = 'US250A-CGXE-009491-10101A2623000001'


class TrialRestartTests(unittest.TestCase):
    def app(self, sink=None):
        clock = FakeClock()
        return FixtureApp(clock=clock, logger=Logger(sink or MemorySDSink(), clock=clock,
                                                     rtc=DS3231RTC(FakeRTCDevice())))

    def test_three_starts_same_second_create_separate_csv_and_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            sink = FileSDSink(folder, fs=HostFS())
            sink.mount()
            app = self.app(sink)
            for number in range(1, 4):
                self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
                self.assertEqual(app.logger.trial_id, 'T{:06d}'.format(number))
                app.logger.log(category='MARK', detail='attempt{}'.format(number))
                if number == 1:
                    app.accept_qr(QR)
            self.assertEqual(app.execute_ate_line('TEST_END'), 'OK')
            paths = sorted(Path(folder, 'BANK_A').glob('*.csv'))
            self.assertEqual(len(paths), 3)
            self.assertEqual(len({p.name for p in paths}), 3)
            marks = []
            for path in paths:
                with path.open(newline='') as stream:
                    rows = list(csv.DictReader(stream))
                marks.extend(r['detail'] for r in rows if r['category'] == 'MARK')
                self.assertEqual(sum(r['category'] == 'MARK' for r in rows), 1)
                self.assertTrue(any(r['event'] == 'TRIAL_START' for r in rows))
                self.assertTrue(any(r['event'] == 'TRIAL_END_REQUEST' for r in rows))
            self.assertEqual(sorted(marks), ['attempt1', 'attempt2', 'attempt3'])
            self.assertEqual([h['reason'] for h in app.logger.test_history],
                             ['NEXT_TEST_START', 'NEXT_TEST_START', 'TEST_END'])
            self.assertEqual([h['serial'] for h in app.logger.test_history], ['000001', None, None])
            self.assertEqual(app.logger.drop_count, 0)
            # 再起動・remount後も旧ファイルへ追記しない。S/N付き名も採番対象。
            before = {p.name: p.read_bytes() for p in paths}
            restarted = FileSDSink(folder, fs=HostFS())
            restarted.mount()
            self.assertEqual(restarted.bank_bytes['BANK_A'], sum(len(v) for v in before.values()))
            other = self.app(restarted)
            self.assertEqual(other.execute_ate_line('TEST_START'), 'OK')
            self.assertEqual(other.logger.trial_id, 'T000004')
            other.execute_ate_line('TEST_END')
            for name, content in before.items():
                self.assertEqual(Path(folder, 'BANK_A', name).read_bytes(), content)

    def test_sc_refresh_query_ten_seconds_restart_invalidates_without_nf_send(self):
        clock = FakeClock()
        peer = MockNF55GScenario([ScenarioStep.ack_response('SC'),
                                 ScenarioStep.ack_response('D0', d0_payload())])
        uart = MockUART(clock, peer)
        app = FixtureApp(protocol=NF55Protocol(uart, clock=clock))
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        self.assertEqual(app.execute_ate_line('CLOCK_SYNC 261111093614'), 'OK')
        self.assertEqual(app.execute_ate_line('DATA_REFRESH'), 'OK')
        self.assertNotEqual(app.execute_ate_line('VOUT12?'), 'ERR:CACHE_INVALID')
        clock.advance_ms(10000)
        sent = list(uart.tx_log)
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        self.assertEqual(app.execute_ate_line('VOUT12?'), 'ERR:CACHE_INVALID')
        self.assertEqual(uart.tx_log, sent)
        app.execute_ate_line('TEST_END')
        self.assertEqual(len(app.logger.sd_sink.files), 2)

    def test_qr_partial_and_ready_are_not_inherited(self):
        app = self.app()
        app.execute_ate_line('TEST_START')
        app.qr_reader.start(0)
        app.qr_reader.feed(QR[:20].encode(), 1)
        app.cache.validate('INFO', {'UNIT_SERIAL': '000001'}, 'D5')
        app.execute_ate_line('TEST_START')
        app.qr_reader.feed((QR[20:] + '\n').encode(), 2)
        self.assertIsNone(app.logger.session_serial)
        self.assertEqual(app.qr_reader.command('QR_GET', 2), 'ERR:CACHE_INVALID')
        self.assertEqual(app.execute_ate_line('UNIT_SERIAL?'), 'ERR:CACHE_INVALID')
        app.qr_reader.start(3)
        app.qr_reader.feed((QR + '\n').encode(), 4)
        self.assertEqual(app.logger.session_serial, '000001')
        app.execute_ate_line('TEST_START')
        self.assertIsNone(app.logger.session_serial)
        self.assertIsNone(app.qr_reader.fields)

    def test_communication_busy_rejects_without_state_or_file_changes(self):
        app = self.app()
        app.execute_ate_line('TEST_START')
        app.accept_qr(QR)
        before = (app.logger.trial_id, app.logger.current_filename)
        app.logger.busy = lambda: True
        self.assertEqual(app.execute_ate_line('TEST_START'), 'ERR:BUSY')
        self.assertEqual((app.logger.trial_id, app.logger.current_filename), before)
        self.assertEqual(app.logger.session_serial, '000001')
        self.assertEqual(app.logger.sd_sink.close_count, 0)

    def test_busy_during_drain_defers_restart_and_preserves_old_queue(self):
        app = self.app()
        app.execute_ate_line('TEST_START')
        app.logger.log(category='MARK', detail='old')
        sink = app.logger.sd_sink
        original = sink.write_record
        busy = [False]
        def write(row):
            original(row)
            busy[0] = True
        sink.write_record = write
        app.logger.busy = lambda: busy[0]
        self.assertEqual(app.execute_ate_line('TEST_START'), 'ERR:BUSY')
        self.assertEqual(app.logger.trial_id, 'T000001')
        self.assertTrue(app.logger.test_running)
        self.assertEqual(sink.close_count, 0)
        sink.write_record = original
        busy[0] = False
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        app.execute_ate_line('TEST_END')
        new_rows = sink.files[app.logger.last_test_filename]
        self.assertFalse(any(row[1] == 'MARK' for row in new_rows))

    def test_sd_failure_is_archived_and_never_remounted_during_restart(self):
        app = self.app()
        app.execute_ate_line('TEST_START')
        app.logger.sd_sink.status = 'NO_CARD'
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        self.assertEqual(app.logger.trial_id, 'T000002')
        self.assertFalse(app.logger.active)
        self.assertTrue(app.logger.test_running)
        self.assertEqual(app.logger.sd_sink.reinit_count, 0)
        self.assertEqual(app.logger.test_history[0]['sd_status'], 'NO_CARD')
        self.assertIn('TEST_LOGGER=NO_CARD', app.execute_ate_line('PICO_SELF_CHECK?'))
        self.assertEqual(app.execute_ate_line('SD_REINIT'), 'ERR:BUSY')
        app.execute_ate_line('TEST_END')
        self.assertIsNone(app.logger.test_history[-1]['filename'])

    def test_close_failure_does_not_start_new_sd_write(self):
        class BadClose(MemorySDSink):
            def close(self):
                super().close()
                raise LoggerError('WRITE_ERR')
        app = self.app(BadClose())
        app.execute_ate_line('TEST_START')
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        self.assertEqual(app.logger.test_history[0]['sd_status'], 'WRITE_ERR')
        self.assertFalse(app.logger.active)
        self.assertEqual(len(app.logger.sd_sink.files), 1)

    def test_close_guard_comm_busy_retains_old_trial_and_serial(self):
        app = self.app()
        app.execute_ate_line('TEST_START')
        app.accept_qr(QR)
        sink = app.logger.sd_sink
        original = sink.close
        def defer():
            raise LoggerError('COMM_BUSY')
        sink.close = defer
        self.assertEqual(app.execute_ate_line('TEST_START'), 'ERR:BUSY')
        self.assertTrue(app.logger.test_running)
        self.assertEqual(app.logger.trial_id, 'T000001')
        self.assertEqual(app.logger.session_serial, '000001')
        self.assertEqual(app.logger.test_history, [])
        self.assertEqual(app.logger.status(), 'OK')
        sink.close = original
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        self.assertEqual(app.logger.test_history[0]['serial'], '000001')

    def test_missing_sd_three_starts_get_distinct_ids_without_recovery(self):
        sink = MemorySDSink()
        sink.status = 'NO_CARD'
        app = self.app(sink)
        for number in range(1, 4):
            self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
            self.assertEqual(app.logger.trial_id, 'T{:06d}'.format(number))
        app.execute_ate_line('TEST_END')
        self.assertEqual(sink.files, {})
        self.assertEqual(sink.reinit_count, 0)
        self.assertEqual(len(app.logger.test_history), 3)
        self.assertTrue(all(h['filename'] is None and h['sd_status'] == 'NO_CARD'
                            for h in app.logger.test_history))

    def test_rotation_recognizes_trial_and_serial_names_and_preserves_other_files(self):
        with tempfile.TemporaryDirectory() as folder:
            sink = FileSDSink(folder, fs=HostFS())
            sink.mount()
            old = Path(folder, 'BANK_B', '000001_20260901_000000_T000023.csv')
            old.write_text('old trial')
            legacy = Path(folder, 'BANK_B', '20260901_000000.csv')
            legacy.write_text('legacy')
            unrelated = Path(folder, 'BANK_B', '20260901_000000_Tbad.csv')
            unrelated.write_text('preserve')
            sink.mount()
            self.assertEqual(sink.trial_high_watermark, 23)
            sink.bank_bytes['BANK_A'] = sink.capacity_bytes
            app = self.app(sink)
            self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
            self.assertEqual(app.logger.trial_id, 'T000024')
            self.assertEqual(sink.bank, 'BANK_B')
            self.assertFalse(old.exists())
            self.assertFalse(legacy.exists())
            self.assertEqual(unrelated.read_text(), 'preserve')
            app.execute_ate_line('TEST_END')

    def test_cont_mode_is_not_replaced_and_history_is_bounded(self):
        app = self.app()
        app.execute_ate_line('LOG_CONT_START')
        self.assertEqual(app.execute_ate_line('TEST_START'), 'ERR:BUSY')
        app.execute_ate_line('LOG_CONT_STOP')
        for _ in range(11):
            self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        app.execute_ate_line('TEST_END')
        self.assertEqual(len(app.logger.test_history), 8)
        self.assertEqual(app.logger.history_drop_count, 3)


if __name__ == '__main__':
    unittest.main()
