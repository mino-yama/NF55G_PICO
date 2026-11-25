import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from inspect_ar_frames import inspect_readback
from src.frame import build_frame


class ArCaptureTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.payload = b'00000A00000001' * 10

    def save(self, name, raw):
        path = self.directory / name
        path.write_text(raw.hex() + '\n', encoding='utf8')
        return path

    def cli(self, *paths):
        return subprocess.run([sys.executable, str(Path(__file__).with_name('inspect_ar_frames.py')),
                               *(str(path) for path in paths)], capture_output=True, text=True)

    def test_before_only_preserves_frame_and_all_ten_points(self):
        raw = build_frame('AR', self.payload)
        report = inspect_readback(self.save('before.hex', raw))
        self.assertEqual(report['before']['frame_hex'], raw.hex().upper())
        self.assertEqual(len(report['before']['fields']), 20)
        self.assertEqual(report['before']['fields']['AR_DISCHG_I_P1_REF_RAW'], '00000001')
        self.assertNotIn('changed_fields', report)

    def test_comparison_reports_only_observed_changes(self):
        before = self.save('before.hex', build_frame('AR', self.payload))
        changed = self.payload[:98] + b'00000B3FECCCCD' + self.payload[112:]
        after = self.save('after.hex', build_frame('AR', changed))
        run = self.cli(before, '--after', after)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['changed_fields'], {
            'AR_BATT_CHG_P2_ADC': {'before': 10, 'after': 11},
            'AR_BATT_CHG_P2_REF_RAW': {'before': '00000001', 'after': '3FECCCCD'},
        })
        self.assertEqual(inspect_readback(before, before)['changed_fields'], {})

    def test_rejects_wrong_command_length_and_bcc_without_partial_result(self):
        frame = build_frame('AR', self.payload)
        wrong_bcc = frame[:-1] + (b'0' if frame[-1:] != b'0' else b'1')
        for raw in (build_frame('AD', self.payload), build_frame('AR', self.payload[:-1]), wrong_bcc):
            with self.subTest(raw=raw):
                run = self.cli(self.save('invalid.hex', raw))
                self.assertEqual(run.returncode, 1)
                self.assertEqual(run.stdout, '')
                self.assertIn('AR capture rejected', run.stderr)


if __name__ == '__main__':
    unittest.main()
