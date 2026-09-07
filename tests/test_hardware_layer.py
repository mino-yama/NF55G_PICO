import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ate_uart import UARTByteTransport
from src.cache_manager import CacheManager
from src.command_parser import ParseError, parse_ate_command
from src.command_dispatcher import CommandDispatcher
from src.diagnostic import FixtureDiagnostics
from src.logger import Logger, MemorySDSink
from src.main import FixtureApp, create_fixture_app
from src.nf55_protocol import IDLE
from src.nf55_uart import NF55UARTTransport, _micropython_parity
from src.rtc_driver import DS3231RTC, FakeRTCDevice


class FakeRawUART:
    def __init__(self, rx=b""):
        self.rx = bytearray(rx)
        self.tx = []

    def any(self):
        return len(self.rx)

    def read(self, count=1):
        if not self.rx:
            return None
        data = bytes(self.rx[:count])
        del self.rx[:count]
        return data

    def write(self, data):
        self.tx.append(bytes(data))
        return len(data)


class HardwareLayerTests(unittest.TestCase):
    def test_uart_byte_transport_normalizes_none_read_and_bytes_write(self):
        raw = FakeRawUART(rx=b"abc")
        transport = UARTByteTransport(raw)

        self.assertEqual(transport.any(), 3)
        self.assertEqual(transport.read(2), b"ab")
        self.assertEqual(transport.read(2), b"c")
        self.assertEqual(transport.read(1), b"")

        self.assertEqual(transport.write("OK"), 2)
        self.assertEqual(raw.tx[-1], b"OK")

    def test_nf55_uart_transport_is_byte_io_only(self):
        raw = FakeRawUART(rx=b"\x06")
        transport = NF55UARTTransport(raw)

        self.assertEqual(transport.read(1), b"\x06")
        transport.write(b"D1")

        self.assertEqual(raw.tx[-1], b"D1")

    def test_nf55_parity_mapping(self):
        self.assertIsNone(_micropython_parity(None))
        self.assertEqual(_micropython_parity("even"), 0)
        self.assertEqual(_micropython_parity("odd"), 1)

        with self.assertRaises(Exception):
            _micropython_parity("mark")

    def test_fixture_self_check_ok_for_local_components(self):
        rtc = DS3231RTC(FakeRTCDevice())
        logger = Logger(sd_sink=MemorySDSink())
        diagnostics = FixtureDiagnostics(rtc=rtc, logger=logger, ate_uart=object(), nf55_uart=object())

        result = diagnostics.pico_self_check()

        self.assertTrue(result.ok)
        self.assertIn("RTC=OK", result.detail)
        self.assertIn("LOGGER=OK", result.detail)
        self.assertNotIn("PASS", result.ate_text())
        self.assertNotIn("FAIL", result.ate_text())

    def test_fixture_self_check_reports_missing_components(self):
        diagnostics = FixtureDiagnostics()

        result = diagnostics.pico_self_check()

        self.assertFalse(result.ok)
        self.assertIn("ATE_UART=UNAVAILABLE", result.detail)
        self.assertIn("NF55_UART=UNAVAILABLE", result.detail)

    def test_diagnostic_dispatcher_does_not_run_nf55g_check_without_unit(self):
        diagnostics = FixtureDiagnostics(rtc=DS3231RTC(FakeRTCDevice()), logger=Logger(), ate_uart=object(), nf55_uart=object())
        dispatcher = CommandDispatcher(protocol=None, cache=CacheManager(), diagnostics=diagnostics)

        result = dispatcher.execute_diagnostic("NF_COMM_CHECK?")

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "NF55G_NOT_CONNECTED")

    def test_diagnostic_dispatcher_returns_fixture_identity(self):
        diagnostics = FixtureDiagnostics(rtc=DS3231RTC(FakeRTCDevice()), logger=Logger(), ate_uart=object(), nf55_uart=object())
        dispatcher = CommandDispatcher(protocol=None, cache=CacheManager(), diagnostics=diagnostics)

        result = dispatcher.execute_diagnostic("*IDN?")

        self.assertTrue(result.ok)
        self.assertEqual(result.ate_response, "NF55G_PICO_FIXTURE,Rev.0")

    def test_fixture_app_host_bootstrap_does_not_require_hardware(self):
        app = create_fixture_app(enable_hardware=False)

        self.assertIsInstance(app, FixtureApp)
        self.assertIsNotNone(app.cache)
        self.assertIsNone(app.protocol)
        self.assertFalse(app.self_check().ok)

    def test_fixture_app_forbids_fw_update_without_nf55g_tx(self):
        app = create_fixture_app(enable_hardware=False)

        self.assertEqual(app.execute_ate_line("FW_UPDATE"), "ERR:FU_DISABLED")

    def test_fixture_app_control_requires_nf55g_connection(self):
        app = create_fixture_app(enable_hardware=False)

        self.assertEqual(app.execute_ate_line("CHARGE_ON"), "ERR:NF55G_NOT_CONNECTED")

    def test_fixture_app_routes_local_commands_without_nf55g(self):
        app = create_fixture_app(enable_hardware=False)

        self.assertEqual(app.execute_ate_line("*IDN?"), "NF55G_PICO_FIXTURE,Rev.0")
        self.assertEqual(app.execute_ate_line("SD_STATUS?"), "OK")
        self.assertEqual(app.execute_ate_line("NF_COMM_CHECK?"), "ERR:NF55G_NOT_CONNECTED")

    def test_parse_ate_command_classifies_local_and_control_commands(self):
        cases = {
            "SD_STATUS?": "LOGGER",
            "RTC_CHECK?": "RTC",
            "RTC_SET_20260907_120000": "RTC",
            "PICO_SELF_CHECK?": "DIAGNOSTIC",
            "CHARGE_ON": "CONTROL",
            "FW_UPDATE": "FORBIDDEN",
            "UNKNOWN?": "UNKNOWN",
        }

        for text, category in cases.items():
            self.assertEqual(parse_ate_command(text).category, category)

    def test_parse_ate_command_extracts_payload(self):
        parsed = parse_ate_command("PARAM_SET 0123456789")

        self.assertEqual(parsed.name, "PARAM_SET")
        self.assertEqual(parsed.payload, "0123456789")

    def test_parse_ate_command_rejects_empty(self):
        with self.assertRaises(ParseError):
            parse_ate_command("  ")

    def test_comm_status_reports_protocol_state(self):
        class Protocol:
            state = IDLE

        diagnostics = FixtureDiagnostics()
        result = diagnostics.comm_status(Protocol())

        self.assertTrue(result.ok)
        self.assertEqual(result.detail, "state=IDLE")


if __name__ == "__main__":
    unittest.main()
