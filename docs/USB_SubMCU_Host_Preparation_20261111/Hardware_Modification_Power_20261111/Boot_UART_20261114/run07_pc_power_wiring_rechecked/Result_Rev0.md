# 配線再確認後のPC給電UART再試験 Rev.0

日付: 2026-11-14

## 確認結果

- ユーザーの「配線確認した。再度テスト」を受けCOM22で受信開始。PC接続または接続済み時RSTの案内に「完了」と回答。どちらの操作かは回答から確定しない。
- 受信309byte、送信0、46.422秒で終了、COM閉。
- 元rawのSHA-256は5c6318ae5489e74e9f5af79279e7555a003a5c23a31f22d29d4865f4b8d42ded。初回PC給電・RSTのrawと完全一致。
- 正規2レコードは連番0 boot=qr-uart-20261111.1、連番1 board_id=A06FEA01012EC137。解析エラーレコードなし。
- 先頭NUL 1byteは再現。明示オプションにより警告付きで解析しoriginal_framing_clean=false。無警告の形式合格・PIO初期化完了・QR動作とはしない。

配線再確認後に受信を回復した事実を記録する。実際に動かした端子・接点は確認できていないため、過去の無受信原因を特定接点や外部給電に断定しない。

## 次の比較

UART GP0→RXD／GNDの2線を動かさず、追加基板Type_C1のPC USBを先に外して無給電にする。外部アダプタOFFでExpanderの5V／GND給電配線を戻す。PC Type_C1・QR・7355は未接続。外部電源は受信READYまでOFFを維持する。

[元raw](boot_uart.raw)／[解析JSON](boot_uart_with_startup_warning.json)／[採取結果](capture_result.json)。FW・ソース変更なし、Host／Mock再実行なし。USB-SUB-04含めOpen事項は維持する。
