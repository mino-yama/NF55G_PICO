# UART版FW 実機書込み結果 Rev.0

日付: 2026-11-14／対象: 追加Waveshare RP2350-USB-C、A06FEA01012EC137

## 確認結果

- BOOT操作後E: RP2350を検出。picotoolのchipidと--serで個体を照合。
- 配置前はusb_submcu_acceptance／dev-20261111.1。全Flash 2,097,152byteをbefore_flash_2MB.binへ退避し、save -a -vで照合成功。
- 配布UF2のSHA-256=31da5f6f743fe6447fa03c56d223ccd6f12ecb074a8cc92374867e1cee754a70を再確認。
- load -vと独立verifyの両方が終了0で成功。
- 配置後はusb_submcu_qr_uart_probe／qr-uart-20261111.1、ARM Secure／SDK2.2.0、GP0 TX 115200 8N1、GP12 D+／GP13 D−。chipidも一致。
- 対象serial指定のrebootは終了0。再起動後一覧はCOM6とCOM19のみ。UART版はnative USB CDCなしのためCOM21消失は期待動作だが、これだけでアプリ正常実行とはしない。
- 起動UART、実行中個体ID、PIO初期化、QR・7355は未確認。既存治具COM6には接続・書込み・resetしていない。

## 次の作業

PC Type_C1を抜き、QR／7355／外部5Vも外した無給電状態にする。SH-U05AのUARTモードを維持し、テスト用TXD–RXD短絡だけを外す。追加基板GP0→SH-U05A RXD、GND→GNDの2線を接続する。変換器TXD／5V0／3V3は接続しない。

SH-U05AをPCへ接続しCOMを確認、受信開始後に追加基板へPC Type_C1のみで給電して、QRなしの起動ログを採取する。外部5Vは同時接続しない。版と実個体ID、初期化ログ確認後に外部枝確認・QR試験へ進む。

## 証跡

[配置前情報](before_info.txt)／[全Flash退避照合](backup_verify.txt)／[書込み照合](load_verify.txt)／[独立verify](independent_verify.txt)／[配置後情報](after_info.txt)／[再起動結果](reboot_status.json)／[再起動後ポート](ports_after_reboot.txt)。

元のバックアップ・旧配布物は保持。ソース変更なし、Host／Mock再実行なし。今回の成功は配置と照合までであり、UART・Host・電源保護の実機受入ではない。

退避Flash SHA-256: 73A33FAF38E02F69B44538080FAB4DA0842CBDAD59EED63570E0AC0E4F3B1AF5
