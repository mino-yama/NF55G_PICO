import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.cache_manager import CacheManager
from src.frame import FrameError, build_frame, calculate_bcc, parse_frame
from src.nf55_decode import decode_d0, decode_d1, decode_d3, decode_d5, decode_fd, decode_realtime


class FrameTests(unittest.TestCase):
    def test_bcc_excludes_stx_and_includes_etx(self):
        self.assertEqual(calculate_bcc("D1", ""), "76")

    def test_build_and_parse_frame(self):
        raw = build_frame("D1", "0123456789ABCDE")
        frame = parse_frame(raw, expected_cmd="D1", expected_length=15)
        self.assertEqual(frame.cmd, "D1")
        self.assertEqual(frame.data, b"0123456789ABCDE")

    def test_parse_rejects_bad_bcc(self):
        raw = build_frame("D1", "0")[:-1] + b"0"
        with self.assertRaises(FrameError):
            parse_frame(raw)


class CacheTests(unittest.TestCase):
    def test_power_on_invalid_and_validate(self):
        cache = CacheManager(clock_ms=lambda: 123)
        self.assertFalse(cache.is_valid("DATA"))
        cache.validate("DATA", {"VOUT12": 12.0}, "D0")
        self.assertTrue(cache.is_valid("DATA"))
        self.assertEqual(cache.get("DATA")["VOUT12"], 12.0)
        self.assertEqual(cache.metadata("DATA")["source_cmd"], "D0")

    def test_refresh_failure_does_not_restore_old_value(self):
        cache = CacheManager()
        cache.validate("DATA", {"old": True}, "D0")
        cache.refresh_started("DATA")
        cache.refresh_failed("DATA")
        self.assertFalse(cache.is_valid("DATA"))
        self.assertIsNone(cache.get("DATA"))

    def test_control_success_invalidation_matrix(self):
        cache = CacheManager()
        for name in ("DATA", "STATUS", "INFO"):
            cache.validate(name, {"ok": True}, name)
        cache.apply_success_invalidation("SP")
        self.assertFalse(cache.is_valid("DATA"))
        self.assertFalse(cache.is_valid("STATUS"))
        self.assertFalse(cache.is_valid("INFO"))


class DecodeTests(unittest.TestCase):
    def test_signed_and_scaled_realtime(self):
        data = (
            "2EE0"
            "0064"
            "1770"
            "1770"
            "00C8"
            "0096"
            "FE"
            "64"
            "19"
            "F6"
            "00"
            "007B"
            "5"
            + "0" * 11
        )
        decoded = decode_realtime(data)
        self.assertEqual(decoded["VOUT12"], 12.0)
        self.assertEqual(decoded["IOUT12"], 0.1)
        self.assertEqual(decoded["BATT_SOC_WH"], -2)
        self.assertEqual(decoded["BATT_TEMP"], 25)
        self.assertEqual(decoded["ADU_TEMP"], -10)
        self.assertEqual(decoded["FAN_RPM"], 123)
        self.assertEqual(decoded["FAN_LEVEL"], 5)

    def test_status_nibbles(self):
        decoded = decode_d1("308000000000000")
        self.assertTrue(decoded["BURST_ON"])
        self.assertTrue(decoded["CHARGE_READY"])
        self.assertTrue(decoded["PS_ON"])

    def test_d0_keeps_status_and_info_raw_only(self):
        payload = (
            "260901123456"
            + "0" * 50
            + "0" * 30
            + "0" * 20
            + "0" * 30
            + "0" * 70
            + "M" * 50
            + "P" * 50
            + "S" * 15
        )
        decoded = decode_d0(payload)
        self.assertEqual(decoded["DATE"], "20260901")
        self.assertEqual(decoded["MANUFACTURING_RAW"], "M" * 50)
        self.assertEqual(decoded["PARAMETER_RAW"], "P" * 50)
        self.assertEqual(decoded["STATUS_RAW"], "S" * 15)
        self.assertNotIn("FW_REV", decoded)
        self.assertNotIn("PS_ON", decoded)

    def test_d3_and_d5_lengths(self):
        self.assertEqual(decode_d3("0" * 21)["EVENT_LOST"], 0)
        decoded = decode_d5("A" * 50 + "0" * 50)
        self.assertEqual(decoded["FW_REV"], "AAAAAA")
        self.assertEqual(decoded["PS_ON_BACKUP"], 0)

    def test_fd_returns_raw_ascii_hex(self):
        payload = "0123456789ABCDEF" * 4
        self.assertEqual(decode_fd(payload)["FD_RAW"], payload)


if __name__ == "__main__":
    unittest.main()
