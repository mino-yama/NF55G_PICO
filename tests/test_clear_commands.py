"""CLEAR routing, wire contract and success/ambiguous cache invalidation."""
import unittest
from src import config
from src.cache_manager import CacheManager
from src.command_dispatcher import CommandDispatcher
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockUART, MockNF55GScenario, ScenarioStep
from src.nf55_protocol import NF55Protocol
from src.frame import parse_frame

CASES = [('CLEAR_POWER','CD',b'1',500),('CLEAR_BATT','CD',b'2',500),
         ('CLEAR_ALL','CD',b'0',500),('CLEAR_LOG','CL',b'',1000)]

class ClearCommandTests(unittest.TestCase):
    def app(self, steps):
        clock=FakeClock()
        uart=MockUART(clock, MockNF55GScenario(steps))
        protocol=NF55Protocol(uart,clock=clock)
        cache=CacheManager()
        for name in config.CACHE_NAMES: cache.validate(name,{'old':True},'OLD')
        return FixtureApp(protocol=protocol,cache=cache),uart

    def test_success_wire_timeout_and_exact_invalidation_without_response_promotion(self):
        for name,cmd,data,t2 in CASES:
            with self.subTest(name=name):
                app,uart=self.app([ScenarioStep.ack_response(cmd,'',response_delay_ms=t2-1)])
                self.assertEqual(app.execute_ate_line(name),'OK')
                frame=parse_frame(uart.tx_log[0])
                self.assertEqual((frame.cmd,frame.data),(cmd,data))
                for target in config.CACHE_NAMES:
                    self.assertEqual(app.cache.is_valid(target),target not in config.SUCCESS_INVALIDATION[cmd],target)
                self.assertEqual(app.protocol.last_result.command_retry_count,0)

    def test_ambiguous_timeout_invalidates_same_caches(self):
        for name,cmd,data,t2 in CASES:
            with self.subTest(name=name):
                app,uart=self.app([ScenarioStep.ack_timeout(),ScenarioStep.ack_timeout()])
                self.assertEqual(app.execute_ate_line(name),'ERR:ACK_TIMEOUT')
                self.assertTrue(app.protocol.last_result.ambiguous)
                self.assertEqual(app.protocol.last_result.command_retry_count,1)
                for target in config.CACHE_NAMES:
                    self.assertEqual(app.cache.is_valid(target),target not in config.SUCCESS_INVALIDATION[cmd],target)

    def test_sequence_error_does_not_invalidate(self):
        for name,cmd,data,t2 in CASES:
            app,uart=self.app([ScenarioStep.error('SQE')])
            self.assertEqual(app.execute_ate_line(name),'ERR:SQE')
            self.assertTrue(all(app.cache.is_valid(n) for n in config.CACHE_NAMES))

    def test_payload_is_rejected_without_transmission(self):
        for name,cmd,data,t2 in CASES:
            app,uart=self.app([])
            self.assertTrue(app.execute_ate_line(name+' 1').startswith('ERR:'))
            self.assertEqual(uart.tx_log,[])

    def test_nonempty_response_is_rejected_with_plain_nak(self):
        for name,cmd,data,t2 in CASES:
            app,uart=self.app([ScenarioStep.ack_response(cmd,'0')])
            self.assertEqual(app.execute_ate_line(name),'ERR:FINAL_BCC_FRAME')
            self.assertTrue(app.protocol.last_result.ambiguous)
            self.assertEqual(uart.tx_log[-1],b'\x15')

if __name__=='__main__': unittest.main()
