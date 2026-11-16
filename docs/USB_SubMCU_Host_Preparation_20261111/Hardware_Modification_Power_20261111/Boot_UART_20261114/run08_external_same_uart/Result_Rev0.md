# 同一UART配線・外部給電とRSTの比較 Rev.0

日付: 2026-11-14

## 結果

- run07のPC給電で受信できたUART2線を動かさず、PC Type_C1を外して外部5Vへ切り替える案内にユーザーが完了と回答。
- 受信READY後の外部電源ON回答後、観測時点で受信0byte。
- 同じ受信待機・外部給電を維持してRSTだけを操作するよう案内し、ユーザー「RST Push」と回答。その後309byteを受信し、無通信5秒で終了。COM22閉、送信0。
- 先頭00＋boot／board_idの正規2レコード。qr-uart-20261111.1／A06FEA01012EC137で一致。元rawはrun07を含む既得の309byteログとSHA-256まで一致。
- init_failedレコードは見られないが、Host初期化成功レコードはこのFWにないため、PIO Host成功とは断定しない。

## 判断と未確認

外部給電でもRST後のUART起動識別を確認できた。外部電源投入だけで起動レコードが現れず、RST後に受信できた差は残課題。今回の観測だけでは起動・リセット・信号線からの影響・電源立上り等の原因を確定しない。無負荷5.00V／3.3Vは静的測定であり、電源立上り波形の代替とはしない。

先頭NULの警告付き解析、original_framing_clean=false、hardware_acceptance=false、qr_text_verified=falseを維持。UART経路の識別確認と、無操作の電源投入起動・QR・7355・保護の受入を分ける。

## 次工程

外部電源をOFFにする。QR負荷試験前に既存作業票で要求した追加5V枝の1A供給枠に適した保護方式を確認する。申告済みアダプタ全体5V／2.4A・内蔵保護を追加枝保護の確認として置換しない。QR固定接続と電源OFF配線、PC Type_C1切離しを維持する。

[原文](boot_uart.raw)／[警告付き解析](boot_uart_with_startup_warning.json)／[受信結果](capture_result.json)。実行FW・ソース変更なし、Host／Mock再実行なし。
