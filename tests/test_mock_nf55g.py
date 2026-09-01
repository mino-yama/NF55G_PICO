import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src import config
from src.frame import FrameError, build_frame, parse_frame
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ResponseFactory, ScenarioStep


class MockNF55GTests(unittest.TestCase):
    def test_ack_response(self):
        scenario = MockNF55GScenario([ScenarioStep.ack_response("D1", "308000000000000")])
        uart = MockUART(scenario=scenario)

        uart.write(build_frame("D1"))

        self.assertEqual(uart.read(1), bytes((config.ACK,)))
        frame = parse_frame(uart.read_all(), expected_cmd="D1", expected_length=15)
        self.assertEqual(frame.data, b"308000000000000")
        self.assertEqual(scenario.handled_command_count, 1)

    def test_nak33(self):
        scenario = MockNF55GScenario([ScenarioStep.nak("33")])
        uart = MockUART(scenario=scenario)

        uart.write(build_frame("SC", "260901123456"))

        self.assertEqual(uart.read_all(), bytes((config.NAK,)) + b"33")

    def test_ack_timeout_returns_no_bytes(self):
        clock = FakeClock()
        scenario = MockNF55GScenario([ScenarioStep.ack_timeout()])
        uart = MockUART(clock=clock, scenario=scenario)

        uart.write(build_frame("D1"))
        clock.advance_ms(config.T1_ACK_TIMEOUT_MS + 1)

        self.assertEqual(uart.read_all(), b"")
        self.assertEqual(uart.any(), 0)

    def test_resp_timeout_returns_ack_only(self):
        clock = FakeClock()
        scenario = MockNF55GScenario([ScenarioStep.resp_timeout()])
        uart = MockUART(clock=clock, scenario=scenario)

        uart.write(build_frame("D1"))

        self.assertEqual(uart.read(1), bytes((config.ACK,)))
        clock.advance_ms(config.T2_DEFAULT_MS + 1)
        self.assertEqual(uart.read_all(), b"")

    def test_bcc_ng_response(self):
        scenario = MockNF55GScenario([ScenarioStep.bcc_ng("D1", "308000000000000")])
        uart = MockUART(scenario=scenario)

        uart.write(build_frame("D1"))

        self.assertEqual(uart.read(1), bytes((config.ACK,)))
        with self.assertRaises(FrameError):
            parse_frame(uart.read_all(), expected_cmd="D1", expected_length=15)

    def test_error_responses_pme_sqe_hwe(self):
        for error_code in ("PME", "SQE", "HWE"):
            with self.subTest(error_code=error_code):
                scenario = MockNF55GScenario([ScenarioStep.error(error_code)])
                uart = MockUART(scenario=scenario)

                uart.write(build_frame("D1"))

                self.assertEqual(uart.read(1), bytes((config.ACK,)))
                frame = parse_frame(uart.read_all(), expected_cmd="ER", expected_length=3)
                self.assertEqual(frame.data.decode("ascii"), error_code)

    def test_delayed_outputs_follow_fake_clock(self):
        clock = FakeClock()
        scenario = MockNF55GScenario([ScenarioStep.ack_response("D1", "0" * 15, ack_delay_ms=5, response_delay_ms=20)])
        uart = MockUART(clock=clock, scenario=scenario)

        uart.write(build_frame("D1"))
        self.assertEqual(uart.read_all(), b"")

        clock.advance_ms(5)
        self.assertEqual(uart.read(1), bytes((config.ACK,)))
        self.assertEqual(uart.read_all(), b"")

        clock.advance_ms(15)
        self.assertEqual(parse_frame(uart.read_all()).data, b"0" * 15)

    def test_response_factory_rejects_unknown_error_code(self):
        with self.assertRaises(ValueError):
            ResponseFactory.error_frame("XYZ")

    def test_pico_ack_nak_writes_do_not_consume_scenario_steps(self):
        scenario = MockNF55GScenario([ScenarioStep.nak("33")])
        uart = MockUART(scenario=scenario)

        uart.write(bytes((config.ACK,)))
        uart.write(bytes((config.NAK,)))

        self.assertEqual(scenario.remaining(), 1)
        self.assertEqual(uart.read_all(), b"")


if __name__ == "__main__":
    unittest.main()
