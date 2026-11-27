from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'docs/ATE_Command_List_for_Test_Program_Rev3_20261126.md'
text = source.read_text(encoding='utf-8').replace('Revision: Rev.3', 'Revision: Rev.4')
text = text.replace('10.1～10.5', '10.1～10.6').replace('14.13～14.17', '14.13～14.18')
text = text.replace('| `AD_<TYPE>_<POINT>_<VALUE>` | 係数種別/point/value | `AD` | 10 chars | Open Issue | あり | `DATA` / `AR` | `AR_REFRESH` | OI-05, OI-12 関連。 |  |',
'''| `AD_<TYPE>_<POINT>_<VALUE>` | 人が読んだA/Vの10進値を直接指定 | `AD` | TYPE1＋POINT1＋float32 HEX8 | 診断1000 ms | あり | `DATA` / `AR`、同回路DMM A/B | 回路名付き`AD_VERIFY`を別送信 | 方式採用確定。サンプル診断条件あり。第10.6／14.18節。正式T2等はOpen。 | ※ |''')
text = text.replace('Parameter 初期化。 | ※ |', 'SPの動作設定・閾値を既定値へ戻す。確認済み製品FWではADC校正値は対象外。S1.14Bの保持実機確認は別途。 | ※ |')
text = text.replace('汎用のAD_<TYPE>_<POINT>_<VALUE>、AR_REFRESH、AR Cache Queryは引き続き未実装。', '人の読取り値の直接指定ADは第10.6節。AR_REFRESH／AR Cache Queryは引き続き未実装。')
text = text.replace('任意数値を引数に取る汎用AD入口は未実装。', '人の読取り値を直接指定するAD入口は第10.6／14.18節。')
text = text.replace('元値復元に使える汎用ATE AD入口は本一覧に存在しないため、復元方法未確認の製品へ書き込まない。', '直接AD入口を第14.18節に追加したが、ARの整数REFから失われた小数の元値を復元できるとは扱わない。復元方法未確認の製品へ書き込まない。')
pos = text.index('## 11. ')
text = text[:pos] + '''### 10.6 人の読取り値をATEから直接指定するAD

2026-11-26ユーザー指示により採用確定。人が測定器を読んだ値をATEへ記載し、NF55Gへ送る方式。CAL_WRITEの測定Cache方式も併用する。

| ATEコマンド | 引数 | 正常応答 | 使用条件 | 実装有無 |
|---|---|---|---|---|
| `AD_<TYPE>_<POINT>_<VALUE>` | TYPE=1～5または回路名、POINT=1/2またはP1/P2、VALUE=A/Vの10進数 | `OK:AD_WRITE:<TYPE>:<POINT>:<VALUE8>:<AD_ADC十進値>:<計算値原文HEX>` | CALIBRATION_SAMPLE_ENABLED=True、同試行D5でS1.14B／000001を確認。DMM・測定Cache不要。 | ※ |

TYPEは1=DISCHG_I、2=BATT_V、3=ACDC12V_V、4=BATT_CHG、5=12VOUT_V。電流TYPE1/4はA、電圧TYPE2/3/5はV。例AD_4_1_1.85とAD_BATT_CHG_P1_1.85は同じ1.85 Aの書込み。符号・小数・E/e指数表記を受け付け、単位文字・生HEXを入力しない。有限float32へ変換し、TYPE1＋POINT1＋VALUE8の10文字を送る。例のNF DATAは413FECCCCD。測定器の再読取り、Cache補完、Picoでの単位換算はしない。

診断T2=1000ms、AD Command Retryなし。正常／成否不明時はDATA／ARと同回路DMM A/B Cacheを失効する。STATUS／INFOはAD応答から更新しない。入力不正はERR:AD_ARGUMENTS／ERR:AD_TYPE／ERR:AD_POINT／ERR:AD_VALUEで無送信拒否。診断無効・試行なし・個体不一致・BUSYは既存の校正診断エラー。通信失敗はERR:AD_WRITE_<理由>:AMBIGUOUS=0/1、内容不正はERR:AD_WRITE_RESPONSE:AMBIGUOUS=1。再送せず停止する。

TYPE表・送信形式・1000msは現行診断の実装条件。直接方式の採用は、製品側正式仕様・量産受入・サンプル制限解除の承認とは区別する。AD_VERIFYは別指令。第14.18節とdocs/AD_Direct_ATE_20261126_Rev0.mdを参照。

''' + text[pos:]
pos = text.index('## 15. ')
text = text[:pos] + '''### 14.18 人が測定器を読んでATEから直接校正値を書く

測定器とPicoの接続は不要。測定値の正しさ、単位、対象回路、製品Pointは人とATEで確認する。自動取得方式と直接方式を同じ製品・点へ同時実行しない。

| 順序 | ATE送信または操作 | 応答と確認内容 |
|---|---|---|
| 1 | 対応FW・診断有効設定、元補正値と復元方法を確認 | 現時点はS1.14B／000001のサンプル診断。 |
| 2 | TEST_START → INFO_REFRESH → FW_REV? → UNIT_SERIAL? | 各応答を待って対象個体を確認。 |
| 3 | 対象回路・補正点の条件を設定して安定を待ち、人が測定器を読む | 目安値ではなく実測値を使う。電流はA、電圧はVを指定。 |
| 4 | 例 `AD_4_1_1.85` | 充電電流Point 1へ1.85 A。OK:AD_WRITE:4:1:3FECCCCD:<ADC>:<計算値原文HEX>を確認・記録。 |
| 5 | `AD_VERIFY_BATT_CHG P1` | 明示ARのVALUE8／REF8／AD ADC／AR ADCを保存。OKは受信成立であり一致やPASSとは別。 |
| 6 | ATEが読戻しと補正後測定を照合 | 小数がAR整数REFで一致確認できなければ照合未成立として記録し停止。丸めで合格にしない。 |
| 7 | 次点の条件設定→人の新値読取り→別のAD→別のAD_VERIFY | 例えば充電Point 2が0.50 AならAD_4_2_0.50。値は例であり、そのまま実機へ送らない。 |
| 8 | 必要なDATA_REFRESH／個別Query、外部測定、TEST_ENDとログ確認 | 補正成立・係数反映・再投入保持は別検証。実機デバッグは後日。 |

実測値が44.25 Aなら放電Point 1の例はAD_1_1_44.25、実測電圧8.12679 VならバッテリPoint 1の例はAD_2_1_8.12679。TYPE3／5も同じ書式。読戻しはAD_VERIFY_DISCHG_I、AD_VERIFY_BATT_V、AD_VERIFY_ACDC12V_V、AD_VERIFY_BATT_CHG、AD_VERIFY_12VOUT_VへP1／P2を別引数で指定する。必須校正は従来の3回路であり、TYPE3／5を必須工程に追加する指示ではない。

NaN／Inf／OL・単位付き・生HEX・float32 overflow／非ゼロunderflowを拒否する。通常のfloat32丸めは生じるためVALUE8を実送信値として記録する。Picoで物理範囲制限・絶対値化・値の自動補完を行わない。書込み正常／成否不明後は同回路の旧DMM A/B Cacheを再使用しない。成否不明・応答不正は再送せず、先行書込みを比較元にした誤照合も禁止する。

ログには人が入力したATE原文、source=ATE_DIRECT、回路・Point・入力値・VALUE8・AD DATA・応答原文・再送情報を残す。取得CacheのIDを人の実測記録の代わりに作らない。人が値を読み違えていないことの確認と最終PASS/FAILはATE側で行う。

''' + text[pos:]
text = text.replace('scripts\\build_ate_command_list_rev3_docx.py', 'scripts\\build_ate_command_list_rev3_docx.py --name ATE_Command_List_for_Test_Program_Rev4_20261126')
text = text.replace('`docs/ATE_Command_List_for_Test_Program_Rev3_20261126.docx`', '`docs/ATE_Command_List_for_Test_Program_Rev4_20261126.docx`')
text = text.replace('Rev.0-draft、Rev.1、Rev.2のMarkdown / Word', 'Rev.0-draft、Rev.1、Rev.2、Rev.3のMarkdown / Word')
text = text.replace('- `src/command_parser.py`', '- `docs/AD_Direct_ATE_20261126_Rev0.md`\n- `src/command_parser.py`')
text += '| Rev.4 | 2026-11-26 | 人が測定器を読み、ATEからADのTYPE／POINT／VALUEを直接指定する方式を採用確定・実装。第10.6／14.18節に手順・応答・制約を追記。Cache方式は併用。PARAM_RESETの対象範囲を明記。製品側未確定Issueと実機デバッグは継続。 |\n'
(ROOT / 'docs/ATE_Command_List_for_Test_Program_Rev4_20261126.md').write_text(text, encoding='utf-8')
