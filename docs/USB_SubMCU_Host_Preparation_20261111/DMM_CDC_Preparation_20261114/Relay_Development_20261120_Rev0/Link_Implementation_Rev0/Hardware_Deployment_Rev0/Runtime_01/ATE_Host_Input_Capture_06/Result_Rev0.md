# 親TX→Host RX受動採取 試行6 結果 Rev.0

2026-11-20。ユーザーが監視RXDをHost GP1へ移し外部電源を再投入した完了通知後に実行。

## 確認事実

COM7の治具*IDN?はNF55G_PICO_FIXTURE,Rev.0+CRを返した。EXT_QUERY 2000 *IDN?はERR:EXT_TIMEOUT:AMBIGUOUS=0+CR。COM22 RX専用監視でHost GP1入力線の75byteを取得し、X1 CRC/形式が正常なHをdecodeできた。request=0、mode=0、timeout=0、payload空、session=F7DC7727C218D7410000000000000000。捕捉例外なし。

親のH送信を監視点で確認できた。Host内部UARTが実際に受理したか、Hostの返答送出やその受信はこの一方向監視だけでは分からない。Qは監視線に存在せず、7355への識別送出は未確認。自動再送/レンジ変更/READ/NF55G通信/Flash変更なし。COM7/22は解放済み。

## 推測と未確認事項

HostはPC USB-C給電・USB-Bなし冷起動でH応答し、その後USB-B接続でREADYと7355識別に成功した。一方、USB-B接続済み状態での試行では無応答だった。起動時USB接続順序と給電条件が異なるため、原因を接続順序や電源に断定しない。外部給電でもUSB-Bなし起動→後接続で比較する。給電線はユーザー接続済み回答、実電圧は未測定。

次はUSB-Bを外して親/Hostを外部電源から冷起動し、同じGP1受動監視のままATE識別/照合を各1回行う準備。機器未接続なのでh/NOT_READYを受けた場合のATE応答ERR:EXT_LINK_NOT_READYも切分け証拠として扱い、受入成功とはしない。IssueはOpen維持。

[ATE送受信](Capture_Result.json)／[Host入力線のdecode結果](Host_RX_Capture.json)／[入力線原文](host_rx.raw)。
