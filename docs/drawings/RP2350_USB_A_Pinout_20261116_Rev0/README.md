# RP2350-USB-Aの端子番号と位置図

2026-11-16。DMM 7355用Waveshare RP2350-USB-A（Switch Science SKU10275）の配線準備図。ユーザー予定の試作完了後のはんだ付けに使う。今回配線・施工・FW配置は行っていない。

- [印刷用A4横PDF 全3枚](RP2350_USB_A_Pinout_Wiring_20261116_Rev0.pdf)
- [1 部品面の位置図 PNG](preview_sheet1.png) / [SVG](RP2350_USB_A_Pinout_Rev0_sheet1.svg)
- [2 UART監視と親接続案 PNG](preview_sheet2.png) / [SVG](RP2350_USB_A_Pinout_Rev0_sheet2.svg)
- [3 裏面の位置図 PNG](preview_sheet3.png) / [SVG](RP2350_USB_A_Pinout_Rev0_sheet3.svg)

## 図の見方

USB-Cが上、USB-Aが下。1枚目は部品面、3枚目はその向きを保って左右へ裏返した裏面。`#01`等はメーカー回路図のP1ヘッダー番号で、GPIO番号や親Pico 2の40pin番号、RP2350 ICの端子番号とは異なる。GP12/13 USBデータ線とGP16 RGBは内部専用でP1には出ていない。

|信号|P1番号|部品面での位置|裏面での位置|
|---|---|---|---|
|GP0 / UART0 TX|#01|右上|左上|
|GP1 / UART0 RX|#02|右上から2番|左上から2番|
|5V / VSYS|#18|左上|右上|
|GND|#17|左上から2番|右上から2番|
|3V3|#16|左上から3番|右上から3番|

初回はGP0→USB-UART変換基板RXD、GND共通の監視専用。GP1、変換基板TXD/5V/3V3は接続しない。監視115200/8N1は診断FW仕様案で、7355のCDC 9600/8N1とは区間が違う。専用CDC Host FWとR13現物状態・給電条件は別途確認する。

親Picoとの接続案は親GP12 TX→Host GP1 RX、Host GP0 TX→親GP13 RX。新しい双方向FW/APIは未実装で、現在の監視専用接続と分けてある。QR用RP2350-USB-Cの位置図として使わない。

## 原典と検証

- [Waveshare回路図 P1](../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/RP2350-USB-A.pdf)
- [メーカー部品面ピン配置図](../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/Waveshare_Pinout.jpg)
- [CDC単体仕様](../../USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/CDC_Host_Single_Acceptance_20261116_Rev0.md)
- [親PIO UART割付案](../../USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Parent_PIO_UART_Pin_Check_20261116/Pin_Assignment_Rev0.md)

[番号一覧と原典hash](verification.json)を保存。18端子の一意性・PDF文字抽出・SVG構文・文字領域・参照先を確認し、3ページをPNGへ描画して目視確認した。メーカー原典と旧図面は変更していない。FW/量産コード変更がないためHost Unit/Mock NF55Gは再実行していない。

再生成: `python scripts/build_rp2350_usb_a_pinout_20261116.py`。図は縮尺なし、メーカー写真との相対位置を示す。今回個体の版・シルク・実装済み配線をはんだ付け前に照合する。
