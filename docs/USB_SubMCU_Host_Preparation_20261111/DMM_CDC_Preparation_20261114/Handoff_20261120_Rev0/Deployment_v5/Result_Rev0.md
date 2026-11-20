# 評価FW.5 配置結果 Rev.0

2026-11-20 JST。ユーザーが指定の接続分離・BOOTSEL準備を完了と回答したため配置を実施。

- 書込み前info: chipid 0xbfcf2edb84b0b37f、boot type bootsel、旧版meter-host-voltage-test-20261120.3、Flash 2048K。
- .5 UF2のSHA-256をbuild manifestと照合、一致。
- 現行.3の全Flash 2,097,152 byteをsave -a -vで退避しFlash照合OK。SHA-256: 2a6e900ec1153ad73dd0b2d12d820b3465f8cc16e9c635954c0467a40d8abcd5。
- load -vで.5を書込み、Flash verify OK。
- 書込み後infoで版meter-host-voltage-test-20261120.5、同じchipid、boot type bootselを確認。
- rebootは行わず、測定FW起動・7355へのSCPI送信・測定は今回未実施。前面20VとCONF約200Vの相違はOpen維持。

## 証跡

[書込み前info](before_info.log)／[旧Flash退避・照合](backup_verify.log)／[書込み・照合](load_verify.log)／[書込み後info](after_info.log)／[配置manifest](Deployment_Manifest.json)

## 次の操作

PC USB-Cを外し、Hostが無給電の状態で7355 USB-B→Host USB-A、GP0 TX→SH-U05A RXD、GND共通を接続する。変換器TXD/3V3/5V0はHostへ接続しない。SH-U05AをPCへ接続し、Hostの外部5VはまだOFFにする。UART採取を先に開始してから外部電源を投入し、.5起動・CDC・CONF読戻しと前面表示を同一試行で記録する。

コード変更なし。実行検証はFlash退避照合・書込み照合・実機metadata読取り。ソフト回帰は直前の382件成功を継承し、今回は再実行していない。
