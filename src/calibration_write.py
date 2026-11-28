# 確認済みサンプルで、Cache採用またはATE直接指定のADを書込み、別指令ARで読戻す。
import binascii
import struct

try:
    from . import config
    from .calibration_guard import check_value
    from .calibration_measurement import MeasurementError, _decimal_text
    from .nf55_decode import decode_ar
    from .models import TransactionResult
except ImportError:  # pragma: no cover
    import config
    from calibration_guard import check_value
    from calibration_measurement import MeasurementError, _decimal_text
    from nf55_decode import decode_ar
    from models import TransactionResult


SAMPLE_TARGET = ('BATT_CHG', 'A')
SAMPLE_POINT = 'A'
# レビュー版のTYPE表。S1.14B実機ではBATT_CHG/Aを先行確認した。
SAMPLE_AD_TYPES = {'DISCHG_I': b'1', 'BATT_V': b'2', 'BATT_CHG': b'4'}
DIRECT_AD_TYPES = {'DISCHG_I': b'1', 'BATT_V': b'2', 'ACDC12V_V': b'3',
                   'BATT_CHG': b'4', '12VOUT_V': b'5'}
SAMPLE_T2_MS = 1000  # AD書込みの診断期限。ARは承認済みのconfig.T2_AR_MSを使用。


def encode_ad_value(value_text):
    # ATEのA/V値をfloat32へ変換する。書込み範囲は送信直前に共通検証する。
    if not _decimal_text(value_text):
        raise MeasurementError('AD_VALUE')
    try:
        encoded = struct.pack('>f', float(value_text))
    except (OverflowError, ValueError):
        raise MeasurementError('AD_VALUE')
    if (encoded[0] & 0x7f) == 0x7f and (encoded[1] & 0x80):
        raise MeasurementError('AD_VALUE')
    # 非ゼロ入力をfloat32のゼロとして送らない。通常のfloat32丸めは許容する。
    if encoded in (b'\x00\x00\x00\x00', b'\x80\x00\x00\x00'):
        mantissa = value_text.lower().split('e')[0]
        if any(c in '123456789' for c in mantissa):
            raise MeasurementError('AD_VALUE')
    return encoded


def parse_direct_ad(name, payload=None):
    if payload is not None:
        raise MeasurementError('AD_ARGUMENTS')
    try:
        target, point, value_text = name[3:].rsplit('_', 2)
    except ValueError:
        raise MeasurementError('AD_ARGUMENTS')
    if target not in DIRECT_AD_TYPES:
        target = next((key for key, value in DIRECT_AD_TYPES.items()
                       if value.decode() == target), None)
    if target is None:
        raise MeasurementError('AD_TYPE')
    if point not in ('A', 'B'):
        raise MeasurementError('AD_POINT')
    encode_ad_value(value_text)
    return target, point, value_text


class SampleCalibrationWrite:
    def __init__(self, measurements, protocol, cache, logger):
        self.measurements = measurements
        self.protocol = protocol
        self.cache = cache
        self.logger = logger
        self.reset()

    def reset(self):
        self.queried = {}

    def mark_queried(self, token):
        if token[2] in SAMPLE_AD_TYPES:
            self.queried[token[2:]] = token

    def _transact(self, command, data, length):
        # 読出しARと書込みADの待ち時間を分離する。再送方針はどちらも変更しない。
        t2_ms = config.T2_AR_MS if command == 'AR' else SAMPLE_T2_MS
        return self.protocol.transact(command, data, t2_ms=t2_ms, expected_length=length,
                                      allow_command_retry=False)

    def execute(self, name, payload):
        if not self.logger.test_running or not self.logger.active:
            return 'ERR:CAL_NO_ACTIVE_TRIAL'
        info = self.cache.get('INFO') or {}
        if (info.get('FW_REV'), info.get('UNIT_SERIAL')) != ('S1.14B', '000001'):
            return 'ERR:CAL_SAMPLE_IDENTITY'
        if name == 'AD_DIRECT':
            target, point, value_text = payload
            return self._write_value(target, point, value_text, direct=True)
        if name == 'CAL_WRITE':
            if payload[0][2:] != SAMPLE_TARGET or payload[1] != SAMPLE_POINT:
                return 'ERR:CAL_WRITE_TARGET'
            return self._write(*payload)
        if name == 'CAL_WRITE_LATEST':
            target, point = payload
            if target not in SAMPLE_AD_TYPES:
                return 'ERR:CAL_WRITE_TARGET'
            try:
                token = self.measurements.latest_token(target, point)
            except MeasurementError as exc:
                return 'ERR:CAL_' + str(exc)
            return self._write(token, point, report_raw=True)
        return 'ERR:CAL_WRITE_COMMAND'

    def _write(self, token, point, report_raw=False):
        target = token[2]
        if point != token[3]:
            return 'ERR:CAL_WRITE_TARGET'
        try:
            value_text = self.measurements.get_calibration(token)['value_text']
        except MeasurementError as exc:
            return 'ERR:CAL_' + str(exc)
        if token != self.queried.get(token[2:]):
            return 'ERR:CAL_WRITE_NOT_QUERIED'
        return self._write_value(target, point, value_text, token, report_raw)

    def _write_value(self, target, point, value_text, token=None, report_raw=False, direct=False):
        prefix = 'AD_WRITE' if direct else 'CAL_WRITE'
        try:
            encoded = encode_ad_value(value_text)
        except MeasurementError:
            return 'ERR:' + prefix + '_VALUE'
        if target not in DIRECT_AD_TYPES or point not in ('A', 'B'):
            return 'ERR:' + prefix + '_TARGET'
        guard_error = check_value(target, point, value_text, encoded)
        if guard_error:
            reply = 'ERR:' + prefix + '_' + guard_error
            # 拒否は未送信。Cache・照会済み記録・直前の正常書込み記録を消費しない。
            self.logger.log(category='CAL', event='REJECT', result=reply,
                            detail='target={};point={};value={};settings={}'.format(
                                target, point, value_text, self._settings_revision()))
            return reply
        value8 = binascii.hexlify(encoded).upper()
        # 製品通信の点番号への変換はここに集約する。
        type_point = DIRECT_AD_TYPES[target] + (b'1' if point == 'A' else b'2')
        try:
            result = self._transact('AD', type_point + value8, 16)
        except OSError:
            result = TransactionResult(False, 'AD', error='UART', ambiguous=True,
                                       elapsed_ms=None, response_retry_count=None)
        # 応答が異常でも書込み済みの可能性があるため、対象Cacheを再利用しない。
        if result.ok or result.ambiguous:
            if direct:
                # 直接指定値と古いDMM Cacheを混同させない。同回路のA/B取得値は失効する。
                for measurement_point in ('A', 'B'):
                    self.queried.pop((target, measurement_point), None)
                    try:
                        self.measurements.discard(self.measurements.latest_token(target, measurement_point))
                    except MeasurementError:
                        pass
            else:
                self.measurements.discard(token)
            self.cache.invalidate_many(('DATA', 'AR'))
        data = result.response_data
        if (result.ok and len(data) == 16 and data.startswith(type_point)
                and all(c in b'0123456789ABCDEF' for c in data[2:8])
                and (direct or report_raw or all(c in b'0123456789ABCDEF' for c in data[8:]))):
            written_adc = int(data[2:8], 16)
            raw_calc = binascii.hexlify(data[8:]).decode().upper()
            if direct:
                reply = 'OK:AD_WRITE:{}:{}:{}:{}:{}'.format(
                    DIRECT_AD_TYPES[target].decode(), point, value8.decode(), written_adc, raw_calc)
            elif report_raw:
                reply = 'OK:CAL_WRITE:{}:{}:{}'.format(value8.decode(), written_adc, raw_calc)
            else:
                reply = 'OK:CAL_WRITE'
        elif result.ok:
            reply = 'ERR:' + prefix + '_RESPONSE:AMBIGUOUS=1'
        else:
            reply = 'ERR:{}_{}:AMBIGUOUS={}'.format(prefix, result.error, int(result.ambiguous))
        self._log('WRITE', reply, 'source={};target={};token={};point={};value={};VALUE8={};AD_DATA={};settings={}'.format(
            'ATE_DIRECT' if direct else 'MEASUREMENT_CACHE', target, token, point, value_text,
            value8.decode(), (type_point + value8).decode(), self._settings_revision()), result)
        return reply

    @staticmethod
    def _settings_revision():
        try:
            from .calibration_guard import settings
        except ImportError:  # pragma: no cover
            from calibration_guard import settings
        return getattr(settings, 'SETTINGS_REV', 'INVALID')

    def readback(self, target, point):
        if not self.logger.test_running or not self.logger.active:
            return 'ERR:CAL_NO_ACTIVE_TRIAL'
        info = self.cache.get('INFO') or {}
        if (info.get('FW_REV'), info.get('UNIT_SERIAL')) != ('S1.14B', '000001'):
            return 'ERR:CAL_SAMPLE_IDENTITY'
        if target not in DIRECT_AD_TYPES or point not in ('A', 'B'):
            return 'ERR:AR_READ_TARGET'
        if self.protocol is None:
            return 'ERR:NF55G_NOT_CONNECTED'
        try:
            result = self._transact('AR', b'', 140)
        except OSError:
            result = TransactionResult(False, 'AR', error='UART', ambiguous=True,
                                       elapsed_ms=None, response_retry_count=None)
        if result.ok:
            try:
                decoded = decode_ar(result.response_data)
                prefix = 'AR_{}_{}'.format(target, point)
                raw_ref = decoded[prefix + '_REF_RAW']
                read_adc = decoded[prefix + '_ADC']
                reply = 'OK:AR_READ:{}:{}:{}:{}'.format(target, point, read_adc, raw_ref)
            except (KeyError, ValueError):
                reply = 'ERR:AR_READ_RESPONSE'
        elif result.error in ('ACK_TIMEOUT', 'RESP_TIMEOUT'):
            reply = 'ERR:AR_READ_TIMEOUT'
        else:
            reply = 'ERR:AR_READ_{}:AMBIGUOUS={}'.format(result.error, int(result.ambiguous))
        self._log('AR_READ', reply, '{};{};result={}'.format(target, point, reply), result)
        return reply

    def _log(self, event, reply, detail, result):
        self.logger.log(category='CAL', event=event, result=reply,
                        detail=detail + ';elapsed_ms={};ambiguous={}'.format(result.elapsed_ms, int(result.ambiguous)),
                        cmd=result.cmd, cmd_retry=result.command_retry_count, rsp_retry=result.response_retry_count,
                        raw_hex=binascii.hexlify(result.raw_response).decode())
