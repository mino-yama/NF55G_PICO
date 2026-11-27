# 2026-11-27 親Pico配置記録：AD直接指定 / AR T2=100 ms

## 配置対象

- 対象: 親Raspberry Pi Pico 2 / RP2350
- USB CDC: COM6、VID/PID 2E8A:0005
- `machine.unique_id()`: `69f7d45962cfdfad`
- MicroPython: 1.27.0
- 配置元: `docs/AD_Direct_Pico_Preparation_20261126_Rev1/`
- 配置内容: `/src/` の33ファイルと `/main.py` の計34ファイル

配置中はユーザー確認によりATE送信を停止し、PicoをNF55G本体から切り離した。元候補のpayloadはサイズ・SHA-256とも34ファイル全件一致。Host/Mock Unit Testは569件成功。

## 実機設定の保持

配置前の実機configには以下の設定があり、元候補の既定値で無効化しないよう配置専用configを作成した。

- `EXTERNAL_INSTRUMENT_ENABLED = True`
- `QR_HOST_ENABLED = True`
- `CALIBRATION_SAMPLE_ENABLED = True`
- `ATE_RESPONSE_TERMINATOR = "CR"`
- `REPL_LOG_ENABLED = True`

AR用 `T2_AR_MS = 100` を反映し、上記の実機固有設定を維持した。元のRev.1候補と正本 `src/config.py` は変更していない。実機用payloadとmanifestは `tmp/pico_deploy_ad_direct_20261127/` に保存。

## 配置と確認

- 配置前バックアップ: `tmp/pico_deploy_ad_direct_20261127/backup/`
  - Picoの `/src/` 33ファイルと `/main.py` を退避。
  - Pico再インベントリの各SHA-256と退避データが一致。
  - Pico内の既存バックアップ領域、`/sd` とその他ファイルは削除・変更していない。
- `/src/` を転送後、実機から読み戻した33ファイルのSHA-256が全件一致。
- `/main.py` を最後に配置。最終読戻しで全34ファイルのSHA-256と個体IDが一致。
- Pico上のMicroPythonで `/main.py` と `/src/` の全33 Pythonファイルを `compile()` し、34ファイルすべて成功。
- `machine.reset()` による通常起動リセットを実行。USB CDCは同じ個体IDでCOM6に再列挙。

## 実施していない操作・残確認

- ATEコマンド、NF55G通信、`AD`、`CAL_WRITE`、`INFO_REFRESH`、`TEST_START` は実行していない。
- 校正値の書込み、AD/AR読戻し、校正成立・製品PASS判定は未実施。
- ハードリセット後のアプリ機能確認は行っていない。今回の完了範囲はファイル配置、実機ハッシュ、構文検査、リセット、USB CDC再列挙まで。
- 2026-11-27のA/B表記統一・書込み上下限ガードはコードへ未反映。`Calibration_AB_Revision_Plan_20261127_Rev2.md` に実装許可待ちと記録されているため、今回の配置には含めていない。
- AD/ARの正式な製品仕様・実機タイミング等のOpen Issueは継続。
