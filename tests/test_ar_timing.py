"""ARの承認済み100ms期限を、実機を使わず仮想時刻の通信で確認する。"""
import unittest

from src import config
from src.frame import build_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from tests.test_calibration_write import D5_SAMPLE, AD_RESPONSE, AR_RESPONSE


class ARTimingTests(unittest.TestCase):
    def sample(self, response_delay):
        self.clock = FakeClock()
        self.scenario = MockNF55GScenario([
            ScenarioStep.ack_response("D5", D5_SAMPLE),
            # ADは100msへ短縮しない。500ms後の診断応答を受理する。
            ScenarioStep.ack_response("AD", AD_RESPONSE, response_delay_ms=500),
            ScenarioStep.ack_response("AR", AR_RESPONSE[:84] + b"00000100000002" + AR_RESPONSE[98:], ack_delay_ms=20,
                                      response_delay_ms=response_delay),
        ])
        self.uart = MockUART(clock=self.clock, scenario=self.scenario)
        self.app = FixtureApp(nf55_uart=self.uart, clock=self.clock,
                              calibration_sample_enabled=True)
        self.ate = self.app.execute_ate_line
        self.assertEqual(self.ate("TEST_START"), "OK")
        self.assertEqual(self.ate("INFO_REFRESH"), "OK")
        self.assertTrue(self.ate("AD_4_A_2.0").startswith("OK:AD_WRITE:"))

    def test_ar_read_within_100ms_after_ack_returns_raw_result(self):
        self.assertEqual(config.T2_AR_MS, 100)
        # 送信から119msでも、ACKから99msなら受理する。
        self.sample(119)
        reply = self.ate('AR_READ_BATT_CHG A')
        self.assertEqual(reply, 'OK:AR_READ:BATT_CHG:A:1:00000002')
        self.assertEqual(self.scenario.handled_command_count, 3)
        self.assertIsNone(self.app.cache.get("AR"))

    def test_ar_after_100ms_times_out_without_retry_or_cache_promotion(self):
        self.sample(121)
        started = self.clock.ticks_ms()
        self.assertEqual(self.ate('AR_READ_BATT_CHG A'), 'ERR:AR_READ_TIMEOUT')
        self.assertLessEqual(self.clock.ticks_ms() - started, 121)
        self.assertEqual(self.scenario.handled_command_count, 3)
        self.assertEqual(self.uart.tx_log.count(build_frame("AR")), 1)
        self.assertIsNone(self.app.cache.get("AR"))


if __name__ == "__main__":
    unittest.main()
