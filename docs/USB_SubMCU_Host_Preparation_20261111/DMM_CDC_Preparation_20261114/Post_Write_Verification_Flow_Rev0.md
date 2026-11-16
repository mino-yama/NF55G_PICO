# QRとDMM取得値の書込み後確認手順

2026-11-14。既存Masterに沿った確認フロー案。新規の取得Cache利用書込みコマンドは未実装、AD/ARは仕様未確定・AR読戻し未実装である。今回コード・FW・機器操作は行わない。

## 共通の流れ

1. 読取り→取得Cache保存→ATE返却→ATE確認。ATEは確認した取得値に加え、実際にNF55Gへ送る項目・補正点・単位/変換後の期待値を確認用に保持する。書込み用Cache破棄後も照合できるようにする設計案で、変換規則は未回答のまま固定しない。
2. ATEが明示的にCache利用書込みを指令する。親Picoは確認対象と同一のCache値を変換・付加し、NF55Gへ送信する。
3. Protocol応答をATEへ返す。正常な書込み完了時に使用した取得Cacheを破棄。成否不明でも関連CacheをINVALIDとし、自動再書込みしない。書込みOKは製品PASSや内容一致の保証ではない。
4. ATEが明示RefreshでNF55Gから実データを再取得する。書込み応答から読戻しCacheを作らず、個別Queryにも自動Refreshをさせない。
5. ATEが個別Queryで新しい読戻し値を受け、保持した期待値と照合する。Picoが返すのは通信・読出し結果であり最終PASS/FAILはATEが判定する。
6. 不一致・Refresh失敗・timeoutは確認NG/不明として原文を記録する。破棄した取得Cacheを復活させず、再書込みへ進む場合は再取得・ATE確認からやり直す。
7. TEST_ENDで未使用の取得Cacheと未完了要求を失効。書込み前期待値・送信原文・結果・読戻し・ATE判定をログ履歴へ残し、再書込み用データとは分ける。

## QRからSS書込みした場合

書込み完了 → ATEが `INFO_REFRESH`（NF55G D5）→ 更新成功後に該当 `<ITEM>?` → ATEで期待値と比較。

例: `UNIT_REV?`、`UNIT_LOT?`、`UNIT_SERIAL?`。ADU/BBUに書き込んだ場合も対応項目をQueryする。比較対象はQR原文35文字そのものではなく、確定した割当て・変換を適用した各SS項目の期待値とする。REV3桁→4byte、年/週→LOTなどの未回答規則は引き続きOpen。

SS後はDATA/INFOがINVALIDになる。INFO_REFRESH開始時も先にINFOをINVALIDにし、失敗時は古い値を使わない。FW_REVISIONはSS書込み対象外であり、製品REVと混同しない。

## DMM取得値からAD校正書込みした場合

計画上は、書込み完了 → ATEが `AR_REFRESH`（NF55G AR）→ 更新成功後に対象・点のREF/ADC Query → ATE照合。

例としてBATT_VのP1なら `AR_BATT_V_P1_REF?` と `AR_BATT_V_P1_ADC?` がMasterにある。REFは書込み基準値との照合対象、ADCは取得された校正点の記録として確認し、DMMの物理量とADCカウントをそのまま数値比較しない。

重要な現状: AR_REFRESH/AR QueryはMaster上の計画で、正式ATE入口は未実装。AD VALUE/AR REFの形式、単位・換算・丸め、反映タイミングは未確定。暫定FWではEEPROM書込みと実行中係数の反映が同時とは確認できず、再起動/再初期化の要否もOpenである。即時反映・自動再起動・暫定フォーマット採用を推定しない。この仕様回答と実装/実機確認をAD校正読戻し成立の条件とする。

係数/基準値の保存確認と、校正後の測定値が正しいことの確認は分ける。反映条件を確定した後、ATEが既知入力・負荷条件を設定し、明示DATA_REFRESHと対象測定Query、外部DMMの新規測定を組み合わせてATEが評価する。DMM側の再測定だけではNF55Gへの保存・反映確認を代替できない。許容差・確認点・反映条件は設計回答を要する。

## 参照と検証

[ATE Command Master](../../ATE_Command_Master.md)のSS/ADとRefresh、INFO Query、AR QueryおよびAR未実装記録、[Cache Master](../../Cache_Master.md)のSS→DATA/INFO失効・AD→DATA/AR失効、[Open Issues](../../Open_Issues.md)のAD/AR形式・反映時期、[取得Cache書込み要件](Acquired_Value_Write_Requirement_Rev0.md)を根拠とする。

今回は確認フロー案を保存し、取得Cache破棄と読戻し照合が両立するよう期待値の保持担当をATEとした。正式API・変換・反映条件等は未確定。文書差分を確認し、Host/Mock・実機試験は未実行。
