# UART診断FW仕様 Rev.0

日付: 2026-11-11／開発版: qr-uart-20261111.1

## 対象と役割

追加RP2350-USB-CのType_C2 QR列挙・HID原文調査用。SH-U05AのRXDで診断出力を受信する。親Picoとの正式UARTリンク、QR文字列判定、7355測定、2 Host共存は対象外。親Pico・既存ATE／NF55Gのピンと処理を変更しない。

| 設定 | 内容 |
|---|---|
| 出力 | 追加基板GP0／UART0 TXのみ |
| 通信 | 115200bps／8bit／parityなし／stopbit1、HWフローなし |
| SH-U05A配線 | GP0→RXD、GND共通。TXD・3V3・5V0未接続 |
| 入力 | UART受信処理・コマンド受付なし。GP1をUARTへ割り当てない |
| USB | Type_C2 PIO Hostのみ、D+=GP12／D−=GP13。ネイティブType_C1 USBとstdioは無効 |
| 診断領域 | RAM g_probe=19476byte、256レコード、満杯時は上書きせず破棄数を加算 |
| 依存 | SDK2.2.0、TinyUSB86ad6e5、Waveshare774cbb1。前回のSDK互換派生とnewlib再帰ロックhookを維持 |

## UART出力形式とタイミング

1レコードはRAM ABIと同じ76byteを大文字ASCII HEXへ変換し、@を先頭、LFを末尾に付ける。1行は154byte（@1＋HEX152＋LF1）。元レコードはlittle-endianのseq:uint32、ms:uint32、kind/addr/instance/length各uint8、data64byte。kindの定義は既存scripts/usb_submcu_probe_log.pyと同じ。CRCや要求受付は付加せず、正式な治具UARTフレーム仕様にはしない。

起動ログはkind1にqr-uart-20261111.1、kind11に実ボードの個体IDを記録する。UART設定後、PIO Host初期化の前にこの2レコードを先に送り、通常ループではtuh_task_ext(0,false)とFIFO空き確認・最大16byte送信を交互に実行する。初期ログの送出待ちはUSB開始前のみ。Hostのconfigure/initがfalseを返した経路ではkind10を記録し、UARTの排出を続ける。SDK panicやクロック設定失敗まで捕捉する例外処理ではない。

USB callback内ではRAM記録だけを行い、SD／Flash書込み・UART送信待ちをしない。SH-U05AのTXDは追加基板へつながず、XON/XOFF等の制御も受けない。送信がログ発生量に追いつく保証はなく、256件上限を踏まえ短い1読取ごとに記録する。UART線上にRAM破棄数は出しておらず、末尾欠落・満杯の完全性をUART単独で保証しない。解析はraw_capture_only／hardware_acceptance=false／qr_text_verified=falseを維持する。

## 配布とビルド

ビルドスイッチ-DiagnosticTxはPROBE_UART_TX_PIN=0を設定し、専用build_uart_gp0フォルダへ出力する。RAM側の既存buildと過去配布フォルダは保持。UARTの版名・bootデータはCMakeのPROBE_FW_VERSIONで共通化し、GP0診断TXとGP12／13のピン用途をバイナリメタデータへ記録する。

```powershell
& ./scripts/build_usb_submcu_host_probe.ps1 -DiagnosticTx
```

検証結果と配布hashは[結果](Result_Rev0.md)に記録する。現物の起動・波形・ログ受信はまだ試験していない。SH-U05A単体の112件ループバック成功はUART版FWの実機受入とは区別する。

## 実機前の条件

- SH-U05AのTXD–RXD短絡をUSBを抜いて外す。UARTモード選択ジャンパは維持。除去済みとの回答はまだ得ていない。
- 実機直前の改造案内、R13／CC抵抗の施工後確認、外部5V枝の保護・極性確認を先に行う。未改造基板へ今回書き込まない。
- GPIO表示0とGNDを現物照合後に診断配線を実施する。親PicoのGP0へは接続しない。
- 実機のFW書込み時はQR／7355・UART配線・外部5Vを外し、PC Type_C1のみの給電に切り替えて対象を照合。機器評価時はPC Type_C1を外し、Expanderの外部5Vのみで追加基板を給電する。
- 受信待ちを起動前から開始して版・個体ID・原文を保存する。実COM番号とVID/PIDを照合し、以前のCOM22を無条件に流用しない。

今回はビルドとファイル・Host／Mockの検証までで、COM・実基板・FW配置を操作しない。USB-SUB-01／02／03はOpen。
