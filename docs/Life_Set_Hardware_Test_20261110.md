# LIFE_SET 通常値書込み・読戻し・元値復元（2026-11-10）

## 最新結果：通常値1点と元値復元を完了

準備後にユーザーから「バッテリ、負荷は無し」と回答。物理条件は両方未接続、Sampleのデータクリア許容を引き継いで実施した。以下の準備節の「SL未送信」「回答待ち」は実施前の履歴。

| 工程 | ATE指令・応答 | 新規D0の積算寿命RAW / Query |
|---|---|---|
| 再退避 | DATA_REFRESH → BATT_DEG_TOTAL? | 000 / 0.0％（先行退避と一致） |
| 通常値設定 | LIFE_SET_123 → OK、NF DATA=07B00000 | 07B / 12.3％ |
| 元値復元 | LIFE_SET_RAW=00000000 → OK | 000 / 0.0％ |

- 2回のSLとも正常応答DATA0文字、elapsed=46ms、cmd_retry=0／rsp_retry=0、ambiguous=False。NF送受信BCC一致。
- 各SL直後のBATT_DEG_TOTAL?はERR:CACHE_INVALID。明示DATA_REFRESHでのみ読戻した。通常値設定直後のPS_ON?=1、FW_REV?=S1.13で、既存STATUS／INFOが維持されることを確認。
- D0内OFF期間RAWは、設定前`D0A600000000000000000000000000`、設定後`00000000000000000007B000000000`、元値復元後`000000000000000000000000000000`。寿命RAWは復元できたが、元のOFF期間欄は復元されていない。SL後の実測として記録し、全ての内部動作や将来FWの仕様を断定しない。
- 終了時はPS_ON=1、BATT_ON=0、BATT_CHECK_RUN=0。TEST_END後Self Check全OK、TEST_LOGGER／TEST_LOG_DROPともOK、SD OK、累積drop0、通信IDLE。
- CSVは9220byte、全91データ行14列。256byte分割回収しSD原本とPCコピーのサイズ／SHA-256が一致。SHA-256=`cc3add1c692e09ac4b8c0d6943250c6fab58852a9a14f5cbbca5087c5895995b`。NFフレームは全件BCC確認。
- CSV回収後のsoft rebootで通常アプリ待受へ戻し、ATEのIDN／IDLE／Self Check／SD／drop0を再確認。COM6／COM20は解放済み。
- 通信正常と寿命値の読戻し・復元を確認した範囲。外部電圧・波形・製品動作、電源切入保持は未確認。範囲外・不正DATA・保守値4095は送信していない。製品PASS/FAIL判定なし、OI-08はOpen継続。

実行証跡: [結果集計](../temp/life_set_precheck_20261110_093741/normal_result.json)、[ATE往復](../temp/life_set_precheck_20261110_093741/normal_ate.json)、[CSV・フレーム照合](../temp/life_set_precheck_20261110_093741/normal_csv_analysis.json)、[CSV原本一致コピー](../temp/life_set_precheck_20261110_093741/normal_20261110_094637.csv)、[待受復帰確認](../temp/life_set_precheck_20261110_093741/after_recovery_runtime.json)。実行用スクリプトは[run_normal.py](../temp/life_set_precheck_20261110_093741/run_normal.py)。記録上のSL時刻は09:46:37／09:46:38 JST。

## 準備段階の記録（実施前の履歴）

ユーザーがSLを先行するよう指示し、「Sampleはクリアされても問題無し」と回答。寿命値変更とOFF期間データクリアが許容されることを確認した。バッテリ・負荷の物理接続状態は別途確認中。**本記録時点でSLは未送信**。正常書込み・復元を確認済みとは扱わない。

## 確認できた事実

- Pico COM6、USB記述子と実機unique_id=`69f7d45962cfdfad`を照合。ATEはCOM20、115200/8N1。NF55G FW=`S1.13`、UNIT_SERIAL=`000832`。
- 配置前にローカル診断で通信IDLE、RTC／SD／自己診断正常、drop=0を確認。
- 未配置差分はSL用のnf55_command.py／command_parser.py／command_dispatcher.pyの3ファイル。既存ソースを256byte分割で回収し、長さ・SHA-256照合後に退避。差分はSLのBuilder／Parser追加と正常応答長0文字の検証追加だった。
- Host Unit／Mock NF55Gを再実行、273件成功（2.496秒）。差分3ファイルを一時ファイル経由で配置し、ソース24ファイルを実機compile・SHA-256照合。/main.pyは変更していない。REPL確認後はsoft rebootで通常待受に戻した。
- TEST_START後、D5／D1／D0を明示取得。PS_ON=1、BATT_ON=0、BATT_CHECK_RUN=0。これは製品応答であり、物理接続状態の断定ではない。
- BATT_DEG_TOTAL?=`0.0`、D0 DATA327文字の0始まり162～164=`000`。OFF期間DATA（62～91）とD0全体を退避。
- TEST_END後、Self Checkは全OK、TEST_LOGGER=OK、TEST_LOG_DROP=OK、SD=OK、累積drop=0、通信IDLE。CSVは256byte分割回収、SD原本とPCコピーの長さ・SHA-256一致、全行14列とNFフレームBCCを確認。COM6／COM20解放済み。

## 証跡

保存先: [temp/life_set_precheck_20261110_093741](../temp/life_set_precheck_20261110_093741)

- [配置前照合](../temp/life_set_precheck_20261110_093741/deployment_precheck.json)、[退避検証](../temp/life_set_precheck_20261110_093741/backup_manifest.json)、[検証済み差分](../temp/life_set_precheck_20261110_093741/verified_deployment_diff.patch)、[配置後24ファイル照合](../temp/life_set_precheck_20261110_093741/deployment_after.json)
- [元値・D0・復元指令](../temp/life_set_precheck_20261110_093741/original_life.json)、[ATE往復](../temp/life_set_precheck_20261110_093741/baseline_ate.json)、[CSV検証](../temp/life_set_precheck_20261110_093741/baseline_csv_analysis.json)、[正常回収CSV](../temp/life_set_precheck_20261110_093741/baseline_20261110_094029.csv)

初回の一括HEXによるソース回収では転送欠落が見られたため、`.unverified`として保持し採用しない。正本の退避は256byte分割＋SHA-256確認済みの3ファイル。製品ソースの破損と断定しない。

## 次の操作（未実施）

物理接続状態の回答を記録後、LIFE_SET_123 → DATA Cache無効化確認 → 明示DATA_REFRESH → BATT_DEG_TOTAL?とRAW07Bの確認 → LIFE_SET_RAW=00000000で元値復元 → 明示DATA_REFRESH → RAW000／0.0％を確認する。新しい区間でもTEST_START／TEST_ENDとログ原本照合を行う。

今回は通常値1点と復元まで。範囲外・不正RAW・保守識別値4095は対象外。OFF期間データは寿命RAWの復元では元に戻らない。OI-08はOpen、製品PASS/FAIL判定なし。
