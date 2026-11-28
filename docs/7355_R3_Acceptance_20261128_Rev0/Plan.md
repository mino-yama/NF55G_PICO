# 7355 R3（200 mV）校正取得・400セット受入計画 Rev.0

現時点の結果：通常構成復帰後もHOST_INFOはtimeout、IDLE／SD OK／drop0。R3校正取得・耐久は未開始。[結果と次の確認](Result.md)。以下は各時点の経過として保持する。

最新再確認：接続確認指示後もHOST情報応答はtimeout、診断受信0バイト。親IDLE・SD OK・drop0。校正取得・400セットは未開始。[接続変更後の再確認](Recheck_After_Rewire_Rev0.md)。

最新ソフト切り分け：親37件SHA一致・通常再起動後もtimeout。7355 USBなしでも同じ。UART単体診断版でHOST起動をnative USBから確認したが、親の照会時にHOST自身のUART受信数が増えなかった。診断後は退避全2 MiBへ復元・verify・.25.2版確認済み。既存コネクタ再装着・通常構成復帰待ち。[ソフト・起動切り分け](Software_Isolation_Rev0.md)。

2026-11-28。ユーザー指定により本案件の保存先をこのフォルダとする。入力源の設定値はユーザー回答で200 mV。これは測定実値・精度保証とは区別する。既存R5実績は参考とし、R3の受入へ流用しない。

## 手順・受入範囲

1. 親／測定器HOSTの個体・FW・起動世代、7355 IDN、SD・通信IDLE・dropを確認する。HOST無応答を解消してから測定へ進む。
2. ATEからADC／DCV／連続・即時測定を確認し、R3を明示設定、R?=R3を確認。入力200 mVでMD?原文・計器エラーを記録する。上限付近でOL等となる場合、通信の完全応答と校正Cache採用の可否を分けて記録する。
3. TEST_START内でCAL_MEASURE_DISCHG_I／BATT_CHGのA/BをMD?で取得。原文V→mV→Aの換算・桁保持、照会の無送信、再取得時の旧ID拒否・TEST_END失効を確認。これは入力源による経路試験であり、実シャントでの精度試験や製品校正書込みとは扱わない。AD／AR／SS等の製品指令は送信しない。
4. 設定を確定した後、既存ADC耐久手順と同じ400セットを連続実行。各セットはTEST_START→MD?→ERR?→TEST_END→自己診断・SD・drop・IDLE照会。完了セット間1秒、399回待機。途中の設定変更・自動再送・リセットなし。
5. 全ATE応答・HOST A/T/Rのsession/request/原文相関、個体/FW/nonce不変、試行CSV400件の14列・開始終了・応答原文・SD／PC SHA-256一致を確認する。timeout／応答不対応／ログ欠落／nonce変化等で停止し、達成分と原因未確定事項を保存する。

製品のPASS／FAILや校正精度、量産総合受入とは区別する。受入基準は[承認済みCDC基準](../USB_Host_Reset_Study_20261121/CDC_Endurance_Acceptance_20261124_Rev0.md)、ADCの適用は[現行運用仕様](../ADC_Decimal_Hardware_Test_20261125/run_02/ADCMT_ADC_Command_Compatibility_Rev1.md)を参照。校正点は現行A/Bを使用し、過去資料の旧指定は使わない。

## 初期診断で確認した事実

親ID `69f7d45962cfdfad`、COM7／57600／CR、通信IDLE、SD OK、drop0。測定器リンクは有効、PIO送受信active、FIFO詰まりなし。ユーザーによる給電・USB・信号配線・診断RX確認とHOST RST後もHOST_INFOは約1秒でERR:HOST_TIMEOUT。監視開始合図後の照会では親PIOへ141バイト受理、受信0バイト。COM23の受信も0バイト。

BOOTSELで測定器HOST ID `BFCF2EDB84B0B37F`、FW `meter-host-relay-20261125.2`、2 MiBを確認。版違いとはいえない。全Flashの退避・独立照合を行う。原因は未確定で、初期受入・校正取得・400セットの実機試験は未開始。

追加確認：全2 MiB退避・独立verify成功（[マニフェスト](host_backup/manifest.json)）。既知.25.2 UF2の198ブロック・50,688バイトと退避内容が一致し、FW書込みは実施しなかった。PC USB単独給電で通常起動後も情報照会timeout、COM23受信0。診断RXを親GP12へ移して採取した141バイトはCRC付き情報要求として正常で、対象個体IDも一致した（[送信フレーム](parent_tx_decoded.json)）。親送信端での信号は確認済み。HOST受信端への到達とHOST内部の動作は切り分け継続。

HOST GP1へ診断RXを移した観測は0バイト（`host_monitor_host_rx_tap.raw`、`ate_host_rx_tap.json`）。親送信端とHOST受信端で観測差があるため、この間の配線・接点・測定位置を調査対象とする。断線箇所やHOST故障を確定したものではない。ユーザーへ別ジャンパ線で親GP12→HOST GP1を接続し直すよう依頼した。

初期ATE／親診断は`ate_initial.json`・`ate_after_rst.json`・`parent_*.log`、同期監視は`link_trace_ready.log`に保存。先行`link_trace.log`は監視開始と照会の同期を保証しないため、送信0バイトの根拠には使わない。

## 準備・検証

既存ADC耐久ランナーを別ファイル`scripts/run_7355_r3_endurance_20261128.py`へ複製。ATEポート、保存先、R3読戻し、入力設定値を明示できるようにした。元案件は未変更。模擬4件で400セット・399待機・ADC設定無送信・単発待機なし・異常停止と無再送を確認済み。実機耐久の成功を意味しない。
