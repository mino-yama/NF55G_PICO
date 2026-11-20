# 親TX→Host RX入力 受動採取 準備 Rev.0

Host側外部5V/GND給電線はユーザーが接続済みと回答。実電圧は未測定。試行5はHost TX監視で0byteだったため、次は監視点をHost GP1へ移す。

外部電源OFF、Host/親のPC USB-Cは外れたまま、UART変換器TXD/VCCは未接続を維持。変換器RXDだけをHost GP0からGP1へ移す。親GP12→Host GP1とHost GP0→親GP13の信号線、共通GND、ATE接続、7355 USB-Bは維持する。Host GP1には親TXと監視用RXDが接続される。監視用TXDは接続しない。

前試行のfaultとHost sessionを持越さないため、外部電源OFFで5秒程度待って親/Hostを通常起動する。ユーザー完了後にcapture_and_ate.pyで治具ID、EXT_QUERY 2000 *IDN?を各1回実行し、COM22にはwriteせず入力線を記録。タイムアウト等で再送しない。コード/Flash変更なし、レンジ/READ/NF55G通信なし。原文の有無/CRC/ヘッダ/sessionを照合して次の切分けを決める。IssueはOpen維持。
