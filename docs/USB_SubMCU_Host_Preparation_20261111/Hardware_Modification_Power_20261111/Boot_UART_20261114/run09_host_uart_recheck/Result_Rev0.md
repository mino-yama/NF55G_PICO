# QR評価前 HOST基板UART再確認結果 Rev.0

日付: 2026-11-14

## 結果

- ユーザーが「その前にもう一度HOSTとの通信」を指示し、COM22／115200・8N1で待受開始。その後「外部給電中」と回答。
- 受信309byte、先頭00＋正規2レコード。受信後5秒無通信で終了しCOM閉。
- boot=qr-uart-20261111.1、board_id=A06FEA01012EC137、連番0／1を確認。過去の起動ログとSHA-256まで完全一致。
- エラーレコードなし。先頭NULの警告付き解析でoriginal_framing_clean=false、hardware_acceptance=falseを維持。
- 給電ON／RSTのどの操作で今回のログが出たかはユーザー回答から確定しない。追加のRST操作は不要。

これは現FWのHOST基板→PCのTX専用起動識別確認。コマンド受信処理は現FWにないため、双方向要求応答・親Picoとの正式UART試験の成功とはしない。PIO Host初期化成功、QR列挙・読取は未確認。

[受信原文](boot_uart.raw)／[解析](boot_uart_with_startup_warning.json)／[採取条件と終了状態](capture_result.json)。FW・コード変更、追加resetなし。次にQR評価へ進む場合は、外部電源OFFでQRをType_C2へ接続し、受信待機後に通電する。
