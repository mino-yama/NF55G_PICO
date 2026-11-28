# 7355 R3（200 mVレンジ）限定受入結果 Rev.0

2026-11-28。配線修正後のPC→ATE→親Pico→HOST→7355経路で、R3の校正用取得と400セット耐久・実SD回収照合を完了した。今回の通信・取得・Loggerの限定受入基準を満たした。製品PASS／FAILや実シャントの校正精度を判定するものではない。

## 条件と結果

| 項目 | 実施条件・結果 |
|---|---|
| 親Pico | 69F7D45962CFDFAD。回収後に配置37件SHA一致・実行中新HOST ID・PIO動作・fault=Falseを確認 |
| 測定器HOST | 新個体73AD3A60D10514E9、meter-host-relay-20261125.2 |
| 7355 | ADC Corp.,7355,246410099, A02。ADC／DCV／R3／INIC1／TRS0／H0、PR4 |
| 入力 | ユーザー設定40 mV。200 mV入力は先行試行でOLとなり校正取得を拒否したため、変更後の別試行で評価 |
| 校正用取得 | DISCHG_I／BATT_CHGのA/BとDISCHG_I A再取得、計5件成功。V→mV→A、原文・ID・対象・点・再照会・旧ID拒否・終了失効を確認 |
| 耐久 | 400／400セット完了。2026-11-28 19:36:31～20:40:04 JST、約1時間3分33秒 |
| セット間隔 | 設定1秒。実測399箇所で1.048875～1.081290秒 |
| MD? | 400件の完全対応応答、39.2019～39.2576 mV。156～641 ms、中央値375 ms |
| 計器エラー | ERR? 400件すべて+0,"No error" |
| HOST原文 | 全要求のsession/request/終端/原文相関をランナーで照合。A/T/R各806（試験前照会を含む）、管理i=2、E=0 |
| 起動・再送 | sessionはdd66808f914230a69290db097e8bb8baの1種類。親nonceとHOST nonceは終了後・CSV回収後も同じ。機器コマンド自動再送・試験中リセット・設定変更なし |
| TEST_START | 2,703～9,218 ms、中央値6,875 ms。ATEの12秒待ち以内 |
| Logger | 全400セットでTEST_LOGGER／TEST_LOG_DROP正常、SD OK、LOG_DROP_COUNT=0、終了時IDLE |
| 実SD CSV | 400／400件、14列・計4,400データ行。開始終了・ATE測定原文を個別照合。SD原本とのSHA一致に加え、PC保存実ファイル全400件のSHAを再照合 |
| 回収後 | 通常ATEの自己診断全項目OK、SD OK／drop0、HOST READY・同じ起動ID、7355 R3・連続／即時・H0を再照会。常駐処理再開・COM6／COM7／COM23解放済み |

入力設定40 mVと、7355の実測原文を区別する。上記の値の差・変動について、入力源の校正や精度保証をこの通信試験だけから判断しない。

## 証跡

- [400セットの実行結果](endurance_20261128_193631_024302/result.json)／[ATE全原文・HOST相関](endurance_20261128_193631_024302/ate.jsonl)／[HOST UART原文](endurance_20261128_193631_024302/host_uart.bin)
- [400セットの独立集計](endurance_20261128_193631_024302/analysis.json)
- [実SD CSV400件のマニフェスト](endurance_20261128_193631_024302/csv_export_20261128_204041_167676/csv_manifest.json)／[回収CSVフォルダ](endurance_20261128_193631_024302/csv_export_20261128_204041_167676/csv/)
- [PC実ファイルSHA・回収後実機の最終照合](endurance_20261128_193631_024302/acceptance.json)
- [校正用取得5件・単発CSV事前照合](Corrected_R3_Acquisition_Rev0.md)
- [Host Unit／Mock596件成功](corrected_host_mock.log)／[耐久ランナー模擬6件成功](replacement_runner_tests.log)

実行結果のTRIALS_COMPLETE_CSV_PENDINGは耐久終了時の段階記録として保持した。回収・PC再ハッシュ・回収後実機の最終結果はacceptance.jsonのstatus=OKで確認する。

## 復旧の経緯と未採用記録

ユーザーが量産治具化時のTX同士／RX同士の逆接を修正した後、親―HOST管理通信が復旧。正式HOST RESETを1回実施し、NOT_READYから新起動ID・READYとなり7355 IDNが一致した。[配線修正後の復旧](Corrected_Wiring_Recovery_Rev0.md)。受入400セット開始後にはリセットを行っていない。

途中の別CSV回収開始記録csv_export_20261128_204348_161648は、COM6使用中で原文0件となった不完全出力であり採用しない。元の回収csv_export_20261128_204041_167676が400件完了・照合成功し、そのPC実ファイル全件を最終確認した。失敗記録は削除しない。

## 残課題・範囲

実シャント・3回路A/B動作条件の通し、NF55GへのAD書込みと別AR照合、製品校正精度、電源再投入後の保持、他DMM型式、QR等を含む量産複合負荷は今回の限定受入に含めない。入力200 mVのOLを無視して有効校正値へ採用していない。関連Open Issue全体は独断でCloseしない。

保存済み製品コードは変更していない。交換HOSTの通常FW配置と親の個体ID1項目変更を保持し、今回追加した校正・耐久・集計・CSV回収／最終確認スクリプトと実行証跡は本案件に保存した。
