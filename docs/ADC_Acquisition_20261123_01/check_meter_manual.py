"""7355のオーバーレンジ・応答形式を原典PDFから別ファイルへ抽出。原典は変更しない。"""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SOURCE = ROOT / 'reference/ADCMT_7355_20261104/7355-ope--foa-00000201a00-e.pdf'

if __name__ == '__main__':
    folder = OUT / 'Manual_Evidence'
    folder.mkdir(exist_ok=True)
    reader = PdfReader(SOURCE)
    hits = []
    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        keys = [key for key in ('overrange', 'over-range', 'over range', '9.999', '9.99', 'E+37', 'E+38') if key.lower() in text.lower()]
        if keys:
            (folder / ('page_%03d.txt' % (index + 1))).write_text(text, encoding='utf-8')
            hits.append({'pdf_page': index + 1, 'keywords': keys})
    (folder / 'manifest.json').write_text(json.dumps({'source': str(SOURCE.relative_to(ROOT)),
        'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'hits': hits}, indent=2), encoding='utf-8')
    print(json.dumps(hits))
