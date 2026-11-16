# Alt方式デコード採用・再開記録 Rev.0

日付: 2026-11-14

## ユーザー指定

英語キーボード設定の切分けについて「ここまでとして、ALTをデコードする方法で進めましょう」と指示を受領。英語設定への切替え調査・メーカー全設定初期化は行わず、実機で繰返し観測したAlt＋テンキー5桁をHOST基板内で復元する方針へ戻す。

## 今回の実施

- 作業ソースが原文取得版.1のsnapshotと一致することを確認し、既存qr-uart-20261114.2の対応ソース・Cデコーダ・テスト・実機fixtureを復元。
- 対象11ファイルを.2保存snapshotとSHA-256照合、全件一致。Source_Verification.jsonを参照。
- Host／Mock346件成功（9.433秒）、skipなし。両向き実機HIDを同じCコードへ再生する16件を含む。
- 既存.2配布UF2は82432byte、SHA-256=419fadbc4d7e79704ff8703574d59524e4bea5262991f10eef71a2c5441d61f3を再確認。ソースが配布snapshotと一致するため、新しい版名で同一バイナリを作り直さず、検証済みの.2を使用する。
- 旧Altデータ・.1／.2配布・英語設定の各再採取と設定資料は全て保持する。QRリーダー全設定の初期化は実行していない。

## 適用範囲

qr_alt_decoder.c／hはVID:E851／PID:1001と取得済み63byte記述子に限定。英数字・ハイフンの35文字＋Enterで完成原文kind12、異常はkind13。部分文字列は公開せず、途中異常はEnter境界まで破棄、切断で初期化、診断用暫定inter-report5秒を維持する。正式親子UART・ATE／Cache／Logger／SSにはまだ接続しない。

1024件の診断ログでは35文字1読取約389件。初期実機試験は1起動2読取以内に制限し、長時間・3回以上の原文保持を保証しない。先頭NUL、電源投入だけでの起動差、量産給電保護、7355／2 Host等は引き続きOpen。

## 実機の状態と次工程

**実機は現在qr-uart-20261114.1の原文取得版。今回のソース復元だけでは.2へ戻っていない。** これから対象個体を照合し、現Flash退避・.2書込み・独立verifyを実施する。

書込み準備は外部電源OFF、外部5V線・QR・UART2線を外し、PC Type_C1だけを接続してBOOTSELへ移行。配置後、外部給電・QR・診断UARTを戻してkind12の35文字と期待原文一致、次いで同一起動内の2回読取と重複／断片混入なしを確認する。

[Alt版仕様](../Decoder_FW_20261114/Specification_Rev0.md)／[既存ビルド・配布検証](../Decoder_FW_20261114/Result_Rev0.md)／[今回のHost／Mock](Host_Mock.txt)／[ソース復元照合](Source_Verification.json)／[配布UF2](../../../../../firmware/usb_submcu_host_probe/releases/qr-uart-20261114.2/usb_submcu_qr_uart_probe.uf2)。

今回実機書込み・読取・resetはまだ行っていない。製品PASS／FAIL判断とOpen Issue Closeは行わない。
