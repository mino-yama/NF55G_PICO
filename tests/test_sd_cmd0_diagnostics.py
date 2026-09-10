import types
import unittest
from src.sd_card import SDCard
from firmware.sd_startup_probe import run_post_failure_probe


class Cmd0DiagnosticTests(unittest.TestCase):
    def test_clocks_only_adds_128_clocks_before_single_same_spi_retry(self):
        events = []
        class CS:
            value = 0
            def __call__(self, value):
                self.value = value
                events.append(('CS', value))
        cs = CS()
        spi = types.SimpleNamespace(
            write=lambda data: events.append(('WRITE', cs.value, bytes(data))),
            deinit=lambda: events.append(('DEINIT',)))
        card = types.SimpleNamespace(cs=cs, spi=spi,
            diagnose_cmd0_multi=lambda **kw: events.append(('CMD0', kw)) or [])
        app = types.SimpleNamespace(logger=types.SimpleNamespace(
            sd_sink=types.SimpleNamespace(mounted=False)), _comm_busy=lambda: False)
        result = run_post_failure_probe(app,
            dict(stage='CARD_INIT', error='CMD0 failed: 31', mounted=False),
            factory=lambda: self.fail('unexpected reconstruction'),
            mode='CLOCKS_ONLY', retained_card=card)
        self.assertEqual(events, [('CS', 1)] + [('WRITE', 1, b'\xff')] * 16
            + [('CMD0', dict(attempts=1, delay_ms=0)), ('CS', 1), ('DEINIT',)])
        self.assertIs(card.spi, spi)
        self.assertEqual(result['extra_idle_bytes'], 16)

    def test_retry_only_reuses_card_without_factory_or_delay(self):
        calls = []
        card = types.SimpleNamespace(cs=lambda v: calls.append(('cs', v)),
            spi=types.SimpleNamespace(deinit=lambda: calls.append(('deinit',))),
            diagnose_cmd0_multi=lambda **kw: calls.append(('cmd0', kw)) or [(1, '0x01', 1, [], True)])
        app = types.SimpleNamespace(logger=types.SimpleNamespace(
            sd_sink=types.SimpleNamespace(mounted=False)), _comm_busy=lambda: False)
        snapshot = dict(stage='CARD_INIT', error='CMD0 failed: 31', mounted=False)
        def forbidden():
            self.fail('SPI must not be reconstructed')
        result = run_post_failure_probe(app, snapshot, forbidden,
                                       mode='RETRY_ONLY', retained_card=card)
        self.assertEqual(calls, [('cmd0', dict(attempts=1, delay_ms=0)), ('cs', 1), ('deinit',)])
        self.assertEqual(result['first_startup'], snapshot)
        self.assertEqual(result['mode'], 'RETRY_ONLY')

    def test_retry_only_missing_card_does_not_fall_back_to_rebuild(self):
        app = types.SimpleNamespace(logger=types.SimpleNamespace(
            sd_sink=types.SimpleNamespace(mounted=False)), _comm_busy=lambda: False)
        result = run_post_failure_probe(app, dict(stage='CARD_INIT', error='CMD0 failed: 31'),
            lambda: self.fail('unexpected rebuild'), mode='RETRY_ONLY')
        self.assertEqual(result['skipped'], 'NO_RETAINED_CARD')

    def test_first_cmd0_sequence_and_failure_are_not_hidden(self):
        for responses, error, reads, pre_dummy in [([255, 255, 31, 1], '31', 3, True),
                                        ([255] * 100, '-1', 100, True),
                                        ([255, 255, 31, 1], '31', 3, False),
                                        ([255] * 100, '-1', 100, False)]:
            with self.subTest(error=error):
                events = []
                class CS:
                    OUT = 1
                    value = None
                    def init(self, mode, value):
                        self(value)
                    def __call__(self, value):
                        self.value = value
                        events.append(('CS', value))
                cs = CS()
                class SPI:
                    def init(self, **kwargs):
                        events.append(('INIT', cs.value, kwargs))
                    def write(self, data):
                        events.append(('WRITE', cs.value, bytes(data)))
                    def readinto(self, buffer, fill):
                        events.append(('READ', cs.value, fill))
                        buffer[0] = self.responses.pop(0)
                spi = SPI()
                spi.responses = list(responses)
                class CardUnderTest(SDCard):
                    CMD0_PRE_DUMMY = pre_dummy
                with self.assertRaisesRegex(OSError, 'CMD0 failed: ' + error):
                    CardUnderTest(spi, cs)
                self.assertEqual(events[0], ('CS', 1))
                self.assertEqual(events[1], ('INIT', 1,
                    dict(baudrate=100000, phase=0, polarity=0)))
                low = events.index(('CS', 0))
                self.assertEqual(events[2:low], [('WRITE', 1, b'\xff')] * 16)
                expected = [('WRITE', 0, b'\xff')] if pre_dummy else []
                expected += [('WRITE', 0, b'\x40\x00\x00\x00\x00\x95')]
                self.assertEqual(events[low + 1:low + 1 + len(expected)], expected)
                self.assertEqual([e for e in events if e[0] == 'READ'],
                                 [('READ', 0, 255)] * reads)
                self.assertEqual(events[-2:], [('CS', 1), ('WRITE', 1, b'\xff')])
                if error == '31':
                    self.assertEqual(spi.responses, [1])  # Do not swallow 31 and wait for 1.

    def test_method_records_timeout_and_errors_with_exact_commands(self):
        card = object.__new__(SDCard)
        sleeps, commands = [], []
        responses = iter([31, -1, 1])
        card.clock = types.SimpleNamespace(sleep_ms=sleeps.append)
        def cmd(*args):
            commands.append(args)
            return next(responses)
        card.cmd = cmd
        rows = card.diagnose_cmd0_multi(3, 50)
        self.assertEqual(commands, [(0, 0, 0x95)] * 3)
        self.assertEqual(sleeps, [50, 50])
        self.assertEqual([r[2] for r in rows], [31, -1, 1])
        self.assertEqual(rows[1][1:4], ('TIMEOUT', -1, []))
        self.assertEqual([r[4] for r in rows], [False, False, True])

    def test_limits_reject_before_spi_access(self):
        card = object.__new__(SDCard)
        for count, delay in [(0, 50), (21, 50), (10, -1), (10, 1001)]:
            with self.assertRaises(ValueError):
                card.diagnose_cmd0_multi(count, delay)

    def test_mounted_or_non_cmd0_failure_never_reset(self):
        def forbidden():
            self.fail('must not initialize SPI')
        for mounted, stage, error, reason in [
                (True, 'CARD_INIT', 'CMD0 failed: 31', 'FILESYSTEM_MOUNTED'),
                (False, 'VFS_MOUNT', 'FAT error', 'NOT_CMD0_FAILURE')]:
            app = types.SimpleNamespace(logger=types.SimpleNamespace(
                sd_sink=types.SimpleNamespace(mounted=mounted)))
            snap = dict(mounted=mounted, stage=stage, error=error)
            self.assertEqual(run_post_failure_probe(app, snap, forbidden)['skipped'], reason)

    def test_post_failure_keeps_first_evidence_and_releases_bus(self):
        cleanup = []
        card = types.SimpleNamespace(cs=lambda v: cleanup.append(v),
            spi=types.SimpleNamespace(deinit=lambda: cleanup.append('deinit')),
            diagnose_cmd0_multi=lambda **kwargs: [(1, '0x01', 1, [], True)])
        app = types.SimpleNamespace(logger=types.SimpleNamespace(
            sd_sink=types.SimpleNamespace(mounted=False)), _comm_busy=lambda: False)
        snapshot = dict(stage='CARD_INIT', error='CMD0 failed: 31', mounted=False)
        report = run_post_failure_probe(app, snapshot, lambda: card)
        self.assertEqual(report['first_startup'], snapshot)
        self.assertEqual(snapshot['error'], 'CMD0 failed: 31')
        self.assertTrue(report['results'][0][4])
        self.assertEqual(cleanup, [1, 'deinit'])
