# 固定配線を前提としたソフト・起動切り分け Rev.0

2026-11-28。ユーザーより「基板・コネクタ接続で従来どおり」と補足。以後、信号線の交換や写真を繰り返し要求せず、現接続を前提に調査する。診断RXの測定位置はソフトから直接確認できないため、受信0バイトだけで断線・HOST故障を断定しない。

## 確認できた事実

- [親の配置・現在設定](parent_config_check.json)：37ファイルのSHA-256がQR／SS試験後の確認済み配置と全件一致。測定器PIO送受信active、FIFO0、closed=False、fault=False。管理・校正の処理待ちはなし。対象HOST IDも既知個体と一致した。GPIO設定値は生データとして保存し、入力端子のFUNCSELがSIOであることをPIO受信故障と解釈しない。
- 試行停止・通信待機を確認して親Picoだけを通常再起動。親nonceは`9abb4c02ffe7af7c`から`f9776a620075c42a`へ更新。SD OK・drop0・IDLE、HOST情報照会は1,000 msでtimeout。[再起動後ATE記録](ate_after_parent_reset.json)。
- ユーザーが7355のUSBをHOST側から外し、HOSTをRST。情報照会は1,000 msでtimeout、診断COM23は0バイト。親IDLE・SD OK・drop0。[測定器USBなしの記録](ate_meter_usb_removed.json)。7355未接続でも情報応答が得られない観測であり、HOST内部のどこで止まるかは未確定。
- HOSTの全Flash退避と既知.25.2コード一致は先行結果のとおり。ここまで実機FW変更なし。

## 次の診断候補

`uart_diagnostic/source/`に、既存relay_host／relay_wireコアと同じUART0 GP0／GP1を使い、測定器USBを初期化しない単体候補を作成。native USB CDCへ起動時刻・個体ID・UART RX/TX数・拒否フレーム数・RX原文を出す。管理INFOには診断版名とNOT_READYを返す。診断用nonceは量産のランダム起動IDとは別であり、量産採用しない。測定器制御・校正書込みには使用しない。

ビルド成功・UF2ハッシュを確認してから、退避済み既知HOSTへ一時配置し、起動とUARTを分離観測する。終了時には退避した全Flashへ戻してverifyする。親のアプリは変更しない。R3校正取得・400セット耐久は復旧後に実施し、診断版での結果を耐久受入へ加算しない。

## UART単体診断の実施結果

候補をARMビルドし、既知HOSTへ一時配置・独立verifyして起動した。native USBはCOM25、個体ID `BFCF2EDB84B0B37F`、診断版名`meter-host-relay-uartdiag-20261128.1`。PC USBから稼働時刻121,904～127,904 msの継続を確認した。

この間に親からHOST_INFOを1件送信し、ATEはtimeout。HOST自身のカウンタは、観測開始から終了までrx=1、tx=0、emit=0、reject=0、GP1読値1で不変だった。従って、観測中の親の照会ではHOST UART受信数が増えず、応答フレームも生成されていない。初期rx=1の原因は未確認。外付け診断RXの測定位置に依存せず、HOST自身の観測でも受信増加なしを確認した。[native USB記録](uart_diagnostic/native_result.json)。

診断後、退避した全2 MiBへ復元し、独立verifyと版読戻しで`.25.2`を確認して通常起動した。[復元記録](uart_diagnostic/restore_retry/result.json)。最初の復元操作はBOOTSELへのUSB再列挙待ち不足でinfo照会が失敗したが、Flash書込み前に停止。再列挙後の個体確認から復元を再開し、成功した。診断版は実機に残していない。

確定できるのはHOST起動と、観測中のUART受信増加なしまで。コネクタ接触・信号経路・端子状態・入力回路等のどれが原因かは未確定。元の接続指定を変えず、全給電停止後の既存コネクタ再装着・通常構成復帰を依頼した。校正取得・400セットは未開始。
