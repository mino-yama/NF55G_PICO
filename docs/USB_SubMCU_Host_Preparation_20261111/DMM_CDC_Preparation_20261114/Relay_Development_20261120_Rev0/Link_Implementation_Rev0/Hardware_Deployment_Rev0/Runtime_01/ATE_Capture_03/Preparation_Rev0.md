# 接続復帰後の中継再試験 準備 Rev.0

ユーザーは7355のUSB-Bが抜けていたと報告し、デバッグを止め最初の中継テストへ戻すよう指示した。追加デバッグを停止。Host単体のH照合は16msで正常応答、ID/FW一致、状態NOT_READYだった（Host_UART_Investigation_01）。USB-B未接続はユーザー確認事実だが、先行のTIMEOUTの全原因をこれだけで断定しない。IssueはCloseしない。

親/HostとATEの通常接続・7355 USB接続へ復帰後、治具ID、EXT_QUERY 2000 *IDN?を各1回試験する。レンジ/READ/NF55Gコマンドは送らず、自動再送しない。ate_trial_reconnected.pyを準備したが未実行。接続/電源復帰の完了通知を待つ。先行試験結果は保持。
