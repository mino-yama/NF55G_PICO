"""親Python adapterと実Host C engineを接続し、同じX1フレームで縦通しを検証する。"""
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from src.external_instrument_contract import encode_frame, decode_frame, parse_monitor_request
from src.external_instrument_link import ExternalInstrumentLink, FrameReader
from src.external_instrument_relay import RelayError
from src.mock_nf55g import FakeClock, MockUART
from src.main import FixtureApp
from src.nf55_protocol import NF55Protocol

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'firmware/usb_submcu_external_meter_host'

WRAPPER = r'''#include "relay_host.h"
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
    relay_host_init(&test->host, nonce, "BFCF2EDB84B0B37F", "meter-host-relay-20261120.1", emit, test);
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
API int test_fault(test_t *test) { return test->host.fault; }
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
        self.last_request = 0
        self.frame_reader = FrameReader()

    def drain(self):
        out = ctypes.create_string_buffer(512)
        while (size := self.lib.test_pop(self.memory, out)):
            if not self.drop_replies:
                self.rx.extend(out.raw[:size])

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
        library = folder / ('relay.dll' if os.name == 'nt' else 'relay.so')
        args = [compiler, '-shared', '-I', str(SOURCE), str(SOURCE/'relay_host.c'),
                str(SOURCE/'relay_wire.c'), str(wrapper), '-o', str(library)]
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
        for name in ('test_command', 'test_pop'):
            getattr(cls.lib, name).argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            getattr(cls.lib, name).restype = ctypes.c_size_t
        cls.lib.test_recode.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
        cls.lib.test_recode.restype = ctypes.c_size_t

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
        for kind in ('H','h','Q','A','T','R','E'):
            for size in (0,1,63,64,191,192):
                wire = encode_frame(bytes(range(16)), 0xffffffff, kind, 1, 10000, bytes(range(size)))
                out = ctypes.create_string_buffer(512)
                length = self.lib.test_recode(wire,len(wire),out)
                self.assertEqual(out.raw[:length], wire)
                bad = wire[:-4] + b'AA' + wire[-2:]
                self.assertEqual(self.lib.test_recode(bad,len(bad),out),0)

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
        self.lib.test_ready(self.transport.memory, 1)
        self.assertTrue(self.request().startswith('OK:EXT_RX:32:'))

    def test_conf_200v_is_transferred_without_range_gate(self):
        self.transport.responses = [b'"VOLT +1.999999E+02,+1.000000E-05"\r\n']
        reply = self.request(b'EXT_QUERY 2000 :CONF?')
        self.assertEqual(bytes.fromhex(reply.split(':')[-1]), b'"VOLT +1.999999E+02,+1.000000E-05"\r\n')

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
