"""中継コアの分割応答・期限・取消・再接続・原文保持をHostで検証する。"""
import unittest

from src.external_instrument_relay import ExternalInstrumentRelay, RelayError
from src.mock_nf55g import FakeClock


class ExternalInstrumentRelayTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.relay = ExternalInstrumentRelay(self.clock, 128, 64)
        self.relay.establish_link()

    def begin(self, command=b'*IDN?', query=True, timeout=100):
        return self.relay.begin(command, query, timeout, b'\r\n' if query else None)

    def send(self, token):
        self.assertTrue(self.relay.mark_tx_started(token))
        self.assertTrue(self.relay.mark_tx_complete(token))

    def test_idn_response_survives_every_two_fragment_boundary(self):
        raw = b'ADC Corp.,7355,246410099,  A02\r\n'
        for offset in range(1, len(raw)):
            with self.subTest(offset=offset):
                self.setUp()
                token = self.begin()
                self.send(token)
                self.assertTrue(self.relay.receive(token, raw[:offset]))
                self.assertIsNone(self.relay.take_result())
                self.assertTrue(self.relay.receive(token, raw[offset:]))
                result = self.relay.take_result()
                self.assertEqual(result['raw'], raw)
                self.assertEqual(result['status'], 'RESPONSE_COMPLETE')
                self.assertFalse(result['ambiguous'])

    def test_command_case_spaces_quotes_and_commas_remain_unchanged(self):
        command = b':sens:func "VOLT:DC" ; :x  +1.00,  2 '
        token = self.begin(command)
        request = self.relay.request(token)
        self.assertEqual(request['command'], command)
        request['command'] = b'changed'
        self.assertEqual(self.relay.request(token)['command'], command)

    def test_response_is_raw_not_range_or_number_judgement(self):
        token = self.begin(b':CONF?')
        self.send(token)
        raw = b'"VOLT +1.999999E+02,+1.000000E-05"\r\n'
        self.assertTrue(self.relay.receive(token, raw))
        self.assertEqual(self.relay.take_result()['raw'], raw)

    def test_response_flag_is_explicit_not_inferred_from_question_mark(self):
        token = self.begin(b':command_without_question', query=True)
        self.send(token)
        self.assertIsNone(self.relay.take_result())
        self.assertTrue(self.relay.receive(token, b'1\r\n'))
        self.assertEqual(self.relay.take_result()['status'], 'RESPONSE_COMPLETE')
        token = self.begin(b':literal?', query=False)
        self.send(token)
        result = self.relay.take_result()
        self.assertEqual(result['status'], 'TX_COMPLETE')
        self.assertEqual(result['raw'], b'')

    def test_result_must_be_consumed_before_next_request(self):
        token = self.begin(query=False)
        self.send(token)
        with self.assertRaisesRegex(RelayError, 'BUSY'):
            self.begin()
        self.relay.take_result()
        self.assertNotEqual(self.begin(), token)

    def test_busy_rejection_keeps_original_request(self):
        token = self.begin()
        with self.assertRaisesRegex(RelayError, 'BUSY'):
            self.begin(b':READ?')
        self.assertEqual(self.relay.request(token)['command'], b'*IDN?')

    def test_response_before_tx_callback_waits_for_both_completions(self):
        token = self.begin()
        self.assertTrue(self.relay.mark_tx_started(token))
        self.assertTrue(self.relay.receive(token, b'1\r\n'))
        self.assertIsNone(self.relay.take_result())
        self.assertTrue(self.relay.mark_tx_complete(token))
        self.assertEqual(self.relay.take_result()['status'], 'RESPONSE_COMPLETE')

    def test_unexpected_response_before_tx_does_not_succeed(self):
        token = self.begin()
        self.assertFalse(self.relay.receive(token, b'old\r\n'))
        result = self.relay.take_result()
        self.assertEqual(result['status'], 'UNEXPECTED_DATA')
        self.assertFalse(result['ambiguous'])
        self.assertFalse(self.relay.ready)

    def test_timeout_before_and_after_tx_have_different_ambiguity(self):
        for started in (False, True):
            with self.subTest(started=started):
                self.setUp()
                token = self.begin()
                if started:
                    self.relay.mark_tx_started(token)
                self.clock.sleep_ms(100)
                result = self.relay.take_result()
                self.assertEqual(result['status'], 'TIMEOUT')
                self.assertEqual(result['ambiguous'], started)
                with self.assertRaisesRegex(RelayError, 'LINK_NOT_READY'):
                    self.begin()

    def test_deadline_boundary_rejects_late_complete_response(self):
        token = self.begin()
        self.send(token)
        self.clock.sleep_ms(99)
        self.assertTrue(self.relay.receive(token, b'part'))
        self.clock.sleep_ms(1)
        self.assertFalse(self.relay.receive(token, b'ial\r\n'))
        result = self.relay.take_result()
        self.assertEqual(result['status'], 'TIMEOUT')
        self.assertEqual(result['raw'], b'part')

    def test_partial_tx_failure_has_no_automatic_retry(self):
        token = self.begin()
        self.relay.mark_tx_started(token)
        self.assertTrue(self.relay.fail(token, 'TX_PARTIAL'))
        self.assertFalse(self.relay.mark_tx_complete(token))
        self.assertFalse(self.relay.receive(token, b'1\r\n'))
        result = self.relay.take_result()
        self.assertEqual(result['status'], 'TX_PARTIAL')
        self.assertTrue(result['ambiguous'])
        self.assertFalse(self.relay.ready)

    def test_stale_token_cannot_finish_new_connection_request(self):
        old = self.begin()
        self.send(old)
        self.relay.disconnect()
        self.assertEqual(self.relay.take_result()['status'], 'DISCONNECTED')
        self.relay.establish_link()
        new = self.begin()
        self.send(new)
        self.assertNotEqual(old, new)
        self.assertFalse(self.relay.receive(old, b'old\r\n'))
        self.assertFalse(self.relay.fail(old, 'DISCONNECTED'))
        self.assertIsNone(self.relay.take_result())
        self.assertTrue(self.relay.receive(new, b'new\r\n'))
        self.assertEqual(self.relay.take_result()['raw'], b'new\r\n')

    def test_cancel_discards_pending_and_requires_explicit_recovery(self):
        token = self.begin()
        self.relay.mark_tx_started(token)
        self.relay.receive(token, b'partial')
        self.assertTrue(self.relay.cancel(token))
        self.assertFalse(self.relay.receive(token, b'late\r\n'))
        with self.assertRaisesRegex(RelayError, 'BUSY'):
            self.relay.establish_link()
        result = self.relay.take_result()
        self.assertEqual(result['status'], 'CANCELLED')
        self.assertTrue(result['ambiguous'])
        self.assertEqual(result['raw'], b'partial')
        self.assertFalse(self.relay.ready)
        self.relay.establish_link()
        self.assertTrue(self.relay.ready)

    def test_extra_lines_are_not_used_as_the_next_response(self):
        token = self.begin()
        self.send(token)
        self.assertFalse(self.relay.receive(token, b'1\r\n2\r\n'))
        result = self.relay.take_result()
        self.assertEqual(result['status'], 'EXTRA_DATA')
        self.assertTrue(result['ambiguous'])
        self.assertFalse(self.relay.ready)

    def test_extra_callback_invalidates_unconsumed_success(self):
        token = self.begin()
        self.send(token)
        self.assertTrue(self.relay.receive(token, b'1\r\n'))
        self.assertFalse(self.relay.receive(token, b'2\r\n'))
        self.assertEqual(self.relay.take_result()['status'], 'EXTRA_DATA')
        self.assertFalse(self.relay.ready)

    def test_response_limit_accepts_boundary_and_rejects_overflow(self):
        for length, expected in ((64, 'RESPONSE_COMPLETE'), (65, 'RESPONSE_TOO_LONG')):
            with self.subTest(length=length):
                self.setUp()
                token = self.begin()
                self.send(token)
                self.relay.receive(token, b'x' * (length - 2) + b'\r\n')
                result = self.relay.take_result()
                self.assertEqual(result['status'], expected)
                self.assertLessEqual(len(result['raw']), 64)

    def test_bad_requests_never_create_pending_work(self):
        for command in (b'', b'x' * 129, b'a\r\n', b'\x00', b'\xff', 'text'):
            with self.subTest(command=command):
                with self.assertRaises(RelayError):
                    self.begin(command)
                self.assertFalse(self.relay.busy)
        for flag, timeout, ending in ((None, 100, b'\r\n'), (True, 0, b'\r\n'),
                                      (True, True, b'\r\n'), (True, 1, b''),
                                      (False, 100, b'\r\n')):
            with self.subTest(flag=flag, timeout=timeout, ending=ending):
                with self.assertRaises(RelayError):
                    self.relay.begin(b'X', flag, timeout, ending)
                self.assertFalse(self.relay.busy)

    def test_no_link_no_request_and_no_silent_recovery(self):
        self.relay.disconnect()
        with self.assertRaisesRegex(RelayError, 'LINK_NOT_READY'):
            self.begin()
        self.clock.sleep_ms(10000)
        with self.assertRaisesRegex(RelayError, 'LINK_NOT_READY'):
            self.begin()

    def test_repeated_tx_callbacks_do_not_duplicate_completion(self):
        token = self.begin(query=False)
        self.assertFalse(self.relay.mark_tx_complete(token))
        self.assertTrue(self.relay.mark_tx_started(token))
        self.assertFalse(self.relay.mark_tx_started(token))
        self.assertTrue(self.relay.mark_tx_complete(token))
        self.assertFalse(self.relay.mark_tx_complete(token))
        self.assertIsNotNone(self.relay.take_result())
        self.assertIsNone(self.relay.take_result())


if __name__ == '__main__':
    unittest.main()
