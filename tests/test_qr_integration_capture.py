"""結合用受動採取で途中接続・不正レコード・個体未確認を誤受入しない。"""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qr_integration_capture',ROOT/'docs/QR_Hardware_Integration_20261123_01/capture_and_inspect.py')
capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
sys.path.insert(0,str(ROOT/'docs/QR_Hardware_Integration_20261123_01'))
from inspect_startup import inspect_boot_segments
QR='NF55G---'+'A1234567890123'+'A03'+'26'+'01'+'000001'


def record(seq,kind,payload):
    raw=struct.pack('<IIBBBB64s',seq,seq*10,kind,1,0,len(payload),payload.ljust(64,b'\0'))
    return b'@'+raw.hex().encode()+b'\n'


class QRCaptureTests(unittest.TestCase):
    def test_new_firmware_period_label_and_unknown_firmware(self):
        label='US250A-CGXE-009491-101A1.2601000001'
        raw=record(0,1,b'qr-fixed-20261123.1')+record(1,11,b'A06FEA01012EC137')+record(2,12,label.encode())
        result=capture.inspect(raw,label,True)
        self.assertTrue(result['identity_verified'])
        self.assertTrue(result['all_texts_match'])
        self.assertEqual(result['texts'][0]['fields']['product_rev'],'A1.')
        self.assertEqual(capture.inspect(raw.replace(b'71722d66697865642d32303236313132332e31',b'71722d66697865642d32303236313132332e39'),label,True)['status'],'CAPTURE_ERRORS')

    def test_explicit_boot_boundary_splits_reset_without_hiding_gaps(self):
        raw=record(90,14,struct.pack('<6I',1,1,0,0,0,12))+record(0,1,b'qr-fixed-20261114.1')+record(1,11,b'A06FEA01012EC137')
        segments=inspect_boot_segments(raw)
        self.assertEqual(len(segments),2)
        self.assertTrue(segments[1]['result']['identity_verified'])
        self.assertEqual(segments[0]['end_byte'],segments[1]['start_byte'])
        broken=raw+record(3,12,QR.encode())
        self.assertEqual(inspect_boot_segments(broken)[1]['result']['status'],'CAPTURE_ERRORS')

    def test_midstream_text_is_decoded_but_identity_and_hardware_are_unaccepted(self):
        result=capture.inspect(record(50,12,QR.encode()),QR)
        self.assertEqual(result['texts'][0]['fields']['serial'],'000001')
        self.assertTrue(result['all_texts_match'])
        self.assertTrue(result['midstream'])
        self.assertFalse(result['identity_verified'])
        self.assertFalse(result['hardware_acceptance'])

    def test_boot_version_and_board_id_require_exact_expected_identity(self):
        raw=record(0,1,b'qr-fixed-20261114.1')+record(1,11,b'A06FEA01012EC137')+record(2,12,QR.encode())
        result=capture.inspect(raw,QR)
        self.assertTrue(result['identity_verified'])
        self.assertFalse(result['midstream'])
        self.assertFalse(result['hardware_acceptance'])
        other=raw.replace(b'41303646454130313031324543313337',b'41303646454130313031324543313338')
        self.assertFalse(capture.inspect(other,QR)['identity_verified'])

    def test_boundary_fragments_are_preserved_and_full_line_corruption_is_error(self):
        result=capture.inspect(b'partial\n'+record(12,12,QR.encode())+b'@partial',QR)
        self.assertEqual(bytes.fromhex(result['prefix_hex']),b'partial\n')
        self.assertEqual(bytes.fromhex(result['tail_hex']),b'@partial')
        self.assertFalse(result['hardware_acceptance'])
        corrupted=record(12,12,QR.encode())[:-3]+b'ZZ\n'
        self.assertEqual(capture.inspect(corrupted)['status'],'CAPTURE_ERRORS')

    def test_gap_drop_and_host_decode_error_are_recorded_as_errors(self):
        samples=(record(20,12,QR.encode())+record(22,12,QR.encode()),
                 record(20,14,struct.pack('<6I',100,1000,1,0,10,9)),
                 record(20,13,b'\1'))
        for raw in samples:
            self.assertEqual(capture.inspect(raw)['status'],'CAPTURE_ERRORS')

    def test_mismatch_invalid_text_and_crlf(self):
        result=capture.inspect(record(1,12,QR.encode()).replace(b'\n',b'\r\n'),'X'*35)
        self.assertEqual(len(result['texts']),1)
        self.assertFalse(result['all_texts_match'])
        self.assertEqual(result['status'],'CAPTURE_ONLY')
        self.assertEqual(capture.inspect(record(1,12,b'X'*34))['status'],'CAPTURE_ERRORS')
