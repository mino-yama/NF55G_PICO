# 固定接続・連続読取候補FW 準備・配置結果 Rev.0

2026-11-14。ユーザー指定の固定接続運用向けqr-fixed-20261114.1を作成し、追加基板へ配置した。

## 変更と目的

- 起動出力後3000ms待ってからHost初期化する候補を追加。phase1～4を各初期化処理前後に送る。待ち時間の効果・原因は実機未確認。
- main回数・PIO frame数・Queue drop累計・完成数・HID数・flagsを1秒ごとに送信。電源投入時の停止箇所やUSBフレーム進行の切分けを可能にする。
- Continuous専用64件FIFOを排出後再利用。生涯1024件で止まる制約を除き、HID原文kind6を省略して完成35文字・エラー・状態を継続送信。有限Queueなので過負荷欠落はdropと連番で検知する。
- 旧RAM／UARTモード・配布版・実機原文は保持。新ビルドスイッチ`-DiagnosticTx -Continuous`で独立出力する。正式親子UART／ATE／Cache／SSには接続していない。

## 検証

- Host／Mock354件成功、48.622秒、skipなし（Host_Mock_Rev1.txt）。同じC FIFOの10000件周回・満杯非上書き／再利用・空読み旧値非公開、同じCデコーダ200回の正常復元とFIFO排出を含む。
- 初回テストではnative TinyCCがC11静的検査構文を解釈できず、等価なtypedefサイズ検査へ修正。初回失敗ログはHost_Mock_Rev0.txtへ保持し、再実行で全件成功。
- ARM Releaseビルド88ステップ成功。main／decoder／FIFO等アプリソースに-Wall／-Wextra／-Werror。最終ビルドはninja no work to doで最新状態を確認。
- UF2=84480byte、165ブロック。ARM Secure164ブロックのmagic／連番／件数／addressと、旧版一致の補助1ブロックを分けて検査。picotool infoで版・SDK2.2.0・GP0/GP12/GP13を確認。
- 対応ソース含む53ファイルを新配布へ保存しhash検証、旧.2の50ファイルはmanifestとの一致を確認。
- packageの初回検査は補助ブロックを通常連番に混ぜたため停止。検査を区別して再実行し成功。途中の配布物は同一内容を照合して再利用し、旧配布物は上書きしていない。
- 準備スクリプトのpy_compileはWindowsの長いpycacheパスで失敗したため、書込みを伴わないcompile()で両スクリプトの構文を確認した。

UF2 SHA-256: `da331d3f14725f666191c2cda6ce180a3c44bf3b53a1d41e657e6284fa304424`。

## 実機配置と残事項

A06FEA01012EC137の現Flash2MB退避後、load -v・独立verify・版と個体ID照合・rebootが成功。[配置証跡](deploy01/Result_Rev0.md)。親Picoは操作していない。

外部給電・QR固定接続のRSTなしcold-startと20回以上／10分以上の連続読取は次工程であり未実施。今回の書込み成功を起動問題の解決・全体受入完了としない。先頭NUL・遅延して届く読取・量産給電保護・7355／2 Host・正式要求境界等は未解決のまま。

[仕様](Specification_Rev0.md)／[Hostテスト](Host_Mock_Rev1.txt)／[初回ARMビルド](Build_Rev0.txt)／[最終ビルド](Build_Final_Rev0.txt)／[UF2情報](UF2_Info_Rev0.txt)／[配布検証](Release_Verification_Rev0.json)／[実機検証計画](Hardware_Test_Plan_Rev0.md)

[配布manifest・対応ソース](../../../../../../firmware/usb_submcu_host_probe/releases/qr-fixed-20261114.1/manifest.json)
