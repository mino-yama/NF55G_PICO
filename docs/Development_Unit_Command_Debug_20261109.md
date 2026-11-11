# 開発機・実装済みATEコマンド実機デバッグ（2026-11-09）

追記・訂正: CSV列欠けはSD原本にはなく、旧PC回収ファイルの欠落だった。SD原本とのサイズ・SHA-256照合と一括回収の再現で確認。正常回収版では項目別SPの送信原文・BCCも一致。ATEの実運用条件は0.1秒に1コマンド程度とユーザー指定があり、101ms以上の117コマンドではログ破棄0・全行14列だった。詳細は[CSV回収再確認](CSV_Log_Recovery_Recheck_20261109.md)。

対象はPico 2 REPL=COM6（固有ID 69f7d45962cfdfad）、ATE=COM20、NF55GサンプルFW=S1.13。ユーザー申告でNF55G通信ケーブル接続済み・電源ON、バッテリと負荷は未接続。COM20は115200bps／8N1／CRLF。COM6をREPLで停止した間はCOM20が無応答となり、再起動後に応答が戻ることを確認済み。Picoは製品PASS/FAILを判定していない。

## 確認できた事実

| 対象 | 結果 | 実機確認の範囲 |
|---|---|---|
| D0 / D1 / D5 | いずれもOK、再送0 | D0の43、D1の37、D5の26項目を個別ATE Queryで取得。Queryからの自動Refreshなし。D0/D1/D5の応答DATA長327/15/100文字、生フレームBCC一致。 |
| EL / OL | EL全4ブロック、OL全8ブロックがOK、再送0 | 各履歴のDATEHOUR/ID Queryを取得。代表ブロックの応答DATA長82文字、BCC一致。履歴内容の製品仕様上の正否は判定していない。 |
| D2 | SC前に2回ERR:SQE、SC後にOK | SC前の応答はD2 DATA=SQE、BCC一致。SC後は再送0、30文字の正常応答。PS_ON=1。SC前のSQEがSC未完了条件による可能性は高いが、初期内部状態を直接取得できず原因確定とはしない。D2-PS-01はOpen継続。 |
| CLOCK_SYNC | `261109174156`でOK | SC応答とBCC一致。D0の製品日時は設定前`20260401_042601`、設定後`20261109_174156`。製品時刻は変更された。長期精度・電源断保持は未確認。 |
| ERP設定 | `1_0`、`1_1`、`0_1`、`0_0`がすべてOK | 各SE後はSTATUS QueryがERR:CACHE_INVALID、明示D1後にBURST/PS_OFF_CHARGEが指定値と一致。BURST_ONは全時点0。元の`0/0`へ復元し再読戻し。ログ内SE/D1フレームは全BCC一致。外部BURST信号、消費電力、出力変化は未測定。 |
| PARAM_SET／項目別PARAM | どちらもOK | D5の現行50文字を同値で一括書戻しし、次にEVENT_ENABLEの現値0を項目別で同値設定。各SP後INFOは無効化、明示D5後に全26項目一致。取得したD5の100文字全体が前・中・後で一致。SP正常応答DATA0文字。値の実変更、保持、保護動作は未確認。 |
| ローカル拒否 | 期待どおり | FW_UPDATE=ERR:FU_DISABLED、不正FDアドレス、未確定CHG_IR_THD、範囲外PARAMを拒否。CLEAR_DATAはERR:UNKNOWN_CMD。試験CSVにNF55カテゴリとTransactionは0、FUを含む製品送信フレームなし。 |

各区間でTEST_START/ENDを使用。間隔を空けた区間は終了時Self Check、SD_STATUS、通信IDLEが正常、試験中のログ破棄0。最終確認はPS_ON=1、BATT_ON=0、BURST=0、PS_OFF_CHARGE=0、FW_REV=S1.13、SD OK、通信IDLE、累積drop0。COM6／COM20を解放し、通常アプリ待受へ戻した。製品12V出力等の外部測定は実施していない。

## ログ系の追加観測と未確定事項

- 339件のATE応答をほぼ無間隔で送った最初の区間では、D0/D1/D5/EL/OLは通信成功したが、試験ログ破棄391件、最終Self CheckはTEST_LOG_DROP=391でNG。LoggerのRAM Queue上限は256件であり、ATE要求が連続している間は`service_once`がSD排出処理よりATE処理を優先する。今回の条件が破棄に寄与したと考えられるが、量産ATEの実間隔・許容条件は未確認。同じCache Query106件を75ms間隔で再実施すると当該試験の破棄0、Self Check OK。最初の累積391件はアプリ再起動まで保持され、その後の累積0は消去されたことを表し、最初の記録が復旧したことではない。LOGGER-BURST-01として追跡する。
- PARAM項目別SPの旧PC回収CSVで送信RAWの1行に列欠けがあり、`raw_hex`欄が空だった。再確認でSD原本は正常、旧PCコピーに96 byte不足が判明した。正常分割回収版ではSP/D5全10フレームのBCCが一致。LOGGER-CSV-01はPC回収経路の問題として訂正し、内部欠落箇所の確認を残す。
- D3はLIFE_CALCのclear副作用、D4はAC_FAIL_COUNTのclear副作用と既知Timing課題があり今回送らない。FDは原典のID表記と正式アドレス未確認のため保留。BCはバッテリ未接続、充放電・バックアップ・再起動は外部監視条件未整備のため実動作試験を保留。RP、CD、CL、SL等の初期化・消去・寿命変更は既存データを変えるため今回実施していない。これらの実装済み入口の未試験を正常扱いしない。RTC電源断保持DEV-RTC-01もOpenのまま。

## 証跡

- [全読出し・Query応答339件](../temp/dev_acceptance_20261109_run01/implemented_read_debug.json)、[間隔を空けたLogger再試験](../temp/dev_acceptance_20261109_run01/paced_logger_debug.json)
- [代表読出しCSV](../temp/dev_acceptance_20261109_run01/focused_20261109_173850.csv)、[フレーム解析](../temp/dev_acceptance_20261109_run01/focused_frame_analysis.json)
- [ERP応答](../temp/dev_acceptance_20261109_run01/erp_debug.json)、[ERP CSV](../temp/dev_acceptance_20261109_run01/erp_20261109_174034.csv)
- [CLOCK_SYNC／D2応答](../temp/dev_acceptance_20261109_run01/clock_d2_debug.json)、[CSV](../temp/dev_acceptance_20261109_run01/clock_d2_20261109_174151.csv)
- [PARAM同値試験](../temp/dev_acceptance_20261109_run01/param_same_value_debug.json)、[CSV](../temp/dev_acceptance_20261109_run01/param_20261109_174306.csv)、[D5/SPフレーム解析](../temp/dev_acceptance_20261109_run01/param_frame_analysis.json)
- [ローカル拒否](../temp/dev_acceptance_20261109_run01/local_rejection_debug.json)、[NF送信なしCSV](../temp/dev_acceptance_20261109_run01/local_20261109_174514.csv)、[最終状態](../temp/dev_acceptance_20261109_run01/nf55_link_final.json)

ソース・Pico配置は変更していない。Host/Mockの再実行はせず、実機のATE UART、NF55G UART、SD CSVで確認した。RTC電池装着後の電源断保持は未再試験。
