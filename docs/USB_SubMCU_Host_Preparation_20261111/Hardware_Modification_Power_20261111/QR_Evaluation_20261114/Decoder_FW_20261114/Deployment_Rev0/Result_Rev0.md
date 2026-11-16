# 基板内QR復元版 実機配置結果 Rev.0

日付: 2026-11-14／対象chipid: A06FEA01012EC137

- BOOTSELで対象個体を照合。配置前はqr-uart-20261114.1。
- 全Flash 2,097,152byteを退避しsave -a -vで照合成功。
- 配布UF2 SHA-256=419fadbc4d7e79704ff8703574d59524e4bea5262991f10eef71a2c5441d61f3を再確認。
- 対象serial指定load -vと独立verifyが終了0で成功。
- 配置後情報でqr-uart-20261114.2／ARM Secure／SDK2.2.0／1024件／GP0 TX 115200 8N1／GP12 D+・GP13 D−を確認。個体ID一致。
- 対象指定rebootは終了0。実行時の版・個体ID・新kind12の35文字出力は次の実機試験で確認する。

## 次の試験

PC Type_C1を抜き、外部電源OFFでExpander 5V／GND、GP0→SH-U05A RXD／GND、Type_C2 QRを戻す。PC Type_C1／7355を外し、変換器TXD／3V3／5V0は接続しない。受信READY後に外部電源投入、起動・列挙を確認して同じ35文字QRを1回読む。最初はkind12が1回だけ出て原文35byteが一致することを確認する。

[配置前情報](before_info.txt)／[Flash退避照合](backup_verify.txt)／[書込み](load_verify.txt)／[独立verify](independent_verify.txt)／[配置後情報](after_info.txt)／[reboot](reboot_status.json)。

旧版・元ログは保持。今回コード変更・Host／Mock再実行なし、直前346件成功を維持。正式親子UART・ATE／Cache／SS、電源投入起動差、先頭NUL、7355・2 Host等のOpen事項は未解決。

退避Flash SHA-256: EB44BB84F67E6A9584D3ED674129594AC947A67C315119155B5B03288C4CC943
