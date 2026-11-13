"""ATE応答の設定終端、要求終端との独立性、短write／異常応答を検証する。"""
import unittest
from unittest.mock import patch
from src import config
from src.ate_server import ATEServer
from src.main import FixtureApp
from tests.test_runtime_integration import BytePort
from tests import test_runtime_integration as runtime_tests


class ATEResponseTerminatorTests(unittest.TestCase):
    def test_default_is_cr(self):
        self.assertEqual(config.ATE_RESPONSE_TERMINATOR, 'CR')
        port = BytePort(b'*IDN?\r\n')
        app = FixtureApp(ate_uart=port)
        app.service_once()
        self.assertEqual(bytes(port.tx), b'NF55G_PICO_FIXTURE,Rev.0\r')

    def test_each_response_setting_is_independent_of_request_ending(self):
        for name, suffix in (('CR', b'\r'), ('LF', b'\n'), ('CRLF', b'\r\n')):
            for request_ending in (b'\r', b'\n', b'\r\n'):
                with self.subTest(response=name, request=request_ending):
                    protocol, nf = runtime_tests.RuntimeIntegrationTests().protocol()
                    port = BytePort(request_ending.join([b'*IDN?', b'UNKNOWN', b'\xff', b'FW_UPDATE', b'']), max_write=1)
                    with patch.object(config, 'ATE_RESPONSE_TERMINATOR', name):
                        app = FixtureApp(ate_uart=port, protocol=protocol)
                    for _ in range(180):
                        app.service_once()
                    expected = suffix.join([b'NF55G_PICO_FIXTURE,Rev.0', b'ERR:UNKNOWN_CMD', b'ERR:ASCII', b'ERR:FU_DISABLED', b''])
                    self.assertEqual(bytes(port.tx), expected)
                    self.assertFalse(app.server.has_work())
                    self.assertEqual(nf.tx_log, [])

    def test_none_and_zero_write_preserve_the_configured_ending(self):
        for name, suffix in (('CR', b'\r'), ('LF', b'\n'), ('CRLF', b'\r\n')):
            with self.subTest(response=name):
                port = BytePort(max_write=1)
                with patch.object(config, 'ATE_RESPONSE_TERMINATOR', name):
                    server = ATEServer(port)
                server.reply('OK')
                expected = b'OK' + suffix
                for no_progress in (None, 0):
                    with patch.object(port, 'write', return_value=no_progress):
                        server.flush_reply()
                    self.assertEqual(server.tx, expected)
                with self.assertRaises(RuntimeError):
                    server.reply('NEXT')
                for _ in range(len(expected)):
                    server.flush_reply()
                self.assertEqual(bytes(port.tx), expected)
                self.assertEqual(server.tx, b'')

    def test_invalid_values_including_eoi_are_rejected_before_tx(self):
        for value in ('EOI', '', 'cr', None, b'\r', False, []):
            with self.subTest(value=value):
                port = BytePort()
                with patch.object(config, 'ATE_RESPONSE_TERMINATOR', value):
                    with self.assertRaisesRegex(ValueError, 'EOI is GPIB-only'):
                        ATEServer(port)
                self.assertEqual(port.tx, b'')

    def test_setting_is_latched_for_existing_server(self):
        port = BytePort()
        with patch.object(config, 'ATE_RESPONSE_TERMINATOR', 'CR'):
            server = ATEServer(port)
        with patch.object(config, 'ATE_RESPONSE_TERMINATOR', 'LF'):
            server.reply('OLD')
            server.flush_reply()
            replacement = ATEServer(port)
            replacement.reply('NEW')
            replacement.flush_reply()
        self.assertEqual(bytes(port.tx), b'OLD\rNEW\n')
