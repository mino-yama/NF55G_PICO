"""BC開始・停止・結果Queryの通信契約とCache境界をHost/Mockで確認。"""
import unittest
from unittest.mock import patch
from src import config
from src.cache_manager import CacheManager
from src.frame import parse_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.nf55_protocol import NF55Protocol

PAYLOAD = "3" "1F40" "1E78" "03E8" "07D0" "EC" "5A" "064" "000000"
EXPECTED = {"BC_MODE?": "3", "BC_V1?": "8.0", "BC_V2?": "7.8", "BC_I1?": "1.0",
            "BC_I2?": "2.0", "BC_TEMP?": "-20", "BC_SOC?": "90", "BC_IR?": "100"}
CASES = (("BATT_CHECK_START", b"1"), ("BATT_CHECK_STOP", b"0"))


class BatteryCheckCommandTests(unittest.TestCase):
    def app(self, steps):
        clock = FakeClock()
        uart = MockUART(clock, MockNF55GScenario(steps))
        cache = CacheManager()
        for name in config.CACHE_NAMES:
            cache.validate(name, {"old": True}, "OLD")
        return FixtureApp(protocol=NF55Protocol(uart, clock=clock), cache=cache), uart

    def assert_cache(self, app, invalid=(), bc_result=False):
        for name in config.CACHE_NAMES:
            self.assertEqual(app.cache.is_valid(name), name not in invalid, name)
            if name not in invalid and not (name == "BC" and bc_result):
                self.assertEqual(app.cache.get(name), {"old": True}, name)

    def test_start_wire_six_second_t2_decode_and_exact_cache_updates(self):
        self.assertEqual(len(PAYLOAD), 30)
        app, uart = self.app([ScenarioStep.ack_response("BC", PAYLOAD, response_delay_ms=5999)])
        original_write = uart.write
        def write(data):
            if data.startswith(b"\x02"):
                self.assertFalse(app.cache.is_valid("BC"))
            return original_write(data)
        uart.write = write
        self.assertEqual(app.execute_ate_line("BATT_CHECK_START\r\n"), "OK")
        frame = parse_frame(uart.tx_log[0], expected_cmd="BC")
        self.assertEqual(frame.data, b"1")
        self.assert_cache(app, ("DATA", "STATUS"), bc_result=True)
        self.assertEqual(app.cache.metadata("BC")["source_cmd"], "BC")
        before = list(uart.tx_log)
        for name, expected in EXPECTED.items():
            self.assertEqual(app.execute_ate_line(name), expected)
        self.assertEqual(app.execute_ate_line("BATT_CHECK_RUN?"), "ERR:CACHE_INVALID")
        self.assertEqual(uart.tx_log, before)
        self.assertEqual((app.protocol.last_result.command_retry_count,
                          app.protocol.last_result.response_retry_count), (0, 0))

    def test_stop_wire_six_second_t2_does_not_publish_result(self):
        app, uart = self.app([ScenarioStep.ack_response("BC", PAYLOAD, response_delay_ms=5999)])
        self.assertEqual(app.execute_ate_line("BATT_CHECK_STOP"), "OK")
        self.assertEqual(parse_frame(uart.tx_log[0], expected_cmd="BC").data, b"0")
        self.assert_cache(app, ("DATA", "STATUS", "BC"))
        before = list(uart.tx_log)
        for name in EXPECTED:
            self.assertEqual(app.execute_ate_line(name), "ERR:CACHE_INVALID")
        self.assertEqual(uart.tx_log, before)

    def test_mode_13_and_other_numeric_modes_are_not_product_judgements(self):
        for mode in (0, 1, 2, 3, 11, 12, 13, 14):
            with self.subTest(mode=mode):
                payload = "{:X}".format(mode) + PAYLOAD[1:]
                app, uart = self.app([ScenarioStep.ack_response("BC", payload)])
                self.assertEqual(app.execute_ate_line("BATT_CHECK_START"), "OK")
                self.assertEqual(app.execute_ate_line("BC_MODE?"), str(mode))
                # 製品が返した非ゼロ値をMODEを理由にゼロ補完・抑止しない。
                self.assertEqual(app.execute_ate_line("BC_V1?"), "8.0")
                self.assertEqual(app.execute_ate_line("BC_IR?"), "100")

    def test_zero_response_and_signed_fields(self):
        app, uart = self.app([ScenarioStep.ack_response("BC", "0" * 30)])
        self.assertEqual(app.execute_ate_line("BATT_CHECK_START"), "OK")
        self.assertEqual(app.execute_ate_line("BC_MODE?"), "0")
        self.assertEqual(app.execute_ate_line("BC_V1?"), "0.0")
        payload = PAYLOAD[:17] + "FF80FFF" + "000000"
        app, uart = self.app([ScenarioStep.ack_response("BC", payload)])
        self.assertEqual(app.execute_ate_line("BATT_CHECK_START"), "OK")
        self.assertEqual(app.execute_ate_line("BC_TEMP?"), "-1")
        self.assertEqual(app.execute_ate_line("BC_SOC?"), "-128")
        self.assertEqual(app.execute_ate_line("BC_IR?"), "4095")

    def test_definite_rejection_invalidates_only_start_bc(self):
        for name, data in CASES:
            for error in ("SQE", "PME", "CME"):
                with self.subTest(name=name, error=error):
                    app, uart = self.app([ScenarioStep.error(error)])
                    self.assertEqual(app.execute_ate_line(name), "ERR:" + error)
                    self.assertFalse(app.protocol.last_result.ambiguous)
                    self.assert_cache(app, ("BC",) if data == b"1" else ())

    def test_timeouts_one_command_retry_and_safe_cache_invalidation(self):
        for name, data in CASES:
            for step, error in ((ScenarioStep.ack_timeout, "ACK_TIMEOUT"),
                                (ScenarioStep.resp_timeout, "RESP_TIMEOUT")):
                with self.subTest(name=name, error=error):
                    app, uart = self.app([step(), step()])
                    self.assertEqual(app.execute_ate_line(name), "ERR:" + error)
                    self.assertTrue(app.protocol.last_result.ambiguous)
                    self.assertEqual((app.protocol.last_result.command_retry_count,
                                      app.protocol.last_result.response_retry_count), (1, 0))
                    frames = [parse_frame(tx) for tx in uart.tx_log if tx.startswith(b"\x02")]
                    self.assertEqual([(f.cmd, f.data) for f in frames], [("BC", data)] * 2)
                    self.assert_cache(app, ("DATA", "STATUS", "BC"))

    def test_response_after_six_seconds_is_not_success(self):
        for name, data in CASES:
            app, uart = self.app([ScenarioStep.ack_response("BC", PAYLOAD, response_delay_ms=6001),
                                  ScenarioStep.resp_timeout()])
            self.assertNotEqual(app.execute_ate_line(name), "OK")
            self.assertTrue(app.protocol.last_result.ambiguous)
            self.assert_cache(app, ("DATA", "STATUS", "BC"))

    def test_empty_short_long_response_plain_nak_and_no_firmware_workaround(self):
        for name, data in CASES:
            for size in (0, 29, 31):
                with self.subTest(name=name, size=size):
                    app, uart = self.app([ScenarioStep.ack_response("BC", "0" * size)])
                    self.assertEqual(app.execute_ate_line(name), "ERR:FINAL_BCC_FRAME")
                    self.assertEqual(uart.tx_log[-1], b"\x15")
                    self.assertTrue(app.protocol.last_result.ambiguous)
                    self.assert_cache(app, ("DATA", "STATUS", "BC"))

    def test_nonhex_payload_including_reserve_rejects_complete_result(self):
        for name, data in CASES:
            for index in (0, 1, 17, 21, 24, 29):
                payload = PAYLOAD[:index] + "Z" + PAYLOAD[index+1:]
                app, uart = self.app([ScenarioStep.ack_response("BC", payload)])
                self.assertEqual(app.execute_ate_line(name), "ERR:DECODE")
                self.assertTrue(app.protocol.last_result.ok)
                self.assert_cache(app, ("DATA", "STATUS", "BC"))

    def test_partial_decoder_result_is_not_published(self):
        app, uart = self.app([ScenarioStep.ack_response("BC", PAYLOAD)])
        with patch("src.command_dispatcher.decode_bc", return_value={"BC_MODE": 3}):
            self.assertEqual(app.execute_ate_line("BATT_CHECK_START"), "ERR:DECODE")
        self.assertFalse(app.cache.is_valid("BC"))

    def test_response_retry_is_separate_and_hwe_invalidates(self):
        for name, data in CASES:
            app, uart = self.app([ScenarioStep.bcc_ng_then_retry("BC", PAYLOAD)])
            self.assertEqual(app.execute_ate_line(name), "OK")
            self.assertEqual((app.protocol.last_result.command_retry_count,
                              app.protocol.last_result.response_retry_count), (0, 1))
            self.assertIn(b"\x15", uart.tx_log)
            app, uart = self.app([ScenarioStep.error("HWE")])
            self.assertEqual(app.execute_ate_line(name), "ERR:HWE")
            self.assert_cache(app, ("DATA", "STATUS", "BC"))

    def test_extra_arguments_and_unknown_bc_queries_no_tx_no_cache_change(self):
        bad = [name + suffix for name, data in CASES for suffix in (" EXTRA", "=1", "=")]
        bad += ["BC_MODE? EXTRA", "BC_IR?=1", "BC_OTHER?", "BATT_CHECK_STARTER"]
        for line in bad:
            app, uart = self.app([])
            self.assertTrue(app.execute_ate_line(line).startswith("ERR:"))
            self.assertEqual(uart.tx_log, [])
            self.assert_cache(app)

    def test_no_connection_and_busy_do_not_bypass_core(self):
        app = FixtureApp(protocol=None)
        app.cache.validate("BC", {"BC_MODE": 3}, "OLD")
        self.assertEqual(app.execute_ate_line("BATT_CHECK_START"), "ERR:NF55G_NOT_CONNECTED")
        self.assertEqual(app.execute_ate_line("BC_MODE?"), "ERR:CACHE_INVALID")
        self.assertEqual(app.execute_ate_line("BATT_CHECK_STOP"), "ERR:NF55G_NOT_CONNECTED")
        for name, data in CASES:
            app, uart = self.app([])
            app.protocol.busy = True
            self.assertEqual(app.execute_ate_line(name), "ERR:BUSY")
            self.assertEqual(uart.tx_log, [])
            self.assert_cache(app, ("BC",) if data == b"1" else ())


if __name__ == "__main__":
    unittest.main()
