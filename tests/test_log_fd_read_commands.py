"""EL/OLブロック読出しとFD読出しのATE・Cache・異常系をHostで確認する。"""
import unittest
from src import config
from src.cache_manager import CacheManager
from src.frame import parse_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.nf55_protocol import NF55Protocol

BLOCKS = [(kind, start) for kind, limit in (("EL", 32), ("OL", 64))
          for start in range(1, limit + 1, 8)]
RAW_FD = "0123456789aBcDeF" * 4


def log_data(start, empty=False):
    records = ["00000000FF" if empty else "1A0B0910{:02X}".format(n)
               for n in range(start, start + 8)]
    return "{:02X}".format(start) + "".join(records)


class ReadLogFdTests(unittest.TestCase):
    def app(self, steps, seeded=True):
        clock = FakeClock()
        uart = MockUART(clock, MockNF55GScenario(steps))
        cache = CacheManager()
        if seeded:
            for target in config.CACHE_NAMES:
                cache.validate(target, {"old": True}, "OLD")
        return FixtureApp(protocol=NF55Protocol(uart, clock=clock), cache=cache), uart

    def test_all_log_blocks_wire_and_all_record_queries(self):
        for kind, start in BLOCKS:
            with self.subTest(kind=kind, start=start):
                app, uart = self.app([ScenarioStep.ack_response(kind, log_data(start), response_delay_ms=99)])
                target = "{}_{:02d}".format(kind, start)
                self.assertEqual(app.execute_ate_line("{}_REFRESH_{:02d}\r\n".format(kind, start)), "OK")
                frame = parse_frame(uart.tx_log[0])
                self.assertEqual((frame.cmd, frame.data), (kind, "{:02X}".format(start).encode()))
                self.assertEqual(app.cache.metadata(target)["source_cmd"], kind)
                before = list(uart.tx_log)
                for number in range(start, start + 8):
                    self.assertEqual(app.execute_ate_line("{}_{:02d}_DATEHOUR?".format(kind, number)), "26110916")
                    self.assertEqual(app.execute_ate_line("{}_{:02d}_ID?".format(kind, number)), str(number))
                self.assertEqual(uart.tx_log, before)
                for other in config.CACHE_NAMES:
                    if other != target:
                        self.assertEqual(app.cache.get(other), {"old": True})

    def test_empty_logs_and_block_cache_isolation(self):
        for kind in ("EL", "OL"):
            app, uart = self.app([ScenarioStep.ack_response(kind, log_data(9, empty=True))], seeded=False)
            self.assertEqual(app.execute_ate_line(kind + "_REFRESH_09"), "OK")
            before = list(uart.tx_log)
            for number in range(9, 17):
                self.assertEqual(app.execute_ate_line("{}_{:02d}_DATEHOUR?".format(kind, number)), "00000000")
                self.assertEqual(app.execute_ate_line("{}_{:02d}_ID?".format(kind, number)), "255")
            self.assertEqual(app.execute_ate_line(kind + "_01_ID?"), "ERR:CACHE_INVALID")
            self.assertEqual(app.execute_ate_line(kind + "_17_ID?"), "ERR:CACHE_INVALID")
            self.assertEqual(uart.tx_log, before)

    def test_fd_address_wire_and_raw_preservation(self):
        for address in ("000000", "001aBc", "FFFFFF"):
            with self.subTest(address=address):
                app, uart = self.app([ScenarioStep.ack_response("FD", RAW_FD, response_delay_ms=99)])
                self.assertEqual(app.execute_ate_line("FD_READ_" + address), "OK")
                frame = parse_frame(uart.tx_log[0])
                self.assertEqual((frame.cmd, frame.data), ("FD", address.encode()))
                before = list(uart.tx_log)
                self.assertEqual(app.execute_ate_line("FD_DATA?"), RAW_FD)
                self.assertEqual(uart.tx_log, before)
                self.assertEqual(app.cache.metadata("FD")["source_cmd"], "FD")
                for other in config.CACHE_NAMES:
                    if other != "FD":
                        self.assertEqual(app.cache.get(other), {"old": True})

    def test_target_invalid_before_tx_and_no_old_restore(self):
        for line, target in (("EL_REFRESH_17", "EL_17"), ("OL_REFRESH_57", "OL_57"), ("FD_READ_000001", "FD")):
            app, uart = self.app([ScenarioStep.error("PME")])
            original_write = uart.write
            def write(data):
                self.assertFalse(app.cache.is_valid(target))
                return original_write(data)
            uart.write = write
            self.assertEqual(app.execute_ate_line(line), "ERR:PME")
            self.assertFalse(app.cache.is_valid(target))
            self.assertEqual(app.cache.get("DATA"), {"old": True})

    def test_wrong_start_bad_datetime_and_nonhex_reject_entire_block(self):
        payloads = [log_data(9), "01" + "1A0D011001" * 8,
                    "01" + "1A021E1001" * 8, "01" + "1A0B09GG01" * 8,
                    log_data(1)[:-1] + "Z"]
        for kind in ("EL", "OL"):
            for payload in payloads:
                with self.subTest(kind=kind, payload=payload):
                    app, uart = self.app([ScenarioStep.ack_response(kind, payload)])
                    self.assertEqual(app.execute_ate_line(kind + "_REFRESH_01"), "ERR:DECODE")
                    self.assertFalse(app.cache.is_valid(kind + "_01"))
                    self.assertEqual(app.execute_ate_line(kind + "_01_ID?"), "ERR:CACHE_INVALID")
                    self.assertTrue(app.cache.is_valid(kind + "_09"))

    def test_bad_fd_hex_invalidates_fd(self):
        app, uart = self.app([ScenarioStep.ack_response("FD", "Z" + "0" * 63)])
        self.assertEqual(app.execute_ate_line("FD_READ_000000"), "ERR:DECODE")
        self.assertEqual(app.execute_ate_line("FD_DATA?"), "ERR:CACHE_INVALID")

    def test_bad_frame_length_plain_nak_and_retry_counts(self):
        for line, cmd, target, length in (("EL_REFRESH_01", "EL", "EL_01", 82),
                                         ("OL_REFRESH_01", "OL", "OL_01", 82),
                                         ("FD_READ_000000", "FD", "FD", 64)):
            for size in (length - 1, length + 1):
                app, uart = self.app([ScenarioStep.ack_response(cmd, "0" * size)])
                self.assertEqual(app.execute_ate_line(line), "ERR:FINAL_BCC_FRAME")
                self.assertTrue(app.protocol.last_result.ambiguous)
                self.assertEqual(uart.tx_log[-1], b"\x15")
                self.assertFalse(app.cache.is_valid(target))

    def test_timeouts_t2_and_command_retry(self):
        for line, cmd, target in (("EL_REFRESH_25", "EL", "EL_25"),
                                  ("OL_REFRESH_57", "OL", "OL_57"),
                                  ("FD_READ_FFFFFF", "FD", "FD")):
            for step, error in ((ScenarioStep.ack_timeout, "ACK_TIMEOUT"),
                                (ScenarioStep.resp_timeout, "RESP_TIMEOUT")):
                app, uart = self.app([step(), step()])
                self.assertEqual(app.execute_ate_line(line), "ERR:" + error)
                result = app.protocol.last_result
                self.assertTrue(result.ambiguous)
                self.assertEqual((result.command_retry_count, result.response_retry_count), (1, 0))
                self.assertFalse(app.cache.is_valid(target))
                self.assertEqual(len([tx for tx in uart.tx_log if tx.startswith(b"\x02")]), 2)
            payload = log_data(25 if cmd == "EL" else 57) if cmd != "FD" else RAW_FD
            app, uart = self.app([ScenarioStep.ack_response(cmd, payload, response_delay_ms=101),
                                  ScenarioStep.resp_timeout()])
            self.assertNotEqual(app.execute_ate_line(line), "OK")
            self.assertFalse(app.cache.is_valid(target))

    def test_response_retry_without_command_retry(self):
        for line, cmd, payload in (("EL_REFRESH_17", "EL", log_data(17)),
                                   ("OL_REFRESH_33", "OL", log_data(33)),
                                   ("FD_READ_000000", "FD", RAW_FD)):
            app, uart = self.app([ScenarioStep.bcc_ng_then_retry(cmd, payload)])
            self.assertEqual(app.execute_ate_line(line), "OK")
            self.assertIn(b"\x15", uart.tx_log)
            self.assertEqual((app.protocol.last_result.command_retry_count,
                              app.protocol.last_result.response_retry_count), (0, 1))

    def test_parser_rejection_no_tx_no_cache_change(self):
        bad = ["FD_READ_", "FD_READ_00000", "FD_READ_0000000", "FD_READ_00000G", "FD_READ_０00000",
               "EL_REFRESH_00", "EL_REFRESH_02", "EL_REFRESH_33", "OL_REFRESH_65",
               "EL_00_ID?", "EL_33_ID?", "OL_65_ID?", "EL_1_ID?", "EL_01_OTHER?"]
        valid = ["EL_REFRESH_01", "OL_REFRESH_57", "FD_READ_000000", "EL_01_ID?", "FD_DATA?"]
        bad += [name + suffix for name in valid for suffix in (" EXTRA", "=1")]
        for line in bad:
            with self.subTest(line=line):
                app, uart = self.app([])
                self.assertTrue(app.execute_ate_line(line).startswith("ERR:"))
                self.assertEqual(uart.tx_log, [])
                self.assertTrue(all(app.cache.is_valid(n) for n in config.CACHE_NAMES))

    def test_no_connection_invalidates_refresh_target_queries_do_not_connect(self):
        app = FixtureApp(protocol=None)
        for line, target in (("EL_REFRESH_01", "EL_01"), ("OL_REFRESH_57", "OL_57"), ("FD_READ_000000", "FD")):
            app.cache.validate(target, {"old": True}, "OLD")
            self.assertEqual(app.execute_ate_line(line), "ERR:NF55G_NOT_CONNECTED")
            self.assertFalse(app.cache.is_valid(target))
        self.assertEqual(app.execute_ate_line("FD_DATA?"), "ERR:CACHE_INVALID")

    def test_hwe_invalidates_data_status_and_target(self):
        app, uart = self.app([ScenarioStep.error("HWE")])
        self.assertEqual(app.execute_ate_line("EL_REFRESH_09"), "ERR:HWE")
        for target in ("DATA", "STATUS", "EL_09"):
            self.assertFalse(app.cache.is_valid(target))
        self.assertTrue(app.cache.is_valid("INFO"))

    def test_clear_log_invalidates_all_blocks_then_explicit_read(self):
        app, uart = self.app([ScenarioStep.ack_response("CL"),
                              ScenarioStep.ack_response("EL", log_data(1, empty=True))])
        self.assertEqual(app.execute_ate_line("CLEAR_LOG"), "OK")
        before = list(uart.tx_log)
        for kind, limit in (("EL", 32), ("OL", 64)):
            for number in range(1, limit + 1):
                self.assertEqual(app.execute_ate_line("{}_{:02d}_ID?".format(kind, number)), "ERR:CACHE_INVALID")
        self.assertEqual(uart.tx_log, before)
        self.assertEqual(app.execute_ate_line("EL_REFRESH_01"), "OK")
        self.assertEqual(app.execute_ate_line("EL_01_ID?"), "255")
        self.assertFalse(app.cache.is_valid("OL_01"))


if __name__ == "__main__":
    unittest.main()
