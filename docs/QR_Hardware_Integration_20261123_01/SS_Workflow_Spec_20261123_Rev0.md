# QR→SS 明示書込み仕様 Rev.0

2026-11-23ユーザーの対応案了承と「はじめて下さい」を受けて実装。製品FW書換えではなく、SSによる製造情報設定である。FUは引き続き禁止。

## 承認された対応

|欄|生成規則|今回の値|
|---|---|---|
|FW_REV6|変更なし指定|FFFFFF|
|UNIT_REV4|QR REV3＋ASCII空白1文字|`A1. `|
|UNIT_LOT4|QR YY＋WW|2601|
|UNIT_SERIAL6|QR号機6文字そのまま|000001|
|ADUのREV4／LOT4／SERIAL6|変更なし指定|各欄をFで充填|
|BBUのREV4／LOT4／SERIAL6|変更なし指定|各欄をFで充填|
|予約2|変更なし指定|FF|

SS DATAは50 ASCII文字。r1本文22ページSET SERIALの最大値＝変更なし指定を使用。型式・品目コードはSS DATAに入れない。型式／REVの値を例示値に固定せず、週から月に変換しない。

## ATE入口

|指令|応答・動作|
|---|---|
|TEST_START|既存の試行開始。QR取得を新世代にし、前試行値を失効|
|QR_SCAN timeout_ms|100～60000ms、現在試行の取得を開始。OK:QR_ARMED:取得ID|
|QR_GET? 取得ID|READYならOK:QR_GET:取得ID:QR原文。照会のみ|
|QR_DATA? 取得ID|READYならOK:QR_DATA:取得ID:SS_DATAの100桁HEX。照会済みとして記録|
|QR_WRITE 取得ID|同一試行・READY・照会済みIDだけSSを一件実行。成功時OK:QR_WRITE:取得ID|
|QR_CANCEL|取得を取り消す。OK。NF55G送信なし|
|INFO_REFRESH|書込み後の明示D5読出し。SSから自動実行しない|
|UNIT_REV? 等|既存INFO Cacheだけを照会。INVALIDで自動D5しない|

取得IDは起動nonce16HEX＋試行世代＋取得連番。QR_GET?だけでは書込み可にしない。ATEはQR_DATA?のHEXを確認した後に別指令QR_WRITEを送る。SERIAL_SET_RAWは内部builder専用で、ATE parserには公開しない。

## 保持・失効と異常

最初の完全な35文字だけを保持する。READY後の2件目は破棄し、確認済みの値を差し替えない。文字・長さ不正、受信frame／overflow、HOSTのエラー・drop、取得中の再起動／切断、timeoutでREADYにしない。開始前の親UART残留と断片を捨てる。照会からQRやNF55Gを再取得しない。

書込み前のBUSY／未接続は無送信で保持。実行結果を得た書込みは成功・明示拒否・成否不明とも取得値を消費し再使用を拒否。成否不明はAMBIGUOUS=1で返し、SSのDATA／INFOをINVALIDにする。STATUSはSS応答から更新しない。TEST_END成立時に未使用取得値も失効する。

NF55G transactionは既存protocolの一件のみで実行し、T2=100ms、SS正常応答DATA0文字。既存Command Retry上限1回／Response Retry別管理を継承。実機限定試験では追加guardでSSフレーム二回目を拒否した。ログはRAM queueに積み、NF通信中SD write/flushをしない。

## 現在の限界

QR HOSTはGP0 TXのみで、親から要求IDを送る双方向契約がない。親へ到着済みの旧データと旧取得IDは排除するが、開始前からスキャナー内で処理中だった読取が開始後に完成する場合の識別は未実装。この遅着境界は正式運用の受入条件として残す。今回の有限試験はQR_SCAN受付後の2回読取りであり、前試行の遅着除外を実証したものではない。

同一QRが別の新規受付で再取得されれば、ATE確認後に再書込みできる。製造号機の重複利用や製品PASS／FAILをPicoは判定しない。電源再投入後の保持とRST不要cold-startも今回の検証外。

root configのQR_HOST_ENABLEDは既定False。今回の実配線済み親だけTrueで配置し、既存EXTERNAL_INSTRUMENT設定を保持した。親7ファイルを退避・配置・hash照合・再起動し、既存active_appを再利用して実機試験した。
