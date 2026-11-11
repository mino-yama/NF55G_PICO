# USB Host SubMCU 開発準備資料

収集日: 2026-11-10
対象構成: Waveshare RP2350-USB-C、Sanwa Supply BCR-TC2D1BK、ADCMT 7355

このフォルダには開発準備に必要な公開ハードウェア原典を保存する。原典PDF／図面は編集していない。ダウンロード元とSHA-256を記録した。資料入手は、実機の基板版・設定・接続・動作を確認したことを意味しない。

## 回路図名称による固定割当て

| 回路図コネクタ名 | 回路経路 | 固定接続先 |
|---|---|---|
| `Type_C1` | RP2350ネイティブUSB D+/D-。CC1/CC2各5.1kΩはVSYS側 | ADCMT 7355 |
| `Type_C2` | PIO-USB。`DB_P`／`DB_N`、R11/R12経由GPIO13/GPIO12 | BCR-TC2D1BK |

この物理ポート割当てを変更しない。USBハブは標準構成に含めない。Type_C1/Type_C2のHost同時動作、Type_C2の実装抵抗・CC/VBUS設定、実機給電は初回受入で検証する。手順は[RP2350-USB-C初回受入チェックリスト](../../docs/RP2350_USB_C_First_Acceptance_20261110.md)。

## 今回取得した資料

| 資料 | ローカルファイル | 取得元 | Bytes | SHA-256 |
|---|---|---|---:|---|
| RP2350-USB-C 回路図 | [RP2350-USB-C_schematic.pdf](RP2350-USB-C_schematic.pdf) | [Waveshare GitHub](https://raw.githubusercontent.com/waveshareteam/RP2350-USB-C/main/hardware/schematics/RP2350-USB-C.pdf) | 74382 | `35F3FD0960F1AF50C592DA0BEFCB716E2B6C5CFEA4FC41F7F7CEB4C27577453D` |
| RP2350-USB-C ピン配置図 | [RP2350-USB-C_pinout.webp](RP2350-USB-C_pinout.webp) | [Waveshare公式資料](https://docs.waveshare.com/assets/files/RP2350-USB-C-details-intro-126ee744b46f6dfbd10b4e5cc83ff3eb.webp) | 3363 | `2E35892BAB72692E06C6C53213BFAC2E58F33718EC807BC539329B6558596105` |
| RP2350 データシート | [RP2350_datasheet.pdf](RP2350_datasheet.pdf) | [Waveshare公式Resources](https://files.waveshare.com/wiki/common/Rp2350-datasheet.pdf) | 7767386 | `1862ADE90D7BF51D5764CD58655023591F22E4D4A707467C5E0991C7D58C9FE7` |
| RP2350 ハードウェア設計リファレンス | [RP2350_hardware_design_reference.pdf](RP2350_hardware_design_reference.pdf) | [Waveshare公式Resources](https://files.waveshare.com/wiki/common/Hardware-design-with-rp2350.pdf) | 4395048 | `6C85405DE48D02C0486AD5E10FFD1434AEE948F6CDCD3E78AF9EAB3070BD4E96` |
| BCR-TC2D1BK 取扱説明書 Ver.1.0 | [BCR-TC2D1BK_manual_ver1-0.pdf](BCR-TC2D1BK_manual_ver1-0.pdf) | [Sanwa Supply公式PDF](https://cdn.sanwa.co.jp/support/setsumeisyo/pdf/B/BCR-TC2D1BK_ver1-0.pdf) | 320559 | `FA5304ED97EB8AA31E05376BFBDC77F31EE1306BA34CE263D37DCF1B2C347DB2` |

## 既存資料

- ADCMT 7355の日本語・英語取扱説明書、製品カタログ、サンプル一式: [ADCMT_7355_20261104](../ADCMT_7355_20261104/)。受領時にコピー元とのSHA-256一致を記録した[manifest](../ADCMT_7355_20261104/manifest.json)がある。マニュアル本文の確認範囲は[変更要求・調査記録](../../docs/CH9350_QR_DMM_Plan_20261109.md)と[外部測定要求](../../docs/Calibration_External_Measurement_Requirements_20261104.md)を参照。
- 製品銘板図: [NF55802-G_01.pdf](../local_hardware_reference_20260904/required_for_development/NF55802-G_01.pdf)。銘板図のQR枠は読み取り試験用の実QRではない。
- BCR-TC2D1BKの商品画面画像: [BCR_TC2D1BK_20261109](../BCR_TC2D1BK_20261109/)。
- 基板のポート用途・特徴: [Waveshare RP2350-USB-C公式説明](https://docs.waveshare.com/RP2350-USB-C)、回路図等の一覧: [公式Resources](https://docs.waveshare.com/RP2350-USB-C/Resources-And-Documents)。
- USBホスト実装の参照: [Waveshare RP2350-USB-C Examples](https://github.com/waveshareteam/RP2350-USB-C)、[TinyUSB](https://docs.tinyusb.org/en/latest/)、[Pico-PIO-USB](https://github.com/sekigon-gonnoc/Pico-PIO-USB)。依存版は実装前に固定する。

## 資料確認後も残る実機確認

- RP2350-USB-C実機の型番・基板版と回路図の一致、ポート用途、CC／VBUSの実装、給電容量・保護、GPIO引出し。
- BCR-TC2D1BK実機の設定・suffix・HID記述子／レポート、使用する実ラベルまたは試験用QRでの35文字完全一致。
- ADCMT 7355の実機FW、USB BUS設定、CDC／USBTMCの実際の列挙、コマンド体系、測定手順・応答。
- USBハブは型番・接続構成未選定のため、適合する取扱説明書・仕様書は未収集。Type-Cポートが下流データ用であることと給電条件を選定後に確認する。
- 電源・ケーブルの型番、実測電圧／電流、逆給電・突入電流、シャント抵抗値・校正情報は実機・ATE側資料待ち。

次の開発手順と段階試験は[USB Host SubMCU Integration Plan](../../docs/USB_Host_SubMCU_Integration_Plan_20261110.md)に従う。回路図は現物照合の資料であり、未確認の基板改造を許可するものではない。

## 2026-11-11 原典照合の訂正

上表のType_C1 CC各5.1kΩはVSYS側ではなく、原典回路図ではR5／R6を介してGNDへ接続される。Type_C2の正確なD線対応はGPIO12=D+／R12、GPIO13=D−／R11。PDF原典は未変更。[Host条件と照合根拠](../../docs/USB_Host_SubMCU_Host_Circuit_Conditions_Rev0_20261111.md)／[今回の一次資料台帳](../USB_Host_SubMCU_Host_Conditions_20261111/manifest.json)参照。
