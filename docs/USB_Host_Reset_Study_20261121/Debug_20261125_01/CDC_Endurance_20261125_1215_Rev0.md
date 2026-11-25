# 測定器HOST診断FW 20261125.2の400セット耐久試験

2026-11-25 12:15:28～12:18:19 JST、固定配線、ATE COM5、HOST TXの受信専用COM23で実施。ATE選択値200 mV、入力設定40 mV。7355の `:CONF?` 原文は `"VOLT +1.999999E+00,+1.000000E-07"`。受入基準に従い、治具側からレンジ設定を変更せずに実施した。結果は80/400セット完了、第81セットのREADで停止。 [試験結果](endurance_20261125_121528_136924/result.json)／[受入基準](../CDC_Endurance_Acceptance_20261124_Rev0.md)

完了した80件のREADは40.406～40.408 mV、最長672 ms。計器エラーは全件0。`TEST_END` 直後の自己診断は最長125 msで全件正常。SD状態はOK、ログ欠落の増加は0件だった。

第81セットの `EXT_QUERY 10000 :READ?` は10,047 ms後に `ERR:EXT_TIMEOUT:AMBIGUOUS=1`。COM23の記録には同一session・要求167のAとTが残った。RとEは記録に残らなかったため、USB OUT/INの診断値とタイムアウト原因は未確定。停止後もHOST boot nonceは `4A7326AC8DE43546` で一致し、HOSTはFAULT。測定の再送やHOSTのリセットを行わず、証跡保存のため `TEST_END` を実行した。 [ATEとHOSTフレーム](endurance_20261125_121528_136924/ate.jsonl)／[UART原文](endurance_20261125_121528_136924/host_uart.bin)／[停止後の確認](endurance_20261125_121528_136924/failed_trial_close.json)

親PicoのSDから T000002～T000082 の81件を回収した。全件でファイル数・行数・14列・試行開始/終了マーカー・SHA-256・ATE応答原文を照合した。 [回収マニフェスト](endurance_20261125_121528_136924/csv_export_20261125_121844_943718/csv_manifest.json)／[第81セットCSV](endurance_20261125_121528_136924/csv_export_20261125_121844_943718/csv/20261125_121808_T000082.csv)

ATE側がエラーまたは無応答になった際に、PC側ランナーがCOM23を最大約1秒追加で受信するよう修正した。受信待ち中の送信はなく、停止基準は維持する。失敗試行の終了処理は記録上のHOST版を照合するよう修正した。遅着して分割されたEの回収とREADの再送なしをPC上の模擬回帰で確認した。Host Unit／Mock NF55G 535件、追加回帰1件が成功。修正したランナーによる再耐久試験と実機E回収は未実施。 [ランナー](run_cdc_endurance.py)／[追加回帰](test_run_cdc_endurance.py)／[終了処理](preserve_failed_trial.py)
