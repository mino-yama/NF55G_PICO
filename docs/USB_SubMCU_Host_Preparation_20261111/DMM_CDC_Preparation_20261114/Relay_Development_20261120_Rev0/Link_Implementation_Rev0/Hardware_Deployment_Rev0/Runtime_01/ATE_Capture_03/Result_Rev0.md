# 接続復帰後の中継試験3 結果 Rev.0

ユーザーの接続・投入完了通知後、試験を実施。COM5の事前検査では変換器がなく、コマンド送信前に停止。再列挙で唯一のELECOM 056E:5004がCOM7、LOCATION=1-2であることを確認し、COM7用の別スクリプトで実行した。

## 確認事実

- COM7、57600/8N1、flow controlなし、DTR/RTS OFF。
- 治具へ*IDN?+CRを1回write。10秒待機で応答0byte、識別未成立。
- EXT_QUERYは未送信。7355の識別、レンジ変更、READ、NF55G通信、自動再送、Flash変更は行っていない。COM7は終了時解放済み。
- 先行の親単体PIO診断とHost単体HELLOの成功は、現在の通常配線・給電・ATE応答の成功を意味しない。

## 未確認事項と次の確認

親Picoの外部電源線が単体診断後に復帰しているか、親の通常起動、ELECOMのATE側接続の現状は未確認。応答0byteだけで原因を断定しない。USB-RELAY-ATE-01とUSB-RELAY-LINK-01はOpen継続。ユーザー指示どおり追加デバッグは行わず、通常中継試験のための給電・ATE接続確認を依頼する。

[送受信記録](Capture_Result.json)／[受信原文](all_rx.raw)。
