# 校正機能のPico配置 Rev.0：切替え前停止

Date: 2026-11-27

親Pico COM6／unique_id=69f7d45962cfdfad。試験・通信停止を確認し、現行36ファイルをbackupへ保存して実機SHA-256と照合した。実機configを保持したpayloadのHost/Mock全575件は成功（23.299秒）。

36候補をPicoの一時領域へ転送し、転送SHA-256とMicroPython構文検査は成功した。続く上下限保護の実行検証でMicroPythonにstr.ljustがないことを検出し、切替え処理に進まず停止した。ライブの/src/、/main.py、製品校正値は変更していない。

修正後の配置候補は[Rev.1](../Calibration_AB_Pico_Deployment_20261127_Rev1/)。本Rev.0のpayload・バックアップ・一時領域と[操作ログ](operations.jsonl)は履歴として保持する。初回のHost試験実行はdiscover起点の指定不備で起動せず、次の試行はSD診断の単体テストが実機QR有効設定へ依存して1件エラーとなった。テストのハードウェア分離を補って上記575件成功を確認した。製品指令は発行していない。
