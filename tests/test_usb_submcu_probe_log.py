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
