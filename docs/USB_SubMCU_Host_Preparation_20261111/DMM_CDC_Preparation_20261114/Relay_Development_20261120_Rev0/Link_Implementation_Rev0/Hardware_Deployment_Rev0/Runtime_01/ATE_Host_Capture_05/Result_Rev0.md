# 親経由・Host TX受動採取 試行5 結果 Rev.0

2026-11-20 17:15 JST。ユーザーの親経由配線復帰・電源投入完了通知後に実施。

## 確認事実

COM7 ELECOM 056E:5004、57600/8N1から治具*IDN?を1回送り、NF55G_PICO_FIXTURE,Rev.0+CRを受信。EXT_QUERY 2000 *IDN?を1回送り、2015ms後ERR:EXT_TIMEOUT:AMBIGUOUS=0+CR。7355の識別応答は未取得。

同時にCOM22 CH341 1A86:5523、115200/8N1、RX専用（Host GP0へ接続する案内）でHost TXを受動採取。受信0byte、捕捉例外なし、フレームなし。COM22へのwriteは行っていない。両ポートは解放済み。自動再送、レンジ変更、READ、NF55Gコマンド、Flash変更なし。

## 推測と未確認事項

PC USB-C給電のHost単体では直前にREADYとA/T/R、7355識別取得に成功した。一方、親経由の外部給電時には監視線にHost返答が観測できなかった。Host外部給電の復帰、親からのH送信/Host GP1への到達、Host現在の起動/USB状態、受動監視線の現物接続は未確認。受信0byteだけでHost無給電や親UART不良を断定しない。

次は親だけでなくHost側の外部5V/GND給電線が復帰しているかユーザーへ確認中。確認前の追加再送・Flash変更・無断復帰はしない。Host USB-Cと外部5Vは同時接続しない。必要なら次に親TX→Host RXを受動採取して経路を切り分ける。IssueはOpen維持。

## 証跡

[ATE送受信](Capture_Result.json)／[Host TX捕捉結果](Host_TX_Capture.json)／[ATE受信原文](all_rx.raw)／[Host TX受信原文](host_tx.raw)。
