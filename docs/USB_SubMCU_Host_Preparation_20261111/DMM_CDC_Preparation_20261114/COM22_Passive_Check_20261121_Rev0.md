# COM22 Host稼働確認 2026-11-21 Rev.0

ユーザー指示によりCOM22を115200bps/8N1、DTR/RTS OFFで受信専用監視。10.063秒で受信0 byte。送信、リセット、FW変更なし。ポートclose済み。

[採取条件・結果](../../../temp/usb_cdc_resume_20261121/com22_passive_151736/result.json)、[受信raw](../../../temp/usb_cdc_resume_20261121/com22_passive_151736/host.raw)。

現行PCソースのrelay_main.cはGP0/GP1をX1 UARTとして使い、起動メッセージ/周期heartbeatを出さない。relay_host.cのhello()は受信H要求に対して個体ID/版/状態を返す。このため受動監視0 byteだけではHostの稼働・停止のどちらも断定できない。親側は直前確認で外部要求をRECOVERY_REQUIREDとして拒否しており、有効なH要求をHostに到達させた証拠はない。

先のpicotool成功は「通常起動指令の成功」の確認であり、UARTでのアプリ稼働/READY確認とは区別する。COM22は既存のHost TX監視接続として扱い、TX配線/駆動競合が確認できていないためCOM22からHostへの直接要求は行っていない。Hostの生存確認には有効な要求と新応答の捕捉が残る。7355接続・スリープも未判定。

コード・仕様変更なし。Host/Mock再実行なし。関連IssueはOpen継続。
