# 外部給電・PC UART直結と親H原文比較 結果 Rev.0

2026-11-20。ユーザーの親TX/RX切離し・PC UART直結・外部給電・USB-C/7355 USB-B未接続の完了後に実施。

## 確認事実

Host_External_UART_01: COM22からHを1回送信しh正常。基板ID BFCF2EDB84B0B37F、FW meter-host-relay-20261120.1、NOT_READY、31ms。

Host_External_Replay_01: 次に試行7の監視原文host_rx.raw（親H 75byte）をdecodeしてHの意味条件を照合し、同じバイト列をPC UARTから1回送信。hのCRC/nonce/ヘッダ/ID/FWを照合しNOT_READY、15ms。今回はUSB-B未接続でHostはREADYではないため、前のHでsession bindせず、別nonceのHへの照合も規約内。自動機器コマンド再送ではなくH書式の比較診断。Q/SCPI/レンジ/READ/NF55G通信/Flash変更なし。COM22解放済み。

## 推測と未確認事項

外部給電でもHost実行とPC UARTでの受信/応答は確認できた。親の照合原文もHostが受理できる。ただし親直結時の起動直後のデータ、信号の電気条件/ビットタイミング、Host内部の受信状態は未確認。単純なH本文不一致だけを原因にはできないが、電源品質や実信号等を断定していない。

コード上、HostのUART readerはCRLFまで累積し、先行する起動時データがある場合は最初の正常Hと同じ不正行として破棄され得る。これは未検証の仮説であり実起動データ未採取。次は外部電源OFFで親経由/Host GP1受動監視へ戻し、待受開始後に外部電源ON、通知後にATE識別/照合を各1回行う。最初から生原文を保存して検証する。IssueはOpen維持。

[PC UART直結JSON](../Host_External_UART_01/Host_UART_Result.json)／[親H原文送信JSON](Host_UART_Result.json)／[送信原文](H_tx.raw)／[受信原文](H_rx.raw)。
