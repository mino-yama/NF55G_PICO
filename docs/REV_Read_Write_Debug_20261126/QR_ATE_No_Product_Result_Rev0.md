# NF55GサンプルなしのQR／COM5試験 Rev.0

2026-11-26、OI-23。親Picoの双方向QR試験モードを追加し、HOSTへの受付要求と、同一受付IDを確認してからのQR受け付けを通常ATEコマンド入口に接続した。試験モードは既定で無効。指令名と取得IDの形式は現行を継承する。試験モードでは `QR_SCAN` が即時に `OK:QR_PENDING:<取得ID>` を返し、`QR_GET?` は、HOST応答待ちで `ERR:QR_ARMING`、応答照合後で `ERR:QR_READING`、完成時に原文を返す。タイムアウトは `QR_SCAN` からの全時間。量産ATEの応答待ち条件は未確定。 [試験計画](QR_ATE_Integration_Test_Plan_Rev0.md)

Host Unit／Mock NF55Gは557件成功。通常20セットと旧IDの遅着10セットを模擬UARTで連続評価した。旧形式、別ID、受付前の結果、取消、期限切れ、切断・再起動からの結果は書込みを許可しなかった。 [全回帰ログ](run_20261126_QR_ATE_No_Product_01/host_mock.log)

親の試験版はCOM6経由でRAMへロードし、実機のCOM5で通常ATEパーサ・サーバーを通した。試験アプリには製品UARTを割り当てていない。初回は全ソースのRAMロードがメモリ不足となったため、必要なクラスと更新メソッドだけを読み込む方式に変更した。再実行時のPIO領域確保エラーは、親の起動時に読み込まれたRXプログラムを再利用して回避した。 [初回ログ](run_20261126_QR_ATE_No_Product_01/parent_wire.log) · [PIO領域エラー](run_20261126_QR_ATE_No_Product_03/parent_wire.log)

COM5で取消済みIDの拒否、タイムアウト、通常のB（000002）の原文35文字とSS候補50文字の一致を確認した。照合後に `QR_WRITE` を問い合わせ、`ERR:NF55G_NOT_CONNECTED` を受信した。製品向け送信0件。同じ試行の遅着区間ではAのHID増加を観測できず、`TEST_END` の応答欠落と治具のログ欠落増加4件を記録した。終了応答とログ欠落の原因は未特定。RAMログに切り替えた再試行は `TEST_END` OK、ログ欠落0だが、最初の待機区間ではHIDカウンターに変化がなかった。 [通常Bと終了応答なし](run_20261126_QR_ATE_No_Product_04/ate_wire.jsonl) · [RAMログでの待機](run_20261126_QR_ATE_No_Product_06/parent_wire.log)

再試行ではAのHID読取中にPCからCOM5へ `QR_SCAN 60000` を送り、`OK:QR_PENDING` を確認した。QR用HOSTが同一受付ID・破棄フラグ1を応答し、応答後に取得したBの原文35文字とSS候補50文字が完全一致した。`QR_WRITE` は `ERR:NF55G_NOT_CONNECTED`、製品向け送信0件、`TEST_END` OK、当該RAM試行のログ欠落0。RAM試験後に親Picoの元の処理へ復帰した。 [COM5の応答原文](run_20261126_QR_ATE_No_Product_07/ate_wire.jsonl) · [HOST通知と受付ID](run_20261126_QR_ATE_No_Product_07/parent_wire.log)

QR用HOSTは試験前の全Flash 2 MiBを復元して独立照合した。固定配線復帰後にQR用HOSTのRSTを1回操作し、`qr-fixed-20261123.1`、対象個体ID、認識フラグあり・欠落0の定期通知3件を確認した。親Picoは通信IDLE、SD OK。親の累積ログ欠落は4、測定器HOSTは引き続き `ERR:HOST_TIMEOUT`。 [Flash照合](qr_arm_flash_20261126_142121_744937/restore_verify.log) · [復元後の起動ログ](qr_arm_flash_20261126_142121_744937/restored_boot_wire.log)

実スキャナーによる30セット、実SD使用時の終了応答とログ欠落の再確認、NF55Gサンプルに対するSS・D5の読戻し・復元は保留。量産ATEでの応答待ち条件と正式採用はOI-23で継続する。
