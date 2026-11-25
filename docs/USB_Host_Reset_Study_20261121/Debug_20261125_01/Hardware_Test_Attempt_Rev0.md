# 測定器USB HOST候補 .25.1 実機試験の着手記録

2026-11-25 09:38–09:39 JST。ユーザー確認済みCOM23のHOST TX受信とCOM5 ATEを使い、400セット耐久を開始。ATE選択200 mV、入力設定40 mV、CONF原文は約2 V相当。開始前確認を通過し、第1セットのTEST_START、READ `+0040.171E-03` V（610ms）、SYST:ERR `+0,"No error"`、TEST_END（156ms）は成功。HOST A/T/RはREADの要求8とSYST:ERRの要求9でそれぞれ同一session・request、応答原文はATEと一致。TEST_END直後の `PICO_SELF_CHECK?` は12.031秒で0 byte。承認済み停止基準に従い第1セットで停止し、完了基準を満たしたセットは0/400。後追いの読取専用照会はIDLE／SD OK／drop 0／TEST_LOGGER OK／TEST_LOG_DROP OK、HOST nonce不変。READ・TEST_STARTの再送、リセットなし。初回無応答原因と試行CSV回収は未確認。[終了結果](endurance_20261125_093854_985304/result.json)／[ATE TX/RXと相関](endurance_20261125_093854_985304/ate.jsonl)／[HOST UART原文](endurance_20261125_093854_985304/host_uart.bin)／[停止後照会](ate_post_state_20261125_093927_596967.json)

2026-11-25 09:36 JST。再起動後もCodexの既定PowerShell起動はOSエラー5。Codex実行ツールで `C:\Windows\System32\cmd.exe` を明示するとPythonを起動でき、COM5へ自動照会できた。09:28の単発試行はATE選択200 mV、入力設定40 mV、CONF原文 `"VOLT +1.999999E+00,+1.000000E-07"`。TEST_START、READ `+0040.170E-03` V（593ms）、SYST:ERR `+0,"No error"`、TEST_ENDは成功。直後の `PICO_SELF_CHECK?` は12.031秒で受信0 byte。後追いの読取専用確認で自己診断のTEST_LOGGER/TEST_LOG_DROP、SD OK、drop 0、IDLE、HOST READY・nonce `7ABC103D90988F33` 不変を確認した。測定は再送していない。元の単発試行は停止結果を保持し、自己診断の初回無応答原因、試行CSVの回収、400セット耐久は未確認。[単発試行](ate_single_trial_20261125_092854_019833.json)／[Codex自動照会](ate_post_state_20261125_093624_624435.json)

2026-11-25 09:18 JST。固定配線復帰後、COM5/57600から新FW `.25.1` の7355 CDC実通信を確認した。`EXT_QUERY 2000 *IDN?` 1件のATE応答は375msで、7355識別文字列とCRLFを含む32byteが期待原文と一致した。前後のHOSTは同一個体・nonce `7ABC103D90988F33`・READY。親通信は前後ともIDLE、SD OK、ログdrop 0。単発READとTEST_START～TEST_END、400セット耐久は未実施。次は選択済みレンジと既知入力を確認して1セットを行う。[ATE原文と所要時間](ate_after_flash_20261125_091817_864122.json)

2026-11-25 09:13 JST。ユーザーが通常のWindows PowerShellで個体 `BFCF2EDB84B0B37F` に `.25.1` を書き込んだ。作業ログから `load -v` と独立 `verify` の両方が `OK`、同一個体の版読戻しが `.25.1`、終了時がBOOTSELであることを確認した。書込み前のFlash退避は2,097,152 byte。再計算したSHA-256 `fadcf3da168f0c10a5e052dbe8487e0303c119ba227db1dea7c23c38a0c7a53d` が退避マニフェストと一致した。固定配線への復帰、通常起動、7355 CDC実通信、400セット耐久は次工程。[版読戻し](flash_20261125_091346_149/05_after.stdout.log)／[退避マニフェスト](flash_20261125_091346_149/backup_manifest.json)

2026-11-25 追記。通常のWindows PowerShellで短い中間パスを使い、ARMビルド92/92とpicotoolの版照合が完了した。対象はRP2350 ARM Secure、Waveshare RP2350-USB-A、Pico SDK 2.2.0。候補UF2は100,864 byteで、SHA-256 `ac9c7a6a43e5fcfaff280717f387e3cf5a4299316fd795ef96de077489936422` を再計算し、ELFとともにマニフェストと照合した。Codex経由の `picotool info -a` はOSエラー5で起動できず、測定器HOSTのBOOTSEL個体照合とFlash書込みは未実施。[候補UF2](candidate_20261125_090518_376/usb_submcu_external_meter_relay.uf2)／[マニフェスト](candidate_20261125_090518_376/manifest.json)／[ビルドログ](candidate_20261125_090518_376/build.log)

2026-11-25。候補は `meter-host-relay-20261125.1`。変更後のHost Unit／Mock NF55Gは534件成功済み。[前回の検証](Firmware_Verification_20261125_Rev0.md)

- SDK 2.2.0の既存Ninja構成で候補ターゲットを確認した。ドライランは85ステップを列挙して終了コード0。実ビルドはコンパイル出力へ進まず、別経路の起動でもWindowsがOSエラー5を返した。[ドライラン](arm_dry_run02.log)
- ビルド先にあったUF2は96,256 byteで、SHA-256 `7a817134cffdf124197c68d958cfe9b5a96a98dbe308c8d5dd5a63e121e98ef2`。前回確認した旧成果物と一致し、今回の候補UF2の生成は未確認。
- COM5のATE経路とCOM6の親Picoが列挙された。`picotool info -a` はBOOTSEL機器を検出せず、親のMicroPython機器のみを報告した。測定器HOSTへの書込み、SCPI送信、候補を使った実機試験は未実施。

再開順は、候補UF2の生成と版・SHA-256の確認、測定器HOST個体 `BFCF2EDB84B0B37F` の手動BOOTSELと現Flashの退避、書込み後の独立verify、固定配線復帰後のHOST情報／7355 IDN／単発READの順。ATEによりレンジと入力条件が確認できたら、TEST_START～TEST_ENDを1セット実施し、SD・ログ・通信状態を照合する。400セットの無リセット試験はその後に実施する。[受入基準](../CDC_Endurance_Acceptance_20261124_Rev0.md)

### 通常のPowerShellから候補をビルドする手順

CodexのPowerShell起動はプロファイルを無効にしてもOSエラー5が再発した。起動できた試行ではスクリプトの構文検査を通過し、CMakeはGNU 14.3.0を検出してCコンパイラのABI確認まで進んだ。[構成ログ](candidate_20261125_084741_235/configure.log)

既存SDKとツールチェーンを使うビルド用スクリプトを用意した。リポジトリ直下を開いた通常のPowerShellで次を実行する。[ビルド用スクリプト](build_candidate_local.ps1)

```powershell
& .\docs\USB_Host_Reset_Study_20261121\Debug_20261125_01\build_candidate_local.ps1
```

ビルド成功後、picotoolでUF2の版を照合し、`candidate_日時`にUF2、ELF、SHA-256付きの `manifest.json` を保存する。スクリプトの新規実行は構成・ビルド・ファイル確認のみを行う。
