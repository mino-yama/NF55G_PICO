# USB SubMCU 実機確認前の準備 Rev.0

日付: 2026-11-11／対象: RP2350-USB-C A06FEA01012EC137

## 今回の範囲

ユーザーの「実機確認の手前まで」を受け、Type_C2 QR単体の列挙・HID原文収集FW、オフライン検査、受信ツール、実機記録票を新規準備。基板への書込み・reset・COM操作・改造・QR／7355への送信は今回行わない。現在配置済みのUSB単体確認FW dev-20261111.1と旧FWバックアップは保持。

本probeは最初の記述子／HID形式調査用であり、QR文字列デコーダ・35文字受付・正式治具UART・DMM測定・2 Host共存の完成版ではない。実機形式未確認のままサンプルのUS配列や8byteキャストを本番へ採用しない。

## 固定条件と実装

- Type_C2=QR、D+=GP12／D−=GP13、PIO0 SM0 TX／PIO1 SM0 RX・SM1 EOP／DMA0、sysclock120MHz。基板内だけの資源であり治具PicoのPIO設定を変更しない。ネイティブType_C1 USBは初期化しない。
- SDK2.2.0 a1438dff1d38bd9c65dbd693f0e5db4b9ae91779、TinyUSB86ad6e56c1700e85f1c5678607a762cfe3aa2f47、Waveshare774cbb1e8ecc9d5cc8474ba9feb90a0939047f3bを使用。メーカーの14ファイルをvendor/upstream-774cbb1へ原文保持し、取得URLとSHA-256をmanifestに記録。ビルド用vendor/pico-pio-usbはusb_rx.pioの重複ヘルパー1箇所をSDK正式APIへ置換した派生コピー。SDK_2_2_0_Compatibility.mdを参照。非void returnの削除はしていない。
- Hostはroothub1のみ、直接接続1機器／HID最大4インターフェース／64byte report、記述子buffer512byte。Hub／CDC／MSCを無効。VID/PID、記述子、HID原文、受信要求失敗等を起動後msと連番付きで保存。64byte超のreportは異常として記録し文字列へ切捨て採用しない。
- RAM診断g_probeは19476byte、256レコード。満杯は旧記録を上書きせず破棄数を加算。満杯または破棄ありのログは検査ツールが拒否。短い1読取ごとに記録する。SD・Flashへ実行時ログを書かず、電源OFFで消える。
- 通常のビルドではUARTピンも初期化しない。正式な治具UARTピン・baud・CRC等は未確定のまま。

## ログ経路の準備と未確定部分

標準成果物はRAMログ版。debuggerでCPUとIRQを停止してg_probeの19476byteを保存し、下記で検査できる仕様。ただしSWD端子のアクセス・プローブ所持・接続は未確認で、この経路が現物で使えると確定していない。

任意の診断TX専用ビルドはCMake PROBE_UART_TX_PIN=0でGP0／UART0 TX、115200・8N1を使える。これは追加基板単体評価だけの候補であり、治具のGP0／ATEへつなぐ指示ではない。現物端子・3.3V対応変換器・共通GND・電源経路を確認してから候補を採用する。受信／指令処理は実装しない。ユーザーから既存Pico転用／専用Pico追加／USB–UART購入の3案が提示された。[比較と購入仕様](Diagnostic_Adapter_Options_Rev0.md)では親Picoを保持できる③を推奨。最終型番は未確定。標準ビルドと任意TX版の検証結果はResult.mdに区別して記載する。

将来の診断配線は追加基板GP0 TX→変換器RX、GND共通の候補。変換器TX／VCCは接続しない。TTL3.3Vであることを型番で確認し、RS232C電圧の変換器をつながない。片側無給電時の逆給電条件も確認。機器評価中のType_C1へのPC接続は行わない。

任意TXは1レコードを「@＋76byteの大文字HEX＋LF」で非blocking送信する。起動前から受信待ちし、途中接続のログはboot欠落として拒否。UARTログでは末尾欠落／RAM破棄数を単独では証明できず、検査結果にもtail_completeness=not_provenと明示する。ログなし・途中ログを合格証跡にしない。

## 実機へ移る前の順序

1. ログ経路と必要機材、56kΩ1%抵抗の実装サイズ、外部5V枝の保護・定格・端子を照合する。
2. 担当者と実機確認を始める直前に、[治具図Rev.4](../drawings/NF55G_Fixture_20261111_Rev4/README.md)の4・5枚目とメーカー位置写真を使い改造手順を案内する。今は施工しない。
3. 全USB・外部5Vを外して改造し、写真・外観・接続を確認。微細DB_N／DN1の測定は要求しない。
4. QR／7355なしで選択した1系統から電源のみを確認。書込み時は外部5VとQR／7355を外し、PC Type_C1のBOOTモードで個体を確認する。今回の書込みコマンドは実行しない。
5. FW書込み・verify後はPCを外し、外部電源OFFでQRをType_C2へ接続。ログ待受と保護枝を用意して電源投入。記述子と短い1読取の原文を取得する。
6. 電源OFFでUSB-C向きを変え再試行。初期評価で活線挿抜しない。電流・電圧降下・resetを記録する。
7. 実記述子／Boot・Report形式／配列／suffixを照合してデコーダを実装・Hostテスト後、35文字完全一致／先頭ゼロ／大小文字／ハイフン／欠落重複を受入する。
8. 7355のType_C1 Host回路と2 Host実装、実USB CDC適合、治具UART正式仕様が整ってからDMM単体・共存へ進む。本probeへ7355を接続しても測定しない。

記録は[未実施の記録票](Hardware_Record_Template_Rev0.md)へ残す。給電はPCデバッグと外部Expanderを排他的に切り替える。QR／DMM時の1A枠はユーザー申告であり、保護機能や負荷時実測の証拠とは分ける。

## 2 Host構成で判明した制約（USB-SUB-03、Open）

確認事実: 固定TinyUSBのsrc/host/usbh.cに単一の_usbh_controllerがあり、Host初期化はその1変数へrhportを代入する。またPIO版とネイティブ版のHCDは同名APIを提供し、CFG_TUH_RPI_PIO_USBで選ぶ構造。メーカー例はネイティブDevice＋PIO Hostで、2 Hostではない。[固定版ソース](https://github.com/hathach/tinyusb/blob/86ad6e56c1700e85f1c5678607a762cfe3aa2f47/src/host/usbh.c)

判断: この構成でtuh_init(0)、tuh_init(1)を2回呼ぶだけの実装を2 Host対応として採用できない。ハードウェア上の2 Host不可能を断定するものではない。

今後の検討案: ネイティブTinyUSB Hostと独立PIO Hostスタックを組み合わせる方式、または複数HCDを管理できる分離・拡張を検証する。API・IRQ・共有Queue・列挙・切断・PIO時刻依存をテストするまで選定済みとしない。ユーザー指定のポート固定とハブなし条件は維持。基板追加・ハブ追加・機器入替えを勝手に行わない。

未確認: 2 Host同時実行、7355記述子と実設定、Type_C1のHost回路条件、診断機材・端子、HID実形式、正式UART仕様、電源保護。USB-SUB-01／02／03はCloseしない。

## 再実行

ビルド（書込みなし）: scripts/build_usb_submcu_host_probe.ps1。

RAMのオフライン解析:

    .venv/Scripts/python.exe scripts/usb_submcu_probe_log.py probe_ram.bin --format ram --output probe_ram.json

任意UART候補を採用し配線・機器を照合した後だけの受信例（今回は実行しない）:

    .venv/Scripts/python.exe scripts/usb_submcu_probe_capture.py --port COM番号 --seconds 20 --output capture.raw
    .venv/Scripts/python.exe scripts/usb_submcu_probe_log.py capture.raw --format uart --output capture.json

結果はraw_capture_onlyまたはcapture_errors。hardware_acceptance=false／qr_text_verified=falseを常に付け、USB列挙・原文取得だけを製品やQR完全一致の合格へ昇格させない。

## ビルド時に確認した互換条件

SDK正式APIと重複するusb_rx.pioのヘルパーは、原文をvendor/upstream-774cbb1に保持した派生コピーで削除。newlib_malloc_lock.cは既存Arduino GCC14.3の公開mallocロックhookをSDK再帰mutexへ接続し、alarm pool確保を含むリンクを成立させる。ロックのno-op化、メーカーのreturn削除、SDKの直接改変は行わない。[newlibの公開hookと再帰要件](https://sourceware.org/newlib/libc.html)およびvendor/SDK_2_2_0_Compatibility.md参照。実機の起動・USB Timingは未検証。

任意GP0 TX分岐は同じGCC／依存include／警告設定で構文検査を行う。正式な診断機材・ピン確認まではRAM版のみを配布対象とし、UART版のUF2書込みや実機受入を済ませた扱いにしない。

## 2026-11-11 デバッグ変換器の指定

ユーザーがDSD TECH SH-U05Aを指定。メーカーのTTL信号3.3V・UART仕様を確認し、FTDI購入候補は履歴として保持。[採用機材と端子・モード・接続準備](SH_U05A_Debug_Setup_Rev0.md)を追加。初回は追加基板GP0診断TX候補→SH-U05A RXDとGNDのみ、TXD／3V3／5V0は接続しない。現物・COMと診断GP0採用は未確認、現RAM版UF2はUART無効のまま。FW変更・書込み・実機通信は行っていない。
