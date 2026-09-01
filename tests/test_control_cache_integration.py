import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.cache_manager import CacheManager
from src.command_dispatcher import CommandDispatcher
from src.frame import parse_frame
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
