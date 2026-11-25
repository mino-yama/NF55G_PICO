# RP2350候補ビルドの起動障害切り分け

2026-11-25追記。ユーザー側の通常のWindows PowerShellとASCII版スクリプトで、C/C++ ABI確認とCMake構成が完了した。ビルドは `runtime_init_stack_guard.c.obj.d` の作成で停止した。依存ファイルの親ディレクトリが存在し、フルパスが261文字だったため、Windowsのパス長制限が有力。中間ディレクトリを `tmp/usb_host_build/日時` へ変更し、同じ相対パスでの試算を207文字に短縮した。成果物とログは従来通り案件内の `candidate_日時` に保存する。修正後のARMビルドは未確認。[構成ログ](candidate_20261125_085956_504/configure.log)／[ビルドログ](candidate_20261125_085956_504/build.log)

2026-11-25。11月23日の成功時はPico SDK 2.2.0とGNU 14.3.0を使用し、C/C++両方のABI確認が完了した。今回も同じSDKとコンパイラ版を検出したが、CのABI確認で出力が止まった。[前回の構成ログ](../Debug_20261123_01/arm_configure_v2.log)／[今回の構成ログ](candidate_20261125_084741_235/configure.log)

既存のNinja構成を使った試行でも、ドライランでは85ステップを表示し、実行時はコンパイル出力を確認できなかった。今回追加した個別起動確認では、CodexのPowerShell起動がOSエラー5で失敗し、別の起動経路から `cmd.exe /d /c ver`、ARM GCCの `--version`、Ninjaの `--version` を直接起動してもすべて `spawn EPERM` となった。ABI確認は停止が見えている箇所で、コンパイラが原因とは確定していない。Windowsが起動を拒んでいる理由は未確認。[実ビルド試行の記録](Hardware_Test_Attempt_Rev0.md)

次回は、通常のPowerShellを開き、管理者権限を付けずにまず `cmd.exe /d /c ver` を実行する。成功したらリポジトリ直下で `& .\.venv\Scripts\ninja.exe --version` を確認する。どちらも成功すれば[候補ビルドスクリプト](build_candidate_local.ps1)を同じPowerShellで実行し、並行してCodexを完全終了して起動し直すことで、Codex側の起動環境が回復するか確認できる。通常のPowerShellでも起動エラーが出る場合は、エラー原文でWindows側の起動障害を切り分ける。
