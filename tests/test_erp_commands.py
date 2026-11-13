"""SET ERP: ATE入口からSE送信、応答長、再送、Cache規則までをMockで確認。"""
import unittest

from src import config
from src.cache_manager import CacheManager
from src.frame import parse_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.nf55_protocol import NF55Protocol


CASES = (("ERP_SET_1_0", b"1000"), ("ERP_SET_0_0", b"0000"),
         ("ERP_SET_0_1", b"0100"), ("ERP_SET_1_1", b"1100"))
STATUS = b"100000000000000"


class ErpCommandTests(unittest.TestCase):
    def make_app(self, steps):
        clock = FakeClock()
        uart = MockUART(clock, MockNF55GScenario(steps))
        protocol = NF55Protocol(uart, clock=clock)
        cache = CacheManager()
        for name in config.CACHE_NAMES:
            cache.validate(name, {"old": True}, "OLD")
        return FixtureApp(protocol=protocol, cache=cache), uart

    def assert_cache(self, app, invalid=()):
        for name in config.CACHE_NAMES:
            self.assertEqual(app.cache.is_valid(name), name not in invalid, name)
            if name not in invalid:
                self.assertEqual(app.cache.get(name), {"old": True}, name)

    def test_success_wire_t2_and_exact_invalidation(self):
        for name, data in CASES:
            with self.subTest(name=name):
                app, uart = self.make_app([
                    ScenarioStep.ack_response("SE", STATUS, response_delay_ms=99)])
                self.assertEqual(app.execute_ate_line(name + "\r\n"), "OK")
                frames = [tx for tx in uart.tx_log if tx.startswith(b"\x02")]
                self.assertEqual(len(frames), 1)
                frame = parse_frame(frames[0], expected_cmd="SE")
                self.assertEqual(frame.data, data)
                self.assert_cache(app, ("DATA", "STATUS"))
                result = app.protocol.last_result
                self.assertEqual(result.response_data, STATUS)
                self.assertFalse(result.ambiguous)
                self.assertEqual((result.command_retry_count, result.response_retry_count), (0, 0))
                # Control応答を昇格せず、Queryから自動Refreshもしない。
                before = list(uart.tx_log)
                for query in ("BURST?", "BURST_ON?", "PS_OFF_CHARGE?", "NF55_DATETIME?"):
                    self.assertEqual(app.execute_ate_line(query), "ERR:CACHE_INVALID")
                self.assertEqual(uart.tx_log, before)

    def test_explicit_status_refresh_after_set(self):
        for name, data in CASES:
            with self.subTest(name=name):
                # D1の第2桁bit3=BURST、bit2=PS_OFF_CHARGE。SE応答を使わず明示取得する。
                status_digit = (8 if data[0:1] == b"1" else 0) | (4 if data[1:2] == b"1" else 0)
                refreshed = ("0{:X}".format(status_digit) + "0" * 13).encode("ascii")
                app, uart = self.make_app([ScenarioStep.ack_response("SE", STATUS),
                                          ScenarioStep.ack_response("D1", refreshed)])
                self.assertEqual(app.execute_ate_line(name), "OK")
                self.assertEqual(app.execute_ate_line("STATUS_REFRESH"), "OK")
                self.assertEqual(app.execute_ate_line("BURST?"), data[0:1].decode("ascii"))
                self.assertEqual(app.execute_ate_line("PS_OFF_CHARGE?"), data[1:2].decode("ascii"))
                self.assertEqual(app.cache.metadata("STATUS")["source_cmd"], "D1")
                self.assertFalse(app.cache.is_valid("DATA"))
                self.assertEqual([parse_frame(tx).cmd for tx in uart.tx_log if tx.startswith(b"\x02")],
                                 ["SE", "D1"])

    def test_ack_timeout_one_command_retry_and_invalidation(self):
        for name, data in CASES:
            with self.subTest(name=name):
                app, uart = self.make_app([ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()])
                self.assertEqual(app.execute_ate_line(name), "ERR:ACK_TIMEOUT")
                result = app.protocol.last_result
                self.assertTrue(result.ambiguous)
                self.assertEqual((result.command_retry_count, result.response_retry_count), (1, 0))
                frames = [parse_frame(tx) for tx in uart.tx_log if tx.startswith(b"\x02")]
                self.assertEqual([(f.cmd, f.data) for f in frames], [("SE", data)] * 2)
                self.assert_cache(app, ("DATA", "STATUS"))

    def test_response_after_t2_is_not_success(self):
        for name, data in CASES:
            with self.subTest(name=name):
                app, uart = self.make_app([
                    ScenarioStep.ack_response("SE", STATUS, response_delay_ms=101),
                    ScenarioStep.resp_timeout()])
                self.assertNotEqual(app.execute_ate_line(name), "OK")
                self.assertTrue(app.protocol.last_result.ambiguous)
                self.assertEqual(app.protocol.last_result.command_retry_count, 1)
                self.assert_cache(app, ("DATA", "STATUS"))

    def test_response_timeout(self):
        for name, data in CASES:
            with self.subTest(name=name):
                app, uart = self.make_app([ScenarioStep.resp_timeout(), ScenarioStep.resp_timeout()])
                self.assertEqual(app.execute_ate_line(name), "ERR:RESP_TIMEOUT")
                self.assertTrue(app.protocol.last_result.ambiguous)
                self.assertEqual(app.protocol.last_result.command_retry_count, 1)
                self.assert_cache(app, ("DATA", "STATUS"))

    def test_wrong_response_length_plain_nak_and_invalidation(self):
        for name, data in CASES:
            for size in (0, 14, 16):
                with self.subTest(name=name, size=size):
                    app, uart = self.make_app([ScenarioStep.ack_response("SE", b"0" * size)])
                    self.assertEqual(app.execute_ate_line(name), "ERR:FINAL_BCC_FRAME")
                    self.assertTrue(app.protocol.last_result.ambiguous)
                    self.assertEqual(uart.tx_log[-1], b"\x15")
                    self.assert_cache(app, ("DATA", "STATUS"))

    def test_bcc_response_retry_is_separate_from_command_retry(self):
        for name, data in CASES:
            with self.subTest(name=name):
                app, uart = self.make_app([ScenarioStep.bcc_ng_then_retry("SE", STATUS)])
                self.assertEqual(app.execute_ate_line(name), "OK")
                self.assertIn(b"\x15", uart.tx_log)
                self.assertEqual((app.protocol.last_result.command_retry_count,
                                  app.protocol.last_result.response_retry_count), (0, 1))
                self.assertEqual(len([tx for tx in uart.tx_log if tx.startswith(b"\x02")]), 1)
                self.assert_cache(app, ("DATA", "STATUS"))

    def test_final_bcc_error_is_ambiguous(self):
        for name, data in CASES:
            with self.subTest(name=name):
                app, uart = self.make_app([ScenarioStep.bcc_ng("SE", STATUS)])
                self.assertEqual(app.execute_ate_line(name), "ERR:FINAL_BCC_FRAME")
                self.assertTrue(app.protocol.last_result.ambiguous)
                self.assertEqual(uart.tx_log[-1], b"\x15")
                self.assert_cache(app, ("DATA", "STATUS"))

    def test_product_rejection_preserves_cache(self):
        for name, data in CASES:
            for error in ("SQE", "PME"):
                with self.subTest(name=name, error=error):
                    app, uart = self.make_app([ScenarioStep.error(error)])
                    self.assertEqual(app.execute_ate_line(name), "ERR:" + error)
                    self.assertFalse(app.protocol.last_result.ambiguous)
                    self.assert_cache(app)

    def test_invalid_name_or_payload_never_transmits(self):
        lines = [name + suffix for name, data in CASES for suffix in (" EXTRA", "=1")]
        lines += ["ERP_SET_2_0", "ERP_SET_0_2", "ERP_SET_1_2", "ERP_SET_0", "ERP_SET_1_0_0", "ERP_SET"]
        for line in lines:
            with self.subTest(line=line):
                app, uart = self.make_app([])
                self.assertTrue(app.execute_ate_line(line).startswith("ERR:"))
                self.assertEqual(uart.tx_log, [])
                self.assert_cache(app)


if __name__ == "__main__":
    unittest.main()
