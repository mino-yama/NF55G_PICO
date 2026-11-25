# USB HOST安定化・受信境界改善 Rev.0

日付: 2026-11-25 JST。継続案件 `USB_Host_Reset_Study_20261121`。

## 現在の開発状況

- 既存記録: 11月24日のIDN 200/200、11月23日のREAD/D1/SD/RTC共存50回は成功。以前の反復試験では117回目および73回目にtimeout。長時間安定性の原因解明・受入完了とは扱わない。
- 400セット/24時間の無リセット耐久は未実施。[承認済み受入基準](../CDC_Endurance_Acceptance_20261124_Rev0.md)を維持する。
- ユーザーが固定配線・給電済み、ATE=COM5と確認。本日の読取専用事前照会5件は成功。治具 `NF55G_PICO_FIXTURE,Rev.0`、COMM IDLE、Host `BFCF2EDB84B0B37F`／`meter-host-relay-20261123.2`／nonce `6AB6B72A586709E7`／READY、SD OK、drop 0。[時刻・原文・所要時間](ate_precheck.json)。
- この照会はUSB CDCでの7355応答を新たに確認したものではない。今日は7355へのSCPI、NF55Gコマンド、RESET、Flash書込みを実施していない。

## 確認できた実装上の問題と修正

旧 `service_usb_rx` はFIFOに既着データがあっても64byteだけ読み、その後 `service_uart` で次要求を受け付ける。FIFO容量は256byteで、USB endpointの64byteとは異なる。

例: FIFOに `62文字 + CRLF + X` が既着の場合、旧処理は先頭64byteでRを発行し、余分なXを残す。次要求が同時期に来ると、余分なデータの検出より先にQ受付／USB送信へ進み得る。これはソース上で確認した境界の欠陥であり、過去のRX0 timeoutの原因と確定したものではない。

候補 `meter-host-relay-20261125.1` は新規 `relay_cdc_rx.c/.h` に受信serviceを分離し、FIFO容量分を1回で読み、既着全体を実engineへ渡す。終端後のデータが同じFIFOにあれば、正常Rの前にEXTRA_DATA／RESPONSE_TOO_LONGとして停止する。最大処理量は256byteで有限。空FIFOのread／再投入、SCPI再送、期限延長、fault解除は追加しない。

制約: FIFO検査後に新たに到着するデータや、測定器内部に残る旧応答の排除まで保証しない。応答の既存192byte上限、CRLF、期限、成否不明、完全な計器エラー値をATEへ返す規則は維持する。

## 試験結果と未完了項目

| 検証 | 結果 |
|---|---|
| 変更前Host Unit / Mock NF55G | 528件成功、13.939秒。[ログ](baseline_host_mock.log) |
| 新規実C受信service＋engine回帰 | 6件成功、0.747秒。ツール実行結果で確認 |
| 回帰の内訳 | 応答2～192byteと分割境界、64/128byte終端後の余分なデータ、256byte過長、未要求データ、空FIFO、期限境界 |
| 旧64byte処理での新規回帰再現 | スクリプト準備済み、プロセス起動障害により未実行 |
| 変更後Host Unit / Mock全体 | 未実行。528＋6を全534件成功とは記載しない |
| SDK 2.2.0 ARMビルド | CMake configure/generate成功。コンパイル・リンク・UF2更新の完了未確認。[ログ](arm_build.log) |
| 候補FWの実機書込み／CDC測定／400セット耐久 | 未実施 |

新規回帰は `python -m unittest discover -s tests -p test_external_meter_rx_service.py -v` で実行。USB APIは決定的なFIFO stub、応答判定は実際の `relay_host.c`／`relay_wire.c` を使用する。既存の実TinyUSB FIFO回帰528件中の容量・wrap検証とは区別する。

途中からWindowsのプロセス生成が `CreateProcessAsUserW failed: 5 / アクセスが拒否されました` で失敗。別起動手段でも `spawn EPERM`、昇格起動でも同じOSエラーとなった。自動承認レビューによる拒否通知は受けていない。以降の試験とビルドを成功扱いにせず、新FWは配置していない。

既存buildディレクトリのrelay UF2は更新されていない旧成果物（SHA-256 `7a817134cffdf124197c68d958cfe9b5a96a98dbe308c8d5dd5a63e121e98ef2`）であり、今回の候補として使用しない。[候補ソースhash](candidate_source_hashes.json)。

## 外部ソースとの照合

[TinyUSB公式cdc_host.c](https://github.com/hathach/tinyusb/blob/master/src/class/cdc/cdc_host.c)で、`tuh_cdc_read` がstream FIFOの読出しであることと、endpoint／FIFO容量の分離を照合した。採用判断はローカル固定SDK 2.2.0の `class/cdc/cdc_host.c`、`tusb.c`、`tusb_config.h` を根拠とする。最新版のSDK／TinyUSB／PIO-USBへの更新や原典の変更は行っていない。

## 次の作業・残Issue

1. PCプロセス起動復帰後、`reproduce_legacy_rx.py`で旧処理の期待失敗を確認し、全Host/Mock回帰を実行する。
2. ARMをビルドし、版・UF2・ELF・hashを別候補として保存する。現build内の古いUF2を配置しない。
3. 既存の個体指定・退避・verify手順で新候補を配置し、明示IDN／READ／TEST_START～ENDを確認する。SCPIレンジはATE責任、成否不明時は再送しない。
4. 上記成功後、承認済み400セット耐久を実施。既存USB timeout原因、電源投入条件、旧応答境界、QR側の残課題と区別する。

USB-CDC-RX-BOUNDARY-01をOpenで追加。関連する既存IssueもCloseしない。
