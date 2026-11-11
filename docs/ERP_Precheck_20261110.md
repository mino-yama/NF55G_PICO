# BURST／PS_OFF_CHARGE 継続デバッグ準備（2026-11-10）

## 確認できた事実

- [前回試験](Development_Unit_Command_Debug_20261109.md)でERP全4組合せの設定、読戻し、Cache無効化、元設定0/0への復元を確認済み。外部BURST動作・消費電力・PS_OFF充電の実測とは区別する。
- 今回 `python -m unittest discover -s tests` はHost／Mock計273件成功（2.201秒）。ERP専用10試験を含む。
- COM6／COM20を検出。COM20のローカル診断はIDN=`NF55G_PICO_FIXTURE,Rev.0`、通信IDLE、自己診断のATE_UART／NF55_UART／RTC／LOGGERすべてOK、RTC_CHECK=OK、SD_STATUS=OK、LOG_DROP_COUNT=0。
- RTC応答は`20261110_121104`。精度比較・電源断保持の確認ではない。終了後COM20解放済み。
- 今回NF55G指令、設定変更、Pico配置、電源・外部信号操作なし。src／testsの変更なし。COM6の個体ID実読出し・配置hash照合は今回未実施。

証跡: [ATE診断JSON](../temp/erp_precheck_20261110/local_check_121105_681231.json)、[実行スクリプト](../temp/erp_precheck_20261110/run_local_check.py)。

## 次の試験と未確認事項

今回の電源・通信、バッテリ／負荷、BURST・PS_ON信号操作の条件をユーザーへ確認中。前回の未接続条件を今回へ流用しない。

1. 条件確認後、明示STATUS_REFRESHで製品状態と元のBURST／PS_OFF_CHARGEを退避。
2. BURST設定と外部信号の条件ごとに明示D1と外部電流・電圧または波形を記録。BURST_ONだけで実動作成立としない。
3. バッテリと充電可能条件を確認後、PS_OFFでPS_OFF_CHARGE無効／有効時の充電電流等を比較。充電許可だけで充電開始を保証せず、CN／CFを自動追加しない。
4. 保存した両設定を対応するERP_SETで復元し、明示STATUS_REFRESHで一致確認。Transactionは1件ずつ、指令間隔0.1秒以上。

ERP-CONDITION-01はOpen継続。信号極性、負荷しきい値、遷移時間、消費電力合否値は未確定であり推測しない。今回の実動作試験は未実施。製品PASS／FAIL判定なし。

## 再開後の初期状態確認（12:23 JST）

ユーザー回答でPico COM6／ATE COM20、NF55G電源ON・通信接続済み、バッテリ／負荷なし、BURST・PS_ON信号操作可能を確認。

TEST_START→明示STATUS_REFRESHでPS_ON=1、BATT_ON=0、BURST_ON=0、BURST=0、PS_OFF_CHARGE=0、BATT_CHECK_RUN=0。再送はcmd=0／rsp=0。TEST_END後の自己診断（TEST_LOGGER／TEST_LOG_DROP含む）すべてOK、SD OK、破棄0、通信IDLE。設定変更なし、COM20解放済み。

証跡: [初期状態](../temp/erp_precheck_20261110/status_122355_187896.json)、[読出しスクリプト](../temp/erp_precheck_20261110/read_status.py)。SD CSV原本のPC回収・BCC照合はこの区間では未実施。

次はPS_ONを維持したまま外部BURST信号を反転してもらい、明示D1でBURST_ONの変化を確認する。操作完了の回答待ち。現在の設定0/0を復元基準とする。バッテリなしのためPS_OFF中の実充電評価は行えない。

## 外部BURST OFFでの読戻し（12:25 JST）

ユーザーが「BURST OFFにした」と回答。明示STATUS_REFRESH後、BURST_ON=0、PS_ON=1、BATT_ON=0、BURST設定=0、PS_OFF_CHARGE=0、BC実行なし。操作前の読戻しもBURST_ON=0のため、この結果だけでは入力の切替検出は未確認。設定変更なし。

再送0、終了時自己診断／SD正常、ログ破棄0、通信IDLE、COM20解放済み。[ATE証跡](../temp/erp_precheck_20261110/status_122555_782844.json)。次はPS_ON維持・BURST ONを依頼し回答待ち。スイッチ表示と電気的極性の対応、低消費動作は未確定のまま。

## BURST ON申告時・有効設定での確認（12:27～12:28 JST）

ユーザーがBURST信号ON・PS_ONと回答。明示D1はPS_ON=1、BURST_ON=0、ERP設定0/0。さらにERP_SET_1_0でBURSTを有効化し、両設定QueryがCACHE_INVALIDとなることを確認して明示D1を取得した。設定は1/0へ変化したがBURST_ON=0を維持。ERP_SET_0_0→明示D1で元の0/0への復元を確認。終了時PS_ON=1、BATT_ON=0、再送・ログ破棄0、自己診断／SD正常、通信IDLE。COM20解放済み。

証跡: [ON申告後D1](../temp/erp_precheck_20261110/status_122738_847779.json)、[有効設定と復元](../temp/erp_precheck_20261110/enabled_restore_122829_647108.json)、[実行スクリプト](../temp/erp_precheck_20261110/check_enabled_restore.py)。今回のSD CSV回収・生フレームBCC照合は未完了。回収処理は標準Pythonのmpremote未導入で停止し、別環境による再試行もシェル起動のアクセス拒否で実行に至っていない。ATE JSONは保存済み。

ユーザーから「ONでGND接続」と回答。これは操作回路の説明であり、NF55G端子実測ではない。その後ユーザーがON/OFFと回路開放／閉路を整理してテストすると回答したため、信号操作を伴う試験は待機する。

| 記録項目 | 今回の確認範囲 |
|---|---|
| スイッチON | ユーザー説明ではGND接続。製品端子の電圧・導通は未測定 |
| スイッチOFF | OFF操作の申告あり。実際の開放状態は未測定 |
| 製品BURST_ON | OFF／ON申告時とも0。有効設定1/0でも0 |
| BURST有効設定 | 0→1→0の読戻しと復元を確認 |

次回は「接点開放」「GNDへ接続」を電気的条件として記録し、各条件で明示D1のBURST_ONを比較する。操作表示だけで受信論理や不具合原因を確定しない。低消費動作・実充電は未確認、ERP-CONDITION-01はOpen継続。Picoソース変更・配置なし。
