"""Manual ATE values must reach AD without a DMM or measurement Cache."""
import struct
import unittest

from src.calibration_write import DIRECT_AD_TYPES
from src.command_parser import parse_ate_command, ParseError
from src.frame import build_frame
from src.main import FixtureApp
from src.mock_nf55g import MockNF55GScenario, MockUART, ScenarioStep
from tests.test_calibration_write import D5_SAMPLE, AR_RESPONSE


class DirectADTests(unittest.TestCase):
    def sample(self, *steps, enabled=True):
        self.scenario = MockNF55GScenario([ScenarioStep.ack_response('D5', D5_SAMPLE), *steps])
        self.uart = MockUART(scenario=self.scenario)
        self.app = FixtureApp(nf55_uart=self.uart, calibration_sample_enabled=enabled)
        self.ate = self.app.execute_ate_line
        self.assertEqual(self.ate('TEST_START'), 'OK')
        self.assertEqual(self.ate('INFO_REFRESH'), 'OK')

    def test_all_five_types_and_two_points_encode_exact_manual_value(self):
        for target, type_byte in DIRECT_AD_TYPES.items():
            for point in ('A', 'B'):
                with self.subTest(target=target, point=point):
                    wire_point = b'1' if point == 'A' else b'2'
                    response = type_byte + wire_point + b'0000014(*444-+'
                    self.sample(ScenarioStep.ack_response('AD', response))
                    self.assertIsNone(self.app.external_link)
                    value = {'DISCHG_I': {'A': 44, 'B': 0.3}, 'BATT_CHG': {'A': 1.85, 'B': 0.5}, 'BATT_V': {'A': 8, 'B': 5}}.get(target, {'A': -1.85, 'B': -1.85})[point]
                    expected = struct.pack('>f', value).hex().upper()
                    cmd = 'AD_{}_{}_{}'.format(type_byte.decode(), point, value)
                    self.assertEqual(self.ate(cmd), 'OK:AD_WRITE:{}:{}:{}:1:34282A3434342D2B'.format(
                        type_byte.decode(), point, expected))
                    self.assertIn(build_frame('AD', type_byte + wire_point + expected.encode()), self.uart.tx_log)
                    self.assertNotIn(build_frame('AR'), self.uart.tx_log)
                    self.assertEqual(self.scenario.handled_command_count, 2)
                    rows = str(self.app.logger.queue)
                    self.assertIn('ATE_DIRECT', rows)
                    self.assertIn('value=' + str(value), rows)

    def test_named_type_and_product_point_aliases(self):
        self.assertEqual(parse_ate_command('AD_BATT_CHG_A_1.85').payload, ('BATT_CHG', 'A', '1.85'))
        self.assertEqual(parse_ate_command('AD_DISCHG_I_B_4.425e+1').payload, ('DISCHG_I', 'B', '4.425e+1'))

    def test_bad_input_is_rejected_before_any_transmission(self):
        app = FixtureApp()
        cases = {'AD_6_A_1.85': 'AD_TYPE', 'AD_4_3_1.85': 'AD_POINT',
                 'AD_4_1': 'AD_ARGUMENTS', 'AD_4_A_1.85 extra': 'AD_ARGUMENTS',
                 'AD_4_A_1.85A': 'AD_VALUE', 'AD_4_A_NaN': 'AD_VALUE',
                 'AD_4_A_inf': 'AD_VALUE', 'AD_4_A_0x3F800000': 'AD_VALUE',
                 'AD_4_A_1,85': 'AD_VALUE', 'AD_4_A_1e9999': 'AD_VALUE',
                 'AD_4_A_1e-9999': 'AD_VALUE', 'AD_4_A_3.5e38': 'AD_VALUE',
                 'AD_4_A_': 'AD_VALUE', 'AD_4_A_1_2': 'AD_TYPE'}
        for command, error in cases.items():
            with self.subTest(command=command):
                self.assertEqual(app.execute_ate_line(command), 'ERR:' + error)

    def test_manual_success_invalidates_product_and_same_circuit_measurement_cache(self):
        self.sample(ScenarioStep.ack_response('AD', b'4100000144A8699A'))
        for point in ('A', 'B'):
            token = self.app.measurements.begin('BATT_CHG', point)
            self.app.measurements.complete(token, b'raw', '+9.1', 'mV')
            self.ate('CAL_MEASUREMENT_BATT_CHG? ' + point)
        for cache in ('DATA', 'AR', 'STATUS'):
            self.app.cache.refresh_succeeded(cache, {'sentinel': 1}, 'test')
        self.assertTrue(self.ate('AD_4_A_1.85').startswith('OK:AD_WRITE:'))
        for cache in ('DATA', 'AR'):
            self.assertIsNone(self.app.cache.get(cache))
        self.assertIsNotNone(self.app.cache.get('STATUS'))
        self.assertIsNotNone(self.app.cache.get('INFO'))
        self.assertEqual(self.ate('CAL_MEASUREMENT_BATT_CHG? A'), 'ERR:CAL_MEASUREMENT_INVALID')
        self.assertEqual(self.ate('CAL_MEASUREMENT_BATT_CHG? B'), 'ERR:CAL_MEASUREMENT_INVALID')

    def test_manual_write_can_be_read_back_only_on_explicit_verify(self):
        self.sample(ScenarioStep.ack_response('AD', b'4100000144A8699A'),
                    ScenarioStep.ack_response('AR', AR_RESPONSE))
        self.assertTrue(self.ate('AD_4_A_1.85').startswith('OK:AD_WRITE:'))
        self.assertEqual(self.scenario.handled_command_count, 2)
        self.assertEqual(self.ate('AD_VERIFY_BATT_CHG A'),
                         'OK:AD_VERIFY:BATT_CHG:A:3FECCCCD:00000001:1:1')
        self.assertIsNone(self.app.cache.get('AR'))
        self.assertEqual(self.ate('AD_VERIFY_BATT_CHG B'), 'ERR:AD_VERIFY_NO_WRITE')
        self.assertEqual(self.ate('TEST_END'), 'OK')
        self.assertEqual(self.ate('AD_VERIFY_BATT_CHG A'), 'ERR:CAL_NO_ACTIVE_TRIAL')

    def test_ad_timeout_does_not_retry_and_clears_previous_write_record(self):
        self.sample(ScenarioStep.ack_response('AD', b'4100000144A8699A'), ScenarioStep.resp_timeout())
        self.ate('AD_4_A_1.5')
        self.assertEqual(self.ate('AD_4_A_1.85'), 'ERR:AD_WRITE_RESP_TIMEOUT:AMBIGUOUS=1')
        self.assertEqual(self.scenario.handled_command_count, 3)
        self.assertEqual(self.ate('AD_VERIFY_BATT_CHG A'), 'ERR:AD_VERIFY_NO_WRITE')

    def test_disabled_identity_and_no_trial_gates_send_nothing(self):
        app = FixtureApp()
        self.assertEqual(app.execute_ate_line('AD_4_A_1.85'), 'ERR:CAL_WRITE_DISABLED')
        self.sample()
        self.app.cache.invalidate_many(('INFO',))
        self.assertEqual(self.ate('AD_4_A_1.85'), 'ERR:CAL_SAMPLE_IDENTITY')
        self.assertEqual(self.ate('TEST_END'), 'OK')
        self.assertEqual(self.ate('AD_4_A_1.85'), 'ERR:CAL_NO_ACTIVE_TRIAL')
        self.assertEqual(self.scenario.handled_command_count, 1)

    def test_busy_gate_does_not_send(self):
        self.sample()
        self.app._comm_busy = lambda: True
        self.assertEqual(self.ate('AD_4_A_1.85'), 'ERR:BUSY')
        self.assertEqual(self.scenario.handled_command_count, 1)

    def test_wrong_ad_response_does_not_create_verify_record(self):
        self.sample(ScenarioStep.ack_response('AD', b'4200000144A8699A'))
        self.assertEqual(self.ate('AD_4_A_1.85'), 'ERR:AD_WRITE_RESPONSE:AMBIGUOUS=1')
        self.assertEqual(self.ate('AD_VERIFY_BATT_CHG A'), 'ERR:AD_VERIFY_NO_WRITE')

    def test_uart_exception_is_ambiguous_and_never_retried(self):
        self.sample()
        calls = []
        def fail(*args, **kwargs):
            calls.append((args, kwargs))
            raise OSError('UART')
        self.app.calibration_write.protocol.transact = fail
        self.assertEqual(self.ate('AD_4_A_1.85'), 'ERR:AD_WRITE_UART:AMBIGUOUS=1')
        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0][1]['allow_command_retry'])
        self.assertEqual(self.ate('AD_VERIFY_BATT_CHG A'), 'ERR:AD_VERIFY_NO_WRITE')


if __name__ == '__main__':
    unittest.main()
