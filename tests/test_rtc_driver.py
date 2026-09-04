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
from src.rtc_driver import DS3231I2CDevice, DS3231RTC, FakeRTCDevice, RTCDateTime, RTCError


class FakeI2CBus:
    def __init__(self, present=True):
        self.present = present
        self.regs = bytearray(19)
        self.regs[0:7] = bytes.fromhex("42120001010100")
        self.regs[0x0F] = 0x88
        self.writes = []

    def scan(self):
        return [0x68] if self.present else []

    def readfrom_mem(self, address, register, length):
        if not self.present or address != 0x68:
            raise OSError("no i2c device")
        return bytes(self.regs[register : register + length])

    def writeto_mem(self, address, register, data):
        if not self.present or address != 0x68:
            raise OSError("no i2c device")
        payload = bytes(data)
        self.regs[register : register + len(payload)] = payload
        self.writes.append((address, register, payload))


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

    def test_ds3231_i2c_device_reads_bcd_datetime(self):
        i2c = FakeI2CBus()
        device = DS3231I2CDevice(i2c=i2c)

        dt = device.read_datetime()

        self.assertEqual(dt.datetime(), "20000101_001242")

    def test_ds3231_i2c_device_writes_bcd_datetime_and_clears_osf(self):
        i2c = FakeI2CBus()
        device = DS3231I2CDevice(i2c=i2c)

        device.set_datetime(RTCDateTime(2026, 9, 4, 13, 22, 57))

        self.assertEqual(i2c.regs[0:7].hex(), "57221305040926")
        self.assertEqual(i2c.regs[0x0F], 0x08)
        self.assertIn((0x68, 0x0F, b"\x08"), i2c.writes)

    def test_ds3231_i2c_device_check_reports_missing_device(self):
        device = DS3231I2CDevice(i2c=FakeI2CBus(present=False))

        self.assertFalse(device.check())


if __name__ == "__main__":
    unittest.main()
