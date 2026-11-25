"""ATE integration candidate for the observed S1.14B BATT_CHG Point 1 profile."""

import binascii
import struct

from src import config
from src.calibration_acquisition import parse_acquisition_id
from src.calibration_measurement import MeasurementError
from src.nf55_decode import decode_ar


class SampleCalibrationCommands:
    def __init__(self, app):
        self.app = app
        self.previous = app._execute_ate_line
        self.trial = None
        self.approved = None
        self.written = None

    def __call__(self, line):
        try:
            text = line.decode('ascii') if isinstance(line, bytes) else line
        except UnicodeError:
            return self.previous(line)
        parts = text.split()
        trial = self.app.logger.trial_id if self.app.logger.test_running else None
        if trial != self.trial:
            self.trial, self.approved, self.written = trial, None, None
        name = parts[0] if parts else ''
        if name not in ('CAL_WRITE', 'AD_VERIFY'):
            reply = self.previous(line)
            if trial and name == 'CAL_MEASUREMENT?' and isinstance(reply, str) and reply.startswith('OK:CAL_MEASUREMENT:'):
                self.approved = parse_acquisition_id(reply.split(':')[2])
            return reply
        if not trial:
            return 'ERR:CAL_NO_ACTIVE_TRIAL'
        if self.app._comm_busy():
            return 'ERR:BUSY'
        if name == 'CAL_WRITE':
            if len(parts) != 3 or parts[2] != 'P1':
                return 'ERR:CAL_WRITE_ARGUMENTS'
            return self.write(parts[1])
        if parts[1:] != ['BATT_CHG', 'P1']:
            return 'ERR:AD_VERIFY_ARGUMENTS'
        return self.verify()

    def _transact(self, name, payload, length):
        original_retry = config.MAX_COMMAND_RETRY
        config.MAX_COMMAND_RETRY = 0
        try:
            return self.app.protocol.transact(name, payload, t2_ms=1000, expected_length=length)
        finally:
            config.MAX_COMMAND_RETRY = original_retry

    def write(self, acquisition):
        try:
            token = parse_acquisition_id(acquisition)
            if token[2:] != ('BATT_CHG', 'A'):
                return 'ERR:CAL_WRITE_TARGET'
            obtained = self.app.measurements.get_calibration(token)
            if token != self.approved:
                return 'ERR:CAL_WRITE_NOT_QUERIED'
            value_text = obtained['value_text']
            value = float(value_text)
            if not 0 <= value <= 3.3:
                return 'ERR:CAL_WRITE_VALUE'
            encoded = struct.pack('>f', value)
        except MeasurementError as exc:
            return 'ERR:CAL_' + str(exc)
        value8 = binascii.hexlify(encoded).upper()
        payload = b'41' + value8
        result = self._transact('AD', payload, 16)
        if result.ok or result.ambiguous:
            self.written = None
            self.app.measurements.discard(token)
            self.app.cache.invalidate_many(('DATA', 'AR'))
        data = result.response_data
        complete = (result.ok and len(data) == 16 and data.startswith(b'41')
                    and all(byte in b'0123456789ABCDEF' for byte in data[2:]))
        if complete:
            self.written = (value_text, encoded)
            reply = 'OK:CAL_WRITE'
        elif result.ok:
            reply = 'ERR:CAL_WRITE_RESPONSE:AMBIGUOUS=1'
        else:
            reply = 'ERR:CAL_WRITE_{}:AMBIGUOUS={}'.format(result.error, int(result.ambiguous))
        self.app.logger.log(category='CAL', event='WRITE', result=reply,
                            detail='id={};value={};VALUE8={}'.format(acquisition, value_text, value8.decode()),
                            raw_hex=binascii.hexlify(result.raw_response).decode())
        return reply

    def verify(self):
        if self.written is None:
            return 'ERR:AD_VERIFY_NO_WRITE'
        value_text, encoded = self.written
        readback = self._transact('AR', b'', 140)
        raw_ref = ''
        if readback.ok:
            try:
                raw_ref = decode_ar(readback.response_data)['AR_BATT_CHG_P1_REF_RAW']
                if any(c not in '0123456789ABCDEF' for c in raw_ref) or int(raw_ref, 16) > 0x7fffffff:
                    raise ValueError('Unverified REF8 format')
                expected = struct.unpack('>f', encoded)[0]
                reply = 'OK:AD_VERIFY' if expected == int(raw_ref, 16) else 'ERR:AD_VERIFY_MISMATCH'
            except ValueError:
                reply = 'ERR:AD_VERIFY_RESPONSE'
        else:
            if readback.error in ('ACK_TIMEOUT', 'RESP_TIMEOUT'):
                reply = 'ERR:AD_VERIFY_TIMEOUT'
            else:
                reply = 'ERR:AD_VERIFY_' + str(readback.error)
        self.app.logger.log(category='CAL', event='VERIFY', result=reply,
                            detail='BATT_CHG;P1;written={};REF8={}'.format(value_text, raw_ref),
                            raw_hex=binascii.hexlify(readback.raw_response).decode())
        return reply
