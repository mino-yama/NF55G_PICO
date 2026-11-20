# 親経由7355識別中継 試行10 結果 Rev.0

2026-11-20。同期修正版meter-host-relay-20261120.2でUSB-Bなし起動照合成功後、同じ通電/配線のままユーザーが電源ONの7355へUSB-Bを接続し完了通知。

## 確認事実

COM7 ELECOM 056E:5004、57600/8N1、flowなし、DTR/RTS OFF。治具*IDN?を一回送信しNF55G_PICO_FIXTURE,Rev.0+CRを受信。EXT_QUERY 2000 *IDN?を一回送信し、313ms後に次の応答を受信した。

OK:EXT_RX:32:41444320436F72702E2C373335352C3234363431303039392C20204130320D0A

復号原文はADC Corp.,7355,246410099,  A02とCRLF、32byte。長さ/終端/機種を照合し、直前Host単体の識別原文と完全一致。任意応答のカンマ・空白を保持した。

同時にCOM22/115200 8N1のHost GP1 RX専用監視で160byteを取得。H request0（親nonce 13E65D6186A73B40、Host nonceゼロ）と、同親nonce/Host nonce7A9F5B04C141A3E8のQ request1/mode1/残期限1887ms/payload *IDN?をCRC/形式正常として確認。要求一件のみで自動再送なし。捕捉例外なし、COM7/22解放済み。レンジ/READ/NF55G通信/Flash変更なし。

## 検証範囲と残事項

PC ATE→親Pico→Host UART→7355 USB CDC→Host→親→ATEの識別中継は実機で成功した。先行の起動時00byteとH連結破棄を修正し、試行9で余分な00があっても親照合が成功、今回USB接続後の識別まで成立。

受入全項目の完了ではない。USB-B接続済みの冷起動、応答なし設定/任意文字列、切断/timeout/遅着拒否/復帰、NF55G・ATE優先/実負荷/SD timing/PIO IRQ負荷などの実機受入は残る。00byteの電気的起源も未特定。既存Issueは人間確認なくCloseしない。レンジ相違はユーザー指示により保留し、ユーザーがシリアルモニターで確認する。

コード変更なし。修正版の回帰450件成功とARM build/Flash verifyを継承し、今回は実機識別を追加確認。

[ATE送受信/原文/hash](Capture_Result.json)／[親→Host要求decode](Host_RX_Capture.json)／[ATE受信原文](all_rx.raw)／[Host入力線原文](host_rx.raw)。
