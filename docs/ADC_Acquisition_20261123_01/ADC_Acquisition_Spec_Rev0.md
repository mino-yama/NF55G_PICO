# ADC取得・測定Cache ATE接続 Rev.0

2026-11-23。同日ユーザーが取得／照会の以下の案を採用。AD/AR・QR/SSは本契約の対象外。開始時の基準commitは258b800、HOSTは.23.2、既存有限共存試験まで成功済み。

## ATE入口

| 要求 | 内容 | 成功応答 |
|---|---|---|
| `CAL_MEASURE <対象> <A\|B> <期限ms> :READ?` | 現在のTEST試行に対する明示取得。期限1～10000ms | `OK:CAL_MEASURE:<取得ID>` |
| `CAL_MEASUREMENT? <取得ID>` | 保存値と校正換算候補の照会。機器／NF55G送信なし | 下記 |

対象はDISCHG_I／BATT_CHG／BATT_Vのみ。点はA／Bであり、ADのPoint1/2対応を意味しない。SCPI本文は`:READ?`（同義の`READ?`も許可）のみに限定し、任意の数字Queryを取得に流用しない。設定・レンジ・動作条件は従来のEXT_SEND/EXT_QUERYでATEが決める。取得自身は設定を変更しない。

取得IDは`<試行世代8桁HEX>-<取得連番8桁HEX>-<対象>-<点>`。例: `00000001-00000001-BATT_V-A`。異なる試行／対象／点／取得連番の値は参照できない。TEST_STARTが成立していない取得はNO_ACTIVE_TRIALで拒否。

照会応答:

```text
OK:CAL_MEASUREMENT:<取得ID>:<対象>:<点>:<測定値文字列>:<測定単位>:<校正候補文字列>:<校正単位>:<応答原文HEX>
```

電流対象はmV／A、BATT_VはV／V。応答原文HEXは7355から返ったV表記のCRLF付き原文そのもの。電流対象の測定値文字列は、元V値を厳密に1000倍してmVへ正規化した値。50A/50mVシャントに従って同じ数値をAの校正候補として返す。符号・仮数の桁は保持し、float変換・丸め・絶対値化を行わない。

例: 原文`-001.8500E-03\r\n` → 測定値`-001.8500E+00 mV` → 校正候補`-001.8500E+00 A`。同じ原文をBATT_Vで取得した場合はVのまま。

## 取得状態機械と保護

1. parserで対象・点・期限・READ本文を検証する。
2. Cache.beginで同点の旧値を先に失効し、試行／取得tokenを確保する。
3. 7355 adapterが`:SENS:FUNC?`を送信し、完成応答`"VOLT:DC"`を確認する。
4. 残期限でATE指定READを一回だけ送信する。機能照会とREADで単一の総期限を共有し、再送しない。
5. 完成した単一DCV応答を検証・正規化し、同じtokenへcompleteする。ATEへ取得IDを返す。

FAULT／切断／timeout／取消／試行世代変化／形式不正／OL等では取得を失敗にし、旧値へ戻さない。通常リンク側のambiguousとfaultは既存規則に従って保持する。取得中は一つの外部linkを専有し、別取得・通常EXT・HOST管理・TEST_START/END等の割込みをBUSY拒否する。2段階の間も通信busyを保持し、SD write/flushを実行しない。

TEST_END成立、再START成立で取得済み／未完の値を失効する。古い応答・重複・別試行の完了を採用しない。照会はCacheのみでありRefresh／測定を開始しない。取得・照会からAD／AR／SS／FUを送信しない。校正候補の返却はATEによる採用・製品PASS・NF55Gへの書込み完了を意味しない。

## 7355固有の検証根拠

保存済み英文取扱説明書§6.8.2／PDF p.120（誌面6-26）を確認。6½／5½桁の符号付き仮数・指数形式、DCVの出力指数-03/+00、OLの±9.999999E+37／±9.99999E+37、scaling OVERの指数+36、dB/dBm errorの指数+35を確認した。これらは数値構文を満たすが校正Cacheへ採用しない。[原典抽出](Manual_Evidence/page_120.txt)、[原典hash](Manual_Evidence/manifest.json)。

7355固有のcommand／数値形式は`Meter7355Voltage`へ閉じる。共通Cache／NF55G通信仕様へ持ち込まず、他機種には対応adapterと検証を追加する。

## 失敗応答

基本形式は`ERR:CAL_<理由>`。ARGUMENTS、ASCII、TIMEOUT、MEASUREMENT_TARGET、MEASUREMENT_COMMAND、ACQUISITION_ID、NO_ACTIVE_TRIAL、DISABLED、BUSY、METER_FUNCTION、MEASUREMENT_VALUE、MEASUREMENT_OVERRANGE、RESPONSE_FRAME、MEASUREMENT_INVALID、STALE、CANCELLED等。外部linkの失敗は既存理由とAMBIGUOUSを保持して、例`ERR:CAL_TIMEOUT:AMBIGUOUS=1`と返す。共通schedulerのBUSYは既存`ERR:BUSY`の場合がある。取消は内部APIで、専用ATE取消コマンドは今回追加しない。

同点の再取得が失敗した後、旧取得IDへの照会もMEASUREMENT_INVALID。文法不正・BUSYで開始拒否された要求は送信／取得更新を行わない。

## 検証と残事項

独立adapter/core15件、実C HOST／親の追加6件を含め、Host Unit／Mock全497件成功（16.409秒）。[全回帰](Host_Mock_Rev0.log)。形式・単位・OL・期限・取消・試行境界、3対象×A/B、Cache照会の無送信、NF送信0を確認。実機結果は後続記録へ追加する。

AD/AR正式契約、小数読戻し、A/BとP1/P2、VALUE8／丸め／極性、QR/SS変換は未回答のまま。CAL-EXT-02は取得／照会契約の決定を追記するがCloseしない。
