"""Host verification of CMD0 software behavior, not electrical or cold-boot proof.

Run: .venv/Scripts/python.exe -B verify_sd_diagnostics.py
Does not connect to Pico or change its files.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main():
    from src.sd_card import SDCard
    print('CMD0 diagnostics: Host verification', flush=True)
    try:
        compile((ROOT / 'firmware/sd_startup_probe.py').read_text(encoding='utf-8'),
                'firmware/sd_startup_probe.py', 'exec')
        expected = ['In Idle State', 'Erase Reset', 'Illegal Command',
                    'Command CRC Error', 'Erase Sequence Error']
        if SDCard._r1_bit_names(1) != ['In Idle State']:
            raise ValueError('incorrect idle label')
        if SDCard._r1_bit_names(31) != expected:
            raise ValueError('incorrect 0x1F labels')
    except Exception as exc:
        print('Precheck failed:', repr(exc))
        return 1
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / 'tests'), pattern='test_sd_cmd0_diagnostics.py')
    if suite.countTestCases() == 0:
        print('No diagnostic tests discovered')
        return 1
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    print('Verified software sequence: CS High, 16 FF bytes (128 clocks), CS Low,')
    print('one extra FF byte, CMD0 40 00 00 00 00 95; response polling uses FF.')
    print('Baseline initialization is 400000 baud, phase=0, polarity=0.')
    print('0x1F ends the first attempt as an error; it is not skipped to find 0x01.')
    print('Diagnostic CMD0_NO_PRE_FF removes only CMD0 pre-FF; both variants are tested.')
    print('R1 bit labels do not prove a physical CRC, wiring or power fault.')
    print('Pico cold-power behavior and signal/voltage measurements remain separate tests.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
