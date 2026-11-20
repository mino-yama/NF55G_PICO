# 7355 CDC Host単体確認とUART監視の仕様

2026-11-20 最新実機結果: .5のUSB/CDC/IDNは成立。レンジ設定後error=0、CONF約200Vと前面報告20Vの相違を再現。CONF_RANGE_NOT_20VでREAD前停止し測定値未取得。[試行1結果](Handoff_20261120_Rev0/Runtime_v5_run01/Result_Rev0.md)。以下の未実行記述は試行前の記録として保持。

2026-11-20 後続更新: 評価FW.5を対象BFCF2EDB84B0B37Fへ配置、Flash verify OK。書込み後infoで.5と同個体を確認。BOOTSELのままでrebootせず、測定は未実施。[配置結果](Handoff_20261120_Rev0/Deployment_v5/Result_Rev0.md)。以下の未配置記述は配置前の状態として保持。

## 2026-11-20 CDC Host引継ぎ・応答検証補強（最新）

USB/CDC/IDNはraw #07で確認済み。測定FW.1/.2はREAD前停止、.3は配置記録あり・実行記録なし。今回ユーザー回答は「20Vレンジで電源OFF」。CONF読戻し約200Vとの相違は未解決として追跡する。

評価版.5では、設定数値とCONF読戻し検証を実FW共用Cモジュールへ分離し、NaN/Inf・非10進表記・埋込みNUL・部分/複数行・不正な分解能を拒否する。既存.4の19～21Vゲートを維持し、レンジ指定コマンドや量産基準を変更しない。実Cの7テストを追加。全Host Unit/Mock 382件成功。実機再配置・測定は未実施。版別成果物・試験ログ・再開手順は[引継ぎ記録](Handoff_20261120_Rev0/Result_Rev0.md)を参照する。


2026-11-16 JST。対象は追加RP2350-USB-Aと7355。PCで確認済みの通信条件をPIO USB Hostで再現する単体確認用。親Pico/ATE/NF55Gへは今回接続しない。QR基板/FWを保持する。

2026-11-19 接続指定: 対象Host基板はWaveshare RP2350-USB-A（WAVESHARE-30274）。USB-Cは開発側、USB-A Host端子からユーザー準備ケーブルで外部測定器のUSB-Bへ接続し、外部電源で給電する。ケーブル結線・外部電源の保護条件・実機適合は別途現物確認する。

## 準備状態

通信条件と識別期待値、基板回路・施工案、固定SDK内CDC APIの存在は確認済み。CDC Host用の新FWは未作成であり、既存QR HID FWでは7355通信を試験できない。原典で未確認の7355 configuration/endpoint等は実機の列挙ログで取得し、固定番号を推測実装しない。

次工程は診断仕様→専用FWの実装/ビルド/検証→個体識別/退避/配置→固定接続で列挙/IDN、の順。配線だけでCDC動作確認可能とはしない。

## 2026-11-19 専用FWビルド進捗

RP2350-USB-A向けの独立診断FW `meter-host-diag-20261119.1`を追加し、固定SDK 2.2.0でARM build/linkを確認した。PIO USB HostはGPIO12/13・root port 1、CDC ACMのみを有効化。対象VID/PID 1334:0309を照合し、9600/8N1・DTR/RTS設定転送の完了後に識別用`*IDN?`＋CRLFを一度だけ送る。応答はraw hexで診断UART GP0 TXへ出す。timeout／部分送信で自動再送しない。FWはQR用Host・親Picoとは別成果物で、ATE本番指令や測定レンジ設定、NF55G制御を含まない。

UF2=83968 byte、SHA-256=`6ee5eb6ec31b2d9277d562fccac3af1e62720df5f56319cf23c39dbc0edc0ff0`。ELF／BIN hash、SDK・ボード・ピン情報は[build manifest](../../../../firmware/usb_submcu_external_meter_host/build_manifest.json)を参照する。`-Wall -Wextra -Werror`でARM build/link成功。全Host/Mock回帰375件も成功したが、この回帰はUSB-A基板のCDC Host動作を検証するものではない。

**未実施:** UF2配置、Flash操作、Host列挙、CDC control transfer、IDN実機通信、UART診断受信、7355測定。外部5V共用時の負荷・電気受入も未完了。基板現物の版・R13施工状態・電源条件を確認するまで書き込まず、実機受入は別途実施する。

## 2026-11-20 初回配置

対象serial `BFCF2EDB84B0B37F`へ診断UF2をpicotool v2.2.0-a4で配置し、`load -v`のFlash verify OKを確認。事前に同一対象の全Flash 2MiBを退避・照合済み。UF2 hashは[build manifest](../../../../firmware/usb_submcu_external_meter_host/build_manifest.json)を参照。

本FWはネイティブUSB Device/CDCを無効化しているため、通常起動後COMが出ないのは想定どおり。現在は診断UART adapterがPCに列挙されず、起動・Host readyログ未取得。外部電源・7355も未接続のため、USB-A Host列挙、CDC設定、IDN、測定は未試験。次はTX専用UART診断受信を準備し、R13施工確認と電源条件を満たしてから外部電源で起動する。

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

## 2026-11-20 診断FW配置後の実機受入

2026-11-20 UART/USB Host実機確認: USB-A–USB-Bケーブル経路と7355 BUS=CDCを確認後、ユーザー申告で7355をUSB-Aへ固定接続しPC USB-Cを切り離して外部電源を投入。SH-U05A COM22で30秒採取した`temp/meter_host_com22_capture_20261120_07.raw`は436 byte、SHA-256=`cac1ab22e6655a323671938428ce66037773c6bd3cc140867f9c394445f5222b`。対象VID/PID `1334:0309`のUSB/CDC mount、line coding 9600/8N1、DTR/RTS ON、IDN Query一回送信とCRLF終端応答32 byteを確認。実測IDN=`ADC Corp.,7355,246410099,  A02`。過去資料の`ADC Corp.,7355,246410072,  A01`は別個体の参照値であり、ユーザー確認により今回のID差は想定内。USB/CDC/IDN確認は成立。測定コマンドは未実施。次は前面LANG=SCPI、既知の低電圧DC入力、V/COM接続を確認してから測定試験用FWを準備する。診断Queryは自動一回で再送なし。

次段階は測定コマンド確認。7355前面でLANG=SCPIを確認し、既知の低電圧DC入力源、入力電圧、V/COM接続を記録する。現診断FWはIDNのみを一度送るため、測定試験には別途試験用FWの準備が必要。未確認の測定条件・終了後復元値を推測して送信しない。

診断FW `meter-host-diag-20261119.1`を対象serial `BFCF2EDB84B0B37F`へ配置し、picotool v2.2.0-a4の`load -v`でFlash verify OK。事前に全Flash 2MiBを退避・照合済み。UF2 hashは[build manifest](../../../../firmware/usb_submcu_external_meter_host/build_manifest.json)を参照する。

本FWはUSB Device/CDCを無効にしているため、通常起動後にCOMが列挙されないのは想定どおり。診断UART adapterがPCに検出されず、起動・Host readyログ未取得。外部電源・7355も未接続のため、USB-A Host列挙、CDC設定、IDN、測定は未試験。次はHost基板GP0 TX→SH-U05A RXDとGND共通のみで受信経路を用意し、115200/8N1で起動ログを確認する。USB-A/7355はまだ接続せず、電源経路・R13周辺の目視確認後に外部電源を使ったHost試験へ進む。

## 今回の変更と検証

既存資料とFW inventoryを再確認し、単体仕様を保存。既存QRしか存在しない状態を確認し、新CDC FW完成とは報告しない。ソース/FW/設定/実配線は変更せず、ビルド・Host/Mock・実機試験は未実行。正式親子UART/ATE API・校正AD/ARのOpen事項は単体IDNの仕様策定を妨げないが、今回確定しない。
