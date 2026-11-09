import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.cache_manager import CacheManager
from src.command_dispatcher import CommandDispatcher
from src.logger import Logger, MemorySDSink, LoggerError, SD_NO_CARD, SD_OK, SD_WRITE_ERR
from src.mock_nf55g import FakeClock


class LoggerSDTests(unittest.TestCase):
    def make_logger(self, queue_limit=256):
        clock = FakeClock()
        sink = MemorySDSink(capacity_bytes=1000)
        logger = Logger(sd_sink=sink, clock=clock, queue_limit=queue_limit)
        return logger, sink, clock

    def test_nf_raw_ascii_is_rendered_after_queueing(self):
        logger, sink, _clock = self.make_logger()
        self.assertTrue(logger.test_start())
        filename = logger.current_filename
        logger.log(category="NF55", direction="TX", event="RAW", raw_hex="025343033133")
        logger.log(category="NF55", direction="RX", event="RAW", raw_hex="06")
        self.assertEqual(logger.queue[0][5], "")
        self.assertTrue(logger.test_end())
        self.assertEqual(sink.files[filename][0][5], r"\x02SC\x0313")
        self.assertEqual(sink.files[filename][0][6], "025343033133")
        self.assertEqual(sink.files[filename][1][5], r"\x06")

    def test_test_start_creates_one_csv_session(self):
        logger, sink, _clock = self.make_logger()

        self.assertTrue(logger.test_start())

        self.assertTrue(logger.active)
        self.assertEqual(logger.mode, "TEST")
        self.assertTrue(logger.current_filename.endswith(".csv"))
        self.assertEqual(sink.open_filename, logger.current_filename)
        self.assertEqual(logger.status(), SD_OK)

    def test_test_end_forces_queue_drain_flush_and_close(self):
        logger, sink, _clock = self.make_logger()
        logger.test_start()
        logger.log(category="NF55", cmd="D1", result="OK")
        logger.log(category="ATE", cmd="TEST_END", result="OK")

        self.assertTrue(logger.test_end())

        self.assertFalse(logger.active)
        self.assertEqual(len(logger.queue), 0)
        self.assertEqual(sink.write_count, 2)
        self.assertEqual(sink.flush_count, 1)
        self.assertEqual(sink.close_count, 1)
        self.assertIsNone(sink.open_filename)

    def test_log_cont_start_stop(self):
        logger, sink, _clock = self.make_logger()

        self.assertTrue(logger.log_cont_start())
        self.assertEqual(logger.mode, "CONT")
        logger.log(category="CONT", event="SAMPLE")
        self.assertTrue(logger.log_cont_stop())

        self.assertFalse(logger.active)
        self.assertEqual(sink.write_count, 1)

    def test_service_flushes_after_32_records(self):
        logger, sink, _clock = self.make_logger()
        logger.test_start()
        for index in range(32):
            logger.log(category="COUNT", detail=index)

        written = logger.service(protocol_busy=False)

        self.assertEqual(written, 32)
        self.assertEqual(sink.write_count, 32)
        self.assertEqual(sink.flush_count, 1)

    def test_service_flushes_after_one_second(self):
        logger, sink, clock = self.make_logger()
        logger.test_start()
        logger.log(category="TIME")

        self.assertEqual(logger.service(protocol_busy=False), 0)
        clock.advance_ms(1000)
        self.assertEqual(logger.service(protocol_busy=False), 1)

        self.assertEqual(sink.write_count, 1)
        self.assertEqual(sink.flush_count, 1)

    def test_no_sd_write_or_flush_while_protocol_busy(self):
        logger, sink, clock = self.make_logger()
        logger.test_start()
        logger.log(category="NF55", cmd="D1")
        clock.advance_ms(1000)

        written = logger.service(protocol_busy=True)

        self.assertEqual(written, 0)
        self.assertEqual(sink.write_count, 0)
        self.assertEqual(sink.flush_count, 0)
        self.assertEqual(len(logger.queue), 1)

    def test_queue_overflow_increments_drop_count(self):
        logger, _sink, _clock = self.make_logger(queue_limit=1)

        self.assertTrue(logger.log(category="A"))
        self.assertFalse(logger.log(category="B"))

        self.assertEqual(logger.drop_count, 1)

    def test_sd_status_usage_drop_count_and_reinit_commands(self):
        logger, sink, _clock = self.make_logger()
        dispatcher = CommandDispatcher(protocol=None, cache=CacheManager(), logger=logger)
        dispatcher.execute_logger("TEST_START")
        logger.log(category="ATE", cmd="TEST_START")
        dispatcher.execute_logger("TEST_END")

        self.assertEqual(dispatcher.execute_logger("SD_STATUS?").ate_response, SD_OK)
        self.assertIn("/", dispatcher.execute_logger("SD_USAGE?").ate_response)
        self.assertEqual(dispatcher.execute_logger("LOG_DROP_COUNT?").ate_response, "0")

        sink.status = SD_NO_CARD
        result = dispatcher.execute_logger("SD_REINIT")
        self.assertTrue(result.ok)
        self.assertEqual(logger.status(), SD_OK)
        self.assertEqual(sink.reinit_count, 1)

    def test_test_start_reports_sd_failure(self):
        logger, sink, _clock = self.make_logger()
        sink.status = SD_NO_CARD

        self.assertFalse(logger.test_start())

        self.assertEqual(logger.status(), SD_NO_CARD)
        self.assertFalse(logger.active)

    def test_write_failure_latches_status_and_drops_queue(self):
        logger, sink, _clock = self.make_logger()
        logger.test_start()
        logger.log(category="A")
        logger.log(category="B")
        sink.flush_blocked = True

        written = logger.force_drain()

        self.assertEqual(written, 0)
        self.assertEqual(logger.status(), SD_WRITE_ERR)
        self.assertEqual(logger.drop_count, 2)
        self.assertEqual(len(logger.queue), 0)

    def test_failed_start_keeps_test_guard_until_end_and_recovers_once(self):
        logger, sink, _ = self.make_logger()
        sink.status = SD_NO_CARD
        self.assertFalse(logger.test_start())
        self.assertTrue(logger.test_running)
        self.assertFalse(logger.reinit())
        self.assertFalse(logger.service_recovery())
        self.assertEqual(sink.reinit_count, 0)
        self.assertFalse(logger.test_end())
        self.assertFalse(logger.test_running)
        self.assertTrue(logger.service_recovery())
        self.assertEqual(sink.reinit_count, 1)
        self.assertFalse(logger.service_recovery())
        self.assertTrue(logger.test_start())

    def test_removal_and_reinsertion_do_not_recover_inside_test(self):
        logger, sink, clock = self.make_logger()
        self.assertTrue(logger.test_start())
        sink.status = SD_NO_CARD
        logger.log(detail='removed')
        clock.advance_ms(1000)
        logger.service()
        self.assertEqual(logger.status(), SD_NO_CARD)
        sink.status = SD_OK
        logger.log(detail='reinserted')
        self.assertFalse(logger.reinit())
        self.assertFalse(logger.service_recovery())
        logger.service()
        self.assertEqual(sink.write_count, 0)
        self.assertEqual(sink.reinit_count, 0)
        self.assertEqual(logger.drop_count, 2)
        self.assertFalse(logger.test_end())
        self.assertTrue(logger.service_recovery())
        self.assertEqual(logger.status(), SD_OK)

    def test_failed_post_test_recovery_is_not_polled_repeatedly(self):
        logger, sink, _ = self.make_logger()
        def missing():
            sink.reinit_count += 1
            raise LoggerError(SD_NO_CARD)
        sink.reinit = missing
        logger.test_start()
        logger.test_end()
        self.assertFalse(logger.service_recovery())
        self.assertFalse(logger.service_recovery())
        self.assertEqual(sink.reinit_count, 1)

    def test_pending_recovery_waits_for_communication(self):
        logger, sink, _ = self.make_logger()
        logger.test_start()
        logger.test_end()
        logger.busy = lambda: True
        self.assertFalse(logger.service_recovery())
        self.assertTrue(logger.recovery_pending)
        logger.busy = lambda: False
        self.assertTrue(logger.service_recovery())


if __name__ == "__main__":
    unittest.main()
