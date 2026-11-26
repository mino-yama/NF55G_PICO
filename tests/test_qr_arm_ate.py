"""Exercise the candidate through the same UART entry as the fixture's ATE."""
import unittest

from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART
from tests.test_qr_ss_workflow import QR, QRPort, record
from tests.test_runtime_integration import BytePort


B = 'US250A-CGXE-009491-101A032601000002'
SS_B = b'FFFFFFA03 2601000002' + b'F' * 30


class QRArmATETests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.ate = BytePort()
        self.qr = QRPort(max_write=4)
        self.nf55 = MockUART(self.clock, MockNF55GScenario(()))
        self.app = FixtureApp(ate_uart=self.ate, nf55_uart=self.nf55, clock=self.clock,
                              qr_transport=self.qr, qr_host_arm=True)
        self.seq = 0
        self.assertEqual(self.ate_command('TEST_START'), 'OK')

    def ate_command(self, command):
        self.ate.tx.clear()
        self.ate.rx.extend(command.encode() + b'\r')
        self.app.service_once()
        self.assertTrue(self.ate.tx.endswith(b'\r'), self.ate.tx)
        return self.ate.tx.decode().strip()

    def scan(self, timeout=5000):
        response = self.ate_command('QR_SCAN {}'.format(timeout))
        self.assertTrue(response.startswith('OK:QR_PENDING:'), response)
        token = response.split(':')[-1]
        host_id = (token[1:17].upper() + token[-8:]).encode()
        self.qr.tx.clear()
        for _ in range(10):
            self.app.service_once()
        self.assertEqual(self.qr.tx, b'\nA' + host_id + b'\n')
        return token, host_id

    def feed(self, kind, payload):
        self.seq += 1
        self.qr.rx.extend(record(self.seq, payload, kind))

    def assert_no_nf55(self):
        self.assertEqual(self.nf55.tx_log, [])

    def test_old_data_and_wrong_id_never_open_gate_or_replace_b(self):
        token, host = self.scan()
        self.feed(12, QR)
        self.feed(16, b'0' * 24 + b'\0')
        self.feed(17, host + QR.encode())
        self.assertEqual(self.ate_command('QR_GET? ' + token), 'ERR:QR_ARMING')
        self.assertEqual(self.ate_command('COMM_STATUS?'), 'OK:state=IDLE')
        self.feed(16, host + b'\1')
        self.assertEqual(self.ate_command('QR_GET? ' + token), 'ERR:QR_READING')
        self.assertEqual(self.app.qr_write.arm_discarded, 1)
        self.feed(17, b'0' * 24 + QR.encode())
        self.feed(17, host + B.encode())
        self.feed(17, host + QR.encode())
        self.assertEqual(self.ate_command('QR_GET? ' + token), 'OK:QR_GET:' + token + ':' + B)
        self.assertEqual(self.ate_command('QR_DATA? ' + token), 'OK:QR_DATA:' + token + ':' + SS_B.hex())
        self.assert_no_nf55()

    def test_cancel_end_and_late_frames_cannot_authorize_write(self):
        old, old_host = self.scan()
        self.assertEqual(self.ate_command('QR_CANCEL'), 'OK')
        new, host = self.scan()
        self.assertNotEqual(old, new)
        self.feed(16, old_host + b'\1')
        self.feed(17, old_host + QR.encode())
        self.assertEqual(self.ate_command('QR_WRITE ' + old), 'ERR:QR_STALE_ID')
        self.assertEqual(self.ate_command('QR_WRITE ' + new), 'ERR:QR_ARMING')
        self.feed(16, host + b'\0')
        self.feed(17, host + B.encode())
        self.assertIn(SS_B.hex(), self.ate_command('QR_DATA? ' + new))
        self.assertEqual(self.ate_command('TEST_END'), 'OK')
        self.assertEqual(self.ate_command('QR_WRITE ' + new), 'ERR:QR_STALE_ID')
        self.assert_no_nf55()

    def test_missing_ack_and_read_timeout_share_original_deadline(self):
        token, host = self.scan(100)
        self.clock.sleep_ms(100)
        self.feed(16, host + b'\0')
        self.feed(17, host + B.encode())
        self.assertEqual(self.ate_command('QR_GET? ' + token), 'ERR:QR_TIMEOUT')
        new, host = self.scan(100)
        self.clock.sleep_ms(90)
        self.feed(16, host + b'\0')
        self.assertEqual(self.ate_command('QR_GET? ' + new), 'ERR:QR_READING')
        self.clock.sleep_ms(10)
        self.assertEqual(self.ate_command('QR_WRITE ' + new), 'ERR:QR_TIMEOUT')
        self.assert_no_nf55()

    def test_disconnect_and_reboot_reject_current_acquisition(self):
        for kind in (3, 1):
            token, host = self.scan()
            self.feed(16, host + b'\0')
            self.feed(kind, b'')
            self.feed(17, host + B.encode())
            self.assertEqual(self.ate_command('QR_WRITE ' + token), 'ERR:QR_HOST_RESTART_OR_DISCONNECT')
        self.assert_no_nf55()

    def test_no_product_guard_even_after_review(self):
        self.app.protocol = None
        self.app.dispatcher.protocol = None
        token, host = self.scan()
        self.feed(16, host + b'\0')
        self.feed(17, host + B.encode())
        self.assertIn(SS_B.hex(), self.ate_command('QR_DATA? ' + token))
        self.assertEqual(self.ate_command('QR_WRITE ' + token), 'ERR:NF55G_NOT_CONNECTED')
        self.assert_no_nf55()

    def test_20_normal_and_10_late_acquisitions_without_nf55(self):
        previous = old_host = None
        for case in range(30):
            with self.subTest(case=case + 1):
                token, host = self.scan()
                self.assertNotEqual(token, previous)
                if case >= 20:
                    self.feed(12, QR)
                    self.feed(17, old_host + QR.encode())
                    self.assertEqual(self.ate_command('QR_GET? ' + token), 'ERR:QR_ARMING')
                self.feed(16, host + bytes([case >= 20]))
                self.feed(17, host + B.encode())
                self.assertIn(SS_B.hex(), self.ate_command('QR_DATA? ' + token))
                if previous is not None:
                    self.assertEqual(self.ate_command('QR_GET? ' + previous), 'ERR:QR_STALE_ID')
                previous, old_host = token, host
        self.assertEqual(self.ate_command('TEST_END'), 'OK')
        self.assert_no_nf55()
