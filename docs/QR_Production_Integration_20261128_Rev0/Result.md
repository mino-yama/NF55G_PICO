# QR遅着対策・ATE経路実機試験結果 Rev.0

2026-11-28。実スキャナー、通常ATE UART入口（PC COM7、57600／8N1、CR）、実SDで通常20＋旧QR排除10の計30セットを確認した。製品UARTは試験用FixtureAppへ割り当てず、SS送信0件。SS候補一致と製品への実書込みは区別する。

## 確認した事実

| 項目 | 結果・証跡 |
|---|---|
| 通常読取 | [normal_03](normal_03/result.json)の20／20セット成功。同一HOST受付IDの応答後に実QR Bを読取。 |
| 旧QR排除 | [late_01](late_01/result.json)の10／10セット成功。HID受信数増加・完成数不変を観測して受付要求。同一IDの破棄フラグ1の後、Bだけを取得。条件不成立による再試行通知なし。 |
| 原文／SS候補 | 全30セットでBの35文字とSS候補50バイトが期待値に一致。REVは`A03 `（末尾ASCII空白）、LOTは`2601`、号機は`000002`。 |
| ID失効 | 全30セットでTEST_END後の旧ID照会が`ERR:QR_STALE_ID`。 |
| ログ | 全30セットでLOG_DROP_COUNT=0。実SD CSV30件のSD／PC SHA-256一致、14列、開始・終了イベント各1件、QR RECEIVEDがBのみ各1件、NF55送信行なしを照合。 |
| ATE応答 | PC直結で最大通常297 ms、旧QR排除266 ms。量産ATEの受入閾値を意味しない。 |
| 製品未接続時 | 各セットのQR_WRITEは`ERR:NF55G_NOT_CONNECTED`。自己診断のNF55_UART=UNAVAILABLEも記録。 |
| 回帰 | 配置前のHost Unit／Mock NF55G全596件成功。[実行ログ](host_mock_tests.log)。 |

詳細は各試行の`ate_wire.jsonl`、`parent_wire.log`、`sets.json`と、[通常CSV照合](normal_03/csv_verification.json)／[旧QR排除CSV照合](late_01/csv_verification.json)に保存。既存FixtureApp、QR受付処理、Logger、FileSDSinkを使用し、専用SD領域へ記録した。QR UARTの監視と音合図はRAM試験ハーネスで追加しており、保存済み常駐アプリだけでの総合負荷試験とは区別する。

## 配置・継続状態

- 親Pico ID `69f7d45962cfdfad`。実機configのQR_HOST_ARM_ENABLEDだけをTrueへ変更し、他の設定とRTCログ改修を保持。対象37件の[読戻しハッシュ](parent_after_hashes.json)を確認。ソース既定値Falseは未変更。
- QR HOST ID `A06FEA01012EC137`。元FW全2 MiBを`host_flash/`へ退避・独立照合し、`qr-arm-diag-20261126.1`候補を書込み・独立照合。候補UF2 SHA-256は`6c3ffd0bd2fc5788c616ff4096df41dc2fb6c6ec7cfcb9a684ddb63d21d5c07c`。親とHOSTは双方向受付の組合せで配置中。
- 固定配線・外部給電復帰後に定期通知が得られず、ユーザーによるQR HOST RST後に通知・スキャナー認識・drop0を確認。RST前後の証跡を保持し、電源投入直後の正常起動を確認済みとは扱わない。
- 完了試験・CSV回収後に元の常駐処理を再開。試験・配置スクリプトは`scripts/*qr*20261128.py`に保存。

## 中断した準備試行

`normal_01`はスキャン報告がないまま待ち時間終了。HOSTのHID受信数0であり、FW不具合と断定しない。`normal_02`は15セットの成功記録があるが20セットの完了記録がない。今回の30セットへ加算せず、記録を保持した。

## 未確認・残課題

30セット後、ユーザーのサンプル接続完了を受け、FW S1.14Bで実QR B→通常ATE QR_WRITE→明示INFO_REFRESHのSS／D5照合を完了。REV `A03 `／LOT `2601`／号機 `000002`を確認し、他86バイトは開始値と一致。開始時D5全100バイトへ復元し、独立照会・配置37件SHA・自己診断全項目OK・drop0を確認した。初回監視タイムアウトと復元確認の履歴も保持。[SS／D5追加結果](product_02/Result.md)。前段30セットのSS送信0件は、その読取専用試験についての記載。

初回HID報告が受付後まで遅れるケースは自動識別できると確認していない。RSTなし電源投入、量産ATE装置との応答条件・間隔、NF55G同時負荷・長時間運転、正式版採用と受入回数／閾値も残る。OI-23はOpen維持。
