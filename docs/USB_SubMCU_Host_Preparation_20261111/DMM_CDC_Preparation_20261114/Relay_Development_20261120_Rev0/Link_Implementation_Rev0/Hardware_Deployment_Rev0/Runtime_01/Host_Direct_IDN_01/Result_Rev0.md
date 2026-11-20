# Host単体デバッグ 実行結果 Rev.0

2026-11-20 17:04 JST。ユーザーの開始指示によりHost単体診断を実行。COM22 CH341 1A86:5523を照合、115200/8N1・flowなし・DTR/RTS OFF。

## 確認事実

Hを1回送信後、3秒以内に応答フレームなし。受信0byte、Host X1 response timeoutで停止。HostのREADY/基板ID/FW版を今回取得できていない。Qと7355の*IDN?は送信していない。自動再送・レンジ変更・READ・NF55G通信・Flash書込みなし。COM22解放済み。

## 推測と未確認事項

先行のHost単体診断ではHに16msで応答し正しいID/版、NOT_READYを確認。その後ユーザーは7355 USB-B抜けを報告。今回の受信0byteだけでUSB処理停止・給電・UART配線などの原因を断定しない。USB接続時にHostが無応答になる可能性を、同じ電源/UARTのまま7355 USB-Bだけ外す比較で調べる。親が切り離されていること、Host USB-Cと外部5Vの排他は維持。

## 次の診断

HostのPC USB-C/UART配線は維持し、7355 USB-Bだけを外してHを1回送る準備をHost_USB_Disconnected_01に作成。未実行。これは自動再送ではなく、接続条件を変えた起動照合の比較。機器コマンドは送らない。追加FW変更は実施していない。USB-RELAY-LINK-01はOpen継続。

[試行JSON](Result.json)／[H送信原文](tx.raw)／[全受信](rx.raw)。
