# NF55G Pico 2 試験治具

## ATEプログラム作成者向けコマンド一覧

最新版は2026-11-27の **Rev.5**: [Markdown版コマンド一覧](docs/ATE_Command_List_for_Test_Program_Rev5_20261127.md)。校正点をA/Bへ統一し、必須3回路×A/Bの書込み範囲保護を実装。[実装仕様・結果](docs/Calibration_AB_Implementation_20261127_Rev0.md)、[Picoルート配置用設定](calibration_limits.py)を参照。実機配置・実測校正は未実施。Word Rev.4および過去一覧は履歴として保持する。

2026-11-20 Codex直接送受信: ユーザー固定入力/COM7解放後、AUTO単発-2.91185V、続けてRANG20指定-2.9118V、RANG200指定-2.912V、AUTO-2.91186Vを取得。全機器エラー0、各READ一回/再送なし、最終AUTO ON/COM7解放済み。CONFは20指定で199.9999V、200指定で1099.999V、AUTO測定後19.99999Vを原文保持し、選択境界の理由は未解決でIssue Open維持。 [測定比較](docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Codex_Fixed_Range_Comparison_01/Result_Rev0.md)。

2026-11-20 .3実機で設定Query5種×12周（60件、機器応答総1035byte）と終了エラーQueryを成功。全周で原文/書式/長さ一致、CONFは正常なVOLT +1.999999E+01,+1.000000E-06、AUTO=1、エラー0。先行の応答崩れは今回再現せず、受信健全性を確認。固定20V切替/前面一致/測定は未実施でレンジIssue等はOpen維持。COM7解放済み。 [結果](docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/CONF_FIFO_Validation_01/Result_Rev0.md)。

2026-11-20 .2実機試行10で親経由7355識別中継成功。ATEへOK:EXT_RX:32:HEXを返しADC Corp.,7355,246410099,  A02+CRLFを原文保持。Host入力線にHとQ一件を正常捕捉、再送/レンジ/READなし。試行9の起動00byte付き照合成功と合わせ同期修正の効果を確認。全受入/Issue Closeとはせず切断復帰/実負荷等は残る。シリアルモニターCOM7/57600 8N1を解放済み。 [解決記録](docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/Resolution_Rev0.md)。

2026-11-20 外部測定器中継: 親ATE入口～Host実C engineのコード結合と全446件Host/Mock試験、独立中継UF2のARM buildが完了。実機配置・疎通は未実施。[実装と配置準備](docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Result_Rev0.md)。

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。 ただしD0のT2のみ、2026-11-11ユーザー指定により通信r2事前確認版p.17／28の300msを採用。r2の他項目は一括採用しない。
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
- Base board: Pico-Quad-Expander（2026-11-10ユーザー指定。RTC／SD／RS232C各基板を同基板経由で接続。従来記録の識別名はSeeedStudio 103030397 / GPIO EXPANDER QUAD RASPBERRY PI PICO。現物のメーカー・品番表記の照合は未実施）
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

## USB HOST Extension Handoff (2026-11-19)

Connection: `Pico 2 ⇔ Expander ⇔ interconnect board ⇔ Waveshare RP2350-USB-C USB HOST ×2`.
The USB HOST units are for the QR reader and DMM. The interconnect board uses Akizuki **117585** (Raspberry Pi Pico 20P pin sockets, 3.2 mm leads, left/right set) and **ADA-5200** (Switch Science 8588, PiCowbell Proto).
Connect Expander CN through the pin sockets to ADA-5200, then use soldered wiring to the two USB HOST units. A RESET signal is present on the interconnect board.

The interconnect board is a physical marker for clarifying USB HOST-to-Pico connection points and wiring, and an aid for hardware-design and debugging explanations. It will be used to document the Pico-side port connections for planned USB CDC development and the already-developed QR function. This does not change existing design policy, GPIO assignments, communication control, or firmware. Specific pin numbers and wiring locations are unconfirmed and must not be inferred. The earlier part number `C-17585` is incorrect; use `117585`.

See [USB HOST Interconnect Specification](docs/USB_HOST_Interconnect_Spec.md) for confirmed scope and unresolved details. The board documents physical connections only; it does not implement USB CDC or change its existing development status.

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
- D0 T2: 300 ms（2026-11-11ユーザー指定、r2事前確認版p.17／28を部分採用）

## Development order
Windows の環境導入手順と導入状況: [Development Environment](docs/Development_Environment.md)

実物NF55G接続前の準備・残実装・試験手順案: [NF55G HIL Preparation](docs/NF55G_HIL_Preparation.md)

Pico時計・EB・ATE受信・実SDの統合とHost検証: [Runtime Integration](docs/Runtime_Integration.md)

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

2026-11-04ユーザー指定の追加開発順序: **現在の実機確認 → QRコード読取り → 7355連携による外部測定値取得・補正機能追加**。
7355の通信仕様・アドレス設定の詳細化、取得値のATE返却、ATE判定後の別指令による数値付き補正書込みは、実機確認とQRコード読取りの後に進める。
詳細: [Implementation Plan](docs/Implementation_Plan.md)、[追加要求仕様](docs/Calibration_External_Measurement_Requirements_20261104.md)。

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

## 最新の治具接続・改造図（2026-11-11）

[治具図Rev.4：接続・GPIO・Type_C2改造箇所と手順、A4横5枚](docs/drawings/NF55G_Fixture_20261111_Rev4/README.md)。改造は実機確認の直前に案内し、現在は未施工。旧Rev.3以前とメーカー原典は保持。
