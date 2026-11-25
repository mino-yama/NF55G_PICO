# 診断ランナー修正後の実機耐久再試験

2026-11-25 12:33 JST。前回のCSV回収後、親Picoのリンクfaultとログ停止状態を個体指定で確認し、親Picoを通常再起動した。測定器HOSTは管理RSTを1回実行し、FW `20261125.2`、同一個体 `BFCF2EDB84B0B37F`、新nonce `3363029CBA05827C`、`READY` を確認。修正したランナーでの単発は40.407 mVで完了。 [HOST復帰ログ](retest_recovery_after_T000082/host_rebind.json)／[単発試験](endurance_20261125_123310_692675/result.json)

12:33:18～12:42:24 JSTに固定配線、COM5／COM23、ATE選択値200 mV、入力設定40 mVで400セットの再試験を実施した。ランナーから測定レンジを変更していない。233セットを完了し、第234セットで停止した。第234セットを含む234件のREADは40.404～40.408 mV、最長688 ms。完了233件の計器エラー値は全件0、終了自己診断は最長141 ms、SDチェックは全件OK、ログ欠落は0件だった。 [試験結果](endurance_20261125_123318_520823/result.json)／[ATE全応答とHOST相関](endurance_20261125_123318_520823/ate.jsonl)

第234セットではREAD要求473が40.405 mVを返した。続く `EXT_QUERY 2000 :SYST:ERR?` の要求474は2,032 msで `ERR:EXT_TIMEOUT:AMBIGUOUS=1`。同一要求のHOST `A/T/E` を採取した。E原文は `TIMEOUT_RX0_T1_C0_XNONE_I2000_N2000_D0_S80_P5A_EP81_H1_K1_L0/64_OA2_ON0_OX0_OPD2_OE02|1`。PIO観測ではOUT EP `0x02` がACK 2、NAK 0、その他0。IN EP `0x81` は2,000回すべてNAK、応答データ0バイト。USBトランザクションのACKまで確認できた。7355内部でのSCPI処理とタイムアウト原因は未確定。 [HOST UART原文](endurance_20261125_123318_520823/host_uart.bin)／[USB-IF USB 2.0仕様](https://www.usb.org/document-library/usb-20-specification)

停止後に同じnonceで `FAULT`、親 `IDLE` とSD応答 `OK` を確認し、失敗セットを `TEST_END` で閉じた。測定器への再送とHOSTの再起動は実施していない。親Pico経由のCSV回収は、対象 `T000084`～`T000317` の同定後に `OSError: read failed` で止まった。24 MHzおよび一時的に4 MHzへ下げた状態で失敗セットのファイルを個別に照会しても同じエラー。設定は24 MHzへ復帰済み。 [停止後の確認](endurance_20261125_123318_520823/failed_trial_close.json)／[回収時のエラー](endurance_20261125_123318_520823/csv_export_20261125_124244_809011/csv_usb_raw.log)／[4 MHzでの読出し](endurance_20261125_123318_520823/sd_readonly_4mhz.log)

12:45 JST。PCカードリーダーのE:でFAT32を確認し、前回回収済みのT000082とSHA-256を照合してSDを識別した。完了233件と失敗1件の計234件をSDへ書き込まずに回収し、すべてでSD原本とコピーのSHA-256、CSVの14列、行数、試行開始・終了マーカー、ATEのREAD／SYST:ERR応答を照合した。親Pico経由のSD読出し異常の原因とUSB応答タイムアウトとの関連は未確定。 [回収マニフェスト](endurance_20261125_123318_520823/pc_card_recovery_20261125_124518_904506/manifest.json)／[停止試行CSV](endurance_20261125_123318_520823/pc_card_recovery_20261125_124518_904506/20261125_124219_T000317.csv)／[FAT32確認](endurance_20261125_123318_520823/pc_sd_volume.log)
