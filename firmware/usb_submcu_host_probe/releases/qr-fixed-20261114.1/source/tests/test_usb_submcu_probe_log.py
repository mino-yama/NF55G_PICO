"""欠落・破損した診断ログを正常な受入証拠として扱わない。"""
import importlib.util
import struct
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('probe_log',Path(__file__).resolve().parents[1]/'scripts/usb_submcu_probe_log.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def rec(seq,kind,data=b'',addr=1,instance=0):
    return p.RECORD.pack(seq,10*seq,kind,addr,instance,len(data),data.ljust(64,b'\0'))
def good():
    return [rec(0,1,b'qr-probe-20261111.1'),rec(1,4,b'\1\0\3\0'),rec(2,5,b'abc'),rec(3,6,b'\0'*8)]
def ram(records,dropped=0):
    return p.HEADER.pack(p.MAGIC,1,len(records),dropped,100)+b''.join(records)+bytes((256-len(records))*76)
class ProbeLogTests(unittest.TestCase):
    def test_stream_has_no_lifetime_1024_record_limit(self):
        records=[rec(0,1,p.STREAM_VERSION)]+[rec(i,14,struct.pack('<6I',i*100,i*1000,0,0,0,8)) for i in range(1,1200)]
        r=p.read_uart('\n'.join('@'+x.hex() for x in records))
        self.assertEqual(r['records'],1200);self.assertIsNone(r['record_capacity'])
        self.assertFalse(r['hardware_acceptance'])
    def test_stream_drop_is_capture_error(self):
        r=p.read_uart('\n'.join('@'+x.hex() for x in [rec(0,1,p.STREAM_VERSION),rec(1,14,struct.pack('<6I',10,10,1,0,0,8))]))
        self.assertEqual(r['status'],'capture_errors')
    def test_health_and_stage_reject_corruption(self):
        cases=[(14,b''),(14,struct.pack('<6I',0,0,0,0,0,16)),(15,b''),(15,struct.pack('<BI',0,0)),(15,struct.pack('<BI',1,20)),(15,struct.pack('<BI',2,1))]
        for kind,data in cases:
            with self.subTest(kind=kind,data=data),self.assertRaises(ValueError):
                p.read_uart('\n'.join('@'+x.hex() for x in [rec(0,1,p.STREAM_VERSION),rec(1,kind,data)]))
    def test_stream_stage_order_data_and_gap_detection(self):
        records=[rec(0,1,p.STREAM_VERSION)]+[rec(i,15,struct.pack('<BI',i,3000 if i==1 else 0)) for i in range(1,5)]
        text='\n'.join('@'+x.hex() for x in records)
        self.assertEqual(p.read_uart(text)['records'],5)
        with self.assertRaisesRegex(ValueError,'sequence gap'):
            p.read_uart('\n'.join(text.splitlines()[:2]+text.splitlines()[3:]))
    def test_firmware_qr_text_is_diagnostic_only(self):
        r=p.read_ram(ram(good()+[rec(4,12,b'AbC-'+b'0'*25+b'123456')]))
        self.assertEqual(r['events'][-1]['kind'],'qr_text')
        self.assertFalse(r['qr_text_verified']);self.assertFalse(r['hardware_acceptance'])
    def test_partial_or_disallowed_qr_text_rejected(self):
        for payload in (b'A'*34,b'A'*36,b'A'*34+b' '):
            with self.subTest(payload=payload),self.assertRaisesRegex(ValueError,'invalid decoded QR'):
                p.read_ram(ram(good()+[rec(4,12,payload)]))
        with self.assertRaisesRegex(ValueError,'invalid decoded QR'):
            p.read_ram(ram([rec(0,1),rec(1,12,b'A'*35)]))
    def test_decoder_error_is_capture_error_and_validated(self):
        r=p.read_ram(ram([rec(0,1),rec(1,13,b'\x0a')]))
        self.assertEqual(r['status'],'capture_errors')
        for payload in (b'',b'\0',b'\x0c',b'\1\2'):
            with self.subTest(payload=payload),self.assertRaisesRegex(ValueError,'invalid QR decode error'):
                p.read_ram(ram([rec(0,1),rec(1,13,payload)]))
    def test_decoder_fw_keeps_1024_capacity(self):
        r=p.read_uart(self.uart_capacity_records(b'qr-uart-20261114.2',400))
        self.assertEqual(r['record_capacity'],1024)
    def uart_capacity_records(self, version, count):
        return '\n'.join('@'+r.hex() for r in
                         [rec(0,1,version)]+[rec(i,11,b'id') for i in range(1,count)])
    def test_known_large_uart_version_allows_more_than_256(self):
        r=p.read_uart(self.uart_capacity_records(b'qr-uart-20261114.1',400))
        self.assertEqual(r['record_capacity'],1024)
        self.assertEqual(r['records'],400);self.assertFalse(r['hardware_acceptance'])
    def test_large_uart_capacity_boundary(self):
        self.assertEqual(p.read_uart(self.uart_capacity_records(b'qr-uart-20261114.1',1023))['records'],1023)
        with self.assertRaisesRegex(ValueError,'at capacity'):
            p.read_uart(self.uart_capacity_records(b'qr-uart-20261114.1',1024))
    def test_old_and_unknown_versions_keep_256_limit(self):
        for version in (b'qr-uart-20261111.1',b'unknown'):
            with self.subTest(version=version):
                self.assertEqual(p.read_uart(self.uart_capacity_records(version,255))['record_capacity'],256)
                with self.assertRaisesRegex(ValueError,'at capacity'):
                    p.read_uart(self.uart_capacity_records(version,256))
    def test_large_uart_still_rejects_sequence_gap(self):
        text=self.uart_capacity_records(b'qr-uart-20261114.1',400)
        lines=text.splitlines();del lines[200]
        with self.assertRaisesRegex(ValueError,'sequence gap'):
            p.read_uart('\n'.join(lines))
    def startup_uart(self, extra=()):
        records=[rec(0,1,b'qr-uart-20261111.1'),rec(1,11,b'A06FEA01012EC137'),*extra]
        return b''.join(b'@'+r.hex().encode('ascii')+b'\n' for r in records)
    def test_startup_nul_requires_explicit_option(self):
        with self.assertRaises(ValueError):p.read_uart_capture(b'\0'+self.startup_uart())
    def test_startup_nul_is_reported_without_acceptance(self):
        raw=b'\0'+self.startup_uart()
        r=p.read_uart_capture(raw,True)
        self.assertEqual(r['startup_prefix_hex'],'00');self.assertEqual(r['source_bytes'],309)
        self.assertFalse(r['original_framing_clean']);self.assertTrue(r['warnings'])
        self.assertFalse(r['hardware_acceptance']);self.assertFalse(r['qr_text_verified'])
        self.assertEqual(raw[:2],b'\0@')
    def test_startup_option_keeps_clean_capture_clean(self):
        r=p.read_uart_capture(self.startup_uart(),True)
        self.assertTrue(r['original_framing_clean']);self.assertEqual(r['warnings'],[])
    def test_arbitrary_or_multiple_prefix_bytes_rejected(self):
        for prefix in (b'\0\0',b'x',b'\xff',b'\n\0'):
            with self.subTest(prefix=prefix),self.assertRaises(ValueError):
                p.read_uart_capture(prefix+self.startup_uart(),True)
    def test_midstream_nul_and_sequence_gap_rejected(self):
        for raw in (self.startup_uart().replace(b'\n@',b'\n\0@'),
                    self.startup_uart([rec(3,2)])):
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                p.read_uart_capture(b'\0'+raw,True)
    def test_startup_requires_identity_and_complete_line(self):
        for body in (b'@'+rec(0,1).hex().encode()+b'\n',
                     self.startup_uart().rstrip(b'\n'),
                     self.startup_uart().replace(b'41303646',b'7a7a7a7a')):
            with self.subTest(body=body),self.assertRaises(ValueError):
                p.read_uart_capture(b'\0'+body,True)
    def test_startup_option_preserves_init_error(self):
        r=p.read_uart_capture(b'\0'+self.startup_uart([rec(2,10)]),True)
        self.assertEqual(r['status'],'capture_errors');self.assertEqual(len(r['errors']),1)
    def test_ram_raw_only(self):
        r=p.read_ram(ram(good()));self.assertEqual(r['records'],4);self.assertFalse(r['hardware_acceptance']);self.assertFalse(r['qr_text_verified'])
    def test_uart_raw_only(self):
        r=p.read_uart('\n'.join('@'+x.hex() for x in good()));self.assertIsNone(r['dropped'])
    def test_ram_overflow_rejected(self):
        with self.assertRaises(ValueError):p.read_ram(ram(good(),1))
    def test_full_log_rejected(self):
        with self.assertRaises(ValueError):p.read_ram(ram([rec(i,1) for i in range(256)]))
    def test_short_ram(self):
        with self.assertRaises(ValueError):p.read_ram(b'bad')
    def test_header_corrupt(self):
        with self.assertRaises(ValueError):p.read_ram(bytes(19476))
    def test_missing_descriptor(self):
        with self.assertRaises(ValueError):p.read_ram(ram(good()[:2]))
    def test_zero_descriptor_rejected(self):
        with self.assertRaises(ValueError):p.read_ram(ram([rec(0,1),rec(1,4,bytes([1,0,0,0]))]))
    def test_sequence_gap(self):
        with self.assertRaises(ValueError):p.read_ram(ram([rec(0,1),rec(3,2)]))
    def test_uart_truncated(self):
        with self.assertRaises(ValueError):p.read_uart('@001')
    def test_unknown_kind(self):
        with self.assertRaises(ValueError):p.decode_record(rec(0,99))
    def test_error_not_success(self):
        r=p.read_ram(ram([rec(0,1),rec(1,7)]));self.assertEqual(r['status'],'capture_errors')
    def test_data_length_overflow(self):
        raw=bytearray(rec(0,1));raw[11]=65
        with self.assertRaises(ValueError):p.decode_record(raw)
    def test_report_without_mount(self):
        with self.assertRaises(ValueError):p.read_ram(ram([rec(0,1),rec(1,6)]))
if __name__=='__main__':unittest.main()
