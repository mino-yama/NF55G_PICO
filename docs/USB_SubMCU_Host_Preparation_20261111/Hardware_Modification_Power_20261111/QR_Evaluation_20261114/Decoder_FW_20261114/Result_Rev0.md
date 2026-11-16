# QR基板内復元版 ビルド・検証結果 Rev.0

日付: 2026-11-14／qr-uart-20261114.2

## 変更と理由

実機で両向きとも取得できたAlt＋テンキー形式をHOST基板内で35文字へ復元する。qr_alt_decoder.c／hを追加し、限定プロファイル照合・完成時だけの診断出力・異常時の断片破棄をmain.cへ接続。CMakeで版を.2へ分離し、PCログ検査器にkind12／13と既知版容量を追加。正式な親Pico UART・ATE・Cache・Logger・SSは変更しない。

## 検証結果

|項目|結果|
|---|---|
|同一Cコードのnative実行|TinyCC 0.9.27でDLL化しctypes実行、両向きの実機HID再生を含む16件成功|
|ログ検査との関連確認|関連45件成功、0.525秒|
|全Host／Mock|346件成功、4.344秒、skipなし|
|ARMビルド|80ステップ、終了0、アプリ3ソースに-Wall／-Wextra／-Werror|
|UF2情報|qr-uart-20261114.2、ARM Secure、SDK2.2.0、1024 records、GP0 TX／115200 8N1、GP12 D+／GP13 D−|
|ELF|qr_alt_decoder_feed／init／poll／profile_supportedあり。g_probe77844byte、ARM decoder状態52byte、bss86448byte、text44992byte|
|UF2全ブロック|161ブロックのmagic、ARM family160件の連番・件数と補助ブロック1件を分けて検査|
|配布・旧版保持|新配布50ファイルをhash検証。旧3版の132ファイルは旧manifestとのbytes／SHA-256一致|

Hostの構造体配置とARMのenumサイズは異なる。native側はsizeofを実行時に取得して領域を確保し、両者のRAM ABI一致を仮定していない。HIDの8byte入力と35byte出力、同じC処理を検証した。

## 配布

[UF2](../../../../../firmware/usb_submcu_host_probe/releases/qr-uart-20261114.2/usb_submcu_qr_uart_probe.uf2)／[配布manifestと対応ソース](../../../../../firmware/usb_submcu_host_probe/releases/qr-uart-20261114.2/manifest.json)。UF2=82432byte、SHA-256=419fadbc4d7e79704ff8703574d59524e4bea5262991f10eef71a2c5441d61f3。

[仕様](Specification_Rev0.md)／[関連テスト](Targeted_Tests.txt)／[全Host／Mock](Host_Mock.txt)／[ビルド](Build.txt)／[UF2情報](UF2_Info.txt)／[ELFサイズ](ELF_Size.txt)／[シンボル](ELF_Symbols.txt)／[配布と旧版検証](Release_Verification.json)／[nativeコンパイラ出典](Native_Compiler_Source.json)。

## 実機未確認と次の工程

新FWはまだ基板へ書き込んでいない。外部電源OFF、外部5V線・QR・UART2線を外し、PC Type_C1のみを接続してBOOTSELへ移行する。chipidとUF2を照合し、現Flash退避・load -v・独立verify後、QR35文字の診断レコードkind12を実機で確認する。その後、同じ起動内の2回読取で旧断片・重複通知の有無を確認する。

1024件ログでは長時間・3回以上の読取全記録を保証しない。プロファイル不一致、inter-report暫定5秒、文字種・長さ・terminator異常、切断のエラーは正式APIの確定ではない。電源投入起動差、先頭NUL、電気保護、7355・2 Host・親子UARTは継続。USB-SUB-01／02／03／04はCloseしない。
