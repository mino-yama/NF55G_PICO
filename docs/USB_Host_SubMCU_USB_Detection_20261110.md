# 追加RP2350-USB-C PC接続後の検出確認

日付: 2026-11-10
状態: ユーザーの接続完了連絡後、Windowsで対象基板を検出できず。BOOT操作待ち。

## 確認事実

- serial.tools.list_ports -v: no ports found、終了コード0。
- Get-PnpDevice -PresentOnlyでVID_2E8A、RP2350、RP2、Pico、USBSTOR等を照合: 該当表示なし、終了コード0。
- Get-Volume: C、Dと内部回復領域のみ。RP2350の書込みドライブは検出されなかった。
- 接続中USB機器を広げて確認: 内蔵カメラ、Bluetooth、USBハブ、ルートハブ、USB Type-C Digital AV Adapterを表示。対象基板を特定できる情報や不明なUSB機器の表示は得られなかった。
- 以上は今回の確認時点のWindows列挙結果。接続ミス・ケーブル不良・FW異常・基板故障のいずれとも原因確定しない。
- 機器への送信、FW書込み、基板設定変更は実施していない。

## 次の切り分け

Waveshare公式 https://docs.waveshare.com/RP2350-USB-C のOnboard Resourcesは、BOOTを押してresetするとdownload modeへ入ること、RUNがresetボタンであること、書込み用Type-CとPIO-USBを区別することを記載。

ユーザーへ書込み用Type_C1の接続を確認し、BOOTを押しながらRUNを押して離し、BOOTを離す操作を依頼した。Type_C2・7355・治具UARTは外したまま。操作完了連絡後にUSB機器／ドライブを再列挙する。検出しなければデータ対応ケーブル・PC接続先・物理ポート識別を順に確認する。

既存のCOM6はユーザー確認により治具Pico 2であり、追加基板のCOM番号として流用しない。既存Open IssueはCloseしない。追加基板の電源受入・USBホスト通信・UART試験は未実施。
