# Type_C2 QR Host probe

追加RP2350-USB-C用の単体調査FW。Type_C2の列挙・HID原文を記録する。正式な治具UART、7355、QR文字列判定、2 Host対応は含まない。親PicoやNF55Gを操作しない。

| ビルド | 識別 | 出力 |
|---|---|---|
| 通常 | qr-probe-20261111.1 | RAMのみ。既配布版の成果物を保持 |
| -DiagnosticTx | qr-uart-20261111.1 | RAM＋GP0 UART0 TX／115200・8N1、送信専用 |

UART版はbuild_uart_gp0、通常版はbuildを使う。バージョン文字列はCMakeで定義し、ファイルメタデータと起動レコードを共通化。配布物は各releasesフォルダのmanifestで特定する。過去RAM版を再現する場合は当該releaseのsource snapshotを用いる。

[UART版の仕様](../../docs/USB_SubMCU_Host_Preparation_20261111/UART_FW_20261111/Specification_Rev0.md)／[UART版の検証結果](../../docs/USB_SubMCU_Host_Preparation_20261111/UART_FW_20261111/Result_Rev0.md)／[従来RAM版の記録](../../docs/USB_SubMCU_Host_Preparation_20261111/Result.md)。

UARTログは@＋76byteのHEX＋LF。起動版・個体IDをUSB初期化前に出力し、通常HostループでFIFO空きの分を最大16byteずつ送る。UART受信・コマンド受付はしない。GP12／13のPIO Hostは起動するため、回路改造と給電条件を整える前に書き込まない。

SH-U05AはGP0→RXDとGNDのみ。TXD–RXD短絡ジャンパはUSBを抜いて外し、UARTモードは維持。TXD／3V3／5V0は追加基板へ接続しない。今回のUART版はビルド済み・実機未配置であり、波形・起動・QR受信は未受入。

メーカー原文はvendor/upstream-774cbb1、ビルド用派生はvendor/pico-pio-usb。差分とnewlib hookはvendor/SDK_2_2_0_Compatibility.mdを参照。
