# 測定器USB HOST候補FW .25.1 検証記録 Rev.0

2026-11-25。前回の[受信境界改善結果](Result_Rev0.md)の続報。

候補版は `meter-host-relay-20261125.1`。測定器HOSTの受信処理は、親UARTから次の要求を受け付ける前に、CDC FIFO容量の256 byteまでを一括で応答検査へ渡す。同じFIFOに終端後のデータがある場合、正常応答を返す前に異常として停止する。[受信処理](../../../firmware/usb_submcu_external_meter_host/relay_cdc_rx.c)／[変更ファイルのSHA-256](candidate_source_hashes.json)

| 検証 | 結果 |
| --- | --- |
| 旧64 byte受信処理での再現 | 6件中、期待した5失敗を確認。内訳には同一テスト内の64／128 byte境界を含む。再現スクリプトの終了コードは0。[ログ](legacy_rx_regression_run01.log) |
| 変更後のHost Unit／Mock NF55G | 534件すべて成功。11.487秒。新規実C回帰6件を含む。[ログ](candidate_host_mock_run01.log) |
| `git diff --check` | 成功。既存の改行変換の警告あり。 |
| SDK 2.2.0 ARMビルド | GNU 14.3.0の検出後、CMakeのCコンパイラABI確認で停止。候補UF2の生成は未確認。[構成ログ](arm_configure_run01.log) |

ARMビルドは `arm_candidate_build` に分離した。追加のPowerShell起動で `CreateProcessAsUserW failed: 5`、NinjaとARM GCCの直接起動で `spawn EPERM` を確認した。PC実行環境が復旧したら候補をビルドし、ELFの版とUF2のSHA-256を確認してから実機検証へ進む。

今回の実機配置、CDC確認、400セット耐久試験は未実施。USB-CDC-RX-BOUNDARY-01はOpenを継続する。過去のRX0 timeout原因は未確定。[耐久受入基準](../CDC_Endurance_Acceptance_20261124_Rev0.md)
