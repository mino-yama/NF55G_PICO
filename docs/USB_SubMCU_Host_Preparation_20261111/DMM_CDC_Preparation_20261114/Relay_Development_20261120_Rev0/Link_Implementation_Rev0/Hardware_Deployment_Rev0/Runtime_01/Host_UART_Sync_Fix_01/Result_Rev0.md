# Host UART受信同期 修正 Rev.0

2026-11-20、FW meter-host-relay-20261120.2（ビルド/配置の結果は別manifest参照）。

## 問題と修正

試行8の電源投入前からの受動採取で、親Hの前にCRLFなしの00 00を2byte確認。旧Hostは余分なデータをHへ連結し、最初のHをCRC/形式検証で破棄する。取得原文を旧C engineへ入力してhなしを再現。

relay_host_uartは@を新フレーム先頭として受信候補を開始/再同期し、候補外のデータを破棄する。X1のpayload/session/各値はHEX等で、正しいフレーム内部に@は現れない。不完全/過長候補も次の@から新候補へ移り、512byte上限とCRLF終端、全体のCRC/形式/長さ/session/request/重複検証を全て通す。破棄した候補を実行せず、Qを自動再送しない。fault解除/再bind/旧機器応答排除の代用にはしない。親FrameReaderやNF55Gプロトコルは変更していない。

## 変更ファイルと検証

- firmware/usb_submcu_external_meter_host/relay_host.c: UARTフレーム先頭への同期。
- 同CMakeLists.txt: 新FW版20261120.2。旧.1 UF2/元Cを本フォルダへ別名保持。
- tests/test_external_instrument_link.py: 4回帰テスト追加。実原文の全78分割境界、起動データ入り親縦通し、不完全/過長候補からの同期、CRC/session/重複拒否を実C engineで検証。
- Software_Module_Interface/Test_Specification/Open_Issues/CHANGELOG: 実装詳細と進捗。

変更前回帰2件: failures=1、subTest errors=78で実不具合を再現。変更後Host Unit/Mock NF55Gは450件成功、失敗/エラー/skip=0。テスト起動の最初の集約コードはTestSuiteの階層処理で停止し、実機操作なし。修正して旧C回帰を実行した。

## 残事項

本記録作成時点でARMビルド実行中、実機Flash未更新。完了後にUF2/hash/metadataを照合して配置を準備する。実機で親H→h、USB-B未接続時LINK_NOT_READY、続いてUSB接続後の識別中継を確認する。電源投入時00byteの電気的発生源、PIO負荷/量産timing/切断復帰の受入は残る。IssueをCodex判断でCloseしない。レンジ問題は引き続き保留。

[修正前回帰](Before_Fix_Regression.log)／[全Host Unit/Mock](After_Fix_Host_Mock.log)／[ARMビルド](Build_Rev0.log)／[実機採取原文](../ATE_Host_Startup_Capture_08/host_rx.raw)。
