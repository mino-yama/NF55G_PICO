"""SLの実送信DATA保持、PME等の実応答、明示D0読戻しをHost Mockで確認する。"""
import unittest
from src import config
from src.cache_manager import CacheManager
from src.frame import parse_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.nf55_command import build_control_command, CommandError
from src.nf55_protocol import NF55Protocol


def readback_data(raw_deg):
    # r1 p.28/41: D0積算データのBATT_DEGは先頭から162文字目。
    data = list("1A0B090D0000" + "0" * 315)
    data[162:165] = raw_deg
    return "".join(data)


class LifeSetTests(unittest.TestCase):
    def app(self, steps):
        clock = FakeClock()
        uart = MockUART(clock, MockNF55GScenario(steps))
        cache = CacheManager()
        for name in config.CACHE_NAMES:
            cache.validate(name, {"old": True}, "OLD")
        return FixtureApp(protocol=NF55Protocol(uart, clock=clock), cache=cache), uart

    def assert_cache(self, app, invalid=()):
        for name in config.CACHE_NAMES:
            self.assertEqual(app.cache.is_valid(name), name not in invalid, name)

    def commands(self, uart):
        return [parse_frame(tx) for tx in uart.tx_log if tx.startswith(b"\x02")]

    def test_decimal_conversion_boundaries_and_special_value(self):
        for value, expected in (("0", b"00000000"), ("1", b"00100000"),
                                ("123", b"07B00000"), ("4094", b"FFE00000"),
                                ("4095", b"FFF00000"), ("000123", b"07B00000")):
            with self.subTest(value=value):
                app, uart = self.app([ScenarioStep.ack_response("SL", response_delay_ms=99)])
                self.assertEqual(app.execute_ate_line("LIFE_SET_" + value), "OK")
                frame = self.commands(uart)[0]
                self.assertEqual((frame.cmd, frame.data), ("SL", expected))
                self.assert_cache(app, ("DATA",))
                self.assertFalse(app.protocol.last_result.ambiguous)

    def test_out_of_range_is_not_clamped_truncated_or_blocked(self):
        for value, expected in (("4096", b"100000000"), ("65535", b"FFFF00000"),
                                ("-1", b"-0100000"), ("+4096", b"100000000")):
            app, uart = self.app([ScenarioStep.error("PME")])
            self.assertEqual(app.execute_ate_line("LIFE_SET_" + value), "ERR:PME")
            self.assertEqual(self.commands(uart)[0].data, expected)
            self.assert_cache(app)

    def test_raw_keeps_nonhex_reserve_case_and_invalid_lengths(self):
        for raw in ("GGG00000", "fff12345", "100000000", "FFF", "", "ABC DEF0"):
            app, uart = self.app([ScenarioStep.ack_response("SL")])
            self.assertEqual(app.execute_ate_line("LIFE_SET_RAW=" + raw), "OK")
            self.assertEqual(self.commands(uart)[0].data, raw.encode("ascii"))
            self.assert_cache(app, ("DATA",))

    def test_raw_space_and_equals_argument_forms(self):
        for command in ("LIFE_SET_RAW GGG00000", "LIFE_SET_RAW=GGG00000"):
            app, uart = self.app([ScenarioStep.error("PME")])
            self.assertEqual(app.execute_ate_line(command), "ERR:PME")
            self.assertEqual(self.commands(uart)[0].data, b"GGG00000")

    def test_invalid_ate_syntax_never_transmits(self):
        for command in ("LIFE_SET_", "LIFE_SET_1.0", "LIFE_SET_0xFFF", "LIFE_SET_１",
                        "LIFE_SET_1 EXTRA", "LIFE_SET_1=", "LIFE_SET_RAW",
                        "LIFE_SET_RAW=非ASCII", "LIFE_SET_RAW=A\x03B", "LIFE_SET_RAW=A\nB"):
            app, uart = self.app([])
            self.assertTrue(app.execute_ate_line(command).startswith("ERR:"), command)
            self.assertEqual(uart.tx_log, [], command)
            self.assert_cache(app)

    def test_clear_product_rejections_preserve_caches(self):
        for error in ("PME", "SQE", "CME"):
            app, uart = self.app([ScenarioStep.error(error)])
            self.assertEqual(app.execute_ate_line("LIFE_SET_RAW=GGG00000"), "ERR:" + error)
            self.assertFalse(app.protocol.last_result.ambiguous)
            self.assert_cache(app)

    def test_timeouts_retry_once_and_hwe_invalidate_data_only(self):
        for steps, error in (([ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()], "ACK_TIMEOUT"),
                             ([ScenarioStep.resp_timeout(), ScenarioStep.resp_timeout()], "RESP_TIMEOUT"),
                             ([ScenarioStep.error("HWE")], "HWE")):
            app, uart = self.app(steps)
            self.assertEqual(app.execute_ate_line("LIFE_SET_123"), "ERR:" + error)
            self.assertTrue(app.protocol.last_result.ambiguous)
            self.assertEqual(app.protocol.last_result.command_retry_count, 0 if error == "HWE" else 1)
            self.assert_cache(app, ("DATA",))

    def test_nonempty_success_response_rejected_with_plain_nak(self):
        app, uart = self.app([ScenarioStep.ack_response("SL", "0")])
        self.assertEqual(app.execute_ate_line("LIFE_SET_123"), "ERR:FINAL_BCC_FRAME")
        self.assertEqual(uart.tx_log[-1], b"\x15")
        self.assert_cache(app, ("DATA",))

    def test_bcc_response_retry_separate_from_command_retry(self):
        app, uart = self.app([ScenarioStep.bcc_ng_then_retry("SL")])
        self.assertEqual(app.execute_ate_line("LIFE_SET_123"), "OK")
        tx = app.protocol.last_result
        self.assertEqual((tx.command_retry_count, tx.response_retry_count), (0, 1))
        self.assertIn(b"\x15", uart.tx_log)
        self.assert_cache(app, ("DATA",))

    def test_success_does_not_publish_setting_until_explicit_d0(self):
        app, uart = self.app([ScenarioStep.ack_response("SL"),
                              ScenarioStep.ack_response("D0", readback_data("07B"))])
        self.assertEqual(app.execute_ate_line("LIFE_SET_123"), "OK")
        self.assertEqual(app.execute_ate_line("BATT_DEG_TOTAL?"), "ERR:CACHE_INVALID")
        self.assertEqual([f.cmd for f in self.commands(uart)], ["SL"])
        self.assertEqual(app.execute_ate_line("DATA_REFRESH"), "OK")
        before = list(uart.tx_log)
        self.assertEqual(app.execute_ate_line("BATT_DEG_TOTAL?"), "12.3")
        self.assertEqual(uart.tx_log, before)
        self.assertEqual([f.cmd for f in self.commands(uart)], ["SL", "D0"])
        self.assertEqual(app.cache.metadata("DATA")["source_cmd"], "D0")
        self.assertEqual(app.cache.get("STATUS"), {"old": True})
        self.assertEqual(app.cache.get("INFO"), {"old": True})

    def test_out_of_range_pme_or_acceptance_uses_actual_readback(self):
        # PME・受理・切捨て等は製品の仕様として確定しない。Mock応答をそのまま確認。
        for step, expected, returned in ((ScenarioStep.error("PME"), "ERR:PME", "07B"),
                                         (ScenarioStep.ack_response("SL"), "OK", "100")):
            app, uart = self.app([step, ScenarioStep.ack_response("D0", readback_data(returned))])
            self.assertEqual(app.execute_ate_line("LIFE_SET_4096"), expected)
            self.assertEqual(self.commands(uart)[0].data, b"100000000")
            self.assertEqual(app.execute_ate_line("DATA_REFRESH"), "OK")
            self.assertEqual(app.execute_ate_line("BATT_DEG_TOTAL?"), str(int(returned, 16) / 10))

    def test_no_implicit_reads_and_no_connection_or_busy(self):
        app = FixtureApp(protocol=None)
        self.assertEqual(app.execute_ate_line("LIFE_SET_4096"), "ERR:NF55G_NOT_CONNECTED")
        self.assertEqual(app.execute_ate_line("LIFE_SET_RAW="), "ERR:NF55G_NOT_CONNECTED")
        app, uart = self.app([])
        app.protocol.busy = True
        self.assertEqual(app.execute_ate_line("LIFE_SET_123"), "ERR:BUSY")
        self.assertEqual(uart.tx_log, [])
        self.assert_cache(app)
        with self.assertRaises(CommandError):
            build_control_command("LIFE_SET_RAW", b"\x15")


if __name__ == "__main__":
    unittest.main()
