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
# レビュー版のTYPE表。S1.14B実機ではBATT_CHG/P1を先行確認した。
SAMPLE_AD_TYPES = {'DISCHG_I': b'1', 'BATT_V': b'2', 'BATT_CHG': b'4'}
SAMPLE_T2_MS = 1000  # 診断期限。正式なT2は未確定。


class SampleCalibrationWrite:
    def __init__(self, measurements, protocol, cache, logger):
        self.measurements = measurements
        self.protocol = protocol
        self.cache = cache
        self.logger = logger
        self.reset()

    def reset(self):
        self.queried = {}
        self.written = {}

    def mark_queried(self, token):
        if token[2] in SAMPLE_AD_TYPES:
            self.queried[token[2:]] = token

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
            if payload[0][2:] != SAMPLE_TARGET or payload[1] != SAMPLE_POINT:
                return 'ERR:CAL_WRITE_TARGET'
            return self._write(*payload)
        if name == 'CAL_WRITE_LATEST':
            target, measurement_point, product_point = payload
            if target not in SAMPLE_AD_TYPES:
                return 'ERR:CAL_WRITE_TARGET'
            try:
                token = self.measurements.latest_token(target, measurement_point)
            except MeasurementError as exc:
                return 'ERR:CAL_' + str(exc)
            return self._write(token, product_point, report_raw=True)
        if payload[0] not in SAMPLE_AD_TYPES or (name == 'AD_VERIFY' and payload != (SAMPLE_TARGET[0], SAMPLE_POINT)):
            return 'ERR:AD_VERIFY_TARGET'
        return self._verify(*payload, report_raw=name == 'AD_VERIFY_READBACK')

    def _write(self, token, point, report_raw=False):
        target = token[2]
        try:
            value_text = self.measurements.get_calibration(token)['value_text']
        except MeasurementError as exc:
            return 'ERR:CAL_' + str(exc)
        if token != self.queried.get(token[2:]):
            return 'ERR:CAL_WRITE_NOT_QUERIED'
        # 測定の許容範囲・符号はATEが判断する。Picoには転送可能なfloat32だけを要求する。
        try:
            encoded = struct.pack('>f', float(value_text))
        except (OverflowError, ValueError):
            return 'ERR:CAL_WRITE_VALUE'
        if (encoded[0] & 0x7f) == 0x7f and (encoded[1] & 0x80):
            return 'ERR:CAL_WRITE_VALUE'
        value8 = binascii.hexlify(encoded).upper()
        type_point = SAMPLE_AD_TYPES[target] + point[1:].encode()
        result = self._transact('AD', type_point + value8, 16)
        # 応答が異常でも書込み済みの可能性があるため、対象Cacheを再利用しない。
        if result.ok or result.ambiguous:
            self.written.pop((target, point), None)
            self.measurements.discard(token)
            self.cache.invalidate_many(('DATA', 'AR'))
        data = result.response_data
        if (result.ok and len(data) == 16 and data.startswith(type_point)
                and all(c in b'0123456789ABCDEF' for c in data[2:8])
                and (report_raw or all(c in b'0123456789ABCDEF' for c in data[8:]))):
            written_adc = int(data[2:8], 16)
            self.written[(target, point)] = (value_text, value8.decode(), struct.unpack('>f', encoded)[0], written_adc)
            reply = ('OK:CAL_WRITE:{}:{}:{}'.format(value8.decode(), written_adc,
                                                     binascii.hexlify(data[8:]).decode().upper())
                     if report_raw else 'OK:CAL_WRITE')
        elif result.ok:
            reply = 'ERR:CAL_WRITE_RESPONSE:AMBIGUOUS=1'
        else:
            reply = 'ERR:CAL_WRITE_{}:AMBIGUOUS={}'.format(result.error, int(result.ambiguous))
        self._log('WRITE', reply, 'token={};point={};value={};VALUE8={}'.format(token, point, value_text, value8.decode()), result)
        return reply

    def _verify(self, target, point, report_raw=False):
        written = self.written.get((target, point))
        if written is None:
            return 'ERR:AD_VERIFY_NO_WRITE'
        value_text, value8, written_value, written_adc = written
        result = self._transact('AR', b'', 140)
        raw_ref = ''
        read_adc = None
        if result.ok:
            try:
                decoded = decode_ar(result.response_data)
                prefix = 'AR_{}_{}'.format(target, point)
                raw_ref = decoded[prefix + '_REF_RAW']
                read_adc = decoded[prefix + '_ADC']
                if any(c not in '0123456789ABCDEF' for c in raw_ref):
                    raise ValueError('Unsupported REF8 format')
                if report_raw:
                    reply = 'OK:AD_VERIFY:{}:{}:{}:{}:{}:{}'.format(target, point, value8, raw_ref,
                                                                    written_adc, read_adc)
                else:
                    if int(raw_ref, 16) > 0x7fffffff:
                        raise ValueError('Unsupported REF8 format for legacy comparison')
                    matches = written_value == int(raw_ref, 16) and written_adc == read_adc
                    reply = 'OK:AD_VERIFY' if matches else 'ERR:AD_VERIFY_MISMATCH'
            except ValueError:
                reply = 'ERR:AD_VERIFY_RESPONSE'
        elif result.error in ('ACK_TIMEOUT', 'RESP_TIMEOUT'):
            reply = 'ERR:AD_VERIFY_TIMEOUT'
        else:
            reply = 'ERR:AD_VERIFY_' + str(result.error)
        self._log('VERIFY', reply, '{};{};written={};REF8={};ADC={}/{}'.format(
            target, point, value_text, raw_ref, written_adc, read_adc), result)
        return reply

    def _log(self, event, reply, detail, result):
        self.logger.log(category='CAL', event=event, result=reply, detail=detail,
                        raw_hex=binascii.hexlify(result.raw_response).decode())
