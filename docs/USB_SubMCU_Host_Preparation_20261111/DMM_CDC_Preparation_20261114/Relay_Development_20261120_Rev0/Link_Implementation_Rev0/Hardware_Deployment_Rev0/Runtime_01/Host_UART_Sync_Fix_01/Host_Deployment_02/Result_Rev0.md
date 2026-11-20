# Host同期修正版 配置結果 Rev.0

2026-11-20。ユーザーの外部電源/Host給電・親信号/GND・UART切離し、Host BOOTSEL単独PC USB-C接続の完了後に配置。

対象serial BFCF2EDB84B0B37F、chipid 0xbfcf2edb84b0b37f、RP2350 A4/2048K/BOOTSEL、旧FW meter-host-relay-20261120.1を照合。新UF2はmetadataの.2とSHA-256 cb3fc420088b72eae1bab80fad5ddb09c75f0bd8a79889aefddb08f42a869defを照合。

現行全Flash 2097152byteをsave -a -vで退避・照合。案件保存先コピーのhashも一致し、SHA-256 db789fa1656ee5db02b7d198b23ae5949d9f68fc22128beaf0b9cb8f19d1e003。対象serial指定load -vで.2を書込み、Flash Verify 100% OK。書込み後infoで同じ個体/新FW版/BOOTSELを照合。rebootなし。

実機は.2へ配置済みだが、通常起動・親経由の実機受入は未確認。親ソフトは変更していない。ソフト回帰は直前450件成功を継承。次はPC USB-Cを外し、外部給電/親信号/監視を戻して電源OFFで待受開始後にONする。USB-BなしでLINK_NOT_READYが返るか確認する。IssueはOpen維持。

[配置manifest](Deployment_Manifest.json)／[全Flash退避照合](backup_verify.log)／[Flash書込み照合](load_verify.log)／[書込み後個体/版](after_info.log)。
