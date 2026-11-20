# .3受信確認後の固定20V確認手順 Rev.0

COM7をシリアルモニターで57600bps/8N1/flowなし/終端CRで開く。Codex診断はポートを解放済み。今回の実機Query12周は原文保持成功、現在はDCV/連続OFF/AUTO ON/CONF約20V。固定20Vの設定確認はこれから。

次を一行ずつ送り、その応答が完了してから次へ進む。設定のOK:EXT_TXだけで成功を判定せず、続くQueryと前面を確認する。

~~~text
EXT_SEND 2000 :SENS:VOLT:DC:RANG:AUTO OFF
EXT_QUERY 2000 :SENS:VOLT:DC:RANG:AUTO?
EXT_SEND 2000 :SENS:VOLT:DC:RANG 20
EXT_QUERY 2000 :CONF?
EXT_QUERY 2000 :SYST:ERR?
~~~

AUTOの復号0、CONFの機能/レンジ/分解能と前面レンジ、エラーを記録してログを共有。値が食い違えば原文のまま記録し、測定へ進む前に切り分ける。文字列が再度崩れた場合も測定せず保存する。タイムアウト等では自動再送しない。

この設定/測定は今回Codexからは送信していない。以降の単発測定手順はHost_UART_Sync_Fix_01/Serial_Monitor_Range_Measurement_Rev0.mdを参照するが、現行Hostの版は.3。
