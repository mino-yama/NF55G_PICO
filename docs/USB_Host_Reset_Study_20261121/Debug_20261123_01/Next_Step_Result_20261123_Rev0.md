# 7355連続取得・NF55G/SD/RTC共存 結果 Rev.0

2026-11-23。ユーザー「次へ進めて下さい」に基づき、既定の設定確認→単発READ10回→50回共存試験を実行した。同一NF55G Pico試験治具案件の継続。

## 結果

**単発READ10/10と、READ＋NF55G D1＋SD＋RTCの共存50/50が成功。** 同じ親runtime／HOST起動世代を保持し、再起動・fault解除・機器要求の再送なし。今回の範囲は正常通信とログの有限試験であり、製品合否・精度・量産受入の判定ではない。

| 確認項目 | 結果・証拠 |
|---|---|
| 個体／FW | 親69f7d45962cfdfad、HOST BFCF2EDB84B0B37F／.23.2、7355 SN246410099／A02 |
| 起動世代 | 親f2caeb2e46c95f01／HOST CBFA8C2C4F42C7BA。前回IDN成功時と同じ |
| 設定 | DCV、AUTO ON、連続OFF、IMM、トリガ1、サンプル1、遅延0。ATEが同じAUTO ONを明示し読戻し1。固定レンジ値は指定していない |
| 単発READ | 10/10成功。9.62123～9.62125V、ATE応答609～703ms。設定前後一致、SYST:ERRは前後0。[原文・全記録](CDC_Read_01/result.json) |
| NF事前確認 | STATUS_REFRESH一回成功、Command/Response Retry0 |
| 共存 | 50/50のREAD＋D1＋Retry/SD/RTC/drop照会が所定順序で成功。[burst結果](CDC_Coexist_01/Burst_01/result.json) |
| 共存中の測定原文 | 9.62118～9.62122V。入力の固定性・測定精度は未評価 |
| 共存burst時間 | 6応答全体で656～1078ms、中央値921.5ms。READ単独の応答時間とは区別 |
| HOST相関 | READのQはrequest32～81、A/T/R各50、同じsessionで相関一致。親frame error0／stale0 |
| NF実送信制限 | 事前1＋共存50のD1計51件とACK51件のみ。NAK0、他コマンド0。RAM guardでD1以外を拒否、違反0 |
| Cache | D1取得によりSTATUSがVALID・source D1。他Cache metadata不変。測定値を校正Cacheへ自動登録していない |
| SD timing | 記録853件、flush27回。通信中write／flush試行0 |
| 終了時 | Logger停止、drop0、Queue0、SD OK、RTC OK、外部fault=false |

全体は[実機結果](CDC_Coexist_01/result.json)、[PC検証](CDC_Coexist_01/verification.json)、[親診断](CDC_Coexist_01/parent.log)、[HOST raw](CDC_Coexist_01/Burst_01/host.raw)を参照。計測のためRAM transport／NF送信／SD writeに観測wrapperを追加した条件であり、追加処理時間はある。

## SD認識不一致の切分け

事前確認で試験用sinkは`mounted=false／MOUNT_ERR／VFS_MOUNT／OSError(1,)`。明示SD_REINIT一回も同じ結果だった。一方、VFS mount一覧には`/sd`のVfsFatがあり、既存BANK_A/Bと容量を読めた。[再認識前後](CDC_Read_01/sd_reinit.log)、[mount一覧](CDC_Read_01/sd_vfs_probe.log)。

通信idle・Logger停止・ファイル未openを確認して既存`/sd`mountを解放し、現在のsinkで明示SD_REINITを実行したところ`OK／mounted=true／READY`へ復帰。[復帰記録](CDC_Read_01/sd_mount_recovery.log)。

確認事実は、実VFS mountと試験用sinkの認識不一致、および整理後の復帰。通常起動で作成したappを中断後、前回RAM試験で別appを生成した経緯との整合がある。SDハード故障や量産起動処理の根本不具合とは断定しない。今回、原典／本番コード／FW／Flashの変更、SDフォーマットは行っていない。

## CSV読戻し

- 実機: `/sd/BANK_A/20261123_123053.csv`
- PC保存: [20261123_123053.csv](CDC_Coexist_01/20261123_123053.csv)
- 55,879 byte。SHA-256 `20d699d9d2ba6f9eb6db15b89ab4035f0aa9dce1393057f2613eaf7feaf854a0`が実機とPCで一致。
- ヘッダ＋853記録、全14列、列崩れ0。D1 TRANSACTION50件はすべてOK／Retry0。READ RESULT50件の完成原文を確認。
- [CSV／wire検証結果](CDC_Coexist_01/verification.json)。SD上の元ログは保持。

## 変更・検証・残事項

追加は実機試験用script、raw、CSV、結果文書と進捗記録。本番src／HOST FWの変更なし。今回の実機・CSV・wire検証を実施し、全Unitの再実行は行っていない。直前修正版の回帰は476件成功。

終了時は親REPL停止、PIO4/5停止・GP12/13入力化、NFのD1限定guardを元の送信禁止guardへ復元。親appと外部sessionはRAMに保持、HOSTは同じ.23.2通常起動、COM6/7/22は解放。

次工程は採用順序に沿うADC測定取得・CacheへのATE接続。ただし正式ATE契約、AD/ARとA/B対応等の未回答は推測しない。既存USB受信0byte問題の根本原因、NOT_READYからREADYになった理由、任意の遅着応答境界、QR実機統合、長期安定性は未確認。今回の成功を根拠に既存Open IssueをCloseしない。
