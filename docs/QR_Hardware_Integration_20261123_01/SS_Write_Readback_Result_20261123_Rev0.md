# QR二連続読取り→SS→D5 実機結果 Rev.0

2026-11-23。ユーザーの書込内容了承後、親のQR／SS実装を配置し、実ATE COM7（57600bps）で検証した。NF55G FWはD5でS1.14Bを確認。QR HOSTはqr-fixed-20261123.1のまま。

## 実機結果：書込み・読戻し成功

|対象|D5事前|D5書込み後|
|---|---|---|
|FW_REV|S1.14B|S1.14B（不変）|
|UNIT_REV|`A5. `|`A1. `（ともに末尾空白1文字）|
|UNIT_LOT|2610|2601|
|UNIT_SERIAL|000832|000001|
|ADU REV／LOT／SERIAL|0000／0000／000000|同じ|
|BBU REV／LOT／SERIAL|0000／0000／000000|同じ|

親ID 69F7D45962CFDFAD、取得ID `Q00ddfa807ef1beb2-00000001-00000001`、試行T000022。

ATEのQR_SCAN受付後、ユーザーが同じQRを2回連続読取。最初の`US250A-CGXE-009491-101A1.2601000001`を固定し、2件目を1件破棄（ignored=1）。QR_GET?の原文とQR_DATA?のSS DATA HEXをPCで期待値と完全照合後に明示QR_WRITEを送った。

実送信は**D5→SS→D5の3フレーム、SSは1回**。SS後のUNIT_SERIAL?はERR:CACHE_INVALIDで、自動D5なし。使用済みIDのQR_WRITEはERR:QR_CONSUMEDで、追加SSなし。明示INFO_REFRESH後に10項目を照会し、上表と完全一致。受信フレームのBCC正常を確認し、D5全100文字のうちUNIT14文字以外（FW、ADU、BBU、予約、PARAMETER）も全て不変だった。

ログdrop=0／終了queue=0、SD write80／flush9、通信中write/flush試行0。TEST_END成立、Logger停止、QR取得失効を確認。NF55Gの最終値は表の書込み後の値であり、元値への復元は行っていない。

## 配置・検証

親の変更対象7ファイルと起動入口を退避。既存runtime設定を保持してQRを有効化し、配置後7ファイルhash完全一致、再起動後active_app／QR有効／SD OK／試行停止を確認してから試験。HOSTのFW書換えやNF55GのFUは実行していない。

QR→SS独立11項目を含む全Host Unit／Mock **527件成功（14.035秒）**。異なる2番目のQRでも最初の値が変わらないこと、未照会／ID違い／timeout／UART異常／旧試行／消費後の無送信、ambiguous時の失効、明示D5照合を検証した。

## CSV回収

`/sd/BANK_A/000001_20261123_145409_T000022.csv`を回収。6,283byte／80記録／全14列正常。親計算とPC SHA-256一致：`acec29d275903ce4236098b14ee9d6d8f58573e083daea0b2e20a7f274ff4fd5`。SS WRITE記録は1行、送信DATAと一致。NF transactionはD5／SS／D5の順。

## 制約・終了状態

今回の結果は通信と書込値・読戻し値の一致確認で、製品PASS判定ではない。電源再投入後の保持は未検証。親受付前からスキャナー内で処理中の旧QRを識別する双方向要求境界、量産のcold-startは未受入。既存IssueはOpen継続。

実機試験の終了後はQRと測定器PIOを停止し、GP9/12/13を入力化。親には新sourceを配置済みだが、通常のATE常駐ループは再開していない。通常再開は親再起動で新構成を起動する。

## 証跡

- [ATE全30操作・前後値・試験結果](SS_HIL_01/result.json)
- [親ログ・二件目受信マーカー](SS_HIL_01/parent.log)
- [CSV原文](SS_HIL_01/000001_20261123_145409_T000022.csv)
- [D5原文全比較](SS_HIL_01/readback_comparison.json)
- [配置manifestと退避hash](SS_Parent_Deployment_01/manifest.json)
- [配置後hash](SS_Parent_Deployment_01/deployed_hashes.json)
- [全527件回帰](SS_Workflow_Final_Host_Mock_Rev0.log)
- [今回の仕様](SS_Workflow_Spec_20261123_Rev0.md)
