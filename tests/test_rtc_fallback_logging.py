"""RTCなし・故障時も実ファイルsinkへ保存し、既存ログを上書きしないことを検証する。"""
import csv
import errno
import os
from pathlib import Path
import tempfile
import unittest

from src.cache_manager import CacheManager
from src.command_dispatcher import CommandDispatcher
from src.log_filename import log_identity
from src.logger import Logger, LoggerError, MemorySDSink
from src.main import FixtureApp
from src.mock_nf55g import FakeClock
from src.rtc_driver import DS3231RTC, FakeRTCDevice
from src.sd_sink import FileSDSink
from tests.test_runtime_integration import HostFS


class RTC:
    value = '20261128_100000'
    def datetime(self):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class RTCFallbackLoggingTests(unittest.TestCase):
    def sink(self, folder, fs=None, **kwargs):
        sink = FileSDSink(folder, fs=fs or HostFS(), **kwargs)
        sink.mount()
        return sink

    def test_no_rtc_test_and_serial_rename_save_actual_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            sink = self.sink(folder)
            logger = Logger(sink, clock=FakeClock())
            dispatcher = CommandDispatcher(None, CacheManager(), logger=logger)
            self.assertEqual(dispatcher.execute_logger('TEST_START').ate_response, 'OK')
            self.assertEqual(logger.current_filename, 'NO_RTC_T000001.csv')
            self.assertTrue(logger.active)
            self.assertEqual(logger.timestamp_snapshot, '')
            logger.log(category='MARK', detail='without time')
            self.assertTrue(logger.set_serial('000001'))
            self.assertTrue(logger.test_end())
            final = Path(folder, 'BANK_A', '000001_NO_RTC_T000001.csv')
            self.assertTrue(final.exists())
            with final.open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[-1]['detail'], 'without time')
            self.assertTrue(all(row['timestamp'] == '' for row in rows))
            self.assertTrue(all(len(row) == 14 for row in rows))
            self.assertEqual(logger.last_test_filename, final.name)
            self.assertEqual(logger.last_test_sd_status, 'OK')

    def test_restart_scans_both_banks_serial_names_zero_bytes_and_legacy(self):
        with tempfile.TemporaryDirectory() as folder:
            self.sink(folder)
            existing = {
                ('BANK_A', '20261127_010203_T000041.csv'): b'legacy',
                ('BANK_B', '000001_NO_RTC_T000099.csv'): b'preserve',
                ('BANK_B', 'NO_RTC_C000105.csv'): b'',
                ('BANK_A', 'NO_RTC_Cbad.csv'): b'foreign',
            }
            for (bank,name),data in existing.items():
                Path(folder,bank,name).write_bytes(data)
            sink = self.sink(folder)
            logger = Logger(sink,clock=FakeClock())
            self.assertTrue(logger.test_start())
            self.assertEqual(logger.trial_id, 'T000106')
            self.assertTrue(logger.set_serial('000002'))
            self.assertTrue(logger.test_end())
            logger = Logger(self.sink(folder),clock=FakeClock())
            self.assertTrue(logger.log_cont_start())
            self.assertEqual(logger.current_filename, 'NO_RTC_C000107.csv')
            self.assertTrue(logger.log_cont_stop())
            for (bank,name),data in existing.items():
                self.assertEqual(Path(folder,bank,name).read_bytes(),data)

    def test_invalid_and_failed_rtc_start_with_empty_timestamp(self):
        for value,status in ((OSError('I2C'),'READ_ERROR'),(ValueError('NO_RTC'),'READ_ERROR'),
                             ('20260230_000000','INVALID'),('20261128_246000','INVALID'),
                             ('bad','INVALID'),(None,'INVALID'),('２０２６１１２８_１０００００','INVALID')):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as folder:
                rtc=RTC(); rtc.value=value
                logger=Logger(self.sink(folder),rtc=rtc,clock=FakeClock())
                logger.timestamp_snapshot='old timestamp'
                self.assertTrue(logger.test_start())
                self.assertEqual(logger.current_filename,'NO_RTC_T000001.csv')
                self.assertEqual(logger.rtc_filename_status,status)
                self.assertEqual(logger.timestamp_snapshot,'')
                self.assertTrue(logger.test_end())

    def test_rtc_recovers_and_fails_without_renaming_open_test(self):
        with tempfile.TemporaryDirectory() as folder:
            rtc=RTC();rtc.value=OSError('I2C')
            logger=Logger(self.sink(folder),rtc=rtc,clock=FakeClock())
            self.assertTrue(logger.test_start())
            rtc.value='20261128_100000'
            self.assertEqual(logger.snapshot_time(),'20261128_100000')
            self.assertEqual(logger.current_filename,'NO_RTC_T000001.csv')
            logger.log(detail='after recovery')
            self.assertTrue(logger.test_end())
            self.assertTrue(logger.test_start())
            self.assertEqual(logger.current_filename,'20261128_100000_T000002.csv')
            rtc.value=OSError('lost')
            self.assertIsNone(logger.snapshot_time())
            logger.log(detail='after loss')
            self.assertTrue(logger.test_end())
            with Path(folder,'BANK_A','20261128_100000_T000002.csv').open(newline='') as stream:
                self.assertEqual(list(csv.DictReader(stream))[-1]['timestamp'],'')

    def test_cont_rollover_without_rtc_and_reboot_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            logger=Logger(self.sink(folder),clock=FakeClock(),rollover_bytes=1,flush_record_count=1)
            self.assertTrue(logger.log_cont_start())
            first=logger.current_filename
            logger.log(detail='rollover')
            self.assertEqual(logger.service(),1)
            self.assertEqual(logger.current_filename,'NO_RTC_C000002.csv')
            self.assertTrue(logger.log_cont_stop())
            logger=Logger(self.sink(folder),clock=FakeClock())
            self.assertTrue(logger.log_cont_start())
            self.assertEqual(logger.current_filename,'NO_RTC_C000003.csv')
            self.assertTrue(Path(folder,'BANK_A',first).exists())
            logger.log_cont_stop()

    def test_cont_rtc_loss_and_recovery_rollover_works(self):
        with tempfile.TemporaryDirectory() as folder:
            rtc=RTC()
            logger=Logger(self.sink(folder),rtc=rtc,clock=FakeClock(),rollover_bytes=1,flush_record_count=1)
            self.assertTrue(logger.log_cont_start())
            rtc.value=OSError('lost')
            logger.log(detail='lost');self.assertEqual(logger.service(),1)
            self.assertEqual(logger.current_filename,'NO_RTC_C000001.csv')
            rtc.value='20261128_100001'
            logger.log(detail='restored');self.assertEqual(logger.service(),1)
            self.assertEqual(logger.current_filename,'20261128_100001.csv')
            logger.log_cont_stop()

    def test_number_grows_past_six_digits_without_wrapping(self):
        with tempfile.TemporaryDirectory() as folder:
            self.sink(folder)
            Path(folder,'BANK_B','NO_RTC_C999999.csv').touch()
            logger=Logger(self.sink(folder),clock=FakeClock())
            self.assertTrue(logger.test_start())
            self.assertEqual(logger.current_filename,'NO_RTC_T1000000.csv')
            logger.test_end()

    def test_unknown_directory_entry_type_falls_back_to_stat_for_number(self):
        class UnknownTypeFS(HostFS):
            def ilistdir(self,path):
                for name in os.listdir(path):
                    yield (name,0,0)
        with tempfile.TemporaryDirectory() as folder:
            self.sink(folder)
            Path(folder,'BANK_B','NO_RTC_C000081.csv').touch()
            Path(folder,'BANK_B','NO_RTC_C000999.csv').mkdir()
            sink=self.sink(folder,fs=UnknownTypeFS())
            self.assertEqual(sink.log_high_watermark,81)
            logger=Logger(sink,clock=FakeClock())
            self.assertTrue(logger.test_start())
            self.assertEqual(logger.trial_id,'T000082')
            logger.test_end()

    def test_name_contract_is_shared_and_rejects_foreign_files(self):
        valid=('20261128_100000.csv','20261128_100000_T000001.csv',
               '000001_20261128_100000_T000001.csv','NO_RTC_T000001.csv',
               '000001_NO_RTC_T000001.csv','NO_RTC_C000002.csv')
        invalid=('NO_RTC_T1.csv','NO_RTC_Cbad.csv','NO_RTC_T000001.csv.bak',
                 '../NO_RTC_T000001.csv','NO_RTC_X000001.csv','12345_NO_RTC_T000001.csv')
        for name in valid+invalid:
            self.assertEqual(FileSDSink._log_name(name),name in valid)
            memory=MemorySDSink()
            if name in valid: memory.open(name)
            else:
                with self.assertRaises(LoggerError):memory.open(name)

    def test_rotation_counts_new_names_and_preserves_foreign_files_and_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            self.sink(folder)
            Path(folder,'BANK_B','000001_NO_RTC_T000041.csv').write_bytes(b'123')
            Path(folder,'BANK_B','NO_RTC_C000042.csv').write_bytes(b'45678')
            Path(folder,'BANK_B','NO_RTC_Cbad.csv').write_bytes(b'keep')
            Path(folder,'BANK_B','NO_RTC_C000999.csv').mkdir()
            sink=self.sink(folder)
            self.assertEqual(sink.bank_bytes['BANK_B'],8)
            self.assertEqual(sink.log_high_watermark,42)
            sink.bank_bytes['BANK_A']=sink.capacity_bytes
            logger=Logger(sink,clock=FakeClock())
            self.assertTrue(logger.test_start())
            self.assertEqual(logger.current_filename,'NO_RTC_T000043.csv')
            self.assertFalse(Path(folder,'BANK_B','NO_RTC_C000042.csv').exists())
            self.assertEqual(Path(folder,'BANK_B','NO_RTC_Cbad.csv').read_bytes(),b'keep')
            self.assertTrue(Path(folder,'BANK_B','NO_RTC_C000999.csv').is_dir())
            logger.test_end()

    def test_collision_after_mount_retries_without_deleting_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            sink=self.sink(folder)
            collision=Path(folder,'BANK_B','NO_RTC_T000001.csv')
            collision.write_bytes(b'old')
            logger=Logger(sink,clock=FakeClock())
            self.assertTrue(logger.test_start())
            self.assertEqual(logger.trial_id,'T000002')
            self.assertEqual(collision.read_bytes(),b'old')
            logger.test_end()

    def test_foreign_bank_rename_collision_preserves_both_files(self):
        with tempfile.TemporaryDirectory() as folder:
            sink=self.sink(folder);logger=Logger(sink,clock=FakeClock())
            self.assertTrue(logger.test_start())
            logger.log(detail='keep source');logger.set_serial('000001')
            collision=Path(folder,'BANK_B','000001_'+logger.current_filename)
            collision.write_bytes(b'keep target')
            self.assertFalse(logger.test_end())
            self.assertEqual(logger.last_test_sd_status,'FILE_EXISTS')
            self.assertEqual(logger.last_test_filename,'NO_RTC_T000001.csv')
            self.assertTrue(Path(folder,'BANK_A',logger.last_test_filename).exists())
            self.assertEqual(collision.read_bytes(),b'keep target')

    def test_collision_retry_is_bounded_and_preserves_all_eight_files(self):
        with tempfile.TemporaryDirectory() as folder:
            sink=self.sink(folder)
            for n in range(1,9):
                Path(folder,'BANK_B','NO_RTC_T{:06d}.csv'.format(n)).write_bytes(b'keep')
            logger=Logger(sink,clock=FakeClock())
            self.assertFalse(logger.test_start())
            self.assertEqual(logger.status(),'FILE_EXISTS')
            self.assertTrue(logger.test_running)
            self.assertFalse(logger.active)
            self.assertEqual(sink.log_high_watermark,8)
            self.assertEqual(list(Path(folder,'BANK_A').glob('*.csv')),[])
            self.assertTrue(all(p.read_bytes()==b'keep' for p in Path(folder,'BANK_B').glob('*.csv')))

    def test_rename_stat_error_preserves_original_name(self):
        class BrokenFS(HostFS):
            def stat(self,path):
                if path.rsplit('/',1)[-1].startswith('000001_NO_RTC_'):
                    raise OSError(errno.EIO,'rename target check failed')
                return os.stat(path)
        with tempfile.TemporaryDirectory() as folder:
            logger=Logger(self.sink(folder,fs=BrokenFS()),clock=FakeClock())
            logger.test_start();logger.log(detail='preserve');logger.set_serial('000001')
            self.assertFalse(logger.test_end())
            self.assertEqual(logger.last_test_sd_status,'WRITE_ERR')
            self.assertEqual(logger.last_test_filename,'NO_RTC_T000001.csv')
            self.assertTrue(Path(folder,'BANK_A',logger.last_test_filename).exists())

    def test_failed_rescan_revokes_previously_ready_namespace(self):
        class SwitchFS(HostFS):
            fail=False
            def listdir(self,path):
                if self.fail and path.endswith('BANK_B'):raise OSError(errno.EIO,'unreadable bank')
                return os.listdir(path)
        with tempfile.TemporaryDirectory() as folder:
            fs=SwitchFS();sink=self.sink(folder,fs=fs)
            self.assertTrue(sink.namespace_ready)
            fs.fail=True
            with self.assertRaises(LoggerError):sink.mount()
            self.assertFalse(sink.namespace_ready)
            with self.assertRaises(LoggerError):sink.reserve_log_number()

    def test_missing_ownership_marker_never_adopts_existing_logs(self):
        with tempfile.TemporaryDirectory() as folder:
            self.sink(folder)
            Path(folder,'BANK_B','NO_RTC_C000077.csv').touch()
            Path(folder,'BANK_B','.nf55_logger').unlink()
            sink=FileSDSink(folder,fs=HostFS())
            with self.assertRaises(LoggerError):sink.mount()
            self.assertFalse(sink.namespace_ready)
            self.assertFalse(Logger(sink,clock=FakeClock()).log_cont_start())
            self.assertTrue(Path(folder,'BANK_B','NO_RTC_C000077.csv').exists())

    def test_partial_scan_failure_does_not_publish_empty_namespace(self):
        class BrokenFS(HostFS):
            def listdir(self,path):
                if path.endswith('BANK_B'):raise OSError(errno.EIO,'read error')
                return os.listdir(path)
        with tempfile.TemporaryDirectory() as folder:
            self.sink(folder)
            sink=FileSDSink(folder,fs=BrokenFS())
            with self.assertRaises(LoggerError):sink.mount()
            self.assertFalse(sink.namespace_ready)
            logger=Logger(sink,clock=FakeClock())
            self.assertFalse(logger.test_start())
            self.assertTrue(logger.test_running)
            self.assertEqual(logger.status(),'MOUNT_ERR')
            self.assertIsNone(logger.current_filename)
            self.assertEqual(list(Path(folder).rglob('*.csv')),[])

    def test_stat_io_error_is_not_missing_file(self):
        class BrokenFS(HostFS):
            def stat(self,path):
                if path.endswith('NO_RTC_T000001.csv'):raise OSError(errno.EIO,'read error')
                return os.stat(path)
        with tempfile.TemporaryDirectory() as folder:
            sink=self.sink(folder,fs=BrokenFS());logger=Logger(sink,clock=FakeClock())
            self.assertFalse(logger.test_start())
            self.assertEqual(logger.status(),'OPEN_ERR')
            self.assertEqual(list(Path(folder).rglob('*.csv')),[])

    def test_busy_does_not_reserve_scan_write_or_rename(self):
        with tempfile.TemporaryDirectory() as folder:
            busy=[False];sink=self.sink(folder,busy=lambda:busy[0])
            logger=Logger(sink,clock=FakeClock(),busy=lambda:busy[0],flush_record_count=1)
            self.assertTrue(logger.test_start());logger.log(detail='wait');logger.set_serial('000001')
            before=sink.log_high_watermark
            busy[0]=True
            self.assertFalse(logger.test_start());self.assertEqual(logger.service(),0)
            self.assertFalse(logger.test_end());self.assertEqual(sink.log_high_watermark,before)
            self.assertEqual(logger.current_filename,'NO_RTC_T000001.csv')
            busy[0]=False;self.assertTrue(logger.test_end())

    def test_missing_serial_is_not_inherited_and_cont_is_not_renamed(self):
        with tempfile.TemporaryDirectory() as folder:
            sink=self.sink(folder);logger=Logger(sink,clock=FakeClock())
            logger.test_start();logger.set_serial('000001');logger.test_end()
            logger.test_start();self.assertIsNone(logger.session_serial);logger.test_end()
            self.assertEqual(logger.last_test_filename,'NO_RTC_T000002.csv')
            logger.log_cont_start();self.assertFalse(logger.set_serial('000002'))
            name=logger.current_filename;logger.log_cont_stop()
            self.assertTrue(Path(folder,'BANK_A',name).exists())

    def test_ate_and_nf_mock_continue_with_missing_rtc_and_actual_sink(self):
        from src.mock_nf55g import MockNF55GScenario, MockUART, ScenarioStep
        with tempfile.TemporaryDirectory() as folder:
            sink=self.sink(folder);clock=FakeClock()
            uart=MockUART(clock,MockNF55GScenario([ScenarioStep.ack_response('D1','0'*15)]))
            app=FixtureApp(nf55_uart=uart,clock=clock,logger=Logger(sink,clock=clock))
            self.assertEqual(app.execute_ate_line('TEST_START'),'OK')
            self.assertEqual(app.execute_ate_line('STATUS_REFRESH'),'OK')
            self.assertEqual(app.execute_ate_line('FW_UPDATE'),'ERR:FU_DISABLED')
            self.assertEqual(app.execute_ate_line('TEST_END'),'OK')
            self.assertTrue(app.logger.last_test_filename.startswith('NO_RTC_'))
            self.assertEqual(app.logger.drop_count,0)


if __name__ == '__main__':
    unittest.main()
