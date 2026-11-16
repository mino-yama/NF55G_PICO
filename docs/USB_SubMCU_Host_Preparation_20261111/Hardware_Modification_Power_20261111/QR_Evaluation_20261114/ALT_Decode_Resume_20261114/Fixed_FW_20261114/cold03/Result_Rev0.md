# 固定接続cold-start第3回 結果 Rev.0

2026-11-14。RSTなしで電源ON、HID mount3606ms。起動記録1件で、A/Bを各1回読み取り35文字完全一致。完成時刻67006ms／70930ms、間隔3924ms。drop0、decode等エラーなし、heartbeatのmain/frameは取得範囲で継続増加。

UART28029 byte、182レコード連番欠落なし。先頭NUL1 byte継続。原文保持、解析時のみ明示分離。
SHA-256: `ffc1923a85c75f0ca40fc3dca2f7486f8d294b1c8e5fb1d8693baf5f3445d00c`。

10分以上試験は未完了。ユーザーの「10分以上かよ」を受け、エージェントが追加した長時間確認は今回の限定目標の必須条件ではないと説明し、実施を省略した。ユーザーが長時間試験の成功や量産保証を承認したとは扱わない。
stop.requestで受信を正常終了しポート閉。追加読取・FW変更なし。

[原文](scan_uart.raw)／[終了記録](capture_result.json)／[解析](Parsed_Rev0.json)／[途中記録](Interim_Rev0.md)
