"""固定SDKの実TinyUSB FIFOでCDC確保量・累積応答・wrap時の境界を検証する。"""
import ctypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'firmware/usb_submcu_external_meter_host'
TINYUSB = ROOT / 'tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src'


class MeterCdcFifoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 実cdc_host.cが配列に使うmacroを取得し、設定との不一致を見逃さない。
        vendor = (TINYUSB / 'class/cdc/cdc_host.c').read_text(encoding='utf8')
        allocated_macro = re.search(r'uint8_t\s+rx_ff_buf\[(\w+)\]', vendor).group(1)
        if not re.search(r'p_cdc->stream\.rx_ff_buf,\s*CFG_TUH_CDC_RX_BUFSIZE', vendor):
            raise RuntimeError('Review changed vendor CDC FIFO initialization')
        tcc = ROOT / 'tools/usb_submcu/host-test-tcc/tcc/tcc.exe'
        compiler = str(tcc) if os.name == 'nt' and tcc.exists() else shutil.which('cc')
        if not compiler:
            raise RuntimeError('Native C compiler required for CDC FIFO tests')
        cls.temp = tempfile.TemporaryDirectory(prefix='nf55g_cdc_fifo_')
        directory = Path(cls.temp.name)
        # 実製品の容量設定を使い、OS/MCUだけnative向けへ置換。SDK sourceは変更しない。
        config = '#include "' + (SOURCE / 'tusb_config.h').as_posix() + '"\n'
        config += '''
#undef CFG_TUSB_OS
#define CFG_TUSB_OS OPT_OS_NONE
#undef CFG_TUSB_MCU
#define CFG_TUSB_MCU OPT_MCU_NONE
#undef CFG_TUH_ENABLED
#define CFG_TUH_ENABLED 0
#define CFG_TUD_ENABLED 0
'''
        (directory / 'tusb_config.h').write_text(config, encoding='utf8')
        wrapper = directory / 'wrapper.c'
        code = '''#include "osal/osal.h"
#include "common/tusb_fifo.h"
#include <string.h>
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API
#endif
#define VENDOR_RX_CAPACITY ALLOCATION_MACRO
/* 隣接領域を安全な同一配列内canaryとして用意し、宣言配列境界への侵入を検出する。 */
static unsigned char memory[CFG_TUH_CDC_RX_BUFSIZE + 64];
static tu_fifo_t fifo;
API unsigned int test_allocated(void) { return VENDOR_RX_CAPACITY; }
API unsigned int test_depth(void) { return CFG_TUH_CDC_RX_BUFSIZE; }
API int test_reset(void) {
    memset(memory, 0xa5, sizeof(memory));
    memset(&fifo, 0, sizeof(fifo));
    return tu_fifo_config(&fifo, memory, CFG_TUH_CDC_RX_BUFSIZE, 1, false);
}
API unsigned int test_roundtrip(const unsigned char *input, unsigned int length, unsigned char *output) {
    unsigned int written = tu_fifo_write_n(&fifo, input, (uint16_t)length);
    if (written != length) return 0;
    return tu_fifo_read_n(&fifo, output, (uint16_t)length);
}
API int test_guard(void) {
    for (unsigned int i=VENDOR_RX_CAPACITY; i<sizeof(memory); i++)
        if (memory[i] != 0xa5) return 0;
    return 1;
}
'''.replace('ALLOCATION_MACRO', allocated_macro)
        wrapper.write_text(code, encoding='utf8')
        library = directory / ('fifo.dll' if os.name == 'nt' else 'fifo.so')
        command = [compiler, '-shared', '-I', str(directory), '-I', str(TINYUSB),
                   str(TINYUSB / 'common/tusb_fifo.c'), str(wrapper), '-o', str(library)]
        if compiler == str(tcc):
            # TCCのGCC互換attributeをTinyUSBへ明示する（native試験のみ）。
            command[2:2] = ['-D__GNUC__=4', '-D__GNUC_MINOR__=8',
                            '-D__BYTE_ORDER__=1234', '-D__ORDER_LITTLE_ENDIAN__=1234']
        if os.name != 'nt':
            command.insert(2, '-fPIC')
        proc = subprocess.run(command, capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError(proc.stdout + proc.stderr)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.test_allocated.restype = ctypes.c_uint
        cls.lib.test_depth.restype = ctypes.c_uint
        cls.lib.test_roundtrip.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p]
        cls.lib.test_roundtrip.restype = ctypes.c_uint

    @classmethod
    def tearDownClass(cls):
        if os.name == 'nt':
            import _ctypes
            _ctypes.FreeLibrary(cls.lib._handle)
        cls.lib = None
        cls.temp.cleanup()

    def setUp(self):
        self.assertTrue(self.lib.test_reset())

    def exchange(self, raw):
        output = ctypes.create_string_buffer(len(raw))
        self.assertEqual(self.lib.test_roundtrip(raw, len(raw), output), len(raw))
        self.assertEqual(output.raw, raw)
        self.assertTrue(self.lib.test_guard(), 'CDC FIFO wrote past its vendor-declared array')

    def test_configured_depth_fits_actual_vendor_array(self):
        self.assertLessEqual(self.lib.test_depth(), self.lib.test_allocated())

    def test_cumulative_instrument_responses_preserve_neighbor_memory(self):
        # 1応答が64byte未満でも、read後のFIFO indexは進み続ける。
        responses = [b'ADC Corp.,7355,246410099,  A02\r\n', b'0\r\n', b'1\r\n',
                     b'"VOLT:DC"\r\n', b'0\r\n',
                     b'"VOLT +1.999999E+02,+1.000000E-05"\r\n', b'+0,"No error"\r\n']
        for cycle in range(40):
            for raw in responses:
                with self.subTest(cycle=cycle, response=raw):
                    self.exchange(raw)

    def test_maximum_response_across_every_fifo_wrap_offset(self):
        response = bytes(range(190)) + b'\r\n'
        for offset in range(self.lib.test_depth()):
            with self.subTest(offset=offset):
                self.assertTrue(self.lib.test_reset())
                if offset:
                    self.exchange(b'P' * offset)
                for start in range(0, len(response), 64):
                    self.exchange(response[start:start+64])
