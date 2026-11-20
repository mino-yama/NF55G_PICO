# 単発測定設定と0x03入力 結果 Rev.0

2026-11-20。ユーザーが2.911V入力の測定準備をシリアルモニターから実施しログ提示。READ?はまだ提示ログにない。

## 確認事実

TRIG:SOUR IMM、TRIG:COUN1、SAMP:COUN1、TRIG:DEL0の各設定送信にOK:EXT_TX。TRIG:SOUR後、SAMP:COUN後、TRIG:DEL後のOPC?はHEX310D0A＝1+CRLF。最後のSYST:ERR?は+0,No error+CRLF。

TRIG:COUN設定の直後にユーザー送信ログで16進03（ETX、Ctrl+C相当）を確認。その後最初のEXT_QUERY *OPC?にERR:FRAMEが返った。src/ate_server.pyはCR/LF以外の制御byte<32でFRAMEを記録し、次の行終端まで入力を拒否。src/main.pyはその行をexecute_ate_lineへ渡さずERR:FRAMEを返す。したがって今回の流れは制御byte03によるATE行拒否の実装と一致し、そのOPC?は機器へ中継されない。

この03は7355のABORや測定キャンセルとして扱わない。行終端で受信エラー状態はクリアされ、その後の設定/OPC?/SYST:ERR?は正常応答。外部中継のEXT_TIMEOUT等やfaultラッチとは区別する。

## 次の操作

通常のUTF8一行送信だけを使い、16進03/Ctrl+Cの送信を避ける。設定を一括再送せず、まずEXT_QUERY 2000 :TRIG:COUN?で回数1を確認（00001等の表現も数値1として扱う）。確認後にEXT_QUERY 10000 :READ?を一回、次にEXT_QUERY 2000 :SYST:ERR?を送り、測定原文を2.911Vと比較する。timeout時の再送なし。

レンジ前面20V/CONF約200Vの相違は未解決のまま。測定原文を10倍/0.1倍等へ補正しない。Codexはポートを開かず提示ログ/ソース照合のみ。コード/Flash変更なし。

[提示ログ](User_Transcript_Rev0.json)。
