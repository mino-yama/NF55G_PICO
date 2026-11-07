import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.cache_manager import CacheManager
from src.frame import parse_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.nf55_command import DATA_QUERY_FIELDS, STATUS_QUERY_FIELDS, INFO_QUERY_FIELDS
from src.nf55_protocol import NF55Protocol
from tests.test_decoder_complete import d0_payload


MFG_VALUES = ("010203", "0001", "0026", "000123", "0002", "0027", "000234",
              "0003", "0028", "000345")
D5 = "".join(MFG_VALUES) + "00" + "F" * 50
D2 = "000A000BFE00AFD06400A" + "0" * 9
D0 = "1A09010C2238" + "0" * 315


class ReadCacheIntegrationTests(unittest.TestCase):
    def make_app(self, steps=()):
        clock = FakeClock()
        uart = MockUART(clock, MockNF55GScenario(steps))
        cache = CacheManager(clock_ms=clock.ticks_ms)
        app = FixtureApp(protocol=NF55Protocol(uart, clock=clock), cache=cache)
        return app, uart

    def seed(self, app):
        for name in ("DATA", "STATUS", "INFO", "BC"):
            app.cache.validate(name, {"old": name}, "OLD")

    def test_d1_refresh_and_all_status_queries_no_additional_tx(self):
        app, uart = self.make_app([ScenarioStep.ack_response("D1", "F" * 15)])
        self.seed(app)
        self.assertEqual(app.execute_ate_line(b"STATUS_REFRESH\r\n"), "OK")
        self.assertEqual(parse_frame(uart.tx_log[0]).cmd, "D1")
        self.assertEqual(parse_frame(uart.tx_log[0]).data, b"")
        self.assertEqual(uart.tx_log[1:], [b"\x06"])
        tx_before = list(uart.tx_log)
        self.assertEqual(len(STATUS_QUERY_FIELDS), 37)
        for field in STATUS_QUERY_FIELDS:
            self.assertEqual(app.execute_ate_line(field + "?"), "1", field)
        self.assertEqual(uart.tx_log, tx_before)
        self.assertEqual(app.cache.metadata("STATUS")["source_cmd"], "D1")
        for name in ("DATA", "INFO", "BC"):
            self.assertEqual(app.cache.get(name), {"old": name})

    def test_d1_zero_flags(self):
        app, _ = self.make_app([ScenarioStep.ack_response("D1", "0" * 15)])
        self.assertEqual(app.execute_ate_line("STATUS_REFRESH"), "OK")
        for field in STATUS_QUERY_FIELDS:
            self.assertEqual(app.execute_ate_line(field + "?"), "0")

    def test_d0_refresh_uses_provisional_t2_and_populates_data_only(self):
        app, uart = self.make_app([ScenarioStep.ack_response("D0", D0)])
        self.seed(app)
        original = app.protocol.transact

        def checked(command, **kwargs):
            self.assertFalse(app.cache.is_valid("DATA"))
            self.assertEqual((command, kwargs),
                             ("D0", dict(data=b"", t2_ms=600, expected_length=327)))
            return original(command, **kwargs)

        app.protocol.transact = checked
        self.assertEqual(app.execute_ate_line("DATA_REFRESH"), "OK")
        self.assertEqual(parse_frame(uart.tx_log[0]).cmd, "D0")
        self.assertEqual(parse_frame(uart.tx_log[0]).data, b"")
        self.assertEqual(len(DATA_QUERY_FIELDS), 43)
        tx_after_refresh = list(uart.tx_log)
        self.assertEqual(app.execute_ate_line("NF55_DATETIME?"), "20260901_123456")
        self.assertEqual(app.execute_ate_line("CHARGE_END?"), "0")
        for query in DATA_QUERY_FIELDS:
            self.assertNotEqual(app.execute_ate_line(query), "ERR:CACHE_INVALID", query)
        self.assertEqual(uart.tx_log, tx_after_refresh)
        self.assertEqual(app.cache.metadata("DATA")["source_cmd"], "D0")
        self.assertNotIn("PS_ON", app.cache.get("DATA"))
        self.assertNotIn("FW_REV", app.cache.get("DATA"))
        self.assertEqual(app.cache.get("STATUS"), {"old": "STATUS"})
        self.assertEqual(app.cache.get("INFO"), {"old": "INFO"})

    def test_d0_decode_failure_leaves_data_invalid(self):
        invalid_d0 = "Z" + D0[1:]
        app, _ = self.make_app([ScenarioStep.ack_response("D0", invalid_d0)])
        self.seed(app)

        result = app.dispatcher.execute_refresh("DATA_REFRESH")

        self.assertEqual(result.ate_response, "ERR:DECODE")
        self.assertIsNone(app.cache.get("DATA"))
        self.assertEqual(app.cache.get("STATUS"), {"old": "STATUS"})
        self.assertEqual(app.cache.get("INFO"), {"old": "INFO"})

    def test_d0_battery_voltage_and_current_queries_use_volts_and_amperes(self):
        app, uart = self.make_app([ScenarioStep.ack_response("D0", d0_payload())])
        self.assertEqual(app.execute_ate_line("DATA_REFRESH"), "OK")
        tx_before = list(uart.tx_log)
        expected = {"BATT_VOLT?": "6.0", "CHG_VOLT?": "6.144",
                    "CHG_CURR?": "0.1", "BATT_CURR?": "0.016"}
        for query, value in expected.items():
            with self.subTest(query=query):
                self.assertEqual(app.execute_ate_line(query), value)
        self.assertEqual(uart.tx_log, tx_before)

    def test_d0_all_queries_return_expected_golden_values_without_transmit(self):
        app, uart = self.make_app([ScenarioStep.ack_response("D0", d0_payload())])
        self.seed(app)
        self.assertEqual(app.execute_ate_line("DATA_REFRESH"), "OK")
        expected = {
            "NF55_DATE?": "20260901", "NF55_TIME?": "123456",
            "NF55_DATETIME?": "20260901_123456", "VOUT12?": "12.0",
            "IOUT12?": "1.0", "BATT_VOLT?": "6.0", "CHG_VOLT?": "6.144",
            "CHG_CURR?": "0.1", "BATT_CURR?": "0.016", "BATT_SOC_WH?": "100",
            "BATT_SOC_MAH?": "-2", "BATT_TEMP?": "25", "ADU_TEMP?": "-10",
            "BBU_TEMP?": "0", "FAN_RPM?": "1234", "FAN_LEVEL?": "5",
            "AC_OFF_HOUR?": "1.0", "PS_OFF_HOUR?": "2.0", "AVE_OFF_TEMP?": "-10",
            "OFF_CHARGE_HOUR?": "1.5", "AVE_CHARGE_TEMP?": "25", "OFF_CHARGE?": "100",
            "OFF_BATT_DEG?": "12.3", "CHARGE_DATA?": "1", "CHARGE_END?": "0",
            "LIFE_BATT_CHARGE?": "100", "LIFE_BATT_TEMP?": "-10", "LIFE_BATT_DEG?": "12.3",
            "TOTAL_ADU_TEMP?": "1", "TOTAL_ADU_HOUR?": "2", "AC_FAIL_COUNT?": "3",
            "AC_LOW_COUNT?": "4", "BACKUP_COUNT?": "5", "BATT_DEG_TOTAL?": "12.3",
            "TOTAL_BATT_HOUR?": "6", "BATT_DISCHARGE_COUNT?": "7", "BATT_CHARGE_COUNT?": "8",
            "BATT_TTL_DISCHARGE?": "9", "BATT_TTL_CHARGE?": "10", "TOTAL_BATT_TEMP?": "11",
            "BATT_TEMP_AVE?": "-10", "BATT_TEMP_MAX?": "25", "BATT_TEMP_MIN?": "-128",
        }
        self.assertEqual(set(expected), set(DATA_QUERY_FIELDS))
        tx_before = list(uart.tx_log)
        for query, value in expected.items():
            with self.subTest(query=query):
                self.assertEqual(app.execute_ate_line(query), value)
        self.assertEqual(uart.tx_log, tx_before)
        self.assertEqual(app.cache.get("STATUS"), {"old": "STATUS"})
        self.assertEqual(app.cache.get("INFO"), {"old": "INFO"})

    def test_d0_rejects_non_hex_numeric_fields_without_validating_cache(self):
        for invalid_field in (" 001", "+001", "0x01"):
            with self.subTest(field=invalid_field):
                invalid_d0 = D0[:12] + invalid_field + D0[16:]
                app, uart = self.make_app([ScenarioStep.ack_response("D0", invalid_d0)])
                self.seed(app)
                self.assertEqual(app.execute_ate_line("DATA_REFRESH"), "ERR:DECODE")
                self.assertFalse(app.cache.is_valid("DATA"))
                self.assertEqual(app.execute_ate_line("VOUT12?"), "ERR:CACHE_INVALID")
                self.assertEqual(uart.tx_log[-1], b"\x06")

    def test_d0_rejects_out_of_range_time_fields(self):
        for invalid_time in ("6409010C2238", "1A00010C2238", "1A0D010C2238",
                             "1A09000C2238", "1A09200C2238", "1A0901182238",
                             "1A09010C3C38", "1A09010C223C"):
            with self.subTest(time=invalid_time):
                app, _ = self.make_app([ScenarioStep.ack_response("D0", invalid_time + D0[12:])])
                self.assertEqual(app.execute_ate_line("DATA_REFRESH"), "ERR:DECODE")
                self.assertFalse(app.cache.is_valid("DATA"))

    def test_ambiguous_d0_refresh_leaves_data_invalid(self):
        app, _ = self.make_app([ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()])
        self.seed(app)

        result = app.dispatcher.execute_refresh("DATA_REFRESH")

        self.assertEqual(result.ate_response, "ERR:ACK_TIMEOUT")
        self.assertTrue(result.transaction.ambiguous)
        self.assertIsNone(app.cache.get("DATA"))
        self.assertEqual(app.cache.get("STATUS"), {"old": "STATUS"})

    def test_d5_all_queries_preserve_text_and_convert_hex_to_decimal(self):
        app, uart = self.make_app([ScenarioStep.ack_response("D5", D5)])
        self.seed(app)
        self.assertEqual(app.execute_ate_line("INFO_REFRESH"), "OK")
        self.assertEqual(parse_frame(uart.tx_log[0]).cmd, "D5")
        self.assertEqual(parse_frame(uart.tx_log[0]).data, b"")
        tx_before = list(uart.tx_log)
        expected = MFG_VALUES + ("15", "15", "15", "15", "15", "255", "255",
                                "255", "65535", "255", "4095", "255", "255",
                                "255", "255", "65535")
        self.assertEqual(len(INFO_QUERY_FIELDS), len(expected))
        for field, value in zip(INFO_QUERY_FIELDS, expected):
            self.assertEqual(app.execute_ate_line(field + "?"), value, field)
        self.assertEqual(uart.tx_log, tx_before)
        self.assertEqual(app.cache.metadata("INFO")["source_cmd"], "D5")
        for name in ("DATA", "STATUS", "BC"):
            self.assertEqual(app.cache.get(name), {"old": name})

    def test_d2_refresh_decodes_off_period_and_invalidates_data(self):
        app, uart = self.make_app([ScenarioStep.ack_response("D2", D2)])
        self.seed(app)
        app.cache.validate("D2", {"old": "D2"}, "OLD")
        original = app.protocol.transact

        def checked(command, **kwargs):
            self.assertFalse(app.cache.is_valid("D2"))
            self.assertEqual((command, kwargs),
                             ("D2", dict(data=b"", t2_ms=100, expected_length=30)))
            return original(command, **kwargs)

        app.protocol.transact = checked
        self.assertEqual(app.execute_ate_line("D2_REFRESH"), "OK")
        self.assertEqual(parse_frame(uart.tx_log[0]).cmd, "D2")
        self.assertEqual(parse_frame(uart.tx_log[0]).data, b"")
        self.assertEqual(app.cache.get("D2"), {
            "AC_OFF_HOUR": 1.0,
            "PS_OFF_HOUR": 1.1,
            "AVE_OFF_TEMP": -2,
            "OFF_CHARGE_HOUR": 1.0,
            "AVE_CHARGE_TEMP": -3,
            "OFF_CHARGE": 100,
            "OFF_BATT_DEG": 1.0,
        })
        self.assertIsNone(app.cache.get("DATA"))
        self.assertEqual(app.cache.get("STATUS"), {"old": "STATUS"})
        self.assertEqual(app.cache.get("INFO"), {"old": "INFO"})

    def test_ambiguous_d2_refresh_invalidates_d2_and_data(self):
        app, _ = self.make_app([ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()])
        self.seed(app)
        app.cache.validate("D2", {"old": "D2"}, "OLD")

        result = app.dispatcher.execute_refresh("D2_REFRESH")

        self.assertEqual(result.ate_response, "ERR:ACK_TIMEOUT")
        self.assertTrue(result.transaction.ambiguous)
        self.assertIsNone(app.cache.get("D2"))
        self.assertIsNone(app.cache.get("DATA"))
        self.assertEqual(app.cache.get("STATUS"), {"old": "STATUS"})

    def test_d2_decode_failure_keeps_d2_invalid_and_invalidates_data(self):
        invalid_d2 = "Z" + D2[1:]
        app, _ = self.make_app([ScenarioStep.ack_response("D2", invalid_d2)])
        self.seed(app)
        app.cache.validate("D2", {"old": "D2"}, "OLD")

        result = app.dispatcher.execute_refresh("D2_REFRESH")

        self.assertEqual(result.ate_response, "ERR:DECODE")
        self.assertIsNone(app.cache.get("D2"))
        self.assertIsNone(app.cache.get("DATA"))

    def test_invalid_queries_never_transmit(self):
        app, uart = self.make_app()
        for field in STATUS_QUERY_FIELDS + INFO_QUERY_FIELDS:
            self.assertEqual(app.execute_ate_line(field + "?"), "ERR:CACHE_INVALID")
        self.assertEqual(uart.tx_log, [])

    def test_refresh_invalidates_before_transact_and_uses_spec_limits(self):
        for name, cmd, target, length in (("STATUS_REFRESH", "D1", "STATUS", 15),
                                          ("INFO_REFRESH", "D5", "INFO", 100)):
            app, _ = self.make_app([ScenarioStep.ack_response(cmd, "0" * length)])
            self.seed(app)
            original = app.protocol.transact

            def checked(command, **kwargs):
                self.assertFalse(app.cache.is_valid(target))
                self.assertIsNone(app.cache.get(target))
                self.assertEqual((command, kwargs),
                                 (cmd, dict(data=b"", t2_ms=100, expected_length=length)))
                return original(command, **kwargs)

            app.protocol.transact = checked
            self.assertEqual(app.execute_ate_line(name), "OK")

    def test_not_connected_refresh_discards_old_target_but_query_works_offline(self):
        app = FixtureApp()
        app.cache.validate("INFO", {"FW_REV": "000123"}, "D5")
        self.assertEqual(app.execute_ate_line("FW_REV?"), "000123")
        self.assertEqual(app.execute_ate_line("INFO_REFRESH"), "ERR:NF55G_NOT_CONNECTED")
        self.assertEqual(app.execute_ate_line("FW_REV?"), "ERR:CACHE_INVALID")

    def test_bad_arguments_and_unknown_queries_do_not_mutate_or_transmit(self):
        app, uart = self.make_app()
        self.seed(app)
        for command in ("STATUS_REFRESH extra", "INFO_REFRESH=", "PS_ON?=1", "FW_REV? x"):
            self.assertEqual(app.execute_ate_line(command), "ERR:UNEXPECTED_PAYLOAD")
        for command in ("R0_3?", "R13_0?", "UNKNOWN?"):
            self.assertEqual(app.execute_ate_line(command), "ERR:UNKNOWN_CMD")
        self.assertEqual(uart.tx_log, [])
        for name in ("DATA", "STATUS", "INFO", "BC"):
            self.assertEqual(app.cache.get(name), {"old": name})

    def test_decode_failure_never_restores_old_cache(self):
        for cmd, name, target, query, payload in (
            ("D1", "STATUS_REFRESH", "STATUS", "PS_ON?", "0" * 14 + "Z"),
            ("D5", "INFO_REFRESH", "INFO", "FW_REV?", D5[:78] + "Z" + D5[79:]),
        ):
            app, uart = self.make_app([ScenarioStep.ack_response(cmd, payload)])
            self.seed(app)
            result = app.dispatcher.execute_refresh(name)
            self.assertEqual(result.ate_response, "ERR:DECODE")
            self.assertTrue(result.transaction.ok)  # Protocol success is not decode success.
            self.assertFalse(app.cache.is_valid(target))
            before = list(uart.tx_log)
            self.assertEqual(app.execute_ate_line(query), "ERR:CACHE_INVALID")
            self.assertEqual(uart.tx_log, before)

    def test_partial_decode_dictionary_is_not_validated(self):
        app, _ = self.make_app([ScenarioStep.ack_response("D5", D5)])
        with patch("src.command_dispatcher.decode_d5", return_value={"FW_REV": "000123"}):
            self.assertEqual(app.execute_ate_line("INFO_REFRESH"), "ERR:DECODE")
        self.assertFalse(app.cache.is_valid("INFO"))

    def test_protocol_failures_leave_target_invalid(self):
        scenarios = (
            ([ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()], "ACK_TIMEOUT", True),
            ([ScenarioStep.resp_timeout(), ScenarioStep.resp_timeout()], "RESP_TIMEOUT", True),
            ([ScenarioStep.nak(), ScenarioStep.nak()], "NAK", False),
            ([ScenarioStep.error("PME")], "PME", False),
            ([ScenarioStep.bcc_ng("D1", "0" * 15)], "FINAL_BCC_FRAME", True),
            ([ScenarioStep.ack_response("D1", "0" * 14)], "FINAL_BCC_FRAME", True),
            ([ScenarioStep.ack_response("D5", "0" * 15)], "FINAL_BCC_FRAME", True),
        )
        for steps, error, ambiguous in scenarios:
            with self.subTest(error=error):
                app, _ = self.make_app(steps)
                self.seed(app)
                result = app.dispatcher.execute_refresh("STATUS_REFRESH")
                self.assertEqual(result.transaction.error, error)
                self.assertEqual(result.transaction.ambiguous, ambiguous)
                self.assertFalse(app.cache.is_valid("STATUS"))
                self.assertTrue(app.cache.is_valid("INFO"))

    def test_bcc_response_retry_then_valid_cache(self):
        app, uart = self.make_app([ScenarioStep.bcc_ng_then_retry("D5", D5)])
        result = app.dispatcher.execute_refresh("INFO_REFRESH")
        self.assertTrue(result.ok)
        self.assertEqual(result.transaction.command_retry_count, 0)
        self.assertEqual(result.transaction.response_retry_count, 1)
        self.assertEqual(uart.tx_log[1:], [b"\x15", b"\x06"])
        self.assertEqual(app.execute_ate_line("UNIT_SERIAL?"), "000123")

    def test_hwe_also_invalidates_data_status(self):
        app, _ = self.make_app([ScenarioStep.error("HWE")])
        self.seed(app)
        self.assertEqual(app.execute_ate_line("INFO_REFRESH"), "ERR:HWE")
        for target in ("DATA", "STATUS", "INFO"):
            self.assertFalse(app.cache.is_valid(target))
        self.assertTrue(app.cache.is_valid("BC"))

    def test_uart_oserror_is_ambiguous_and_target_stays_invalid(self):
        app, _ = self.make_app()
        self.seed(app)
        with patch.object(app.protocol, "transact", side_effect=OSError("port failed")):
            result = app.dispatcher.execute_refresh("INFO_REFRESH")
        self.assertEqual(result.ate_response, "ERR:UART")
        self.assertTrue(result.transaction.ambiguous)
        self.assertIsNone(result.transaction.elapsed_ms)
        self.assertFalse(app.cache.is_valid("INFO"))

    def test_control_invalidates_d1_cache_without_auto_refresh(self):
        app, uart = self.make_app([ScenarioStep.ack_response("D1", "F" * 15),
                                   ScenarioStep.ack_response("CN")])
        self.assertEqual(app.execute_ate_line("STATUS_REFRESH"), "OK")
        self.assertEqual(app.execute_ate_line("CHARGE_ON"), "OK")
        before = list(uart.tx_log)
        self.assertEqual(app.execute_ate_line("PS_ON?"), "ERR:CACHE_INVALID")
        self.assertEqual(app.execute_ate_line("FW_UPDATE"), "ERR:FU_DISABLED")
        self.assertEqual(uart.tx_log, before)
        self.assertEqual([parse_frame(tx).cmd for tx in uart.tx_log if tx.startswith(b"\x02")],
                         ["D1", "CN"])


if __name__ == "__main__":
    unittest.main()
