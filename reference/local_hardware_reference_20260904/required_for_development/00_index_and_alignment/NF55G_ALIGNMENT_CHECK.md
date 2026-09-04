# NF55G整合確認メモ

作成日: 2026-09-04

## 確認に使ったローカル資料

- `01_NF55G_saved_context/US76HG_RS232C_2ch_reference_20260423.py`
- `01_NF55G_saved_context/RB01G_2ch_RS232_reference_20240527.py`
- `01_NF55G_saved_context/NF55G_試験治具仕様書_添付資料_CN24通信ハーネス結線表.docx`
- 前回ChatGPT会話の要約: RTCはWaveshare Pico-RTC-DS3231、SDカードはAdafruit ADA-5703 PiCowbell Data Loggerを想定

注記: `NF55G_試験治具仕様書_Rev0` 本体は、この作業時点でアクセス可能なローカルフォルダからは検出できませんでした。したがって、本メモは上記の関連RS-232C使用例、添付資料、前回会話要約に基づく確認です。

## 採用・保全対象の確定

| 機能 | 保全対象 | 根拠 |
|---|---|---|
| RTC | Waveshare Pico-RTC-DS3231 / DS3231 | 前回会話要約、公式Wiki、公式回路図 |
| SDカード | Adafruit ADA-5703 PiCowbell Adalogger for Pico | 前回会話要約、Adafruit公式Learning Guide/Product Page |
| RS-232C 2ch | Waveshare Pico-2CH-RS232 / SP3232EEN | 関連RS-232C使用例、Waveshare公式Wiki、公式回路図 |

## 現行NF55G Pico 2治具の主要ピン

本プロジェクトの `README.md`、`docs/Implementation_Plan.md`、実機ログより:

| 信号 | Pico GPIO | 用途 |
|---|---:|---|
| ATE UART0 TX/RX | GP0 / GP1 | ATE側ASCII transport |
| NF55G UART1 TX/RX | GP4 / GP5 | NF55G側RS-232C、38400 bps、8E1 |
| microSD SPI | GP16/GP17/GP18/GP19 | MISO/CS/SCK/MOSI |
| DS3231 I2C0 | GP20 / GP21 | SDA/SCL、address `0x68` |

## RS-232C 2ch整合

Waveshare Pico-2CH-RS232公式Wiki/回路図、および保存済みコードより:

| RS-232Cチャンネル | Pico UART | Pico GPIO | NF55Gでの扱い |
|---|---|---|---|
| CH0 | UART0 | TX=GP0 / RX=GP1 | ATE側ASCII transportで使用 |
| CH1 | UART1 | TX=GP4 / RX=GP5 | NF55G側RS-232Cで使用 |

現行NF55G Pico 2治具との整合は良好です。

## RTC整合

Waveshare Pico-RTC-DS3231公式回路図より:

- DS3231 I2Cアドレス: `0x68`
- 電源: `+3.3V`
- INT/SQWは標準では未使用。0R抵抗実装で `GP3`、`3V3_EN`、`RUN` への接続選択が可能
- I2C接続は基板上のジャンパ/ヘッダ設定に依存するため、最終実装時は実機の半田ジャンパ状態を確認すること

NF55G方針:

- DS3231を基準RTCとして使う
- RTC初期化ではI2C応答だけでなく、DS3231のOSFを確認する
- OSFが立っている場合は、ATE/PCから時刻再設定する運用を用意する

## SDカード整合

Adafruit ADA-5703公式Learning Guide/Product Pageより:

| 機能 | Pico GPIO |
|---|---:|
| microSD MISO | GP16 |
| microSD CS | GP17 |
| microSD SCK | GP18 |
| microSD MOSI | GP19 |
| Card Detect optional jumper | GP15 |
| PiCowbell I2C SDA | GP4 |
| PiCowbell I2C SCL | GP5 |
| PCF8523 RTC address | `0x68` |

重要な注意点:

| 競合 | 現行NF55G Pico 2治具 | ADA-5703 |
|---|---|---|
| GP4/GP5 | NF55G RS-232C CH1 | ADA-5703 I2C / STEMMA QT / PCF8523 |
| I2Cアドレス `0x68` | DS3231 | ADA-5703 PCF8523 |

結論:

- 現行NF55G Pico 2治具では、GP16-GP19をADA-5703 microSD専用として使う方針です。
- ADA-5703のGP4/GP5 I2C系はNF55G UART1と衝突するため、2026-09-04実機テストでは物理切り離し済みです。
- DS3231とPCF8523はどちらも `0x68` なので、同一I2Cバスで同時に有効化しないこと。NF55GではPCF8523を未使用扱いにし、DS3231を基準RTCとする方針が妥当です。

## 実装時の推奨整理

1. RS-232C CH0は現行どおり `GP0/GP1` のまま固定。
2. CH1は `GP4/GP5` を使うが、ADA-5703のI2Cと競合するため物理切り離しを前提にする。
3. RTCはDS3231のみを有効化し、PCF8523は未使用扱いにする。
4. SDカードはADA-5703のGP16-GP19を使用する。
5. 最終治具ではGP4/GP5切り離し方法と検査記録を残す。
