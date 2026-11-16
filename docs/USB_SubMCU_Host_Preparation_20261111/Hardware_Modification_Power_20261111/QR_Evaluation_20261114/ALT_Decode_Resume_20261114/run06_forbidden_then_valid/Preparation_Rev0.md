# 禁止文字拒否後の正常35文字復帰 準備 Rev.0

2026-11-14。診断仕様Rev.0とqr_alt_decoder.cの許容文字・Enterまで破棄する処理に基づく実機試験。
同一起動でFORBIDDEN35→5秒間隔→VALID35を各1回読む。最初は4文字目のアンダースコア（ASCII95）を禁止文字としてkind13理由7で拒否し、完成文字列は出さない。残りをEnterまで破棄し、次の正常QRはkind12で35文字完全一致となることを確認する。
汎用解析器のcapture_errorsは保持し、異常系試験として期待との一致を別途照合する。
QR生成qrcode8.2、独立復号zxing-cpp3.1.1。原文・画像hashはTest_Data_Manifest.json。
FW変更なし。外部給電・QR Type_C2・GP0→SH-U05A RXD/GNDを維持、PC Type_C1・7355は外す。
受信READY後RSTのみ→3秒待ち→FORBIDDEN35を1回→5秒待ち→VALID35を1回。3回目は読まない。
UART115200/8N1・送信なし。完成またはエラー合計2件後5秒無受信で終了、最大600秒。終了条件と厳密解析は区別する。
