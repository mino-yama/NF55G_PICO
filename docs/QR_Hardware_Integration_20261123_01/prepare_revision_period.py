"""提示された実原文を基に、旧サンプルと別版の試験データを保存する。"""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.qr_reader import decode_nf55g_label

raw='US250A-CGXE-009491-101A1.2601000001'
fields=decode_nf55g_label(raw)
out=Path(__file__).resolve().parent/'Samples_Rev1'
out.mkdir(exist_ok=False)
samples=[]
for number in range(1,11):
    text=raw[:29]+f'{number:06d}'
    samples.append(dict(raw=text,fields=decode_nf55g_label(text),serial=f'{number:06d}'))
(out/'normal_samples.txt').write_text('\n'.join(item['raw'] for item in samples)+'\n',encoding='ascii')
(out/'normal_samples.json').write_text(json.dumps(dict(
    source='2026-11-23 user supplied actual QR text; serials 000002..000010 are generated test data',
    purpose='QR receive/parse test only; not manufacturing or SS write instructions',
    supplied_raw=raw,sample_count=10,model_item_revision_not_fixed=True,samples=samples),ensure_ascii=False,indent=2),encoding='utf-8')
print(fields)
