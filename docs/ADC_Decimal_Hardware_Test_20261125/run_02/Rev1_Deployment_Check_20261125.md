# Rev.1 実機配置の接続確認

予定する初回試験は `BATT_CHG A→P1`。操作者申告の7355 DCV表示は9.174 mV。ATE COM5は親Picoの `*IDN?`、`IDLE`、SD `OK`、測定器HOST `20261125.2` の `READY`（nonce `4484B624AB211315`）、ログ欠落0を返した。配置候補6ファイルと試験ランナーのPC側構文確認が成功した。 [ATE事前確認](13_rev1_deploy_precheck.log)

親Picoの保守USBを再接続した後も、PCで有効なシリアルポートはCOM5とCOM23のみ。Windows PnP上で、親Pico `69F7D45962CFDFAD` が以前使っていた `Port_#0003.Hub_#0004` に「デバイス記述子要求の失敗」、問題コード43を確認した。当該PnPデバイスの再起動はWindowsのアクセス拒否で実行できなかった。親Picoの保守接続を復帰させるため、別ポート／ケーブルでの再接続を依頼。新版の配置、試験開始、校正書込みはいずれも未実施。

## 配線復帰後の配置

親Picoは配線修正後にCOM6で認識し、個体ID `69F7D45962CFDFAD` が一致した。初回のステージ上のcompileで `command_parser.py` のタプル展開をMicroPythonが拒否。現行ファイルとの差し替え前に停止したため、位置を明示する構文に修正して新しいステージから再試行した。修正版で全544件のPC回帰が成功。親Picoで候補6ファイルの事前compileと配置前後のSHA-256照合に成功した。測定器HOSTは再結合後に `READY`、FW `20261125.2`、nonce `28DC3FAC659AE8DB`。 [初回配置ログ](integrated_20261125_144102_965633/operations.jsonl)／[修正版マニフェスト](integrated_20261125_144228_568098/manifest.json)／[HOST復帰ログ](integrated_20261125_144228_568098/host_rebind.json)

## BATT_CHG AからP1の実機試行

14:43 JST、サンプル `S1.14B`／UNIT `000001` をD5で照合。新コマンドで実行し、`CAL_MEASURE_BATT_CHG A 4000 :READ?` から `CAL_MEASUREMENT_BATT_CHG? A` によって7355原文 `+0009.177E-03` V（9.177 mV）を取得した。1 mΩ換算値9.177 Aを `CAL_WRITE_BATT_CHG A P1` で保持値からADへ送り、送信DATA `414112D4FE` を確認。続く `AD_VERIFY_BATT_CHG P1` は `OK:AD_VERIFY:BATT_CHG:P1:4112D4FE:00000003:1:1`。ADとARはそれぞれ1回。両応答のBCC・データ長・P1のADC値を照合し、対象外のAR欄は変更前から一致した。Picoによる上限拒否がなく、実測を明示書込みに通せることを確認した。送信9.177 AとARの整数読戻し3は不一致で、実際の内部保存値は未確認。 [ATE通信ログ](cache_point_20261125_144342_461391.json)

`TEST_END`、直後の自己診断、SD `OK`、ログ欠落0を確認。SDから試行 `T000565` のCSVを回収し、39データ行・14列とSHA-256 `6966cb3a3756ab0530b42a149e92d36a62ae5fc80ac26cf5b034fef356c0b85c` を照合。回収後も親Pico `IDLE`、SD `OK`、HOST `READY`、ログ欠落0。残りの測定点は操作側の条件準備待ち。 [回収CSV](20261125_144342_T000565.csv)／[回収後のATE照会](15_rev1_batt_chg_post_state.log)

## BATT_V AからP1の実機試行

14:47 JST、操作者指定は8.120 V。初回の測定は `ERR:CAL_MEASUREMENT_OVERRANGE`。7355の `RANG?` と `CONF?` は約2 Vを返し、校正書込みは行わず試行終了。ATEから `:SENS:VOLT:DC:RANG 20` を1回送信したところ、設定読戻しは約200 V。計器エラー0、`READ?` で8.1272 Vを実測したため、その読戻しレンジで書込み試行を行った。設定指定と読戻しの差は未解決。 [初回測定](cache_point_20261125_144759_460814.json)／[初期レンジ](16_batt_v_range_precheck.log)／[レンジ変更と確認](17_batt_v_range_20v.log)

14:48 JST、`CAL_MEASURE_BATT_V A 4000 :READ?` の原文 `+008.1272E+00` VをCacheに保持し、`CAL_WRITE_BATT_V A P1` で実測値8.1272 Vを1回送信した。AD DATAは `2141020903`、ARは `OK:AD_VERIFY:BATT_V:P1:41020903:00000008:0:0`。AD／ARのBCCとDATA長、対象外の欄が直前の実機試行から変わっていないことを確認した。ARの整数読戻し8は送信値8.1272 Vと不一致。P1のADCはAD／ARとも0で、ADCが0となった理由と内部保存値は未確認。 [ATE通信ログ](cache_point_20261125_144854_972100.json)

`TEST_END`、直後の自己診断、SD `OK`、ログ欠落0。SDから `T000567` のCSVを回収し、39データ行・14列・SHA-256 `07db1ffe77bdeac7e9d9e3789958fee9254615730bcda0667b3b5ee0d0e7a1a2` を照合した。 [回収CSV](20261125_144855_T000567.csv)
