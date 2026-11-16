"""取得した既知35文字テスト1件だけをAlt数字列と期待HID列の二方式で照合する。"""
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent
capture=json.loads((base/'scan.json').read_text(encoding='utf8'))
assert capture['status']=='raw_capture_only' and not capture['errors']
assert capture['records']<capture['record_capacity']==1024
assert [e['seq'] for e in capture['events']]==list(range(capture['records']))
boot=bytes.fromhex(capture['events'][0]['data_hex']).decode('ascii')
identity=bytes.fromhex(capture['events'][1]['data_hex']).decode('ascii')
assert boot=='qr-uart-20261114.1' and identity=='A06FEA01012EC137'
reports=[bytes.fromhex(e['data_hex']) for e in capture['events'] if e['kind']=='hid_report']
assert all(len(r)==8 for r in reports)
keys={0x62:'0',**{0x58+i:str(i) for i in range(1,10)}}
previous=set();alt=False;digits='';groups=[];text=[];enter_count=0;terminated=False
for report in reports:
 modifier,reserved=report[:2]
 assert reserved==0
 pressed=set(report[2:])-{0}
 assert len(pressed)<=1
 assert modifier in (0,4)
 if alt and modifier==0:
  assert len(digits)==5 and digits.isdecimal()
  value=int(digits)
  assert 32<=value<=126
  groups.append(digits);text.append(chr(value));digits=''
 if modifier==4:
  assert not terminated
  for key in pressed-previous:
   assert key in keys
   digits+=keys[key]
 elif pressed-previous:
  assert pressed=={0x28} and not terminated and not digits
  terminated=True;enter_count+=1
 alt=modifier==4
 previous=pressed
assert not alt and not digits and not previous and reports[-1]==bytes(8)
assert terminated and enter_count==1
actual=''.join(text)
expected=(base.parent/'test_data/expected_35chars.txt').read_bytes()
assert len(expected)==35 and actual.encode('ascii')==expected
# 期待文字列を別経路でHID入力列へ展開し、空報告・Enterも含め全件一致を確認。
key_for_digit={value:key for key,value in keys.items()}
expected_reports=[]
for ch in expected:
 for digit in f'{ch:05d}':
  expected_reports += [bytes([4,0,key_for_digit[digit],0,0,0,0,0]),bytes([4,0,0,0,0,0,0,0])]
 expected_reports.append(bytes(8))
expected_reports += [bytes([0,0,0x28,0,0,0,0,0]),bytes(8),bytes(8)]
assert reports==expected_reports
result={'scope':'this one known test scan only; offline analysis, not device firmware decoding',
 'fw':boot,'board_id':identity,'input_records':capture['records'],
 'hid_reports':len(reports),'observed_alt_decimal_groups':groups,
 'expected_ascii':expected.decode('ascii'),'actual_ascii':actual,
 'ascii_length':len(actual),'exact_35char_match':True,
 'independent_expected_hid_sequence_match':True,'enter_suffix_count':enter_count,
 'last_report_all_keys_released':True,'raw_sha256':capture['source_sha256'],
 'payload_sha256':hashlib.sha256(actual.encode('ascii')).hexdigest(),
 'startup_warning':capture['warnings'],'uart_tail_completeness':capture['tail_completeness'],
 'hardware_acceptance':False,'production_decoder_implemented':False}
(base/'decoded_35chars_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(base/'decoded_35chars.txt').write_bytes(actual.encode('ascii'))
print(json.dumps(result,ensure_ascii=False,indent=2))
