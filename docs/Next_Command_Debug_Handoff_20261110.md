# 次回コマンドデバッグ 引継ぎ（2026-11-10）

再開後の更新: ユーザーがSampleクリア許容・バッテリ／負荷未接続を回答し、SLの通常値1点と元値復元を完了した。積算寿命RAW000→07B→000、0.0％→12.3％→0.0％を確認。OFF期間欄は元に戻らない。詳細は[SL実機結果](Life_Set_Hardware_Test_20261110.md)。以下の「本日終了」「次回候補」は中断時点の履歴。SLの範囲外評価とBCは引き続き未実施で、BCにはバッテリ・負荷・監視条件の準備が必要。

ユーザー指示により本日の開発・デバッグは一旦終了。今回は記録確認と次回候補の提示のみ。実機接続・コマンド送信・配置・追加テストは行っていない。下記は実施済み結果ではなく、次回の進め方案。

## 1. 再開時の確認

- 直近の開発機記録はPico保守COM6／unique_id `69f7d45962cfdfad`、ATE COM20、NF55G FW S1.13。COM14は別のPico個体。次回も同じ接続・状態とは仮定せず、機器・ポート・電源・バッテリ・負荷を確認する。
- 11/10のATE終端修正は開発機へ配置・実機確認済み。CR／LF／CRLFを受理、空CRは無応答、応答はCRLF。LIFE_SET等の後続ソースが同じ個体へ配置済みかは別途hashで照合する。
- コマンド間隔は約0.1秒以上、Transactionは1件ずつ。長い応答の処理終了を待って次を送る。連続指令で応答を追い越さない。
- 既存Host／Mockの最終確認は273件成功。これは実機未確認機能の成立証明ではない。

最初の確認用コマンド（実送信は次回）：

```text
*IDN?
COMM_STATUS?
PICO_SELF_CHECK?
RTC_CHECK?
SD_STATUS?
LOG_DROP_COUNT?
```

通信IDLE・RTC・SD状態を記録する。DEV-RTC-01（電源断後のRTC保持）は未解決のため、日付を確認してログ時刻を扱う。正常応答だけで未解決IssueをCloseしない。製品読出しへ進む場合はTEST_START後にSTATUS_REFRESH／INFO_REFRESHを明示し、製品状態とFWを取得する。

## 2. 次の書込み系候補：LIFE_SET（SL）

**専用Sample準備と変更可能な条件の確認後に実施する第一候補。** 実装・Host試験・手順作成まで進んでいるが、[既存手順](Life_Set_Hardware_Test_Procedure_20261109.md)では実機送信・追加配置は未確認。先に配置照合と元値退避を行う。今回の提示を実機実行や量産採用の決定とはしない。

| 順序 | コマンド・作業 | 確認点 |
|---|---|---|
| 1 | TEST_START → DATA_REFRESH → BATT_DEG_TOTAL? | D0原文、積算BATT_DEG RAW3文字、OFF期間欄を退避。D0の副作用条件も既存手順で確認 |
| 2 | LIFE_SET_123 | 12.3％の指定例。SL DATA=07B00000、正常応答DATA0文字を照合 |
| 3 | DATA_REFRESH → BATT_DEG_TOTAL? | 新しいD0からRAWと表示値を確認。旧Cacheや自動Refreshを使わない |
| 4 | 元値をLIFE_SET_RAWで明示復元 → DATA_REFRESH → BATT_DEG_TOTAL? | 退避RAW3文字＋予約00000で復元し、RAW一致を確認。成否不明なら復元済みとしない |
| 5 | TEST_END → PICO_SELF_CHECK?／SD_STATUS?／LOG_DROP_COUNT?／COMM_STATUS? | 終了状態・CSV原本を保存。取得と復元が追跡可能であること |

通常値で成立を確認してから、0／4094／4095と、4096／負数／不正RAW等の評価を既存手順に従って段階的に行う。4095は保守識別値、4096は送信桁数も増えるため、単純な通常値試験と混同しない。範囲外のPMEを決めつけず、実応答と新規D0を記録する。SLはOFF期間データをクリアし得るため、寿命RAW復元だけで全データが元に戻るとは扱わない。OI-08はOpen継続。

## 3. その次の候補：バッテリ診断BC

バッテリ・負荷・充放電状態と外部監視が整ってから実施する。前回のバッテリ未接続条件を引き継いだまま開始しない。OI-06／07とr1の受付条件を事前確認する。

- BATT_CHECK_START → BC_MODE?／BC_V1?／BC_V2?／BC_I1?／BC_I2?／BC_TEMP?／BC_SOC?／BC_IR?で取得結果を確認。
- BATT_CHECK_STOP → 明示STATUS_REFRESHで停止後の状態を確認。STOP後のBC CacheはINVALID。
- START／STOPともT2=6000ms、正常応答DATA30文字。STOPの空応答をPicoで正常化しない。
- STOPはTransaction終了後の別指令。実行中Transactionを割り込ませる緊急停止手段ではない。測定状態・外部停止手段の確認を先に行う。
- MODEやProtocol OKを製品PASSと扱わない。充電制御CN／CFを自動追加しない。

## 4. 保留・重複を避ける項目

- 項目別PARAM通常10項目は、変更・D5読戻し・元値復元まで記録確認済み。未実施として繰り返さず、保持・境界値・外部動作は別目的で扱う。
- D0／D1／D5、EL／OL、ERP全4組合せ、CLOCK_SYNC→D2には実機記録がある。再確認は配置変更・新たな異常などの理由がある範囲に絞る。
- FD_READは正式アドレスとREAD-FD-01の確認後。D4は量産不使用・Timing課題あり。QR→SS、補正AD、AR等の未確定仕様を推測して進めない。
- 新HOST／QR／DMMの開発はハード入手後。治具接続の最新説明図は[Rev.2](drawings/NF55G_Fixture_20261110_Rev2/README.md)。

## 5. 次回の証跡保存

現在案件のtemp配下に実施日・試験名別の新規フォルダを作り、機器ID／FW／配置hash、ATE送受信、NF RAW・BCC・retry・elapsed、元値／復元値、外部観測を保存する。CSV回収は256byte分割とサイズ・SHA-256照合を使用し、SD原本とPCコピーの完全性を確認する。結果はReal_Hardware_Test_Logへ追記し、推測・未確認・実測を分ける。

参照: [ATE仕様](ATE_Command_Master.md)、[SL手順](Life_Set_Hardware_Test_Procedure_20261109.md)、[前回開発機試験](Development_Unit_Command_Debug_20261109.md)、[項目別PARAM確認](Parameter_Item_Hardware_Test_20261110.md)、[ATE終端修正](ATE_Line_Ending_Fix_20261110.md)、[CSV回収](CSV_Log_Recovery_Recheck_20261109.md)、[Open Issues](Open_Issues.md)。
