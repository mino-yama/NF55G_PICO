import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.cache_manager import CacheManager
from src.command_dispatcher import CommandDispatcher
from src.frame import parse_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.nf55_protocol import NF55Protocol


class ControlCacheIntegrationTests(unittest.TestCase):
    def make_dispatcher(self, steps):
        clock = FakeClock()
        scenario = MockNF55GScenario(steps)
        uart = MockUART(clock=clock, scenario=scenario)
        protocol = NF55Protocol(uart=uart, clock=clock)
        cache = CacheManager()
        dispatcher = CommandDispatcher(protocol=protocol, cache=cache)
        return dispatcher, cache, uart

    def seed_cache(self, cache, names=("DATA", "STATUS", "INFO", "BC")):
        for name in names:
            cache.validate(name, {"cache": name}, "TEST")

    def assert_frame_tx(self, uart, expected_cmd, expected_data):
        frame_txs = [tx for tx in uart.tx_log if tx.startswith(b"\x02")]
        self.assertEqual(len(frame_txs), 1)
        frame = parse_frame(frame_txs[0], expected_cmd=expected_cmd)
        self.assertEqual(frame.data, expected_data)

    def test_clock_sync_sends_explicit_time_and_invalidates_data_status(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("SC")])
        self.seed_cache(cache)
        app = FixtureApp(protocol=dispatcher.protocol, cache=cache)

        result = app.execute_ate_line("CLOCK_SYNC 260102030405")

        self.assertEqual(result, "OK")
        self.assert_frame_tx(uart, "SC", b"1A0102030405")
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))
        self.assertTrue(cache.is_valid("BC"))

    def test_clock_sync_rejects_bad_payload_without_tx_or_cache_change(self):
        for line in ("CLOCK_SYNC", "CLOCK_SYNC 26010203040", "CLOCK_SYNC 2601020304050",
                 "CLOCK_SYNC 26010203040A", "CLOCK_SYNC 26010203040\u00e9",
                 "CLOCK_SYNC 261332030405", "CLOCK_SYNC 260229030405"):
            with self.subTest(line=line):
                dispatcher, cache, uart = self.make_dispatcher([])
                self.seed_cache(cache)
                app = FixtureApp(protocol=dispatcher.protocol, cache=cache)
                self.assertTrue(app.execute_ate_line(line).startswith("ERR:"))
                self.assertEqual(uart.tx_count(), 0)
                self.assertTrue(cache.is_valid("DATA"))
                self.assertTrue(cache.is_valid("STATUS"))

    def test_clock_sync_ambiguous_timeout_invalidates_data_and_status(self):
        dispatcher, cache, uart = self.make_dispatcher(
            [ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()]
        )
        self.seed_cache(cache)
        result = dispatcher.execute_control("CLOCK_SYNC", "260102030405")
        self.assertEqual(result.ate_response, "ERR:ACK_TIMEOUT")
        self.assertTrue(result.transaction.ambiguous)
        self.assertEqual(len([tx for tx in uart.tx_log if tx.startswith(b"\x02")]), 2)
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))

    def test_clock_sync_sequence_error_preserves_cache(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.error("SQE")])
        self.seed_cache(cache)
        result = dispatcher.execute_control("CLOCK_SYNC", "260102030405")
        self.assertEqual(result.ate_response, "ERR:SQE")
        self.assert_frame_tx(uart, "SC", b"1A0102030405")
        self.assertFalse(result.transaction.ambiguous)
        self.assertTrue(cache.is_valid("DATA"))
        self.assertTrue(cache.is_valid("STATUS"))

    def test_clock_sync_invalid_response_length_is_ambiguous(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("SC", "0")])
        self.seed_cache(cache)
        result = dispatcher.execute_control("CLOCK_SYNC", "260102030405")
        self.assertEqual(result.ate_response, "ERR:FINAL_BCC_FRAME")
        self.assertTrue(result.transaction.ambiguous)
        self.assertEqual(uart.tx_log[-1], b"\x15")
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))

    def test_charge_on_success_invalidates_data_status_only(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("CN")])
        self.seed_cache(cache)

        result = dispatcher.execute_control("CHARGE_ON")

        self.assertTrue(result.ok)
        self.assertEqual(result.ate_response, "OK")
        self.assert_frame_tx(uart, "CN", b"1")
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))
        self.assertTrue(cache.is_valid("BC"))

    def test_charge_off_success_invalidates_data_status_only(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("CF")])
        self.seed_cache(cache)

        result = dispatcher.execute_control("CHARGE_OFF")

        self.assertTrue(result.ok)
        self.assert_frame_tx(uart, "CF", b"1")
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))

    def test_backup_enable_success_invalidates_data_status_only(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("BE")])
        self.seed_cache(cache)

        result = dispatcher.execute_control("BACKUP_ENABLE")

        self.assertTrue(result.ok)
        self.assert_frame_tx(uart, "BE", b"")
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))

    def test_output_restart_success_invalidates_data_status_only(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("OR")])
        self.seed_cache(cache)

        result = dispatcher.execute_control("OUTPUT_RESTART")

        self.assertTrue(result.ok)
        self.assert_frame_tx(uart, "OR", b"")
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))

    def test_param_set_success_sends_sp_50_chars_and_invalidates_data_status_info(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("SP")])
        self.seed_cache(cache)
        payload = "1" + "0" * 49

        result = dispatcher.execute_control("PARAM_SET", payload)

        self.assertTrue(result.ok)
        self.assert_frame_tx(uart, "SP", payload.encode("ascii"))
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertFalse(cache.is_valid("INFO"))
        self.assertTrue(cache.is_valid("BC"))

    def test_param_reset_empty_response_and_t2_invalidates(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("RP", "", response_delay_ms=99)])
        self.seed_cache(cache)
        result = dispatcher.execute_control("PARAM_RESET")
        self.assertEqual(result.ate_response, "OK")
        self.assert_frame_tx(uart, "RP", b"")
        for name in ("DATA", "STATUS", "INFO"):
            self.assertFalse(cache.is_valid(name))
        self.assertTrue(cache.is_valid("BC"))

    def test_param_reset_nonempty_response_is_ambiguous(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("RP", "0")])
        self.seed_cache(cache)
        result = dispatcher.execute_control("PARAM_RESET")
        self.assertEqual(result.ate_response, "ERR:FINAL_BCC_FRAME")
        self.assertTrue(result.transaction.ambiguous)
        self.assertEqual(uart.tx_log[-1], b"\x15")
        for name in ("DATA", "STATUS", "INFO"):
            self.assertFalse(cache.is_valid(name))

    def test_param_reset_timeout_invalidates(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()])
        self.seed_cache(cache)
        result = dispatcher.execute_control("PARAM_RESET")
        self.assertEqual(result.ate_response, "ERR:ACK_TIMEOUT")
        self.assertTrue(result.transaction.ambiguous)
        self.assertEqual(result.transaction.command_retry_count, 1)
        for name in ("DATA", "STATUS", "INFO"):
            self.assertFalse(cache.is_valid(name))

    def test_param_reset_sequence_error_preserves_cache(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.error("SQE")])
        self.seed_cache(cache)
        result = dispatcher.execute_control("PARAM_RESET")
        self.assertEqual(result.ate_response, "ERR:SQE")
        self.assertFalse(result.transaction.ambiguous)
        for name in ("DATA", "STATUS", "INFO", "BC"):
            self.assertTrue(cache.is_valid(name))

    def test_param_set_nonempty_response_is_ambiguous_and_invalidates(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_response("SP", "0")])
        self.seed_cache(cache)
        result = dispatcher.execute_control("PARAM_SET", "0" * 50)
        self.assertEqual(result.ate_response, "ERR:FINAL_BCC_FRAME")
        self.assertTrue(result.transaction.ambiguous)
        self.assertEqual(uart.tx_log[-1], b"\x15")
        for name in ("DATA", "STATUS", "INFO"):
            self.assertFalse(cache.is_valid(name))
        self.assertTrue(cache.is_valid("BC"))

    def test_param_set_sequence_error_preserves_all_cached_values(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.error("SQE")])
        self.seed_cache(cache)
        result = dispatcher.execute_control("PARAM_SET", "0" * 50)
        self.assertEqual(result.ate_response, "ERR:SQE")
        self.assertFalse(result.transaction.ambiguous)
        for name in ("DATA", "STATUS", "INFO", "BC"):
            self.assertTrue(cache.is_valid(name))

    def test_param_set_timeout_is_ambiguous_and_invalidates(self):
        dispatcher, cache, uart = self.make_dispatcher([ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()])
        self.seed_cache(cache)
        result = dispatcher.execute_control("PARAM_SET", "0" * 50)
        self.assertEqual(result.ate_response, "ERR:ACK_TIMEOUT")
        self.assertTrue(result.transaction.ambiguous)
        self.assertEqual(result.transaction.command_retry_count, 1)
        for name in ("DATA", "STATUS", "INFO"):
            self.assertFalse(cache.is_valid(name))

    def test_param_set_rejects_wrong_length_without_nf55_tx_or_cache_change(self):
        dispatcher, cache, uart = self.make_dispatcher([])
        self.seed_cache(cache)

        result = dispatcher.execute_control("PARAM_SET", "1" * 49)

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "PARSER")
        self.assertEqual(uart.tx_count(), 0)
        self.assertTrue(cache.is_valid("DATA"))
        self.assertTrue(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))

    def test_pme_sqe_do_not_invalidate_existing_cache(self):
        for error_code in ("PME", "SQE"):
            with self.subTest(error_code=error_code):
                dispatcher, cache, _uart = self.make_dispatcher([ScenarioStep.error(error_code)])
                self.seed_cache(cache)

                result = dispatcher.execute_control("CHARGE_ON")

                self.assertFalse(result.ok)
                self.assertEqual(result.ate_response, "ERR:{}".format(error_code))
                self.assertFalse(result.transaction.ambiguous)
                self.assertTrue(cache.is_valid("DATA"))
                self.assertTrue(cache.is_valid("STATUS"))
                self.assertTrue(cache.is_valid("INFO"))

    def test_hwe_invalidates_control_related_cache(self):
        dispatcher, cache, _uart = self.make_dispatcher([ScenarioStep.error("HWE")])
        self.seed_cache(cache)

        result = dispatcher.execute_control("CHARGE_ON")

        self.assertFalse(result.ok)
        self.assertEqual(result.ate_response, "ERR:HWE")
        self.assertTrue(result.transaction.ambiguous)
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))

    def test_ack_timeout_ambiguous_invalidates_control_related_cache(self):
        dispatcher, cache, _uart = self.make_dispatcher(
            [ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()]
        )
        self.seed_cache(cache)

        result = dispatcher.execute_control("BACKUP_ENABLE")

        self.assertFalse(result.ok)
        self.assertEqual(result.ate_response, "ERR:ACK_TIMEOUT")
        self.assertTrue(result.transaction.ambiguous)
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertTrue(cache.is_valid("INFO"))

    def test_control_does_not_auto_refresh_status_after_success(self):
        dispatcher, _cache, uart = self.make_dispatcher([ScenarioStep.ack_response("CN")])

        result = dispatcher.execute_control("CHARGE_ON")

        self.assertTrue(result.ok)
        frame_txs = [tx for tx in uart.tx_log if tx.startswith(b"\x02")]
        self.assertEqual(len(frame_txs), 1)
        self.assertEqual(parse_frame(frame_txs[0]).cmd, "CN")


if __name__ == "__main__":
    unittest.main()
