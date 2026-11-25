# SD再認識を短縮した親Picoでの耐久再開

2026-11-25。セット間5秒の前回試験は第2セットの `TEST_START` で停止し、終了後のSD再認識に27,089 msかかっていた。実機で320件を読み取った比較では、ディレクトリ一覧のファイルサイズを用いる方式で27,119 msから1,380 msに短縮し、ファイル名とサイズの照合結果が一致した。 [前回試験と読取比較](CDC_Endurance_5s_20261125_Rev0.md)

親PicoのBANK集計を変更し、FATの一覧に有効なファイルサイズがある場合はその値を利用した。サイズを取得できない場合は個別 `stat` を使用する。両方式でBANK容量と試行番号集計が一致することを検証し、Host Unit／Mock NF55Gの全536件が成功した。 [実装](../../../src/sd_sink.py)／[回帰テスト](../../../tests/test_logger_sd.py)

対象親Pico `69f7d45962cfdfad` を照合し、旧SDモジュールをPCと実機に退避して候補を配置した。旧版・配置版をSHA-256で照合。再起動時にWindows側のCOM6端末は切断エラーを返したが、その後のATEで親Picoの `IDLE` とSDの `OK` を確認した。測定器HOST FW `20261125.2` を管理RSTで復帰させ、boot nonce `544D61E9D497CE96` と `READY` を確認した。 [配置・退避マニフェスト](sd_bank_scan_deploy_20261125_130302_735862/manifest.json)／[HOST復帰](sd_bank_scan_deploy_20261125_130302_735862/host_rebind.json)

13:03:31 JST、COM5／COM23、セット間5秒、ATE選択値200 mV、入力設定40 mVで400セットの試験を再開。前回無応答だった第2セットの `TEST_START` は641 msで `OK`、測定と終了確認も成功。 [ATE実機記録](endurance_20261125_130331_188284/ate.jsonl)

13:34:33 JSTに240/400セット完了で停止。241回の `TEST_START` は全件 `OK`（547～1,860 ms）。前セットの最終確認応答から次の `TEST_START` までは計測上5.049～5.077秒。READは第241セットを含む全241回で完了（40.402～40.407 mV、最長719 ms）。完了240件の計器エラー値とログ欠落は0、終了診断は全件正常（最長141 ms）。 [耐久試験結果](endurance_20261125_130331_188284/result.json)

第241セットはREAD要求483で40.405 mVを返した。次の `:SYST:ERR?`（要求484）が2,047 msで `ERR:EXT_TIMEOUT:AMBIGUOUS=1`。診断Eはセット間5秒導入前の第234セット停止時と同じ `TIMEOUT_RX0_T1_C0_XNONE_I2000_N2000_D0_S80_P5A_EP81_H1_K1_L0/64_OA2_ON0_OX0_OPD2_OE02|1`。OUT EP `0x02` でACK 2回、IN EP `0x81` の2,000回はすべてNAK、応答0バイト。現行FWの奇数長分割ではこの照会の12バイトを11+1バイトに分けるため、ACK 2回は通常の送信分割と整合する。USB OUTの採取結果から7355内部のSCPI処理や停止原因は特定できない。再送せず `TEST_END` で閉じ、測定器HOSTは同一nonceの `FAULT` を維持した。 [UART原文](endurance_20261125_130331_188284/host_uart.bin)／[停止後の状態](endurance_20261125_130331_188284/failed_trial_close.json)／[前回の同一症状](CDC_Endurance_Retest_20261125_1233_Rev0.md)

親Pico経由でSDから `T000321`～`T000561` の241件を回収した。各ファイルのSHA-256、列数、行数、開始と終了のマーカー、ATE応答を照合した。回収後に同一セッションで親Picoの処理を再開し、親 `IDLE`、SD `OK`、ログ欠落0、測定器HOST `FAULT` を再確認した。400セット耐久とCDCタイムアウトの原因調査は継続。 [CSV回収マニフェスト](endurance_20261125_130331_188284/csv_export_20261125_133446_238675/csv_manifest.json)／[CSV回収後の状態](endurance_20261125_130331_188284/ate_after_csv.log)
