# UART 1024件版 実機配置結果 Rev.0

日付: 2026-11-14／対象: RP2350-USB-C A06FEA01012EC137

## 結果

- 初回のBOOT操作回答後はBOOTSELが検出されず書込み未実施。その後のBOOT押下・再確認指示で対象chipidのBOOTSEL認識に成功。
- 配置前FWはqr-uart-20261111.1。全Flash 2,097,152byteを退避し、save -a -vで照合成功。
- 配布UF2 SHA-256=0ce5168e546f25431e51922fb6fd0728a38697efb65937b9532da9f9aece1b81を再照合。
- 対象serialを指定してload -v成功、続いて独立verify成功。
- 配置後情報はusb_submcu_qr_uart_probe／qr-uart-20261114.1、Diagnostic RAM capacity 1024 records、GP0診断TX／115200 8N1、GP12 D+／GP13 D−、SDK2.2.0／ARM Secure。chipid一致。
- 対象serial指定rebootは終了0。実行時の新FW版・個体ID・QR再読取ログは次工程で確認する。

## 次工程

追加基板のPC Type_C1を抜き、外部電源OFFのまま外部5V／GND配線、GP0→SH-U05A RXD／GND、Type_C2 QRを戻す。変換器TXD／3V3／5V0は接続しない。PC Type_C1と7355は未接続。受信READY前に外部電源を投入しない。35文字試験QRは同じ画像・原文を使用する。

[配置前情報](before_info.txt)／[全Flash退避照合](backup_verify.txt)／[書込み照合](load_verify.txt)／[独立照合](independent_verify.txt)／[配置後情報](after_info.txt)／[再起動](reboot_status.json)。旧配布物・元ログは変更しない。今回ソース変更・Host／Mock再実行なし。直前の全326件成功はビルド準備時の結果。

退避SHA-256: A80A6559172AA97158FD4B22D6F727DEACF37CBA8D4C2AA8B29453E3090E545E
