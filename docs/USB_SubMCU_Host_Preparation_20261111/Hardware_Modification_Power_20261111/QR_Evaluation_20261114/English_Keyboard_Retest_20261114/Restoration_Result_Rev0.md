# QR英語キーボード設定への変更・原文取得版への復元 Rev.0

日付: 2026-11-14

## ユーザー指示

進行中の処理を待つこと、QRリーダーがAlt設定だったこと、英語キーボードへ設定変更したためAlt処理は不要であることを回答。再試験とプログラムを戻す指示を受領した。

## 実施したこと

- 進行中run07_firmware_decode_singleの受信を停止。停止状態と受信量は当該フォルダのUser_Stop_20261114.jsonへ保存。基板内Alt復元の実機試験完了として扱わない。
- 作業ソースが.2配布snapshotと一致することを確認後、Alt専用Cモジュール・nativeテスト・HID fixtureを本フォルダalt_working_archiveへ退避。旧releaseと既得rawは保持。
- CMakeLists.txt／main.c／README.md、PCログ検査器とそのテストを、旧release qr-uart-20261114.1の対応snapshotから復元。5ファイルの復元時hashはRestoration_Check.jsonで一致。
- 1024件のログ容量・GP0 TX／115200 8N1・Type_C2 PIO Hostは維持。Alt復元kind12／13は現ビルド・現解析から撤回する。正式親子UART・ATE／Cache／SSは引き続き変更しない。
- Host／Mock326件成功（5.854秒）、Host_Mock.txtへ保存。復元用UF2は既存のqr-uart-20261114.1、79360byte、SHA-256=0ce5168e546f25431e51922fb6fd0728a38697efb65937b9532da9f9aece1b81を再確認。

## 未実施・次工程

**現時点の実機Flashはqr-uart-20261114.2のまま。ソース復元と実機の書戻しを区別する。** .1への書戻しはまだ行っていない。build_uart_gp0の既存中間成果物も.2のままであり、復元には検証済みrelease/.1のUF2を用いる。将来の再ビルドはbuildスクリプトのCMake再設定を通す。

外部電源OFF、追加基板から外部5V線・QR・UART2線を外し、PC Type_C1だけを接続してBOOTSELへ移行。対象とUF2を照合しFlash退避・load -v・独立verifyで.1へ書戻す。その後、無給電で外部給電・QR・UART配線を戻し、英語キーボード設定の同じ35文字QRを1回再取得する。

英語キーボードの実HIDレポート・配列・suffixは今回まだ取得していない。旧Alt設定での実績を新設定の合格として転用しない。Altデコーダのnativeテスト結果は当時の履歴として保持し、採用済み・実機確認済みにはしない。USB-SUBのOpen状態は維持。

[復元hash](Restoration_Check.json)／[Host／Mock](Host_Mock.txt)／[復元用UF2](../../../../../firmware/usb_submcu_host_probe/releases/qr-uart-20261114.1/usb_submcu_qr_uart_probe.uf2)。
