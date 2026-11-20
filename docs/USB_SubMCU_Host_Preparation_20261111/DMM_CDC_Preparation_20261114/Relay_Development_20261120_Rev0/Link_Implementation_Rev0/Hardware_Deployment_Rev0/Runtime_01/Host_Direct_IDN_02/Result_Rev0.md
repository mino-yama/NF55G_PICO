# Host単体 USB接続後の識別 結果 Rev.0

2026-11-20。USB-Bなしの冷起動でh/NOT_READY応答を確認した後、Host電源/UARTを維持し、ユーザーが電源ONの7355へUSB-Bを接続した完了通知を受け実行。

## 確認事実

COM22 CH341 1A86:5523、115200/8N1、flowなし、DTR/RTS OFF。Hを1回送信、hでchipid BFCF2EDB84B0B37F、FW meter-host-relay-20261120.1、READYを確認。nonce/CRC/ヘッダ照合後にQ(*IDN?、2000ms)を1回送信。A→T→Rを全て正しいsession/request/timeoutで照合し、R原文はADC Corp.,7355,246410099,  A02とCRLF、32byte。

Host単体のUART→USB CDC→7355→UART識別経路は今回成功。USB-B接続後の無応答は今回は再現しなかった。レンジ変更/READ/NF55G通信/自動再送/Flash変更なし。COM22解放済み。

## 未確認事項

先行の無応答の原因、親GP13入力/親Host現物配線、親経由中継は未解決。単体識別成功は親経由受入完了ではない。USB-RELAY-LINK-01等はOpenを維持し、親経由へ復帰時にHost TXをCOM22のRXだけで受動採取する。Hostは今回の診断親nonceへbind済みのため、親への復帰前にHost/親を無給電から通常起動して新sessionを作る。新親nonceへ無断再bindせず仕様を維持。

[JSONと全イベント](Result.json)／[送信原文](tx.raw)／[受信原文](rx.raw)。
