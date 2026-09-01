import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.cache_manager import CacheManager
from src.command_dispatcher import CommandDispatcher
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART
from src.nf55_protocol import NF55Protocol
from src.rtc_driver import DS3231RTC, FakeRTCDevice, RTCDateTime, RTCError


class RTCDriverTests(unittest.TestCase):
    def make_dispatcher(self, present=True):
        clock = FakeClock()
        uart = MockUART(clock=clock, scenario=MockNF55GScenario([]))
        protocol = NF55Protocol(uart=uart, clock=clock)
        device = FakeRTCDevice(
            present=present,
            initial=RTCDateTime(2026, 9, 1, 12, 34, 56),
        )
        rtc = DS3231RTC(device)
        dispatcher = CommandDispatcher(protocol=protocol, cache=CacheManager(), rtc=rtc)
        return dispatcher, device, uart

    def test_rtc_date_time_datetime_queries(self):
        dispatcher, _device, _uart = self.make_dispatcher()

        self.assertEqual(dispatcher.execute_rtc("RTC_DATE?").ate_response, "20260901")
        self.assertEqual(dispatcher.execute_rtc("RTC_TIME?").ate_response, "123456")
        self.assertEqual(dispatcher.execute_rtc("RTC_DATETIME?").ate_response, "20260901_123456")

    def test_rtc_set_updates_ds3231_only_not_nf55g_sc(self):
        dispatcher, device, uart = self.make_dispatcher()

        result = dispatcher.execute_rtc("RTC_SET_20261231_235959")

        self.assertTrue(result.ok)
        self.assertEqual(result.ate_response, "OK")
        self.assertEqual(device.dt.datetime(), "20261231_235959")
        self.assertEqual(device.set_count, 1)
        self.assertEqual(uart.tx_count(), 0)

    def test_rtc_check_ok_and_ng(self):
        dispatcher, _device, _uart = self.make_dispatcher(present=True)
        self.assertEqual(dispatcher.execute_rtc("RTC_CHECK?").ate_response, "OK")

        dispatcher, _device, _uart = self.make_dispatcher(present=False)
        self.assertEqual(dispatcher.execute_rtc("RTC_CHECK?").ate_response, "NG")

    def test_rtc_missing_query_reports_error_without_nf55g_tx(self):
        dispatcher, _device, uart = self.make_dispatcher(present=False)

        result = dispatcher.execute_rtc("RTC_DATE?")

        self.assertFalse(result.ok)
        self.assertEqual(result.ate_response, "ERR:NO_RTC")
        self.assertEqual(uart.tx_count(), 0)

    def test_rtc_set_rejects_invalid_format_and_calendar(self):
        dispatcher, device, uart = self.make_dispatcher()

        bad_values = (
            "RTC_SET_20260901123456",
            "RTC_SET_20261301_000000",
            "RTC_SET_20260229_000000",
            "RTC_SET_20261231_246000",
        )
        for cmd in bad_values:
            with self.subTest(cmd=cmd):
                result = dispatcher.execute_rtc(cmd)
                self.assertFalse(result.ok)

        self.assertEqual(device.set_count, 0)
        self.assertEqual(uart.tx_count(), 0)

    def test_leap_day_is_accepted(self):
        dt = RTCDateTime.parse_ate("20280229_010203")
        self.assertEqual(dt.datetime(), "20280229_010203")

    def test_unknown_rtc_command(self):
        dispatcher, _device, _uart = self.make_dispatcher()

        result = dispatcher.execute_rtc("CLOCK_SYNC")

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "UNKNOWN_RTC_CMD")


if __name__ == "__main__":
    unittest.main()
