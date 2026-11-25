# 明示ADC取得を機能確認→READの2段階で進め、完成値だけを試行別Cacheへ渡す。
# 7355固有の形式/単位検証はadapterに閉じ、NF55G書込みや製品判定を行わない。
import binascii

try:
    from .calibration_measurement import MeasurementError, CALIBRATION_TARGETS, CALIBRATION_POINTS
    from .external_instrument_contract import format_query_response
    from .external_instrument_relay import RelayError
except ImportError:  # pragma: no cover
    from calibration_measurement import MeasurementError, CALIBRATION_TARGETS, CALIBRATION_POINTS
    from external_instrument_contract import format_query_response
    from external_instrument_relay import RelayError


def acquisition_id(token):
    return '{:08X}-{:08X}-{}-{}'.format(*token)


def parse_acquisition_id(text):
    try:
        generation, sequence, target, point = text.split('-')
        if (len(generation) != 8 or len(sequence) != 8 or
                any(c not in '0123456789ABCDEF' for c in generation + sequence) or
                target not in CALIBRATION_TARGETS or point not in CALIBRATION_POINTS):
            raise ValueError('id')
        token = (int(generation, 16), int(sequence, 16), target, point)
        if not token[0] or not token[1]:
            raise ValueError('zero id')
        return token
    except (ValueError, AttributeError):
        raise MeasurementError('ACQUISITION_ID')


def measurement_reply(measurements, token):
    value = measurements.get_calibration(token)
    return 'OK:CAL_MEASUREMENT:{}:{}:{}:{}:{}:{}:{}:{}'.format(
        acquisition_id(token), value['target'], value['point'],
        value['measurement_value_text'], value['measurement_unit'],
        value['value_text'], value['unit'], binascii.hexlify(value['raw']).decode('ascii').upper())


def parse_measure_request(raw):
    try:
        fields = raw.rstrip(b'\r\n').split(b' ', 4)
        if len(fields) != 5 or fields[0] != b'CAL_MEASURE':
            raise MeasurementError('ARGUMENTS')
        target, point = fields[1].decode('ascii'), fields[2].decode('ascii')
        if target not in CALIBRATION_TARGETS or point not in CALIBRATION_POINTS:
            raise MeasurementError('MEASUREMENT_TARGET')
        timeout = fields[3]
        if not 1 <= len(timeout) <= 5 or any(c < 48 or c > 57 for c in timeout):
            raise MeasurementError('TIMEOUT')
        timeout_ms = int(timeout)
        if not 1 <= timeout_ms <= 10000:
            raise MeasurementError('TIMEOUT')
        Meter7355Voltage.validate_command(fields[4])
        return {'target': target, 'point': point, 'timeout_ms': timeout_ms, 'command': fields[4]}
    except UnicodeError:
        raise MeasurementError('ASCII')


class Meter7355Voltage:
    """7355 manual section 6.8.2, PDF p.120: DCV ASCII and error sentinels.

    The raw signed 6/7-digit mantissa and exponent are retained. Reserved
    numeric OL/scaling/dB error values cannot become calibration values.
    """
    function_command = b':SENS:FUNC?'

    @staticmethod
    def validate_command(command):
        if command not in (b':READ?', b'READ?'):
            raise MeasurementError('MEASUREMENT_COMMAND')

    @staticmethod
    def validate_function(raw):
        if raw not in (b'"VOLT:DC"\r\n', b'VOLT:DC\r\n'):
            raise MeasurementError('METER_FUNCTION')

    @staticmethod
    def decode(raw, target):
        if target not in CALIBRATION_TARGETS:
            raise MeasurementError('MEASUREMENT_TARGET')
        if not isinstance(raw, bytes) or not 2 < len(raw) <= 32 or not raw.endswith(b'\r\n'):
            raise MeasurementError('MEASUREMENT_VALUE')
        try:
            text = raw[:-2].decode('ascii')
            mantissa, exponent = text.split('E')
            if (mantissa[:1] not in ('+', '-') or mantissa.count('.') != 1 or
                    len(exponent) != 3 or exponent[0] not in ('+', '-') or
                    any(c not in '0123456789' for c in exponent[1:])):
                raise ValueError('format')
            digits = mantissa[1:].replace('.', '')
            if len(digits) not in (6, 7) or any(c not in '0123456789' for c in digits):
                raise ValueError('digits')
            whole, fraction = mantissa[1:].split('.')
            if not whole or not fraction:
                raise ValueError('mantissa')
            power = int(exponent)
            if power in (35, 36, 37) and mantissa[1:] in ('9.999999', '9.99999'):
                raise MeasurementError('MEASUREMENT_OVERRANGE')
            # 原典DCVの出力指数は200/2000mVで-03、それ以外で+00。
            if power not in (-3, 0):
                raise ValueError('DCV exponent')
        except (UnicodeError, ValueError) as exc:
            if isinstance(exc, MeasurementError):
                raise
            raise MeasurementError('MEASUREMENT_VALUE')
        if target == 'BATT_V':
            return text, 'V'
        # 浮動小数点へ変換せずV×1000。元raw・符号・仮数の全桁は変更しない。
        return mantissa + 'E{:+03d}'.format(power + 3), 'mV'


class CalibrationAcquisition:
    """One nonblocking, explicit acquisition; owns the link until completion.

    The single deadline covers function evidence, handshake and READ. Queries
    access CalibrationMeasurements only; no automatic settings, retry or AD.
    """
    def __init__(self, measurements, link, clock, adapter=None):
        self.measurements, self.link, self.clock = measurements, link, clock
        self.adapter = adapter or Meter7355Voltage()
        self._active = None
        self._result = None

    @property
    def busy(self):
        return self._active is not None or self._result is not None

    def start(self, target, point, timeout_ms, command):
        if self.link is None:
            raise MeasurementError('DISABLED')
        if self.busy or self.link.busy:
            raise MeasurementError('BUSY')
        if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or not 1 <= timeout_ms <= 10000:
            raise MeasurementError('TIMEOUT')
        self.adapter.validate_command(command)
        token = self.measurements.begin(target, point)
        self._active = {'token': token, 'command': command, 'stage': 'FUNCTION',
                        'started': self.clock.ticks_ms(), 'timeout_ms': timeout_ms, 'cancelled': None}
        try:
            self._send(self.adapter.function_command)
        except (RelayError, MeasurementError) as exc:
            self._finish('ERR:CAL_' + str(exc))
        return token

    def _send(self, command):
        active = self._active
        left = active['timeout_ms'] - (self.clock.ticks_ms() - active['started'])
        if left <= 0:
            raise MeasurementError('TIMEOUT')
        self.link.start({'command': command, 'expects_response': True,
                         'timeout_ms': left, 'response_ending': b'\r\n'})

    @staticmethod
    def _decode_reply(reply):
        try:
            prefix, kind, length, encoded = reply.split(':', 3)
            raw = binascii.unhexlify(encoded)
            if (prefix != 'OK' or kind != 'EXT_RX' or int(length) != len(raw) or
                    format_query_response(raw) != reply):
                raise ValueError('response')
            return raw
        except (ValueError, TypeError, AttributeError):
            raise MeasurementError('RESPONSE_FRAME')

    def _finish(self, reply, raw=None):
        token = self._active['token']
        if not reply.startswith('OK:'):
            self.measurements.fail(token)
        self._active = None
        self._result = {'token': token, 'reply': reply, 'raw': raw}

    def cancel(self):
        if self._active is not None and self._active['cancelled'] is None:
            self.measurements.fail(self._active['token'])
            self._active['cancelled'] = 'CANCELLED'
            self.link.cancel()

    def poll(self):
        if self._active is None:
            return
        active = self._active
        if not self.measurements.pending_matches(active['token']) and active['cancelled'] is None:
            active['cancelled'] = 'STALE'
            self.link.cancel()
        self.link.poll()
        reply = self.link.take_reply()
        if reply is None:
            return
        if active['cancelled'] is not None:
            self._finish('ERR:CAL_' + active['cancelled'])
            return
        if reply.startswith('ERR:EXT_'):
            self._finish('ERR:CAL_' + reply[len('ERR:EXT_'):])
            return
        raw = None
        try:
            raw = self._decode_reply(reply)
            if active['stage'] == 'FUNCTION':
                self.adapter.validate_function(raw)
                active['stage'] = 'READ'
                self._send(active['command'])
                return
            value_text, unit = self.adapter.decode(raw, active['token'][2])
            if not self.measurements.complete(active['token'], raw, value_text, unit):
                raise MeasurementError('STALE')
            self._finish('OK:CAL_MEASURE:' + acquisition_id(active['token']), raw)
        except (MeasurementError, RelayError) as exc:
            self._finish('ERR:CAL_' + str(exc), raw)

    def take_result(self):
        result, self._result = self._result, None
        if result is not None and result['reply'].startswith('OK:'):
            try:
                self.measurements.get(result['token'])
            except MeasurementError:
                result['reply'] = 'ERR:CAL_STALE'
        return result
