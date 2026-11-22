"""7355原典PDFを変更せず、READ/USB終端の該当ページを別フォルダへ抽出する。"""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'reference/ADCMT_7355_20261104/7355-ope--foa-00000201a00-e.pdf'
OUT = Path(__file__).resolve().parent / 'Manual_Check'
OUT.mkdir(exist_ok=False)
reader = PdfReader(SOURCE)
hits = []
for index, page in enumerate(reader.pages):
    text = page.extract_text() or ''
    keys = [key for key in ('READ?', 'CRLF', 'output queue', 'terminator') if key.lower() in text.lower()]
    if keys:
        (OUT / ('page_%03d.txt' % (index + 1))).write_text(text, encoding='utf-8')
        hits.append({'pdf_page': index + 1, 'keywords': keys})
manifest = {'source': str(SOURCE), 'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'pages': len(reader.pages), 'hits': hits}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest), flush=True)
