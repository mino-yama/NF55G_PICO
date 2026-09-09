# NF55G Pico 2 試験治具

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.0  
Date: 2026-09-01

## 概要
Raspberry Pi Pico 2 を使用し、ATE と NF55G の間を仲介する量産試験治具である。

### 主な役割
- ATE から ASCII Command を受信
- NF55G 通信 Frame の生成・送受信
- ACK / NAK / BCC / Retry / Timeout 管理
- D0/D1/D5/BC/AR/EL/OL 等の Decode
- 明示 Refresh + Cache
- DS3231 RTC
- microSD Logger
- Diagnostic / Self Check
- 将来 USB CDC / Windows PySide6 保守コンソール対応

### 責任分離
- Pico: 通信、Decode、Cache、Logger、RTC、Diagnostic
- ATE: 試験シーケンス、外部計測器制御、最終 PASS/FAIL
- NF55G: 製品動作

## Hardware baseline
- MCU: Raspberry Pi Pico 2
- Base: Waveshare Pico-Quad-Expander
- RS232: Waveshare Pico-2CH-RS232
  - ATE: GP0/GP1
  - NF55G: GP4/GP5
- RTC: Waveshare Pico-RTC-DS3231
  - I2C0 GP20/GP21
  - 0x68
  - 100 kHz
- Logger: Adafruit ADA-5703 PiCowbell Data Logger
- microSD: 32GB, FAT32
- Power: 5V external power, Pico 常時動作
- NF55G connector: CN24 HRS DF11-4DS-2C

## NF55G communication
- 38400 bps
- 8 data bits
- Even parity
- 1 stop bit
- Full duplex
- STX + CMD(2 ASCII) + DATA + ETX + BCC(2 ASCII HEX)
- BCC: CMD ID から ETX まで XOR、STX は除外
- Pico Command Retry: max 1
- Pico T1: 200 ms provisional
- D0 T2: 600 ms provisional

## Development order
Windows の環境導入手順と導入状況: [Development Environment](docs/Development_Environment.md)

1. Read all specifications and `AGENTS.md`
2. Review only; do not implement immediately
3. Build Host test environment
4. Implement models/config/BCC/frame/decode/cache
5. Implement Mock NF55G
6. Implement Protocol State Machine
7. Implement ATE parser/dispatcher
8. Implement NF55 command builder
9. Implement Logger/SD
10. Implement RTC
11. Add Pico hardware UART/I2C layer
12. HIL with real NF55G

## Directory
```text
NF55G_Pico/
├─ AGENTS.md
├─ README.md
├─ Codex_Master_Prompt.md
├─ docs/
├─ reference/
├─ src/
└─ tests/
```

## Important
Do not start by implementing control commands against real hardware.
First complete Host Unit Tests and Mock NF55G tests.
