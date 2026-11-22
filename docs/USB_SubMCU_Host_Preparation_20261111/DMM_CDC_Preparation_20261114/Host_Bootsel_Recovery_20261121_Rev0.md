# USB CDC Host BOOTSEL確認・通常起動 2026-11-21 Rev.0

## 確認事実

ユーザーよりFW更新後にリセットされていない可能性の指摘があり、picotoolによる実機照会を実施した。

- `picotool info -a`は対象chipid `0xbfcf2edb84b0b37f`、Flash版`meter-host-relay-20261121.1`、`boot type: bootsel`を返した。通常アプリ未起動だったことを確認。
- 直前まで参照した「.21.1未配置」の既存資料と実機状態が食い違う。今回の作業ではFW書込みは実施していない。いつ・どの手順で.21.1が配置されたか、配置時の退避/verifyは未確認であり、記録が見つからないことから未実施とは断定しない。
- `picotool reboot --ser BFCF2EDB84B0B37F`を実施し、`The device was rebooted into application mode.`を受信。
- 続いてCOM22を受動採取し、COM7から`EXT_QUERY 2000 *IDN?`を一回送信。ATEは`ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`、COM22は0 byte。
- 両COMは解放済み。親Picoの再起動、機器設定/READ、NF55Gコマンド、Flash書込みなし。

[通常起動後のATE原記録](../../../temp/usb_cdc_resume_20261121/after_host_boot_151054/result.json)、[Host採取](../../../temp/usb_cdc_resume_20261121/after_host_boot_151054/host.raw)。picotool照会・rebootの出力は今回セッションの実行結果で確認し、上記へ転記した。

## 解釈と残確認

HostがBOOTSELのままだったことは、通常UART応答が得られない状態の説明と整合する。7355のスリープを確認したものではない。

Host通常起動後も親側fault保持による受付拒否と整合する応答が続いており、Host起動指令成功だけでCDC復帰完了とはしない。Hostの稼働応答/READY、実行版のUART照合、7355の新IDNは未取得。親Picoの通信状態を既存手順で復帰し、新規HELLO/READY/IDNを確認する必要がある。親のPC USB保守COMは現在の列挙に存在せず、このセッションでは操作していない。

ソフトRESET/WDTの新規実装は保留。関連IssueはOpen継続。コード・仕様変更なし、Host/Mockテスト再実行なし。
