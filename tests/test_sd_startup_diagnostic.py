"""Startup failures must remain observable without retrying or blocking ATE."""
import sys
import types
import unittest
from unittest.mock import patch

from src import main
from src.logger import LoggerError
from src.sd_sink import PicoSDSink


class StartupDiagnosticTests(unittest.TestCase):
    def test_experiment_changes_only_selected_pre_card_condition(self):
        for delay, early in [(0, False), (500, False), (0, True), (500, True)]:
            with self.subTest(delay=delay, early=early):
                events = []
                class Pin:
                    OUT = 1
                    IN = 0
                    PULL_UP = 2
                    def __init__(self, pin, *args, **kwargs):
                        if pin == 17:
                            events.append(('CS', kwargs.get('value')))
                def spi(*args, **kwargs):
                    events.append(('SPI', None))
                    return object()
                def card(*args):
                    events.append(('CARD', None))
                    raise OSError('CMD0 failed: 31')
                machine = types.SimpleNamespace(Pin=Pin, SPI=spi)
                sink = PicoSDSink(startup_delay_ms=delay, cs_before_spi=early)
                with patch.dict(sys.modules, machine=machine), \
                        patch('src.pico_clock.SystemClock.sleep_ms', side_effect=lambda ms: events.append(('WAIT', ms))), \
                        patch('src.sd_card.SDCard', side_effect=card) as init:
                    with self.assertRaises(LoggerError):
                        sink.mount()
                expected = [('WAIT', delay)] if delay else []
                expected += [('CS', 1), ('SPI', None)] if early else [('SPI', None), ('CS', None)]
                self.assertEqual(events, expected + [('CARD', None)])
                self.assertEqual(init.call_count, 1)
                self.assertIn('CMD0 failed: 31', sink.last_error)

    def test_card_init_error_preserved_and_no_retry(self):
        def pin_mock(pin, *args, **kwargs):
            return pin
        pin_mock.IN = 0
        pin_mock.OUT = 1
        pin_mock.PULL_UP = 2
        machine = types.SimpleNamespace(Pin=pin_mock, SPI=lambda *a, **k: object())
        sink = PicoSDSink()
        with patch.dict(sys.modules, machine=machine), patch(
                'src.sd_card.SDCard', side_effect=OSError('CMD0 failed: 31')) as card:
            with self.assertRaisesRegex(LoggerError, 'MOUNT_ERR'):
                sink.mount()
        self.assertEqual(card.call_count, 1)
        self.assertEqual(sink.mount_stage, 'CARD_INIT')
        self.assertIn('CMD0 failed: 31', sink.last_error)
        self.assertFalse(sink.mounted)

    def test_first_failure_snapshot_survives_recovery_and_ate_available(self):
        sink = PicoSDSink()
        def fail():
            sink.mount_stage = 'CARD_INIT'
            sink._error('MOUNT_ERR', OSError('CMD0 failed: 31'))
        with patch.object(main, 'startup_sd_diagnostic', None), \
                patch.object(main, 'create_ate_uart', return_value=None), \
                patch.object(main, 'create_nf55_uart', return_value=None), \
                patch.object(main, 'DS3231I2CDevice', side_effect=OSError('no RTC')), \
                patch.object(main, 'PicoSDSink', return_value=sink), \
                patch.object(sink, 'mount', side_effect=fail):
            app = main.create_fixture_app()
            snapshot = dict(main.startup_sd_diagnostic)
            self.assertEqual(app.execute_ate_line('SD_STATUS?'), 'MOUNT_ERR')
            self.assertEqual(app.execute_ate_line('FW_UPDATE'), 'ERR:FU_DISABLED')
            self.assertEqual(app.execute_ate_line('*IDN?'), 'NF55G_PICO_FIXTURE,Rev.0')
            with patch.object(sink, 'mount', return_value=None):
                sink.status, sink.last_error, sink.mount_stage = 'OK', None, 'READY'
                main.create_fixture_app()
            self.assertEqual(main.startup_sd_diagnostic, snapshot)
            self.assertIn('CMD0 failed: 31', snapshot['error'])


if __name__ == '__main__':
    unittest.main()
