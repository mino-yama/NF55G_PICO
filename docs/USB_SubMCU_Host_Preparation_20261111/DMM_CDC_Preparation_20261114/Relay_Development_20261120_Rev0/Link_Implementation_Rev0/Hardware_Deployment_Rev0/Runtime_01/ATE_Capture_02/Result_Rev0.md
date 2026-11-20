# 中継実機再試験2 結果 Rev.0

2026-11-20 16:43 JST。ユーザーの「現在 *IDN?通ります。再度テストして下さい」により、現在の通電・接続状態で再試験した。

## 確認事実

- COM5 ELECOM（056E:5004）、57600/8N1、flow controlなし、DTR/RTS OFF。
- 治具へ *IDN?+CR を1回送信し、NF55G_PICO_FIXTURE,Rev.0+CR を受信。ATE受付・識別応答は今回確認できた。
- 続けて EXT_QUERY 2000 *IDN?+CR を1回送信。2016ms後、ERR:EXT_TIMEOUT:AMBIGUOUS=0+CR を受信。
- 7355の識別原文は未取得。中継受入は未成立。ATEからEXT_QUERYを送った事実と、7355への実USB送出確認は区別する。
- 自動再送・電源操作・Flash/親コード変更なし。レンジ切替・READ・NF55Gコマンドは送信していない。COM5解放済み。
- 全受信53byte、SHA-256: 33efb8b7bfb7abf901d4a41992dd248811baa6a54d25e61a41970676f95280fc。

## 推測と未確認事項

実装上、TIMEOUT/AMBIGUOUS=0は親のHELLO待ち期限切れ、またはHostがUSB送信開始前に返すTIMEOUT等で生じ得る。ATE応答だけで停止箇所や配線不良を断定しない。親/Host間X1原文、実PIO初期化、Host通常起動とUSB状態は未確認。失敗後はfaultを保持する設計のため、盲目的な再送は行わない。

ソース確認ではSDはGP16/17/18/19、RTCはGP20/21を使用し、今回の親GP12/13との重複は見当たらない。これは実機GPIO状態の確認ではない。

## 次の切分け

外部電源OFF後、親とHost間の信号線・共通GNDを切り離し、親PicoだけをPC USBへ接続して、準備済みStartup_Investigation_01診断でFactory/PIO初期化を確認する。Hostの外部5VとUSB-Cは同時接続しない。コード/仕様を原因推測だけで変更せず、USB-RELAY-ATE-01の再現有無追跡とUSB-RELAY-LINK-01をOpen維持する。レンジ問題はユーザー指示どおり保留。

## 証跡

[送受信・時刻・hash](Capture_Result.json)／[全受信原文](all_rx.raw)。試行1の資料は上書きせず保持した。変更は試験記録・進捗のみで、既存446件成功のコード/Mock結果は今回の実機受入成功を意味しない。
