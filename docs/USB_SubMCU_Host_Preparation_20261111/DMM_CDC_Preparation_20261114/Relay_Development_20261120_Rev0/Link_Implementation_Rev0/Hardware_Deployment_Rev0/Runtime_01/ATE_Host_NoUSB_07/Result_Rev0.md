# 外部給電・USB-B未接続起動 試行7 結果 Rev.0

2026-11-20。外部電源OFF、7355 USB-B切離し、5秒程度待機後外部電源ONのユーザー完了通知を受け実施。Host PC USB-Cは未接続、監視はHost GP1入力線。

## 確認事実

COM7/57600 8N1で治具ID NF55G_PICO_FIXTURE,Rev.0+CRを取得。EXT_QUERY 2000 *IDN?を1回送信し、2031ms後ERR:EXT_TIMEOUT:AMBIGUOUS=0+CR。COM22/115200 8N1のRX専用監視でHを75byte取得。CRC/形式正常、request/mode/timeoutは0、payload空、session=F60B2A0C15B817220000000000000000。捕捉例外なし。両ポート解放済み。自動再送/機器設定/READ/NF55G通信/Flash変更なし。

## 比較と限界

| 給電・経路 | USB-B条件 | 観測 |
|---|---|---|
| PC USB-C・HostへPC UART直結 | 未接続で冷起動 | h正常、NOT_READY |
| 上と同じ・起動後USB-B接続 | 接続 | h READY、A/T/R、7355識別成功 |
| 外部給電・親経由（試行6） | 接続済みで起動 | 親Hは監視点で正常、親はTIMEOUT |
| 外部給電・親経由（今回） | 未接続で起動 | 親Hは監視点で正常、親はTIMEOUT |

今回もUSB-Bなし起動で親経由の応答が得られなかった。起動時USB接続順序だけを原因としない。給電源と要求送信元も異なるため、電源異常/Host実行状態/Host入力受理/返答経路等の原因はまだ区別できない。今回は入力線の一方向採取なのでHost TXの有無は直接観測していない。

Host給電線はユーザー接続済み回答だが、実電圧は未測定。次は外部給電中のHost基板給電端子-GND（想定5V）と、可能なら3V3-GNDの実電圧をユーザーへ依頼中。PC USB-C/7355 USB-Bは切離し維持。測定不可なら別の比較手順を選ぶ。測定値を得る前に電源正常/異常を断定しない。USB-RELAY-LINK-01等はOpen維持。

[ATE送受信](Capture_Result.json)／[Host入力線decode](Host_RX_Capture.json)／[入力線原文](host_rx.raw)。
