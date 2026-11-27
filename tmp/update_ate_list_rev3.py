from pathlib import Path
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / 'docs/ATE_Command_List_for_Test_Program_Rev2_20261123.md'
out = ROOT / 'docs/ATE_Command_List_for_Test_Program_Rev3_20261126.md'
text = src.read_text(encoding='utf-8')
text = text.replace('Revision: Rev.2', 'Revision: Rev.3').replace('Date: 2026-11-23', 'Date: 2026-11-26')
text = text.replace('2026-11-23までの追加仕様', '2026-11-26までの追加仕様').replace('実装状況は2026-11-23の', '実装状況は2026-11-26の')
text = text.replace('- Rev.1の構成と実装印を維持し、追加入口は第10.1～10.3節、操作手順は第14.13～14.15節へ追記した。過去の実機記録は確認日を付けて保持する。', '- 最新の追加入口は第10.1～10.5節、ATEの順序付き操作手順は第14.13～14.17節に示す。※は条件付き診断入口にも付けるため、使用条件を必ず確認する。\n- 本改訂はATE実機確認の準備資料であり、今回の実機デバッグ・FW配置は行わない。現行ソースと配置済みFWは別に確認する。')
text = text.replace('QR_HOST_ENABLED=False／EXTERNAL_INSTRUMENT_ENABLED=False', 'QR_HOST_ENABLED=False／EXTERNAL_INSTRUMENT_ENABLED=False／CALIBRATION_SAMPLE_ENABLED=False／QR_HOST_ARM_ENABLED=False')
text = text.replace('本書は、NF55G Pico 2 試験治具', '本書は、2026-11-26時点の開発状況に基づき、NF55G Pico 2 試験治具', 1)
text = text.replace('## 3. 共通応答', '''### 実機確認を始める前の確認

ATE接続は57600bps／8N1、要求・応答はCRLFとする。コマンドを並列送信せず、一行の応答完了を待つ。NF55G側は38400bps／8E1。以下の表は使用可否を切り分ける入口であり、動作確認の完了を宣言するものではない。

| 機能 | 実機確認前に確認する条件 | 今回の資料での扱い |
|---|---|---|
| 製品RefreshとQuery | 接続製品、治具FW、RTC、SD、ATE経路 | 既存の正式入口。既存制約を維持。 |
| 7355取得 | ADC言語／USB CDC、対応親FW、測定器HOST 20261125.2、外部測定器有効 | 第14.13～14.14節。7355の現行運用はADC。 |
| 校正ADとAR | CALIBRATION_SAMPLE_ENABLED、同一試行のD5でS1.14B／000001、照会済み測定Cache | 特定サンプル診断。正式なAD／AR汎用入口・量産承認とは区別。第14.16節。 |
| QRからSS | QR_HOST_ENABLED、QR用HOST・スキャナー・配線、対象ラベルをATEで照合 | 現行単方向はARMED応答。第14.15節。 |
| 双方向QR候補 | QR_HOST_ARM_ENABLEDと対応HOST・双方向配線 | PENDING応答の試験モード。正式採用・待ち条件は未確定。第14.17節。 |

*IDN?だけで全モジュールの版と有効設定を確認できるとは扱わない。配置記録・設定値と照合する。TEST_STARTの実機実績は最長11.218秒であり、T2をATEの全体待ち時間に流用しない。量産ATEの待ち時間は別途確認する。

## 3. 共通応答''', 1)
start = text.index('### 10.2 ')
end = text.index('### 10.3 ', start)
text = text[:start] + '''### 10.2 校正用の外部測定値取得とCache照会

回路はDISCHG_I／BATT_CHG／BATT_V、測定点はA／B、期限は1～10000ms。現行7355では末尾MD?を使用する。取得と照会はAD／ARを送信しない。

| ATEコマンド | 引数と用途 | 正常応答 | NF55G通信とCache | 実装有無 |
|---|---|---|---|---|
| `CAL_MEASURE_<回路> <AまたはB> <期限ms> MD?` | 回路名指定の現行取得入口 | `OK:CAL_MEASURE:<取得ID>` | NF通信なし。同点旧値を先に失効、完全取得のみ保存。 | ※ |
| `CAL_MEASUREMENT_<回路>? <AまたはB>` | 現試行の同回路・点の最新値を照会 | 下記の測定応答 | Cacheのみ。書込み用の照会済み記録を付ける。 | ※ |
| `CAL_MEASURE <回路> <AまたはB> <期限ms> MD?` | 従来の対象引数形式も利用可能 | `OK:CAL_MEASURE:<取得ID>` | 同上。 | ※ |
| `CAL_MEASUREMENT? <取得ID>` | 現試行の有効IDを指定 | 下記の測定応答 | Cacheのみ。書込み用の照会済み記録を付ける。 | ※ |

測定応答は `OK:CAL_MEASUREMENT:<ID>:<回路>:<AまたはB>:<測定値>:<測定単位>:<校正候補>:<校正単位>:<原文HEX>`。取得ID形式は試行世代8桁HEX－取得連番8桁HEX－回路－点。回路名方式でもIDは応答とログに残る。

MD?経路はF?→INIC?→TRS?→RN?→MSR?初回クリア→新しいEOM待ち→MD?の順。全処理に単一総期限を適用する。READ?／:READ?のSCPI経路はコード上残るが、7355現行運用の手順には使用しない。失敗はERR:CAL_<理由>、中継の成否不明はAMBIGUOUSを保持する。再取得で旧値は失効し、失敗しても戻さない。TEST_END成立・再STARTでIDは失効する。

''' + text[end:]
pos = text.index('## 11. ')
text = text[:pos] + '''### 10.4 サンプル診断用の校正書込みと明示読戻し

下表は通常ATE経路に実装した条件付き診断入口。CALIBRATION_SAMPLE_ENABLEDは既定False。同一の有効TEST試行でINFO_REFRESHし、FW_REV=S1.14B／UNIT_SERIAL=000001であることが必要。汎用のAD_<TYPE>_<POINT>_<VALUE>、AR_REFRESH、AR Cache Queryは引き続き未実装。

| ATEコマンド | 引数と用途 | 正常応答 | NF55G通信とCache | 実装有無 |
|---|---|---|---|---|
| `CAL_WRITE_<回路> <AまたはB> <P1またはP2>` | 最新の照会済み測定Cacheを明示採用 | `OK:CAL_WRITE:<VALUE8>:<AD_ADC十進値>:<計算値欄の原文HEX>` | AD DATA10文字／応答16文字。成功・成否不明時に測定値を失効しDATA／ARをINVALID。 | ※ |
| `AD_VERIFY_<回路> <P1またはP2>` | 同試行の正常書込み記録に対する明示AR | `OK:AD_VERIFY:<回路>:<点>:<VALUE8>:<REF8>:<AD_ADC>:<AR_ADC>` | AR応答140文字から対象欄を返す。AR CacheはVALIDにしない。 | ※ |
| `CAL_WRITE <取得ID> P1` | 互換用。BATT_CHG A→P1に限定 | `OK:CAL_WRITE` | 上記と同じAD。 | ※ |
| `AD_VERIFY BATT_CHG P1` | 互換用。書込み値とAR整数値・ADCを比較 | `OK:AD_VERIFY` または `ERR:AD_VERIFY_MISMATCH` | 別の明示AR。小数喪失により不一致になり得る。 | ※ |

回路はDISCHG_I／BATT_CHG／BATT_V、診断TYPEはそれぞれ1／4／2。A／BとP1／P2はATEが別々に指定し、Picoは対応を固定しない。正式な量産対応の確定を意味しない。ADは校正候補を有限のfloat32へ変換したビッグエンディアン8桁HEX（VALUE8）で送る。測定値の採否・範囲・符号はATEが判定する。Picoで3.3 Aを上限として拒否しない。

AD／ARとも診断T2=1000msでCommand Retryなし。正式T2はOI-12等で未確定のまま。書込みから自動ARは行わず、AD_VERIFYを別送信する。回路名付きAD_VERIFYのOKはAR受信成立であり、値の一致や校正PASSではない。VALUE8とREF8は表現が異なる可能性があり、HEX文字列の単純一致で合否を決めない。S1.14Bの実測診断では小数の書込み0.50／1.85／1.86／2.25 Aに対しAR REF8は0／1／1／2。内部の小数保持は未確認。

主な拒否はERR:CAL_WRITE_DISABLED、ERR:CAL_NO_ACTIVE_TRIAL、ERR:CAL_SAMPLE_IDENTITY、ERR:CAL_WRITE_NOT_QUERIED、ERR:CAL_WRITE_VALUE、ERR:AD_VERIFY_NO_WRITE、ERR:BUSY。通信異常はERR:CAL_WRITE_<理由>:AMBIGUOUS=0/1、AD正常フレームの応答内容不正はERR:CAL_WRITE_RESPONSE:AMBIGUOUS=1。AR timeoutはERR:AD_VERIFY_TIMEOUT、形式不正はERR:AD_VERIFY_RESPONSE。成否不明時はADを自動再送せず停止し、原文・対象・値・ログを保全する。

### 10.5 双方向QR受付の試験モード

通常モードのコマンド名・取得IDは維持する。試験モードではQR_SCANが `OK:QR_PENDING:<取得ID>` を返す。これはHOST受付応答待ちであり、読取り開始完了ではない。QR_GET?／QR_DATA?はHOST応答待ちでERR:QR_ARMING、同一受付ID照合後の読取り待ちでERR:QR_READING、完成後に通常のQR_GET／QR_DATA応答を返す。期限はQR_SCANからの全時間で、ARMING後にリセットしない。

旧読取りをHOSTで破棄して同じ受付IDの応答を確認する候補実装。QR_HOST_ARM_ENABLED=Falseが既定であり、現在の単方向配置にPENDINGを期待しない。対応HOSTと配線・設定を確認する。量産採用とATEの待ち条件はOI-23で未確定。手順は第14.17節。

''' + text[pos:]
text = text.replace('ATE_Command_List_for_Test_Program_Rev2_20261123.md --output docs\\ATE_Command_List_for_Test_Program_Rev2_20261123.docx', 'ATE_Command_List_for_Test_Program_Rev3_20261126.md --output docs\\ATE_Command_List_for_Test_Program_Rev3_20261126.docx')
text = text.replace('`docs/ATE_Command_List_for_Test_Program_Rev2_20261123.docx`', '`docs/ATE_Command_List_for_Test_Program_Rev3_20261126.docx`').replace('Rev.0-draftおよびRev.1のMarkdown / Word', 'Rev.0-draft、Rev.1、Rev.2のMarkdown / Word')
text = text.replace('- A / BとADのP1 / P2の対応は未確定。AD / ARの正式ATE入口は未実装。7355測定値の取得・照会はCAL_MEASURE／CAL_MEASUREMENT?として実装済み（第14.14節）。取得・校正候補の確認だけではADを書き込まない。', '- A／BとP1／P2はATEから明示する。量産での対応は未確定。サンプル診断用CAL_WRITE／AD_VERIFYは第10.4節・第14.16節、測定取得は第14.14節に従う。取得・照会だけではADを書き込まない。')
text = text.replace('- 数値指定による直接書込みと、測定値取得後にATEが判定して別途数値指定で書き込む方式を要求として保持する。取得だけでは補正を書き込まず、Pico内の取得値で書込み指定値を自動補完しない。', '- 現行の診断ATE入口は、取得して照会済みのCacheを回路名・測定点・製品点で明示採用する。任意数値を引数に取る汎用AD入口は未実装。取得や照会から自動書込みしない。')
text = text.replace('未実装の書込み・個別照合コマンド名を推測で確定しない。', 'サンプル診断入口の実装を正式なAD／AR仕様の確定とは扱わない。')
text = text.replace('長時間連続試験での受信TIMEOUTは未解決で、有限成功から安定性完了を推定しない。', '2026-11-25にADC・20 V・セット間1秒の400セット耐久を受入済み。過去のSCPI無応答原因、200 mV耐久、他機種への互換性は未確認。')
text = text.replace('`CAL_MEASURE BATT_V A 2000 :READ?`', '`CAL_MEASURE_BATT_V A 4000 MD?`').replace('2秒は例示で、試験条件に従って指定する。', '4秒は例示で、試験条件に従って指定する。').replace('`CAL_MEASUREMENT? <返された取得ID>`', '`CAL_MEASUREMENT_BATT_V? A`')
text = text.replace('A/BとAD P1/P2の対応、ADの値形式・小数読戻し・個別照合は未確定／未実装であり、本手順からAD／ARを送らない。', '測定値採用後の明示ADと別指令ARは第14.16節で行う。取得から自動書込みしない。量産での点対応・正式REF表現は未確定。')
text = text.replace('親UART到着済みの旧データは開始時に破棄するが、受付前からHOST内で処理中だった読取の遅着識別は未実装。スキャナー内部の旧読取と対象製品の取り違えを排除する受入は残る。', '通常の単方向モードでは親UART到着済みの旧データを開始時に破棄するが、HOST内処理中の旧QRは受付後に届き得る。771ms／1080ms遅着の実機記録がある。ATEは予定製品の型式・品目・REV・LOT・号機と照合し、不一致ならQR_CANCELし、対象ラベルを改めて読む。旧QR識別の双方向候補は第14.17節に示す。')
text = text.replace('FW6／ADU14／BBU14／予約2はF埋めの変更なし指定。', 'REV3文字の右にASCII空白0x20を1文字追加する。A03ならA03<SP>、B7.ならB7.<SP>であり、前詰め・ゼロ埋め・末尾空白削除をしない。D5の4バイトと照合する。FW6／ADU14／BBU14／予約2はF埋めの変更なし指定。')
pos = text.index('## 15. ')
text = text[:pos] + '''### 14.16 ADC校正をATEから順に実行する

この節はS1.14B／UNIT 000001の診断入口を対象とする。実機書込みは後日のデバッグで行う。書込み前に製品の元補正データと復元方法を確認し、対象回路・試験条件・ATEが指定するA/BとP1/P2を決める。例のA→P1、B→P2を量産の確定対応として転用しない。

| 順序 | ATE送信または操作 | 応答と次へ進む条件 |
|---|---|---|
| 1 | 治具FW・設定、7355のADC言語とUSB CDCを確認 | 外部測定器有効、診断有効、対応親FW／HOSTを配置記録で確認。無効ならここで停止。 |
| 2 | `*IDN?` → `PICO_SELF_CHECK?` → `SD_STATUS?` → `LOG_DROP_COUNT?` → `HOST_INFO? METER` | 各応答を保存。治具・測定器HOST・ログの事前状態をATEが確認。 |
| 3 | `TEST_START` → `INFO_REFRESH` → `FW_REV?` → `UNIT_SERIAL?` | 各応答を待つ。S1.14B／000001でなければ本診断書込みは停止。 |
| 4 | 7355を下記の設定表で設定・照会 | EXT_TXだけで進まず、DCV・連続・即時・ヘッダ・メモリ呼出・レンジの一致を確認。 |
| 5 | ATEで対象回路のA点条件を設定し安定を待つ | 目標値と実測値を混同しない。3回路の条件は第14.4節と試験指示に従う。 |
| 6 | 例 `CAL_MEASURE_BATT_CHG A 4000 MD?` | OK:CAL_MEASURE:<ID>。ERRなら旧Cacheを採用せず停止。 |
| 7 | `CAL_MEASUREMENT_BATT_CHG? A` | 対象／点／符号／測定単位mV／校正単位A／原文をATEで確認し採用。 |
| 8 | `CAL_WRITE_BATT_CHG A P1` | OK:CAL_WRITE:<VALUE8>:<AD_ADC>:<計算値原文HEX>を保存。AD一回。製品PASSにはしない。 |
| 9 | `AD_VERIFY_BATT_CHG P1` | OK:AD_VERIFY:BATT_CHG:P1:<VALUE8>:<REF8>:<AD_ADC>:<AR_ADC>を保存。ATEが表現を考慮して照合。小数を整数REFで一致確認できなければ照合未成立として停止・記録。 |
| 10 | B点の条件設定→`CAL_MEASURE_BATT_CHG B 4000 MD?`→`CAL_MEASUREMENT_BATT_CHG? B`→`CAL_WRITE_BATT_CHG B P2`→`AD_VERIFY_BATT_CHG P2` | A→P1／B→P2は例。承認された点対応で実施し、各段階で応答と値を確認。A点失敗を残して自動継続しない。 |
| 11 | DISCHG_I、BATT_Vも回路名と条件を変更して同じ順に実行 | 各回路2点。電流はR3、BATT_VはR5を指定・読戻ししてから取得。実シャント・全回路の通し試験は未完。 |
| 12 | `DATA_REFRESH`と必要Query、外部実測、必要な状態確認 | 補正後の値と動作をATEが確認。AR読戻しと補正成立と再投入保持は別項目。 |
| 13 | `TEST_END` → `PICO_SELF_CHECK?` → `SD_STATUS?` → `LOG_DROP_COUNT?` → `COMM_STATUS?` | 各応答と試行ログを確認。書込み値・AR原文・ADC・ATE照合結果を試行に紐付けて保管。 |

7355設定は各行についてEXT_SENDの応答後に対応するEXT_QUERYを送り、原文HEXをASCIIに戻して確認する。機器コマンド間は20ms以上空ける。機器へのCRLFは中継が付けるため本文に埋め込まない。

| 項目 | ATE設定例 | ATE照会例 | 確認する計器原文 |
|---|---|---|---|
| DCV | `EXT_SEND 2500 F1` | `EXT_QUERY 2500 F?` | F01（7355） |
| 連続測定 | `EXT_SEND 2500 INIC1` | `EXT_QUERY 2500 INIC?` | INIC1 |
| 即時トリガ | `EXT_SEND 2500 TRS0` | `EXT_QUERY 2500 TRS?` | TRS0 |
| ヘッダなし | `EXT_SEND 2500 H0` | `EXT_QUERY 2500 H?` | H0 |
| メモリ呼出解除 | `EXT_SEND 2500 RN0` | `EXT_QUERY 2500 RN?` | RN0,00000など、呼出解除 |
| SLOW2 | `EXT_SEND 2500 PR4` | `EXT_QUERY 2500 PR?` | PR4 |
| シャント200 mV | `EXT_SEND 2500 R3` | `EXT_QUERY 2500 R?` | R3 |
| バッテリ20 V | `EXT_SEND 2500 R5` | `EXT_QUERY 2500 R?` | R5 |

R3／R5は対象に応じ一つを選ぶ。DISCHG_IとBATT_CHGはV原文→mV→A、BATT_VはV→V。Cache照会時点では測定の桁を保持するが、AD送信ではfloat32へ変換する。VALUE8は送信したfloat32、REF8はARの製品表現であり、同形式とは限らない。AD応答計算値欄は原文8文字をHEX化した16桁で、正常数値を保証しない。両ADCは十進数。

失敗時は後続書込みを止める。取得失敗は再測定する場合もATEの明示操作とし、必ず新値を照会する。AD成功／成否不明では元測定Cacheは失効するため、同じCacheでの再書込みはしない。AR照合できない場合に丸め・絶対値化・許容差をPico側で補完しない。元値復元に使える汎用ATE AD入口は本一覧に存在しないため、復元方法未確認の製品へ書き込まない。

### 14.17 QR受付モード別の待ち方と書込み後の照合

第14.15節の通常手順に対し、双方向候補を使用するときは受付と読取り待ちを次のように分ける。両モードを同一配置で同時使用できるとは扱わない。

| 順序 | ATE送信または操作 | 通常単方向モード | 双方向候補モード |
|---|---|---|---|
| 1 | 配置版・設定・ラベルと製品の対応を確認 | QR_HOST_ENABLED、既存HOST | 左記に加えQR_HOST_ARM_ENABLEDと対応HOST・双方向配線 |
| 2 | `TEST_START` → `INFO_REFRESH` → INFO Query | 元FW／UNIT／ADU／BBU／設定を記録 | 同左 |
| 3 | `QR_SCAN 10000` | OK:QR_ARMED:<ID> | OK:QR_PENDING:<ID>。HOST応答待ち |
| 4 | `QR_GET? <ID>` | ERR:QR_READINGなら同じIDで待つ | ERR:QR_ARMINGはHOST応答待ち、ERR:QR_READINGは受付照合後。各行の応答を待って同じIDを照会 |
| 5 | 対象QRを読取り、`QR_GET? <ID>` | OK:QR_GET:<ID>:<35文字原文>を確認 | 同左。ARMING中に対象を読んでも採用されるとは扱わない |
| 6 | 原文をATEの予定製品情報と比較 | 型式・品目・REV・YYWW・号機の一致を確認。不一致はQR_CANCEL→対象再読取 | 同左。候補モードでも製品照合は省略しない |
| 7 | `QR_DATA? <同じID>` | OK:QR_DATA:<ID>:<100桁HEX>を復号 | 同左 |
| 8 | SS候補をATEで点検 | FW6、UNIT_REV4、LOT4、SERIAL6、ADU14、BBU14、予約2の計50文字。UNIT_REVはREV3＋0x20、他の非対象領域はF | 同左 |
| 9 | `QR_WRITE <同じID>` | OK:QR_WRITE:<ID>はSS通信成功。DATA／INFOは失効 | 同左。ただし候補と実製品SS／D5の通し受入は未完 |
| 10 | `INFO_REFRESH` → `UNIT_REV?` → `UNIT_LOT?` → `UNIT_SERIAL?` | 4バイトREV（末尾空白含む）、YYWW、6桁号機を候補と厳密比較 | 同左 |
| 11 | `FW_REV?`、ADU／BBU各Query、PARAMETER Query | 非対象領域が事前値を保持したことをATEで照合。F埋め自体を読戻し期待値にしない | 同左 |
| 12 | `TEST_END`、自己診断・SD・drop・ログ確認 | 書込み／D5読戻し／ATE照合結果を保存。次試行は新たにQR取得 | 同左 |

取得IDは応答をそのまま使い、例示IDを固定しない。読取り待ちではQR_SCANを繰り返さず同一IDを照会する。期限切れ・取消・旧ID・消費済みIDは書込み禁止。QR_WRITEが成否不明なら再送せず、INFO_REFRESHで実値を明示確認し記録する。試行終了・再STARTでIDは失効する。未接続／BUSYなど送信前拒否と、実行結果後の消費を区別する。

通常モードでは受付前からの読取りが遅着し得る。双方向候補は旧読取りの終端・キー解放後に受付IDを返し、それ以後の一件を同じIDで返す。親のCOM5 RAM試験で旧A破棄後のB照合と未接続書込み拒否を確認したが、実スキャナー30セット、実SD時の終了応答とdrop、製品SS／D5統合は保留。量産での待ち間隔・総待ち条件は未確定のため、本節から独断で量産設定を決めない。

''' + text[pos:]
text = text.replace('2026-11-23までのREADME／CHANGELOG', '2026-11-26までのREADME／CHANGELOG')
text = text.replace('過去の長期反復ではTIMEOUT再現。根本原因・送信中切断・旧応答境界・量産復旧は未受入。', '11月25日にADC・20 V・1秒間隔で400/400セット受入済み。timeout／再送／再起動／drop0、SD CSV400件SHA一致。過去SCPI無応答原因、200 mV耐久、他機種・量産復旧全般は未確認。')
text = text.replace('実シャント電流・8V/5V補正点・製品校正は未確認。専用結果ではCSV2本読戻し未完了。AD/ARとCAL-EXT残件は継続。', '11月25日ADC経路のBATT_V取得とR3 overrange時の旧Cache失効・R5再取得を確認。AD／ARなし。実シャント・3回路2点通し・CAL-EXT残件は継続。')
text = text.replace('電源再投入保持・旧HOST内遅着・RST不要cold-startは未受入。全体受入／OI-14・23 Closeとはしない。', '11月25日A/B別試行の取得・旧ID失効、再起動後初回取得を確認。11月26日A03<SP>／B7.<SP>のSS→D5一致。旧QR遅着は再現し、双方向は別の候補試験。保持・量産全体受入／OI-14・23は継続。')
text = text.replace('直近の機能実装記録ではHost Unit Test / Mock NF55G Test全527件成功（2026-11-23、QR→SS独立11項目を含む）。', '直近の記録ではHost Unit Test / Mock NF55G Test全557件成功（2026-11-26、双方向QR候補）。11月25日ADC経路は548件、回路名校正入口は543件成功。これらは既存記録であり、本改訂に伴う実機再試験の結果ではない。')
text = text.replace('## 17. 改訂履歴', '''### 直近追加機能の実機確認範囲

| 対象 | 確認できた事実 | 未確認事項と停止条件 |
|---|---|---|
| CAL_WRITE／AD_VERIFY | S1.14BのBATT_CHG P1人工値診断で小数REF切捨てを観測。回路名入口3回路と任意P1/P2はHost／Mock確認済み。 | 実シャント→ADC取得→AD→ARの全通し、新回路名版の実測書込み、他回路・点・再投入保持は未完。診断有効・個体一致・照会済みが必要。 |
| 双方向QR候補 | 診断で3連続成功、通常ATE COM5のRAM候補で旧A破棄後B一致、未接続拒否・製品送信0。 | 実スキャナー30セット、実SDの終了応答／drop、製品SS／D5、量産採用は未完。元HOSTへ復元済みの記録があり、恒久配置済みと扱わない。 |
| 7355 ADC耐久 | 20 V、連続／即時、セット間1秒、400セットとCSV照合を受入済み。 | R3の400セット、7351A／7351E等は未確認。別DMMへ交換した実機治具で機種ごとに確認する。 |

正式AD／ARのT2・REF表現・小数保持、量産点対応はOI-04／05／12／16～21とCAL-EXT関連、QRの旧読取り・正式双方向・全体受入はOI-23等で継続する。本改訂はIssue状態と製品FWを変更しない。

参照記録は以下のとおり。過去の「未実装」「未実施」は記録日の状態であり、直近の限定的な進捗と読み分ける。

- `docs/ADC_Decimal_Hardware_Test_20261125/run_02/Cache_Write_HIL_Rev1.md`
- `docs/ADC_Decimal_Hardware_Test_20261125/run_02/ADCMT_ADC_Command_Compatibility_Rev1.md`
- `docs/ADC_Decimal_Hardware_Test_20261125/run_02/Result_Rev0.md`
- `docs/USB_Host_Reset_Study_20261121/CDC_ADC_Endurance_Acceptance_20261125_Rev1.md`
- `docs/REV_Read_Write_Debug_20261126/QR_ATE_No_Product_Result_Rev0.md`
- `docs/REV_Read_Write_Debug_20261126/run_20261126_083052_555081/Result_Rev0.md`
- `src/command_parser.py`、`src/main.py`、`src/calibration_acquisition.py`、`src/calibration_write.py`、`src/config.py`

## 17. 改訂履歴''')
text += '\n| Rev.3 | 2026-11-26 | 7355のADC運用・回路名取得照会・サンプル診断ADと別ARを反映。ATEの順序付き校正手順、QR受付からSS・D5照合、双方向QR候補の待ち分岐、実機前提と停止条件を追記。400セット受入と11月26日QR進捗を反映。実機デバッグ・FW配置は本改訂では実施しない。 |\n'
out.write_text(text, encoding='utf-8')
print(out)
