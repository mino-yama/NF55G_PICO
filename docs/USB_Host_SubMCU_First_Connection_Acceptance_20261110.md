# RP2350-USB-C 初回PC接続・識別の受入結果

日付: 2026-11-10
状態: **PC接続・BOOTモード認識・通常起動時USB列挙を確認。USBホスト／UART受入は未実施。**

## 結果

| 項目 | 確認結果 | 評価範囲 |
|---|---|---|
| 通信用ケーブル変更後の認識 | RP2350 Boot、VID:PID 2E8A:000F、Windows状態OK | PCとのUSBデータ接続成立 |
| BOOTモードのドライブ | E:、ラベルRP2350、FAT。INDEX.HTMとINFO_UF2.TXTを読み取り | ROM書込み待機の列挙・ファイル読取を確認。UF2書込みは未実施 |
| INFO_UF2.TXT | UF2 Bootloader v1.1 / Model: Raspberry Pi RP2350 / Board-ID: RP2350 | ボードメーカー・基板版を証明する情報ではない |
| RUN／RST単独操作後 | E:は消え、COM21、VID:PID 2E8A:0009、製品文字列Pico、Windows状態OK | 通常起動時USB CDCの列挙を確認 |
| 起動モード間の対応 | USB serial A06FEA01012EC137が両モードで一致 | 同じUSB識別子の追加基板と確認 |
| COM21の受信 | 115200指定、DTR=True、RTS=False、6秒間、受信0byte、エラーなし | ポートopen/read/closeのみ。USB CDCの設定であり、基板間UARTのbaud受入ではない |
| ファーム名・版 | 不明 | 受信0byteから未実装・故障・空Flash等を断定しない |

ユーザーが旧ケーブルは充電専用の可能性ありとして通信用へ変更し、その後認識した。旧ケーブルのデータ結線を直接確認していないため、原因はケーブルの可能性が高いという推測に留める。

既存治具Pico 2のCOM6／serial 69F7D45962CFDFADとは別のUSB識別子。追加基板の呼称はユーザーの現物申告に基づく。基板版・メーカー・回路図一致は現物確認待ち。

## 証跡

- [USB識別・BOOT情報JSON](USB_Host_SubMCU_First_Connection_Evidence_20261110.json)
- [COM21送信なし受信記録JSON](USB_Host_SubMCU_COM21_Passive_20261110.json)
- [PC接続ポート位置の公式写真と案内](USB_Host_SubMCU_Port_Identification_20261110.md)
- [初回受入チェックリスト](RP2350_USB_C_First_Acceptance_20261110.md)

機器へのデータ送信、UF2書込み、Flash消去／書換え、基板改造、GPIO初期化は行っていない。COM21受信時はUSB CDCのDTRを有効にし、取得終了後にポートを閉じた。受信スクリプトはtemp/usb_submcu_acceptance_20261110/capture_com21.pyに保存し、実行終了コード0。これまでの既存Host Unit／Mock NF55Gは273件成功。今回通信コードを変更していないため再実行していない。

## 次の受入項目

1. 基板表裏と型番・版／ロットを確認し、Type_C1／Type_C2・抵抗実装を保存済み回路図へ照合する。現物写真が必要。
2. Type_C2のCC Source構成、VBUS供給元・保護・逆給電条件を確認し、電圧／電流測定値を記録する。未確認の抵抗付替え・VBUS直結を行わない。確認前にQRを接続しない。
3. 現ファームと依存版を特定・保全し、基板適合を確認した受入用FWを準備する。PATHと確認した標準保管先ではcmake／ninja／arm-none-eabi-gcc／picotool／SDKを検出できず、Pico VS Code拡張機能は存在した。PC全体に未導入とは断定しない。
4. QRはType_C2、7355はType_C1の固定割当てで単体試験を行う。7355使用時はType_C1のPC接続を外す。代替デバッグ経路は未確定。
5. 双方のホスト受入後、治具UARTと共存Timingへ進む。下位GPIO・内部フレーム・CRC等は現行計画で未確定のため推測で固定しない。

USB-SUB-01等のIssueはOpen継続。今回のPC列挙成功は、電源受入、USBホスト通信、UF2書込み、製品PASSを意味しない。原典・既存通信実装は変更していない。
