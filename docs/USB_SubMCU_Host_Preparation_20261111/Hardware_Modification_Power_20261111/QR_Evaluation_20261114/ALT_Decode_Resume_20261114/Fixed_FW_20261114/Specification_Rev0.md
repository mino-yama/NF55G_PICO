# 固定接続・連続読取候補FW 診断仕様 Rev.0

2026-11-14。ユーザー指定の「固定接続で電源投入～連続読取」を対象とする。正式親子UART／ATE／Cache／SSへは接続しない。

## 起動候補と診断

既存FWは起動ログを出すが、QR固定接続で電源ON時に列挙せず、RST後に列挙した。原因は未確定。
qr-fixed-20261114.1は起動出力後3000ms待ってからHostを初期化する候補。これは診断用仮値で正式timeoutではなく、解決済みとはしない。自動MCU再起動・無制限の初期化リトライは追加しない。
kind15は5byte（phase:uint8, value:uint32 little endian）。phase1=待機開始/value3000ms、2=configure直前、3=configure成功、4=tuh_init成功（2～4のvalueは0）。
kind14は24byte、uint32 little endian×6（main loop回数、PIO USB frame数、送信Queue drop累計、完成文字列累計、受信HID報告累計、flags）。flags bit0=既知QR profile有効、bit1=GP12電位、bit2=GP13電位、bit3=Host init成功。1秒ごとに送信し、mainとframeの進行を比較する。端子への追加の測定・配線変更は不要。

## 継続送信

旧RAM／UART原文版は保持し、新しいContinuousビルドだけ64件のFIFOを使用する。排出済み領域を再利用し、レコード数1024で停止しない。76byteのレコード形式と@HEX改行を維持。UART0 GP0 TX115200/8N1・受信なし。
HID原文kind6は送信せず、完成35文字kind12、エラーkind13、mount／descriptor等と上記診断だけ送る。Cデコーダの既知profile・許容文字・Enter境界・暫定5秒timeoutは変更しない。
FIFO満杯で上書きしない。dropを加算し、採番欠落と後続heartbeatのdropで検出する。有限Queueのため無限速度・無欠落は保証しない。callback内でUART待機せず、mainで最大16byteずつ排出。
新parserはこの版だけ蓄積上限1024件を適用せず、連番・descriptor・文字種・heartbeat／stage形式を厳密検査する。drop>0はcapture_errors。原文・先頭NULは保持し、汎用parserが自動受入判定しない方針を維持。

## 検証・実機への条件

Hostでは同じC FIFOをnativeコンパイルし、周回・満杯・再利用・順序とCデコーダの複数読取を検証する。既存Host／Mockを実行し、ARM版をビルド・配布hash固定後、対象個体のFlash退避・書込み・独立verifyへ進む。
実機ではQR固定接続のcold-startをRSTなしで複数回、異なるQRを含む20回以上の連続読取、完成順序・各1件・heartbeat進行・drop0を確認する。旧1024件上限を超える時間／読取数でも動作が止まらないことを確認する。
初回実機未検証。先頭NUL・電源ON認識・量産給電保護・7355／2 Host・正式リンクは未解決のまま。製品PASS/FAIL・Open Issue Closeなし。
