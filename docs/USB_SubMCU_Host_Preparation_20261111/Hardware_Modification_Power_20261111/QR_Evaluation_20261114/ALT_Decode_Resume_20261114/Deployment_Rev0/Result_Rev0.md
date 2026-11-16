# Alt対応版の再配置結果 Rev.0

日付: 2026-11-14／対象chipid A06FEA01012EC137

- BOOTSELで対象個体を照合。配置前は原文取得版qr-uart-20261114.1。
- 現Flash全2,097,152byteを退避しsave -a -vで照合成功。
- 検証済みAlt対応版UF2のSHA-256=419fadbc4d7e79704ff8703574d59524e4bea5262991f10eef71a2c5441d61f3を再確認。
- 対象serial指定load -v、独立verifyの両方が終了0。
- 配置後版qr-uart-20261114.2、ARM Secure／SDK2.2.0／1024件、GP0 TX 115200 8N1、GP12 D+／GP13 D−、chipid一致を確認。
- 対象指定reboot成功。これで実機もAlt対応版へ戻った。実行時の版・個体ID・kind12の35文字受信は次工程で確認する。

## 次の手順

PC Type_C1を抜き、外部電源OFFでExpander 5V／GND、GP0→SH-U05A RXDとGND、Type_C2 QRを戻す。変換器TXD／3V3／5V0は追加基板へ接続しない。SH-U05AのみPC接続、PC Type_C1／7355は未接続。受信READY後に外部給電・必要時RST、同じ35文字試験QR1回を読み、完成原文kind12と期待35byteの一致、kind13エラーなしを確認する。

[配置前情報](before_info.txt)／[全Flash退避](backup_verify.txt)／[load verify](load_verify.txt)／[独立verify](independent_verify.txt)／[配置後情報](after_info.txt)／[reboot](reboot_status.json)。

退避Flash SHA-256: EB44BB84F67E6A9584D3ED674129594AC947A67C315119155B5B03288C4CC943

旧配布物・旧raw・英語設定調査は履歴で保持。今回コード変更・Host／Mock再実行なし、再開時の346件成功を維持。正式親子UART・ATE／Cache／SS、先頭NUL・電源投入起動差・有限ログ・保護・7355／2 Host等は未解決。
