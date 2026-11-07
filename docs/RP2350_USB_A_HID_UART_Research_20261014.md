# RP2350-USB-A HID受信 UART出力サンプル調査

調査日: 2026-10-14。対象はNF55G試験治具のQR入力経路。既存NF55G通信とPico 2プログラムは変更しない。

USB HIDキーボード入力をASCIIへ変換してUARTへ送る公開実装が見つかった。ただし、そのUART出力はASCIIを含むバイナリフレームであり、既存QR受信器が扱う35文字＋LFの文字列へ変更が必要。メーカー公式デモはHIDからASCIIへの変換を持つが、出力先はUSB CDC。どちらもL-46Xでの動作保証ではない。

## 確認できた実装

| 候補 | 受信と変換 | 出力 | NF55Gへの適用 |
|---|---|---|---|
| THLN33 RP2350-USB-A / host_hid_to_fpga | TinyUSBとPico-PIO-USB。キーボードHIDから文字へ変換 | UART0、115200bps、GP0 TX / GP1 RX。ASCIIを含む13byteフレーム | UART送信の参考。文字列出力と配列変更が必要 |
| Waveshare公式 / host_hid_to_device_cdc | TinyUSBとPico-PIO-USB。Shiftと前回キーとの差分を使ってASCII化 | USB CDC。EnterはCRLF出力 | 比較的単純な土台。UART出力を追加する案 |

公開元:

- [THLN33リポジトリ](https://github.com/THLN33/RP2350-USB-A)
- [Waveshare公式Wiki](https://www.waveshare.com/wiki/RP2350-USB-A)
- [公式デモZIP](https://files.waveshare.com/wiki/RP2350-USB-A/RP2350-USB-A.zip)

## ソース確認で分かった条件

THLN33の固定コミットは735aef9c6bfd286ca0ca6bdccabfdebc72610bbb。主要ファイルはexamples/host_hid_to_fpga/host_hid_to_fpga.c。

- process_kbd_reportが新規キーをASCII化し、send_key_frame_to_fpgaがUARTへ送る。接続・切断も別フレームで送るため、UART出力をそのまま既存QR原文として受け取れない。
- _AZERTY_が有効で、フランス語配列に変換する。リーダのUS/JIS等の設定と一致させる必要がある。
- 複数の新規キーが同じレポートにある場合、UARTフレームのASCII欄には最後の文字だけが入る。QR用途では各文字を漏れなく扱う変更と検証が必要。
- UARTは同期的なuart_putcを使う。量産用には送信待ちによるUSB処理への影響を評価する。

両サンプルはKeyboardのinterface protocolを使い、受信をhid_keyboard_report_tとして扱う。レポート長を使用せず、キーコードを128要素の変換表へ直接参照する。採用時には長さ・範囲・rollover異常の検証、切断時の前回キー状態の破棄を追加する。任意のHID descriptorやReport IDへの一般対応とは扱わない。

## 基板に関する実装者の報告

THLN33 READMEはR13除去とD+/D-それぞれへの15kΩプルダウン追加を前提とする。元の実験記事はR13による接続検出への影響を報告し、後続記事はプルダウン追加による切断検出の改善を報告している。

- [接続検出の実験報告](https://qsantos.fr/2025/11/21/fixing-the-rp2350-usb-a-not-working-as-usb-host/)
- [切断検出の実験報告](https://qsantos.fr/2026/01/01/the-rp2350-usb-a-cannot-see-devices-disconnect/)

これは実装者の基板での報告。今回手配する基板の版、R13実装、D+/D-抵抗、VBUS給電回路との一致は未確認。現物に改造が必要と確定せず、回路図と実装部品・電圧を照合する。

メーカーWikiにはTinyUSBのhcd_pio_usb.cのreturn行をコメントアウトする手順が記載されている。SDK/ライブラリ版に依存する回避策として扱い、戻り値のある関数からreturnを除去する変更をそのまま量産実装へ適用しない。整合する依存版とビルド結果を確認する。

## NF55G向けの開発案

公式デモを土台に、検証済みの各ASCII文字とLFだけを専用UARTへ送る案を優先する。THLN33はUART・接続状態処理の参考にする。これは調査に基づく提案で、実装完了ではない。

1. 依存するPico SDK、TinyUSB、Pico-PIO-USBの版を固定し、RP2350-USB-A向けにビルドする。
2. リーダ設定と文字配列を一致させ、英数字・ハイフン・先頭ゼロ・Enterを確認する。診断メッセージをQR用UARTに混在させない。
3. UART速度と8N1を両側で合わせる。既存Pico 2のGP9/PIO受信は9600bpsの実績があるため、初回比較の候補とする。THLN33の115200bpsを無条件に採用しない。
4. RP2350側TXからPico 2側GP9 RXへ3.3V信号を渡し、GNDを共通化する。両基板の電源・逆給電・リーダ電流を確認して配線を確定する。Pico 2のUART0とUART1はATE/NF55G用として維持する。
5. 既存QR_SCAN受付後、35文字＋LF受信、6項目分割、一時Cache、REPL表示を確認する。
6. 同一QR反復、連続100回、接続済み起動、起動後接続、抜き差し、途中切断、電源再投入を分けて評価する。

QR受信のみでSS送信や製品PASS/FAIL判定を行わない。正式Cache・SS連携・CSV命名はOI-14/OI-23の確定待ちを維持する。

## 保存資料と確認範囲

reference/RP2350_USB_A_research_20261014/へ保存した。

- Waveshare_RP2350-USB-A.zipおよびWaveshare/展開物。ZIP SHA-256: E709329B4EC4735BA1895578EDAC8FD0FBA1F575656DF213B55E6997FDA1DEC5。
- THLN33/にREADME、LICENSE、主要ソース・CMake等8ファイルを固定コミットから保存。THLN33_manifest.jsonにURLとSHA-256を記録。リポジトリ全体・依存ライブラリの取得ではない。
- 原典コピーは変更していない。ソース読解と出力経路の比較まで完了。ビルド、UF2書込み、L-46X実機試験は今回未実施。

## 未確認事項

今回基板の回路・版と改造要否、L-46Xの実レポート形式と配列設定、依存版の整合、UART速度、電源容量、起動・再接続の安定性、量産Timingへの影響。既存旧ホストのQR受信成功をRP2350-USB-Aでの成功と扱わない。
