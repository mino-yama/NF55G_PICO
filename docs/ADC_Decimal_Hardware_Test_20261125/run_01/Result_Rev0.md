# ADC校正のAD／AR小数試験準備

2026-11-25。USB HOSTの耐久調査は `USB-CDC-RX-BOUNDARY-01` をOpenのまま保留。校正側は、確定済みの取得／Cache照会の次工程として、既存の小数試験計画に沿ってDEC-01のAR証跡処理を準備した。 [Open Issues](../../Open_Issues.md)／[小数試験計画](../../ADC_Decimal_Hardware_Test_Plan_20261122_Rev0.md)

## 接続個体

親Picoの `*IDN?` と `IDLE` を確認してから、既存のD5 `INFO_REFRESH` を1回実行した。NF55Gの `FW_REV?` は `S1.14B`、`UNIT_SERIAL?` は `000001`。既存の小数切捨てレビューはS1.13／S1.15_r1のソースに基づく。今回の接続個体のAR応答、小数の内部保持、元値の復元手段は確認できていない。 [今回の読取ログ](product_info_precheck.log)／[既存ソースレビュー](../../ADC_Calibration_Development_20261119.md)

## 実装・検証

PC用ツール `inspect_ar_frames.py` は保存済みのNF55G AR応答を読み、既存の実装でCMD、BCC、DATA 140文字を検証する。10点のADC値、REF8原文、フレーム全体のHEXをJSONに出力し、2フレーム指定時は観測された差分を表示する。REF8の表示には製品側の小数形式の仮定を加えない。 [解析ツール](inspect_ar_frames.py)／[テスト](test_inspect_ar_frames.py)

```powershell
.\.venv\Scripts\python.exe .\docs\ADC_Decimal_Hardware_Test_20261125\run_01\inspect_ar_frames.py before.hex --after after.hex
```

`before.hex` と `after.hex` は、それぞれSTXからBCCまでの完全なAR応答1フレームをHEXで保存したテキスト。DEC-01で基準値だけを確認する場合は `--after` を省略する。模擬3件で原文保全・差分表示・異常フレーム拒否を確認。Host Unit／Mock NF55Gは536件すべて成功。

実機ではD5による個体確認まで実施した。AD／ARの送信と校正値の変更は未実施。S1.14Bで使うARの診断送信条件を照合し、最初にDEC-01で書込み前の原文を採取する。小数を書き込む段階では、元値を精度を落とさず復元できる手段、または試験専用個体の再校正手順が必要。正式ATE入口、A/BとP1/P2の対応、AR T2、小数表現に関するOpen Issueは継続する。
