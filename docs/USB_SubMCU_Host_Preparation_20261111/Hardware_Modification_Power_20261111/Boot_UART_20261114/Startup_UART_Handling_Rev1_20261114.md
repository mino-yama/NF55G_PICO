# 起動UART先頭NULの診断解析 Rev.1

日付: 2026-11-14。Rev.0の厳密形式不合格と元ログは保持する。

## 確認と変更

電源投入・RSTの両受信は309byteで完全一致。00が1byte、その後に版と個体IDの正規レコード各154byteが続く。原因は未確定。

scripts/usb_submcu_probe_log.pyのread_uartと既定CLIは引き続き先頭NULを拒否する。追加したread_uart_captureとCLIの--allow-startup-nulは、先頭が00 40（NUL＋@）の場合だけ1byteを分離し、以後の厳密解析を実施する。任意ノイズを探して読み飛ばす処理は入れない。

分離時は連番0のboot、連番1のboard_id、16桁HEXのID、最終LFを必須とする。source_sha256／source_bytes／startup_prefix_hex=00／original_framing_clean=falseと警告をJSONへ保存する。途中NUL・任意prefix・複数NUL・連番欠落・不完全記述子は拒否し、init_failedはcapture_errorsとして保持する。

raw_capture_only／hardware_acceptance=false／qr_text_verified=falseは従来どおり。警告付き解析の成功をUART電気・元フレームの合格、Host初期化成功、QR読取成功としない。

## 検証

新規7テスト: 明示指定なし拒否、警告と非合格情報、clean入力、任意／複数prefix拒否、途中破損／連番欠落拒否、IDと最終LF必須、init_failed維持。

全Host／Mock322件成功（6.967秒）。[実行ログ](Startup_NUL_Host_Mock_20261114.txt)。2本の既得rawを変更せず解析し、[電源投入時JSON](boot_uart_with_startup_warning.json)／[RST時JSON](run02_rst/boot_uart_with_startup_warning.json)を新規保存した。FW・旧配布ソースsnapshotは変更していない。

## 次の実機手順

外部電源OFF、追加基板のPC Type_C1を外し、QR／7355も未接続で、GP0→SH-U05A RXDとGND→GNDの2線を戻す。変換器TXD／3V3／5V0は接続しない。SH-U05AのみPC接続、追加基板はExpander経由の外部5V配線を使用する。受信待機を確認するまでは外部電源を投入しない。

この次工程は外部給電・QRなしの起動診断。保護条件未確認のQR負荷試験を先行させない。アダプタ5V／2.4Aと内蔵保護の申告、追加枝1A保護・制限値未確認という状態は維持する。異常発熱等の有無はユーザー未回答のため「異常なし」とは記録しない。
