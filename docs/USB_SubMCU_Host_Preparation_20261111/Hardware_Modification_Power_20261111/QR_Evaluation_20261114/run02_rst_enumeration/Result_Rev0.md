# QR初回USB列挙・HID記述子取得 Rev.0

日付: 2026-11-14

## 実機取得結果

- QRをType_C2に接続、外部給電・UART維持、PC Type_C1と7355を外した手順。ユーザーがRST操作、QR LED青を維持・音なしと回答。
- COM22で771byte受信、5レコード連番0～4、解析エラーレコードなし、終了時COM閉。
- boot=qr-uart-20261111.1／board_id=A06FEA01012EC137一致。
- 起動後556msでHID mount（USB addr1／instance0）、同時刻に63byteのReport Descriptor全体を取得。
- 557msでmount、VID=E851／PID=1001（raw 51e80110をlittle-endian変換）。
- HID mount raw=00003f00、interface_protocolと現在protocolの取得値は各0。Boot対応を推定して確定せず、レポート記述子を根拠に次の原文調査へ進む。
- 記述子はGeneric Desktop Keyboard用途。修飾8bit＋予約8bit＋8bitキー6個の入力、LED出力5bit等を宣言していると読める。実際のHID reportは未取得。

## 範囲と制約

今回Type_C2 PIO Hostで対象のUSB列挙とHID記述子取得を実証。QR文字列・配列・suffix・35文字一致、両プラグ向き、7355と2 Hostは未確認。先頭NUL 1byteは警告付き解析、original_framing_clean=falseを維持。UART末尾完全性・破棄数は単独で証明しない。

初回180秒無受信と今回のRST後取得を保持し、電源投入起動の問題解消や全Host受入とはしない。青LED・音なしは申告観察であり、LED色のメーカー定義から動作状態を推測していない。

## 次の1回読取

[35文字試験QR](../test_data/QR_35chars.png)、[期待原文35byte](../test_data/expected_35chars.txt)、[生成情報](../test_data/manifest.json)を作成。qrcode 8.2をGit管理外tools/usb_submcu/qr-test-generatorへ導入して生成し、元画像の加工や外部サービスへの送信はしていない。独立ソフトによるQR復号は未実施のため、実機取得結果とも照合する。

受信を起動前から開始しRSTでboot／記述子を取得した後、このQRを1回だけ読む。読取データはまずHID原文として保持し、配列・suffix確認後にデコーダの実装とテストへ進む。

[受信原文](boot_uart.raw)／[解析JSON](enumeration.json)／[受信条件と終了状態](capture_result.json)。FW・既存ソース変更なし、Host／Mock再実行なし。
