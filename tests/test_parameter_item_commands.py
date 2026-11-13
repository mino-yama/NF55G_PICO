"""項目別SPの範囲、未変更マスク、ATE入口とCache規則の統合試験。"""
import unittest
from src import config
from src.cache_manager import CacheManager
from src.frame import parse_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.nf55_protocol import NF55Protocol
from src.nf55_command import build_control_command, CommandError

# r1 p.19の表順・桁数・上限を試験側に記載し、実装表から期待値を作らない。
ITEMS = (("PS_ON_BACKUP", 0, 1, 1), ("AC_LINK", 1, 1, 1),
         ("AUTO_CHARGE", 2, 1, 3), ("EVENT_ENABLE", 3, 1, 1),
         ("MAX_BACKUP_TIME", 4, 1, 14), ("MIN_BACKUP_TIME", 5, 2, 254),
         ("RESTART_TIME", 7, 2, 254), ("BATT_LOW_THD", 9, 2, 100),
         ("BATT_CAP_MAH", 11, 4, 65534), ("BATT_CAP_WH", 15, 2, 254))


class ParameterItemTests(unittest.TestCase):
    def app(self, steps):
        clock = FakeClock()
        uart = MockUART(clock, MockNF55GScenario(steps))
        cache = CacheManager()
        for target in config.CACHE_NAMES:
            cache.validate(target, {"old": True}, "OLD")
        return FixtureApp(protocol=NF55Protocol(uart, clock=clock), cache=cache), uart

    def assert_cache(self, app, invalid=()):
        for target in config.CACHE_NAMES:
            self.assertEqual(app.cache.is_valid(target), target not in invalid, target)
            if target not in invalid:
                self.assertEqual(app.cache.get(target), {"old": True})

    def test_all_items_min_max_wire_mask_and_t2(self):
        for item, offset, width, maximum in ITEMS:
            for value in (0, maximum):
                with self.subTest(item=item, value=value):
                    app, uart = self.app([ScenarioStep.ack_response("SP", response_delay_ms=99)])
                    name = "PARAM_{}_{}".format(item, value)
                    self.assertEqual(app.execute_ate_line(name + "\r\n"), "OK")
                    frame = parse_frame(uart.tx_log[0], expected_cmd="SP")
                    self.assertEqual(len(frame.data), 50)
                    encoded = format(value, "0{}X".format(width)).encode()
                    self.assertEqual(frame.data[offset:offset+width], encoded)
                    self.assertEqual(frame.data[:offset], b"F" * offset)
                    self.assertEqual(frame.data[offset+width:32], b"F" * (32-offset-width))
                    self.assertEqual(frame.data[32:], b"0" * 18)
                    self.assert_cache(app, ("DATA", "STATUS", "INFO"))
                    self.assertEqual((app.protocol.last_result.command_retry_count,
                                      app.protocol.last_result.response_retry_count), (0, 0))
                    before = list(uart.tx_log)
                    self.assertEqual(app.execute_ate_line("AUTO_CHARGE?"), "ERR:CACHE_INVALID")
                    self.assertEqual(uart.tx_log, before)

    def test_decimal_input_converted_to_hex_and_zero_is_not_replaced(self):
        spec = build_control_command("PARAM_MIN_BACKUP_TIME_15")
        self.assertEqual(spec.data, b"FFFFF0F" + b"F" * 25 + b"0" * 18)
        self.assertEqual(build_control_command("PARAM_MIN_BACKUP_TIME_015").data, spec.data)
        spec = build_control_command("PARAM_BATT_LOW_THD_0")
        self.assertEqual(spec.data[9:11], b"00")
        self.assertEqual(build_control_command("PARAM_BATT_CAP_MAH_4900").data[11:15], b"1324")

    def test_out_of_range_and_no_change_sentinel_are_rejected(self):
        for item, offset, width, maximum in ITEMS:
            for value in (maximum + 1, (16 ** width) - 1):
                app, uart = self.app([])
                self.assertEqual(app.execute_ate_line("PARAM_{}_{}".format(item, value)), "ERR:PARAMETER_RANGE")
                self.assertEqual(uart.tx_log, [])
                self.assert_cache(app)

    def test_invalid_syntax_unknown_item_and_payload_do_not_send(self):
        bad = ["PARAM_AUTO_CHARGE_", "PARAM_AUTO_CHARGE_-1", "PARAM_AUTO_CHARGE_+1",
               "PARAM_AUTO_CHARGE_1.0", "PARAM_AUTO_CHARGE_0x1", "PARAM_AUTO_CHARGE_１",
               "PARAM_AUTO_CHARGE_1_EXTRA", "PARAM_AUTO_CHARGE_1 EXTRA", "PARAM_AUTO_CHARGE_1=",
               "PARAM_AUTO_CHARGE_1=1", "PARAM_UNKNOWN_1", "PARAM_EVENT_1", "PARAM_",
               "PARAM_MIN_BACKUP_TIME_9999999999999999999999999999999999999999"]
        for name in bad:
            with self.subTest(name=name):
                app, uart = self.app([])
                self.assertTrue(app.execute_ate_line(name).startswith("ERR:"))
                self.assertEqual(uart.tx_log, [])
                self.assert_cache(app)

    def test_protected_and_unconfirmed_items_never_send(self):
        for item in ("BATT_WNG_THD", "BATT_ALM_THD", "ADU_TEMP_THD", "BBU_TEMP_THD", "FAN_WNG_THD", "CHG_IR_THD"):
            app, uart = self.app([])
            expected = "ERR:PARAMETER_UNCONFIRMED" if item == "CHG_IR_THD" else "ERR:PARAMETER_PROTECTED"
            self.assertEqual(app.execute_ate_line("PARAM_{}_0".format(item)), expected)
            self.assertEqual(uart.tx_log, [])
            self.assert_cache(app)

    def test_explicit_info_readback_after_item_set(self):
        parameters = "103000F0F32132424000415055550267000000000000000000"
        self.assertEqual(len(parameters), 50)
        app, uart = self.app([ScenarioStep.ack_response("SP"),
                              ScenarioStep.ack_response("D5", "0" * 50 + parameters)])
        self.assertEqual(app.execute_ate_line("PARAM_AUTO_CHARGE_3"), "OK")
        self.assertEqual(app.execute_ate_line("INFO_REFRESH"), "OK")
        self.assertEqual(app.execute_ate_line("AUTO_CHARGE?"), "3")
        self.assertEqual(app.execute_ate_line("MIN_BACKUP_TIME?"), "15")
        self.assertEqual([parse_frame(tx).cmd for tx in uart.tx_log if tx.startswith(b"\x02")], ["SP", "D5"])
        self.assertEqual(app.cache.metadata("INFO")["source_cmd"], "D5")
        self.assertFalse(app.cache.is_valid("DATA"))
        self.assertFalse(app.cache.is_valid("STATUS"))

    def test_product_rejections_preserve_all_caches(self):
        for error in ("PME", "SQE", "CME"):
            app, uart = self.app([ScenarioStep.error(error)])
            self.assertEqual(app.execute_ate_line("PARAM_AUTO_CHARGE_2"), "ERR:" + error)
            self.assertFalse(app.protocol.last_result.ambiguous)
            self.assert_cache(app)

    def test_timeouts_one_command_retry_and_hwe_invalidate(self):
        for steps, error in (([ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()], "ACK_TIMEOUT"),
                             ([ScenarioStep.resp_timeout(), ScenarioStep.resp_timeout()], "RESP_TIMEOUT"),
                             ([ScenarioStep.error("HWE")], "HWE")):
            app, uart = self.app(steps)
            self.assertEqual(app.execute_ate_line("PARAM_AUTO_CHARGE_2"), "ERR:" + error)
            self.assertTrue(app.protocol.last_result.ambiguous)
            self.assertEqual(app.protocol.last_result.command_retry_count, 0 if error == "HWE" else 1)
            self.assert_cache(app, ("DATA", "STATUS", "INFO"))

    def test_nonempty_response_plain_nak_and_bcc_response_retry(self):
        app, uart = self.app([ScenarioStep.ack_response("SP", "0")])
        self.assertEqual(app.execute_ate_line("PARAM_AUTO_CHARGE_2"), "ERR:FINAL_BCC_FRAME")
        self.assertEqual(uart.tx_log[-1], b"\x15")
        self.assert_cache(app, ("DATA", "STATUS", "INFO"))
        app, uart = self.app([ScenarioStep.bcc_ng_then_retry("SP")])
        self.assertEqual(app.execute_ate_line("PARAM_AUTO_CHARGE_2"), "OK")
        self.assertEqual((app.protocol.last_result.command_retry_count,
                          app.protocol.last_result.response_retry_count), (0, 1))
        self.assertIn(b"\x15", uart.tx_log)

    def test_invalid_values_rejected_even_without_connection(self):
        app = FixtureApp(protocol=None)
        self.assertEqual(app.execute_ate_line("PARAM_AUTO_CHARGE_4"), "ERR:PARAMETER_RANGE")
        self.assertEqual(app.execute_ate_line("PARAM_AUTO_CHARGE_2"), "ERR:NF55G_NOT_CONNECTED")
        with self.assertRaises(CommandError):
            build_control_command("PARAM_AUTO_CHARGE_2", payload="EXTRA")


if __name__ == "__main__":
    unittest.main()
