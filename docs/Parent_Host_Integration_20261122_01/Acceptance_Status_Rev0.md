# HOST USB CDC受入試験 2026-11-22 Rev.0

## 完了した検証

- 前工程のidle USB-B切断/未送信拒否/RESETなし再接続/IDNは1回成功。詳細は[引継ぎ実行結果](Result_Rev0.md)。
- tests/test_external_instrument_link.pyへ3件追加。実Host C engine + 親Pythonで1000回の3〜192 byte可変長応答、途中応答後の切断/remount/遅着データでのfault保持、不正ATE行4種類と正常要求の交互受付を確認。
- リンク試験35件成功、2.452秒。全Host Unit / Mock NF55Gは459件成功、17.130秒。[全体ログ](Acceptance_Unit_20261122.log)。実USB adapterの転送/遅延callbackを直接試験した証明ではない。

## 実機試験の経過と現在状態

1. Acceptance_01: COM6 openがアクセス拒否。全ポートopen前なので要求未送信。フォルダは初回試行の履歴として保持。
2. [Acceptance_02](Acceptance_02/result.json): COMポートopen後、EXT_QUERY 2000 *IDN?とCOMM_STATUS?を一つのburstで一回送信。4秒以内にATE/Host/親USB出力なし。自動再送せず停止。
3. その後、親COM6のunique_id=69f7d45962cfdfad、EXTERNAL=True、PIO SM4/5=False、REPL globalsに__thonny_helperを確認。親runtime停止は確認事実。誰のどの操作が停止原因か、これだけで断定しない。[割込時記録](Acceptance_02/parent_interrupt.raw)。
4. ユーザーがThonny等のCOM6接続解除とCodexでの起動続行を回答。
5. ユーザーがCDC HostのRESET完了を回答。Codexが親をsoft rebootし、[Acceptance_03](Acceptance_03/result.json)の最初のIDNでERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0、後続COMM_STATUS?はOK:state=IDLE。
6. [Host原記録](Acceptance_03/host.raw)のhは.21.1/FAULT。Host nonceはB2F13F9BB5D183BEで前工程の成功時と同一、親nonceはD51DEE0AFD9C4383へ変更。対象Hostの新boot成立を確認できていない。操作対象/ボタン/RESETの成立を確認中。実物位置を推測して操作指示を続けない。
7. picotool infoではBOOTSEL対象なし。親MicroPython通常USBのみを検出。これでHostの電源状態やRESET回路を断定しない。

8. ユーザーの「完了」をHost操作完了として受領し、親をsoft reboot。[Acceptance_04](Acceptance_04/result.json)の初回IDNもERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0。Host hの親nonceは306F8CB1E7845A0A、Host nonceは再びB2F13F9BB5D183BE、状態FAULT。要求を繰り返さず、操作対象の基板とボタン表示を具体的に確認する質問を送った。[Host原記録](Acceptance_04/host.raw)、[親再起動記録](parent_restart_after_operator_complete.raw)。

9. ユーザーは「7355につながるUSB-A Host基板のボタンを押した」と回答。基板の対象は確認済み。ボタン表示は未回答のため、印字を確認中。ボタン操作の事実と、対象MCU再起動成立の実証を区別する。

現在: 親は通常runtime稼働、外部リンクfault保持、NF protocol state=IDLE。COM6/7/22は解放済み。Acceptance_04以降の追加IDN/READ/設定・Flash変更・配線変更・NF55Gコマンドは送っていない。Host再起動成立は未確認。200回反復試験はまだ開始できていない。

## 完成までの受入項目

|項目|現状|次の確認|
|---|---|---|
|idle切断/再接続|前工程1回成功|複数回と起動順/電源条件の再現性|
|通常連続通信/ATE応答順序|実C/Python 1000回成功、実機反復は開始前停止|Host起動確認後、200回IDN+COMM_STATUS?|
|不正→正常受付|実C/Python 4種類成功|実機のATE形式異常・境界・応答原文|
|送信開始後切断|実C/Pythonはambiguous fault/再送禁止を確認|実機でA/T/E時刻と抜線時刻を捕捉|
|旧/途中/遅着応答排除|実C/Pythonで拒否|実USB/計測器内部出力を含む境界確認|
|SD/RTC・ATE/NF55G/他Host負荷|既存Mock回帰成功|実機の構成/測定条件と負荷受入|
|測定Cache連携|中継確定仕様では任意応答を保存しない|後続の正式測定API/取得tokenとの接続仕様が必要|
|fault後の自動復旧/監視/WDT|方式・管理要求・期限等が未確定|検討Rev.2とOpen Issueに沿って設計回答後実装|

確定済み中継仕様の試験と、未確定の量産自動復旧/校正Cache実装を区別する。quiet待ちだけで故障を解除しない。IssueはOpen、完成/量産受入済みとはしない。製品PASS/FAILをPicoで判定しない。

## 変更ファイル

- tests/test_external_instrument_link.py: 上記3回帰試験。
- [acceptance_stress.py](acceptance_stress.py): 生byte保持、CRC decode、session/request/A/T/R照合、200回IDN+ローカル照会、異常停止/再送禁止の実機試験script。今回、ポート競合後に親USB監視のみ任意化（欠測を明記）。
- 本文書、CHANGELOG、Test_Specification、Open_Issuesへ現状を追記。src/Host firmware実装は変更なし。過去の合格記録や退避Flashは保持。
