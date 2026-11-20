# 2.911V入力の単発測定 手順 Rev.0

2026-11-20。V/COMへ接続している直流入力値の照会に対し、ユーザーは2.911Vと回答。申告値として記録し、基準の精度や製品合否を推定しない。前面20V/CONF約200Vの相違はOpenのまま、測定原文と入力値の比較を独立に行う。現在の機能DCV/連続OFFは直前のユーザーログと.3 Query検証で確認。

COM7、57600bps/8N1/flowなし/終端CR。以下は一行ずつ送信し、各応答が完了してから次へ。設定後の*OPC?は復号1（HEX 310D0A）を確認。

~~~text
EXT_SEND 2000 :TRIG:SOUR IMM
EXT_QUERY 10000 *OPC?
EXT_SEND 2000 :TRIG:COUN 1
EXT_QUERY 10000 *OPC?
EXT_SEND 2000 :SAMP:COUN 1
EXT_QUERY 10000 *OPC?
EXT_SEND 2000 :TRIG:DEL 0
EXT_QUERY 10000 *OPC?
EXT_QUERY 2000 :SYST:ERR?
~~~

SYST:ERR?が+0,No error（HEX 2B302C224E6F206572726F72220D0A）の場合に、次を一行ずつ送る。非ゼロエラーやtimeout/不正応答なら先へ進まず保存する。

~~~text
EXT_QUERY 10000 :READ?
EXT_QUERY 2000 :SYST:ERR?
~~~

READ?は一回測定。返却HEXをそのまま共有し、ヘッダ/単位/指数表現を含む原文から2.911V付近かを確認する。結果へ10倍/0.1倍等のレンジ補正はしない。timeout後の自動再送やfault解除/再bindは行わない。これはユーザー操作用の手順で、作成時点でCodexから測定を送っていない。前面/CONF相違IssueをCloseしない。
