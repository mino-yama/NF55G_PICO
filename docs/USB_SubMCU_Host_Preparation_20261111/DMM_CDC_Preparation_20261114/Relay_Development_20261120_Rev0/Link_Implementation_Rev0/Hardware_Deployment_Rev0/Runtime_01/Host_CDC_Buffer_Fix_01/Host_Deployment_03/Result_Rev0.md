# Host CDC FIFO修正版 配置結果 Rev.0

2026-11-20。ユーザーのシリアルモニター終了、外部電源OFF、Hostの外部給電/親信号/GND/監視UART/USB-A切離し、BOOTSEL単独PC USB-C接続の完了後に実施。

対象BFCF2EDB84B0B37F、chipid 0xbfcf2edb84b0b37f、2048K、BOOTSEL、旧版meter-host-relay-20261120.2を照合。新UF2のSHA-256 529f12081432aea98189c4aeb3cc7a96fa28deb13d49b7a2f175cc9c75336ab5とmetadata .3を照合。旧全Flash2097152byteをsave -a -vで退避・照合し、案件保存先コピーhashも一致。退避SHA-256 406bfa54e0391a53fc572db42f12e06e5e81482382da94c1295c88632766bd65。

対象serial指定load -vで.3を書込み、Flash Verify成功。after infoで同一個体/新FW .3/BOOTSELを照合。rebootは行っていない。親ソフト変更なし。実機通常起動/累積Queryでの受信健全性は次試験待ち。全453件成功を継承し今回追加のソフト変更なし。

次はPC USB-Cを外し、外部給電・親信号/GND・ATEと7355 USB-Bを通常接続へ戻す。外部電源ON後にCONF_FIFO_Validation_01で設定変更/READなしのQuery12周を実施。監視UARTは今回未接続でよい。USERレンジ相違の確認と測定は受信健全性確認後へ保留。IssueはOpen維持。

[配置manifest](Deployment_Manifest.json)／[旧Flash退避照合](backup_verify.log)／[書込み照合](load_verify.log)／[書込み後照合](after_info.log)。
