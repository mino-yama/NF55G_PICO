# Host CDC FIFO確保量の修正 Rev.0

2026-11-20。ユーザーのレンジ確認ログでCONF?が36byteの不正な構成文字列を返したため、測定前に受信経路を調査。

## 確認事実

提示ログの復号: INIT:CONT?は0、OPC?は1、FUNC?は引用符付きVOLT:DC、AUTO?は0、SYST:ERR?は+0,No error。CONF?は999ET +1.999999E0E-0+1.000000E-05と引用符/CRLFで、宣言長も実データ長も36byteだが正常な設定応答として解釈不能。レンジ値を200V等へ読み替えない。提示ログは保存したが今回Codexによる同時実機採取ではない。

固定SDK2.2.0のTinyUSB src/class/cdc/cdc_host.cはrx_ff_bufをCFG_TUH_CDC_TX_BUFSIZEで確保し、FIFO初期化ではCFG_TUH_CDC_RX_BUFSIZEを渡していた。現行設定はTX=64/RX=256で、実配列64byteに対して深さ256のFIFOとなる。read後も累積indexが進むため、個別応答が64byte未満でも隣接領域への書込みが起こる。

## 再現と修正

実SDKのtusb_fifo.cと実cdc_host.cから取得した確保macro、製品設定headerをnative DLLへ接続した3テストで容量不一致/隣接canary書換えを再現。変更前は3テスト実行、532件のassert/subTest失敗、実テストerrorなし。初回3回はnativeコンパイラ属性/OSAL include順のテスト環境構築で停止し、ログを保持。native専用にGCC互換属性・little endianを指定して実FIFOを実行し、製品SDKは変更していない。

firmware/usb_submcu_external_meter_host/tusb_config.hのTX容量を256へ揃え、RX>TXのビルド時拒否を追加。固定SDKのrx配列も256byteとなり設定深さと一致。TX/RXのFIFO容量とUSB endpoint64byteは別で、endpointは64を維持。バッファ増加により関連CDC配列のRAM確保は計384byte増える。relay_mainの奇数長USB分割、X1上限/CRC/セッション、fault/再送禁止/任意SCPI本文保持は変更していない。新中継FW版はmeter-host-relay-20261120.3。

3回帰テストは実SDK FIFOによる累積応答40周の原文/隣接領域保持と、全256offsetから最大192byte応答の64byte分割読書き/周回を検証。変更後全Host Unit/Mock NF55G453件成功、失敗/エラー/skip=0。

## 推測と未確認事項

この容量不一致は確定したメモリ破壊不具合。ただし提示CONF?の特定の崩れ方がこれだけで生じたことは実機で未確認。修正版で複数Queryを累積して繰り返し、元の設定応答が保持されるか検証する。20V前面/200V読戻しの旧Issue原因をこの時点で確定/Closeしない。機器SCPIエラー0でもHostの受信メモリ健全性を保証しない。

ARMビルド実行中。完了後UF2版/hash確認→現行.2全Flash退避→.3配置→実機で累積Query/CONFを検証。測定/レンジ変更の追加送信は未実施。新Issue USB-RELAY-CDC-BUF-01はOpenで追跡、既存IssueもOpen維持。

[提示ログ復号](User_Transcript_Decode_Rev0.json)／[変更前実FIFO回帰](Before_Fix_FIFO_04.log)／[変更後453件](After_Fix_Host_Mock.log)／[ビルドログ](Build_Rev0.log)。
