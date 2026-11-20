# 起動前からの親TX監視 準備 Rev.0

外部電源OFFのまま親TX GP12→Host GP1、Host GP0→親RX GP13、共通GNDを戻す。監視変換器RXD→Host GP1、GND→GND、TXD/VCC未接続。Host PC USB-C/7355 USB-Bは未接続。ATE ELECOMは接続を維持。

ユーザーが配線完了（まだ電源OFF）を通知後、capture_and_ate.pyでCOM22受動監視とCOM7待受を開始する。ready/WAITINGを確認して外部電源ONを案内。ユーザーON通知後にpower_on.confirmedを作り、治具ID/EXT_QUERY 2000 *IDN?を各1回送る。待機上限300秒、自動再送なし。起動時からHost GP1の全原文を保持する。USB未接続なのでNOT_READY応答を期待するが、成否は観測から判断する。
