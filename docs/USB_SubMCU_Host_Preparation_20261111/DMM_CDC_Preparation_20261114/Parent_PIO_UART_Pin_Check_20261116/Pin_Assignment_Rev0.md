# 親Pico 2の追加PIO UARTのGPIO空き確認と割付案

2026-11-16 JST。同一USB Host案件。親Pico 2にQR用・7355用の独立双方向PIO UARTを追加するため、現行ソース、Rev.4配線図、周辺基板原典を照合した。**QRはGP8 TX/GP9 RXを維持し、7355用はGP12 TX/GP13 RXを第一候補とする。確認したソース・基板資料の範囲で、この4本と既存ATE/NF55G/SD/RTCとの機能競合はない。**

GP8/GP9は旧QR試作の予約ピンであり、新規未使用ではない。GP12/GP13は親の現行処理では未使用、SD基板にも機能接続がない。実機の追加ジャンパやハーネスは操作・導通測定していないため、物理的な未接続・取り出し位置まで確認済みとはしない。今回の結果は割付案で、配線・FW定数・原典図面は変更していない。

## 追加リンクの割付案

方向は全て親Picoから見た方向。物理pinは親Pico 2の40pinヘッダー基準で、Host基板側の端子番号ではない。

|論理名|用途|親GPIO|親の物理pin|接続先の案|確認状態|
|---|---|---|---|---|---|
|PIO UART2 TX|QRへの要求|GP8|11|QR HostのGP1/UART RX候補|旧QR TX idle High予約を双方向TXへ置換する案|
|PIO UART2 RX|QRからの応答|GP9|12|QR HostのGP0/UART TX候補|旧QR受信ピンを維持|
|QR GND|信号基準|GND|13候補|QR Host GND|取り出し位置は現物照合|
|PIO UART3 TX|7355への要求|GP12|16|DMM HostのGP1/UART RX候補|親ソース未使用、周辺基板機能と競合なし|
|PIO UART3 RX|7355からの応答|GP13|17|DMM HostのGP0/UART TX候補|親ソース未使用、周辺基板機能と競合なし|
|DMM GND|信号基準|GND|18候補|DMM Host GND|取り出し位置は現物照合|

各HostのGP0 TX/GP1 RXもまだ正式割付ではない。QR診断FWはGP0 TXのみ実装済み、GP1 RXの要求受付は今後の開発である。両Hostで同じGPIO番号を使用しても別MCUなので競合しない。**親のGP12/GP13をPIO UARTへ使うことと、Host基板のGP12/GP13をUSB D+/D−へ使うことは別の回路**である。親GP12/13をUSB D線へ直結しない。

いずれも3.3VロジックUARTで、親TX→Host RX、Host TX→親RX、GND共通。既存のRS232端子や5Vを追加UART信号へ接続しない。親UART0/UART1の別ピン機能へ割り当てず、PIOで駆動する。

## 既存使用と避けるピン

|GPIO|既存の用途・状態|今回の扱い|
|---|---|---|
|GP0/GP1|ATE UART0 TX/RX、57600/8N1|維持|
|GP4/GP5|NF55G UART1 TX/RX、38400/8E1。SD基板内RTC/STEMMAの同ピンは分離条件あり|維持、追加リンクに使わない|
|GP16/17/18/19|SD SPI0 MISO/CS/SCK/MOSI|維持|
|GP20/GP21|DS3231 I2C0 SDA/SCL、100kHz|維持|
|GP8/GP9|旧QR RX試作、GP8 High固定/GP9受信。Rev.4も追加Host候補|QRに継承。旧試作を新PIO TXと同時起動しない|
|GP10|旧EasyUSBHost TX0診断、PIO0/SM1・230400bps、単独scriptのみ|将来の保守診断と混同しないため今回選択しない|
|GP6/GP7|親の通常ソースでは未使用だが、DS3231基板のI2C選択ヘッダーで利用可能|現行GP20/21を維持し、追加UART候補から避ける|
|GP3|DS3231のINTに0Ω/NCで接続し得る|未使用と単純断定せず避ける|
|GP15|SD card-detectの任意ジャンパあり|追加UART候補にしない|
|GP12/GP13|通常ソース・診断scriptでピン初期化なし。RS232/RTC回路はヘッダー引出しのみ、SD基板のIO12/13はCB1接点のみ|7355用の第一候補|
|GP2/GP11/GP14/GP22/GP26～28等|今回のソースで通常処理の占有は見つからない|予備候補。全基板・実配線の自由使用を保証する一覧ではない|

Quad ExpanderはGPIO数を増やすI/O ICではなく、同じPico GPIOを各スロットで共有する拡張基板。空いたスロットに挿すだけで別のGPIOになるとは扱わない。

## PIO資源の確認と予約案

親`src/`と`scripts/`内のPIO初期化を検索し、該当は`src/qr_pio_rx.py`を呼ぶ次の単独試作に限定された。

- `scripts/pico_qr_receive_test.py`: GP9 RX/GP8 High、PIO0/SM0、9600bps。
- `scripts/pico_usb_host_debug.py`: GP10 RX、PIO0/SM1、230400bps。
- `src/main.py`の通常起動にはこの物理PIO receiverを生成する経路がなく、QRReceiverはGPIO非依存の状態処理である。SDはmachine.SPI、RTCはmachine.I2Cを使用しており、今回見たアプリケーションのPIO SMを消費しない。

RP2350は3 PIO block×各4 SMを持つ。旧PIO0試作と分離するため、追加2 UARTは**PIO1の4 SMを使う案**とする。

|用途|PIO block内SM|MicroPython StateMachine ID候補|
|---|---|---|
|UART2/QR TX|PIO1 SM0|4|
|UART2/QR RX|PIO1 SM1|5|
|UART3/DMM TX|PIO1 SM2|6|
|UART3/DMM RX|PIO1 SM3|7|

TX/RX別構成で計4 SMを予約する案。両経路でRXプログラムとTXプログラムをそれぞれ共有すれば、SMごとに同じ命令を重複配置する必要はない。ただし実装するプログラムがPIO1の命令メモリ32語に収まること、FIFO/IRQ、受信リング・RAM Queue、同時受信負荷を実装時に検証する。今回PIOプログラムを作成・loadしておらず、配置成功や量産Timing成立を報告しない。

ハードUART名と混同しないよう、UART2/3は説明用論理名。MicroPythonのmachine.UART(2)/(3)を使用する意味ではない。baudrateと正式なクラス/APIは未確定。

公式根拠: [RP2350のPIO構成](https://www.raspberrypi.com/documentation/microcontrollers/microcontroller-chips.html)、[MicroPython PIO仕様](https://docs.micropython.org/en/latest/rp2/tutorial/pio.html)。利用中FW上でのSM生成・命令load・同時通信確認は今後実施する。

## 照合した原典と証跡

- `src/ate_uart.py`、`src/nf55_uart.py`、`src/rtc_driver.py`、`src/sd_sink.py`、`src/main.py`、`src/qr_pio_rx.py`、`scripts/pico_qr_receive_test.py`、`scripts/pico_usb_host_debug.py`。位置とhashは[確認記録](Pin_Check_Evidence.json)。
- [Rev.4 GPIO表](../../../drawings/NF55G_Fixture_20261111_Rev4/sheet2_text.txt)。QR/7355を1 Hostに集約する記述とATE115200は過去時点の図面で、現構成は2 Host・ATE57600。GPIOの既存接続位置を照合する資料として使用し、原図は変更しない。
- 保存済みメーカーRS232回路図を描画して[画像確認](RS232_Schematic.png)。GP0/1/4/5以外の候補に機能接続なし。
- 保存済みメーカーRTC回路図を描画して[画像確認](RTC_Schematic.png)。GP6/7の選択接続・GP3 INT選択を確認。現行のGP20/21を変更しない。
- Adafruit PiCowbell Adaloggerの保存済みEAGLE `.brd`をXMLで解析。IO8/9はCB1/JP3への引出し、IO12/13はCB1のみ。GP15任意card-detect等は別扱いとした。ネット証跡は上記JSON。
- [過去の基板整合確認](../../../Hardware_Reference_Alignment_Check_20260904.md)のSD/RTC/UART条件とも照合。

## 結果と次の確認

ソース・原典で競合のない割付案は作成できた。今回の実機に追加ジャンパ・旧診断線・周辺回路が残っていないこと、Expanderの接触・GPIO取出し位置を無給電で照合し、その後にPIO単体→2系統同時→ATE/NF55G併用試験へ進む。現物の未接続までソフト検索だけで断定しない。

今回は調査記録と関連仕様注記のみ。ソース・ピン設定・FW・実配線は変更せず、Host Unit/Mock NF55G・実機操作は行わない。資料リンク、ピン重複、原典ネット、ソースhashを確認。USB-SUB-05はPIO/受信負荷/正式リンクの残課題を含むためOpenを維持する。
