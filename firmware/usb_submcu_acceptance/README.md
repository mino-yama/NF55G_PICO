# USB SubMCU 単体確認FW（開発用）

識別: dev-20261111.1。Waveshare RP2350-USB-C（RP2350A／Flash 2MB）のType_C1 USB CDCだけを使用する。量産版・QR／DMM用FWではない。USB Host・PIO・UART・LED・SD・RTC・NF55G処理を初期化しない。既存の治具Picoへ配置しない。

## 確認用USBコンソール

これは内部UART／正式ATEコマンドの確定ではなく、この隔離した単体確認FWだけの診断用インターフェース。

| 入力 | 応答 |
|---|---|
| ID? | FW／VERSION／BUILD／SDK／BOARD／ID、USB_HOST=OFF／UART=OFF／PIO=OFF |
| PING | PONG |
| UPTIME? | UPTIME_MS=起動後ミリ秒 |
| ECHO 半角ASCII文字列 | ECHO=受信文字列 |
| その他 | ERR:UNKNOWN_CMD |

入力はCR／LF／CRLF終端、応答CRLF。空行は無応答。最大95文字（終端を除く）。過長／不正文字は終端まで破棄しERR:LINE_TOO_LONG／ERR:ASCIIを1回返す。DTR接続時にREADY:USB_SUBMCU_ACCEPTANCEを出力。DTR切断で部分行を失効。USB CDCの115200設定は内部UARTの正式baudを決定しない。

自動測定、補正書込み、Flash設定保存、USBデータ用リセットコマンドは設けない。SDKのpicotool向けUSB reset interfaceは残し、復旧／書込みに利用する。1200bps resetは無効。GPIO12/13のPIO-USB、GPIO16のLEDも操作しない。

## 依存とビルド

- Pico SDK 2.2.0: a1438dff1d38bd9c65dbd693f0e5db4b9ae91779
- TinyUSB: SDKが指定する86ad6e56c1700e85f1c5678607a762cfe3aa2f47
- GCC Arm 14.3.0（既存Arduino環境pqt-gcc 4.1.0-1aec55e）
- CMake 3.31.6、Ninja 1.11.1.4（案件内.venv）、公式picotool 2.2.0-a4（pico-sdk-tools v2.2.0-4）

ボードヘッダはSDKのpico2既定GPIO・4MBを流用せず、本基板用RP2350A・2MB・Flash divider4を明示する。GPIO割当てを定義せず、UART stdioを無効化。USBだけを直接stdio_usb_initする。

ビルドと配置証跡は[受入記録フォルダ](../../docs/USB_SubMCU_FW_Acceptance_20261111/)に保存する。出力UF2・ELF・binは配布物のhashと対応付ける。main.cppのSHA-256先頭16桁をBUILDへ埋め込む。全ファイルの同一性は別途manifestで管理する。

## 実機試験・復旧

scripts/usb_submcu_acceptance_hil.pyを--serial A06FEA01012EC137 --build <BUILD> --output <新規JSON>で実行。対象USB serialを限定し、識別・終端・分割／連結・最大長／過長・不正文字・100件の連番echo・切断後部分行失効を検証する。既存治具69F7D45962CFDFADへ接続しない。

書込み前に対象Flash全2MBをbackup/original_flash_2MB.binへ保存し、picotool verifyで元Flashとの一致を確認する。復旧時は対象USB serialを限定して元binを0x10000000へ書込み、verify後に再起動する。量産承認やUSB Host／電気受入の合格を意味しない。Type_C2、QR、7355、治具UARTは外したまま。
