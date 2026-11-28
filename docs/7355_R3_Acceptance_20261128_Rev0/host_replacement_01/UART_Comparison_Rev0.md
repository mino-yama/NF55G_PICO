# 交換HOST・PIO／ハードウェアUART比較 Rev.0

2026-11-28。交換後も情報無応答が続くため、固定基板・コネクタとHOST FW .25.2を変更せず、親のPIO依存を分離する追加試験を実施した。

## 実施と確認結果

開始時に親保守COM6は未列挙だった。ユーザーが親保守USBを接続後、試行・Logger停止、通信非busy、ATE要求・送信待ちなしを確認して実施した。初回の`hardware_uart_probe_01`はCOM6未接続により実機操作前に停止した。

保守USBからの有限診断で、親のPIO TX/RXを一時停止し、UART0を115200／8N1・GP12 TX／GP13 RXへ一時割当てした。ATE GP0/GP1はこの間だけ入力化し、情報要求Iフレーム1件だけを送信。NF55G用UART1には触れていない。

- 対象個体IDは`73AD3A60D10514E9`、管理要求番号3。CRC・個体ID・challengeはPC側で独立デコードして一致確認した。
- 全141バイトを書込み、flush後1,500 msの受信は0バイトだった。[送受信・復元記録](hardware_uart_probe_02/result.json)、[要求デコード](hardware_uart_probe_02/decoded_request.json)。
- finallyでUART0をATE用57600／8N1・GP0/GP1・RX buffer4096へ復元し、GPIO制御／パッド値、PIO IRQ、TX/RX activeを元へ戻した。記録されたGPIO CTRLはGP0/1=2、GP12=7、GP13=5。
- 同じ試験プロセスの最後のATE確認は、COM7が他アプリに占有されており実行できなかった。ユーザーの接続解除後に別の確認を実施し、治具IDN、IDLE、SD OK、drop0の正常応答でATE復帰を確認した。[復帰後ATE原文](verify_after_hardware_uart_01/normal_ate.json)。通常PIO経由のHOST_INFOは引き続きtimeout。

## 解釈と残確認

PIOを介さないUART照会でも応答は得られず、親PIOドライバだけが原因とは絞れない。送信レジスタへの書込みと要求構文は確認したが、HOST受信端での電気信号や通常給電時のHOST内部起動を今回の試験だけで確定しない。

次は交換HOSTの外部給電時の5V／VSYS―GNDと3V3―GNDの実測を依頼した。過去のPC USB単独給電での診断と、現在の通常外部給電は分けて扱う。HOST故障・断線・給電不良のいずれも現時点で断定しない。

新規スクリプトは`scripts/probe_meter_hardware_uart_20261128.py`。有限RAM試験と設定復帰の実機照合、要求のCRC／ID／challenge独立検査を実施した。保存済み製品コード・HOST FW・配線指定は変更していない。R3測定・400セットは未開始。
