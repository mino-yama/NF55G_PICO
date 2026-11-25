"""親Python adapterと実Host C engineを接続し、同じX1フレームで縦通しを検証する。"""
import ctypes
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from src.external_instrument_contract import encode_frame, decode_frame, parse_monitor_request
from src.external_instrument_link import ExternalInstrumentLink, FrameReader
from src.external_instrument_relay import RelayError
from src.frame import build_frame
from src.mock_nf55g import FakeClock, MockNF55GScenario, MockUART, ScenarioStep
from src.main import FixtureApp
from src.nf55_protocol import NF55Protocol

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'firmware/usb_submcu_external_meter_host'

WRAPPER = r'''#include "relay_host.h"
#include "relay_cdc_guard.h"
#include "relay_usb_diag.h"
#include "tusb.h"
#include <string.h>
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API
#endif
typedef struct {
    relay_host_t host;
    unsigned char output[8][X1_FRAME_MAX];
    size_t lengths[8], head, tail, count;
} test_t;
static unsigned int real_cdc_calls;
bool __real_cdch_xfer_cb(uint8_t address, uint8_t endpoint, xfer_result_t result, uint32_t count) {
    (void)address; (void)endpoint; (void)result; (void)count;
    real_cdc_calls++;
    return true;
}
bool __wrap_cdch_xfer_cb(uint8_t, uint8_t, xfer_result_t, uint32_t);
API int test_cdc_xfer(unsigned int address, unsigned int endpoint, unsigned int result) {
    return __wrap_cdch_xfer_cb((uint8_t)address, (uint8_t)endpoint, (xfer_result_t)result, 0);
}
API unsigned int test_cdc_real_calls(void) { return real_cdc_calls; }
API void test_cdc_unbind(void) { relay_cdc_guard_bind(NULL, 0); }
static bool emit(void *context, const x1_frame_t *frame) {
    test_t *test = (test_t *)context;
    if (test->count == 8) return false;
    size_t size = x1_encode(frame, test->output[test->head], X1_FRAME_MAX);
    if (!size) return false;
    test->lengths[test->head] = size;
    test->head = (test->head+1)%8;
    test->count++;
    return true;
}
API size_t test_chunk(size_t remaining) { return relay_usb_chunk_size(remaining); }
API size_t test_size(void) { return sizeof(test_t); }
API void test_init(test_t *test, const unsigned char *nonce) {
    memset(test,0,sizeof(*test));
    relay_host_init(&test->host, nonce, "BFCF2EDB84B0B37F", "meter-host-relay-20261123.1", emit, test);
    relay_cdc_guard_bind(&test->host, 3);
    real_cdc_calls = 0;
}
API void test_ready(test_t *test, int ready) { relay_host_device_ready(&test->host, ready != 0); }
API void test_uart(test_t *test, const unsigned char *bytes, size_t size, unsigned int now) {
    relay_host_uart(&test->host, bytes,size,now);
}
API void test_poll(test_t *test, unsigned int now) { relay_host_poll(&test->host,now); }
API void test_start(test_t *test) { relay_host_tx_started(&test->host); }
API void test_done(test_t *test) { relay_host_tx_done(&test->host); }
API void test_rx(test_t *test, const unsigned char *bytes, size_t size, unsigned int now) {
    relay_host_rx(&test->host,bytes,size,now);
}
API int test_pending(test_t *test) { return test->host.pending; }
API void test_set_pending(test_t *test) {
    test->host.pending = true;
    test->host.started_at = 0;
    test->host.request.timeout_ms = 1000;
}
API int test_fault(test_t *test) { return test->host.fault; }
API void test_fail(test_t *test) { relay_host_fail(&test->host, "TEST_FAULT"); }
API void test_reset_ack_sent(test_t *test) { relay_host_reset_ack_transmitted(&test->host); }
API int test_reset_due(test_t *test) { return relay_host_reset_due(&test->host); }
API int test_take_reset(test_t *test) { return relay_host_take_reset(&test->host); }
API size_t test_command(test_t *test, unsigned char *out) {
    memcpy(out,test->host.command,test->host.command_length);
    return test->host.command_length;
}
API size_t test_pop(test_t *test, unsigned char *out) {
    if (!test->count) return 0;
    size_t size=test->lengths[test->tail];
    memcpy(out,test->output[test->tail],size);
    test->tail=(test->tail+1)%8;
    test->count--;
    return size;
}
API size_t test_recode(const unsigned char *bytes, size_t size, unsigned char *out) {
    x1_frame_t frame;
    return x1_decode(bytes,size,&frame) ? x1_encode(&frame,out,X1_FRAME_MAX) : 0;
}
API size_t test_usb_diag(const unsigned char *bytes, size_t size, unsigned char *out) {
    x1_frame_t frame;
    if (!x1_decode(bytes,size,&frame)) return 0;
    relay_usb_snapshot_t snapshot = {2000,1998,2,0x80,0xD2,0x81,1,0,0,64,2,3,0,0xD2,0x02};
    relay_usb_diag_decorate(&frame, &snapshot);
    return x1_encode(&frame,out,X1_FRAME_MAX);
}
'''


class NativeHostTransport:
    def __init__(self, lib, clock, ready=True, write_limit=64):
        self.lib, self.clock = lib, clock
        self.memory = ctypes.create_string_buffer(lib.test_size())
        lib.test_init(self.memory, b'HOSTNONC')
        lib.test_ready(self.memory, ready)
        self.rx = bytearray()
        self.commands = []
        self.responses = [b'ADC Corp.,7355,246410099,  A02\r\n']
        self.auto_device = True
        self.write_limit = write_limit
        self.drop_replies = False
        self.drop_kinds = set()
        self.auto_ack_transmission = False
        self.reboot_on_reset_ack = False
        self.last_request = 0
        self.frame_reader = FrameReader()
        self.output_reader = FrameReader()

    def drain(self):
        out = ctypes.create_string_buffer(512)
        while (size := self.lib.test_pop(self.memory, out)):
            raw = out.raw[:size]
            frames = self.output_reader.feed(raw)
            if self.auto_ack_transmission and any(frame['kind'] == 'K' for frame in frames):
                self.lib.test_reset_ack_sent(self.memory)
                self.lib.test_poll(self.memory, self.clock.ticks_ms())
                if self.reboot_on_reset_ack and self.lib.test_reset_due(self.memory):
                    self.lib.test_init(self.memory, b'NEWHOST1')
                    self.lib.test_ready(self.memory, 1)
            if not self.drop_replies and not any(frame['kind'] in self.drop_kinds for frame in frames):
                self.rx.extend(raw)

    def any(self):
        self.drain()
        return len(self.rx)

    def read(self, size):
        self.drain()
        raw = bytes(self.rx[:size])
        del self.rx[:size]
        return raw

    def write(self, data):
        data = data[:self.write_limit]
        self.lib.test_uart(self.memory, data, len(data), self.clock.ticks_ms())
        self.service_device()
        return len(data)

    def service_device(self):
        if not self.auto_device or not self.lib.test_pending(self.memory):
            return
        output = ctypes.create_string_buffer(194)
        size = self.lib.test_command(self.memory, output)
        command = output.raw[:size]
        self.commands.append(command)
        self.lib.test_start(self.memory)
        self.lib.test_done(self.memory)
        if self.lib.test_pending(self.memory) and self.responses:
            response = self.responses.pop(0)
            self.lib.test_rx(self.memory, response, len(response), self.clock.ticks_ms())


class NativeRelayLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tcc = ROOT / 'tools/usb_submcu/host-test-tcc/tcc/tcc.exe'
        compiler = str(tcc) if os.name == 'nt' and tcc.exists() else shutil.which('cc')
        if not compiler:
            raise RuntimeError('Native C compiler required for relay Host tests')
        cls.temp = tempfile.TemporaryDirectory(prefix='nf55g_relay_link_')
        folder = Path(cls.temp.name)
        wrapper = folder / 'wrapper.c'
        wrapper.write_text(WRAPPER, encoding='ascii')
        # guard自体は実Cを検証し、SDK型だけをnative ABI用に最小stub化する。
        (folder / 'tusb.h').write_text(
            '#include <stdbool.h>\n#include <stdint.h>\n#include <stddef.h>\n'
            'typedef enum { XFER_RESULT_SUCCESS=0, XFER_RESULT_FAILED=1, '
            'XFER_RESULT_STALLED=2, XFER_RESULT_TIMEOUT=3 } xfer_result_t;\n', encoding='ascii')
        library = folder / ('relay.dll' if os.name == 'nt' else 'relay.so')
        args = [compiler, '-shared', '-I', str(folder), '-I', str(SOURCE), str(SOURCE/'relay_host.c'),
                str(SOURCE/'relay_wire.c'), str(SOURCE/'relay_cdc_guard.c'), str(SOURCE/'relay_usb_diag.c'), str(wrapper), '-o', str(library)]
        if os.name != 'nt':
            args.insert(2, '-fPIC')
        subprocess.run(args, check=True, capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.test_size.restype = ctypes.c_size_t
        cls.lib.test_chunk.argtypes = [ctypes.c_size_t]
        cls.lib.test_chunk.restype = ctypes.c_size_t
        for name in ('test_init',):
            getattr(cls.lib, name).argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        cls.lib.test_ready.argtypes = [ctypes.c_void_p, ctypes.c_int]
        for name in ('test_uart', 'test_rx'):
            getattr(cls.lib, name).argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
        cls.lib.test_poll.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        for name in ('test_start', 'test_done', 'test_pending', 'test_fault'):
            getattr(cls.lib, name).argtypes = [ctypes.c_void_p]
        for name in ('test_set_pending', 'test_fail', 'test_reset_ack_sent', 'test_reset_due', 'test_take_reset'):
            getattr(cls.lib, name).argtypes = [ctypes.c_void_p]
        for name in ('test_command', 'test_pop'):
            getattr(cls.lib, name).argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            getattr(cls.lib, name).restype = ctypes.c_size_t
        cls.lib.test_recode.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
        cls.lib.test_recode.restype = ctypes.c_size_t
        cls.lib.test_usb_diag.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
        cls.lib.test_usb_diag.restype = ctypes.c_size_t
        cls.lib.test_cdc_xfer.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
        cls.lib.test_cdc_xfer.restype = ctypes.c_int
        cls.lib.test_cdc_real_calls.restype = ctypes.c_uint

    @classmethod
    def tearDownClass(cls):
        if os.name == 'nt':
            import _ctypes
            _ctypes.FreeLibrary(cls.lib._handle)
        cls.lib = None
        cls.temp.cleanup()

    def setUp(self):
        self.clock = FakeClock()
        self.transport = NativeHostTransport(self.lib, self.clock)
        self.link = ExternalInstrumentLink(self.transport, self.clock, b'PARENT01', 'BFCF2EDB84B0B37F')

    def request(self, line=b'EXT_QUERY 2000 *IDN?'):
        self.link.start(parse_monitor_request(line))
        for _ in range(1000):
            self.link.poll()
            reply = self.link.take_reply()
            if reply is not None:
                return reply
            self.clock.sleep_ms(1)
        self.fail('No bounded response')

    def test_host_recovers_power_on_capture_at_every_split(self):
        # 試行8の実原文。起動時00 00がCRLFなしで正常Hの直前に入る。
        captured = bytes.fromhex(
            '00004058312C4341303033394141364631364535324430303030303030303030303030303030'
            '2C30303030303030302C482C302C30303030303030302C303030302C2C39453745394233440D0A')
        parent = decode_frame(captured[2:])
        for split in range(len(captured) + 1):
            with self.subTest(split=split):
                transport = NativeHostTransport(self.lib, self.clock, ready=False)
                for part in (captured[:split], captured[split:]):
                    self.lib.test_uart(transport.memory, part, len(part), 0)
                transport.drain()
                reply = decode_frame(bytes(transport.rx))
                self.assertEqual(reply['kind'], 'h')
                self.assertEqual(reply['session'][:8], parent['session'][:8])
                self.assertTrue(reply['payload'].endswith(b'|NOT_READY'))
                self.assertFalse(self.lib.test_pending(transport.memory))
                self.assertFalse(self.lib.test_fault(transport.memory))
                self.assertEqual(transport.commands, [])

    def test_power_on_bytes_do_not_block_parent_query(self):
        self.lib.test_uart(self.transport.memory, b'\x00\x00', 2, 0)
        reply = self.request()
        self.assertTrue(reply.startswith('OK:EXT_RX:32:'))
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n'])

    def test_error_valued_read_response_does_not_block_next_explicit_read(self):
        error_value = b'+9.999999E+37\r\n'
        next_value = b'+0040.154E-03\r\n'
        self.transport.responses = [error_value, next_value]

        first = self.request(b'EXT_QUERY 10000 :READ?')
        self.assertTrue(first.startswith('OK:EXT_RX:'))
        _, _, length, encoded = first.split(':', 3)
        first_raw = bytes.fromhex(encoded)
        self.assertEqual(int(length), len(error_value))
        self.assertEqual(first_raw, error_value)
        self.assertFalse(self.lib.test_fault(self.transport.memory))

        second = self.request(b'EXT_QUERY 10000 :READ?')
        self.assertTrue(second.startswith('OK:EXT_RX:'))
        _, _, length, encoded = second.split(':', 3)
        second_raw = bytes.fromhex(encoded)
        self.assertEqual(int(length), len(next_value))
        self.assertEqual(second_raw, next_value)
        self.assertEqual(self.transport.commands, [b':READ?\r\n', b':READ?\r\n'])
        self.assertFalse(self.lib.test_fault(self.transport.memory))

    def test_host_finds_header_after_noise_truncation_and_overflow(self):
        hello = encode_frame(b'PARENT01' + bytes(8), 0, 'H', 0, 0, b'')
        for prefix in (b'noise', b'\x00'*600, b'@X1,incomplete',
                       b'@' + b'A'*512, b'noise\r\n@X1,partial'):
            with self.subTest(prefix=prefix[:20], length=len(prefix)):
                transport = NativeHostTransport(self.lib, self.clock, ready=False)
                raw = prefix + hello
                for start in range(0, len(raw), 4):
                    part = raw[start:start+4]
                    self.lib.test_uart(transport.memory, part, len(part), 0)
                transport.drain()
                self.assertEqual(decode_frame(bytes(transport.rx))['kind'], 'h')
                self.assertFalse(self.lib.test_pending(transport.memory))

    def test_resync_keeps_crc_session_and_replay_checks(self):
        def feed(raw):
            self.lib.test_uart(self.transport.memory, raw, len(raw), 0)
            self.transport.service_device()
            self.transport.drain()
            result = bytes(self.transport.rx)
            self.transport.rx.clear()
            return result

        session = b'PARENT01HOSTNONC'
        hello = encode_frame(session[:8]+bytes(8), 0, 'H', 0, 0, b'')
        self.assertEqual(decode_frame(feed(b'\x00\x00'+hello))['kind'], 'h')
        command = encode_frame(session, 1, 'Q', 1, 2000, b'*IDN?')
        bad_crc = command[:-10] + b'00000000\r\n'
        self.assertEqual(feed(b'noise'+bad_crc), b'')
        wrong_session = encode_frame(b'OTHER001HOSTNONC', 1, 'Q', 1, 2000, b'*IDN?')
        self.assertEqual(feed(b'noise'+wrong_session), b'')
        self.assertEqual(self.transport.commands, [])
        replies = feed(b'noise'+command)
        self.assertTrue(replies)
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n'])
        duplicate = decode_frame(feed(b'noise'+command))
        self.assertEqual(duplicate['kind'], 'E')
        self.assertEqual(duplicate['payload'], b'REPLAY_REQUEST|0')
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n'])

    def test_python_and_c_codec_agree_all_kinds_and_payload_lengths(self):
        for kind in ('H','h','Q','A','T','R','E','I','i','S','K'):
            for size in (0,1,63,64,191,192):
                wire = encode_frame(bytes(range(16)), 0xffffffff, kind, 1, 10000, bytes(range(size)))
                out = ctypes.create_string_buffer(512)
                length = self.lib.test_recode(wire,len(wire),out)
                self.assertEqual(out.raw[:length], wire)
                bad = wire[:-4] + b'AA' + wire[-2:]
                self.assertEqual(self.lib.test_recode(bad,len(bad),out),0)

    def test_management_info_is_available_in_fault_without_device_command(self):
        self.lib.test_fail(self.transport.memory)
        challenge = b'0123456789ABCDEF'
        payload = b'BFCF2EDB84B0B37F|' + challenge
        request = encode_frame(b'PARENT01' + bytes(8), 7, 'I', 0, 1000, payload)
        self.lib.test_uart(self.transport.memory, request, len(request), 10)
        reply = decode_frame(self.transport.read(512))
        self.assertEqual(reply['kind'], 'i')
        self.assertEqual(reply['request'], 7)
        self.assertEqual(reply['session'], b'PARENT01HOSTNONC')
        self.assertTrue(reply['payload'].endswith(b'|FAULT|' + challenge))
        self.assertEqual(self.transport.commands, [])

        self.lib.test_uart(self.transport.memory, request, len(request), 11)
        duplicate = decode_frame(self.transport.read(512))
        self.assertEqual(duplicate['kind'], 'E')
        self.assertEqual(duplicate['payload'], b'REPLAY_REQUEST|0')

    def test_management_reset_is_challenge_bound_and_waits_for_ack_transmission(self):
        challenge = b'0123456789ABCDEF'
        parent_session = b'PARENT01' + bytes(8)
        payload = b'BFCF2EDB84B0B37F|' + challenge
        info = encode_frame(parent_session, 7, 'I', 0, 1000, payload)
        self.lib.test_uart(self.transport.memory, info, len(info), 10)
        info_reply = decode_frame(self.transport.read(512))

        reset = encode_frame(info_reply['session'], 8, 'S', 0, 1000, payload)
        self.lib.test_uart(self.transport.memory, reset, len(reset), 20)
        ack = decode_frame(self.transport.read(512))
        self.assertEqual((ack['kind'], ack['payload']), ('K', b'RESET_ACCEPTED'))
        self.assertFalse(self.lib.test_reset_due(self.transport.memory))
        self.assertEqual(self.transport.commands, [])

        self.lib.test_reset_ack_sent(self.transport.memory)
        self.lib.test_poll(self.transport.memory, 21)
        self.assertTrue(self.lib.test_reset_due(self.transport.memory))

        self.lib.test_uart(self.transport.memory, reset, len(reset), 22)
        duplicate = decode_frame(self.transport.read(512))
        self.assertEqual(duplicate['kind'], 'E')
        self.assertEqual(duplicate['payload'], b'REPLAY_REQUEST|0')

        stale = NativeHostTransport(self.lib, self.clock)
        info = encode_frame(parent_session, 7, 'I', 0, 1000, payload)
        self.lib.test_uart(stale.memory, info, len(info), 10)
        stale_info = decode_frame(stale.read(512))
        wrong_reset = encode_frame(stale_info['session'], 9, 'S', 0, 1000, payload)
        self.lib.test_uart(stale.memory, wrong_reset, len(wrong_reset), 20)
        self.assertEqual(decode_frame(stale.read(512))['payload'], b'CHALLENGE_EXPIRED|0')
        valid_reset = encode_frame(stale_info['session'], 8, 'S', 0, 1000, payload)
        self.lib.test_uart(stale.memory, valid_reset, len(valid_reset), 21)
        self.assertEqual(decode_frame(stale.read(512))['payload'], b'REPLAY_REQUEST|0')

    def test_management_reset_timeout_and_pending_request_never_reboot(self):
        challenge = b'0123456789ABCDEF'
        payload = b'BFCF2EDB84B0B37F|' + challenge
        session = b'PARENT01' + bytes(8)
        info = encode_frame(session, 7, 'I', 0, 1000, payload)
        reset = encode_frame(b'PARENT01HOSTNONC', 8, 'S', 0, 1000, payload)

        self.lib.test_uart(self.transport.memory, info, len(info), 1)
        self.transport.read(512)
        self.lib.test_uart(self.transport.memory, reset, len(reset), 2)
        self.assertEqual(decode_frame(self.transport.read(512))['kind'], 'K')
        self.lib.test_poll(self.transport.memory, 1002)
        self.assertFalse(self.lib.test_reset_due(self.transport.memory))

        busy = NativeHostTransport(self.lib, self.clock)
        self.lib.test_set_pending(busy.memory)
        info = encode_frame(session, 7, 'I', 0, 1000, payload)
        self.lib.test_uart(busy.memory, info, len(info), 3)
        info_reply = decode_frame(busy.read(512))
        self.assertEqual(info_reply['kind'], 'i', repr(info_reply))
        self.assertTrue(info_reply['payload'].endswith(b'|BUSY|' + challenge), repr(info_reply))
        reset = encode_frame(b'PARENT01HOSTNONC', 8, 'S', 0, 1000, payload)
        self.lib.test_uart(busy.memory, reset, len(reset), 4)
        rejected = decode_frame(busy.read(512))
        self.assertEqual(rejected['kind'], 'E')
        self.assertEqual(rejected['payload'], b'BUSY|0')
        self.assertFalse(self.lib.test_reset_due(busy.memory))

    def test_ate_host_management_fault_reset_and_new_nonce_round_trip(self):
        self.lib.test_fail(self.transport.memory)
        app = FixtureApp(clock=self.clock, external_link=self.link)

        def run_management(command):
            self.assertIsNone(app.execute_ate_line(command))
            for _ in range(1000):
                app._service_external()
                reply = app.take_external_response()
                if reply is not None:
                    return reply
                self.clock.sleep_ms(1)
            self.fail('No bounded management response')

        info = run_management('HOST_INFO? METER')
        self.assertEqual(info, 'OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261123.1:484F53544E4F4E43:FAULT')
        self.transport.auto_ack_transmission = True
        self.transport.reboot_on_reset_ack = True
        reset = run_management('HOST_RESET METER')
        self.assertEqual(reset, 'OK:HOST_RESET_ACCEPTED:BFCF2EDB84B0B37F:484F53544E4F4E43')
        self.assertEqual(self.transport.commands, [])

        confirmed = run_management('HOST_INFO? METER')
        self.assertEqual(confirmed, 'OK:HOST_RESET_DONE:BFCF2EDB84B0B37F:484F53544E4F4E43:4E4557484F535431:READY')
        self.assertEqual(self.transport.commands, [])

    def run_management(self, operation):
        self.link.start_management(operation)
        for _ in range(1100):
            self.link.poll()
            reply = self.link.take_reply()
            if reply is not None:
                return reply
            self.clock.sleep_ms(1)
        self.fail('No bounded management response')

    def test_reset_confirmation_precedes_normal_query(self):
        self.transport.auto_ack_transmission = True
        self.transport.reboot_on_reset_ack = True
        self.assertTrue(self.run_management('RESET').startswith('OK:HOST_RESET_ACCEPTED:'))
        with self.assertRaisesRegex(RelayError, 'RECOVERY_REQUIRED'):
            self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
        self.assertEqual(self.transport.commands, [])

    def test_reset_dispatch_arms_watchdog_once_and_keeps_busy_until_reboot(self):
        self.assertFalse(self.lib.test_take_reset(self.transport.memory))
        self.assertTrue(self.run_management('RESET').startswith('OK:HOST_RESET_ACCEPTED:'))
        self.assertFalse(self.lib.test_take_reset(self.transport.memory))
        self.lib.test_reset_ack_sent(self.transport.memory)
        calls = 0
        for now in range(1000):
            self.lib.test_poll(self.transport.memory, self.clock.ticks_ms() + now)
            calls += bool(self.lib.test_take_reset(self.transport.memory))
        self.assertEqual(calls, 1)
        self.assertTrue(self.lib.test_reset_due(self.transport.memory))
        self.assertFalse(self.lib.test_take_reset(self.transport.memory))
        self.assertEqual(self.transport.commands, [])

    def test_reset_done_requires_normal_hello_before_explicit_query(self):
        self.transport.auto_ack_transmission = True
        self.transport.reboot_on_reset_ack = True
        self.assertTrue(self.run_management('RESET').startswith('OK:HOST_RESET_ACCEPTED:'))
        self.assertTrue(self.run_management('INFO').startswith('OK:HOST_RESET_DONE:'))
        self.assertEqual(self.transport.commands, [])
        self.assertTrue(self.request().startswith('OK:EXT_RX:32:'))
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n'])

    def test_reset_done_preserves_existing_parent_fault(self):
        self.link.fault = True
        self.transport.auto_ack_transmission = True
        self.transport.reboot_on_reset_ack = True
        self.assertTrue(self.run_management('RESET').startswith('OK:HOST_RESET_ACCEPTED:'))
        self.assertTrue(self.run_management('INFO').startswith('OK:HOST_RESET_DONE:'))
        with self.assertRaisesRegex(RelayError, 'RECOVERY_REQUIRED'):
            self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
        self.assertTrue(self.link.fault)
        self.assertEqual(self.transport.commands, [])

    def test_reset_ack_loss_is_result_unknown_and_latches_parent_fault(self):
        self.transport.drop_kinds.add('K')
        self.transport.auto_ack_transmission = True
        self.link.start_management('RESET')
        reply = None
        for _ in range(1100):
            self.link.poll()
            reply = self.link.take_reply()
            if reply is not None:
                break
            self.clock.sleep_ms(1)
        self.assertEqual(reply, 'ERR:HOST_RESULT_UNKNOWN')
        self.assertTrue(self.link.fault)
        self.assertIsNone(self.link.session)
        self.assertEqual(self.transport.commands, [])
        self.assertTrue(self.lib.test_reset_due(self.transport.memory))

    def calibration_app(self):
        nf = MockUART(clock=self.clock)
        app = FixtureApp(clock=self.clock, external_link=self.link, protocol=NF55Protocol(nf, clock=self.clock))
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        return app, nf

    def calibration_request(self, app, target='BATT_V', point='A'):
        self.assertIsNone(app.execute_ate_line('CAL_MEASURE {} {} 2000 :READ?'.format(target, point)))
        for _ in range(2200):
            app._service_external()
            reply = app.take_external_response()
            if reply is not None:
                return reply
            self.clock.sleep_ms(1)
        self.fail('No bounded calibration response')

    def test_calibration_native_all_targets_points_and_cache_only_queries(self):
        app, nf = self.calibration_app()
        for target in ('BATT_V', 'DISCHG_I', 'BATT_CHG'):
            for point in ('A', 'B'):
                self.transport.responses = [b'"VOLT:DC"\r\n', b'-001.8500E-03\r\n']
                reply = self.calibration_request(app, target, point)
                self.assertTrue(reply.startswith('OK:CAL_MEASURE:'), reply)
                token_id = reply.split(':', 2)[2]
                before = list(self.transport.commands)
                query = app.execute_ate_line('CAL_MEASUREMENT? ' + token_id)
                unit_fields = ':-001.8500E-03:V:-001.8500E-03:V:' if target == 'BATT_V' else ':-001.8500E+00:mV:-001.8500E+00:A:'
                self.assertIn(unit_fields, query)
                self.assertEqual(self.transport.commands, before)
        self.assertEqual(self.transport.commands, [b':SENS:FUNC?\r\n', b':READ?\r\n'] * 6)
        self.assertEqual(nf.tx_log, [])
        self.assertEqual(app.execute_ate_line('TEST_END'), 'OK')
        self.assertEqual(app.execute_ate_line('CAL_MEASUREMENT? ' + token_id), 'ERR:CAL_MEASUREMENT_INVALID')
        self.assertEqual(nf.tx_log, [])

    def test_named_calibration_workflow_from_ate_uart_through_six_points(self):
        points = (
            ('DISCHG_I', 'A', 'P2', '12', b'+044.2500E-03\r\n', 44.25),
            ('DISCHG_I', 'B', 'P1', '11', b'+000.3000E-03\r\n', 0.3),
            ('BATT_CHG', 'A', 'P2', '42', b'+001.8500E-03\r\n', 1.85),
            ('BATT_CHG', 'B', 'P1', '41', b'+000.5000E-03\r\n', 0.5),
            ('BATT_V', 'A', 'P2', '22', b'+08.12500E+00\r\n', 8.125),
            ('BATT_V', 'B', 'P1', '21', b'+05.25000E+00\r\n', 5.25),
        )
        manufacturing = b'S1.14BA1. 2601000001' + b'0' * 80
        scenario = MockNF55GScenario([ScenarioStep.ack_response('D5', manufacturing)])
        ate = MockUART(clock=self.clock)
        nf = MockUART(clock=self.clock, scenario=scenario)
        app = FixtureApp(ate_uart=ate, nf55_uart=nf, clock=self.clock, external_link=self.link,
                         calibration_sample_enabled=True)

        def exchange(command):
            start = len(ate.tx_log)
            ate.enqueue_rx(command.encode('ascii') + b'\r')
            for _ in range(2200):
                app.service_once()
                output = b''.join(ate.tx_log[start:])
                if output.endswith(b'\r'):
                    self.assertEqual(output.count(b'\r'), 1)
                    return output[:-1].decode('ascii')
                self.clock.sleep_ms(1)
            self.fail('No ATE response for ' + command)

        self.assertEqual(exchange('TEST_START'), 'OK')
        self.assertEqual(exchange('INFO_REFRESH'), 'OK')
        for circuit, point, destination, type_point, raw, value in points:
            with self.subTest(circuit=circuit, point=point):
                self.transport.responses = [b'"VOLT:DC"\r\n', raw]
                measured = exchange(f'CAL_MEASURE_{circuit} {point} 2000 :READ?')
                self.assertTrue(measured.startswith('OK:CAL_MEASURE:'), measured)
                token = measured.split(':')[-1]
                self.assertEqual(exchange(f'AD_VERIFY_{circuit} {destination}'), 'ERR:AD_VERIFY_NO_WRITE')
                instrument_requests = list(self.transport.commands)
                before = scenario.handled_command_count
                cached = exchange(f'CAL_MEASUREMENT_{circuit}? {point}')
                self.assertTrue(cached.startswith(f'OK:CAL_MEASUREMENT:{token}:{circuit}:{point}:'))
                self.assertEqual(cached.rsplit(':', 1)[-1], raw.hex().upper())
                self.assertEqual(scenario.handled_command_count, before)
                scenario.add(ScenarioStep.ack_response('AD', type_point.encode() + b'00012344A8699A'))
                value8 = struct.pack('>f', value).hex().upper()
                self.assertTrue(exchange(f'CAL_WRITE_{circuit} {point} {destination}').startswith(
                    f'OK:CAL_WRITE:{value8}:291:'))
                self.assertEqual(scenario.handled_command_count, before + 1)
                self.assertIn(build_frame('AD', (type_point + value8).encode()), nf.tx_log)
                scenario.add(ScenarioStep.ack_response('AR', b'00012300000001' * 10))
                self.assertEqual(exchange(f'AD_VERIFY_{circuit} {destination}'),
                                 f'OK:AD_VERIFY:{circuit}:{destination}:{value8}:00000001:291:291')
                self.assertEqual(exchange(f'CAL_MEASUREMENT_{circuit}? {point}'), 'ERR:CAL_MEASUREMENT_INVALID')
                self.assertEqual(scenario.handled_command_count, before + 2)
                self.assertEqual(self.transport.commands, instrument_requests)
        self.assertEqual(self.transport.commands, [b':SENS:FUNC?\r\n', b':READ?\r\n'] * len(points))
        self.assertEqual(exchange('TEST_END'), 'OK')
        self.assertEqual(exchange('LOG_DROP_COUNT?'), '0')
        self.assertEqual(exchange('AD_VERIFY_BATT_V P1'), 'ERR:CAL_NO_ACTIVE_TRIAL')

    def test_calibration_native_no_trial_disabled_or_bad_command_sends_nothing(self):
        app = FixtureApp(clock=self.clock, external_link=self.link)
        self.assertEqual(app.execute_ate_line('CAL_MEASURE BATT_V A 2000 :READ?'), 'ERR:CAL_NO_ACTIVE_TRIAL')
        self.assertEqual(app.execute_ate_line('CAL_MEASURE BATT_V A 2000 :CONF?'), 'ERR:CAL_MEASUREMENT_COMMAND')
        disabled = FixtureApp(clock=self.clock)
        disabled.execute_ate_line('TEST_START')
        self.assertEqual(disabled.execute_ate_line('CAL_MEASURE BATT_V A 2000 :READ?'), 'ERR:CAL_DISABLED')
        self.assertEqual(self.transport.commands, [])

    def test_calibration_native_non_dcv_stops_before_read(self):
        app, nf = self.calibration_app()
        self.transport.responses = [b'"CURR:DC"\r\n']
        self.assertEqual(self.calibration_request(app), 'ERR:CAL_METER_FUNCTION')
        self.assertEqual(self.transport.commands, [b':SENS:FUNC?\r\n'])
        self.assertEqual(nf.tx_log, [])

    def test_calibration_trial_start_invalidates_prior_product_status(self):
        app, nf = self.calibration_app()
        app.cache.validate('STATUS', {'previous_product': True}, 'D1')
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        self.assertFalse(app.cache.is_valid('STATUS'))
        self.transport.responses = [b'"VOLT:DC"\r\n', b'+09.62123E+00\r\n']
        self.assertTrue(self.calibration_request(app).startswith('OK:CAL_MEASURE:'))
        self.assertFalse(app.cache.is_valid('STATUS'))
        self.assertTrue(all(not app.cache.is_valid(name) for name in app.cache._entries))
        self.assertEqual(nf.tx_log, [])

    def test_calibration_native_bad_reacquisition_never_restores_prior_id(self):
        app, nf = self.calibration_app()
        self.transport.responses = [b'"VOLT:DC"\r\n', b'+09.62123E+00\r\n']
        old_id = self.calibration_request(app).split(':', 2)[2]
        self.transport.responses = [b'"VOLT:DC"\r\n', b'+9.999999E+37\r\n']
        self.assertEqual(self.calibration_request(app), 'ERR:CAL_MEASUREMENT_OVERRANGE')
        self.assertEqual(app.execute_ate_line('CAL_MEASUREMENT? ' + old_id), 'ERR:CAL_MEASUREMENT_INVALID')
        self.assertEqual(nf.tx_log, [])

    def test_calibration_native_pending_blocks_trial_change_and_regular_queries(self):
        app, nf = self.calibration_app()
        self.transport.responses = [b'"VOLT:DC"\r\n', b'+09.62123E+00\r\n']
        self.assertIsNone(app.execute_ate_line('CAL_MEASURE BATT_V A 2000 :READ?'))
        for command in ('TEST_END', 'TEST_START', 'STATUS_REFRESH', 'HOST_RESET METER'):
            self.assertEqual(app.execute_ate_line(command), 'ERR:BUSY')
        self.assertEqual(app.execute_ate_line('EXT_QUERY 2000 *IDN?'), 'ERR:EXT_BUSY:AMBIGUOUS=0')
        for _ in range(2000):
            app._service_external()
            reply = app.take_external_response()
            if reply is not None:
                break
            self.clock.sleep_ms(1)
        self.assertTrue(reply.startswith('OK:CAL_MEASURE:'), reply)
        self.assertEqual(nf.tx_log, [])

    def test_calibration_native_timeout_keeps_link_fault_and_never_sends_read(self):
        app, nf = self.calibration_app()
        self.transport.responses = []
        reply = self.calibration_request(app)
        self.assertTrue(reply.startswith('ERR:CAL_TIMEOUT'), reply)
        self.assertTrue(self.link.fault)
        self.assertEqual(self.transport.commands, [b':SENS:FUNC?\r\n'])
        self.assertEqual(nf.tx_log, [])

    def test_idn_round_trip_has_no_automatic_instrument_query(self):
        self.link.poll()
        self.assertEqual(self.transport.commands, [])
        reply = self.request()
        self.assertEqual(reply, 'OK:EXT_RX:32:41444320436F72702E2C373335352C3234363431303039392C20204130320D0A')
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n'])

    def test_192_byte_command_and_uart_fragmentation(self):
        self.transport.write_limit = 3
        body = b':s ' + b'X'*188 + b' '
        reply = self.request(b'EXT_SEND 2000 ' + body)
        self.assertEqual(reply, 'OK:EXT_TX')
        self.assertEqual(self.transport.commands, [body+b'\r\n'])

    def test_no_device_does_not_send_and_can_be_rechecked(self):
        self.lib.test_ready(self.transport.memory, 0)
        self.assertEqual(self.request(), 'ERR:EXT_LINK_NOT_READY:AMBIGUOUS=0')
        self.assertEqual(self.transport.commands, [])
        self.assertIsNone(self.link.session)
        self.lib.test_ready(self.transport.memory, 1)
        self.transport.responses = [b'ADC Corp.,7355,246410099,  A02\r\n']
        self.assertTrue(self.request().startswith('OK:EXT_RX:32:'))
        self.assertIsNotNone(self.link.session)

    def test_idle_disconnect_and_remount_reuse_link_without_reset(self):
        self.assertTrue(self.request().startswith('OK:EXT_RX:32:'))
        old_session = self.link.session
        self.lib.test_ready(self.transport.memory, 0)
        self.assertFalse(self.lib.test_fault(self.transport.memory))
        self.lib.test_ready(self.transport.memory, 1)
        self.transport.responses = [b'ADC Corp.,7355,246410099,  A02\r\n']

        reply = self.request()

        self.assertTrue(reply.startswith('OK:EXT_RX:32:'))
        self.assertFalse(self.lib.test_fault(self.transport.memory))
        self.assertIsNotNone(self.link.session)
        self.assertEqual(self.link.session, old_session)
        self.assertIsNotNone(self.link.host_info)
        self.assertTrue(self.link.core.ready)
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n', b'*IDN?\r\n'])

    def test_query_while_usb_disconnected_is_definite_and_recovers_after_remount(self):
        self.assertTrue(self.request().startswith('OK:EXT_RX:32:'))
        self.lib.test_ready(self.transport.memory, 0)

        reply = self.request()

        self.assertEqual(reply, 'ERR:EXT_LINK_NOT_READY:AMBIGUOUS=0')
        self.assertFalse(self.link.fault)
        self.assertFalse(self.lib.test_fault(self.transport.memory))
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n'])

        self.lib.test_ready(self.transport.memory, 1)
        self.transport.responses = [b'ADC Corp.,7355,246410099,  A02\r\n']
        reply = self.request()

        self.assertTrue(reply.startswith('OK:EXT_RX:32:'))
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n', b'*IDN?\r\n'])

    def test_active_disconnect_latches_ambiguous_fault_without_retry(self):
        self.transport.auto_device = False
        self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
        for _ in range(10):
            self.link.poll()
            if self.lib.test_pending(self.transport.memory):
                break
            self.clock.sleep_ms(1)
        self.assertTrue(self.lib.test_pending(self.transport.memory))

        self.lib.test_start(self.transport.memory)
        self.lib.test_ready(self.transport.memory, 0)
        self.transport.drain()
        for _ in range(10):
            self.link.poll()
            reply = self.link.take_reply()
            if reply is not None:
                break
            self.clock.sleep_ms(1)

        self.assertEqual(reply, 'ERR:EXT_DISCONNECTED:AMBIGUOUS=1')
        self.assertTrue(self.lib.test_fault(self.transport.memory))
        self.assertEqual(self.transport.commands, [])
        with self.assertRaisesRegex(RelayError, 'RECOVERY_REQUIRED'):
            self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))

    def test_conf_200v_is_transferred_without_range_gate(self):
        self.transport.responses = [b'"VOLT +1.999999E+02,+1.000000E-05"\r\n']
        reply = self.request(b'EXT_QUERY 2000 :CONF?')
        self.assertEqual(bytes.fromhex(reply.split(':')[-1]), b'"VOLT +1.999999E+02,+1.000000E-05"\r\n')

    def test_cdc_guard_delegates_success_and_other_device_errors(self):
        self.assertEqual(self.lib.test_cdc_xfer(3, 0x81, 0), 1)
        self.assertEqual(self.lib.test_cdc_xfer(4, 0x81, 1), 1)
        self.assertEqual(self.lib.test_cdc_real_calls(), 2)
        self.assertFalse(self.lib.test_fault(self.transport.memory))

    def test_cdc_guard_ignores_unmounted_device_error(self):
        self.lib.test_cdc_unbind()
        self.assertEqual(self.lib.test_cdc_xfer(3, 0x81, 2), 1)
        self.assertEqual(self.lib.test_cdc_real_calls(), 1)
        self.assertFalse(self.lib.test_fault(self.transport.memory))

    def test_cdc_guard_reports_transfer_error_without_retry(self):
        for endpoint, started, expected in ((0x81, False, 'USB_RX_XFER:AMBIGUOUS=0'),
                                           (0x81, True, 'USB_RX_XFER:AMBIGUOUS=1'),
                                           (0x02, True, 'USB_TX_XFER:AMBIGUOUS=1')):
            with self.subTest(endpoint=endpoint, started=started):
                self.setUp()
                self.transport.auto_device = False
                self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
                for _ in range(20):
                    self.link.poll()
                if started:
                    self.lib.test_start(self.transport.memory)
                self.assertEqual(self.lib.test_cdc_xfer(3, endpoint, 1), 0)
                for _ in range(20):
                    self.link.poll()
                self.assertEqual(self.link.take_reply(), 'ERR:EXT_' + expected)
                self.assertEqual(self.lib.test_cdc_real_calls(), 0)
                self.assertTrue(self.lib.test_fault(self.transport.memory))
                self.assertTrue(self.link.fault)
                with self.assertRaisesRegex(RelayError, 'RECOVERY_REQUIRED'):
                    self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))

    def test_host_timeout_snapshot_distinguishes_no_partial_and_completed_rx(self):
        cases = ((b'', True, 'TIMEOUT_RX0_T1_C0_XNONE'),
                 (b'12', True, 'TIMEOUT_RX2_T1_C0_X3132'),
                 (b'123456\r', True, 'TIMEOUT_RX7_T1_C0_X3435360D'),
                 (b'1\r\n', False, 'TIMEOUT_RX3_T0_C1_X310D0A'))
        for raw, tx_done, reason in cases:
            with self.subTest(raw=raw, tx_done=tx_done):
                self.setUp()
                self.transport.auto_device = False
                self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
                for _ in range(20):
                    self.link.poll()
                self.lib.test_start(self.transport.memory)
                if tx_done:
                    self.lib.test_done(self.transport.memory)
                if raw:
                    self.lib.test_rx(self.transport.memory, raw, len(raw), 0)
                self.lib.test_poll(self.transport.memory, 2100)
                for _ in range(20):
                    self.link.poll()
                self.assertEqual(self.link.take_reply(), 'ERR:EXT_' + reason + ':AMBIGUOUS=1')
                self.assertTrue(self.link.fault)
                self.assertTrue(self.lib.test_fault(self.transport.memory))

    def test_usb_timeout_diagnostic_preserves_identity_and_ambiguous_flag(self):
        raw = encode_frame(b'PARENTNCHOSTNONC', 7, 'E', 1, 2000, b'TIMEOUT_RX0_T1_C0_XNONE|1')
        out = ctypes.create_string_buffer(512)
        size = self.lib.test_usb_diag(raw, len(raw), out)
        frame = decode_frame(out.raw[:size])
        original = decode_frame(raw)
        for name in ('session', 'request', 'kind', 'mode', 'timeout_ms'):
            self.assertEqual(frame[name], original[name])
        self.assertEqual(frame['payload'], b'TIMEOUT_RX0_T1_C0_XNONE_I2000_N1998_D2_S80_PD2_EP81_H1_K0_L0/64_OA2_ON3_OX0_OPD2_OE02|1')

    def test_usb_diagnostic_leaves_normal_other_error_and_full_payload_unchanged(self):
        for kind, payload in (('R', b'TIMEOUT_RX0_T1_C0_XNONE|1'),
                              ('E', b'USB_RX_XFER|1'), ('E', b'TIMEOUT_X|0'),
                              ('E', b'TIMEOUT_' + b'A' * 182 + b'|1')):
            with self.subTest(kind=kind, payload=payload):
                raw = encode_frame(b'PARENTNCHOSTNONC', 7, kind, 1, 2000, payload)
                out = ctypes.create_string_buffer(512)
                size = self.lib.test_usb_diag(raw, len(raw), out)
                self.assertEqual(out.raw[:size], raw)

    def test_thousand_native_exchanges_preserve_variable_response_boundaries(self):
        # 最小/最大応答とFIFO累積量を跨ぎ、前要求の末尾を次へ混ぜない。
        session = None
        for index in range(1000):
            length = (index % 190) + 1
            raw = bytes([65 + index % 26]) * length + b'\r\n'
            self.transport.responses = [raw]
            reply = self.request()
            self.assertEqual(bytes.fromhex(reply.split(':')[-1]), raw)
            session = session or self.link.session
            self.assertEqual(self.link.session, session)
            self.assertFalse(self.link.fault)
            self.assertFalse(self.link.busy)
            self.assertFalse(self.lib.test_pending(self.transport.memory))
        self.assertEqual(len(self.transport.commands), 1000)
        self.assertEqual(self.link.core._sequence, 1000)

    def test_partial_response_disconnect_cannot_revive_after_remount_or_late_data(self):
        self.transport.auto_device = False
        self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
        for _ in range(20):
            self.link.poll()
        self.lib.test_start(self.transport.memory)
        self.lib.test_done(self.transport.memory)
        self.lib.test_rx(self.transport.memory, b'OLD', 3, self.clock.ticks_ms())
        self.lib.test_ready(self.transport.memory, 0)
        for _ in range(20):
            self.link.poll()
        self.assertEqual(self.link.take_reply(), 'ERR:EXT_DISCONNECTED:AMBIGUOUS=1')
        self.lib.test_ready(self.transport.memory, 1)
        self.lib.test_rx(self.transport.memory, b'\r\n', 2, self.clock.ticks_ms())
        self.lib.test_done(self.transport.memory)
        with self.assertRaisesRegex(RelayError, 'RECOVERY_REQUIRED'):
            self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
        self.assertTrue(self.lib.test_fault(self.transport.memory))
        self.assertIsNone(self.link.take_reply())

    def test_fixture_rejects_bad_ate_lines_then_accepts_one_normal_request_each(self):
        app, ate, nf = self.app()
        bad_lines = (b'EXT_QUERY 0 *IDN?', b'EXT_QUERY 2000 \x03*IDN?',
                     b'EXT_QUERY 2000 \xff', b'X' * 513)
        for index, bad in enumerate(bad_lines):
            self.transport.responses = [b'GOOD\r\n']
            ate.enqueue_rx(bad + b'\rEXT_QUERY 2000 *IDN?\r')
            self.run_app(app, 150)
            self.assertEqual(len(self.transport.commands), index + 1)
        replies = b''.join(ate.tx_log).split(b'\r')[:-1]
        self.assertEqual(len(replies), len(bad_lines) * 2)
        for index in range(0, len(replies), 2):
            self.assertTrue(replies[index].startswith(b'ERR:'))
            self.assertEqual(replies[index + 1], b'OK:EXT_RX:6:474F4F440D0A')
        self.assertEqual(nf.tx_log, [])

    def test_query_timeout_latches_and_never_retries(self):
        self.transport.responses = []
        self.link.start(parse_monitor_request(b'EXT_QUERY 50 :READ?'))
        for _ in range(60):
            self.link.poll()
            self.clock.sleep_ms(1)
        reply = self.link.take_reply()
        self.assertEqual(reply, 'ERR:EXT_TIMEOUT:AMBIGUOUS=1')
        self.assertEqual(self.transport.commands, [b':READ?\r\n'])
        with self.assertRaisesRegex(RelayError, 'RECOVERY_REQUIRED'):
            self.link.start(parse_monitor_request(b'EXT_QUERY 50 *IDN?'))

    def test_expired_partial_uart_request_is_not_completed_after_deadline(self):
        self.transport.write_limit = 1
        self.link.start(parse_monitor_request(b'EXT_QUERY 2 *IDN?'))
        for _ in range(10):
            self.link.poll()
            self.clock.sleep_ms(1)
        self.assertTrue(self.link.take_reply().startswith('ERR:EXT_TIMEOUT:'))
        self.assertEqual(self.transport.commands, [])

    def test_host_timeout_rejects_late_usb_data_and_new_request(self):
        self.transport.auto_device = False
        self.link.start(parse_monitor_request(b'EXT_QUERY 100 *IDN?'))
        for _ in range(20):
            self.link.poll()
            self.clock.sleep_ms(1)
        self.assertTrue(self.lib.test_pending(self.transport.memory))
        self.lib.test_start(self.transport.memory)
        self.lib.test_poll(self.transport.memory, 200)
        self.lib.test_rx(self.transport.memory, b'late\r\n', 6, 201)
        self.assertTrue(self.lib.test_fault(self.transport.memory))
        self.assertFalse(self.lib.test_pending(self.transport.memory))

    def test_host_rejects_duplicate_request_without_reexecution(self):
        self.assertTrue(self.request().startswith('OK:EXT_RX:'))
        repeat = encode_frame(self.link.session,1,'Q',1,2000,b'*IDN?')
        self.lib.test_uart(self.transport.memory,repeat,len(repeat),self.clock.ticks_ms())
        self.assertFalse(self.lib.test_pending(self.transport.memory))
        self.assertEqual(self.transport.commands,[b'*IDN?\r\n'])

    def test_new_parent_cannot_silently_rebind_old_host_session(self):
        self.assertTrue(self.request().startswith('OK:EXT_RX:'))
        second = ExternalInstrumentLink(self.transport,self.clock,b'PARENT02','BFCF2EDB84B0B37F')
        second.start(parse_monitor_request(b'EXT_QUERY 100 *IDN?'))
        reply = None
        for _ in range(30):
            second.poll()
            reply = second.take_reply()
            if reply:
                break
            self.clock.sleep_ms(1)
        self.assertEqual(reply,'ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0')
        self.assertEqual(self.transport.commands,[b'*IDN?\r\n'])

    def test_crc_broken_request_never_reaches_usb(self):
        self.assertTrue(self.request().startswith('OK:EXT_RX:'))
        wire=encode_frame(self.link.session,2,'Q',1,100,b':READ?')
        wire=wire.replace(b'3A524541443F',b'3A524541443E')
        self.lib.test_uart(self.transport.memory,wire,len(wire),self.clock.ticks_ms())
        self.assertFalse(self.lib.test_pending(self.transport.memory))
        self.assertEqual(self.transport.commands,[b'*IDN?\r\n'])

    def test_overlong_uart_stream_resynchronizes_only_at_line_boundary(self):
        reader=FrameReader()
        wire=encode_frame(bytes(16),1,'A',0,0,b'')
        self.assertEqual(reader.feed(b'X'*600+wire),[])
        self.assertEqual(reader.errors,1)
        self.assertEqual(reader.feed(wire),[decode_frame(wire)])

    def test_unsolicited_usb_data_quarantines_host_before_first_request(self):
        self.lib.test_rx(self.transport.memory,b'old\r\n',5,0)
        self.assertEqual(self.request(),'ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0')
        self.assertEqual(self.transport.commands,[])


    def app(self):
        ate = MockUART(clock=self.clock)
        nf = MockUART(clock=self.clock)
        protocol = NF55Protocol(nf, clock=self.clock)
        return FixtureApp(ate_uart=ate, protocol=protocol, clock=self.clock, external_link=self.link), ate, nf

    def run_app(self, app, count=100):
        for _ in range(count):
            app.service_once()
            self.clock.sleep_ms(1)

    def test_fixture_ate_to_real_c_host_and_back_without_nf55g_transmission(self):
        app, ate, nf = self.app()
        ate.enqueue_rx(b'EXT_QUERY 2000 *IDN?\r')
        self.run_app(app)
        wire = b''.join(ate.tx_log)
        self.assertTrue(wire.startswith(b'OK:EXT_RX:32:'))
        self.assertTrue(wire.endswith(b'\r'))
        self.assertEqual(nf.tx_log, [])
        self.assertEqual(self.transport.commands, [b'*IDN?\r\n'])
        self.assertEqual(app.measurements._values, {})
        self.assertFalse(app._comm_busy())

    def test_fixture_defers_reply_and_preserves_ate_order_while_waiting(self):
        self.transport.auto_device = False
        app, ate, nf = self.app()
        ate.enqueue_rx(b'EXT_QUERY 2000 *IDN?\rCOMM_STATUS?\r')
        self.run_app(app, 30)
        self.assertEqual(ate.tx_log, [])
        self.assertTrue(app._external_pending)
        self.assertEqual(len(app.server.pending), 1)
        self.transport.auto_device = True
        self.transport.service_device()
        self.run_app(app, 50)
        replies = b''.join(ate.tx_log).split(b'\r')
        self.assertTrue(replies[0].startswith(b'OK:EXT_RX:32:'))
        self.assertEqual(len(replies), 3)
        self.assertEqual(nf.tx_log, [])

    def test_back_to_back_cdc_nf_bursts_do_not_starve_sd_between_replies(self):
        from src.logger import Logger, MemorySDSink
        from src.mock_nf55g import MockNF55GScenario, ScenarioStep
        outer = self
        class GuardedSink(MemorySDSink):
            def write_record(self, row):
                outer.assertFalse(app._comm_busy())
                outer.assertFalse(app.server.has_work())
                super().write_record(row)
            def flush(self):
                outer.assertFalse(app._comm_busy())
                outer.assertFalse(app.server.has_work())
                super().flush()
        sink = GuardedSink()
        nf = MockUART(clock=self.clock, scenario=MockNF55GScenario([
            ScenarioStep.ack_response('D1', '0' * 15) for _ in range(50)]))
        ate = MockUART(clock=self.clock)
        logger = Logger(sd_sink=sink, clock=self.clock, queue_limit=64)
        app = FixtureApp(ate_uart=ate, nf55_uart=nf, clock=self.clock,
                         logger=logger, external_link=self.link)
        self.assertEqual(app.execute_ate_line('LOG_CONT_START'), 'OK')
        for _ in range(50):
            self.transport.responses = [b'1\r\n']
            before = b''.join(ate.tx_log).count(b'\r')
            ate.enqueue_rx(b'EXT_QUERY 2000 :READ?\rSTATUS_REFRESH\rRETRY_COUNT?\rSD_STATUS?\rCOMM_STATUS?\r')
            for _ in range(1000):
                app.service_once()
                if b''.join(ate.tx_log).count(b'\r') == before + 5:
                    break
                self.clock.sleep_ms(1)
            else:
                self.fail('burst did not finish')
            # 最終応答が返ったらidle巡回を挟まず次burstを投入する実機条件。
        self.assertEqual(logger.drop_count, 0)
        self.assertGreater(sink.write_count, 0)
        self.assertEqual(nf.scenario.handled_command_count, 50)

    def test_pending_ate_request_keeps_priority_over_due_sd_write(self):
        from src.logger import Logger, MemorySDSink
        sink = MemorySDSink()
        logger = Logger(sd_sink=sink, clock=self.clock, flush_record_count=1)
        ate = MockUART(clock=self.clock)
        app = FixtureApp(ate_uart=ate, clock=self.clock, logger=logger)
        self.assertEqual(app.execute_ate_line('LOG_CONT_START'), 'OK')
        ate.enqueue_rx(b'COMM_STATUS?\rCOMM_STATUS?\r')
        app.service_once()
        self.assertEqual(sink.write_count, 0)
        self.assertEqual(len(app.server.pending), 1)
        app.service_once()
        self.assertGreater(sink.write_count, 0)

    def test_fixture_send_preserves_trailing_spaces_and_does_not_add_query(self):
        app, ate, nf = self.app()
        body = b':sens:func "VOLT:DC"  '
        ate.enqueue_rx(b'EXT_SEND 2000 ' + body + b'\r\n')
        self.run_app(app)
        self.assertEqual(b''.join(ate.tx_log), b'OK:EXT_TX\r')
        self.assertEqual(self.transport.commands, [body+b'\r\n'])
        self.assertEqual(nf.tx_log, [])

    def test_fixture_busy_boundary_does_not_end_trial_or_bypass_fu_prohibition(self):
        app = FixtureApp(clock=self.clock, external_link=self.link)
        self.assertEqual(app.execute_ate_line('TEST_START'), 'OK')
        trial = app.logger.trial_id
        self.assertIsNone(app.execute_ate_line('EXT_QUERY 2000 *IDN?'))
        self.assertEqual(app.execute_ate_line('TEST_END'), 'ERR:BUSY')
        self.assertEqual(app.execute_ate_line('TEST_START'), 'ERR:BUSY')
        self.assertEqual(app.logger.trial_id, trial)
        self.assertEqual(app.execute_ate_line('FW_UPDATE'), 'ERR:FU_DISABLED')
        self.run_app(app)
        self.assertTrue(app.take_external_response().startswith('OK:EXT_RX:32:'))
        self.assertEqual(app.execute_ate_line('TEST_END'), 'OK')

    def test_disabled_fixture_validates_request_without_touching_hardware(self):
        app = FixtureApp(clock=self.clock)
        self.assertEqual(app.execute_ate_line('EXT_QUERY 2000 *IDN?'), 'ERR:EXT_DISABLED:AMBIGUOUS=0')
        self.assertEqual(app.execute_ate_line('EXT_QUERY 0 *IDN?'), 'ERR:EXT_TIMEOUT:AMBIGUOUS=0')
        self.assertEqual(self.transport.commands, [])

    def test_host_response_overflow_is_error_not_truncated_success(self):
        self.transport.responses = [b'X'*191+b'\r\n']
        self.assertEqual(self.request(), 'ERR:EXT_RESPONSE_TOO_LONG:AMBIGUOUS=1')
        self.assertTrue(self.link.fault)

    def test_host_handles_response_before_tx_completion(self):
        self.transport.auto_device = False
        self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
        for _ in range(20):
            self.link.poll()
        self.lib.test_start(self.transport.memory)
        self.lib.test_rx(self.transport.memory,b'1\r\n',3,self.clock.ticks_ms())
        for _ in range(10):
            self.link.poll()
        self.assertIsNone(self.link.take_reply())
        self.lib.test_done(self.transport.memory)
        reply = None
        for _ in range(10):
            self.link.poll()
            reply = self.link.take_reply()
            if reply:
                break
        self.assertEqual(reply, 'OK:EXT_RX:3:310D0A')

    def test_host_timeout_clock_wrap(self):
        self.transport.auto_device = False
        hello = encode_frame(b'PARENT01'+bytes(8),0,'H',0,0,b'')
        self.lib.test_uart(self.transport.memory,hello,len(hello),0xfffffff0)
        query = encode_frame(b'PARENT01HOSTNONC',1,'Q',1,50,b'*IDN?')
        self.lib.test_uart(self.transport.memory,query,len(query),0xfffffff0)
        self.lib.test_start(self.transport.memory)
        self.lib.test_poll(self.transport.memory,0x10)
        self.assertTrue(self.lib.test_pending(self.transport.memory))
        self.lib.test_poll(self.transport.memory,0x22)
        self.assertFalse(self.lib.test_pending(self.transport.memory))
        self.assertTrue(self.lib.test_fault(self.transport.memory))


    def test_all_usb_command_lengths_avoid_zlp_and_preserve_exact_byte_count(self):
        self.assertEqual(self.lib.test_chunk(0), 0)
        for total in range(1,195):
            remaining = total
            chunks = []
            while remaining:
                chunk = self.lib.test_chunk(remaining)
                self.assertGreater(chunk, 0)
                self.assertLessEqual(chunk, min(63,remaining))
                for packet in (8,16,32,64):
                    self.assertNotEqual(chunk % packet, 0)
                chunks.append(chunk)
                remaining -= chunk
            self.assertEqual(sum(chunks), total)

    def test_partial_q_stops_at_parent_deadline_without_usb_execution(self):
        self.assertTrue(self.request().startswith('OK:EXT_RX:'))
        self.transport.write_limit = 1
        self.link.start(parse_monitor_request(b'EXT_QUERY 2 :READ?'))
        for _ in range(10):
            self.link.poll()
            self.clock.sleep_ms(1)
        self.assertEqual(self.link.take_reply(),'ERR:EXT_TIMEOUT:AMBIGUOUS=1')
        self.assertEqual(self.transport.commands,[b'*IDN?\r\n'])

    def test_real_c_engine_reassembles_usb_response_at_every_split(self):
        raw = b'ADC Corp.,7355,246410099,  A02\r\n'
        for split in range(1,len(raw)):
            self.setUp()
            self.transport.auto_device = False
            self.link.start(parse_monitor_request(b'EXT_QUERY 2000 *IDN?'))
            for _ in range(20):
                self.link.poll()
            self.lib.test_start(self.transport.memory)
            self.lib.test_done(self.transport.memory)
            self.lib.test_rx(self.transport.memory,raw[:split],split,0)
            for _ in range(8):
                self.link.poll()
            self.assertIsNone(self.link.take_reply())
            self.lib.test_rx(self.transport.memory,raw[split:],len(raw)-split,0)
            reply = None
            for _ in range(10):
                self.link.poll()
                reply = self.link.take_reply()
                if reply:
                    break
            self.assertEqual(bytes.fromhex(reply.split(':')[-1]),raw)

    def test_wrong_host_identity_never_sends_q(self):
        self.link.expected_chipid = '0000000000000000'
        self.assertEqual(self.request(),'ERR:EXT_HOST_IDENTITY:AMBIGUOUS=0')
        self.assertEqual(self.transport.commands,[])


if __name__ == '__main__':
    unittest.main()
