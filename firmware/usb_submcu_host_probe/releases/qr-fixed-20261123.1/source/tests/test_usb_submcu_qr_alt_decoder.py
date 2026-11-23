"""FWと同じCデコーダをnative DLLへコンパイルし、実機HIDと異常系を再生する。"""
import ctypes
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT/'tests/fixtures/usb_submcu_qr_alt'
EXPECTED = 'AbC-'+'0'*25+'123456'


def reports_for(text, terminate=True):
    result=[]
    for char in text:
        for digit in f'{ord(char):05d}':
            key=0x62 if digit=='0' else 0x58+int(digit)
            result.extend([bytes([4,0,key,0,0,0,0,0]),bytes([4,0,0,0,0,0,0,0])])
        result.append(bytes(8))
    if terminate:
        result.extend([bytes([0,0,0x28,0,0,0,0,0]),bytes(8)])
    return result


class NativeQRDecoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tcc=ROOT/'tools/usb_submcu/host-test-tcc/tcc/tcc.exe'
        compiler=str(tcc) if os.name=='nt' and tcc.exists() else shutil.which('cc') or shutil.which('gcc')
        if not compiler:
            raise unittest.SkipTest('Native C compiler required for actual firmware decoder tests')
        cls.temp=tempfile.TemporaryDirectory(prefix='nf55g_qr_decoder_')
        directory=Path(cls.temp.name)
        wrapper=directory/'wrapper.c'
        wrapper.write_text('''#include "qr_alt_decoder.h"
#ifdef _WIN32
#define TEST_API __declspec(dllexport)
#else
#define TEST_API
#endif
TEST_API size_t qr_test_size(void) { return sizeof(qr_alt_decoder_t); }
TEST_API int qr_test_error(qr_alt_decoder_t *s) { return s->error; }
''',encoding='ascii')
        library=directory/('decoder.dll' if os.name=='nt' else 'decoder.so')
        source=ROOT/'firmware/usb_submcu_host_probe'
        command=[compiler,'-shared','-DQR_ALT_TEST_DLL','-I',str(source),str(source/'qr_alt_decoder.c'),str(wrapper),'-o',str(library)]
        if os.name!='nt':command.insert(2,'-fPIC')
        subprocess.run(command,check=True,capture_output=True,text=True)
        cls.lib=ctypes.CDLL(str(library))
        cls.lib.qr_test_size.restype=ctypes.c_size_t
        cls.lib.qr_test_error.argtypes=[ctypes.c_void_p]
        cls.lib.qr_alt_decoder_init.argtypes=[ctypes.c_void_p]
        cls.lib.qr_alt_decoder_feed.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_void_p]
        cls.lib.qr_alt_decoder_poll.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
        cls.lib.qr_alt_profile_supported.argtypes=[ctypes.c_uint16,ctypes.c_uint16,ctypes.c_void_p,ctypes.c_size_t]
        cls.lib.qr_alt_profile_supported.restype=ctypes.c_bool

    @classmethod
    def tearDownClass(cls):
        if os.name=='nt':
            import _ctypes
            _ctypes.FreeLibrary(cls.lib._handle)
        cls.lib=None
        cls.temp.cleanup()

    def setUp(self):
        self.state=ctypes.create_string_buffer(self.lib.qr_test_size())
        self.lib.qr_alt_decoder_init(self.state)
        self.now=0

    def feed(self, report, when=None):
        when=self.now if when is None else when
        raw=ctypes.create_string_buffer(report)
        output=ctypes.create_string_buffer(36)
        result=self.lib.qr_alt_decoder_feed(self.state,raw,len(report),when&0xffffffff,output)
        self.now=when+3
        return result,output.value.decode('ascii') if result==1 else None

    def replay(self, reports):
        return [result for report in reports if (result:=self.feed(report))[0]]

    def assert_scan(self, text=EXPECTED):
        self.assertEqual(self.replay(reports_for(text)),[(1,text)])

    def replay_fixture(self, name):
        raw=(FIXTURES/name).read_bytes()
        results=[]
        for when,report in struct.iter_unpack('<I8s',raw):
            result=self.feed(report,when)
            if result[0]:results.append(result)
        self.assertEqual(results,[(1,EXPECTED)])

    def test_physical_orientation_a(self):self.replay_fixture('orientation_a.bin')
    def test_physical_orientation_b(self):self.replay_fixture('orientation_b.bin')

    def test_preserve_case_zero_and_hyphen(self):self.assert_scan('Az09-'*7)

    def test_actual_label_revision_period_and_next_scan(self):
        self.assert_scan('US250A-CGXE-009491-101A1.2601000001')
        self.assert_scan('US250A-CGXE-009491-101B2.2601000010')

    def test_period_outside_revision_is_rejected_without_partial_publication(self):
        for index in (0,8,21,25,29,34):
            self.setUp()
            raw=EXPECTED[:index]+'.'+EXPECTED[index+1:]
            self.assertEqual(self.replay(reports_for(raw)),[(2,None)])
            self.assertEqual(self.lib.qr_test_error(self.state),7)
            self.assert_scan()

    def test_repeated_held_reports_do_not_duplicate(self):
        source=reports_for(EXPECTED)
        self.assertEqual(self.replay([r for r in source for _ in range(2)]),[(1,EXPECTED)])

    def test_two_consecutive_scans_are_separate(self):
        self.assertEqual(self.replay(reports_for(EXPECTED)+reports_for('Z9-0a'*7)),[(1,EXPECTED),(1,'Z9-0a'*7)])

    def test_missing_enter_never_publishes(self):
        self.assertEqual(self.replay(reports_for(EXPECTED,False)),[])
        self.assertEqual(self.lib.qr_alt_decoder_poll(self.state,self.now+5001),2)
        self.assertEqual(self.lib.qr_test_error(self.state),9)
        self.now+=5002
        self.replay(reports_for(''))  # 異常試行の終端を消費する。
        self.assert_scan()

    def test_short_scan_rejected_and_next_scan_recovers(self):
        self.assertEqual(self.replay(reports_for('A'*34)),[(2,None)])
        self.assertEqual(self.lib.qr_test_error(self.state),8)
        self.assert_scan()

    def test_long_scan_rejected_without_partial_publication(self):
        self.assertEqual(self.replay(reports_for('A'*36)),[(2,None)])
        self.assert_scan()

    def test_disallowed_character_discards_until_enter(self):
        self.assertEqual(self.replay(reports_for('A'*10+' '+'B'*24)),[(2,None)])
        self.assert_scan()

    def test_malformed_hid_does_not_publish_or_contaminate_next(self):
        invalid=[b'bad',bytes([4,1,0,0,0,0,0,0]),bytes([2,0,4,0,0,0,0,0]),
                 bytes([4,0,0x59,0x5a,0,0,0,0]),bytes([4,0,1,0,0,0,0,0]),
                 bytes([0,0,4,0,0,0,0,0])]
        for raw in invalid:
            with self.subTest(raw=raw):
                self.setUp()
                self.assertEqual(self.feed(raw)[0],2)
                self.replay(reports_for(''))
                self.assert_scan()

    def test_incomplete_alt_digits_rejected(self):
        source=reports_for('A')[:8]+[bytes(8)]
        self.assertEqual(self.replay(source),[(2,None)])
        self.replay(reports_for(''));self.assert_scan()

    def test_more_than_five_alt_digits_rejected(self):
        source=[bytes([4,0,0x62,0,0,0,0,0]),bytes([4,0,0,0,0,0,0,0])]*6
        self.assertEqual(self.replay(source),[(2,None)])
        self.replay(reports_for(''));self.assert_scan()

    def test_timeout_boundary_and_duplicate_reports(self):
        raw=bytes([4,0,0x62,0,0,0,0,0])
        self.assertEqual(self.feed(raw,0)[0],0)
        self.assertEqual(self.feed(raw,4999)[0],0)
        self.assertEqual(self.lib.qr_alt_decoder_poll(self.state,5000),0)
        self.assertEqual(self.lib.qr_alt_decoder_poll(self.state,5001),2)
        self.assertEqual(self.lib.qr_alt_decoder_poll(self.state,15000),0)

    def test_timeout_handles_tick_wrap(self):
        start=0xfffffff0
        self.feed(bytes([4,0,0x62,0,0,0,0,0]),start)
        self.assertEqual(self.lib.qr_alt_decoder_poll(self.state,(start+5001)&0xffffffff),2)

    def test_reset_discards_partial_scan(self):
        self.assertEqual(self.replay(reports_for('A'*12,False)),[])
        self.lib.qr_alt_decoder_init(self.state)
        self.assert_scan()

    def test_exact_device_and_descriptor_required(self):
        descriptor=bytes.fromhex(json.loads((FIXTURES/'manifest.json').read_text(encoding='utf8'))['descriptor_hex'])
        raw=ctypes.create_string_buffer(descriptor)
        self.assertTrue(self.lib.qr_alt_profile_supported(0xe851,0x1001,raw,len(descriptor)))
        self.assertFalse(self.lib.qr_alt_profile_supported(0xe851,0x1002,raw,len(descriptor)))
        self.assertFalse(self.lib.qr_alt_profile_supported(0xe851,0x1001,raw,len(descriptor)-1))
        changed=ctypes.create_string_buffer(bytes([descriptor[0]^1])+descriptor[1:])
        self.assertFalse(self.lib.qr_alt_profile_supported(0xe851,0x1001,changed,len(descriptor)))


if __name__=='__main__':unittest.main()
