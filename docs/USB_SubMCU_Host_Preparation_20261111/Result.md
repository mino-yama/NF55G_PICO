# USB SubMCU Host実機前準備 結果 Rev.0

日付: 2026-11-11。**QR単体調査用のオフライン準備。基板改造・FW書込み・実機通信は未実施。**

## 作成物と検証

| 項目 | 結果 | 証跡 |
|---|---|---|
| QR単体PIO Host FW | SDK2.2.0／GCC14.3でコンパイル・リンク・UF2生成成功、終了0 | [最終ビルド](build_ram_verified.txt) |
| UF2識別 | RP2350 ARM Secure、qr-probe-20261111.1、SDK2.2.0、専用2MB基板設定 | [ファイルのみの解析](UF2_Info.txt) |
| 原典・依存 | 上流14ファイルのSHA照合、TinyUSB固定版原文と改行正規化後一致。派生変更はusb_rx.pioのみ | [依存検証](Dependency_Verification.json) |
| RAM ABI／初期化範囲 | g_probe=19476byte、PIO Hostとmalloc再帰ロックhookのシンボルあり、UART initシンボルなし | [ELFシンボル](ELF_Symbols.txt) |
| Host Unit／Mock回帰＋初期ログ検査 | 300件成功、16.072秒（既存287＋初期13） | [全件ログ](Host_Mock.txt) |
| 最終ログ検査 | 記述子長0拒否を追加後14件成功、0.003秒。欠落・破損・満杯・エラー非昇格を確認 | [最終14件](Probe_Log_Tests_Final.txt) |
| 任意診断TX候補 | GP0 TX分岐の構文検査終了0。UART版リンク／配布UF2／実機は未実施 | [構文検査](UART_Syntax_Check.txt)、[検査スクリプト](check_uart_compile.py) |

[配布フォルダ](../../firmware/usb_submcu_host_probe/releases/qr-probe-20261111.1-ram/)にRAM版UF2／ELF／bin、対象ソースと原文・派生コピー、ビルド／受信／解析スクリプト、[manifest](../../firmware/usb_submcu_host_probe/releases/qr-probe-20261111.1-ram/manifest.json)を保存。

UF2: 77312byte、SHA-256 **5cc267ff10eea15a6c3507a5a74cf317ec44517e7ff304873f3ef91369da8018**。全UF2ブロックの境界・magicを検査。今回はファイルを検査しただけでUSB実機へ接続していない。

「Fixed Pin Information none」はメタデータの値であり、GPIO不使用の証拠ではない。このFWは起動するとGP12／13・PIO・DMA・タイマーを使用するため、未改造基板へ今回書き込まない。

## 解消したビルド条件

メーカー原文ではSDK2.2.0のpio_sm_set_jmp_pinと重複してコンパイル失敗。原文をvendor/upstream-774cbb1へ保持し、派生コピーではSDK正式APIを使用するよう独自定義のみ除去した。[失敗ログ](build_ram_compat_failure.txt)。

既存Arduino GCC14.3のnewlibはmallocのretargetロック参照が未解決となった。[リンク失敗ログ](build_ram_newlib_failure.txt)。newlib公開hookの__malloc_lock／__malloc_unlockをSDK再帰mutexへ接続して解消。ロックを空実装にはせず、SDK／toolchain本体と既存FWは変更していない。詳細はvendor/SDK_2_2_0_Compatibility.md。mutex・Host起動の実機検証は今後。

## 残る条件と次工程

- USB-SUB-01／02／03はOpen。2 Host同時構成は固定TinyUSBの単一Host管理を踏まえ実装方式の検討が必要。今回のprobeはType_C2だけで、Type_C1=7355の要求を変更しない。
- QRの実記述子・配列・suffixは未確認。原文収集後にデコーダを確定し、35文字完全一致試験へ進む。今回の検査結果はqr_text_verified=false／hardware_acceptance=false。
- [機材の3案](Diagnostic_Adapter_Options_Rev0.md)では親Picoを保持する③3.3V USB–UART購入を推奨。最終選択・型番・配線確認は未完了。任意TX候補GP0を正式治具UARTへ昇格しない。
- 抵抗サイズ・現物位置、外部5V枝保護・定格、ログ取得経路の確認後、実機直前に[治具図Rev.4](../drawings/NF55G_Fixture_20261111_Rev4/README.md)を使って改造を案内する。微細DB_N／DN1の測定は要求しない。
- 現在配置済みdev-20261111.1、旧FW2MBバックアップ、既存親Pico環境、NF55G／ATEコードと設定は保持。今回COMを開く・resetする・書込みする操作はしていない。

[準備仕様と手順](Preparation_Rev0.md)／[実機記録票（未実施）](Hardware_Record_Template_Rev0.md)。

## 2026-11-11 デバッグ変換器の指定

ユーザーがDSD TECH SH-U05Aを指定。メーカーのTTL信号3.3V・UART仕様を確認し、FTDI購入候補は履歴として保持。[採用機材と端子・モード・接続準備](SH_U05A_Debug_Setup_Rev0.md)を追加。初回は追加基板GP0診断TX候補→SH-U05A RXDとGNDのみ、TXD／3V3／5V0は接続しない。現物・COMと診断GP0採用は未確認、現RAM版UF2はUART無効のまま。FW変更・書込み・実機通信は行っていない。
