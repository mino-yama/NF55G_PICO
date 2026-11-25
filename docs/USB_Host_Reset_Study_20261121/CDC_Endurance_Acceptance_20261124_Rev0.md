# USB HOST CDC 1日耐久受入基準 Rev.0

日付: 2026-11-24  
状態: ユーザー承認済みの受入基準。400試行の実機耐久試験は未実施。

## 目的と範囲

7355 USB HOST CDC経路を、実運用に近い固定電源・固定配線条件で反復確認する。ATEが選択した測定レンジを使い、Pico/Hostはレンジを選択・最適化・独自補正しない。

本基準の合格はUSB HOST CDCとTEST_START～TEST_ENDログ経路の限定耐久受入を示す。NF55G全機能、校正精度、製品PASS、QR Host、電源投入順、配線接続/切断、ホットプラグ、全量産負荷の合格を意味しない。

## 合格基準

- 一連の実機試験を1つの24時間枠内で実施し、TEST_STARTからTEST_ENDまでの完了試行を400セット記録する。
- 7355、測定器Host、親Picoを試験開始から終了まで再起動・リセット・電源再投入しない。USB-Bの抜差し、ATE/Host接続の切断も行わない。
- 各セットでATE選択済みのレンジを維持し、7355の設定コマンドによるレンジ変更を試験ランナーから送らない。`:CONF?`は原文を記録するが、特定の公称レンジ値との一致を合否条件にしない。
- ATEはREAD?応答の値/計器エラーを判定する。正常な完全応答としてATEへ届いたエラー値・OL・非採用値だけを理由に、Pico/Hostがfault停止してはならない。ATEが再読取を選択した場合、明示した次のREAD?を新規要求として受け付け、対応する完全応答を返す。
- Pico/HostはREAD?を自動再送しない。各要求/応答の終端、長さ、原文、request/session相関を記録する。ATEが明示発行した複数READ?は別要求として対応させる。
- 400セットすべてでTEST_STARTとTEST_ENDがOKであり、各READ?要求に対して完全で対応の取れたATE応答が返る。`:SYST:ERR?`の値とREAD数値の製品判定はATEの規則で記録し、値が非ゼロ/OL/ATE不採用であることだけではCDC受入失敗にしない。
- 各TEST_END後の`PICO_SELF_CHECK?`に`TEST_LOGGER=OK`と`TEST_LOG_DROP=OK`を含み、`SD_STATUS?=OK`、累積`LOG_DROP_COUNT?`の増加が0、`COMM_STATUS?=OK:state=IDLE`である。
- 開始時と終了時のHOST_INFOでHOST個体/FWを照合し、boot nonceが不変である。中間確認を行う場合も管理INFOのみとし、通常CDC Queryの順序を乱さない。
- 完了した400件の試行CSVが個別に保存され、試行ID・時刻・ATE要求/応答・READ原文と対応する。PC回収後に行数、列数、ファイル数、SHA-256を照合する。
- timeout/AMBIGUOUS、応答欠落・破損・要求との不対応、Pico/Hostがエラー値だけで停止して次の明示要求を処理できない状態、ログ異常/drop、HOST/親の再起動・nonce変化、USB切断が発生したら停止し、量産適合とは判定しない。成否不明コマンドは再送しない。完全応答として返った計器エラー/READ値の判定・再読取要否はATEが決める。

## 1セットの手順

試験前にATEが対象7355と入力条件を確認し、使用するレンジを選択・設定する。選択レンジと`:CONF?`原文を開始記録へ保存する。ATEが指定する既知入力が当該レンジ内であることを確認する。Pico/Host側でレンジ値を置換しない。

各試行は次の範囲を1セットとする。各ATE応答を完全に受信してから次のコマンドを送る。

1. `TEST_START` → `OK`
2. `EXT_QUERY 10000 :READ?` → 値を含む応答原文を記録し、ATEが判定
3. ATEが再読取を選ぶ場合は、新しい`EXT_QUERY 10000 :READ?`を明示発行し、各応答を個別に記録。Pico/Hostによる自動再送はしない
4. `EXT_QUERY 2000 :SYST:ERR?` → 原文を記録し、計器エラーの扱いはATEが判定
5. `TEST_END` → `OK`
6. `PICO_SELF_CHECK?`、`SD_STATUS?`、`LOG_DROP_COUNT?`、`COMM_STATUS?`を照会して終了条件を確認

新しいレンジ選択はATE側の工程で行い、READ間にPico/Hostから自動設定しない。計器エラー値を受けてもATEが続行/再読取を選択できる場合は、同じTEST_START～TEST_END内で明示要求を続ける。通信timeout/AMBIGUOUSや応答相関不明では続行・再送しない。CDC/Logger受入失敗時は後続セットへ進まず、失敗時刻・要求原文・応答raw・試行CSVを保全する。

## 実施前後の記録

開始前に記録する項目: 7355 IDN、ATE選択レンジとCONF原文、入力源の設定値、配線/電源構成、親Pico ID、Host ID/FW/boot nonce、開始日時、SD/drop状態。

終了後に保存する項目: 全ATE TX/RX raw、HOST UART raw、400試行CSV、READ値の原文、各セットの開始/終了時刻と所要時間、各TEST_LOGGER/TEST_LOG_DROP、総drop、SD状態、親/Host nonce、試験全体の終了コード、PC回収CSVとSD原本のhash照合。

## 現在の事前実績

- 2026-11-24、7355 IDN反復200/200成功。各32byte完全一致、HOST A/T/R各200、E=0。これはIDNのみの通信反復であり、TEST_START/END耐久試験ではない。
- 2026-11-24、TEST_START付き単発測定を1セット実施。ATE指定`:SENS:VOLT:DC:RANG 0.2`後のCONFは約2V相当だったが、ユーザー決定に従いレンジ相違を不合格理由とせず、約40mV入力で単発READ `+0040.154E-03`、機器error=0を確認。TEST_END、TEST_LOGGER、TEST_LOG_DROP、SD、drop、COMM_STATUSは正常。
- 2026-11-24、実C HOST/親リンク回帰`test_error_valued_read_response_does_not_block_next_explicit_read`を追加。overrange相当の完全応答を原文で返し、ATEの次の明示READが成功、Host faultなしを確認。Host Unit/Mock全528件成功。実7355のエラー値後続READは未確認。
- 400セット/24時間、無リセットの実績はまだない。したがって量産適合判定は保留。
