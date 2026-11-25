from collections import deque
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from calibration_candidate import SampleCalibrationCommands
from src.calibration_acquisition import acquisition_id, measurement_reply
from src.calibration_measurement import CalibrationMeasurements
from src.models import TransactionResult


class CalibrationWriteTests(unittest.TestCase):
    def setUp(self):
        self.results = deque()
        self.transactions = []
        self.logs = []
        self.invalidated = []
        self.measured = CalibrationMeasurements()
        self.measured.start_trial()
        self.token = self.measured.begin('BATT_CHG', 'A')
        self.measured.complete(self.token, b'+001.8500E-03\r\n', '+001.8500E+00', 'mV')
        self.id = acquisition_id(self.token)
        self.app = SimpleNamespace(measurements=self.measured, _comm_busy=lambda: False,
                                   protocol=SimpleNamespace(transact=self.transact),
                                   cache=SimpleNamespace(invalidate_many=self.invalidated.extend),
                                   logger=SimpleNamespace(trial_id='T000001', test_running=True,
                                                          log=lambda **item: self.logs.append(item)),
                                   _execute_ate_line=lambda command: measurement_reply(self.measured, self.token))
        self.execute = SampleCalibrationCommands(self.app)

    def transact(self, cmd, data, **options):
        self.transactions.append((cmd, data, options))
        return self.results.popleft()

    def test_cache_write_then_explicit_ar_reports_fraction_mismatch(self):
        command = 'CAL_WRITE ' + self.id + ' P1'
        self.assertEqual(self.execute(command), 'ERR:CAL_WRITE_NOT_QUERIED')
        self.assertTrue(self.execute('CAL_MEASUREMENT? ' + self.id).startswith('OK:CAL_MEASUREMENT:'))
        self.assertEqual(self.transactions, [])
        self.results.append(TransactionResult(True, 'AD', b'4100000144A8699A'))
        self.assertEqual(self.execute(command), 'OK:CAL_WRITE')
        self.assertEqual(self.transactions, [('AD', b'413FECCCCD', {'t2_ms': 1000, 'expected_length': 16})])
        self.assertEqual(self.invalidated, ['DATA', 'AR'])
        self.assertEqual(self.execute(command), 'ERR:CAL_MEASUREMENT_INVALID')
        self.results.append(TransactionResult(True, 'AR', b'00000100000001' * 10))
        self.assertEqual(self.execute('AD_VERIFY BATT_CHG P1'), 'ERR:AD_VERIFY_MISMATCH')
        self.assertEqual(self.transactions[-1][0], 'AR')
        self.assertIn('REF8=00000001', self.logs[-1]['detail'])
        self.app.logger.trial_id = 'T000002'
        self.assertEqual(self.execute('AD_VERIFY BATT_CHG P1'), 'ERR:AD_VERIFY_NO_WRITE')
        self.assertEqual(len(self.transactions), 2)

    def test_ambiguous_write_consumes_measurement_without_enabling_verify(self):
        self.execute('CAL_MEASUREMENT? ' + self.id)
        self.results.append(TransactionResult(False, 'AD', error='RESP_TIMEOUT', ambiguous=True))
        self.assertEqual(self.execute('CAL_WRITE ' + self.id + ' P1'), 'ERR:CAL_WRITE_RESP_TIMEOUT:AMBIGUOUS=1')
        self.assertEqual(self.execute('CAL_WRITE ' + self.id + ' P1'), 'ERR:CAL_MEASUREMENT_INVALID')
        self.assertEqual(self.execute('AD_VERIFY BATT_CHG P1'), 'ERR:AD_VERIFY_NO_WRITE')
        self.assertEqual(len(self.transactions), 1)

    def test_explicit_verify_timeout_is_recorded(self):
        self.execute('CAL_MEASUREMENT? ' + self.id)
        self.results.append(TransactionResult(True, 'AD', b'4100000144A8699A'))
        self.assertEqual(self.execute('CAL_WRITE ' + self.id + ' P1'), 'OK:CAL_WRITE')
        self.results.append(TransactionResult(False, 'AR', error='RESP_TIMEOUT', ambiguous=True))
        self.assertEqual(self.execute('AD_VERIFY BATT_CHG P1'), 'ERR:AD_VERIFY_TIMEOUT')
        self.assertEqual(self.logs[-1]['event'], 'VERIFY')

    def test_explicit_verify_returns_ok_for_exact_integer_readback(self):
        self.token = self.measured.begin('BATT_CHG', 'A')
        self.measured.complete(self.token, b'+001.0000E-03\r\n', '+001.0000E+00', 'mV')
        self.id = acquisition_id(self.token)
        self.execute('CAL_MEASUREMENT? ' + self.id)
        self.results.append(TransactionResult(True, 'AD', b'4100000144A8699A'))
        self.assertEqual(self.execute('CAL_WRITE ' + self.id + ' P1'), 'OK:CAL_WRITE')
        self.results.append(TransactionResult(True, 'AR', b'00000100000001' * 10))
        self.assertEqual(self.execute('AD_VERIFY BATT_CHG P1'), 'OK:AD_VERIFY')

    def test_malformed_ad_calculated_value_preserves_ambiguity(self):
        self.execute('CAL_MEASUREMENT? ' + self.id)
        self.results.append(TransactionResult(True, 'AD', b'410000014(*444-+'))
        self.assertEqual(self.execute('CAL_WRITE ' + self.id + ' P1'), 'ERR:CAL_WRITE_RESPONSE:AMBIGUOUS=1')
        self.assertEqual(self.execute('AD_VERIFY BATT_CHG P1'), 'ERR:AD_VERIFY_NO_WRITE')
        self.assertEqual(len(self.transactions), 1)


if __name__ == '__main__':
    unittest.main()
