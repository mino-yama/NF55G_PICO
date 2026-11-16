# 7355 USB CDC PC直結確認 結果 Rev.0

2026-11-14。同一USB Host SubMCU案件の継続。ユーザーの「USB_HOST 7355との接続確認をすすめて」に基づく実機確認。

## 確認できた事実

ユーザーより7355のPC直結済み、その後「RMTになりました」と申告。Windowsで新たにCOM24を検出し、識別応答により7355実機との通信を確認した。追加RP2350によるHost通信の成功とは区別する。

|項目|取得結果|
|---|---|
|Windowsポート|COM24（既存SH-U05AはCOM22、今回は開いていない）|
|VID／PID|1334／0309、USB REV_0100|
|Windows USB serial|24641007200|
|Compatible ID|Class_02／SubClass_02／Prot_01（CDC ACMに対応するWindows識別情報）|
|Windowsドライバー|usbser|
|送信|`*IDN?`＋CRLF、7 byte|
|応答原文|`ADC Corp.,7355,246410072,  A01\r\n`|
|機種／応答S/N／FW欄|7355／246410072／`  A01`|
|成功条件|PC側9600・8N1、DTR=True、RTS=True|
|再開確認|上記成功条件でCOMを閉じて開き直した2回とも応答原文が完全一致。初回を含め3回成功|
|終了状態|すべてのCOMハンドルを閉じた。RMTからLOCALへの復帰操作・確認はしていない|

USB serialと識別応答S/Nは文字列が異なるため、それぞれ原文を記録した。USB構成記述子全体・endpoint・ACM functional descriptorを取得したわけではない。

## 制御線の切分け

|順序|DTR|RTS|結果|
|---|---|---|---|
|1|OFF|OFF|write timeout、事前受信なし|
|2|ON|OFF|write timeout、事前受信なし|
|3|ON|ON|7 byte受理、7355識別応答を取得|
|4|OFF|ON|7 byte受理、2秒以内の受信なし|
|5・6|ON|ON|各7 byte受理、各同一識別応答を取得|

このPC／ドライバー／実機の組合せでは両方ONを再現条件とする。RTSをOFFにした試行で送信timeout、DTRをOFFにした試行で応答未取得を観測したが、デバイス内部の原因や全機種共通の必須仕様までは断定しない。timeout試行の送信完了・実機受信有無は不明。再送不能な設定指令は扱わず、識別Queryだけを使った。各試行の事前受信を保存し、入力バッファ消去はしていない。baudrateはPCで成功した試行条件であり、CDC実転送速度や正式UART契約ではない。

## 次のHost工程と未確認事項

- 現配置QR FWはType_C2 PIO Host専用。Type_C1 native CDC Hostと2 Hostは未実装・未受入。
- 原典回路図の接続線を画像でも再確認した。Type_C1 CC1はR5=5.1kΩ、CC2はR6=5.1kΩを介してGNDへ接続される。これはDevice/Sink側の回路。Type_C2の既済改造をType_C1へ施工済みと扱わない。
- Type_C1にType_C2のようなSource用予備抵抗パッドがあるとは原典から確認できない。R5／R6を同じGND接続のまま56kΩへ置換してもRpにならない。現物位置・ケーブル・必要なCC経路を確定する前に部品撤去やジャンパ施工を指示しない。
- Type_C1とType_C2のVBUSはVSYSに直結。追加基板でPC給電と外部5Vを同時直結しない。今回は7355→PCの直結であり、追加基板へ7355を接続していない。
- 次に使用するUSB-C－Bケーブル／変換アダプター構成と、R5／R6の現物施工状態をユーザーへ照会中。回答後にHost回路条件を具体化し、人間確認が必要な施工とFW書込み・識別試験を分けて案内する。
- native Hostの準備条件は、固定SDK2.2.0、roothub0、CDC ACMのみ、9600/8N1・DTR/RTS両ON、GP0診断TX、別プロジェクト・配布でQR版を保持すること。固定TinyUSBのCDC Hostには列挙時line codingとline controlの設定口が存在することをソースで確認した。これは実装・ARMビルド・実機成功の報告ではない。
- 実機BUS／LANGの前面設定値は未回答。CDC class認識と通信成功から前面表示値を補完しない。
- 測定値取得・前面測定値との比較、測定条件、機能／レンジ、Host側descriptor全体、電源／逆流／保護、2 Host、親子UART／ATE連携は未確認。USB-SUB-01／02／03／04のClose、製品PASS／FAIL判定は行わない。

## 操作・変更範囲

送信した計測器ASCIIコマンドは識別用`*IDN?`だけ。測定設定・初期化・校正・NF55G指令は送っていない。CDC制御線とPC line codingは試行のため変更した。コード／既存FW／元資料の変更・書込みなし。Host Unit／Mock NF55Gはコード変更がないため今回再実行しない。PC識別通信の試験結果は上表の通り。

## 証跡と根拠

- [初回DTR/RTS OFF試行](Identity_Query.json)
- [DTR ON試行](DTR_On_Trial/Identity_Query.json)
- [両ONでの初回成功](DTR_RTS_On_Trial/Identity_Query.json)、[受信原文](DTR_RTS_On_Trial/rx.bin)
- [制御線比較と再開2回](Repeat_And_RTS_Check/Results.json)
- [Windows機器識別](Windows_Device_Identity.json)
- [原典回路図の確認画像](Schematic_Review.png)
- メーカー英文説明書: reference/ADCMT_7355_20261104/7355-ope--foa-00000201a00-e.pdf、PDF131／146（*IDN?、応答形式）、PDF95／104（IF選択・CDC）。CRLF受理は今回の実機で確認した条件。
- 回路図: reference/USB_Host_SubMCU_20261110/RP2350-USB-C_schematic.pdf、1ページ。
- 固定TinyUSB: tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src/class/cdc/cdc_host.h、examples/host/cdc_msc_hid/src/tusb_config.h。CFG_TUH_CDC_LINE_CONTROL_ON_ENUM／CFG_TUH_CDC_LINE_CODING_ON_ENUM。

メーカーCDC用xlsmサンプルはzip内に存在することだけ確認。VBA解析用oletoolsが未導入で取得にも失敗したため、サンプル内部コードは未確認。通信成功条件の根拠をサンプル照合済みとはしない。
