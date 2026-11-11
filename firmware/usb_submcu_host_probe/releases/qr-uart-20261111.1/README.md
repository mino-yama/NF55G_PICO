# qr-uart-20261111.1 配布物

追加RP2350-USB-CのGP0診断UART版。未書込み・実機未受入。対象運用個体A06FEA01012EC137。
UF2はusb_submcu_qr_uart_probe.uf2、115200bps／8N1／送信専用。PIO HostはGP12／13で起動する。
回路改造・給電確認前に配置しない。SH-U05AのTXD–RXD短絡はUSBを抜いて解除し、RXDとGNDだけを配線する。
[検証結果](../../../../docs/USB_SubMCU_Host_Preparation_20261111/UART_FW_20261111/Result_Rev0.md)／[仕様](../../../../docs/USB_SubMCU_Host_Preparation_20261111/UART_FW_20261111/Specification_Rev0.md)。
manifest.jsonの各ファイルhashで配布物を特定。source/は当該ビルド時のソースsnapshotで、原典と派生コピーの両方を保持。
