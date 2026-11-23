"""製造号機000001～000010の正常形式サンプル。例示型式/REV/年週を製品条件へ固定しない。"""
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
from src.qr_reader import decode_nf55g_label


if __name__=='__main__':
    target=OUT/'Samples_Rev0'
    target.mkdir(exist_ok=False)
    examples={'product_name':'US250A-C','item_code':'GXE-009491-101',
              'product_rev':'A03','manufacture_year':'26','manufacture_week':'01'}
    samples=[]
    for index in range(1,11):
        serial='{:06d}'.format(index)
        raw=examples['product_name']+examples['item_code']+examples['product_rev']+examples['manufacture_year']+examples['manufacture_week']+serial
        fields=decode_nf55g_label(raw)
        assert fields['serial']==serial and len(raw)==35
        samples.append({'serial':serial,'raw':raw,'fields':fields})
    result={'purpose':'正常形式の読取/分解試験用。実製造Lot/校正/SS書込み指定ではない。',
            'sample_count':10,'serial_start':'000001','serial_end':'000010',
            'example_values_only':examples,'model_item_revision_not_fixed':True,'samples':samples}
    (target/'normal_samples.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (target/'normal_samples.txt').write_text('\n'.join(item['raw'] for item in samples)+'\n',encoding='ascii')
    print('CREATED',len(samples),'NORMAL_SAMPLE_RECORDS',flush=True)
