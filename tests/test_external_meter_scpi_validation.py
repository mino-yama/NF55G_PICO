"""実FWと同じC処理でSCPI設定応答とREAD前レンジゲートを検証する。"""
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'firmware/usb_submcu_external_meter_host'


class MeterScpiValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tcc = ROOT / 'tools/usb_submcu/host-test-tcc/tcc/tcc.exe'
        compiler = str(tcc) if os.name == 'nt' and tcc.exists() else shutil.which('cc')
        if not compiler:
            raise RuntimeError('Native C compiler required for meter firmware validation')
        cls.temp = tempfile.TemporaryDirectory(prefix='nf55g_meter_scpi_')
        directory = Path(cls.temp.name)
        wrapper = directory / 'wrapper.c'
        wrapper.write_text('''#include "scpi_response_validation.h"
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API
#endif
API int test_number(const unsigned char *b, size_t n, double *v) {
    return meter_scpi_number(b, n, v);
}
API int test_range(const unsigned char *b, size_t n) {
    return meter_scpi_confirms_20v(b, n);
}
''', encoding='ascii')
        library = directory / ('validation.dll' if os.name == 'nt' else 'validation.so')
        command = [compiler, '-shared', '-I', str(SOURCE),
                   str(SOURCE / 'scpi_response_validation.c'), str(wrapper), '-o', str(library)]
        if os.name != 'nt':
            command[2:2] = ['-fPIC']
        subprocess.run(command, check=True, capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.test_number.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_double)]
        cls.lib.test_number.restype = ctypes.c_int
        cls.lib.test_range.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.test_range.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        if os.name == 'nt':
            import _ctypes
            _ctypes.FreeLibrary(cls.lib._handle)
        cls.lib = None
        cls.temp.cleanup()

    def number(self, raw):
        value = ctypes.c_double(123.0)
        accepted = bool(self.lib.test_number(raw, len(raw), ctypes.byref(value)))
        return accepted, value.value

    def test_observed_zero_padded_setting_and_exponent(self):
        for raw, expected in [(b'00001\r\n', 1), (b'0\r\n', 0),
                              (b'+1.000000E+00\r\n', 1), (b' -0.0 ', 0), (b'.5', .5)]:
            with self.subTest(raw=raw):
                self.assertEqual(self.number(raw), (True, expected))

    def test_reject_nondecimal_nonfinite_and_malformed_numbers(self):
        for raw in [b'', b' ', b'NaN', b'Inf', b'-Infinity', b'0x1p0', b'1E',
                    b'1E+', b'.', b'--1', b'1V', b'1,2', b'1\x00junk',
                    b'1\r\n2', b'1\n', b'1e9999', b'1e-9999', b'1' * 257]:
            with self.subTest(raw=raw):
                self.assertEqual(self.number(raw), (False, 123.0))

    def test_accept_complete_20v_configuration(self):
        for raw in [b'"VOLT +1.999999E+01,+1.000000E-05"\r\n',
                    b'VOLT 20,0.00001\r\n', b'  "VOLT 20,1e-5"  \r\n']:
            with self.subTest(raw=raw):
                self.assertTrue(self.lib.test_range(raw, len(raw)))

    def test_observed_200v_configuration_stops_before_read(self):
        # raw #09のCONF応答。前面20Vとの相違は未解決のため許容しない。
        raw = b'"VOLT +1.999999E+02,+1.000000E-05"\r\n'
        self.assertFalse(self.lib.test_range(raw, len(raw)))

    def test_reject_nan_inf_and_nul_in_range_fields(self):
        for field in [b'NaN', b'Inf', b'1e9999', b'20\x00junk', b'0x14']:
            for raw in [b'VOLT ' + field + b',1e-5\r\n',
                        b'VOLT 20,' + field + b'\r\n']:
                with self.subTest(raw=raw):
                    self.assertFalse(self.lib.test_range(raw, len(raw)))

    def test_reject_incomplete_extra_or_wrong_function_configuration(self):
        for raw in [b'VOLT 20,1e-5', b'VOLT 20,1e-5\n', b'VOLT 20',
                    b'VOLTAGE 20,1e-5\r\n', b'VOLT:AC 20,1e-5\r\n',
                    b'CURR 20,1e-5\r\n', b'"VOLT 20,1e-5\r\n',
                    b'VOLT 20,1e-5"\r\n', b'VOLT 20,1e-5,extra\r\n',
                    b'VOLT 20,1e-5\r\nVOLT 20,1e-5\r\n', b'VOLT 20,0\r\n',
                    b'VOLT 20,-1e-5\r\n', b'"VOLT 20,1e-5"junk\r\n']:
            with self.subTest(raw=raw):
                self.assertFalse(self.lib.test_range(raw, len(raw)))

    def test_preserve_existing_evaluation_gate_boundaries(self):
        for value, expected in [(18.999, False), (19, True), (20, True),
                                (21, True), (21.001, False), (200, False)]:
            raw = ('VOLT %s,1e-5\r\n' % value).encode('ascii')
            with self.subTest(raw=raw):
                self.assertEqual(bool(self.lib.test_range(raw, len(raw))), expected)


if __name__ == '__main__':
    unittest.main()
