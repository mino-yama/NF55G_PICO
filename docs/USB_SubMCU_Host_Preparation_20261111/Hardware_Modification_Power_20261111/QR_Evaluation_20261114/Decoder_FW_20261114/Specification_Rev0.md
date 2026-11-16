# HOST基板内 QR文字列復元 診断仕様 Rev.0

日付: 2026-11-14／開発版qr-uart-20261114.2

## 目的・適用範囲

実機で両向き各1回確認したHID形式を、HOST基板内で35文字へ復元する。診断版であり、親Picoの正式UART、ATEコマンド・Cache・Logger・SSへの結合は行わない。文字列の形が整っても製品PASSやSS書込み可とは判定しない。

## プロファイルと受付

- VID:E851／PID:1001、取得済み63byteのHID Report Descriptorとの完全一致を条件に、単一HID interfaceの復元を有効化する。不一致はエラー10として原文調査にとどめ、推測で別配列へ切替えない。
- reportは8byte、予約byte0、修飾は0またはLeft Alt（04）、非ゼロキー最大1個。Alt＋テンキー5桁の10進数字をAlt解除時に1文字へ復元する。
- 文字は確定QR要件のASCII英数字とハイフンのみ。大小文字と先頭ゼロを保持し、値補正や桁埋めはしない。
- 35文字が揃いEnterを受けた時だけ完成文字列を公開。Enter自体は35文字に含めない。重複した同じ押下報告は再入力にしない。Enter解放前の重複報告も再通知しない。

## 状態・失敗時

途中データは状態内だけに保持。Enter前の異常・35文字超過・文字種異常では内部文字列を消去し、Enter境界まで破棄する。短いままEnterならエラーとし、そのEnterで境界が確定したので次の読取へ戻る。切断・再mountで状態を初期化し、旧断片を引き継がない。

診断用inter-report期限は暫定5000ms超。正式ATE／内部リンクのtimeoutではない。変化のない長押し報告で期限を延ばさず、超過時に1回エラーを出してEnterまで破棄。終端が欠けた試行の後は、次のEnterを消費してから再受付するため、次に読ませたQRを1回破棄する場合がある。取消・要求ID・試行境界の正式仕様は引き続き未確定。

## 診断レコード

既存76byteのレコードとUARTのHEX形式は維持。HID原文kind6は継続保存。

|kind|名称|data|
|---|---|---|
|12|qr_text|完成した35 ASCII byte。NUL・Enterは含めない|
|13|qr_decode_error|エラー理由1byte|

エラー: 1=report長、2=予約byte、3=修飾、4=複数キー、5=非対応キー、6=Alt数字桁、7=文字種、8=文字数、9=暫定timeout、10=profile不一致、11=途中切断。

文字列復元と診断レコード記録はUSB callback内で固定長・非blocking。Flash／SD書込み・UART待ちは追加しない。通常ループはFIFO空き確認・最大16byte排出を維持。kind13はPC解析でcapture_errors、kind12は長さ・文字種・HID mount状態を検査し、原文解析器のhardware_acceptance=false／qr_text_verified=falseは維持する。

## 容量・制約

UART版は1024件、g_probeヘッダと76byte構造は維持。RAM版は旧256件のまま。ログ満杯では上書きせず破棄数を加算するが、UART上に破棄数の報告はない。実機35文字1読取約389件のため、初期試験は1起動2読取以内とし、3読取以上や長時間連続の記録完全性は保証しない。文字列を継続的に親Picoへ届ける正式Queue／内部リンクは別工程。

先頭NUL原因と、電源投入だけではログが出ずRST後に取得する差は今回修正していない。電気保護・7355・2 Host・正式親子UARTのOpen Issueは維持する。

## 検証

FWと同じqr_alt_decoder.cをWindows x64 native DLLへコンパイルし、Python ctypesから実行。TinyCC 0.9.27の公式配布ミラーをTLS検証付きで取得、導入先はGit管理外tools/usb_submcu/host-test-tcc。取得元・zip hashはNative_Compiler_Source.jsonに保存。証明書検証の無効化は行わない。

両向きの実機HIDをtests/fixtures/usb_submcu_qr_altへ時刻と8byteの組で保存し、Cコードへ再生。両方とも完成35文字を各1回だけ出力。その他、大小文字・ゼロ・ハイフン、長押し重複、連続2読取、終端欠落、34／36文字、禁止文字、report異常、Alt桁不足／超過、timeout境界とtick wrap、状態初期化、profile不一致を確認した。

関連45件成功、全Host／Mock346件成功（4.344秒）、skipなし。Targeted_Tests.txt／Host_Mock.txt参照。これはCコードのHost実行と模擬再生であり、新FWの実機受入ではない。

ARMビルドと配布hash、配置状態はResult_Rev0.mdに記録する。旧配布物・既得rawは変更しない。
