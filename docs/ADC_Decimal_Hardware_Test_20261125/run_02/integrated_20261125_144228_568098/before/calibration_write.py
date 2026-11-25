# 確認済みサンプルのAD書込みと、別の明示AR要求による照合を担当する。
import binascii
import struct

try:
    from .calibration_measurement import MeasurementError
    from .nf55_decode import decode_ar
except ImportError:  # pragma: no cover
    from calibration_measurement import MeasurementError
    from nf55_decode import decode_ar


SAMPLE_TARGET = ('BATT_CHG', 'A')
SAMPLE_POINT = 'P1'
SAMPLE_TYPE_POINT = b'41'
SAMPLE_T2_MS = 1000  # 診断期限。正式なT2は未確定。


class SampleCalibrationWrite:
    def __init__(self, measurements, protocol, cache, logger):
        self.measurements = measurements
        self.protocol = protocol
        self.cache = cache
        self.logger = logger
        self.reset()

    def reset(self):
        self.queried = None
        self.written = None

    def mark_queried(self, token):
        if token[2:] == SAMPLE_TARGET:
            self.queried = token

    def _transact(self, command, data, length):
        return self.protocol.transact(command, data, t2_ms=SAMPLE_T2_MS, expected_length=length,
                                      allow_command_retry=False)

    def execute(self, name, payload):
        if not self.logger.test_running or not self.logger.active:
            return 'ERR:CAL_NO_ACTIVE_TRIAL'
        info = self.cache.get('INFO') or {}
        if (info.get('FW_REV'), info.get('UNIT_SERIAL')) != ('S1.14B', '000001'):
            return 'ERR:CAL_SAMPLE_IDENTITY'
        if name == 'CAL_WRITE':
            return self._write(*payload)
        if payload != (SAMPLE_TARGET[0], SAMPLE_POINT):
            return 'ERR:AD_VERIFY_TARGET'
        return self._verify()

    def _write(self, token, point):
        if token[2:] != SAMPLE_TARGET or point != SAMPLE_POINT:
            return 'ERR:CAL_WRITE_TARGET'
        try:
            value_text = self.measurements.get_calibration(token)['value_text']
        except MeasurementError as exc:
            return 'ERR:CAL_' + str(exc)
        if token != self.queried:
            return 'ERR:CAL_WRITE_NOT_QUERIED'
        value = float(value_text)
        if not 0 <= value <= 3.3:
            return 'ERR:CAL_WRITE_VALUE'
        encoded = struct.pack('>f', value)
        value8 = binascii.hexlify(encoded).upper()
        result = self._transact('AD', SAMPLE_TYPE_POINT + value8, 16)
        # 応答が異常でも書込み済みの可能性があるため、対象Cacheを再利用しない。
        if result.ok or result.ambiguous:
            self.written = None
            self.measurements.discard(token)
            self.cache.invalidate_many(('DATA', 'AR'))
        data = result.response_data
        if (result.ok and len(data) == 16 and data.startswith(SAMPLE_TYPE_POINT)
                and all(c in b'0123456789ABCDEF' for c in data[2:])):
            self.written = (value_text, struct.unpack('>f', encoded)[0], int(data[2:8], 16))
            reply = 'OK:CAL_WRITE'
        elif result.ok:
            reply = 'ERR:CAL_WRITE_RESPONSE:AMBIGUOUS=1'
        else:
            reply = 'ERR:CAL_WRITE_{}:AMBIGUOUS={}'.format(result.error, int(result.ambiguous))
        self._log('WRITE', reply, 'token={};value={};VALUE8={}'.format(token, value_text, value8.decode()), result)
        return reply

    def _verify(self):
        if self.written is None:
            return 'ERR:AD_VERIFY_NO_WRITE'
        value_text, written_value, written_adc = self.written
        result = self._transact('AR', b'', 140)
        raw_ref = ''
        read_adc = None
        if result.ok:
            try:
                decoded = decode_ar(result.response_data)
                raw_ref = decoded['AR_BATT_CHG_P1_REF_RAW']
                read_adc = decoded['AR_BATT_CHG_P1_ADC']
                if any(c not in '0123456789ABCDEF' for c in raw_ref) or int(raw_ref, 16) > 0x7fffffff:
                    raise ValueError('Unsupported REF8 format')
                matches = written_value == int(raw_ref, 16) and written_adc == read_adc
                reply = 'OK:AD_VERIFY' if matches else 'ERR:AD_VERIFY_MISMATCH'
            except ValueError:
                reply = 'ERR:AD_VERIFY_RESPONSE'
        elif result.error in ('ACK_TIMEOUT', 'RESP_TIMEOUT'):
            reply = 'ERR:AD_VERIFY_TIMEOUT'
        else:
            reply = 'ERR:AD_VERIFY_' + str(result.error)
        self._log('VERIFY', reply, 'BATT_CHG;P1;written={};REF8={};ADC={}/{}'.format(
            value_text, raw_ref, written_adc, read_adc), result)
        return reply

    def _log(self, event, reply, detail, result):
        self.logger.log(category='CAL', event=event, result=reply, detail=detail,
                        raw_hex=binascii.hexlify(result.raw_response).decode())
