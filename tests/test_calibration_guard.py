"""校正範囲保護をATE入口からMock製品まで検証する。実機へは送信しない。"""
import struct
import unittest
from unittest.mock import patch

from src import calibration_guard as guard
from src.calibration_write import DIRECT_AD_TYPES
from src.frame import build_frame
from tests import test_direct_ad


class CalibrationGuardTests(unittest.TestCase):
    def fixture(self, target, point):
        from src.mock_nf55g import ScenarioStep
        helper = test_direct_ad.DirectADTests()
        type_point = DIRECT_AD_TYPES[target] + (b'1' if point == 'A' else b'2')
        helper.sample(ScenarioStep.ack_response('AD', type_point + b'00000144A8699A'))
        return helper, type_point

    def test_all_six_pairs_include_both_limits_on_direct_and_cache_paths(self):
        for target in guard.TARGETS:
            for point in ('A', 'B'):
                for suffix in ('LOWER', 'UPPER'):
                    value = str(getattr(guard.settings, target + '_' + point + '_' + suffix))
                    for direct in (True, False):
                        with self.subTest(target=target, point=point, value=value, direct=direct):
                            h, wire = self.fixture(target, point)
                            if direct:
                                command = 'AD_{}_{}_{}'.format(target, point, value)
                            else:
                                token = h.app.measurements.begin(target, point)
                                unit = 'V' if target == 'BATT_V' else 'mV'
                                h.app.measurements.complete(token, b'raw', value, unit)
                                h.ate('CAL_MEASUREMENT_{}? {}'.format(target, point))
                                command = 'CAL_WRITE_{} {}'.format(target, point)
                            reply = h.ate(command)
                            self.assertTrue(reply.startswith('OK:'), reply)
                            self.assertIn(build_frame('AD', wire + struct.pack('>f', float(value)).hex().upper().encode()), h.uart.tx_log)

    def test_just_outside_limits_is_rejected_even_when_float32_rounds_inside(self):
        for target in guard.TARGETS:
            for point in ('A', 'B'):
                for suffix, delta in (('LOWER', -1e-10), ('UPPER', 1e-10)):
                    boundary = getattr(guard.settings, target + '_' + point + '_' + suffix)
                    value = str(boundary + delta)
                    self.assertEqual(struct.pack('>f', boundary), struct.pack('>f', float(value)))
                    for direct in (True, False):
                        with self.subTest(target=target, point=point, suffix=suffix, direct=direct):
                            h, _ = self.fixture(target, point)
                            if direct:
                                command = 'AD_{}_{}_{}'.format(target, point, value)
                                prefix = 'AD_WRITE'
                            else:
                                token = h.app.measurements.begin(target, point)
                                h.app.measurements.complete(token, b'raw', value, 'V' if target == 'BATT_V' else 'mV')
                                h.ate('CAL_MEASUREMENT_{}? {}'.format(target, point))
                                command = 'CAL_WRITE_{} {}'.format(target, point)
                                prefix = 'CAL_WRITE'
                            before = list(h.uart.tx_log)
                            self.assertEqual(h.ate(command), 'ERR:' + prefix + '_RANGE')
                            self.assertEqual(h.uart.tx_log, before)

    def test_invalid_settings_fail_closed_for_every_required_pair(self):
        cases = (('DISCHG_I_A_LOWER', float('nan')), ('BATT_V_B_UPPER', float('inf')),
                 ('BATT_CHG_B_LOWER', True), ('BATT_CHG_A_LOWER', '1.48'),
                 ('BATT_V_A_LOWER', 10), ('SETTINGS_REV', ''),
                 ('BATT_V_B_LOWER', 1e-99))
        for key, value in cases:
            with patch.object(guard.settings, key, value):
                for target in guard.TARGETS:
                    for point in ('A', 'B'):
                        h, _ = self.fixture(target, point)
                        self.assertEqual(h.ate('AD_{}_{}_1.85'.format(target, point)), 'ERR:AD_WRITE_SETTINGS')
                        self.assertEqual(h.scenario.handled_command_count, 1)
        for settings in (None, object()):
            with patch.object(guard, 'settings', settings):
                h, _ = self.fixture('BATT_CHG', 'A')
                self.assertEqual(h.ate('AD_4_A_1.85'), 'ERR:AD_WRITE_SETTINGS')
                self.assertEqual(h.scenario.handled_command_count, 1)

    def test_rejected_candidate_preserves_caches_and_query_record(self):
        h, _ = self.fixture('BATT_CHG', 'A')
        self.assertTrue(h.ate('AD_4_A_1.85').startswith('OK:'))
        token = h.app.measurements.begin('DISCHG_I', 'A')
        h.app.measurements.complete(token, b'0V', '0', 'mV')
        h.ate('CAL_MEASUREMENT_DISCHG_I? A')
        h.app.cache.validate('DATA', {'old': 1}, 'D0')
        before = list(h.uart.tx_log)
        for command in ('CAL_WRITE_DISCHG_I A', 'AD_1_A_0', 'AD_1_A_-44'):
            self.assertTrue(h.ate(command).endswith('_RANGE'))
        self.assertEqual(h.uart.tx_log, before)
        self.assertEqual(h.app.measurements.get(token)['value_text'], '0')
        self.assertEqual(h.app.cache.get('DATA'), {'old': 1})
        self.assertEqual(h.app.calibration_write.queried[token[2:]], token)

    def test_old_and_double_point_commands_never_transmit(self):
        h, _ = self.fixture('BATT_CHG', 'A')
        for command in ('CAL_WRITE_BATT_CHG A P1', 'CAL_WRITE_BATT_CHG A B',
                        'AD_VERIFY_BATT_CHG P1', 'AD_VERIFY_BATT_CHG 1',
                        'AD_4_1_1.85', 'AD_4_P1_1.85', 'AD_4_2_0.5',
                        'CAL_WRITE 1-1-BATT_CHG-A P1'):
            with self.subTest(command=command):
                self.assertTrue(h.ate(command).startswith('ERR:'))
        self.assertEqual(h.scenario.handled_command_count, 1)

    def test_edited_settings_are_used_and_logged_without_numeric_fallback(self):
        with patch.object(guard.settings, 'BATT_CHG_A_LOWER', 3), patch.object(guard.settings, 'BATT_CHG_A_UPPER', 4):
            h, _ = self.fixture('BATT_CHG', 'A')
            self.assertEqual(h.ate('AD_4_A_1.85'), 'ERR:AD_WRITE_RANGE')
            self.assertIn('settings=' + guard.settings.SETTINGS_REV, str(h.app.logger.queue))
            self.assertTrue(h.ate('AD_4_A_3.5').startswith('OK:'))


if __name__ == '__main__':
    unittest.main()
