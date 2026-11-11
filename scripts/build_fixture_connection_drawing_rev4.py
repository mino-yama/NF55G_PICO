"""Rev.4接続・GPIO・Type_C2改造手順図を生成する。旧版とメーカー原典は変更しない。"""
from pathlib import Path
import math
from html import escape
import pymupdf as fitz
import base64
import io
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'drawings' / 'NF55G_Fixture_20261111_Rev4'
OUT.mkdir(parents=True, exist_ok=True)
W, H = 842, 595
BLUE, GREEN, AMBER, INK, LIGHT = '#245b83', '#287a60', '#aa650b', '#203243', '#eef3f7'
FONT = 'C:/Windows/Fonts/msgothic.ttc'
font = fitz.Font(fontfile=FONT)
doc = fitz.open()


def rgb(color):
    return tuple(int(color[i:i+2], 16) / 255 for i in (1, 3, 5))


class Sheet:
    def __init__(self, number, subtitle):
        self.number = number
        self.page = doc.new_page(width=W, height=H)
        self.page.insert_font(fontname='jp', fontfile=FONT)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 {W} {H}">', '<rect width="842" height="595" fill="white"/>']
        self.text(24, 29, 'NF55G 試験治具 接続・GPIO割付図', 18)
        self.text(24, 50, subtitle, 11, BLUE)
        self.text(600, 27, 'NF55G-FIX-001 / Rev.4', 10)
        self.text(600, 44, f'2026-11-11  |  A4横  |  {number}/5', 10)
        self.line([(24, 63), (818, 63)])
        self.line([(24, 565), (818, 565)])
        self.text(24, 581, '実機確認直前に改造を案内 / 今は未施工 / 現物照合・給電保護確認後に実施', 9, AMBER)
        self.text(741, 581, f'Rev.4   {number}/5', 9)

    def text(self, x, y, value, size=10, color=INK):
        self.page.insert_text((x, y), value, fontname='jp', fontsize=size, color=rgb(color))
        self.svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-family="MS Gothic, Noto Sans CJK JP, sans-serif">{escape(value)}</text>')

    def rect(self, x, y, w, h, color=BLUE, fill=LIGHT, dash=False):
        self.page.draw_rect(fitz.Rect(x, y, x+w, y+h), color=rgb(color), fill=rgb(fill), width=1, dashes='[5 3]' if dash else None)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" stroke="{color}" fill="{fill}" stroke-width="1"'+ (' stroke-dasharray="5 3"' if dash else '') + '/>')

    def line(self, points, color=BLUE, dash=False, arrows=False):
        for a, b in zip(points, points[1:]):
            self.page.draw_line(a, b, color=rgb(color), width=1.3, dashes='[5 3]' if dash else None)
        path = ' '.join(f'{x},{y}' for x, y in points)
        self.svg.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="1.3"'+ (' stroke-dasharray="5 3"' if dash else '') + '/>')
        if arrows:
            for end, prev in [(points[-1], points[-2]), (points[0], points[1])]:
                angle = math.atan2(prev[1]-end[1], prev[0]-end[0])
                for delta in (-0.45, 0.45):
                    tip = (end[0]+6*math.cos(angle+delta), end[1]+6*math.sin(angle+delta))
                    self.line([end, tip], color)

    def box(self, x, y, w, h, title, lines, proposed=False):
        color = GREEN if proposed else BLUE
        self.rect(x, y, w, h, color, '#f0f8f4' if proposed else LIGHT, proposed)
        self.text(x+10, y+19, title, 11, color)
        for i, value in enumerate(lines):
            self.text(x+10, y+37+i*14, value, 9)

    def table(self, x, y, widths, rows, heights=None, size=9):
        for ri, row in enumerate(rows):
            height = heights[ri] if heights else 21
            xx = x
            for ci, (value, width) in enumerate(zip(row, widths)):
                self.rect(xx, y, width, height, '#b9c8d3', LIGHT if ri == 0 else '#ffffff')
                for li, text in enumerate(value.split('\n')):
                    self.text(xx+6, y+14+li*13, text, size, BLUE if ri == 0 else INK)
                xx += width
            y += height
        return y

    def finish(self):
        self.svg.append('</svg>')
        path = OUT / f'NF55G_Fixture_Rev4_sheet{self.number}.svg'
        path.write_text('\n'.join(self.svg), encoding='utf-8')


s = Sheet(1, '01  全体接続図：USBポートを回路名で固定割当て')
s.box(24, 98, 106, 80, 'ATE', ['試験工程・測定条件', '製品PASS/FAIL判定'])
s.box(158, 98, 130, 80, 'PIA5100', ['GPIB - RS232C', '変換（既存経路）', 'RS232C → CH0'])
s.box(650, 98, 168, 80, 'NF55G', ['CN24 : DF11-4DS-2C', '端子番号・線順は別途照合'])
s.line([(130, 136), (158, 136)], arrows=True)
s.text(131, 92, 'GPIB', 8)
s.rect(14, 199, 814, 172, BLUE, '#f5f8fb')
s.text(28, 218, 'Pico-Quad-Expander', 12, BLUE)
s.text(28, 234, '4基板の共通ベース / GPIOを共有', 9, BLUE)
s.box(310, 210, 220, 64, 'Pico-2CH-RS232', ['CH0 : ATE / 115200 / 8N1', 'CH1 : NF55G / 38400 / 8E1'])
s.line([(288, 136), (299, 136), (299, 242), (310, 242)], arrows=True)
s.text(310, 185, 'RS232C / CH0', 8)
s.line([(650, 136), (556, 136), (556, 242), (530, 242)], arrows=True)
s.text(565, 125, 'RS232C / CH1', 8)
s.box(310, 300, 220, 63, 'Raspberry Pi Pico 2', ['UART0 : GP0 TX / GP1 RX', 'UART1 : GP4 TX / GP5 RX'])
s.line([(420, 274), (420, 300)], arrows=True)
s.text(433, 290, '3.3V UART × 2CH', 8)
s.box(28, 253, 230, 100, 'RTC : Pico-RTC-DS3231', ['GP20 SDA / GP21 SCL', 'I2C0 / 0x68 / 100kHz', 'Expanderヘッダー経由'])
s.line([(258, 330), (310, 330)], arrows=True)
s.text(270, 321, 'I2C', 9)
s.box(584, 253, 230, 100, 'SD : ADA-5703 PiCowbell', ['GP16 MISO / GP17 CS', 'GP18 SCK / GP19 MOSI / SPI0', 'GP4/GP5はSD基板から分離 ※1'])
s.line([(530, 330), (584, 330)], arrows=True)
s.text(546, 321, 'SPI', 9)
s.box(320, 415, 200, 85, '追加 : RP2350-USB-C', ['Type_C1 : DMM 7355', 'Type_C2 : QR BCR-TC2D1BK', '下位UARTピン : 未確定'], True)
s.line([(420, 363), (420, 415)], GREEN, True, True)
s.text(430, 387, 'GP8 TX / GP9 RX / GND', 9, GREEN)
s.text(430, 401, 'PIO双方向UART案 / 115200 8N1候補', 8, GREEN)
s.box(702, 380, 116, 71, 'QRリーダー', ['BCR-TC2D1BK', 'Type_C2 / PIO HID'], True)
s.box(702, 473, 116, 71, 'DMM : 7355', ['USB Type-B', 'Type_C1 / USB Host'], True)
s.line([(520, 438), (600, 438), (600, 406), (702, 406)], GREEN, True, True)
s.text(548, 428, 'Type_C2 / PIO-USB', 8, GREEN)
s.line([(520, 478), (620, 478), (620, 508), (702, 508)], GREEN, True, True)
s.text(548, 470, 'Type_C1 / Native USB', 8, GREEN)
s.box(24, 400, 239, 100, '電源・保守（系統は詳細設計）', ['デバッグ : PC → Type_C1のみ', 'QR / DMM : Expander分岐5V / 最大1A', 'PCとExpanderの同時給電は禁止', '機器接続時はPCを外す / GND共通'])
s.text(24, 520, '青：現行のExpander経由接続   緑破線：追加案   ※スロット位置・積層順・電源配線は示していない。', 9)
s.text(24, 539, '※1 ADA-5703内蔵RTC / STEMMAのGP4/GP5を分離。詳細は2・3枚目。Type_C2改造・手順は4・5枚目。', 9, AMBER)
s.finish()

s = Sheet(2, '02  Pico 2 GPIO割付・基板間信号：物理ピン番号はPico 2の40ピンヘッダー基準')
rows = [['用途', 'Pico GPIO', '物理pin', '方向 ※2', '接続先・条件', '区分'],
 ['ATE UART0', 'GP0 / GP1', '1 / 2', 'TX / RX', 'RS232 CH0 → PIA5100 / 115200 8N1', '現行'],
 ['NF55G UART1', 'GP4 / GP5', '6 / 7', 'TX / RX', 'RS232 CH1 → NF55G / 38400 8E1', '現行'],
 ['RTC I2C0', 'GP20', '26', '双方向', 'DS3231 SDA / address 0x68', '現行'],
 ['RTC I2C0', 'GP21', '27', '出力', 'DS3231 SCL / 100kHz', '現行'],
 ['SD SPI0', 'GP16', '21', '入力', 'ADA-5703 MISO', '現行'],
 ['SD SPI0', 'GP17', '22', '出力', 'ADA-5703 CS', '現行'],
 ['SD SPI0', 'GP18', '24', '出力', 'ADA-5703 SCK', '現行'],
 ['SD SPI0', 'GP19', '25', '出力', 'ADA-5703 MOSI', '現行'],
 ['追加HOST UART', 'GP8', '11', 'TX出力', '→ HOST UART RX（下位GPIO未定）', '候補'],
 ['追加HOST UART', 'GP9', '12', 'RX入力', '← HOST UART TX（下位GPIO未定）', '候補'],
 ['追加HOST GND', 'GND', '13（候補）', '基準', 'HOST GND / 絶縁要否は配線条件で確認', '候補'],
 ['Pico電源', 'VSYS', '39', '電源', '治具の既存給電 / 追加側はExpander 5V分岐', '要照合'],
 ['USB電源', 'VBUS', '40', '電源', 'USB 5V系 / 外部5Vとの逆流防止を設計', '要照合'],
 ['3.3V電源', '3V3(OUT)', '36', '電源', '周辺回路用 / USBの5V給電には使わない', '端子参照'],
 ['電源GND', 'GND', '38（例）', '基準', '複数GNDあり / 実ハーネスで端子確定', '端子参照']]
s.table(24, 80, [100, 84, 78, 64, 390, 78], rows, size=9)
s.text(24, 455, '※2 方向はPico 2から見た信号方向。TX同士・RX同士では接続しない。3.3V UARTとRS232Cを区別する。', 9)
s.text(24, 474, '重要：GP8/GP9のハードUART機能もUART1。NF55G用UART1と独立しないため、追加側はPIO方式を検討。', 9, AMBER)
s.text(24, 493, '現行QR試作はGP9受信のみ、GP8はHigh固定。双方向化には送信処理・PIO資源・本番統合の追加設計が必要。', 9)
s.text(24, 512, 'GP4/GP5はNF55G専用。ADA-5703の内蔵PCF8523 / STEMMA QTは使用しない。分離箇所・導通を検査する。', 9)
s.text(24, 531, '各基板はPico-Quad-Expander経由。全スロットで同じGPIOを共有するため、割付と競合条件は変わらない。', 9)
s.text(24, 550, '固定USB割当て：RP2350-USB-C回路図 Type_C1 → 7355 / Type_C2 → BCR-TC2D1BK。', 8, GREEN)
s.finish()

s = Sheet(3, '03  追加発注・改造範囲の説明：既存接続と候補を分け、加工承認前に現物で確定する')
rows = [['対象', '説明・追加する作業', '確定度 / 発注前の確認'],
 ['既存RS232 / RTC / SD', '各基板はPico-Quad-Expanderのヘッダー経由で接続。\nNF55G CN24とPIA5100側は既存ハーネスを照合。', 'ユーザー指定の現行接続\nスロット位置・向き・積層順は未記録'],
 ['A : SD基板の分離', 'ADA-5703のGP4/GP5をPicoバスから物理分離。\n内蔵RTC / STEMMAをNF55G UARTへ接続しない。', '既存治具は分離済み申告あり\n再発注品にも処置・導通検査が必要'],
 ['B : HOSTの追加配線', 'Expander側からGP8 / GP9 / GNDをHOSTへ引き出す案。\nHOSTは別途固定し、RX / TX / GNDを接続。', '引出し位置・PIO・下位側ピンは未確定\n既存ヘッダー利用 / コネクタ追加の要否を確認'],
 ['C : USBデータ接続', 'Type_C1 → ADCMT 7355 (USB Type-B)。\nType_C2 → BCR-TC2D1BK (USB Type-C)。', '回路名と機器割当ては固定\nUSBハブは標準構成に含めない'],
 ['D : USBホスト条件', 'Type_C2のR13・CCを改造する案。\nD+はGPIO12 / D-はGPIO13（原典再照合）。', 'USB-C専用の改造図は4枚目\n実機直前の施工・確認手順は5枚目'],
 ['E : 5V給電の追加', 'デバッグはPC、機器使用時は外部5Vアダプタの\nExpander分岐。追加側は最大1A（申告値）。', 'PC給電と外部5Vを同時直結しない\n保護・負荷電流・取出し端子は現物照合'],
 ['F : 筐体・保守接続', 'HOST固定、USBケーブル保持、保守用USBアクセス、\n必要に応じパネル中継・内部ハーネスを追加。', '基板寸法・取り付け・コネクタ位置を実測\n加工図・部品型番・数量は後続で確定']]
s.table(24, 80, [146, 352, 296], rows, heights=[23]+[46]*7, size=9)
s.rect(24, 437, 794, 77, AMBER, '#fff8ed')
s.text(34, 455, '発注説明：追加するのは「USB HOST基板・双方向UART配線・USB接続部品・電源／固定部品」。', 10, AMBER)
s.text(34, 474, 'コネクタの撤去やUSB信号線の直付けが必要とは、現時点では確定していない。', 10)
s.text(34, 493, '必要な場合は、対象端子・加工箇所・配線表・検査方法を追記した製造用Rev.を作成してから加工する。', 9)
s.text(24, 535, '残確認：Host用部品サイズ・電源保護、二系統Host同時動作、下位UART、CN24/RS232、SD分離。', 9)
s.text(24, 551, '管理：HW-01 / USB-SUB-01をOpen維持。今回の図面作成では機器への接続・改造・プログラム配置を行っていない。', 9)
s.finish()


# Type_C2の改造回路とメーカー位置写真。原典画像自体は変更しない。
s = Sheet(4, '04  Type_C2 Host専用化：改造箇所・回路対応（未施工 / 実機試験直前に案内）')
s.text(24, 88, '回路図の正しい対応：D+ = GPIO12 / D- = GPIO13', 11, BLUE)
s.text(24, 106, '赤：撤去   緑：新規56kΩ   青：維持   図は改造対象の説明、縮尺なし', 8.5)
RED = '#b72d32'
# D+ / D-直列抵抗とDevice用プルアップ
for yy, gp, rr, net, pins in [(143, 'GPIO12 (D+)', 'R12 / 27R', 'DB_P', 'DP1 / DP2'),
                              (217, 'GPIO13 (D-)', 'R11 / 27R', 'DB_N', 'DN1 / DN2')]:
    s.text(24, yy-10, gp, 9)
    s.line([(24, yy), (154, yy)])
    s.rect(154, yy-6, 58, 12, BLUE, '#ffffff')
    s.text(150, yy-12, rr, 8.5)
    s.line([(212, yy), (410, yy)])
    s.text(265, yy-8, net, 9)
    s.text(418, yy+3, 'Type_C2 '+pins, 8.5)
s.line([(115, 143), (115, 162)], RED, True)
s.rect(107, 162, 16, 24, RED, '#fff0f0')
s.line([(115, 186), (115, 194)], RED, True)
s.text(132, 178, 'R13 1.5kΩ : 撤去 / 3V3へ', 9, RED)
s.text(24, 243, 'R10（D-側プルアップ候補）は未実装を維持', 9, AMBER)
# CC1/CC2をそれぞれ独立したRpへ。Rdは撤去対象として示す。
for yy, cc, rp, rd in [(282, 'CC1 / A5', 'R21', 'R19'), (350, 'CC2 / B5', 'R20', 'R18')]:
    s.text(24, yy-7, '5V / VSYS', 8.5)
    s.line([(24, yy), (154, yy)], GREEN)
    s.rect(154, yy-6, 58, 12, GREEN, '#f0f8f4')
    s.text(147, yy-12, rp+' 56kΩ / 1%', 9, GREEN)
    s.line([(212, yy), (410, yy)], GREEN)
    s.text(418, yy+3, 'Type_C2 '+cc, 9, GREEN)
    s.line([(275, yy), (275, yy+14)], RED, True)
    s.rect(269, yy+14, 12, 20, RED, '#fff0f0')
    s.line([(264, yy+12), (286, yy+36)], RED)
    s.line([(286, yy+12), (264, yy+36)], RED)
    s.text(295, yy+29, rd+' 5.1kΩ → 撤去 / GND側', 8.5, RED)
# メーカーUSB-C専用FAQの位置写真をPDFとSVGへ同じ原図で埋め込む。
photo = ROOT / 'reference/USB_Host_SubMCU_Host_Conditions_20261111/Waveshare_USB_C_FAQ_pullup.webp'
# WebP原図を画素の加工なしでPNG形式へ変換し、PDF/SVGへ埋め込む。
with Image.open(photo) as source_image:
    image_buffer = io.BytesIO()
    source_image.save(image_buffer, format='PNG')
    photo_png = image_buffer.getvalue()
s.page.insert_image(fitz.Rect(592, 78, 806, 376), stream=photo_png)
s.svg.append('<image x="592" y="78" width="214" height="298" href="data:image/png;base64,'+base64.b64encode(photo_png).decode('ascii')+'"/>')
s.text(580, 388, 'メーカーFAQの赤丸 = D+プルアップ撤去位置', 8)
rows = [['箇所', '改造前 / 部品位置', '実施内容', '維持するもの・確認'],
 ['R13', '1.5kΩ / 写真の赤丸', '取り外す（D+側、GPIO12）', 'Type_C2のDevice利用は不可になる'],
 ['R19 / R18', 'CC1 / CC2の0=Sink', '両方取り外す（原典5.1kΩ）', '既存抵抗を1側へ移さない'],
 ['R21 / R20', 'CC1 / CC2の1=Source', '各56kΩ・1%を新規実装', '部品サイズは現物照合 / 両側実装しない'],
 ['R10', 'D-側 / 原典NC', '未実装を維持', '実装があれば独断で進めず照合'],
 ['R11 / R12', 'D線直列27Ω', '変更しない', 'D+ / D-を逆にしない'],
 ['R5 / R6', 'Type_C1 CC各5.1kΩ', '今回変更しない', '原典はGND接続 / VSYS接続ではない']]
s.table(24, 400, [91, 176, 256, 271], rows, heights=[21]*7, size=8.5)
s.finish()

s = Sheet(5, '05  実機確認直前の改造・受入手順：案内前に施工しない / 作業結果を記録する')
s.box(24, 82, 387, 85, 'デバッグ時：PC給電', ['PC → Type_C1 / Type_C2は空', 'Expanderの外部5Vは切り離す', 'PCと外部5Vの同時直結はしない'])
s.box(431, 82, 387, 85, '機器使用時：外部アダプタ給電', ['外部5V → Expander分岐 → 下位基板5V / GND', '最大1Aはユーザー申告。保護・実負荷は確認待ち', 'Type_C1に7355、Type_C2にQR。PCは外す'], True)
rows = [['順', '作業と判定点', '記録欄'],
 ['0', 'Host用FW・ログ経路・分岐の保護条件を準備。実機確認前に改造を案内する。\n現物と4枚目の部品位置、56kΩ部品サイズ・値を照合してから着手。', '案内 / 作業者 / 部品確認\n____________________'],
 ['1', 'PC USB・外部アダプタ・QR・7355・治具UARTを全て外して無給電にする。\nType_C1とExpanderの給電切替えは、必ず電源OFFで行う。', '無給電確認\n____________________'],
 ['2', '変更前の写真を保存。4枚目のメーカー赤丸と現物を照合し、R13を取り外す。\n位置が一致しなければ中断。別の抵抗を推定して除去しない。', 'R13 / 写真\n____________________'],
 ['3', 'CC1=R19、CC2=R18の0側抵抗を外す。1側R21 / R20へ各56kΩ・1%を実装。\n5.1kΩの移設・0Ω短絡・0側と1側の両側実装はしない。', 'CC1 / CC2\n____________________'],
 ['4', 'R11 / R12とType_C1側は維持。はんだブリッジ・剥離・残片を目視確認。\n変更後写真を保存。DB_N / DN1の微細端子プロービングは要求しない。', '外観 / 写真\n____________________'],
 ['5', 'QR / 7355なし、1系統だけで給電し、5V / 3V3と異常消費・リセットを確認。\n既に測れる電源端子・ブレークアウトを使用。異常なら電源OFFして中断。', '5V / 3V3 / 電流\n____________________'],
 ['6', 'QR試験はPCを外し、無給電でType_C2にQRを接続後、保護したExpander 5Vを投入。\nHost FW版・列挙・読取・電流を記録。別工程で7355をType_C1へ接続する。', 'FW版 / 結果\n____________________']]
s.table(24, 185, [30, 610, 154], rows, heights=[23]+[43]*7, size=9)
s.text(24, 526, '注意：両VBUSはVSYS直結。初期は固定機器・無給電で配線し、活線挿抜や汎用Sourceの合格としない。', 9, AMBER)
s.text(24, 543, '最大1Aは保護の実測ではない。供給能力・過電流・逆流、USB Hostの同時動作は別途受入。', 9)
s.text(24, 557, '参照：USB_Host_SubMCU_Host_Circuit_Conditions_Rev0_20261111.md / USB-SUB-01・02はOpen継続', 8)
s.finish()

pdf = OUT / 'NF55G_Fixture_Connection_GPIO_Rev4_20261111.pdf'
doc.subset_fonts()
doc.save(pdf, garbage=4, deflate=True)
doc.close()
check = fitz.open(pdf)
for n, page in enumerate(check, 1):
    page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6)).save(OUT / f'preview_sheet{n}.png')
    assert len(page.get_text()) > 300
print(f'Created {pdf} ({len(check)} sheets), SVG and PNG previews')
