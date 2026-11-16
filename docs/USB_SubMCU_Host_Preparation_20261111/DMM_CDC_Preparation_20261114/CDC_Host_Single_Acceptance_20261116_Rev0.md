# 7355 CDC Host単体確認とUART監視の仕様

2026-11-16 JST。対象は追加RP2350-USB-Aと7355。PCで確認済みの通信条件をPIO USB Hostで再現する単体確認用。親Pico/ATE/NF55Gへは今回接続しない。QR基板/FWを保持する。

## 準備状態

通信条件と識別期待値、基板回路・施工案、固定SDK内CDC APIの存在は確認済み。CDC Host用の新FWは未作成であり、既存QR HID FWでは7355通信を試験できない。原典で未確認の7355 configuration/endpoint等は実機の列挙ログで取得し、固定番号を推測実装しない。

次工程は診断仕様→専用FWの実装/ビルド/検証→個体識別/退避/配置→固定接続で列挙/IDN、の順。配線だけでCDC動作確認可能とはしない。

## 初回配線と監視条件

|接続|仕様・条件|
|---|---|
|USB機器|追加RP2350-USB-AのUSB-A → USB A–Bケーブル → 7355 USB-B|
|監視UART|追加HostのGP0 TX → 3.3V USB–UART変換基板のRXD、GND共通。115200bps/8N1を初回診断用の案とする|
|監視方向|初回はHostからのTX専用。変換基板TXD/5V/3V3をHostへつながない。TXD-RXD短絡ジャンパがある場合は外す。型番・信号電圧・ピン表示を照合|
|HostのGP1|初回診断では接続/初期化しない。親からの正式双方向要求受付は別工程|
|Host給電|機能評価では外部5Vの1供給系統。PC Type-Cを外す。枝の供給/保護条件は新個体で確認|
|FW書込み|7355と外部5Vを外しPC Type-Cを使用する独立モード。外部5V/PC VBUSを同時直結しない|

親のUART0/1使用とは競合しない。ここでGP0を使うのは別MCUである追加Host側。監視用115200bpsと、7355のCDC line coding 9600bpsは別の通信区間である。

基板R13/R10実装と現物版を照合し、公開回路と一致するR13実装個体では[Host専用化の施工案](RP2350_USB_A_20261116/Assessment_Rev0.md)に従う。未施工状態でHostの受入条件が整ったと判断しない。今回R13状態と監視adapter型番をユーザーへ確認中。実機配線・給電・書込みはまだ行っていない。

## CDC通信の仕様と最小FW範囲

- RP2350-USB-AのPIO USB Host: GP12 D+/GP13 D−、roothub1を出発点とする。SDK2.2.0と既存PIO派生の互換APIを照合して別プロジェクトで実装。
- CDC ACM機器の記述子を取得し、VID:PID=1334:0309、interface/endpoint/速度を診断出力する。機種識別はIDNも照合する。
- CDC line codingは9600/8N1、DTR/RTSともON。制御転送の完了/失敗を確認してから送信。
- `*IDN?`+CRLFを1件送信し、応答原文を行終端まで保存。期待値は `ADC Corp.,7355,246410072,  A01\r\n`。USB serialの24641007200とは区別。
- 部分送受信、受信長上限、timeout、切断、予期しない応答は診断結果へ分け、自動再送しない。初回Query timeoutはPC比較用の暫定2秒。正式量産Timingではない。
- 診断にはFW版/個体、USB初期化/mount、CDC設定結果、送受信原文、timeout/切断/Queue dropを含める。UART出力はRAM Queue経由の非blocking。PC側は先に受信を開始して原文保存。
- 診断ログ形式/最大長は専用FW実装時に記録し、旧QRの76byte形式/解析器に未対応の新ログをそのまま入力しない。原文完全性と通信成功を分けて検証する。

## 試験順と判定の境界

1. FW単体のARMビルドと適切なHost/Mock回帰確認、対象個体識別・旧Flash退避・配置verify。
2. 無給電で配線を整え、UART受信を開始後、固定USB接続状態で起動。初回は列挙/CDC設定/IDNまで確認。
3. IDN一致後、BUS=CDC/LANG=SCPIと既知の低電圧入力を確認し、[電圧/レンジ試験](CDC_Settings_Voltage_Quick_Test_Rev0.md)を逐次実施。設定後はQuery応答を挟む。
4. 単体成立後に親PIO UART、取得Cache、ATE確認後の別書込み・書込み後読戻しへ接続する。初回FWからNF55Gへ書き込まない。

IDN成功はUSB/CDC識別の成立。電圧取得成功・校正成功・製品PASSとは扱わない。QRも接続した総合試験は単体確認の後に行う。ホットプラグを初回の必須条件へ追加しない。

## 今回の変更と検証

既存資料とFW inventoryを再確認し、単体仕様を保存。既存QRしか存在しない状態を確認し、新CDC FW完成とは報告しない。ソース/FW/設定/実配線は変更せず、ビルド・Host/Mock・実機試験は未実行。正式親子UART/ATE API・校正AD/ARのOpen事項は単体IDNの仕様策定を妨げないが、今回確定しない。
