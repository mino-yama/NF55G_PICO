# Host冷起動比較 結果 Rev.0

2026-11-20。7355 USB-B未接続、外部電源OFFのままHost USB-CとUART変換器のPC USBを一旦外し、Host USB-C→UART変換器USBの順で接続した旨のユーザー完了通知後に実施。

## 確認事実

COM22 CH341 1A86:5523、115200/8N1、flowなし、DTR/RTS OFF。Hを1回送信しh応答を受信、CRC/nonce/ヘッダを照合。基板ID BFCF2EDB84B0B37F、FW meter-host-relay-20261120.1、状態NOT_READYが一致。今回の経過時間は16ms。Q/SCPI/レンジ/READ/NF55G通信/自動再送/Flash変更なし、COM22解放済み。

## 推測・未確認事項

USB切離しだけでは無応答だったが、USB-Bなしの冷起動で照合応答が回復した。現在のHost起動とUART双方向は確認できたが、先行無応答の原因をUSB処理停止/電源等に確定しない。次は電源/UARTを維持し7355 USB-Bだけ接続して、Hの応答/READY状態を確認。READYと実機ID/FW版が一致する場合のみ*IDN?のQを1回送る。

Host_Direct_IDN_02へ同じ診断スクリプトを別名保存して未実行。過去資料/ログは保持。USB-RELAY-LINK-01はOpen維持。

[JSON](Host_UART_Result.json)／[H送信原文](H_tx.raw)／[h受信原文](H_rx.raw)。
