# ADC校正 3回路の実機デバッグ準備

2026-11-25。コマンドは印刷用Rev.1と同じ。対象はサンプル `S1.14B`／UNIT `000001`。測定回路 `DISCHG_I`／`BATT_CHG`／`BATT_V`、測定点 `A`／`B`、製品の書込先 `P1`／`P2` は個別に指定する。 [コマンド仕様](Cache_Write_HIL_Rev1.md)

## 親Picoに最新版を入れる

リポジトリのルートを開いたPowerShellで実行する。親Picoの保守ポートがCOM6以外の場合は `--port` を変更する。準備コマンドは対象Picoを識別し、既存ソースをPCに退避してから六つの候補ファイルとハッシュの記録を作る。現行の基板設定を引き継ぐ。適用コマンドは退避時のハッシュを再照合し、旧ファイルを親Pico内にも保存してから新版を配置する。

```powershell
$bench = '.\docs\ADC_Decimal_Hardware_Test_20261125\run_02'
$python = '.\.venv\Scripts\python.exe'
$stage = & $python "$bench\deploy_integrated_sample.py" --port COM6
if ($LASTEXITCODE -ne 0) { throw '親Picoの退避・準備に失敗しました' }
& $python "$bench\deploy_integrated_sample.py" --port COM6 --apply $stage
if ($LASTEXITCODE -ne 0) { throw '親Picoへの配置に失敗しました' }
```

親Picoが再起動してCOM5が応答する状態で、測定器HOSTを再結合する。`HOST_INFO? METER` による `READY` と起動識別子の更新を確認する。HOST管理コマンドを使う場合は既存の復帰スクリプトが結果をJSONに保存する。 [HOST復帰スクリプト](../../USB_Host_Reset_Study_20261121/Debug_20261125_01/rebind_meter_after_parent_update.py)

```powershell
& $python '.\docs\USB_Host_Reset_Study_20261121\Debug_20261125_01\rebind_meter_after_parent_update.py' "$stage\host_rebind.json" --host-version 20261125.2
```

## デバッグ記録を取る

ATEの印刷用コマンド列を使用できる。PCで一連の応答を保存する場合は、同じCOM5を使うATEプログラムを閉じてから次のランナーを使う。3つの指定値と7355の実際の表示値を入れる。例では `--measure-only` により測定とCache照会を行う。書込み・読戻しまで実施する試行ではこの引数を外す。

```powershell
& $python "$bench\run_cache_point.py" --target BATT_V --measurement-point A --product-point P1 --operator-reading '<7355の実表示値と単位>' --measure-only
```

フィードバックには回路・測定点・書込先、7355の表示値と単位、ATEの応答を添える。PCランナーでは `cache_point_日時.json` に全応答と通信時間が残る。実機用ファームウェアの配置と校正試験は作業者が実施する。

## 開発側の確認結果

ATE UARTの入力から測定器HOSTのCリレー、模擬NF55Gまでを接続し、3回路×2点の全6点で測定、Cache照会、単発AD、明示AR、使用済みCacheの失効を確認した。A/BとP1/P2を逆順にも指定し、ADの実送信フレームとARの返却内容を照合。Host Unit／Mock NF55Gの全544件が成功した。配布スクリプトには `calibration_measurement.py` を追加し、旧版の5ファイル構成のマニフェストを拒否するよう修正した。今回の実機配置・試験は未実施。 [統合回帰](../../../tests/test_external_instrument_link.py)／[配布スクリプト](deploy_integrated_sample.py)
