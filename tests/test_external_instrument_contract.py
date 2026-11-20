"""ユーザー承認の中継書式を原文・CRC破損・上限・入力境界で検証する。"""
import unittest
import zlib

from src.external_instrument_contract import (
    ContractError, parse_monitor_request, encode_frame, decode_frame,
    format_query_response, format_error,
)


def signed(fields):
    prefix = (','.join(fields) + ',').encode('ascii')
    return prefix + ('%08X\r\n' % (zlib.crc32(prefix) & 0xffffffff)).encode('ascii')


class ExternalInstrumentContractTests(unittest.TestCase):
    def setUp(self):
        self.session = bytes.fromhex('00112233445566778899AABBCCDDEEFF')
        self.fields = ['@X1', self.session.hex().upper(), '00000001', 'Q', '1',
                       '000007D0', '0005', '2A49444E3F']

    def test_monitor_query_matches_approved_example(self):
        request = parse_monitor_request(b'EXT_QUERY 2000 *IDN?\r\n')
        self.assertEqual(request, {'command': b'*IDN?', 'expects_response': True,
                                  'timeout_ms': 2000, 'response_ending': b'\r\n'})

    def test_monitor_preserves_body_and_explicit_mode(self):
        body = b' :sens:func "VOLT:DC" , 1 '
        request = parse_monitor_request(b'EXT_SEND 1 ' + body)
        self.assertEqual(request['command'], body)
        self.assertFalse(request['expects_response'])
        self.assertIsNone(request['response_ending'])
        self.assertFalse(parse_monitor_request(b'EXT_SEND 1 *IDN?')['expects_response'])

    def test_monitor_endings_and_command_limits(self):
        for ending in (b'', b'\r', b'\n', b'\r\n'):
            request = parse_monitor_request(b'EXT_QUERY 10000 ' + b'X' * 192 + ending)
            self.assertEqual(request['command'], b'X' * 192)
        for body in (b'', b'X' * 193, b'a\rb', b'a\nb', b'\x00', b'\xff', b'x\r\n\r\n'):
            with self.subTest(body=body):
                with self.assertRaises(ContractError):
                    parse_monitor_request(b'EXT_QUERY 1 ' + body)

    def test_monitor_rejects_bad_envelope_and_timeout(self):
        for line in (b'EXT_QUERY 0 X', b'EXT_QUERY 10001 X', b'EXT_QUERY -1 X',
                     b'EXT_QUERY +1 X', b'EXT_QUERY abc X', b'EXT_QUERY 1',
                     b'EXT_OTHER 1 X', b'EXT_QUERY  1 X', 'EXT_QUERY 1 X'):
            with self.subTest(line=line):
                with self.assertRaises(ContractError):
                    parse_monitor_request(line)

    def test_wire_matches_independently_crc_signed_frame(self):
        wire = signed(self.fields)
        self.assertEqual(encode_frame(self.session, 1, 'Q', 1, 2000, b'*IDN?'), wire)
        self.assertEqual(decode_frame(wire), {'session': self.session, 'request': 1,
                                             'kind': 'Q', 'mode': 1, 'timeout_ms': 2000,
                                             'payload': b'*IDN?'})

    def test_payload_is_binary_safe_and_bounded(self):
        payload = bytes(range(192))
        wire = encode_frame(self.session, 0xffffffff, 'R', 1, 10000, payload)
        self.assertLessEqual(len(wire), 512)
        self.assertEqual(decode_frame(wire)['payload'], payload)
        with self.assertRaises(ContractError):
            encode_frame(self.session, 1, 'Q', 1, 1, b'X' * 193)

    def test_handshake_kind_case_and_empty_payload(self):
        for kind in ('H', 'h'):
            wire = encode_frame(bytes(16), 0, kind, 0, 0, b'')
            frame = decode_frame(wire)
            self.assertEqual(frame['kind'], kind)
            self.assertEqual(frame['payload'], b'')

    def test_crc_rejects_changed_request_and_payload(self):
        wire = signed(self.fields)
        for wrong in (wire.replace(b'00000001', b'00000002', 1),
                      wire.replace(b'2A49444E3F', b'2A49444E3E', 1)):
            with self.assertRaisesRegex(ContractError, 'CRC'):
                decode_frame(wrong)

    def test_valid_crc_does_not_hide_bad_header_or_length(self):
        for index, value in ((0, '@X2'), (1, '00'), (1, 'Z' * 32), (2, '1'),
                             (3, 'x'), (4, '2'), (4, '01'), (5, '00002711'),
                             (5, '2000'), (6, '0006'), (7, 'GG' * 5)):
            fields = list(self.fields)
            fields[index] = value
            with self.subTest(index=index, value=value):
                with self.assertRaises(ContractError):
                    decode_frame(signed(fields))

    def test_decoder_rejects_incomplete_oversized_and_extra_frames(self):
        wire = signed(self.fields)
        for wrong in (wire[:-1], wire[:-2], wire + wire, b'X' * 513, b'\xff\r\n', b'\r\n'):
            with self.subTest(wrong=wrong[:30]):
                with self.assertRaises(ContractError):
                    decode_frame(wrong)

    def test_encoder_rejects_unrepresentable_header(self):
        for session, request, kind, mode, timeout in ((b'x', 1, 'Q', 1, 1),
                (self.session, -1, 'Q', 1, 1), (self.session, 0x100000000, 'Q', 1, 1),
                (self.session, 1, 'X', 1, 1), (self.session, 1, 'Q', True, 1),
                (self.session, 1, 'Q', 1, 10001)):
            with self.assertRaises(ContractError):
                encode_frame(session, request, kind, mode, timeout, b'X')

    def test_ate_reply_hex_preserves_raw_and_embedded_delimiters(self):
        raw = b'ADC Corp.,7355,246410099,  A02\r\n'
        reply = format_query_response(raw)
        _, _, count, hex_text = reply.split(':')
        self.assertEqual(int(count), len(raw))
        self.assertEqual(bytes.fromhex(hex_text), raw)
        for wrong in (b'', b'1\n', b'1\r\n2\r\n', b'x' * 193):
            with self.assertRaises(ContractError):
                format_query_response(wrong)

    def test_ate_error_cannot_inject_another_reply(self):
        self.assertEqual(format_error('TIMEOUT', True), 'ERR:EXT_TIMEOUT:AMBIGUOUS=1')
        self.assertEqual(format_error('COMMAND', False), 'ERR:EXT_COMMAND:AMBIGUOUS=0')
        for reason in ('', 'x', 'TIMEOUT\r\nOK', 'X:Y'):
            with self.assertRaises(ContractError):
                format_error(reason, False)


if __name__ == '__main__':
    unittest.main()
