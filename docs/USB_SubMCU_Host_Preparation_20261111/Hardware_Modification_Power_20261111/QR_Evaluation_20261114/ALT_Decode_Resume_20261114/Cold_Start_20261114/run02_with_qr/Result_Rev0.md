# QR接続電源投入・RST前 結果 Rev.0

2026-11-14。電源OFFでQR Type_C2接続、UART受信準備後、外部5VのみON。RST/BOOTなし。

確認事実: 起動版qr-uart-20261114.2／基板A06FEA01012EC137のboot・board_id 2件、309 byte（先頭NUL1 byte含む）。QR A読取前後で原文byte数・hashは不変。HID mount／descriptor／mount／HID report／完成文字列は未取得。初期化失敗の記録もなし。
ユーザー観察:「読み取り完了。LED 赤に変化、青、音あり」。これはリーダーの読取反応であり、HOSTへの転送成立を意味しない。

この条件でFWは起動出力まで実行された。一方QR認識・データ転送は確認できない。無受信をCPU未実行とは判定せず、Host初期化以降の状態・給電立上り・機器起動順・接続状態等の原因は未特定。
受信プロセスを対象限定で停止し、原文を固定保存。通常完了metadataとは区別してCapture_Stop_Rev0.jsonへ記録。元原文は変更しない。
次に外部給電・QR・UARTをそのまま維持し、別受信区間でRSTだけを操作して比較する。FW変更・書込みなし。

[原文](scan_uart.raw)／[解析](Parsed_Rev0.json)／[停止記録](Capture_Stop_Rev0.json)
