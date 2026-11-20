# USB-B切離し比較 結果 Rev.0

2026-11-20。ユーザーの7355 USB-B切離し完了後、Hostの電源/UARTを維持した条件でHを1回送信。

## 確認事実

COM22 CH341 1A86:5523、115200/8N1、flowなし、DTR/RTS OFF。Hのwrite戻り値75。3000ms待機で受信0byte。基板ID/FW版/状態は今回取得できていない。Q/SCPI/レンジ変更/READ/NF55G通信/Flash変更/自動再送なし、COM22解放済み。

診断スクリプトは空受信に対してdecode_frameを呼びContractError(FRAME_ENDING)を記録した。これは実機から不正フレームを受信した意味ではなく、実際の観測は無応答。原JSON/原文は改変せず保持する。

## 推測・未確認事項

USB接続状態から切断しただけではHost照合応答は回復しなかった。電源/実配線/Host実行状態/USB内停止等の原因を特定していない。次はHostとUART変換器のUSB給電を一旦除去し、USB-B未接続のまま冷起動してH応答を比較する。GPIO経由の給電を避けるため変換器側もPC USBを外す。外部5VはOFF維持。USB-RELAY-LINK-01はOpen維持。

[診断JSON](Host_UART_Result.json)／[受信原文](H_rx.raw)／[送信原文](H_tx.raw)。
