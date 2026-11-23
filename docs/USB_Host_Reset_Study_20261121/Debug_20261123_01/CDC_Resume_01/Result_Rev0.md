# 7355通信再開 実機確認 Rev.0

2026-11-23。ユーザー指示「7355通信再開 実行して見て下さい」に基づく、同一案件の継続試験。

## 結果

**明示IDN一回の通信成功を確認した。** HOST .23.2のREADY確認後、実ATE経由で`EXT_QUERY 2000 *IDN?`を一回送信し、期待原文32 byteと完全一致した。

```text
ADC Corp.,7355,246410099,  A02\r\n
```

| 項目 | 確認結果 |
|---|---|
| 親実機／ATE／HOST受動採取 | COM6／COM7（57600bps）／COM22（115200bps） |
| HOST個体／FW | BFCF2EDB84B0B37F／meter-host-relay-20261123.2 |
| HOST起動nonce | CBFA8C2C4F42C7BA。前回RST後と同じ世代 |
| HOST状態 | 管理INFOと通常HELLOの両方でREADY |
| 親nonce | f2caeb2e46c95f01。前回と同じruntimeを維持 |
| 親からの実送信フレーム | I／H／Q。Qは1件、Sなし |
| HOST受信確認 | i／h／A／T／R。Qのrequest=1、session一致 |
| IDN応答 | 32 byte、CRLF込みで期待原文と完全一致 |
| 異常 | 親frame error0、stale0、受動decode error0、親fault=false |
| 付帯確認 | NF55G送信試行0、Cache metadata不変 |

[結果JSON・各応答原文](result.json)、[HOST raw](host.raw)、[親RAM診断](parent.log)、[PC実行ログ](execution.log)。

## 実施方法と終了状態

前回の親app／nonce／fault／管理連番を保持し、閉じていた測定器PIO transportだけを再開。実機に配置済みのparser／scheduler／linkを使用し、PCから実ATE入口にINFOとIDNを送信した。RAM上のtransport wrapperで実際に受け付けた送信byteを記録し、COM22でHOST TXを受動採取した。診断採取による追加処理時間はある。

親／HOSTの再起動、fault解除、Flash書込み、7355へのRESET／設定／READ、Query再送は行っていない。NF送信は前回から継続したRAM guardで禁止・計数した。

12秒の有限診断終了後、親はREPL停止、PIO4/5停止・GP12/13入力化。親の同じappと確立済みsessionをRAMに保持し、HOSTは同じ起動世代の通常FWで稼働。PC採取プロセス終了後はCOM6／7／22を解放。次回も親の新nonceを不用意に生成せず、実機状態を確認して継続する。

## 判定の範囲・未確認事項

確認事実は、前回RST後の同一HOST起動世代でREADYと新規IDN応答が一回成立したこと。前回NOT_READYからREADYへ変化した物理的理由・時点は今回観測しておらず、原因を断定しない。

連続測定、レンジ設定／読戻し、USB受信0 byte問題の根本原因、旧機器応答境界、既存FAULT条件のRST、NF55G／SD等との複合負荷、量産復旧は未受入。製品PASSやIssue Closeとはしない。コード／FW変更なしの実機試験であり、全Unit再実行は行っていない。直前の修正版回帰は全476件成功。
