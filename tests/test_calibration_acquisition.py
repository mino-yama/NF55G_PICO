"""完成値・実単位・期限・試行相関を確認し、任意の数値応答をCacheへ採用しない。"""
from decimal import Decimal
import unittest

from src.calibration_acquisition import (CalibrationAcquisition, Meter7355Voltage,
    acquisition_id, parse_acquisition_id, measurement_reply)
from src.calibration_measurement import CalibrationMeasurements, MeasurementError
from src.command_parser import parse_ate_command, ParseError
from src.external_instrument_contract import format_query_response
from src.mock_nf55g import FakeClock


class ScriptedLink:
    def __init__(self, clock, responses):
        self.clock, self.responses = clock, list(responses)
        self.requests = []
        self.request_times = []
        self.pending = None
        self.reply = None
        self.cancel_count = 0

    @property
    def busy(self):
        return self.pending is not None or self.reply is not None

    def start(self, request):
        assert not self.busy
        self.requests.append(dict(request))
        self.request_times.append(self.clock.ticks_ms())
        self.pending = (dict(request), self.clock.ticks_ms())

    def poll(self):
        if self.pending is None:
            return
        request, started = self.pending
        if self.clock.ticks_ms() - started >= request['timeout_ms']:
            self.reply = 'ERR:EXT_TIMEOUT:AMBIGUOUS=1'
        elif self.responses and self.clock.ticks_ms() - started >= self.responses[0][0]:
            _, response = self.responses.pop(0)
            self.reply = format_query_response(response) if isinstance(response, bytes) else response
        else:
            return
        self.pending = None

    def take_reply(self):
        reply, self.reply = self.reply, None
        return reply

    def cancel(self):
        self.cancel_count += 1
        self.pending = None
        self.reply = 'ERR:EXT_CANCELLED:AMBIGUOUS=1'


class VoltageAdapterTests(unittest.TestCase):
    def test_actual_voltage_mantissa_sign_precision_and_source_are_preserved(self):
        for raw in (b'+09.62123E+00\r\n', b'-000.0000E-03\r\n', b'+5.00000E+00\r\n'):
            text, unit = Meter7355Voltage.decode(raw, 'BATT_V')
            self.assertEqual((text, unit), (raw[:-2].decode(), 'V'))

    def test_shunt_conversion_scales_exponent_exactly_without_float_or_abs(self):
        for raw, expected in ((b'+044.0123E-03\r\n', '+044.0123E+00'),
                              (b'-0.300120E-03\r\n', '-0.300120E+00'),
                              (b'+001.8500E-03\r\n', '+001.8500E+00'),
                              (b'+0.500020E-03\r\n', '+0.500020E+00'),
                              (b'-000.0000E-03\r\n', '-000.0000E+00'),
                              (b'+09.62123E+00\r\n', '+09.62123E+03')):
            for target in ('DISCHG_I', 'BATT_CHG'):
                with self.subTest(raw=raw, target=target):
                    text, unit = Meter7355Voltage.decode(raw, target)
                    self.assertEqual((text, unit), (expected, 'mV'))
                    self.assertEqual(Decimal(text), Decimal(raw[:-2].decode()) * 1000)

    def test_numeric_ol_scaling_and_db_error_sentinels_are_rejected(self):
        for power in (35, 36, 37):
            for sign in ('+', '-'):
                for mantissa in ('9.999999', '9.99999'):
                    raw = (sign + mantissa + 'E+' + str(power) + '\r\n').encode()
                    with self.subTest(raw=raw), self.assertRaisesRegex(MeasurementError, 'OVERRANGE'):
                        Meter7355Voltage.decode(raw, 'BATT_V')

    def test_partial_multiple_nonmeasurement_and_malformed_data_never_decode(self):
        for raw in (b'1\r\n', b'OL\r\n', b'NaN\r\n', b'+09.62123E+00', b'+09.62123E+00\r\n1\r\n',
                    b'+09.62123E+00,1\r\n', b' +09.62123E+00\r\n', b'+09.62123E+00\x00\r\n',
                    b'+09.62123e+00\r\n', b'+09.62123E+01\r\n', b'+09.62123E+000\r\n',
                    b'+0962123.E+00\r\n', b'+.0962123E+00\r\n', b'\xff\r\n', None):
            with self.subTest(raw=raw), self.assertRaises(MeasurementError):
                Meter7355Voltage.decode(raw, 'BATT_V')

    def test_dc_voltage_function_evidence_is_required(self):
        for raw in (b'"VOLT:DC"\r\n', b'VOLT:DC\r\n'):
            Meter7355Voltage.validate_function(raw)
        for raw in (b'"VOLT:AC"\r\n', b'"CURR:DC"\r\n', b'1\r\n', b'VOLT:DC', b'VOLT:DC\r\nextra'):
            with self.assertRaises(MeasurementError):
                Meter7355Voltage.validate_function(raw)


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.cache = CalibrationMeasurements()
        self.cache.start_trial()

    def create(self, responses):
        link = ScriptedLink(self.clock, responses)
        acquisition = CalibrationAcquisition(self.cache, link, self.clock)
        return acquisition, link

    def finish(self, acquisition):
        for _ in range(300):
            acquisition.poll()
            result = acquisition.take_result()
            if result is not None:
                return result
            self.clock.sleep_ms(1)
        self.fail('no bounded result')

    def test_function_then_read_completes_cache_and_query_does_not_send(self):
        acquisition, link = self.create([(0, b'"VOLT:DC"\r\n'), (0, b'-001.8500E-03\r\n')])
        token = acquisition.start('BATT_CHG', 'A', 100, b':READ?')
        self.assertEqual(self.finish(acquisition)['reply'], 'OK:CAL_MEASURE:' + acquisition_id(token))
        self.assertEqual([r['command'] for r in link.requests], [b':SENS:FUNC?', b':READ?'])
        for _ in range(5):
            reply = measurement_reply(self.cache, token)
            self.assertIn(':-001.8500E+00:mV:-001.8500E+00:A:', reply)
        self.assertEqual(len(link.requests), 2)
        self.assertEqual(self.cache.get(token)['raw'], b'-001.8500E-03\r\n')

    def test_adc_read_requires_new_eom_and_keeps_unmodified_meter_response(self):
        raw = b'+08.1268E+00\r\n'
        answers = (b'F01\r\n', b'INIC1\r\n', b'TRS0\r\n', b'RN0,00000\r\n',
                   b'00256\r\n', b'00000\r\n', b'00257\r\n', raw)
        acquisition, link = self.create([(0, item) for item in answers])
        token = acquisition.start('BATT_V', 'A', 250, b'MD?')
        self.assertEqual(self.finish(acquisition)['reply'], 'OK:CAL_MEASURE:' + acquisition_id(token))
        self.assertEqual([item['command'] for item in link.requests],
                         [b'F?', b'INIC?', b'TRS?', b'RN?', b'MSR?', b'MSR?', b'MSR?', b'MD?'])
        self.assertTrue(all(after - before >= 20 for before, after in
                            zip(link.request_times, link.request_times[1:])))
        self.assertEqual(self.cache.get(token)['raw'], raw)

    def test_adc_rejects_wrong_trigger_and_recall_without_reading(self):
        for answers, expected in (
            ((b'F1\r\n', b'INIC0\r\n'), 'ERR:CAL_METER_TRIGGER'),
            ((b'F01\r\n', b'INIC1\r\n', b'TRS3\r\n'), 'ERR:CAL_METER_TRIGGER'),
            ((b'F01\r\n', b'INIC1\r\n', b'TRS0\r\n', b'RN1,00000\r\n'), 'ERR:CAL_METER_RECALL'),
        ):
            with self.subTest(answers=answers):
                acquisition, link = self.create([(0, item) for item in answers])
                token = acquisition.start('BATT_V', 'A', 200, b'MD?')
                self.assertEqual(self.finish(acquisition)['reply'], expected)
                self.assertNotIn(b'MD?', [item['command'] for item in link.requests])
                with self.assertRaises(MeasurementError):
                    self.cache.get(token)

    def test_adc_eom_wait_honors_deadline_and_cancel_before_send(self):
        answers = (b'F01\r\n', b'INIC1\r\n', b'TRS0\r\n', b'RN0,00000\r\n',
                   b'00256\r\n', b'00000\r\n')
        acquisition, link = self.create([(0, item) for item in answers])
        token = acquisition.start('BATT_V', 'A', 130, b'MD?')
        self.assertEqual(self.finish(acquisition)['reply'], 'ERR:CAL_TIMEOUT')
        self.assertEqual(len(link.requests), 6)
        with self.assertRaises(MeasurementError):
            self.cache.get(token)
        acquisition, link = self.create([])
        acquisition.start('BATT_V', 'A', 200, b'MD?')
        acquisition.cancel()
        self.assertEqual(self.finish(acquisition)['reply'], 'ERR:CAL_CANCELLED')
        self.assertFalse(link.requests)

    def test_wrong_function_never_sends_read_or_caches_numeric_data(self):
        acquisition, link = self.create([(0, b'"CURR:DC"\r\n')])
        token = acquisition.start('BATT_V', 'A', 100, b':READ?')
        self.assertEqual(self.finish(acquisition)['reply'], 'ERR:CAL_METER_FUNCTION')
        self.assertEqual(len(link.requests), 1)
        with self.assertRaises(MeasurementError):
            self.cache.get(token)

    def test_one_deadline_covers_both_steps_and_preserves_ambiguous_flag(self):
        acquisition, link = self.create([(7, b'"VOLT:DC"\r\n'), (4, b'+09.62123E+00\r\n')])
        token = acquisition.start('BATT_V', 'A', 10, b':READ?')
        result = self.finish(acquisition)
        self.assertEqual(result['reply'], 'ERR:CAL_TIMEOUT:AMBIGUOUS=1')
        self.assertEqual([r['timeout_ms'] for r in link.requests], [10, 3])
        self.assertEqual(self.clock.ticks_ms(), 10)
        with self.assertRaises(MeasurementError):
            self.cache.get(token)

    def test_reacquisition_overrange_invalidates_old_value_without_retry(self):
        old = self.cache.begin('BATT_V', 'A')
        self.cache.complete(old, b'+08.00123E+00\r\n', '+08.00123E+00', 'V')
        acquisition, link = self.create([(0, b'"VOLT:DC"\r\n'), (0, b'+9.999999E+37\r\n')])
        token = acquisition.start('BATT_V', 'A', 100, b':READ?')
        self.assertEqual(self.finish(acquisition)['reply'], 'ERR:CAL_MEASUREMENT_OVERRANGE')
        for item in (old, token):
            with self.assertRaises(MeasurementError):
                self.cache.get(item)
        self.assertEqual(len(link.requests), 2)

    def test_end_trial_during_function_cancels_without_read_or_resurrection(self):
        acquisition, link = self.create([(5, b'"VOLT:DC"\r\n')])
        token = acquisition.start('BATT_V', 'A', 100, b':READ?')
        self.cache.end_trial()
        self.cache.start_trial()
        self.assertEqual(self.finish(acquisition)['reply'], 'ERR:CAL_STALE')
        self.assertEqual(link.cancel_count, 1)
        self.assertEqual(len(link.requests), 1)
        self.assertFalse(self.cache.complete(token, b'8', '8', 'V'))

    def test_end_trial_after_completion_before_delivery_cannot_report_success(self):
        acquisition, _ = self.create([(0, b'"VOLT:DC"\r\n'), (0, b'+09.62123E+00\r\n')])
        acquisition.start('BATT_V', 'A', 100, b':READ?')
        acquisition.poll()
        acquisition.poll()
        self.cache.end_trial()
        self.assertEqual(acquisition.take_result()['reply'], 'ERR:CAL_STALE')

    def test_cancelled_request_is_drained_and_never_retried(self):
        acquisition, link = self.create([])
        token = acquisition.start('BATT_V', 'A', 100, b':READ?')
        acquisition.cancel()
        acquisition.cancel()
        self.assertEqual(self.finish(acquisition)['reply'], 'ERR:CAL_CANCELLED')
        self.assertEqual(link.cancel_count, 1)
        self.assertFalse(acquisition.busy)
        self.assertFalse(self.cache.complete(token, b'8', '8', 'V'))

    def test_bad_reply_or_remote_failure_does_not_become_measurement(self):
        for reply, expected in (('OK:EXT_TX', 'ERR:CAL_RESPONSE_FRAME'),
                                ('OK:EXT_RX:5:31', 'ERR:CAL_RESPONSE_FRAME'),
                                ('ERR:EXT_DISCONNECTED:AMBIGUOUS=1', 'ERR:CAL_DISCONNECTED:AMBIGUOUS=1')):
            acquisition, _ = self.create([(0, reply)])
            acquisition.start('BATT_V', 'A', 100, b':READ?')
            self.assertEqual(self.finish(acquisition)['reply'], expected)


class CalibrationParserTests(unittest.TestCase):
    def test_adc_read_is_explicit(self):
        self.assertEqual(parse_ate_command('CAL_MEASURE_BATT_V A 4000 MD?').payload['command'], b'MD?')
        with self.assertRaises(ParseError):
            parse_ate_command('CAL_MEASURE_BATT_V A 4000 MD?;*RST')

    def test_circuit_named_measure_command_uses_existing_request_validation(self):
        named = parse_ate_command('CAL_MEASURE_BATT_CHG A 4000 :READ?')
        legacy = parse_ate_command('CAL_MEASURE BATT_CHG A 4000 :READ?')
        self.assertEqual(named.category, 'CALIBRATION_ACQUIRE')
        self.assertEqual(named.payload, legacy.payload)

    def test_new_commands_and_opaque_id_roundtrip(self):
        parsed = parse_ate_command('CAL_MEASURE BATT_V A 2000 :READ?')
        self.assertEqual(parsed.category, 'CALIBRATION_ACQUIRE')
        self.assertEqual(parsed.payload['command'], b':READ?')
        token = (1, 13, 'BATT_CHG', 'B')
        text = acquisition_id(token)
        self.assertEqual(parse_acquisition_id(text), token)
        self.assertEqual(parse_ate_command('CAL_MEASUREMENT? ' + text).payload, token)

    def test_invalid_commands_are_rejected_without_aliasing_scpi(self):
        for text in ('CAL_MEASURE', 'CAL_MEASURE BATT_V A 0 :READ?',
                     'CAL_MEASURE BATT_V A 10001 :READ?', 'CAL_MEASURE BATT_V A +1 :READ?',
                     'CAL_MEASURE BATT_V P1 20 :READ?', 'CAL_MEASURE 12VOUT_I A 20 :READ?',
                     'CAL_MEASURE BATT_V A 20 :CONF?', 'CAL_MEASURE BATT_V A 20 :READ?;*RST',
                     'CAL_MEASUREMENT?', 'CAL_MEASUREMENT? 00000000-00000001-BATT_V-A',
                     'CAL_MEASUREMENT? 00000001-00000001-BATT_V-A EXTRA'):
            with self.subTest(text=text), self.assertRaises(ParseError):
                parse_ate_command(text)
