# 中継実機再試験4 結果 Rev.0

2026-11-20。ユーザーの「再度テスト」により現在の接続で実行。COM7にELECOM 056E:5004があることを確認。

## 確認事実

- 57600/8N1、flow controlなし、DTR/RTS OFF。
- 治具*IDN?+CRを1回送信し、NF55G_PICO_FIXTURE,Rev.0+CRを受信。前試行のATE無応答は今回は再現しなかった。
- EXT_QUERY 2000 *IDN?+CRを1回送信し、ERR:EXT_TIMEOUT:AMBIGUOUS=0+CRを受信。7355の識別応答は未取得で中継受入未成立。
- 自動再送・追加Query・レンジ変更・READ・NF55Gコマンド・電源操作・コード/Flash変更なし。COM7解放済み。

## 未確認事項

7355 USB-B未接続のユーザー報告後、接続復帰を経た今回も同じ中継TIMEOUTが返った。USB-B抜けだけを先行/今回のTIMEOUT原因と断定しない。ATE応答だけでは親HELLO待ちとHost USB送信前TIMEOUT等を区別できない。親Host間の実配線/信号原文、元の親GP13受信、現在のHost起動/USB状態は未確認。親内PIO照合とHost単体H照合の成功は現在の親Host間通信成功を示さない。USB-RELAY-ATE-01、USB-RELAY-LINK-01は原因未確定でOpen維持。ユーザーの追加デバッグ停止指示を維持し、今回の再試験後は追加操作せず終了。

[送受信・時刻・hash](Capture_Result.json)／[受信原文](all_rx.raw)。先行試験記録は保持。
