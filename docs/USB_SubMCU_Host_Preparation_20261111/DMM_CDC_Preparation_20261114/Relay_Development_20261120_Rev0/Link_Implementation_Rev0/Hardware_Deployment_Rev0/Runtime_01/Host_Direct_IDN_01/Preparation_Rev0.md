# Host単体識別デバッグ 準備 Rev.0

ユーザーのHostデバッグ指示により、現行meter-host-relay-20261120.1を変更せずに切分ける。親を電源/信号とも切離し、Host単体を3.3V USB-UARTへ接続。外部電源OFFでPC USB-Cのみ給電し、7355電源ON・Host USB-Aと7355 USB-Bを接続する。

host_direct_idn.pyは唯一の1A86:5523変換器を照合し、Hを1回送る。hのnonce/CRC/chipid/FW版/READYを照合後だけQ（*IDN?、2000ms）を1回送り、A/T/Rを記録。NOT_READY/FAULT/timeout/不正相関では停止し自動再送しない。レンジ変更・READ・NF55Gコマンド・Flash書込みなし。実行はユーザー接続完了後。

確認事実: 前回Host単体Hは16msで正しいID/版とNOT_READYを返した。その後ユーザーが7355 USB-B抜けを報告。接続復帰後の親経由試行4はTIMEOUT/AMBIGUOUS=0。推測: 親Host実配線/親GP13入力、Host側USB経路等は実フレーム未取得のため区別できない。今回Host直接で経路を分離する。既存資料/ログは保持、IssueはCloseしない。
