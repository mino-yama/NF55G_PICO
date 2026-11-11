# USB SubMCU Host実機前準備（2026-11-11）

[仕様・準備手順](Preparation_Rev0.md)／[検証結果](Result.md)／[実機記録票（未実施）](Hardware_Record_Template_Rev0.md)。QR単体の記述子／HID原文収集が対象。部品改造・書込み・実機通信は実施していない。2 Hostと正式治具UARTは未確定。

## SH-U05A所持済み・配線設定手順（2026-11-11）

最新手順は[SH-U05A配線・設定・ログ受信Rev.1](SH_U05A_Debug_Setup_Rev1.md)。メーカー端子写真、単体UARTモード・COM確認、追加基板との2線配線、給電順序、ログ保存・解析、終了・切り分け、記録欄を統合。Rev.0は履歴として保持。現行RAM版はUART無効、実機前の改造・UART版FW準備は未実施。

## SH-U05A単体確認（2026-11-11）

[単体確認結果](SH_U05A_Single_Check_20261111/Result_Rev0.md): COM22／WCH3.9.2024.9／ProblemCode0、115200・8N1・フローなしで無送信open/read/close成功、COM解放済み。UART LED非点灯はユーザー申告として記録、ループバック・追加基板接続は未実施。取得したドライバEXEは未実行。

### UART LED点灯の追加確認（2026-11-11）

ユーザーからUART LED点灯との回答。[単体結果Rev.1](SH_U05A_Single_Check_20261111/Result_Rev1.md)へ反映。前回のCOM22正常認識・115200／8N1開閉成功と合わせ、単体設定・COM確認の範囲は完了。送受信・追加基板接続は未実施。Rev.0とJSON証跡は保持。

## SH-U05Aループバック（2026-11-11）

[単体ループバック結果](SH_U05A_Loopback_20261111/Result_Rev0.md): COM22、115200／8N1、112件・送受信各5113byte完全一致、余分な受信なし、COM閉。次はUSBを抜いてTXD–RXD短絡だけを外し、UARTモードは維持。追加基板配線はUART版FW・改造準備後。

## 工程② UART版FW（2026-11-11）

[qr-uart-20261111.1のUF2・検証結果](UART_FW_20261111/Result_Rev0.md)／[UART診断仕様](UART_FW_20261111/Specification_Rev0.md)。GP0／115200・8N1送信専用。ビルド・301件回帰成功、実機未配置。次はSH-U05Aの短絡除去・改造・給電確認の工程③。
