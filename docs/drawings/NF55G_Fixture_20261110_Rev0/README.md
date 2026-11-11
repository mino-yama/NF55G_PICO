# NF55G試験治具 接続・GPIO割付図 Rev.0

作成日: 2026-11-10。追加発注・改造範囲の説明用。案件保存先は現在のNF55G_Picoリポジトリ。

## 成果物

- [印刷用PDF（A4横・3枚）](NF55G_Fixture_Connection_GPIO_Rev0_20261110.pdf)
- 編集用SVG: [1 全体接続](NF55G_Fixture_Rev0_sheet1.svg)、[2 GPIO割付](NF55G_Fixture_Rev0_sheet2.svg)、[3 追加・改造範囲](NF55G_Fixture_Rev0_sheet3.svg)
- PNGプレビュー: [1](preview_sheet1.png)、[2](preview_sheet2.png)、[3](preview_sheet3.png)
- 生成元: [Pythonスクリプト](../../../scripts/build_fixture_connection_drawing.py)。PyMuPDFとWindowsのMS Gothicを使用。PDFはフォントを埋め込む。SVGは文字編集が可能で、表示環境に日本語フォントが必要。

## 図面の読み方と適用限界

青実線は現行の接続構成、緑破線は追加する接続案。機器間の論理接続を示す説明図であり、基板の積層順・外形寸法・端子位置・全電源配線を示した製造図ではない。

Pico 2のGPIO番号と40ピン物理番号を区別した。下位RP2350-USB-CのUARTピン、CN24の端子番号、RS232コネクタの端子番号は未確定として記載を保留。実物と原典を照合せず線順を確定しない。

現行UART0はATE、UART1はNF55Gで使用する。GP8/GP9のハードUART機能はUART1と共用のため、追加HOSTとの接続はPIOによる双方向UART案。GP8=TX、GP9=RXは候補であり、本番実装済みではない。既存QR試作のGP8はHigh固定、GP9はPIO受信のみ。

## 追加発注時の説明要点

1. RP2350-USB-C、USBハブ、QR用Type-Cデータ接続、7355用Type-Bデータ接続と固定部品を追加する案。
2. Pico側からGP8/GP9/GNDを引き出し、HOSTのRX/TX/GNDに接続する。下位GPIOと中継コネクタは後続設計で確定する。
3. USB接続は既製ケーブル・ハブでの成立を先に確認する。USBコネクタ撤去・D+/D-への直付けが必要との判断はしていない。
4. RP2350-USB-Cのホスト用ポート、CC抵抗、VBUS供給の実回路を確認する。必要な設定変更・加工の要否を記録する。USB-A向けR13除去をUSB-Cへ転用しない。
5. USB追加給電は容量・突入・過電流保護・逆流・GNDを確認して設計する。QR動作時230mAだけから電源容量を決めない。PicoのVBUS/VSYS/3V3を相互に直結する指示ではない。
6. ADA-5703のGP4/GP5分離は既存構成でも必要。再発注時に処置漏れがないよう、分離箇所・方法・導通検査記録を製造用図面へ追加する。既存機の物理分離済み申告と、最終検査記録の未確定は区別する。
7. 発注用の加工確定図には、部品型番・数量、コネクタ型番と端子番号、実寸・固定位置、電源分配、加工箇所、検査方法を追加する。現時点ではこれらを推測して指定しない。

## 事実・提案・未確認の区分

| 区分 | 内容 |
|---|---|
| 記録で確認できる現行構成 | Pico 2、SeeedStudio 103030397、Pico-2CH-RS232、Pico-RTC-DS3231、ADA-5703。UART0 GP0/1、UART1 GP4/5、RTC GP20/21、SD GP16～19 |
| ユーザー指定 | 追加HOSTはRP2350-USB-C、QRはBCR-TC2D1BK、DMMは7355のUSB接続、Picoとの双方向UART |
| 設計案 | Pico PIO TX=GP8/RX=GP9、115200/8N1、USBハブ共用、DMM CDC方式 |
| 未確認 | 実HOST基板版・回路、USB共存・給電、ピンと端子番号、配線加工、機構、測定精度、Timing |

管理IssueはHW-01、USB-SUB-01、関連QR／補正Issue。Openを維持する。今回の図面作成でコード・実機接続・改造・配置は変更していない。

## 出典・照合資料

- [現行ハードウェア資料索引](../../../reference/local_hardware_reference_20260904/README.md): 使用基板、GPIO、ADA-5703の分離条件。
- [現行資料との整合確認](../../Hardware_Reference_Alignment_Check_20260904.md): SDA/SCL、SD信号、分離条件。
- [既存QR単独試験](../../QR_Receive_Test.md): GP8/GP9、物理ピン11/12/13、PIO受信とTX High固定。
- [追加HOST開発準備](../../USB_Host_SubMCU_Integration_Plan_20261110.md): ユーザー指定、内部連携案、給電と未確定事項。
- [既存NF55G接続準備](../../NF55G_HIL_Preparation.md): UART経路、CN24ハーネスは実物照合が必要。
- [Raspberry Pi公式Pico 2 pinout](https://datasheets.raspberrypi.com/pico/Pico-2-Pinout.pdf)（2026-11-10確認）: GPIO、電源、40ピン番号。
- [Waveshare RP2350-USB-C公式資料](https://docs.waveshare.com/RP2350-USB-C)（2026-11-10確認）: 内蔵USB用Type-CとPIO-USB用Type-C、CC抵抗によるSink/Source切替え。
- [BCR-TC2D1BK公式仕様](https://www.sanwa.co.jp/product/syohin?code=BCR-TC2D1BK)（前工程11/10確認）: USB HID、Type-C、動作時230mA。

## 検証

PDF生成後、全3枚をPNG化して文字・配線・表の重なりと欠けを目視確認する。GPIO物理ピンは公式pinoutと照合する。生成スクリプトはPDFのページ数・文字抽出も確認する。新HOSTの電気的成立や実機動作の検証は含まない。
