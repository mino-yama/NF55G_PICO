# S1.14BサンプルでのAD／AR小数試験

2026-11-25。ユーザー了承のサンプル `UNIT 000001`、FW `S1.14B`。変更前にD5で個体を照合し、ARで製品が返した全10点のADC／REF8原文を保存した。BATT_CHG Point 1はADC 2292、REF8 `00000001`。AR原文は保存したが、小数を含む内部値はARから復元できない。 [変更前ARフレーム](baseline.hex)／[全10点](baseline.json)／[通信ログ](01_baseline.log)

ARリクエストはDATAなし、正常応答はDATA 140文字。ADはレビュー版と同じTYPE `4`、Point `1`、VALUE8で送信し、同じTYPE／PointのDATA 16文字応答を実機で確認した。AD／ARの1,000 msはこの診断の観測期限。各ADを一回だけ発行し、別の明示ARで読戻した。実測校正値に用いる前の人工値試験として、1点に4値を設定した。

| 指定値 A | AD VALUE8 | AD応答の計算値8文字 | AR REF8 | AR ADC |
|---:|---|---|---|---:|
| 0.50 | `3F000000` | `4(*444-+` | `00000000` | 1 |
| 1.85 | `3FECCCCD` | `44A8699A` | `00000001` | 1 |
| 1.86 | `3FEE147B` | `44A9A99A` | `00000001` | 1 |
| 2.25 | `40100000` | `44DA699A` | `00000002` | 1 |

0.50 AのAD応答はBCCと長さが正しい一方、計算値欄に16進数以外の文字を含んだ。初回スクリプトはこの欄を拒否して停止し、続けて書込みなしのARで初回の結果を取得した。残り3値は初回の結果と対象外の全欄を照合してから実施。最終ARは当該点ADC 1／REF8 `00000002`、その他の点は変更前と同一。1.85／1.86 AでAD応答の計算値欄は異なるが、ARには両方とも `00000001` が返る。この個体のAR出力では小数を区別できず、EEPROMや実際の補正係数に小数が保持されるかは未確認。 [0.50 A書込み](02_decimal_cases.log)／[明示AR](03_after_first_readonly.log)／[残り3値の原文](04_remaining_cases.log)

## 7355実測からの診断候補

既存の `CAL_MEASURE` と `CAL_MEASUREMENT?` を使用し、照会済み取得IDを `CAL_WRITE <取得ID> P1` で明示指定する候補を実装した。測定Cacheの値を小数のままADのfloat32に格納する。別の `AD_VERIFY BATT_CHG P1` がARを発行し、書込値のfloat32とこの実機で観測した整数のREF8を比較する。数値が異なる場合は `ERR:AD_VERIFY_MISMATCH`、期限切れは `ERR:AD_VERIFY_TIMEOUT`。比較原文はCALログに残す。AD応答の計算値欄が不正な場合は成否不明とし、同じ取得IDからの再送を防ぐ。サンプルのBATT_CHG A→P1の診断候補で、他系統・他点や量産APIは未確定。

候補を親PicoのRAMに読み込み、試行外の `AD_VERIFY` が `ERR:CAL_NO_ACTIVE_TRIAL` で拒否されることを確認した。試行外の照会では製品ARを送信しない。測定器HOSTは校正準備のため復帰させ、FW `20261125.2`／新nonce `564F8C13F12827F1`／`READY` を確認。候補のMock 5件と既存回帰536件を通過。 [候補](calibration_candidate.py)／[候補試験](test_calibration_candidate.py)／[実測ランナー](run_cache_point.py)／[実機の準備状態](08_candidate_status.log)

14:01 JST、操作者申告1～2 mV前後で実測経路を試行。`CAL_MEASURE BATT_CHG A` は取得IDを返し、`CAL_MEASUREMENT?` の7355原文は `+0012.156E-03` V（12.156 mV）。1 mΩ換算候補は12.156 A。想定より大きく、診断候補の範囲検査が `ERR:CAL_WRITE_VALUE` を返した。ADを送信せず `TEST_END` で試行を閉じ、CSVを回収してSHA-256一致・AD／AR実送信0件を確認した。実測値の明示ADと書込み後の実機 `AD_VERIFY` はシャント調整後に実施する。 [実測試行ログ](cache_point_20261125_140107_616228.json)／[SDのCSV](20261125_140107_T000562.csv)

14:02 JST、操作者の再読取り指示に従い、7355の取得・Cache照会を再実行。新しい取得ID `00000002-00000002-BATT_CHG-A` の7355原文は `+0009.178E-03` V（9.178 mV）、換算候補は9.178 A。取得と試行終了が成功し、CSVのSHA-256一致・AD／AR実送信0件を確認した。 [再読取りログ](cache_point_20261125_140226_127865.json)／[SDのCSV](20261125_140226_T000563.csv)
