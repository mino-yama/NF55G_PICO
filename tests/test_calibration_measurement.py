"""DMM未接続で取得相関・古い値の拒否・試行境界を検証する。"""
import unittest

from src.calibration_measurement import CalibrationMeasurements, MeasurementError
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockUART, MockNF55GScenario
from src.nf55_protocol import NF55Protocol


class CalibrationMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.cache = CalibrationMeasurements()
        self.cache.start_trial()

    def acquire(self, target="DISCHG_I", point="A", text="+4.400000E-02", unit="V"):
        token = self.cache.begin(target, point)
        self.assertTrue(self.cache.complete(token, (text + "\r\n").encode(), text, unit))
        return token

    def test_three_systems_two_points_keep_raw_and_do_not_convert_shunt(self):
        tokens = [self.acquire(target, point) for target in
                  ("DISCHG_I", "BATT_CHG", "BATT_V") for point in ("A", "B")]
        self.assertEqual(len(set(tokens)), 6)
        for token in tokens:
            value = self.cache.get(token)
            self.assertEqual(value["raw"], b"+4.400000E-02\r\n")
            self.assertEqual(value["value_text"], "+4.400000E-02")
            self.assertEqual(value["unit"], "V")
            self.assertEqual((value["target"], value["point"]), token[2:])

    def test_snapshot_cannot_change_confirmed_measurement(self):
        token = self.acquire()
        self.cache.get(token)["value_text"] = "44"
        self.assertEqual(self.cache.get(token)["value_text"], "+4.400000E-02")

    def test_failed_reacquisition_never_restores_old_value(self):
        old = self.acquire()
        new = self.cache.begin("DISCHG_I", "A")
        self.assertTrue(self.cache.fail(new))
        for token in (old, new):
            with self.assertRaises(MeasurementError):
                self.cache.get(token)
        self.assertFalse(self.cache.complete(new, b"44", "44", "A"))

    def test_late_or_duplicate_reply_cannot_replace_confirmed_value(self):
        old = self.acquire()
        new = self.cache.begin("DISCHG_I", "A")
        self.assertFalse(self.cache.complete(old, b"999", "999", "V"))
        self.assertFalse(self.cache.fail(old))
        self.assertTrue(self.cache.complete(new, b"0.043", "0.043", "V"))
        self.assertFalse(self.cache.complete(new, b"999", "999", "V"))
        self.assertFalse(self.cache.fail(new))
        self.assertEqual(self.cache.get(new)["value_text"], "0.043")

    def test_wrong_point_or_trial_cannot_read_or_finish_request(self):
        token = self.cache.begin("BATT_V", "B")
        for other in ((token[0] + 1,) + token[1:], token[:3] + ("A",)):
            self.assertFalse(self.cache.complete(other, b"5.001", "5.001", "V"))
            with self.assertRaises(MeasurementError):
                self.cache.get(other)
        self.assertTrue(self.cache.complete(token, b"5.001", "5.001", "V"))

    def test_end_and_restart_reject_ready_pending_and_late_measurements(self):
        old = self.acquire()
        pending = self.cache.begin("BATT_V", "A")
        self.cache.end_trial()
        for token in (old, pending):
            with self.assertRaises(MeasurementError):
                self.cache.get(token)
        self.assertFalse(self.cache.complete(pending, b"8", "8", "V"))
        with self.assertRaises(MeasurementError):
            self.cache.begin("BATT_V", "A")
        self.cache.start_trial()
        new = self.cache.begin("BATT_V", "A")
        self.assertNotEqual(new, pending)
        self.assertFalse(self.cache.complete(pending, b"8", "8", "V"))
        self.assertTrue(self.cache.complete(new, b"8.001", "8.001", "V"))

    def test_restart_without_end_also_invalidates_previous_trial(self):
        old = self.acquire()
        pending = self.cache.begin("BATT_V", "A")
        self.cache.start_trial()
        with self.assertRaises(MeasurementError):
            self.cache.get(old)
        self.assertFalse(self.cache.complete(pending, b"8", "8", "V"))

    def test_bad_or_busy_request_preserves_other_confirmed_values(self):
        old = self.acquire()
        pending = self.cache.begin("BATT_V", "A")
        for target, point in (("12VOUT_I", "A"), ("BATT_V", "P1"), ("DISCHG_I", "A")):
            with self.assertRaises(MeasurementError):
                self.cache.begin(target, point)
        self.assertEqual(self.cache.get(old)["unit"], "V")
        self.assertTrue(self.cache.fail(pending))

    def test_invalid_numbers_raw_or_units_are_not_cached(self):
        cases = [(b"x", text, "V") for text in
                 ("", "NaN", "Inf", "OL", "1,2", " 1", "1\r\n", ".", "1.2.3", "1e", "1e+", "1e2e3", "１")]
        cases += [(b"", "1", "V"), (b"\xff", "1", "V"), ("測定", "1", "V"),
                  (bytearray(b"1"), "1", "V"), (b"1", "1", "uV")]
        for raw, text, unit in cases:
            with self.subTest(raw=raw, text=text, unit=unit):
                token = self.cache.begin("BATT_V", "A")
                with self.assertRaises(MeasurementError):
                    self.cache.complete(token, raw, text, unit)
                with self.assertRaises(MeasurementError):
                    self.cache.get(token)
                self.assertFalse(self.cache.complete(token, b"1", "1", "V"))

    def test_decimal_syntax_preserves_sign_precision_and_exponent(self):
        for text in ("0", "-0.000", "+.123", "8.", "1e-3", "1E+03"):
            token = self.acquire(text=text)
            self.assertEqual(self.cache.get(token)["value_text"], text)

    def test_discard_used_value_preserves_other_point_and_cannot_repeat(self):
        used = self.acquire()
        other = self.acquire(point="B")
        self.assertTrue(self.cache.discard(used))
        self.assertFalse(self.cache.discard(used))
        with self.assertRaises(MeasurementError):
            self.cache.get(used)
        self.assertEqual(self.cache.get(other)["point"], "B")

    def test_shunt_millivolts_to_amperes_for_each_current_calibration_point(self):
        for target, point, text in (("DISCHG_I", "A", "44.0123"),
                                    ("DISCHG_I", "B", "0.30012"),
                                    ("BATT_CHG", "A", "1.85001"),
                                    ("BATT_CHG", "B", "0.50002")):
            with self.subTest(target=target, point=point):
                token = self.acquire(target, point, text, "mV")
                candidate = self.cache.get_calibration(token)
                self.assertEqual(candidate["value_text"], text)
                self.assertEqual(candidate["unit"], "A")
                self.assertEqual(candidate["measurement_value_text"], text)
                self.assertEqual(candidate["measurement_unit"], "mV")
                self.assertEqual(candidate["raw"], (text + "\r\n").encode())
                self.assertEqual(candidate["token"], token)
                self.assertEqual(self.cache.get(token)["unit"], "mV")

    def test_shunt_conversion_preserves_sign_zero_precision_and_exponent(self):
        for text in ("-0.30000", "+4.40123E+01", "-0.000", "+.5000200"):
            token = self.acquire(text=text, unit="mV")
            self.assertEqual(self.cache.get_calibration(token)["value_text"], text)

    def test_battery_voltage_remains_volts_at_both_points(self):
        for point, text in (("A", "8.00123"), ("B", "5.00456")):
            token = self.acquire("BATT_V", point, text, "V")
            candidate = self.cache.get_calibration(token)
            self.assertEqual(candidate["unit"], "V")
            self.assertEqual(candidate["value_text"], text)

    def test_wrong_units_cannot_be_silently_relabelled_for_calibration(self):
        for target, units in (("DISCHG_I", ("V", "A")), ("BATT_CHG", ("V", "A")),
                              ("BATT_V", ("mV", "A"))):
            for unit in units:
                token = self.acquire(target, text="0.044", unit=unit)
                with self.assertRaisesRegex(MeasurementError, "CALIBRATION_UNIT"):
                    self.cache.get_calibration(token)
                self.assertEqual(self.cache.get(token)["unit"], unit)

    def test_calibration_candidate_cannot_survive_invalidation_or_mutate_raw_cache(self):
        token = self.acquire(unit="mV")
        self.cache.get_calibration(token)["value_text"] = "999"
        self.assertEqual(self.cache.get_calibration(token)["value_text"], "+4.400000E-02")
        self.cache.discard(token)
        with self.assertRaises(MeasurementError):
            self.cache.get_calibration(token)


class MeasurementTrialIntegrationTests(unittest.TestCase):
    def setUp(self):
        clock = FakeClock()
        self.uart = MockUART(clock, MockNF55GScenario([]))
        self.app = FixtureApp(protocol=NF55Protocol(self.uart, clock=clock))

    def acquire(self):
        token = self.app.measurements.begin("BATT_V", "A")
        self.app.measurements.complete(token, b"8.001\r\n", "8.001", "V")
        return token

    def test_ate_end_invalidates_ready_and_pending_without_nf55g_send(self):
        with self.assertRaises(MeasurementError):
            self.app.measurements.begin("BATT_V", "A")
        self.assertEqual(self.app.execute_ate_line("TEST_START"), "OK")
        ready = self.acquire()
        pending = self.app.measurements.begin("BATT_CHG", "B")
        self.assertEqual(self.app.execute_ate_line("TEST_END"), "OK")
        with self.assertRaises(MeasurementError):
            self.app.measurements.get(ready)
        self.assertFalse(self.app.measurements.complete(pending, b"0.5", "0.5", "A"))
        self.assertEqual(self.uart.tx_log, [])

    def test_ate_restart_invalidates_measurement_but_retains_history(self):
        self.app.execute_ate_line("TEST_START")
        token = self.acquire()
        self.assertEqual(self.app.execute_ate_line("TEST_START"), "OK")
        with self.assertRaises(MeasurementError):
            self.app.measurements.get(token)
        self.assertEqual(len(self.app.logger.test_history), 1)
        self.assertEqual(self.app.measurements.get(self.acquire())["value_text"], "8.001")
        self.assertEqual(self.uart.tx_log, [])

    def test_busy_rejected_start_and_end_preserve_measurement(self):
        self.app.execute_ate_line("TEST_START")
        token = self.acquire()
        self.app.logger.busy = lambda: True
        for command in ("TEST_START", "TEST_END"):
            self.assertEqual(self.app.execute_ate_line(command), "ERR:BUSY")
            self.assertEqual(self.app.measurements.get(token)["value_text"], "8.001")
        self.assertEqual(self.uart.tx_log, [])

    def test_queries_do_not_reacquire_and_ad_entry_is_not_enabled(self):
        self.app.execute_ate_line("TEST_START")
        token = self.acquire()
        self.assertEqual(self.app.execute_ate_line("BATT_VOLT?"), "ERR:CACHE_INVALID")
        self.assertTrue(self.app.execute_ate_line("AD_BATT_V_A_CACHE").startswith("ERR:"))
        self.assertEqual(self.app.measurements.get(token)["value_text"], "8.001")
        self.assertEqual(self.uart.tx_log, [])

    def test_current_conversion_on_parent_does_not_send_ad_or_modify_measurement(self):
        self.app.execute_ate_line("TEST_START")
        token = self.app.measurements.begin("DISCHG_I", "A")
        self.app.measurements.complete(token, b"44.012\r\n", "44.012", "mV")
        self.assertEqual(self.app.measurements.get_calibration(token)["unit"], "A")
        self.assertEqual(self.app.measurements.get_calibration(token)["value_text"], "44.012")
        self.assertEqual(self.app.measurements.get(token)["unit"], "mV")
        self.assertEqual(self.uart.tx_log, [])


if __name__ == "__main__":
    unittest.main()
