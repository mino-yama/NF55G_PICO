import struct
import unittest

from src.calibration_acquisition import acquisition_id
from src.frame import build_frame
from src.main import FixtureApp
from src.mock_nf55g import MockNF55GScenario, MockUART, ScenarioStep


D5_SAMPLE = b'S1.14BA1. 2601000001' + b'0' * 80
AD_RESPONSE = b'4100000144A8699A'
AR_RESPONSE = b'00000100000001' * 10


class CalibrationWriteIntegrationTests(unittest.TestCase):
    def set_up_sample(self, *steps, sample_enabled=True):
        self.scenario = MockNF55GScenario([ScenarioStep.ack_response('D5', D5_SAMPLE), *steps])
        self.uart = MockUART(scenario=self.scenario)
        self.app = FixtureApp(nf55_uart=self.uart, calibration_sample_enabled=sample_enabled)
        self.ate = self.app.execute_ate_line

    def acquire(self, value='+1.85'):
        token = self.app.measurements.begin('BATT_CHG', 'A')
        self.app.measurements.complete(token, b'original\r\n', value, 'mV')
        return acquisition_id(token)

    def test_explicit_write_consumes_cache_and_verify_compares_fraction_as_sent(self):
        self.set_up_sample(ScenarioStep.ack_response('AD', AD_RESPONSE), ScenarioStep.ack_response('AR', AR_RESPONSE))
        self.assertEqual(self.ate('TEST_START'), 'OK')
        measure = self.acquire()
        command = 'CAL_WRITE ' + measure
        self.assertEqual(self.ate(command), 'ERR:CAL_SAMPLE_IDENTITY')
        self.assertEqual(self.ate('INFO_REFRESH'), 'OK')
        self.assertEqual(self.ate(command), 'ERR:CAL_WRITE_NOT_QUERIED')
        self.assertEqual(self.ate('AD_VERIFY BATT_CHG A'), 'ERR:AD_VERIFY_NO_WRITE')
        self.assertTrue(self.ate('CAL_MEASUREMENT? ' + measure).startswith('OK:CAL_MEASUREMENT:'))
        self.assertEqual(self.scenario.handled_command_count, 1)
        self.assertEqual(self.ate(command), 'OK:CAL_WRITE')
        self.assertIn(build_frame('AD', b'413FECCCCD'), self.uart.tx_log)
        self.assertEqual(self.ate(command), 'ERR:CAL_MEASUREMENT_INVALID')
        self.assertNotIn(build_frame('AR'), self.uart.tx_log)
        self.assertEqual(self.ate('AD_VERIFY BATT_CHG A'), 'ERR:AD_VERIFY_MISMATCH')
        self.assertEqual(self.scenario.handled_command_count, 3)
        self.assertEqual(self.ate('TEST_END'), 'OK')
        self.assertEqual(self.ate('AD_VERIFY BATT_CHG A'), 'ERR:CAL_NO_ACTIVE_TRIAL')

    def test_ambiguous_ad_is_not_retried_and_invalidates_cache(self):
        self.set_up_sample(ScenarioStep.resp_timeout(), ScenarioStep.ack_response('AD', AD_RESPONSE))
        self.assertEqual(self.ate('TEST_START'), 'OK')
        self.assertEqual(self.ate('INFO_REFRESH'), 'OK')
        measure = self.acquire()
        self.ate('CAL_MEASUREMENT? ' + measure)
        self.app.cache.validate('DATA', {}, 'D0')
        self.app.cache.validate('AR', {}, 'AR')
        command = 'CAL_WRITE ' + measure
        self.assertEqual(self.ate(command), 'ERR:CAL_WRITE_RESP_TIMEOUT:AMBIGUOUS=1')
        self.assertEqual(self.scenario.handled_command_count, 2)
        self.assertFalse(self.app.cache.is_valid('DATA'))
        self.assertFalse(self.app.cache.is_valid('AR'))
        self.assertEqual(self.ate(command), 'ERR:CAL_MEASUREMENT_INVALID')
        self.assertEqual(self.ate('AD_VERIFY BATT_CHG A'), 'ERR:AD_VERIFY_NO_WRITE')

    def test_disabled_and_unsupported_destination_send_no_ad_or_ar(self):
        self.set_up_sample(sample_enabled=False)
        self.assertEqual(self.ate('AD_VERIFY BATT_CHG A'), 'ERR:CAL_WRITE_DISABLED')
        self.assertEqual(self.uart.tx_log, [])
        self.set_up_sample()
        self.assertEqual(self.ate('TEST_START'), 'OK')
        self.assertEqual(self.ate('INFO_REFRESH'), 'OK')
        measure = self.acquire('+9.178')
        self.ate('CAL_MEASUREMENT? ' + measure)
        self.assertEqual(self.ate('CAL_WRITE ' + measure + ' B'), 'ERR:CAL_WRITE_ARGUMENTS')
        self.assertEqual(self.scenario.handled_command_count, 1)

    def test_named_commands_use_current_cache_and_return_raw_readback_to_ate(self):
        self.set_up_sample(ScenarioStep.ack_response('AD', b'410000014(*444-+'),
                           ScenarioStep.ack_response('AR', AR_RESPONSE))
        self.assertEqual(self.ate('TEST_START'), 'OK')
        self.assertEqual(self.ate('INFO_REFRESH'), 'OK')
        command = 'CAL_WRITE_BATT_CHG A'
        self.acquire('+1.85')
        self.assertTrue(self.ate('CAL_MEASUREMENT_BATT_CHG? A').startswith('OK:CAL_MEASUREMENT:'))
        latest = self.acquire('+1.974')
        self.assertEqual(self.ate(command), 'ERR:CAL_WRITE_NOT_QUERIED')
        self.assertIn(latest, self.ate('CAL_MEASUREMENT_BATT_CHG? A'))
        value8 = struct.pack('>f', 1.974).hex().upper()
        self.assertEqual(self.ate(command), 'OK:CAL_WRITE:' + value8 + ':1:34282A3434342D2B')
        self.assertIn(build_frame('AD', ('41' + value8).encode()), self.uart.tx_log)
        self.assertEqual(self.ate('AD_VERIFY_BATT_CHG A'), 'OK:AD_VERIFY:BATT_CHG:A:' + value8 + ':00000001:1:1')
        self.assertEqual(self.ate('CAL_MEASUREMENT_BATT_CHG? A'), 'ERR:CAL_MEASUREMENT_INVALID')

    def test_three_circuits_use_explicit_product_points_and_keep_separate_records(self):
        cases = (('DISCHG_I', 'A', 'A', '11', 'mV', '+44.25'),
                 ('BATT_CHG', 'B', 'B', '42', 'mV', '+0.5'),
                 ('BATT_V', 'A', 'A', '21', 'V', '+8.125'))
        self.set_up_sample(*(ScenarioStep.ack_response('AD', type_point.encode() + b'00000144A8699A')
                             for _, _, _, type_point, _, _ in cases),
                           *(ScenarioStep.ack_response('AR', AR_RESPONSE) for _ in cases))
        self.assertEqual(self.ate('TEST_START'), 'OK')
        self.assertEqual(self.ate('INFO_REFRESH'), 'OK')
        for target, measurement_point, product_point, type_point, unit, value in cases:
            token = self.app.measurements.begin(target, measurement_point)
            self.app.measurements.complete(token, b'original\r\n', value, unit)
            self.assertIn(acquisition_id(token), self.ate(f'CAL_MEASUREMENT_{target}? {measurement_point}'))
            self.assertTrue(self.ate(f'CAL_WRITE_{target} {measurement_point}').startswith('OK:CAL_WRITE:'))
            value8 = struct.pack('>f', float(value)).hex().upper()
            self.assertIn(build_frame('AD', (type_point + value8).encode()), self.uart.tx_log)
        for target, _, product_point, _, _, value in cases:
            value8 = struct.pack('>f', float(value)).hex().upper()
            self.assertEqual(self.ate(f'AD_VERIFY_{target} {product_point}'),
                             f'OK:AD_VERIFY:{target}:{product_point}:{value8}:00000001:1:1')
        self.assertEqual(self.ate('AD_VERIFY_DISCHG_I B'), 'ERR:AD_VERIFY_NO_WRITE')
        self.assertEqual(self.scenario.handled_command_count, 7)

    def test_integer_value_and_adc_readback_must_both_match(self):
        readback = AR_RESPONSE[:84] + b'00000100000002' + AR_RESPONSE[98:]
        wrong_adc = readback[:84] + b'00000200000002' + readback[98:]
        self.set_up_sample(ScenarioStep.ack_response('AD', AD_RESPONSE),
                           ScenarioStep.ack_response('AR', wrong_adc),
                           ScenarioStep.ack_response('AR', readback))
        self.assertEqual(self.ate('TEST_START'), 'OK')
        self.assertEqual(self.ate('INFO_REFRESH'), 'OK')
        measure = self.acquire('+2.0')
        self.ate('CAL_MEASUREMENT? ' + measure)
        self.assertEqual(self.ate('CAL_WRITE ' + measure), 'OK:CAL_WRITE')
        self.assertEqual(self.ate('AD_VERIFY BATT_CHG A'), 'ERR:AD_VERIFY_MISMATCH')
        self.assertEqual(self.ate('AD_VERIFY BATT_CHG A'), 'OK:AD_VERIFY')


if __name__ == '__main__':
    unittest.main()
