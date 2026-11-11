# NF55G試験治具 接続・GPIO割付図 Rev.3

2026-11-10作成。RP2350-USB-Cの回路図コネクタ名を使い、USB機器の接続先を固定した。

- `Type_C1`（ネイティブUSB）→ ADCMT 7355
- `Type_C2`（PIO-USB）→ Sanwa BCR-TC2D1BK
- USBハブは標準構成に含めない。機器のポート間移行をしない。

## ファイル

- [印刷用PDF・A4横3枚](NF55G_Fixture_Connection_GPIO_Rev3_20261110.pdf)
- 編集用SVG: [1 全体接続図](NF55G_Fixture_Rev3_sheet1.svg)、[2 GPIO表](NF55G_Fixture_Rev3_sheet2.svg)、[3 追加・改造範囲](NF55G_Fixture_Rev3_sheet3.svg)
- [全体図プレビュー](preview_sheet1.png)、[GPIO表プレビュー](preview_sheet2.png)、[追加範囲プレビュー](preview_sheet3.png)
- [生成スクリプト](../../../scripts/build_fixture_connection_drawing.py)
- 過去版: [Rev.2](../NF55G_Fixture_20261110_Rev2/README.md)、[Rev.1](../NF55G_Fixture_20261110_Rev1/README.md)、[Rev.0](../NF55G_Fixture_20261110_Rev0/README.md)。旧版は履歴として保持。
- [RP2350-USB-C回路図・資料台帳](../../../reference/USB_Host_SubMCU_20261110/README.md)
- [RP2350-USB-C初回受入チェックリスト](../../RP2350_USB_C_First_Acceptance_20261110.md)

## 変更範囲と注意

Rev.2にあった「RP2350-USB-C→USBハブ→QR／7355」案を、回路名による固定ポート接続へ更新した。通信プログラム、ATE/NF55G接続、GPIO割当ては変更していない。

基板回路図のコネクタ名と回路経路を示す説明図であり、実基板版との一致、Type_C2のCC抵抗設定／VBUS給電、二つのUSB Hostの同時動作、7355の実機USB classや通信成立を証明しない。電源分岐、筐体寸法・スロット位置・積層順、加工要否、下位UARTピンは未確定。製造用加工確定図ではない。作業は[初回受入チェックリスト](../../RP2350_USB_C_First_Acceptance_20261110.md)に従い、未確認時は接続・加工を保留する。

## 生成・検証

`python scripts/build_fixture_connection_drawing.py`でRev.3 PDF/SVG/PNGを生成する。PDFはA4横3ページ。各ページのレンダリングとテキスト抽出を確認済み。通信コード変更、実機接続、基板改造、プログラム配置は行っていない。USB-SUB-01／HW-01はOpen継続。
