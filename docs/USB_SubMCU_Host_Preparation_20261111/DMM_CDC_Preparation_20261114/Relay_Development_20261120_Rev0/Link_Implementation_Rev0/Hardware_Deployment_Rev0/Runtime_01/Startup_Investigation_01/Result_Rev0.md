# 親単体 起動・PIO診断結果 Rev.0

2026-11-20。ユーザーの外部電源OFF・親/Host信号/GND切離し・親単体USB接続完了後に実施。

## 確認事実

COM6 VID:PID 2E8A:0005、実機unique_id 69f7d45962cfdfadを照合。リセット前のSM4/5はともにactiveだった。raw soft reset後、create_fixture_app(enable_hardware=True)が成功し、external_error=None、中継リンクあり、SM4/5 active、ATE UART0 57600/8N1 GP0/1、SD READY/OKを確認した。

続けて親内のPIO RX入力を一時的に同じGP12へ割り当て、実配置ドライバのTX/IRQ/RAMリング/readを通してHフレーム75byteを照合。送受信原文が一致し、UART_ERROR=None。外部配線のジャンパ追加は不要で、Host/NF55G/7355への要求は送信していない。診断終了時はraw soft reset後のfriendly REPL停止。ファイル/Flash書込みなし。

初回実行ではシステムPythonにmpremoteがなく、import段階で停止したため実機操作なし。その後既存.venvのPythonで実行成功。元ログや先行試験資料は保持した。

## 未確認事項

親GP13という元のRX端子からの実入力、親とHostの現物配線、Host UART/通常起動/USB状態、親Host間の実フレームは未確認。親単体の成功だけで実中継成功や原因確定とはしない。USB-RELAY-LINK-01はOpen維持。

次は親と切り離したHost単体に、COM22の3.3V USB-UARTからHフレームだけを1回送り、h応答/基板ID/FW版/状態を照合する。Host_UART_Investigation_01/host_hello_diagnostic.pyを準備したが未実行。機器コマンドQやSCPIは送らず、レンジ検証は保留する。Hostの外部5VとUSB-Cは同時接続しない。

## 証跡

[起動診断JSON](Startup_Result.json)／[初期化ログ](Factory_Diagnostic.log)／[リセット前状態](Before_Raw_Reset.log)／[PIO照合JSON](PIO_Internal_Result.json)／[送受信原文HEX](PIO_Internal.log)。

今回の変更は診断スクリプトと記録のみ。本番コード/仕様変更なし。実機診断2件成功、既存Host Unit/Mockの446件成功は前回実装版の結果として保持し今回の実機中継受入とは区別する。
