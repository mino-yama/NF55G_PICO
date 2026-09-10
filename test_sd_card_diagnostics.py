"""Compatibility entry for the executable CMD0 diagnostic regression tests."""
import sys
import unittest

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover('tests', pattern='test_sd_cmd0_diagnostics.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
