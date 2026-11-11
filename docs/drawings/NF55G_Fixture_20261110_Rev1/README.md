# NF55G試験治具 接続・GPIO割付図 Rev.1

更新日: 2026-11-10。追加発注・改造範囲の説明用。ユーザー補足「各基板の接続はPico-Quad-Expanderを使用」を反映。[Rev.0](../NF55G_Fixture_20261110_Rev0/README.md)は旧版として保持する。

## 成果物

- [PDF（A4横・3枚）](NF55G_Fixture_Connection_GPIO_Rev1_20261110.pdf)
- 編集用SVG: [全体接続](NF55G_Fixture_Rev1_sheet1.svg)、[GPIO割付](NF55G_Fixture_Rev1_sheet2.svg)、[追加・改造範囲](NF55G_Fixture_Rev1_sheet3.svg)
- PNG: [1](preview_sheet1.png)、[2](preview_sheet2.png)、[3](preview_sheet3.png)
- [生成スクリプト](../../../scripts/build_fixture_connection_drawing.py)

## 今回の修正

RTC、SD、RS232C 2CHの各基板はPico-Quad-Expander経由で接続する。図面1の中央にExpanderの枠を表示し、Pico 2と共通GPIOで各基板へ接続する構成を明示した。図面の配置は機能ブロック配置であり、実際のスロット位置・向き・積層順ではない。

Expanderは同じPico GPIOを共有する接続として扱うため、UART0=GP0/1、UART1=GP4/5、RTC=GP20/21、SD=GP16～19の割付、およびADA-5703のGP4/GP5分離条件は変わらない。ヘッダー経由でつながることと、競合する信号の分離が必要なことを区別する。

追加HOSTのGP8/GP9/GNDはExpander側から引き出す案とし、下位側GPIO、使用するヘッダー位置、引出しコネクタ、固定方法は未確定。RP2350-USB-CをExpanderのPico用ソケットへ直接挿せるという指定・確認はない。PIO双方向UART案と、既存GP9受信専用試作の違いを維持する。

製品名は今回指定のPico-Quad-Expanderを使用する。従来READMEにはSeeedStudio 103030397という識別記録があるが、現物ラベルとメーカー・品番の照合は今回未実施。同一製品として追加のメーカー仕様を推測しない。

## 適用範囲と検証

説明・検討用の図面であり、製造用結線確定図ではない。USBコネクタ撤去・信号直付け・ホスト基板加工の要否は未確定。USBホスト用ポート・CC・VBUS、給電保護、下位UARTピン、実コネクタ端子番号、機構と加工位置を確認後に製造用Rev.へ展開する。HW-01／USB-SUB-01はOpenを維持する。

PDF全3枚の画像表示、SVGの構文、PDF文字抽出とページ内収まりを確認。通信コード・実機接続・配置・改造は変更せず、Host／Mockは再実行していない。

出典は今回ユーザー補足、[Rev.0の資料索引](../NF55G_Fixture_20261110_Rev0/README.md#出典照合資料)、[追加HOST開発準備](../../USB_Host_SubMCU_Integration_Plan_20261110.md)。GPIO物理ピンと未確定事項はRev.0から変更していない。
