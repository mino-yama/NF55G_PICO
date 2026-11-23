"""ユーザー指定のREV3銘板図を原典不変で保存・hash照合し、確認用に抽出する。"""
import hashlib
import json
from pathlib import Path
import shutil
from pypdf import PdfReader
import pymupdf

OUT=Path(__file__).resolve().parent/'Drawing_Evidence'
SOURCE=Path(r'Z:\開発技術部\A-共有領域\技術情報\DRAWING\NF\NF55G\構造設計\構造図面\銘板\REV3\NF55802-G_03.pdf')

if __name__=='__main__':
    OUT.mkdir(exist_ok=False)
    target=OUT/SOURCE.name
    shutil.copyfile(SOURCE,target)
    digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
    reader=PdfReader(target)
    document=pymupdf.open(target)
    for index,page in enumerate(reader.pages):
        (OUT/('page_%02d.txt'%(index+1))).write_text(page.extract_text() or '',encoding='utf-8')
        document[index].get_pixmap(matrix=pymupdf.Matrix(2,2)).save(OUT/('page_%02d.png'%(index+1)))
    (OUT/'manifest.json').write_text(json.dumps({'source':str(SOURCE),'copy':target.name,
        'source_sha256':digest,'copy_matches':True,'pages':len(reader.pages)},ensure_ascii=False,indent=2),encoding='utf-8')
    print('DRAWING_COPIED_VERIFIED',len(reader.pages),digest)
