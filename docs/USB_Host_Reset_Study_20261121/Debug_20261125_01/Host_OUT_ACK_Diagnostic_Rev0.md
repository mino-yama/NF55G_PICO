# 測定器HOSTのUSB OUT応答診断 Rev.0

2026-11-25 12:13 JST。ユーザーがSDを親Picoに戻した後、COM5／COM23で `.25.2` のログ付き単発試験を1セット完了。SD_STATUSは前後ともOK、READ 40.407mV、計器エラー0、HOST A/T/RとATE原文一致。TEST_END OK、直後の自己診断94ms、TEST_LOGGER/TEST_LOG_DROP OK、累積drop 0、親IDLE、HOST nonce `4A7326AC8DE43546` 不変。SDのファイルシステムをPC上で再照合していない。単発試行CSVのPC回収と長時間試験、タイムアウト時の新OUT項目の実測は未実施。[単発試験結果](endurance_20261125_121353_294259/result.json)／[ATE・HOST相関データ](endurance_20261125_121353_294259/ate.jsonl)

2026-11-25 交換カードをPCのE:として読取専用で確認。ボリューム番号 `D0E4-A9F7`、容量62,257,102,848 byte（約58 GiB）、ファイルシステムはexFAT。ルート読み取り成功、`System Volume Information` のみ、治具のBANK_A/Bなし。治具仕様はFAT32、実装は `VfsFat` を使用するため、このカードは現状のままでは治具のSD要件を満たさない。交換カードの `VFS_MOUNT` エラーの有力な説明。元のカードで起きた読み出しエラーと起動遅延は別途未確定。修復・フォーマット・書込みなし。[Logger SD仕様](../../Logger_SD_Spec.md)

2026-11-25 12:04 JST。ユーザー操作で交換SDを装着して通常起動。親PicoはATE IDNとIDLEに応答し、測定器HOSTは `.25.2`／nonce `0478133D04F13240`／READY。`SD_STATUS?` は `MOUNT_ERR` で単発測定は未開始。親Pico REPLで個体照合後、初期化466ms、`VFS_MOUNT` の `OSError(19,)`、未マウントを確認。SDカード初期化処理はVFSマウント呼出しまで進んだ。交換カードのファイルシステム・パーティション構成・読出し可否は未確認。親Picoは診断後USB REPL。7355へのSCPI・測定・ログ書込みはない。[ATE記録](endurance_20261125_120447_956639/ate.jsonl)／[親SD初期化診断](endurance_20261125_120447_956639/parent_sd_startup.log)

2026-11-25 11:06 JST。ユーザー操作で親PicoをSDなしで通常起動した。COM5で治具IDNと `COMM_STATUS?=OK:state=IDLE` を受信。SD状態は `MOUNT_ERR`、測定器HOSTは個体 `BFCF2EDB84B0B37F`／`.25.2`／nonce `A95735E25BD2E3CF`／READYと確認した。SDなしではATE起動・HOST管理経路が応答する。カード有無で結果が分かれたが、カード、SPI経路、VFS、起動時ログ走査のどれが直接原因かは未確定。この試行で7355へのSCPI、測定、ログ書込みは実施していない。次は正常確認済みの別のSDで起動を比較し、SDがOKならログ付き単発測定に進む。[SDなしの原文](parent_no_sd_20261125_110657_219907.json)

2026-11-25 固定配線復帰後、測定器HOSTがPCのBOOTSEL一覧から消えたこととCOM5/6/23を確認。単発試験は親PicoのATE `*IDN?` が0byteで、セット開始前に停止した。USB REPLで親個体69f7d45962cfdfad・適用済み250ms設定・`active_app` 未生成を確認。REPLから初期化し直した試行では `VFS_MOUNT` の `OSError(1)` と既に使用中の外部中継PIOを観測した。これは起動を中断した後の観測で、通常起動停止の直接原因は未確定。親の個体指定リセットを実施し、待機して再確認してもATE IDNは無応答。7355へのSCPI・測定・ログ書込みは実施していない。HOST `.25.2` の通常通信およびOUT/IN観測は保留。[親起動状態](host_out_diag_preflight/parent_startup_state.log)／[初期化再試行の状態](host_out_diag_preflight/parent_startup_failure_state.log)／[再起動後の試験結果](endurance_20261125_110348_809082/result.json)

2026-11-25。治具経由では第303セットにREADが無応答。PC直結では再列挙後に400回すべて成功した。治具で次に無応答となった際、USB OUT側の観測とUSB IN側の観測を同じX1要求に残すため、測定器HOST診断候補 `.25.2` を追加した。[比較と既存の実機結果](ATE_Post_End_Stability_Rev0.md)

既存のPIO USBハンドシェイク関数が返したPIDを、対象7355のbulk OUT転送中にだけ数える。USB OUTを増やす処理やタイムアウト後の再送は追加していない。観測結果は要求のタイムアウトEフレームにのみ付与する。

| 項目 | 意味 |
| --- | --- |
| `OA` | bulk OUTで観測したACKの回数 |
| `ON` | bulk OUTで観測したNAKの回数 |
| `OX` | bulk OUTで観測したそれ以外の応答または応答なしの回数 |
| `OP` | 最後に観測したbulk OUTのPID（16進） |
| `OE` | bulk OUTエンドポイント（16進、未特定は00） |

既存の `I/N/D/EP` はIN側を示す。OUT ACKはUSBエンドポイントの受理を示し、SCPIの実行完了を示さない。PIOが観測した値を採取する方法であり、外部USBアナライザの独立観測は未実施。

Host Unit／Mock NF55Gは535件成功。タイムアウト診断の追加後も、X1の相関キーと曖昧フラグを維持し、通常応答と診断を付けられない長さの既存フレームを保持することを回帰で確認した。[回帰ログ](out_ack_535_regression.log)

通常のCMake／Ninja起動が途中で停止したため、短い別フォルダでCMake生成のcompile／linkコマンドを使用した。既存SDK構成の生成済みPIOヘッダとboot-stageを再利用し、中継ターゲットの84オブジェクトをARM GCC 14.3.0で再コンパイル。リンク・UF2変換・picotoolの版照合を完了。UF2は101,376 byte、SHA-256 `088e6e2a11b2ea333e9de66af34dfe2558ab5d2c7a9ffbc6368110329d7035e4`。[ビルドマニフェスト](candidate_20261125_105200_326526/manifest.json)

測定器HOST `BFCF2EDB84B0B37F` の旧 `.25.1` 全Flash 2 MiBを退避し、実機verifyを通過してから `.25.2` を書き込んだ。書込み後の独立verifyと版の読戻しに成功。終了時点はBOOTSEL。固定配線復帰後にCOM5／COM23で1セット検証する。長時間試験および次回のタイムアウト時OUT/INの実測は未実施。[退避マニフェスト](host_out_diag_preflight/manifest.json)／[版読戻し](candidate_20261125_105200_326526/flash_after.log)
