# 親Pico GPIO 配線基準 Rev.0

2026-11-20。ユーザーのGPIO早期確定/基板配線並行作業に対応し、既存GPIOを維持する配線基準を整理した。確認したソース/既存原典表で競合なし。ここで固定するのは親の信号割当で、QR双方向FW完成やExpander CN導通検査完了を意味しない。

## 親UARTとHost間の信号割当

方向は全て親Pico基準。物理pinは親Pico 2の40pinヘッダー番号で、Host基板側番号ではない。

|用途|親GPIO|親物理pin|方向/接続先|状態|
|---|---|---|---|---|
|ATE TX|GP0|1|親→既存RS232 CH0→ATE|現行維持、57600 8N1|
|ATE RX|GP1|2|ATE→既存RS232 CH0→親|現行維持|
|NF55G TX|GP4|6|親→既存RS232 CH1→NF55G|現行維持、38400 8E1|
|NF55G RX|GP5|7|NF55G→既存RS232 CH1→親|現行維持|
|QR Host TX|GP8|11|親→QR用RP2350-USB-CのGP1/RX|既存予約を配線基準として維持|
|QR Host RX|GP9|12|QR用RP2350-USB-CのGP0/TX→親|既存受信割当を維持|
|測定器Host TX|GP12|16|親→測定器用RP2350-USB-AのGP1/RX|実装/実機確認済み、115200 8N1|
|測定器Host RX|GP13|17|測定器用RP2350-USB-AのGP0/TX→親|実装/実機確認済み|

QR/測定器の配線用に親GP8/9とGP12/13を確保し、この4本を他用途へ転用しない。QR側は現在診断FWのGP0 TXと旧受信試作GP9が根拠で、GP1 RXの正式要求受付と親GP8の双方向送信は後続ソフト開発。信号線は両方向を配線しておけばその実装で変更不要。QRの速度/フレーム/統合受入を現行診断値から推測して完成扱いしない。

各HostのGNDと親GNDを共通化。親側の近接GNDはQRで物理13、測定器で物理18を使えるが、Expander/CNから取り出す位置は現物ラベル/導通で対応を確認する。UART信号は3.3V TTL。親GP12/13をHostのGP12/13へつながない（測定器Host側GP12/13はUSB-A D+/D−）。ATE/NF55Gは既存RS232変換経路を使用する。

## SD/RTCなどの既存割当

|用途|親GPIO|親物理pin|
|---|---|---|
|SD MISO|GP16|21|
|SD CS|GP17|22|
|SD SCK|GP18|24|
|SD MOSI|GP19|25|
|RTC SDA|GP20|26|
|RTC SCL|GP21|27|

GP4/5のSD基板RTC回路との分離条件は継続。GP3（RTC INT候補）、GP6/7（RTC選択回路）、GP15（SD検出任意配線）、GP10（旧診断）を追加Host用に転用しない。Quad Expanderの各スロットは同じGPIOを共有する。

## PIOの現行と予約

現在の測定器中継はPIO1のMicroPython SM4 TX/SM5 RXを使用済み。旧2026-11-16案のQR=SM4/5・測定器=SM6/7という順序を現行確定値として使わない。QR双方向の候補は残るSM6/7で、GPIOはGP8/9のまま。2経路のPIOプログラム共有/命令領域/IRQ/負荷は今後実装・検証する。SM番号の検討は基板信号割当を変更する理由にしない。旧QR単独PIO0試作の同時起動/GP8固定出力と双方向ドライバの競合を避ける。

## RESETは信号割当と分けて保留

ユーザーは「電源リセットではなく強制リセットが必要ということか」と確認。現時点で必須/親から個別制御という設計回答は確定していない。Host RUN等をアサートするMCUリセットは電源遮断と別で、測定器出力や遅着まで清浄にする保証ではない。

配線余地を失わないよう、GP14（物理19）をQR RESET候補、GP22（物理29）を測定器RESET候補として空けておく。現行ソース/今回の既存割当に競合は見つからないが、RESET接続承認や実物の空き確認ではない。現段階は親側予備パッド/中継位置の確保まで。Host RUN取出し位置・極性・回路/電源条件・独立制御の要否を確認してから結線する。GPIOとHost RUNを未確認で直結せず、回路図で駆動方式を確定する。今はRESET GPIO初期化/FW追加を行わない。

## 配線作業の範囲

先行できるのはGP8/9のQR信号、GP12/13の測定器信号、共通GNDの配線設計/基板上ルート確保。施工時は外部/PC給電を切った状態で信号端子と導通を照合する。CN番号/Host物理pin/RESETの接続先をこの表から推測しない。外部5VとHost PC USB-Cの同時給電禁止条件は維持する。

測定値Cache/ATE応答/AD追加は既存通信線上の処理なので、その機能だけで親GPIOの追加は不要。

根拠: src/ate_uart.py、src/nf55_uart.py、src/qr_pio_rx.py、src/external_instrument_pio.py、src/sd_sink.py、src/rtc_driver.py、2026-11-16親PIO pin check、Rev4 GPIO表、USB_HOST_Interconnect_Spec。

[照合/hash](Verification_Rev0.json)。今回は配線基準整理のみ、コード/Flash/実配線変更なし。既存Issueは全体としてOpen維持。
