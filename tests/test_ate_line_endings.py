"""ATE終端の混在、空行、分割到着、異常復帰を確認する。"""
import unittest
from src.ate_server import ATEServer
from src.main import FixtureApp
from tests.test_runtime_integration import BytePort
from tests import test_runtime_integration as runtime_tests
from tests.test_decoder_complete import d0_payload
from src.mock_nf55g import ScenarioStep


class ATELineEndingTests(unittest.TestCase):
    def test_d0_each_ending_executes_once(self):
        for ending in (b'\r', b'\n', b'\r\n'):
            with self.subTest(ending=ending):
                protocol, nf = runtime_tests.RuntimeIntegrationTests().protocol([
                    ScenarioStep.ack_response('D0', d0_payload())])
                port = BytePort(b'DATA_REFRESH' + ending)
                app = FixtureApp(ate_uart=port, protocol=protocol)
                for _ in range(20):
                    app.service_once()
                self.assertEqual(bytes(port.tx), b'OK\r\n')
                self.assertEqual(len([x for x in nf.tx_log if x.startswith(b'\x02')]), 1)

    def test_periodic_cr_does_not_leave_work_or_poison_next_command(self):
        port = BytePort()
        app = FixtureApp(ate_uart=port)
        for _ in range(10):
            port.rx.extend(b'\r')
            app.service_once()
            self.assertFalse(app.server.has_work())
            self.assertEqual(port.tx, b'')
        port.rx.extend(b'*IDN?\n')
        app.service_once()
        self.assertEqual(bytes(port.tx), b'NF55G_PICO_FIXTURE,Rev.0\r\n')

    def test_split_crlf_and_mixed_empty_lines(self):
        port = BytePort(b'*IDN?\r')
        app = FixtureApp(ate_uart=port)
        app.service_once()
        self.assertFalse(app.server.has_work())
        port.rx.extend(b'\n\r\n\n*IDN?\n*IDN?\r\n')
        for _ in range(10):
            app.service_once()
        self.assertEqual(bytes(port.tx), b'NF55G_PICO_FIXTURE,Rev.0\r\n' * 3)

    def test_errors_recover_at_each_ending(self):
        for ending in (b'\r', b'\n', b'\r\n'):
            for raw, error in ((b'A' * 513, 'LINE_TOO_LONG'), (b'\xff', 'ASCII'), (b'\x00', 'FRAME')):
                with self.subTest(ending=ending, error=error):
                    port = BytePort(raw + ending + b'*IDN?\r\n')
                    app = FixtureApp(ate_uart=port)
                    for _ in range(30):
                        app.service_once()
                    self.assertEqual(bytes(port.tx), ('ERR:' + error + '\r\nNF55G_PICO_FIXTURE,Rev.0\r\n').encode())

    def test_pending_queue_limit_preserves_mixed_lines(self):
        port = BytePort(b'A\r\nB\nC\r')
        server = ATEServer(port, max_pending=1)
        for expected in (b'A', b'B', b'C'):
            server.pump()
            self.assertEqual(server.pending.pop(0), (expected, None))
        server.pump()
        self.assertFalse(server.has_work())
