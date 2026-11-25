# 7355実測値によるAD書込み・AR照合

対象はサンプル `S1.14B`／UNIT `000001` の `BATT_CHG` A点→`P1`。7355と1 mΩシャントの実測値をPicoで `mV→A` に換算する。操作側は7355をDCVに設定し、この点の入力が安定するよう調整してから取得する。現在の最新実測は9.178 mV（9.178 A）で、サンプル診断候補の許容範囲 `0～3.3 A` を超えている。範囲はレビュー版のBATT_CHG上限に基づく診断上の送信条件で、量産校正の合否基準ではない。 [既存実機結果](Result_Rev0.md)

## ATEコマンド順

COM5、57600 bps、8N1。各応答を受けてから次の要求を送る。`{id}` は当該試行の応答から取り出した取得IDに置換する。

| 順 | 送信 | 確認する応答と判断 |
|---|---|---|
| 1 | `*IDN?`、`COMM_STATUS?`、`SD_STATUS?`、`HOST_INFO? METER` | 親Picoの識別、`IDLE`、SD `OK`、測定器HOST `READY` |
| 2 | `TEST_START` | `OK` |
| 3 | `INFO_REFRESH`、`FW_REV?`、`UNIT_SERIAL?` | 同じ試行の製品情報が `OK`、`S1.14B`、`000001` |
| 4 | `CAL_MEASURE BATT_CHG A 4000 :READ?` | `OK:CAL_MEASURE:{id}`。4,000 msは7355機能照会とREADの総期限 |
| 5 | `CAL_MEASUREMENT? {id}` | 取得ID、対象、点、mV、A、7355原文を取得。ATEがこの値で進めるか判断する |
| 6 | `CAL_WRITE {id} P1` | `OK:CAL_WRITE`。Picoが同一試行の照会済みCacheを参照し、小数を保持したままADのfloat32へ格納 |
| 7 | `AD_VERIFY BATT_CHG P1` | 明示ARでREF8とADCを照合。`OK:AD_VERIFY`、`ERR:AD_VERIFY_MISMATCH`、`ERR:AD_VERIFY_TIMEOUT` を記録 |
| 8 | `TEST_END`、`PICO_SELF_CHECK?`、`SD_STATUS?`、`LOG_DROP_COUNT?` | 試行終了、SD保存・ログ欠落を確認。ATE原文とSDの `CAL WRITE`／`CAL VERIFY` を照合 |

取得やCache照会だけでADを送信することはない。書込みが成立、または成否不明になった取得IDは失効する。書込み成否不明時は、その試行で同値を再送しない。`ERR:CAL_WRITE_VALUE` はAD送信前の停止であり、測定条件が変われば新しいIDで取得し直す。AD／ARの1,000 msは診断の観測期限。

このS1.14BサンプルでARは整数のREF8を返す。例えば1.85 Aのfloat32を書き、ARが1を返した場合は不一致を記録する。`OK:CAL_WRITE` はAD応答の成立を示し、AR照合の結果は別に記録する。どの応答も製品の最終判定を兼ねない。

## 実装と実機確認の範囲

通常のATE parserと親Picoの `FixtureApp` に実装し、`CALIBRATION_SAMPLE_ENABLED` で明示的に有効化する。既定値は `False`。有効化しても、同一試行でD5の製品情報が一致するまで書込み・照合を受け付けない。BATT_CHG A→P1のサンプル以外の対象、量産APIと正式T2はOpen。 [実装](../../../src/calibration_write.py)／[統合回帰](../../../tests/test_calibration_write.py)

2026-11-25 14:13 JST。対象親Picoに統合版5ファイルを配置し、退避した旧版と配置版をSHA-256で照合した。サンプル機に限り診断設定を有効化した。通常ATE入口で取得・Cache照会に成功。7355の実測は `+0009.174E-03` V（9.174 mV／換算9.174 A）で、`CAL_WRITE` は `ERR:CAL_WRITE_VALUE` を返した。実装上、この応答はAD送信前に返る。`TEST_END`、終了診断、SD `OK`、ログ欠落0を確認した。親PicoのUSB保守COM6がPCの一覧から消えたため、今回のSD CSVのPC回収は未確認。ATE COM5の `IDLE` と測定器HOST `READY` は確認済み。 [配置マニフェスト](integrated_20261125_141032_865531/manifest.json)／[実機ATE記録](cache_point_20261125_141307_506871.json)／[終了後の状態](12_integrated_final_ate_status.log)

Host Unit／Mock NF55Gは540件成功。うち4件は通常ATE入口で明示書込み、値とADCの照合、範囲外拒否、成否不明時の再送防止を確認した。実測値でADとARの両方を成立させるには、当該校正点の入力を診断許容範囲内に準備する必要がある。
