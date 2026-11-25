# セット間5秒の実機試験

2026-11-25、親Picoに戻したSDはATEから `OK`、測定器HOST FW `20261125.2` は `READY`。単発は40.406 mVで完了。初回の400セット起動は測定開始前の親Pico `*IDN?` が12秒無応答で停止。親のSD起動ログでマウントとBANK準備を含む初期化時間が26,195 ms、直前試行 `T000318` が保存済みであることを確認した。 [単発結果](endurance_20261125_125042_624920/result.json)／[初回結果](endurance_20261125_125051_619607/result.json)／[親の状態](endurance_20261125_125051_619607/parent_after_preflight_failure.log)

親Picoのループを同一セッションで再開した12:52の400セット試験では、最初のセット `T000319` は40.405 mV、計器エラー0、終了診断正常、ログ欠落0で完了。第2セットの `TEST_START` は前セットの終了確認から約5秒後に送信したが、12.032秒で受信0バイトのため停止。親Picoはその後、要求を遅れて処理して `T000320` を開始した。親PicoのRAMとUSBログで状態を照合し、測定器に追加コマンドを送らずに `TEST_END` で閉じた。 [試験結果](endurance_20261125_125201_447886/result.json)／[ATE通信](endurance_20261125_125201_447886/ate.jsonl)／[遅着後の親の状態](endurance_20261125_125201_447886/parent_after_start_timeout.log)／[試行の終了](endurance_20261125_125201_447886/failed_trial_close.json)

試行終了後のSD同期再認識を実機上で計測したところ、正常終了まで27,089 ms。現行仕様では親Picoが試行後の連続通信待機250 msを検出すると同期再認識を開始する。その間は次のATEコマンドを処理できないため、5秒間隔の第2セットが無応答となった。測定器HOSTは同一nonce `FF0E33637BDF04BD` で `READY`。今回の停止は測定器へのCDC照会の前に発生した。完了分と遅れて開始した分のCSVは2/2件を親Picoから回収してSHA-256とATE応答を照合した。 [SD同期再認識ログ](endurance_20261125_125201_447886/sd_recovery_runtime.log)／[Logger SD仕様](../../Logger_SD_Spec.md)／[CSV照合](endurance_20261125_125201_447886/csv_export_20261125_125422_548254/csv_manifest.json)

同じ実機とSDでBANKの320件を読取専用で比較した。現行の `listdir` とファイルごとの `stat` は27,119 ms。`ilistdir` の各項目に含まれるサイズを使う方法は1,380 msで、ファイル名とサイズのSHA-256および合計338,184バイトが一致した。新方式でのSD再認識全体の時間と400セット耐久は未検証。診断後に同じ親Picoのループを再開し、親 `IDLE`、SD `OK`、HOST同一nonce `READY`、累積ログ欠落0を確認した。 [ディレクトリ比較ログ](endurance_20261125_125201_447886/sd_directory_timing_streamed.log)
