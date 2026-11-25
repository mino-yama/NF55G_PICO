"""実C受信serviceとengineで、FIFO既着データと次要求の境界を検証する。"""
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from src.external_instrument_contract import encode_frame, decode_frame

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'firmware/usb_submcu_external_meter_host'

WRAPPER = r'''
#include "relay_host.h"
#include "relay_cdc_rx.h"
#include "tusb.h"
#include <string.h>
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API
#endif
static relay_host_t host;
static uint8_t fifo[CFG_TUH_CDC_RX_BUFSIZE];
static uint32_t used, reads;
static uint8_t output[8][X1_FRAME_MAX];
static size_t sizes[8], emitted;
static bool emit(void *ctx, const x1_frame_t *frame) {
    (void)ctx;
    if (emitted == 8) return false;
    sizes[emitted] = x1_encode(frame, output[emitted], X1_FRAME_MAX);
    emitted++;
    return true;
}
uint32_t tuh_cdc_read_available(uint8_t index) { (void)index; return used; }
uint32_t tuh_cdc_read(uint8_t index, void *buffer, uint32_t count) {
    (void)index;
    reads++;
    if (count > used) count = used;
    memcpy(buffer, fifo, count);
    used -= count;
    memmove(fifo, fifo + count, used);
    return count;
}
API void init(void) {
    relay_host_init(&host, (const uint8_t *)"HOSTNONC", "BFCF2EDB84B0B37F", "test", emit, NULL);
    host.ready = host.bound = true;
    memcpy(host.session, "PARENT01HOSTNONC", 16);
    used = reads = 0;
    emitted = 0;
}
API void request(const uint8_t *raw, size_t length) { relay_host_uart(&host, raw, length, 0); }
API void start(void) { relay_host_tx_started(&host); relay_host_tx_done(&host); }
API void feed(const uint8_t *raw, uint32_t count) { memcpy(fifo, raw, count); used = count; }
API void service(uint32_t now) { relay_cdc_rx_service(&host, 0, now); }
API uint32_t remaining(void) { return used; }
API uint32_t read_count(void) { return reads; }
API int fault(void) { return host.fault; }
API int pending(void) { return host.pending; }
API size_t pop(size_t index, uint8_t *out) {
    if (index >= emitted) return 0;
    memcpy(out, output[index], sizes[index]);
    return sizes[index];
}
'''


class MeterRxServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tcc = ROOT / 'tools/usb_submcu/host-test-tcc/tcc/tcc.exe'
        compiler = str(tcc) if os.name == 'nt' and tcc.exists() else shutil.which('cc')
        if not compiler:
            raise RuntimeError('Native C compiler required')
        cls.temp = tempfile.TemporaryDirectory(prefix='nf55g_rx_service_')
        folder = Path(cls.temp.name)
        # 実容量設定を使い、USB APIだけ決定的な既着FIFOへ置き換える。
        (folder / 'tusb.h').write_text(
            '#include <stdint.h>\n#include "' + (SOURCE / 'tusb_config.h').as_posix() + '"\n'
            'uint32_t tuh_cdc_read_available(uint8_t);\n'
            'uint32_t tuh_cdc_read(uint8_t, void *, uint32_t);\n', encoding='utf8')
        wrapper = folder / 'wrapper.c'
        wrapper.write_text(WRAPPER, encoding='ascii')
        library = folder / ('rx.dll' if os.name == 'nt' else 'rx.so')
        args = [compiler, '-shared', '-I', str(folder), '-I', str(SOURCE),
                str(SOURCE / 'relay_cdc_rx.c'), str(SOURCE / 'relay_host.c'),
                str(SOURCE / 'relay_wire.c'), str(wrapper), '-o', str(library)]
        if os.name != 'nt':
            args.insert(2, '-fPIC')
        subprocess.run(args, check=True, capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.request.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.feed.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        cls.lib.service.argtypes = [ctypes.c_uint32]
        cls.lib.pop.argtypes = [ctypes.c_size_t, ctypes.c_void_p]
        cls.lib.pop.restype = ctypes.c_size_t

    @classmethod
    def tearDownClass(cls):
        if os.name == 'nt':
            import _ctypes
            _ctypes.FreeLibrary(cls.lib._handle)
        cls.lib = None
        cls.temp.cleanup()

    def setUp(self):
        self.lib.init()

    def request(self, number=1):
        raw = encode_frame(b'PARENT01HOSTNONC', number, 'Q', 1, 1000, b':READ?')
        self.lib.request(raw, len(raw))

    def feed(self, raw, now=1):
        self.assertLessEqual(len(raw), 256)
        self.lib.feed(raw, len(raw))
        self.lib.service(now)

    def frames(self):
        output = ctypes.create_string_buffer(512)
        frames = []
        for index in range(8):
            count = self.lib.pop(index, output)
            if not count:
                break
            frames.append(decode_frame(output.raw[:count]))
        return frames

    def test_complete_response_and_queued_extra_never_emit_success(self):
        for boundary in (64, 128):
            with self.subTest(boundary=boundary):
                self.lib.init()
                self.request()
                self.lib.start()
                self.feed(b'1' * (boundary - 2) + b'\r\nX')
                self.assertEqual(self.lib.remaining(), 0)
                self.assertTrue(self.lib.fault())
                self.assertNotIn('R', [f['kind'] for f in self.frames()])
                self.assertEqual(self.frames()[-1]['payload'], b'EXTRA_DATA|1')
                self.request(2)
                self.assertFalse(self.lib.pending())
                self.assertEqual(self.frames()[-1]['payload'], b'RECOVERY_REQUIRED|0')

    def test_all_response_lengths_and_packet_splits_keep_original(self):
        for length in range(2, 193):
            for split in {0, min(64, length), min(128, length)}:
                self.lib.init()
                self.request()
                self.lib.start()
                raw = b'7' * (length - 2) + b'\r\n'
                self.feed(raw[:split])
                self.feed(raw[split:])
                self.assertFalse(self.lib.fault(), (length, split))
                self.assertFalse(self.lib.pending(), (length, split))
                self.assertEqual(self.frames()[-1]['payload'], raw)
                self.assertEqual(self.lib.remaining(), 0)

    def test_full_fifo_overlong_response_fails_without_truncation(self):
        self.request()
        self.lib.start()
        self.feed(b'8' * 254 + b'\r\n')
        self.assertTrue(self.lib.fault())
        self.assertEqual(self.lib.remaining(), 0)
        self.assertEqual(self.frames()[-1]['payload'], b'RESPONSE_TOO_LONG|1')

    def test_unsolicited_fifo_is_checked_before_next_request(self):
        self.feed(b'9' * 128)
        self.request()
        self.assertTrue(self.lib.fault())
        self.assertFalse(self.lib.pending())
        self.assertEqual(self.lib.remaining(), 0)
        self.assertEqual(self.frames()[-1]['payload'], b'RECOVERY_REQUIRED|0')

    def test_empty_fifo_does_not_rearm_usb(self):
        self.lib.service(1)
        self.assertEqual(self.lib.read_count(), 0)
        self.assertFalse(self.lib.fault())

    def test_deadline_keeps_ambiguous_and_does_not_return_partial(self):
        self.request()
        self.lib.start()
        self.feed(b'123\r\n', now=1000)
        self.assertTrue(self.lib.fault())
        self.assertEqual([f['kind'] for f in self.frames()], ['A', 'T', 'E'])
        self.assertTrue(self.frames()[-1]['payload'].startswith(b'TIMEOUT_RX0_'))
