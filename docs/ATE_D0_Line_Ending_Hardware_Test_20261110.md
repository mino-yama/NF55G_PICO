# D0要求とATE終端の実機確認

日時: 2026-11-10 08:08:48～08:09:26 JST

## 条件

- 開発機のATE UART COM20、115200bps、8N1。既存配置プログラムを使用し、コード変更・再配置なし。COM6 REPLは使用していない。
- ATEからNF CMD D0を要求する正式入口は `DATA_REFRESH`。文字列 `D0` 自体も比較対象として送信した。NF55G側のバイナリフレーム終端を変更する試験ではない。
- 全48送信、送信開始間隔の最短113.966ms。通常コマンドは送信後約1秒観測。応答なしもその観測時間内の結果として記録した。
- CR単独は10回送信。2～10回目の送信開始間隔は約114～134ms。設定変更、制御、CLEAR、RTC設定は行っていない。
- [全送受信記録（HEX・応答・間隔）](ATE_D0_Line_Ending_Evidence_20261110.json)。実行スクリプトは `temp/dev_acceptance_20261109_run01/d0_ending_check.py`。

## 実機結果

表の「次のD0要求」は `DATA_REFRESH<CR><LF>` を意味する。

| 試験入力 | 応答 | 次のD0要求 | その次のD0要求 |
|---|---|---|---|
| `D0<CR>` | なし | `ERR:FRAME` | `OK` |
| `D0<LF>` | なし | `ERR:FRAME` | `OK` |
| `D0<CR><LF>` | `ERR:UNKNOWN_CMD` | `OK` | `OK` |
| `DATA_REFRESH<CR>` | なし | `ERR:FRAME` | `OK` |
| `DATA_REFRESH<LF>` | なし | `ERR:FRAME` | `OK` |
| `DATA_REFRESH<CR><LF>` | `OK` | `OK` | `OK` |
| CR単独を10回定期送信 | 全10回なし | `ERR:FRAME` | `OK` |
| 空の `<CR><LF>` | なし | `OK` | — |
| `DATA_REFRESH<CR>` の後、約0.3秒以上空けて `<LF>` | CR時点ではなし、LF後 `OK` | `OK` | — |

基準確認のDATA_REFRESHはOK。DATA CacheのBATT_VOLT?は開始・終了とも0.003を返した。今回NF生フレームの別採取・BCC再検証は行っておらず、D0成功はATE応答とCache Queryで確認した。

終了時: `COMM_STATUS? = OK:state=IDLE`、`RETRY_COUNT? = OK:cmd=0,rsp=0`、`SD_STATUS? = OK`、`PICO_SELF_CHECK? = OK:ATE_UART=OK;NF55_UART=OK;RTC=OK;LOGGER=OK`。LOG_DROP_COUNT?は開始・終了とも0。最後に空CRLFで受信状態を整え、正常応答を確認してCOM20を解放した。

RTCの自己診断OKは電池による電源断保持確認を意味しない。今回TEST_STARTでCSV試験セッションは開始していない。CR待ち中のSD書込み滞留・長時間影響は未測定で、終了時SD正常／破棄0から影響なしとは断定しない。

## 結果からの処置案（未決定）

1. ATEがCRLFを保証できる場合: コマンドは必ずCRLFで送信し、空送信もCRLFまたは送信しない運用とする。今回この組合せは正常だった。
2. CR単独の定期送信が必須の場合: 現行Pico処理では次の正常要求を1件失うため、空状態のCRを無害に扱う修正を検討する。正規コマンドのCRLF分割到着を維持する回帰確認が必要。
3. CR／LF単独もコマンド終端として使う場合: 現行CRLF限定仕様の変更となるため、受理する終端と空行の扱いを先に確定する。

推奨は、ATE側がCRLFを保証できるかで1または2を選ぶこと。今回の結果だけで3へ拡張する必要性は確定しない。自動再送を恒久処置とはせず、終端の扱いを決める。ATE-EOL-01はOpenを維持し、実装修正は未着手。
