import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src import config
from src.frame import build_frame, parse_frame
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.nf55_protocol import (
    COMMAND_RETRY,
    FAILED,
    NF55Protocol,
    SUCCESS,
    TX_RESPONSE_ACK,
    TX_RESPONSE_NAK,
    VALIDATE_RESPONSE,
    WAIT_ACK,
    WAIT_RESPONSE,
    WAIT_RESPONSE_RETRY,
)


class NF55ProtocolTests(unittest.TestCase):
    def make_protocol(self, steps):
        clock = FakeClock()
        scenario = MockNF55GScenario(steps)
        uart = MockUART(clock=clock, scenario=scenario)
        return NF55Protocol(uart=uart, clock=clock), uart, scenario

    def test_normal_ack_response_ack_success(self):
        protocol, uart, _scenario = self.make_protocol(
            [ScenarioStep.ack_response("D1", "308000000000000")]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertTrue(result.ok)
        self.assertEqual(result.response_data, b"308000000000000")
        self.assertEqual(result.command_retry_count, 0)
        self.assertEqual(result.response_retry_count, 0)
        self.assertFalse(result.ambiguous)
        self.assertIn(WAIT_ACK, protocol.state_trace)
        self.assertIn(WAIT_RESPONSE, protocol.state_trace)
        self.assertIn(VALIDATE_RESPONSE, protocol.state_trace)
        self.assertIn(TX_RESPONSE_ACK, protocol.state_trace)
        self.assertIn(SUCCESS, protocol.state_trace)
        self.assertEqual(uart.tx_log[-1], bytes((config.ACK,)))

    def test_nak33_then_one_command_retry_recovers(self):
        protocol, uart, scenario = self.make_protocol(
            [
                ScenarioStep.nak("33"),
                ScenarioStep.ack_response("D1", "0" * 15),
            ]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertTrue(result.ok)
        self.assertEqual(result.command_retry_count, 1)
        self.assertEqual(result.response_retry_count, 0)
        self.assertEqual(scenario.handled_command_count, 2)
        self.assertEqual(len([tx for tx in uart.tx_log if tx.startswith(bytes((config.STX,)))]), 2)
        self.assertIn(COMMAND_RETRY, protocol.state_trace)

    def test_second_nak33_fails_without_ambiguous(self):
        protocol, _uart, _scenario = self.make_protocol(
            [ScenarioStep.nak("33"), ScenarioStep.nak("33")]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "NAK")
        self.assertEqual(result.nak_reason, "33")
        self.assertEqual(result.command_retry_count, 1)
        self.assertFalse(result.ambiguous)
        self.assertIn(FAILED, protocol.state_trace)

    def test_ack_timeout_retry_recovers(self):
        protocol, _uart, _scenario = self.make_protocol(
            [
                ScenarioStep.ack_timeout(),
                ScenarioStep.ack_response("D1", "0" * 15),
            ]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertTrue(result.ok)
        self.assertEqual(result.command_retry_count, 1)
        self.assertFalse(result.ambiguous)

    def test_final_ack_timeout_fails_ambiguous(self):
        protocol, _uart, _scenario = self.make_protocol(
            [ScenarioStep.ack_timeout(), ScenarioStep.ack_timeout()]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "ACK_TIMEOUT")
        self.assertEqual(result.command_retry_count, 1)
        self.assertTrue(result.ambiguous)

    def test_response_timeout_retry_recovers(self):
        protocol, _uart, _scenario = self.make_protocol(
            [
                ScenarioStep.resp_timeout(),
                ScenarioStep.ack_response("D1", "0" * 15),
            ]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertTrue(result.ok)
        self.assertEqual(result.command_retry_count, 1)
        self.assertEqual(result.response_retry_count, 0)

    def test_final_response_timeout_fails_ambiguous(self):
        protocol, _uart, _scenario = self.make_protocol(
            [ScenarioStep.resp_timeout(), ScenarioStep.resp_timeout()]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "RESP_TIMEOUT")
        self.assertEqual(result.command_retry_count, 1)
        self.assertTrue(result.ambiguous)

    def test_bcc_ng_sends_plain_nak_then_response_retry_success(self):
        protocol, uart, scenario = self.make_protocol(
            [ScenarioStep.bcc_ng_then_retry("D1", "0" * 15, retry_data="1" * 15)]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertTrue(result.ok)
        self.assertEqual(result.response_data, b"1" * 15)
        self.assertEqual(result.command_retry_count, 0)
        self.assertEqual(result.response_retry_count, 1)
        self.assertEqual(scenario.response_retry_request_count, 1)
        self.assertIn(bytes((config.NAK,)), uart.tx_log)
        self.assertNotIn(bytes((config.NAK,)) + b"33", uart.tx_log)
        self.assertIn(TX_RESPONSE_NAK, protocol.state_trace)
        self.assertIn(WAIT_RESPONSE_RETRY, protocol.state_trace)

    def test_final_bcc_ng_fails_ambiguous_without_command_retry(self):
        protocol, _uart, _scenario = self.make_protocol(
            [ScenarioStep.bcc_ng("D1", "0" * 15)]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "FINAL_BCC_FRAME")
        self.assertEqual(result.command_retry_count, 0)
        self.assertEqual(result.response_retry_count, 1)
        self.assertTrue(result.ambiguous)

    def test_pme_sqe_hwe_error_frames(self):
        expected_ambiguous = {"PME": False, "SQE": False, "HWE": True}
        for error_code, ambiguous in expected_ambiguous.items():
            with self.subTest(error_code=error_code):
                protocol, uart, _scenario = self.make_protocol([ScenarioStep.error(error_code)])

                result = protocol.transact("D1", t2_ms=100, expected_length=15)

                self.assertFalse(result.ok)
                self.assertEqual(result.error, error_code)
                self.assertEqual(result.ambiguous, ambiguous)
                self.assertEqual(uart.tx_log[-1], bytes((config.ACK,)))

    def test_wrong_length_uses_response_retry_path(self):
        protocol, uart, _scenario = self.make_protocol(
            [ScenarioStep.ack_response("D1", "0" * 14)]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "FINAL_BCC_FRAME")
        self.assertEqual(result.response_retry_count, 1)
        self.assertEqual(result.command_retry_count, 0)
        self.assertIn(bytes((config.NAK,)), uart.tx_log)

    def test_raw_response_is_valid_frame_on_success(self):
        protocol, _uart, _scenario = self.make_protocol(
            [ScenarioStep.ack_response("D1", "0" * 15)]
        )

        result = protocol.transact("D1", t2_ms=100, expected_length=15)

        frame = parse_frame(result.raw_response)
        self.assertEqual(frame.cmd, "D1")


if __name__ == "__main__":
    unittest.main()
