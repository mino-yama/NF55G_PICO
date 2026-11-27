# 親Picoへの校正機能配置 完了記録

Date: 2026-11-27
Revision: Rev.1
結果：配置・全件読戻し・通常再起動・アプリ起動確認を完了し、常駐処理を再開。

## 対象と配置内容

- 親Raspberry Pi Pico 2／COM6／USB VID:PID=2E8A:0005。
- `machine.unique_id()`：`69f7d45962cfdfad`、MicroPython v1.27.0。
- `/src/` 34ファイル、`/calibration_limits.py`、`/main.py`の計36ファイル。
- 校正点A/B統一、点の二重指定廃止、必須3回路×A/Bの共通書込み保護を反映。
- 設定版：`SETTINGS_REV="20261127-Rev0"`。数値設定は今回変更していない。

## バックアップと実機設定

配置前に試験・Logger・NF55G通信が停止中であることを確認した。現行`/src/`とルートPythonファイル計36件を[backup](backup/)へ保存し、実機SHA-256との全件一致を確認した。実機内の既存バックアップ・SD・ログは削除していない。

実機configをバイト単位でそのまま候補へ引き継いだ。正本`src/config.py`の既定値へ戻していない。

| 設定 | 保持値 |
|---|---|
| EXTERNAL_INSTRUMENT_ENABLED | True |
| QR_HOST_ENABLED | True |
| QR_HOST_ARM_ENABLED | False |
| CALIBRATION_SAMPLE_ENABLED | True |
| ATE_RESPONSE_TERMINATOR | CR |
| REPL_LOG_ENABLED | True |
| T2_AR_MS | 100 |

## 検証結果

1. 実機設定を保持した[payload](payload/)を優先importし、Host Unit／Mock NF55G全575件成功（28.139秒）。[試験ログ](host_mock_tests.log)。
2. Pico内の一時領域へ候補36件を転送し、全SHA-256とMicroPythonの`compile()`を確認。
3. 切替え前にPico上で保護処理を実行。6点×上下限の12境界を許可し、DISCHG_I Aの0と境界直外の10進値2件を拒否。製品指令は発行していない。
4. 旧ファイルを実機内の`/Calibration_AB_Pico_Deployment_20261127_Rev1_before`へ保持し、`/main.py`を最後に切替え。
5. 配置後36件を実機から[readback](readback/)へ読み戻し、候補SHA-256との全件一致を確認。
6. `machine.reset()`後、同じ個体IDで再接続。アプリ生成、校正機能生成、設定モジュールの実読込み、新A/B書式の解釈、旧数値点形式の拒否、上下限12境界・0拒否を確認。
7. 再起動後も配置36件のSHA-256が一致。SD状態OK、外部測定器初期化エラーなし、試験・通信停止状態を確認した。
8. 初期化を繰り返さず、同じ`active_app.run()`を再開。再開直後にTracebackがないことを確認し、COM6を閉じて解放。

根拠：[manifest.json](manifest.json)、[操作ログ](operations.jsonl)、[再起動後ハッシュ](post_boot_hashes.json)、[完了状態](result.json)。配置手順は[scripts/deploy_calibration_ab_20261127.py](../../scripts/deploy_calibration_ab_20261127.py)。

## 修正履歴と確認範囲

[Rev.0](../Calibration_AB_Pico_Deployment_20261127_Rev0/Result.md)は切替え前の実機検証でMicroPythonに`str.ljust()`がないことを検出して停止した。比較処理を末尾0の連結へ修正し、Rev.1を別フォルダとして保存・再検証した。未切替えのRev.0候補とログも保持する。

実機設定を用いたHost試験では、SD診断の単体テストがQR有効設定へ依存することを検出したため、`tests/test_sd_startup_diagnostic.py`で対象外ハードウェアを明示的に無効化するMockを補った。製品コードの設定や機能を無効化する変更ではない。

ATEコマンド送信、NF55GへのAD／AR／CAL_WRITE、製品校正値変更、実電流・実電圧での校正検証は実施していない。純粋なparser呼出しと保護処理検証を、ATE実通信・製品書込みと区別する。

実ATEの新書式への移行、実測値による書込み・AR読戻し、AR小数保持、係数反映、電源再投入後保持、量産向けの個体制限解除は未確認。CAL-GUARD、OI-04等のOpen IssueをCloseしない。Picoの配置成功を製品校正PASSとは扱わない。
