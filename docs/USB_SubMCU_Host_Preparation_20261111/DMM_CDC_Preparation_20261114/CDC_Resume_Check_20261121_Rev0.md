# USB CDC継続確認 2026-11-21 Rev.0

## 確認できた事実

- ユーザー指示でNF55G本体の確認よりUSB CDCの続きを優先。スイッチ操作を伴わない範囲で確認した。
- ユーザー申告: 7355電源ON、背面USB-BとHost接続済み、Host給電済み。実配線・電圧は独立確認していない。
- PC列挙はATE COM7（ELECOM 056E:5004）、監視COM22（CH341 1A86:5523）。
- COM7は57600/8N1、COM22は115200/8N1、DTR/RTS OFF。COM22へは送信せず受動採取した。
- COM7の開始時未読データなし。`*IDN?`は`NF55G_PICO_FIXTURE,Rev.0`＋CR。
- `EXT_QUERY 2000 *IDN?`を一回送信し、`ERR:EXT_TIMEOUT:AMBIGUOUS=0`＋CRを受信。測定器IDNは取得できなかった。
- 同時採取したCOM22は0 byte。監視点自体の電気的な健全性は今回独立確認していない。
- 両ポートをclose済み。READ、設定書込み、自動再送、リセット、Flash配置、NF55G向けコマンドは実施していない。
- Windows PnP追加照会はアクセス拒否のため取得できず、デバイス不在の根拠には用いない。

原記録: [ATE要求・応答と時間](../../../temp/usb_cdc_resume_20261121/150534/result.json)、[Host受動採取](../../../temp/usb_cdc_resume_20261121/150534/host.raw)。

## 推測・ソースとの整合

現行PCソースのExternalInstrumentLinkではsession未確立時、HELLOの応答を待ち、期限切れでTIMEOUT/ambiguous=Falseを返しfaultを保持する。今回のATE応答とHost無受信はこの経路と整合する。ただし実機搭載ソースの照合および親TXの捕捉は未実施のため、HELLO送信・Host受信・7355への未送信を断定しない。

## 未確認事項と再開条件

- Hostの実行状態、搭載版、親→Host UART要求の到達、Host→親応答、監視配線の導通。
- COM22無受信だけでHost停止・USB CDC不良・配線不良のいずれとも断定できない。
- 前回記録では実機版は20261120.3、hotplug候補20261121.1は未配置。今回、実機版の再確認には至っていない。
- タイムアウト後の無条件な追加Queryでは進展しない可能性がある。まず通信配線・対象個体・Host状態を確認し、既存手順で復帰可能になった時点で起動からH/hを採取する。READYと新IDNを確認してから測定を再開する。
- ソフトRESET/WDT/状態クリアは既存の保留方針を維持し、本確認から実装しない。関連IssueはOpen継続。

コード・仕様変更なし。Host/Mockテストの再実行なし（今回の確認は実機読取通信のみ）。
