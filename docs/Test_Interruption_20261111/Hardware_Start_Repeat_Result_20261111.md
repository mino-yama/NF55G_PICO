# 現行実機：10秒待機後のTEST_START再受信

実施: 2026-11-11 09:36 JST。状態: 試験完了、開発着手の判断待ち。

## 結果

TEST_START → SC → DATA_REFRESH → データ取得 → 10秒待機 → TEST_STARTの指定シーケンスを実機で実施した。2回目のTEST_STARTはERR:BUSYとなり、試行を分割しなかった。初回開始と再START拒否は同じCSVに記録された。通信busyが10秒続いていたわけではなく、再START後のCOMM_STATUS?はOK:state=IDLEだった。

採用方針の「TEST_START受付ごとの新試行・1試行1CSV」へ変更するには、試験中の再STARTを拒否する現行処理と、前試行の保存・新試行開始を変更する必要がある。今回の結果だけで開発を開始せず、ユーザー判断を待つ。SS開発は保留。

## 構成と手順

- ユーザー接続確認: 治具Pico 2 COM6、ATE COM20。
- COM6列挙: VID:PID=2E8A:0005、USB serial=69F7D45962CFDFAD。COM20はElecom USB-Serial Converter、115200bps。COM21のUSB下位マイコンには送信していない。
- COM20のID応答: NF55G_PICO_FIXTURE,Rev.0。
- 初期状態: 通信IDLE、RTC 20261111_093613、SD OK、Self Check OK、破棄0。
- 現在配置されているプログラムを変更せず使用した。配置ソースと作業ツリーのhash比較は今回未実施。
- SCの既存ATE入口はCLOCK_SYNC。送信直前の日本時間を使い、CLOCK_SYNC 261111093614を実行した。製品時刻を変更する明示操作であり、その他の設定・SSは送信していない。

| 順序 | 操作 | 実測結果 |
|---|---|---|
| 1 | TEST_START | OK |
| 2 | CLOCK_SYNC 261111093614（SC） | OK、Transaction 22ms、ambiguous=False |
| 3 | DATA_REFRESH（D0） | OK、Transaction 190ms、ambiguous=False |
| 4 | NF55_DATETIME? | 20261111_093614 |
| 5 | VOUT12? / IOUT12? / BATT_VOLT? | 11.998 / 0.056 / 0.003 |
| 6 | データ取得後の待機 | PC単調時計で10.0秒 |
| 7 | TEST_START（TEST_ENDを挟まない） | ERR:BUSY |
| 8 | NF55_DATETIME? / VOUT12? | 20261111_093614 / 11.998、明示Refreshなしで前回DATAを参照 |
| 9 | COMM_STATUS? / SD_STATUS? / LOG_DROP_COUNT? | OK:state=IDLE / OK / 0 |
| 10 | TEST_END（観測後の終了処理） | OK |
| 11 | 最終診断 | Self Check OK、TEST_LOGGER=OK、TEST_LOG_DROP=OK、SD OK、破棄0、通信IDLE |

SC／D0ともCommand Retry・Response RetryはCSV上0。測定値はPicoが返した通信値であり、外部計測値や製品PASSの確認ではない。再START後に日時が同じなのはDATA Cache参照の結果であり、製品時計が停止した証拠ではない。

## SDログ照合

- 対象ログは1本: `/sd/BANK_A/20261111_093613.csv`。同時間帯の第2ファイルはなく、同ファイル内に初回TEST_START=OKと再TEST_START=ERR:BUSYを確認した。
- PCへ256byte単位で回収し、全3578byteのSD／PC SHA-256一致を確認した。
- SHA-256: `1c4d6beaa657b972a923197a22cd86b640b12e14a846193f7874b32d9e87bead`。
- ヘッダ＋39データ行、全行14列。SCとD0の送受信4フレームはすべてBCC一致。
- 前後のQueryと再START拒否も同じCSV内にある。QRは今回入力しておらず、S/N命名・QR遅延受信・SSの検証は含まない。
- 回収はTEST_END後にCOM6のREPLで実施。SD原本は変更しない。回収後、通常アプリを再起動し、COM20のID応答を再確認して両ポートを解放した。終了診断は再起動前の証跡である。

## 証跡と変更範囲

- [ATE送受信・待機時間](Hardware_Sequence_20261111_093612.json)
- [SDとhash一致のCSV](sequence_20261111_093613_verified.csv)
- [CSV解析・NF RAW・BCC確認](Hardware_Sequence_20261111_093612_CSV_Analysis.json)
- [実機シーケンス用スクリプト](run_current_start_sequence.py)、[分割回収スクリプト](recover_sequence_csv.py)

追加したのは案件内の観測スクリプト・証跡・結果資料と、関連資料への結果参照。src／tests／firmwareの修正・配置なし。Host／Mock全体は再実行していない。TEST-SESSION-01はOpenのまま。次の開発着手はユーザー判断とする。
