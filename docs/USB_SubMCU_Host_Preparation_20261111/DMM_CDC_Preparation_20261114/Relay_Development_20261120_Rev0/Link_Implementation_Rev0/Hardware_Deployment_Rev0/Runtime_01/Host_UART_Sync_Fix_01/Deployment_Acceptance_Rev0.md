# 修正版Host 配置と受入手順 Rev.0

対象はHost BFCF2EDB84B0B37F、FW .1→.2のみ。親Picoソフトは変更しない。旧版/source/採取原文/全回帰ログは同フォルダで保持。新ビルドUF2の版とSHA照合後に配置する。

1. 外部電源OFF、Hostから親TX/RX/GNDとUART変換器を切離す。Host USB-A側も未接続にする。外部5V給電線をHostから切離す。
2. HostのBOOTSELを押しながらPC USB-Cへ単独接続。PC USB-Cと外部5Vは同時接続しない。
3. 個体ID/chipid/現在版/BOOTSELをpicotoolで照合。今回の配置先に現行Flash全2MiBを別名save -a -vしhash/照合を保存。新UF2の版/hashと対象serial指定を確認してload -v、Flash verifyとafter info照合。
4. PC USB-Cを外して無給電にし、外部給電・親経由信号・共通GND・ATEを復帰。監視UARTはRXD→Host GP1/GNDのみ、TXD/VCC未接続。7355 USB-Bなしで待受後電源ONしH/h・ERR:EXT_LINK_NOT_READYを確認する。電源投入時00byteを含んでもHが受理されるか観測する。
5. 正常照合後に7355 USB-Bを接続し、READYの照合後EXT_QUERY 2000 *IDN?を1回送信。原文32byteをATE HEX応答と照合。レンジ/READは送らない。

実機結果が成立するまでIssueはOpen。timeout等を自動再送せず、fault復帰/旧機器応答排除の条件を維持する。
