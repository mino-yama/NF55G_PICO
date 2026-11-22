# USB CDC応答再確認 2026-11-21 Rev.0

ユーザーの「7355スリープ？」との指摘を受け、識別要求を再確認した。

## 確認事実

- COM7/57600/8N1の治具`*IDN?`は正常応答。
- `EXT_QUERY 2000 *IDN?`一回に対し`ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`＋CR。
- 同時に受動監視したCOM22/115200/8N1は0 byte。両ポートは解放済み。
- 測定・設定・再起動・Flash変更・NF55Gコマンドなし。

原記録: [ATE応答](../../../temp/usb_cdc_resume_20261121/recheck_150855/result.json)、[Host受動採取](../../../temp/usb_cdc_resume_20261121/recheck_150855/host.raw)。

## 解釈と未確認事項

直前のTIMEOUT後、今回のRECOVERY_REQUIREDとHost無受信は、現行PCソースで親リンクがfaultを保持し、追加要求をHostへ送る前に拒否する経路と整合する。実機ソースの照合は未実施。

今回7355自体の応答は取得できておらず、スリープ状態かどうかは未確認。RECOVERY_REQUIREDを7355のスリープの証拠とは扱わない。通信リンク復帰後に新しいIDN応答を取得する必要がある。ソフトRESET/WDT等は保留方針を維持し実装していない。IssueはCloseしない。
