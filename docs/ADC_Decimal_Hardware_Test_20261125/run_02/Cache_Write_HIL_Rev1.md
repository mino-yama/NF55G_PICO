# 回路名で指定する7355測定・書込み・照合

2026-11-25。ユーザー確認の対象は `DISCHG_I`、`BATT_CHG`、`BATT_V` の3回路。ATEは取得IDを返送せず、コマンド名の回路と引数の補正点を指定する。取得IDは結果とログに残る。試行内で同じ回路・点を再取得すると旧値は失効し、新しい値を照会してから明示書込みに使用する。 `TEST_START` 後に `INFO_REFRESH` で対象サンプル `S1.14B`／`000001` を確認する。 [前版の配置・実測記録](Cache_Write_HIL_Rev0.md)

| 回路 | 測定 | Cache照会 | 書込み | 読戻し |
|---|---|---|---|---|
| 放電電流 | `CAL_MEASURE_DISCHG_I A 4000 :READ?` | `CAL_MEASUREMENT_DISCHG_I? A` | `CAL_WRITE_DISCHG_I A P1` | `AD_VERIFY_DISCHG_I P1` |
| 充電電流 | `CAL_MEASURE_BATT_CHG A 4000 :READ?` | `CAL_MEASUREMENT_BATT_CHG? A` | `CAL_WRITE_BATT_CHG A P1` | `AD_VERIFY_BATT_CHG P1` |
| バッテリ電圧 | `CAL_MEASURE_BATT_V A 4000 :READ?` | `CAL_MEASUREMENT_BATT_V? A` | `CAL_WRITE_BATT_V A P1` | `AD_VERIFY_BATT_V P1` |

表のAとP1は入力例。ATEが測定点 `A`／`B` と製品書込先 `P1`／`P2` を指定する。Picoは両者の対応を固定しない。ADのTYPEはレビュー版の対応 `DISCHG_I=1`、`BATT_CHG=4`、`BATT_V=2` を使用する。S1.14Bで書込み・読戻しの実績があるのは `BATT_CHG P1` の人工値診断。新コマンドと他回路・点の実機確認は未実施。

`CAL_WRITE_BATT_CHG A P1` は、同一試行で照会済みの測定値をfloat32でADへ渡す。Picoによる3.3 A上限での拒否を削除した。ATEが測定値の採否を決める。成功応答は `OK:CAL_WRITE:<VALUE8>:<ADのADC十進値>:<AD応答の計算値欄をHEX化した原文>`。製品の計算値欄の表現にかかわらず、フレームと対象・ADCが確かなら原文を返し、ATEからの読戻し要求を受け付ける。

`AD_VERIFY_BATT_CHG P1` は明示ARを送信し、`OK:AD_VERIFY:BATT_CHG:P1:<VALUE8>:<REF8>:<ADのADC十進値>:<ARのADC十進値>` を返す。ここでの `OK` はARの受信成立を表す。照合と合否はATEで判断する。通信異常時は成否を記録し、ADコマンドは再送しない。前版の取得IDを引数に取るコマンドも、互換用として使用できる。

Host Unit／Mock NF55Gは543件成功。3回路のTYPE・明示P1/P2、試行内再取得による旧値の失効、9.174 AをPicoで制限せずにADへ渡す動作、読戻し原文のATE返却を模擬で確認した。PCでCOM5とCOM23を認識したが、親Picoの保守COM6は一覧にない。新コマンド版の実機配置と実測書込み・照合は未実施。
