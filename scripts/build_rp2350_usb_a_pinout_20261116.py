"""DMM用RP2350-USB-Aの端子位置とUART監視配線を描く。原典は変更しない。"""
from pathlib import Path
from html import escape
import hashlib
import json
import math
import fitz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/drawings/RP2350_USB_A_Pinout_20261116_Rev0'
OUT.mkdir(parents=True, exist_ok=True)
FONT = 'C:/Windows/Fonts/msgothic.ttc'
W, H = 842, 595
INK, BLUE, PURPLE, RED, GREEN, GRAY = '#213244', '#176a9b', '#7735a4', '#bf3434', '#18765e', '#647483'
doc = fitz.open()
LEFT = [(18, '5V / VSYS'), (17, 'GND'), (16, '3V3'), (15, 'GP29'),
        (14, 'GP28'), (13, 'GP27'), (12, 'GP26'), (11, 'GP10'), (10, 'GP9')]
RIGHT = [(i + 1, 'GP' + str(i)) for i in range(9)]
assert {n for n, _ in LEFT + RIGHT} == set(range(1, 19))
assert len({n for n, _ in LEFT + RIGHT}) == 18


def rgb(c):
    return tuple(int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))


class Sheet:
    def __init__(self, num, subtitle):
        self.num = num
        self.page = doc.new_page(width=W, height=H)
        self.page.insert_font(fontname='jp', fontfile=FONT)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 {W} {H}">',
                    '<rect width="842" height="595" fill="white"/>']
        self.text(25, 29, 'RP2350-USB-A 端子位置・UART監視配線', 19)
        self.text(25, 51, subtitle, 11, BLUE)
        self.text(634, 28, 'DMM 7355用 / Rev.0', 11)
        self.text(634, 48, f'2026-11-16 / A4横 / {num}/3', 9)
        self.line([(25, 65), (817, 65)], GRAY)
        self.line([(25, 563), (817, 563)], GRAY)
        self.text(25, 581, '配線準備図 / はんだ付けは試作完了後 / 実機の向き・シルク・給電条件を照合', 9, GRAY)
        self.text(760, 581, f'{num} / 3', 10, GRAY)

    def text(self, x, y, value, size=10, color=INK):
        self.page.insert_text((x, y), value, fontname='jp', fontsize=size, color=rgb(color))
        self.svg.append(f'<text x="{x}" y="{y}" font-family="MS Gothic, Noto Sans CJK JP, sans-serif" font-size="{size}" fill="{color}">{escape(value)}</text>')

    def rect(self, x, y, w, h, fill='white', stroke=GRAY, dash=False):
        self.page.draw_rect(fitz.Rect(x, y, x+w, y+h), color=rgb(stroke), fill=rgb(fill), width=1,
                            dashes='[4 3]' if dash else None)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}"'+(' stroke-dasharray="4 3"' if dash else '')+'/>')

    def line(self, pts, color=BLUE, arrow=False):
        for a, b in zip(pts, pts[1:]):
            self.page.draw_line(a, b, color=rgb(color), width=1.5)
        self.svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="1.5"/>')
        if arrow:
            x,y=pts[-1]; px,py=pts[-2]; angle=math.atan2(py-y,px-x)
            for delta in [-0.45,0.45]:
                self.line([(x,y),(x+8*math.cos(angle+delta),y+8*math.sin(angle+delta))],color)

    def finish(self):
        self.svg.append('</svg>')
        (OUT/f'RP2350_USB_A_Pinout_Rev0_sheet{self.num}.svg').write_text('\n'.join(self.svg),encoding='utf-8')


s = Sheet(1, '01  部品面の位置図：USB-Cが上 / USB-Aが下 / 縮尺なし')
s.text(30, 88, 'P1端子番号', 11, BLUE)
s.text(145, 88, '信号名', 11, BLUE)
s.text(414, 88, 'P1端子番号 / 信号名', 11, BLUE)
s.rect(220, 113, 168, 309, '#eaf5ef', GREEN)
s.rect(262, 95, 84, 51, '#dfe6ed', GRAY)
s.text(270, 117, 'USB-C', 13)
s.text(266, 133, 'PC書込み', 10)
s.rect(250, 400, 108, 57, '#dfe6ed', GRAY)
s.text(271, 423, 'USB-A', 15)
s.text(265, 442, '7355へ', 12, GREEN)
s.rect(272, 240, 65, 72, '#263c4f', INK)
s.text(280, 268, 'RP2350', 11, '#ffffff')
s.text(281, 288, '部品面', 11, '#ffffff')
s.rect(246, 194, 43, 24, '#e0e6eb', GRAY)
s.rect(317, 194, 49, 24, '#e0e6eb', GRAY)
s.text(253, 210, 'BOOT', 9, GRAY)
s.text(321, 210, 'RESET', 9, GRAY)
for side, items in [('left', LEFT), ('right', RIGHT)]:
    for row, (num, name) in enumerate(items):
        y=158+28*row
        important = num in (1,2,17,18)
        color = RED if num==18 else INK if num==17 else PURPLE if num==1 else BLUE if num==2 else GRAY
        xpad = 214 if side=='left' else 382
        s.rect(xpad,y-9,12,18,'#ead99d','#8e773d')
        if side=='left':
            s.rect(30,y-11,170,23,'#fff5f2' if num==18 else '#eef5f9' if important else '#f6f7f8',color)
            s.text(40,y+5,f'#{num:02d}',12,color)
            s.text(100,y+5,name,13,color)
            s.line([(200,y),(214,y)],color)
        else:
            s.line([(394,y),(411,y)],color)
            s.rect(411,y-11,158,23,'#f5eefb' if num==1 else '#eef5f9' if important else '#f6f7f8',color)
            s.text(421,y+5,f'#{num:02d}',12,color)
            extra=' / TX' if num==1 else ' / RX' if num==2 else ''
            s.text(472,y+5,name+extra,13,color)
s.rect(591,104,224,154,'#f3f7fb',BLUE)
for y,t,size,c in [(124,'今回のUART監視',13,BLUE),(147,'#01 GP0 → 変換基板 RXD',11,PURPLE),
                    (171,'#17 GND → 変換基板 GND',11,INK),(196,'#02 GP1：今回は未接続',10,BLUE),
                    (219,'監視：115200bps / 8N1',10,INK),(242,'3.3Vロジック / RS232不可',10,INK)]:
    s.text(601,y,t,size,c)
s.rect(591,273,224,133,'#fff6ed','#ba762a')
for i,t in enumerate(['番号の読み方','「#」は回路図P1の端子番号。','「GP」はGPIO番号。','親Picoの40pin番号や、','RP2350 ICの端子番号とは別。']):
    s.text(601,294+22*i,t,12 if i==0 else 10,'#8e551a')
s.text(30,479,'内部専用：GP12=D+ / GP13=D-（USB-A）、GP16=RGB LED。上の18端子には出ていません。',10,BLUE)
s.text(30,500,'電源：#18=5V入力の候補 / #16=3V3。5Vを#16やGPIOへ接続しない。',11,RED)
s.text(30,521,'USB-A VBUS・USB-C VBUS・#18は同一VSYS。外部5VとPC USB給電を同時直結しない。',10,RED)
s.text(30,546,'原典：Waveshare RP2350-USB-A.pdf（P1）、Waveshare_Pinout.jpg。現物の基板版・端子表示で最終照合。',8.5,GRAY)
s.finish()

s = Sheet(2, '02  初回は監視専用 / 親Picoへの双方向接続は後工程')
s.rect(35,97,253,197,'#eef6f1',GREEN)
s.text(48,121,'追加RP2350-USB-A',15,GREEN)
s.text(48,143,'DMM用Host / 部品面位置は1枚目',9)
s.text(48,170,'#01 GP0 / UART TX',12,PURPLE)
s.text(48,212,'#17 GND',12,INK)
s.text(48,248,'#02 GP1は今回未接続',10,BLUE)
s.text(48,271,'USB-A → 7355 USB-B',12,GREEN)
s.rect(501,97,306,197,'#f1f5fb',BLUE)
s.text(516,121,'USB-UART変換基板',15,BLUE)
s.text(516,143,'3.3Vロジック対応のUARTモード',10)
s.text(518,170,'RXD  ← Hostの送信を受信',12,PURPLE)
s.text(518,212,'GND  ― 信号基準を共通化',12,INK)
s.text(516,248,'TXD / 5V / 3V3：接続しない',11,RED)
s.text(516,271,'USB側 → PCで原文ログ保存',11,BLUE)
s.line([(288,166),(501,166)],PURPLE,True)
s.text(322,155,'115200bps / 8N1',11,PURPLE)
s.line([(288,208),(501,208)],INK)
s.text(330,230,'TXD-RXD短絡なし',10,RED)
s.text(36,315,'機能試験時：外部5V→Host #18、GND→#17。HostのPC側USB-Cは外す。',11,RED)
s.text(36,335,'FW書込み時：外部5Vと7355を外し、Host USB-C→PC。上記は専用診断FWの配線案です。',10)
s.rect(35,355,772,121,'#f8f9fb',GRAY,True)
s.text(48,377,'後工程：親Picoとの接続案（今回の監視専用配線とは分ける）',12,BLUE)
s.text(48,401,'親Pico GP12 TX（物理16） → DMM Host GP1 RX（P1 #02）',11)
s.text(48,424,'親Pico GP13 RX（物理17） ← DMM Host GP0 TX（P1 #01）',11)
s.text(48,447,'親Pico GND                ― DMM Host GND（P1 #17）',11)
s.text(48,465,'親のGP12/13とHostの内部USB GP12/13は別MCU。HostのUSBデータ線へ接続しない。',9,RED)
s.text(36,497,'試験開始前：R13の現物確認・Host専用FWの準備/配置・電源条件の確認が必要。',10)
s.text(36,518,'7355のCDC条件：9600 / 8N1、DTR・RTSともON、終端CRLF（監視UARTの速度とは別）。',10)
s.text(36,545,'図面上のGP1受信・親接続は未実装の候補。基板改造・配線・FW配置を本図作成時に実施していません。',9,GRAY)
s.finish()

s = Sheet(3, '03  裏面から見た位置図：USB-Cが上のまま、左右を反転 / 縮尺なし')
s.text(30, 88, '裏面の左側', 11, BLUE)
s.text(411, 88, '裏面の右側', 11, BLUE)
s.rect(220, 113, 168, 309, '#f2f5f8', BLUE)
s.rect(262, 95, 84, 51, '#edf0f4', GRAY, True)
s.text(270, 118, 'USB-C', 13)
s.text(269, 134, '位置目安', 9)
s.rect(250, 400, 108, 57, '#edf0f4', GRAY, True)
s.text(271, 425, 'USB-A', 15)
s.text(265, 443, '位置目安', 10)
s.text(274, 266, '裏面', 18, BLUE)
s.text(253, 291, '左右反転図', 12, BLUE)
for side, items in [('left', RIGHT), ('right', LEFT)]:
    for row,(num,name) in enumerate(items):
        y=158+28*row
        color=RED if num==18 else INK if num==17 else PURPLE if num==1 else BLUE if num==2 else GRAY
        extra=' / TX' if num==1 else ' / RX' if num==2 else ''
        xp=214 if side=='left' else 382
        s.rect(xp,y-9,12,18,'#ead99d','#8e773d')
        x=30 if side=='left' else 411
        width=170 if side=='left' else 158
        s.rect(x,y-11,width,23,'#fff5f2' if num==18 else '#f5eefb' if num==1 else '#f6f7f8',color)
        s.text(x+10,y+5,f'#{num:02d}',12,color)
        s.text(x+65,y+5,name+extra,12,color)
        s.line([(x+width,y),(214,y)] if side=='left' else [(394,y),(411,y)],color)
s.rect(591,104,224,176,'#fff6ed','#ba762a')
for i,t in enumerate(['裏面での目印','USB-Cを上に保持。','GP0 / #01：左上。','5V / #18：右上。','GND / #17：右上から2番。','3V3 / #16：右上から3番。']):
    s.text(601,126+26*i,t,12 if i==0 else 10,'#8e551a')
s.rect(591,300,224,108,'#f1f5fb',BLUE)
for i,t in enumerate(['はんだ付け前に','表面シルクと本図を照合。','「#」は回路図P1の番号。','基板を上下逆にしない。']):
    s.text(601,321+23*i,t,12 if i==0 else 10,BLUE)
s.text(30,481,'見方：部品面の図からUSB-Cを上に保って左右へ裏返した図。上下方向も変える場合は再照合。',10)
s.text(30,504,'#18は5V / VSYS、#16は3V3。電源の左右取り違えに注意。無給電で施工する。',11,RED)
s.text(30,527,'図は位置確認用。基板版・実装済み配線と照合し、試作完了後に必要な端子だけ施工する。',10)
s.text(30,547,'原典：Waveshare RP2350-USB-A.pdf（P1）と部品面ピン配置図から左右反転して作成。',9,GRAY)
s.finish()

pdf=OUT/'RP2350_USB_A_Pinout_Wiring_20261116_Rev0.pdf'
doc.subset_fonts()
doc.save(pdf,garbage=4,deflate=True)
doc.close()
check=fitz.open(pdf)
for i,p in enumerate(check,1):
    p.get_pixmap(matrix=fitz.Matrix(1.8,1.8)).save(OUT/f'preview_sheet{i}.png')
    (OUT/f'sheet{i}_text.txt').write_text(p.get_text(),encoding='utf-8')
    assert len(p.get_text())>500
sources=[ROOT/'reference/USB_Host_SubMCU_20261116_RP2350_USB_A/RP2350-USB-A.pdf',
         ROOT/'reference/USB_Host_SubMCU_20261116_RP2350_USB_A/Waveshare_Pinout.jpg']
data={'date_jst':'2026-11-16','view':'component side; USB-C top, USB-A bottom',
      'header':'P1; not MCU package or parent Pico physical pins','left_top_to_bottom':LEFT,
      'right_top_to_bottom':RIGHT,'sources':[{'path':p.relative_to(ROOT).as_posix(),
      'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]}
(OUT/'verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Created three-page PDF, three SVGs, PNG previews and pin verification record')
