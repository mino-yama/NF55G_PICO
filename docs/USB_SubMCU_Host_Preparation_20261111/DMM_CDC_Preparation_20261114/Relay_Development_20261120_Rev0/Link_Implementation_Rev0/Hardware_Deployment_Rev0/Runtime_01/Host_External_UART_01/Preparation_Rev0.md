# 外部給電・PC UART直結 比較準備 Rev.0

直前の外部給電・親経由試行7はHost GP1監視で正常Hを捕捉したが親はTIMEOUT。ユーザーはHost実電圧5.0V/3.2Vと回答。次は外部給電/USB-B未接続を維持し、要求送信元をPC UARTへ変える。

外部電源OFF後、親GP12→Host GP1とHost GP0→親GP13の信号線を切離す。変換器TXD→Host GP1、RXD→Host GP0、GND→Host GND。変換器の電源線は接続しない。HostのPC USB-Cと7355 USB-Bは未接続のまま、外部電源から起動する。

完了通知後にhost_hello_diagnostic.pyを一回実行。COM22 1A86:5523、115200/8N1、H一回のみ、正しいID/FW/nonce/CRC/h状態を照合。機器未接続なのでNOT_READYも照合成功として扱う。Q/SCPI/レンジ/READ/Flash変更/自動再送なし。過去の結果は保持しIssueはOpen維持。
