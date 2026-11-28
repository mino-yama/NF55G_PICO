# 配線修正後・R3有効入力での校正用取得 Rev.0

2026-11-28。TX/RX配線修正と新HOSTの正式再起動後、通常ATE経由の7355 IDNを確認。入力200 mVはR3でOLとなり取得拒否したため、ユーザーが入力を40 mVへ変更した。診断USB-UART自身のPC接続後、COM23を識別した。

R3、ADC DCV、連続／即時、H0、RN0、PR4をATEで設定・照会し、次を確認した。校正値の製品書込みは行っていない。

| 取得 | 校正候補A（測定mVと同じ数値） |
|---|---|
| DISCHG_I A | +039.2028E+00 |
| DISCHG_I B | +039.2033E+00 |
| BATT_CHG A | +039.2029E+00 |
| BATT_CHG B | +039.2031E+00 |
| DISCHG_I A 再取得 | +039.2029E+00 |

これは入力源による取得・変換経路確認であり、実シャント回路の電流、A/B各点の目標値や校正精度の確認ではない。40 mVは入力源設定値で、表示原文の実測値とは区別する。

全5件で原文V→mVの厳密1000倍、50 A／50 mV換算のA候補、対象・点・取得ID・原文CRLFを照合。Cache再照会一致と再照会中のHOST出力0、再取得後の旧ID拒否、TEST_END後の取得ID失効、SD OK・drop0を確認した。[取得結果](corrected_r3_calibration_02/result.json)／[値とID](corrected_r3_calibration_02/values.json)／[ATE原文](corrected_r3_calibration_02/ate.jsonl)。

診断UARTの保存原文13,315バイトを独立FrameReaderで検証し、163フレーム・CRC等エラー0・末尾残り0を確認した。[独立照合](corrected_r3_calibration_02/verification.json)。

## 耐久開始前の確認

R3・40 mVで耐久と同じ1セットを実施し、MD?=+039.2043E-03、ERR?、TEST_START／END、自己診断・SD・drop・IDLE、HOST session/request/原文相関を確認。実SD CSV1件の14列・開始終了・ATE原文・SHA一致を回収後に照合し、常駐処理を再開した。[単発結果](endurance_20261128_193351_843749/result.json)／[CSV照合](endurance_20261128_193351_843749/csv_export_20261128_193554_181053/csv_manifest.json)。

Host Unit／Mock全596件成功。[実行ログ](corrected_host_mock.log)。新個体ID対応の耐久ランナー模擬6件成功。[模擬ログ](replacement_runner_tests.log)。

この後、別記録`endurance_20261128_193631_024302/`で400セットを開始した。開始前にR?=R3等を照合し、耐久中は測定器設定を送らず、各完了セット間1秒待機する。開始時点の文書であり、400セット完了・CSV400件照合を済んだとは扱わない。
