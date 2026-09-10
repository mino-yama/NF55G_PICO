import types
import unittest
from src.sd_card import SDCard
from firmware.sd_startup_probe import run_post_failure_probe


class Cmd0DiagnosticTests(unittest.TestCase):
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
