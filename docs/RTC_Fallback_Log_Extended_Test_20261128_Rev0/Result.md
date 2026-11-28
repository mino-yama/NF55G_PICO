# RTC異常時ログ 追加実機テスト結果

Date: 2026-11-28  
Revision: Rev.0  
結果：実SD異常系6件、PCシリアル経由30試行＋CONT、保存後の実電源OFF／ON確認に成功。今回の条件内で実装不具合は検出していない。

## 1. 対象・確認条件

- 親Pico COM6／unique_id=`69f7d45962cfdfad`、RTCログ改修配置済み版。
- 各実機接続時にアプリ対象37件のハッシュが[前回配置結果](../RTC_Fallback_Log_Deployment_20261128_Rev0/Result.md)と一致。製品コード・設定の追加変更や再配置は行っていない。
- 通常BANKに保存せず、実SDの`/sd/rtc_extended_20261128_rev0/`内で実施した。
- RTCなし・RTC読取り異常、SD確認I/O異常は試験用オブジェクトで模擬した。物理的なRTC取外し・SD故障を再現したものではない。
- PCシリアル試験はCOM7／57600bps／8N1／CR。配置済みFixtureApp／ATEServerを使用するRAM上の試験アプリへ既存ATE UARTを渡した。NF55G UART・ProtocolはNoneとし、製品へ指令を送れない構成にした。
- 終了後は元の常駐アプリを再開し、保守・ATE用ポートを閉じた。

## 2. 実SD上の異常系・保全確認

| ケース | 結果 |
|---|---|
| 同名8候補の衝突 | FILE_EXISTSで有界に停止。既存8ファイルのハッシュ一致、新規CSV作成なし |
| 他方BANKのS/N付き名と衝突 | FILE_EXISTS。変更元・変更先ともハッシュ一致、元名を保持 |
| 存在確認statのI/Oエラー注入 | OPEN_ERR。確認不能を「空き」と判断せず、CSV作成なし |
| BANK_B一覧取得エラー注入 | namespace_ready=False、保存開始を拒否。既存データのハッシュ一致 |
| renameのI/Oエラー注入 | WRITE_ERR。close済み変更元の名前・内容を保持 |
| 循環開始条件の注入 | 試験用BANKの使用量をRAM上で閾値超過とし、実SD上でBANK_Bへ循環。自作の正規名fixtureだけを削除し、対象外ファイルと同名ディレクトリを保全 |

媒体を実際に満杯にした試験ではない。削除対象は今回作成した専用試験領域のfixtureだけで、通常の既存ログを循環削除していない。

証跡：[異常系結果](fault_results.json)、[操作ログ](operations.jsonl)。

## 3. 通常UARTサーバー経路の繰返し

RTCなしの試験アプリへ、PCから通常のUARTサーバー・parser・dispatcherを通して以下を送信した。製造用ATEアプリやGPIB／PIA5100を介した試験ではない。

各試行：TEST_START → *IDN? → SD_STATUS? → PICO_SELF_CHECK? → TEST_END → PICO_SELF_CHECK? → LOG_DROP_COUNT?。

| 確認項目 | 結果 |
|---|---|
| TEST | 30/30試行成功。T000001～T000030で別ファイルを保存 |
| CONT | 1セッション成功。C000031へ保存 |
| 応答 | 冒頭IDN・CONT指令を含む215要求すべて期待応答を受信 |
| RTC診断と保存診断 | RTC=UNAVAILABLE、NF55_UART=UNAVAILABLEを正しく報告しつつLOGGER=OK。TEST終了後はTEST_LOGGER=OK／TEST_LOG_DROP=OK |
| ログ欠落 | 全試行で0 |
| PC回収 | 31ファイルのSD／PCハッシュ一致。全CSVが14列、397データ行のtimestampは空欄 |
| 試行分離 | 各TESTにTRIAL_START／TRIAL_END_REQUESTを1件ずつ、END_REQUESTも確認 |
| 応答時間 | 全体・TEST_START最大147.637ms、TEST_END最大123.381ms |

前応答完了後に110ms以上待って次要求を送る条件で実施した。専用領域のファイル数とRTC／NF55Gなしの条件で得た値であり、通常BANKの大量ログ・実製品通信・量産ATEでの最大応答時間は保証しない。自己診断全項目がOKだったという意味ではない。

証跡：[UART応答原文](ate_wire.jsonl)、[回収結果](ate_result.json)、[応答時間](ate_timing.json)、[CSV照合](ate_csv_verification.json)、[31件のCSV](ate_csv/)。

## 4. 保存後の実電源OFF／ON

1. 専用領域powerに`000001_NO_RTC_T000001.csv`を保存。flush・close・os.syncを実施し、内容と最大番号1を記録した。
2. 元のアプリを試験・通信停止状態で再開し、ポートを解放。ユーザーへUSBを含むPico全給電のOFF／ONを依頼した。
3. ユーザーから「再投入完了」の回答を受け、同一個体へ再接続した。
4. 電源断前に置いたRAM sentinelが消えていること、配置ハッシュ一致、SD状態OKを確認した。電源操作の物理実施はユーザーの申告に基づき、ソフトウェア側ではRAM再起動と保持データを検証した。
5. 実SDから最大番号1を再読取りし、`000002_NO_RTC_T000002.csv`を保存。電源断前ログのSHA-256が新規保存の前後とも一致し、drop=0だった。

実RTCは接続したままで、仮IDLoggerだけRTC=Noneとしている。したがって「実RTCなしでの電源投入」を確認したものではない。一方、仮ID・S/N付き名の採番が電源断で初期値へ戻らず、保存済みログから引き継がれることは実SDで確認した。

## 5. RTCの保持観測

| 項目 | 電源断準備時 | 再投入後 |
|---|---|---|
| RTC日時 | 2026-11-28 15:20:42 | 2026-11-28 15:21:51 |
| status | 0x09 | 0x09 |
| OSF | 0 | 0 |

RTC_SET・レジスタ変更は行っていない。RTCの観測間隔69秒に対しPCの観測間隔は69.280秒で、初期日時へ戻らず進行した。ただしこれは電源断前後の観測間隔であり、実際の無給電時間ではない。無給電時間、VBAT電圧、長時間保持は測定していない。

電源断前後のCSV2件もSD／PCハッシュと14列・時刻空欄を照合した。

証跡：[電源断前](power_ready.json)、[再投入後](power_result.json)、[前CSV](power_before/)、[後CSV](power_after/)、[集計結果](result.json)。

## 6. 残確認

- 書込み中・flush中・名前変更途中の電源断、FAT破損時の回復。
- RTCを物理的に未接続とする起動、実I2C障害、長時間・反復電源断、電池／VBATの確認。
- 通常BANKの実容量循環、通常ログ数での開始時間、NF55G・QR・7355・SDの複合負荷、製造ATE／GPIBの応答待ち条件。
- 削除済みログ・別SDを含む永久欠番の要否と正式運用受入。

RTC-LOG-01～04は今回の限定結果を追記してOpenを維持する。実装不具合がないことや、量産条件全般の合格をこの試験だけで断定しない。

実行：[追加テスト用スクリプト](../../scripts/test_rtc_fallback_extended_20261128.py)。製品コードは変更していないためHost全体596件の再実行はせず、配置版ハッシュと追加実機結果を証拠として記録した。
