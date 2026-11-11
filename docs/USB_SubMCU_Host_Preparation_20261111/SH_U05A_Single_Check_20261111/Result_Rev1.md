# SH-U05A単体設定・COM確認 結果 Rev.1

日付: 2026-11-11／対象: ユーザー所持SH-U05A

更新: ユーザーから「UART LED点灯した」と回答。旧[Rev.0](Result_Rev0.md)とPC取得のJSON証跡は保持。今回PC再検出・COM再オープンは行っていない。

## 確認結果

**SH-U05AはCOM22として正常認識。115200bps／8N1・フロー制御なしで無送信の開閉確認に成功。前回確認終了後COMは閉じている。今回、ユーザーがUART LED点灯も確認。**

| 項目 | 結果・証跡 |
|---|---|
| 現物モード | ユーザーがUART側へジャンパ設定済みと回答 |
| LED | UART LED点灯をユーザーが確認（2026-11-11の追記）。以前の非点灯報告は経過として保持 |
| Windows表示 | USB-SERIAL CH341 (COM22) |
| Hardware ID | VID_1A86／PID_5523、REV_0304 |
| PnP状態 | OK／ProblemCode=0 |
| ドライバ | wch.cn／3.9.2024.9／oem218.inf／CH341SER_A64 |
| ポート設定 | 115200bps、8bit、parity N、stopbit 1、XON/XOFF・RTS/CTS・DSR/DTRフローすべて無効 |
| DTR／RTS | 開く前から両方False |
| 開閉確認 | pyserialでVID/PIDとCOM22を照合後open成功、1秒受信待ち、close成功 |
| データ | 送信0byte、受信0byte。ループバック等の入力を与えていないため、無受信だけで異常としない |

[最終PnP・ドライバ情報](Final_Device_Status.json)／[ポート設定と開閉結果](COM22_Open_Check.json)／[実行した無送信確認スクリプト](check_com22.py)。COM番号は今回の値であり、USBポート変更等で再列挙した際は照合する。設定は今回のポートopenで適用し、今後使う受信ソフトでも115200／8N1を指定する。

## 検出の経過とドライバ取得

1. 最初はUSB UART-LPT、VID1A86／PID5512、ProblemCode28、COMなし。[初期検出](Initial_Detection.json)。コード28はWindowsのドライバ未選択／未インストール状態として扱う。[Microsoftの説明](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/device-manager-problem-codes)。
2. ユーザーへ単体のUART設定を依頼。ユーザーがUART側へ設定・UART LED非点灯と回答。PC側ではPID5523への変化を観測したが、この段階ではCode28・COMなしだった。
3. メーカー製品ページのCH341-I2C-UART-driverリンクからZIPを取得・展開。EXEのAuthenticodeはWCH（Nanjing Qinheng Microelectronics）による有効な署名だった。
4. 再確認でCOM22・Status OKへ変化。導入操作の経路は未確認で、自動導入やユーザー操作と断定しない。こちらではインストーラ起動・ドライバ導入操作を行っていない。取得物は未実行のまま保持した。
5. VID/PIDとCOM22を再照合し、ポート設定・無送信のopen/read/closeを確認した。
6. その後ユーザーからUART LED点灯との回答を受領。LED点灯時期の詳細や点灯へ変化した原因は未確認。

[取得ドライバとhash](../../../reference/USB_Host_SubMCU_Host_Conditions_20261111/SH-U05A/Driver_20261111/Download_Manifest.json)。SPI/IIC用ドライバの追加、他の既存ドライバの更新・削除は行っていない。

## 実施範囲と次工程

確認できたのはUSB列挙、Windowsドライバ正常状態、COMポートの指定設定での開閉。UART端子の電圧実測、RXD–TXDループバック、追加基板からのデータ受信、負荷時・連続受信・信頼性は未実施。ユーザー確認のUART LED点灯と既得のCOM開閉成功をもって単体設定・COM確認の範囲を完了とする。LED点灯をUARTデータ転送・USB Host動作・製品合格の証拠へ昇格させない。

追加基板との配線は[設定・配線手順Rev.1](../SH_U05A_Debug_Setup_Rev1.md)に従い、実機直前の改造案内とUART出力版FWの準備後に行う。現在のRAM版と配置済みUSB診断FWはこの診断UARTを出さない。親Pico／追加基板のFW・配線、QR／7355、NF55G／ATEは今回操作していない。USB-SUB-01／02／03はOpen継続。

Host／Mockは再実行していない。今回の確認は実機アダプタの列挙・無送信ポート設定試験であり、製品ソフト変更はない。
