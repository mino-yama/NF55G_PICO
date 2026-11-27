from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_ate_command_list_docx as b
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT

import argparse
parser = argparse.ArgumentParser(description='ATEコマンド一覧を既存のA3横形式で生成する。')
parser.add_argument('--name', default='ATE_Command_List_for_Test_Program_Rev3_20261126')
name = parser.parse_args().name
target = ROOT / 'docs' / (name + '.docx')
b.build_docx(ROOT / 'docs' / (name + '.md'), target)
doc = Document(target)
# 直近の閲覧用A3横版を引き継ぎ、長いコマンドと応答を表内で読める幅にする。
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(16.5354), Inches(11.6931)
for s in ('Title', 'Heading 1', 'Heading 2', 'Heading 3'):
    doc.styles[s].font.color.rgb = RGBColor(0, 0, 0)
# Word既定スタイル由来のタイトル罫線を取り除く。
for node in doc.styles.element.xpath('.//w:pBdr'):
    node.getparent().remove(node)
for node in doc.element.xpath('.//w:pBdr'):
    node.getparent().remove(node)
first = doc.paragraphs[0]
first.style = doc.styles['Title']
for run in first.runs:
    run.font.color.rgb = RGBColor(0, 0, 0)
for p in doc.paragraphs:
    if p.style.name.startswith('Heading'):
        p.paragraph_format.keep_with_next = True
    for run in p.runs:
        if run.font.size and run.font.size.pt < 10:
            run.font.size = Pt(10)
usable = int((sec.page_width - sec.left_margin - sec.right_margin) / 635)
for table in doc.tables:
    headers = [c.text for c in table.rows[0].cells]
    weights = b.markdown_table_widths(headers)
    # 手順表は短い番号欄とコマンド・応答説明欄に幅を配分する。
    if headers[0] == '順序':
        weights = [650, 6900, 7600] if len(headers) == 3 else [650, 4800, 4900, 4900]
    widths = [round(usable * w / sum(weights)) for w in weights]
    b.set_table_grid(table, widths)
    borders = OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        edge = OxmlElement('w:' + side)
        for key, val in (('val','single'),('sz','4'),('color','D9D9D9')):
            edge.set(qn('w:' + key), val)
        borders.append(edge)
    table._tbl.tblPr.append(borders)
    for row in table.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cell.paragraphs:
                p.paragraph_format.line_spacing = 1.05
                for run in p.runs:
                    run.font.size = Pt(10)
doc.save(target)
print(target)
