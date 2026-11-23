"""図面の欄長を守り、型式/品目/REVやサンプル号機を受付固定値にしない。"""
import json
from pathlib import Path
import unittest
from src.qr_reader import decode_qr,decode_nf55g_label


class NF55GLabelTests(unittest.TestCase):
    def test_actual_label_preserves_revision_period_only_in_revision_field(self):
        raw='US250A-CGXE-009491-101A1.2601000001'
        fields=decode_nf55g_label(raw)
        self.assertEqual(fields['product_rev'],'A1.')
        self.assertEqual(fields['serial'],'000001')
        with self.assertRaises(ValueError): decode_qr(raw)
        for index in (0,8,21,25,29,34):
            with self.subTest(index=index),self.assertRaises(ValueError):
                decode_nf55g_label(raw[:index]+'.'+raw[index+1:])

    def build(self,rev='A03',date='2647',serial='000001'):
        return 'US250A-C'+'GXE-009491-101'+rev+date+serial

    def test_fixed_fields_positions_and_leading_zero_serial(self):
        raw=self.build()
        self.assertEqual(len(raw),35)
        fields=decode_nf55g_label(raw)
        self.assertEqual(fields,{'product_name':'US250A-C','item_code':'GXE-009491-101',
            'product_rev':'A03','manufacture_year':'26','manufacture_week':'47','serial':'000001'})

    def test_revision_date_and_serial_vary_without_invented_conversion(self):
        for rev,date,serial in (('A04','2601','000002'),('B01','2753','123456'),('999','0000','000000')):
            fields=decode_nf55g_label(self.build(rev,date,serial))
            self.assertEqual(fields['product_rev'],rev)
            self.assertEqual(fields['manufacture_year']+fields['manufacture_week'],date)
            self.assertEqual(fields['serial'],serial)

    def test_other_model_and_item_code_are_accepted_without_fixed_prefix(self):
        raw=self.build()
        for changed in (raw[:7]+'D'+raw[8:], raw[:21]+'2'+raw[22:],
                        'XS999Z-Q'+'ABC-123456-999'+'B01'+'2753'+'123456'):
            self.assertEqual(len(changed),35)
            fields=decode_nf55g_label(changed)
            self.assertEqual(fields['product_name'],changed[:8])
            self.assertEqual(fields['item_code'],changed[8:22])

    def test_date_and_serial_are_digits_but_revision_need_not_be_numeric(self):
        for raw,error in ((self.build(date='26AA'),'QR_DATE'),(self.build(serial='00000A'),'QR_SERIAL')):
            with self.assertRaisesRegex(ValueError,error): decode_nf55g_label(raw)
        self.assertEqual(decode_nf55g_label(self.build(rev='A03'))['product_rev'],'A03')

    def test_placeholders_and_wrong_length_are_not_real_qr_values(self):
        for raw in (self.build()[:-1],self.build()+'0','US250A-CGXE-009491-101$$$YYWW######'):
            with self.assertRaises(ValueError): decode_nf55g_label(raw)

    def test_generic_decoder_remains_available_for_historical_test_data(self):
        raw='NF55G---'+'A1234567890123'+'A03'+'26'+'01'+'000001'
        self.assertEqual(decode_qr(raw)['product_name'],'NF55G---')
        self.assertEqual(decode_nf55g_label(raw),decode_qr(raw))

    def test_normal_sample_data_has_ten_unique_six_digit_serials(self):
        path=Path(__file__).resolve().parents[1]/'docs/QR_Hardware_Integration_20261123_01/Samples_Rev0/normal_samples.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(len(data['samples']),10)
        for index,item in enumerate(data['samples'],1):
            self.assertEqual(len(item['raw']),35)
            self.assertEqual(decode_nf55g_label(item['raw'])['serial'],'{:06d}'.format(index))
        self.assertEqual(len({item['raw'] for item in data['samples']}),10)

    def test_sample_serial_range_is_not_a_production_whitelist(self):
        for serial in ('000011','123456','999999'):
            self.assertEqual(decode_nf55g_label(self.build(serial=serial))['serial'],serial)
