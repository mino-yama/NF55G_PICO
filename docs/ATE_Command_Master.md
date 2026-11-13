# ATE Command Master

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。 ただしD0のT2のみ、2026-11-11ユーザー指定により通信r2事前確認版p.17／28の300msを採用。r2の他項目は一括採用しない。
Revision: Rev.0

## 1. 共通原則
- 物理通信条件: ATE UART0はGP0=TX／GP1=RX、57600bps、8N1。NF55G UART1の38400bps／8E1とは独立設定する。ATE側のUARTも同一条件に合わせる。
- ATE UARTの要求終端はCR、LF、CRLFをすべて受理する（2026-11-10ユーザー指示により変更）。CRまたはLFで直ちに行を確定し、空のCR／LFは応答せず無視する。分割CRLFでも二重実行しない。応答終端は`src/config.py`の`ATE_RESPONSE_TERMINATOR`で`"CR"`／`"LF"`／`"CRLF"`から選択する。初期値は`"CR"`（2026-11-13ユーザー指定、PIA5100の終端CRに合わせる）。変更後はPicoを再起動する。EOIはGPIB側の信号であり本UART設定の選択肢に含めない。PIA5100／ATE側のEOI条件は別途照合する。
  ホストは応答完了後に次コマンドを送る。開発受信上限は512文字、保留8コマンド。
- ATE 応答は半角 ASCII 英数字、および 10 進数値（小数点・符号可）。
- HEX/BIN 取得値は必要に応じ 10 進表記へ変換。
- FD は例外で 32 byte を 64 ASCII HEX のまま返す。
- 個別 Query は Cache のみ参照し NF55G 通信を行わない。
- Control command の `OK` は Protocol Transaction 成功のみを意味する。
- 製品動作成立確認は ATE が `STATUS_REFRESH` + 外部測定で行う。

## 2. Refresh / Read
| ATE | NF CMD | T2 | Cache | 備考 |
|---|---|---:|---|---|
| DATA_REFRESH | D0 | 300ms | DATA | D0 327 chars、2026-11-11ユーザー指定によりr2を部分採用 |
| STATUS_REFRESH | D1 | 100ms | STATUS | Status 15 chars |
| INFO_REFRESH | D5 | 100ms | INFO | MFG50 + PARAM50 |
| D2_REFRESH | D2 | 100ms | D2 | 量産原則未使用 |
| D3_REFRESH | D3 | 200ms | D3 | LIFE_CALC clear 副作用 |
| D4_MAINT_READ | D4 | 100ms | D4 | 量産では使用しない（2026-11-09ユーザー指定）。AC_FAIL_COUNT clear 副作用 |
| AR_REFRESH | AR | Open Issue | AR | FW 独自 |
| FD_READ_xxxxxx | FD | 100ms | FD | 6 hex address |
| EL_REFRESH_01/09/17/25 | EL | 100ms | EL block | 8 records/block |
| OL_REFRESH_01/09/17/25/33/41/49/57 | OL | 100ms | OL block | 8 records/block |

### D0/D1/D5 Host実装状況（2026-11-07）

- `DATA_REFRESH`（D0）、`STATUS_REFRESH`（D1）、`INFO_REFRESH`（D5）と、第4節～第6節の個別Queryを共通Command Coreに実装済み。
- D0はNF CMD `D0`、DATAなし、T2=300ms（2026-11-11改訂）、応答DATA 327文字。完全Decode後にDATA CacheのみをVALIDにする。
  D0内STATUSはraw保持、Manufacturing/Parameterもraw保持とし、STATUS/INFO Cacheへ昇格しない。
- D0の各DATA QueryはDATA Cacheのみ参照し、自動Refreshしない。未取得・INVALID時は`ERR:CACHE_INVALID`。
- OI-03は未解決。PicoはD0後のCHARGE_END等の製品側副作用を推測・抑止・補正しない。ATE/設計側がr1/final FWとの整合を確認する。
- 引数なし。余分な引数・`=`指定は `ERR:UNEXPECTED_PAYLOAD`（Cache変更・送信なし）。
- Refreshは対象Cacheを先にINVALIDにし、D0=327文字/T2=300ms、D1=15文字/T2=100ms、D5=100文字/T2=100msで通信する。
  完全Decode後のみ対象CacheをVALIDにし `OK` を返す。失敗時に旧値は復元しない。
- 個別QueryはCacheのみ参照。INVALID時は `ERR:CACHE_INVALID`。
  STATUSは `0`/`1`、INFOの数値は10進数、製造ASCII textは先頭ゼロを保持する。
- 通信未接続は `ERR:NF55G_NOT_CONNECTED`、Decode失敗は `ERR:DECODE`。
  NF55Gエラー/timeout等は `ERR:<transaction.error>`。HWE時はDATA/STATUSもINVALID。
- ATE受信ループ、Pico時計、EB、実SD統合コードはHost/Mockで検証済み。
  最終firmware経由の実機検証は別途必要。実機送信Gateは変更しない。

### D2_REFRESH Host実装状況（2026-11-07）

- `D2_REFRESH` は引数なしでNF CMD `D2`、T2=100ms、応答DATA 30文字として実装。
- 開始時にD2 CacheをINVALIDにし、完全なOFF_PERIOD Decode成功後だけD2 CacheをVALIDにする。
  D2のProtocol SUCCESS時はCache Masterに従いDATA CacheをINVALIDにする。ambiguous failure時もD2/DATAをINVALIDにする。
- `decode_d2` はr1 §13.5.1(1)のPS_OFF期間更新条件をそのまま適用し、値の補完・更新推測をしない。
- D2個別QueryのATE名・応答契約は本Masterで未定義。既存DATA QueryをD2 Cache参照へ流用せず、正式名が決まるまで追加しない。
- Host/Mock検証はD2フレーム、DATA長、T2、Cache invalidation、Decode/ambiguous failureを対象とする。実機HILはコード同期・配置後に別途行い、結果値による製品PASS/FAIL判定はしない。

### D3_REFRESH / D4_MAINT_READ Host実装状況（2026-11-07）

- `D3_REFRESH` はNF CMD `D3`、T2=200ms、応答DATA 21文字、`D4_MAINT_READ` はNF CMD `D4`、T2=100ms、応答DATA 212文字として共通Dispatcherへ実装。
- Refresh開始時に各対象CacheをINVALIDにし、完全Decode成功後のみD3/D4 CacheをVALIDにする。D3/D4のSUCCESSまたはambiguous failureでは仕様表どおりDATA CacheをINVALIDにする。
- D3/D4専用のATE個別Query名・応答契約は未定義のため追加しない。D3のLIFE_CALC clear、D4のAC_FAIL_COUNT clear副作用を前提に、必要時のみ明示Refreshする。
- Host/MockでATE入口、NF CMD、T2、応答長、Decode、Cache invalidation、Decode/ambiguous failureを検証。Pico配置および実機HILは未実施。

## 3. Control / Set
| ATE | NF CMD | NF DATA | T2 | Success invalidation | Post check |
|---|---|---|---:|---|---|
| PARAM_<ITEM>_<VALUE> | SP | 50 chars | 100 | DATA/STATUS/INFO | INFO_REFRESH |
| PARAM_RESET | RP | none | 100 | DATA/STATUS/INFO | INFO_REFRESH |
| ERP_SET_1_0 | SE | 1000 (BURST=1, PS_OFF_CHARGE=0, reserve=00) | 100 | DATA/STATUS | STATUS_REFRESH + 外部測定 |
| ERP_SET_0_0 | SE | 0000 (BURST=0, PS_OFF_CHARGE=0, reserve=00) | 100 | DATA/STATUS | STATUS_REFRESH + 外部測定 |
| ERP_SET_0_1 | SE | 0100 (BURST=0, PS_OFF_CHARGE=1, reserve=00) | 100 | DATA/STATUS | STATUS_REFRESH + 外部測定 |
| ERP_SET_1_1 | SE | 1100 (BURST=1, PS_OFF_CHARGE=1, reserve=00) | 100 | DATA/STATUS | STATUS_REFRESH + 外部測定 |
| CLOCK_SYNC | SC | YYMMDDHHMMSS | 100 | DATA/STATUS | DATA_REFRESH |
| SERIAL_<ITEM>_<VALUE> | SS | 50 chars | 100 | DATA/INFO | INFO_REFRESH |
| LIFE_SET_<VALUE> | SL | 3 chars + reserve | 100 | DATA | DATA_REFRESH |
| BATT_CHECK_START | BC | 1 | 6000 | DATA/STATUS, BC refreshed | BC queries |
| BATT_CHECK_STOP | BC | 0 | 6000 | BC/DATA/STATUS | STATUS_REFRESH |
| CHARGE_ON | CN | 1 | 100 | DATA/STATUS | STATUS_REFRESH + ext current |
| CHARGE_ON_STOP | CN | 0 | 100 | DATA/STATUS | STATUS_REFRESH + ext current |
| CHARGE_OFF | CF | 1 | 100 | DATA/STATUS | STATUS_REFRESH + ext current |
| CHARGE_OFF_CLEAR | CF | 0 | 100 | DATA/STATUS | STATUS_REFRESH + ext current |
| BACKUP_ENABLE | BE | none | 100 | DATA/STATUS | STATUS_REFRESH + ext 12V |
| BACKUP_OFF | BF | none | 100 | DATA/STATUS | STATUS_REFRESH + ext 12V |
| OUTPUT_RESTART | OR | none | 100 | DATA/STATUS | STATUS_REFRESH + ext 12V |
| CLEAR_ALL | CD | 0 | 500 | DATA/STATUS/BC | DATA+STATUS_REFRESH |
| CLEAR_POWER | CD | 1 | 500 | DATA/STATUS/BC | DATA+STATUS_REFRESH |
| CLEAR_BATT | CD | 2 | 500 | DATA/STATUS/BC | DATA+STATUS_REFRESH |
| CLEAR_LOG | CL | none | 1000 | all EL/OL | EL/OL refresh |
| AD_<TYPE>_<POINT>_<VALUE> | AD | 10 chars | Open Issue | DATA/AR | AR_REFRESH |
| FW_UPDATE | FU | BLOCKED | - | none | ERR:FU_DISABLED |

### CLOCK_SYNC Host実装（2026-11-07）

- `CLOCK_SYNC YYMMDDHHMMSS`（または `CLOCK_SYNC=YYMMDDHHMMSS`）はATEが明示する10進日時を使用する。PicoのRTCを変更・自動参照しない。
- 年・月・日・時・分・秒の各10進値を2桁ASCII HEXへ変換し、SC DATAに格納する。例: `260102030405` -> `1A0102030405`。正常応答DATAは0文字、T2=100ms。
- 日時の構文と暦を検証する。成功時または成否不明時はDATA/STATUSをINVALIDにし、Control応答をCacheへ昇格しない。自動Refreshは行わない。
- SCは時刻のずれをAC OFF時間として計算する。過去時刻は製品側でパラメータエラーとなる仕様のため、実機送信時刻と影響を担当者が確認する。
- Host/Mock検証対象。Picoへの配置およびSC実機送信は未実施。

## 4. DATA Cache Query
- NF55_DATE?
- NF55_TIME?
- NF55_DATETIME?
- VOUT12?
- IOUT12?
- BATT_VOLT?
- CHG_VOLT?
- CHG_CURR?
- BATT_CURR?
- BATT_SOC_WH?
- BATT_SOC_MAH?
- BATT_TEMP?
- ADU_TEMP?
- BBU_TEMP?
- FAN_RPM?
- FAN_LEVEL?
- AC_OFF_HOUR?
- PS_OFF_HOUR?
- AVE_OFF_TEMP?
- OFF_CHARGE_HOUR?
- AVE_CHARGE_TEMP?
- OFF_CHARGE?
- OFF_BATT_DEG?
- CHARGE_DATA?
- CHARGE_END?
- LIFE_BATT_CHARGE?
- LIFE_BATT_TEMP?
- LIFE_BATT_DEG?
- TOTAL_ADU_TEMP?
- TOTAL_ADU_HOUR?
- AC_FAIL_COUNT?
- AC_LOW_COUNT?
- BACKUP_COUNT?
- BATT_DEG_TOTAL?
- TOTAL_BATT_HOUR?
- BATT_DISCHARGE_COUNT?
- BATT_CHARGE_COUNT?
- BATT_TTL_DISCHARGE?
- BATT_TTL_CHARGE?
- TOTAL_BATT_TEMP?
- BATT_TEMP_AVE?
- BATT_TEMP_MAX?
- BATT_TEMP_MIN?

## 5. STATUS Cache Query
- PS_ON?
- BURST_ON?
- BURST?
- PS_OFF_CHARGE?
- RESTART_READY?
- BACKUP_READY?
- CHARGE_READY?
- BATT_CHECK_RUN?
- CHARGE_OFF_STATUS?
- CHARGE_ON_STATUS?
- BATT_ON?
- BATT_LOW?
- S_CHARGE_ON?
- CHARGE_OK?
- CHARGER_ON?
- FAN_WNG?
- ADU_TEMP_WNG?
- OC_OFF_H?
- PFC_OV?
- FAN_FAIL?
- BBU_TEMP_WNG?
- BBU_FAIL?
- CHG_LV?
- CHG_OV?
- CHG_OC?
- BATT_TEMP_WNG?
- BATT_TEMP_ALM?
- BATT_LV?
- BATT_OV?
- BATT_LIFE?
- BATT_MCN?
- BATT_P_FAIL?
- BATT_DCN?
- 12V_OV?
- 12V_LV?
- 12V_OC?
- 12V_OC_OFF_L?

## 6. INFO Cache Query
- FW_REV?
- UNIT_REV?
- UNIT_LOT?
- UNIT_SERIAL?
- ADU_REV?
- ADU_LOT?
- ADU_SERIAL?
- BBU_REV?
- BBU_LOT?
- BBU_SERIAL?
- PS_ON_BACKUP?
- AC_LINK?
- AUTO_CHARGE?
- EVENT_ENABLE?
- MAX_BACKUP_TIME?
- MIN_BACKUP_TIME?
- RESTART_TIME?
- BATT_LOW_THD?
- BATT_CAP_MAH?
- BATT_CAP_WH?
- CHG_IR_THD?
- BATT_WNG_THD?
- BATT_ALM_THD?
- ADU_TEMP_THD?
- BBU_TEMP_THD?
- FAN_WNG_THD?

## 7. BC Cache Query
BC_MODE?, BC_V1?, BC_V2?, BC_I1?, BC_I2?, BC_TEMP?, BC_SOC?, BC_IR?

## 8. AR Cache Query
- AR_DISCHG_I_P1_ADC?/REF?, P2_ADC?/REF?
- AR_BATT_V_P1_ADC?/REF?, P2_ADC?/REF?
- AR_ACDC12V_V_P1_ADC?/REF?, P2_ADC?/REF?
- AR_BATT_CHG_P1_ADC?/REF?, P2_ADC?/REF?
- AR_12VOUT_V_P1_ADC?/REF?, P2_ADC?/REF?

## 9. EL/OL Query
Pattern:
- EL_<NN>_DATEHOUR? / EL_<NN>_ID?, NN=01..32
- OL_<NN>_DATEHOUR? / OL_<NN>_ID?, NN=01..64

No log:
- DATEHOUR -> 00000000
- ID -> 255

## 10. RTC / Diagnostic / Logger
RTC_DATE?, RTC_TIME?, RTC_DATETIME?, RTC_SET_YYYYMMDD_HHMMSS, RTC_CHECK?
*IDN?, PICO_SELF_CHECK?, NF_COMM_CHECK?, COMM_STATUS?, RETRY_COUNT?
TEST_START, TEST_END, LOG_CONT_START, LOG_CONT_STOP

### 2026-11-11 TEST_START再受付による試行分離

- 試験中のTEST_STARTは、通信待機時に前試行のQueueを排出・flush・close・命名して新試行を開始する。前試行の終了区分はNEXT_TEST_STARTとし、製品FAILや実際の停止理由を推定しない。
- 受付ごとにT000001等の試行IDを付け、1試行1CSVとする。引数なしSTARTの再送も新たに受付すれば別試行。通信busy、保存中の通信検出、連続ログ中はERR:BUSY。拒否時は新試行を開始しない。
- 新試行ではQR受信状態・ログ用S/N・全製品Cacheを失効する。自動Refresh・SSは行わない。QR再取得は当該試行で実施する。
- OKは試行受付を示し、保存成功を保証しない。SD異常時も試行IDは分けるがCSV作成は保証できない。再START途中の自動SD再認識は行わない。
- 直前完了試行のTEST_LOGGER／TEST_LOG_DROPは新STARTでも保持し、次の試行完了時に更新する。logger.last_test_idとRAM履歴で試行を対応付ける。
- Host／Mock284件成功。修正版のPico配置・実機Timingは未確認。[実装記録](Test_Interruption_20261111/Implementation_20261111.md)。SS開発は保留。
SD_STATUS?, SD_USAGE?, LOG_DROP_COUNT?, SD_REINIT

## QR読取の追加要件（2026-09-18、未実装）
- ATEが発行する読取開始はPico専用コマンドとする。正式コマンド名・引数・応答・待ち時間はOI-23で管理する。
- 開始指示後、QRリーダ → かんたんUSBホスト HIDキーボード用 → Picoの経路で読み取り、PicoにCacheする。
- 読取完了からNF55G書込みを自動起動しない。後続のATE指示でCacheをNF55Gへの書込みに利用する。
- QR情報の書込みはNF55GのSSコマンドに紐付ける（ユーザー指定）。保存Cache名は後日決定し、SS DATAへの詳細対応を具体化する。ATEの明示書込み指示を必要とし、FU禁止は継続する。
- 詳細: [QR読取要件](QR_Reader_Requirements.md)。

### 工程分離と異常返却（2026-09-18追加、未実装）
コマンド案は QR_SCAN → QR_GET → QR_PARSE → QR_DATA → 既存NF55G WRITE → 必要時に既存NF55G READ → QR_VERIFYまたはATE照合。
QR_PARSEでフィールド分解と桁数・文字種・範囲検証を行い、QR_DATAでATEが内容を確認した後、ATEの明示指示で変換・書込みを実行する。
QR_GET/QR_DATAは保持情報を返し、自動読取・自動Refreshを行わない。QR_VERIFYを採用する場合も明示読出し済みの値と比較する。
各工程の異常はATEへエラーコードを返す。正式名称、応答形式、エラーコード表と照合担当はOI-23で確定する。

### SET_SERIAL画面によるSS書込み対象の指定
生産LOT・生産年月・S/N情報の書込み範囲は画面のUNIT_REVからBBU_SRLまで。SS対象はUNIT_REV/UNIT_LOT/UNIT_SERIAL、ADU_REV/ADU_LOT/ADU_SERIAL、BBU_REV/BBU_LOT/BBU_SERIALの9項目。画面のSRL表記は既存SERIAL項目に対応する。FW_REVISIONはFW書き込み仕様書のREVSIONとの一致照合のみとし、書込み対象に含めない。ATEが明示INFO_REFRESHを実行した後、FW_REV?で読出し値を取得する。比較元の仕様書・期待値・比較規則・照合担当はOI-23で確定する。
QR値からの変換、各値の取得元、SS DATA詳細は[QR読取要件](QR_Reader_Requirements.md)とOI-23で管理する。

QRのREVは製品REVで、SSのUNIT_REVに対応する。FW_REVISIONとの照合値には使用しない。QRの3桁からUNIT_REVの4桁への格納規則はOI-23で確定する。

## 2026-09-26 QR単独受信試験（正式APIとは別）
今回の試験ではQR_SCANでPico受信を開始し、35文字+LF/CRLFを受信後に自動分割して試作用RAM CacheとREPLへ出力する。以前のQR_PARSE工程分離案の本番採否は保留。
試作用コマンド: QR_SCAN、QR_STATUS?、QR_GET、QR_DATA、QR_CANCEL。ATE終端はCRLF。詳細は[試験手順](QR_Receive_Test.md)。本番dispatcherには未登録。NF55Gコマンド送信機能なし。

## SD復帰の試験期間制約（2026-11-09）

TEST_START～TEST_END（ログ開始失敗時を含む）および連続記録中のSD_REINITはERR:BUSYを返す。TEST_END／LOG_CONT_STOP後、ATE応答・待ち要求を優先した通信待機時に1回だけ再認識する。2026-11-09②③要求によりTEST_START／TEST_ENDはSD異常でも試験受付・終了のOKを返す。保存異常はTEST_END最終段のSelf CheckとPICO_SELF_CHECK?で報告し、NF55G通信は継続可能。復帰結果はSD_STATUS?で確認する。フォーマットは実行しない。詳細は[Logger / SD仕様](Logger_SD_Spec.md)を参照。

## 試験終了時の装置自己診断（2026-11-09）

TEST_START後にQRを読み、試験終了のTEST_ENDで最終Self Checkを実行する。PICO_SELF_CHECK?には既存のATE_UART／NF55_UART／RTC／LOGGERに加え、試験終了後はTEST_LOGGER（その試験のSD保存状態）、TEST_LOG_DROP（OKまたは破棄件数）を含める。NGは装置異常であり製品FAILではない。復帰後および次のTEST_STARTでも直前完了試行の異常を保持し、次の試行完了時に更新する（2026-11-11変更）。TEST_START／TEST_ENDのOKはログ保存成功や製品PASSの意味ではない。

ログ名は日時を基本とし、試験中に取得したQRの末尾6桁の数字S/Nを終了時に付加する。正式QR取得コマンド・物理入力はOI-23で引き続き管理し、今回新設しない。

## 2026-11-09 D4運用とCLEAR試験

D4は副作用のため量産では使用しない。D4-TIM-01は未解決のまま保守課題として保持し、CLEAR試験を優先する。CLEAR_ALL／POWER／BATTはCDのDATA0／1／2、T2=500ms。CLEAR_LOGはCLのDATAなし、T2=1000ms。r1 p.35に従い正常応答はどちらもDATA0文字。成功と成否不明時は既存Cache規則に従い無効化し、応答から昇格しない。CDで満充電情報等が初期化され初期充電が動作し得るため、今回ユーザー確認済みのバッテリ未接続条件で通信試験する。

2026-11-09 CLEAR実機結果: POWER／BATT／ALL／LOGの4種がOK、19／19／20／19ms、再送0、BCC一致。CD後のDATA／STATUS無効化、CL後の全EL／OL無効化と96件の空ログ表現を確認。CLEAR_ALLは先行個別消去後の0維持を確認したもので、単独非ゼロ値消去は未検証。Host／Mock全203件合格。詳細・制限はReal_Hardware_Test_Log.md。

2026-11-09 PARAM_SET実機前準備: r1 p.19のSP正常応答DATA0文字をDispatcherで厳密検証する。非空応答のplain NAK・最終FRAME異常、SQE、ACK_TIMEOUTとDATA/STATUS/INFOの無効化／保持をHost試験へ追加。今回の試験はD5の現行設定RAW50文字を同値で書き戻す。RPは別段階。

2026-11-09 PARAM_SET同値書戻し実機結果: 現行D5の設定RAW50文字をreserve込みで退避・同値送信し、SP正常応答DATA0文字、72ms、BCC一致、再送0を確認。INFO/STATUS無効化と再取得後の設定・製造情報の完全一致を確認。ユーザー報告は出力変化・瞬断・再起動なし（電圧数値未提示）。ログ3本をtemp直下へ順次コピー。Host／Mock全206件成功。設定の実変更・保持・RPは未確認。詳細はReal_Hardware_Test_Log.md。

2026-11-09 PARAM_RESET準備: r1 p.21に従いRP正常応答DATA0文字をDispatcherで厳密検証。空応答・T2=100ms、非空応答plain NAK、SQE、ACK_TIMEOUTとCache規則を回帰試験に追加。現在のD5 RAW50文字を退避→RP初期値読出し→元RAWをSPで復元→完全一致確認の順で実機試験する。RESETは全項目を数値0にする意味ではなく、電源初期値へ戻す。

## 2026-11-09 SET ERP Host実装

- r1 p.21のSET ERPに基づき、ATE入口は `ERP_SET_0_0`／`ERP_SET_1_0`／`ERP_SET_0_1`／`ERP_SET_1_1` の全4種を実装。いずれも引数なし。前の数字がBURST、後ろの数字がPS_OFF_CHARGEで、毎回両設定を指定する。
- NF CMDはSE、DATAはASCII 4文字の0000／1000／0100／1100、T2=100ms。正常応答DATAは状態情報15文字として厳密に長さを確認する。
- 正常終了またはambiguous時はDATA／STATUSだけをINVALIDにする。SE応答の状態情報をSTATUSへ昇格せず、自動Refreshしない。SQE／PMEでは既存Cacheを保持する。
- OKはProtocol Transaction成功のみ。設定確認は明示STATUS_REFRESH後のBURST?／PS_OFF_CHARGE?で行う。BURST_ON?はBURST入力信号の受信状態で、実際のバースト有無に依存しない（r1 p.30）。実動作成立は外部測定で確認し、製品PASS／FAILはATE側で判断する。
- Host／Mock専用試験はtests/test_erp_commands.py。Picoへの配置およびSample併用の実機試験は未実施。

### ERP DATA各桁と追加条件の原典照合（2026-11-09）

確認事実（r1 p.5、§8.3 p.21）:

| 左からの位置 | 項目 | 意味 |
|---|---|---|
| 1文字目 | BURST | 0=バースト動作無効、1=有効 |
| 2文字目 | PS_OFF_CHARGE | 0=PS_OFF時の充電無効、1=有効 |
| 3～4文字目 | RESERVE | 00を送る。動作設定項目ではない |

- 4文字はASCII（ルール①）。1000は31h 30h 30h 30h、0000は30h 30h 30h 30h。整数の桁・上位下位や、1バイトの4ビットを表す0000とは異なる。配列は仕様表の順序に従う。予約領域へデータがあっても製品は無視する仕様だが、治具は規定どおり00を送る。
- 1000はBURST=1・PS_OFF_CHARGE=0であり、p.21の低消費電力設定条件を同時に指定する。0000は両方を無効にし、PS_OFF充電を有効へ戻す操作ではない。
- 仕様上の組合せは0000／0100／1000／1100。p.21の初期値欄はBURST=1、PS_OFF_CHARGE=1（組合せ1100）。現在の実値を初期値と推定してはならない。ユーザーの追加実装指示により、ATE実装は0000／1000／0100／1100の全4組合せに対応。

追加設定・動作確認（確認事実）:

- r1 p.21は低消費電力状態にする設定としてBURST有効・PS_OFF_CHARGE無効を指定。p.43（RW11動作概要・参考）にも、DeepsleepをEnableとして消費電流を抑える場合はPS_OFF_CHARGE無効とする記載がある。2文字目は今回の1000へ既に含まれるため、これを別のSPコマンドで設定する必要を示す記載はない。
- p.17のSEはPS_OFF受付可、バックアップ中受付不可、T2=100ms。p.18ではバックアップ中のSQEと設定値のPMEを規定。SEの前にSC／RP／CN／CFを必須送信する記載は確認できない。p.17のSC完了待ち注記はD2の条件であり、SEへ流用しない。
- p.29～30ではBURSTは有効設定、PS_OFF_CHARGEは有効設定、BURST_ONは外部BURST信号の受信状態。BURST_ON=1だけで実際のバースト動作成立と判定しない。

推測・未確認:

- 低消費の実動作には外部信号・PS_ON／PS_OFF・負荷などの条件が関係し得るが、今回確認した通信仕様ではBURST入力の必要論理・極性、負荷しきい値、遷移時間、消費電力の合否値を確定できない。最終NF55G製品仕様とSampleの試験条件を設計側に確認する（ERP-CONDITION-01）。
- 元設定のPS_OFF_CHARGE=1を復元する場合や充電許可の比較にはERP_SET_0_1／ERP_SET_1_1を使用できる。充電許可は実際の充電開始を保証せず、CHARGE_OFFの解除にもならない。復元は保存したBURST／PS_OFF_CHARGEに対応するコマンドをATEが明示実行する。実機送信は未実施。
- ソフトウェアの1000／0000／0100／1100配置は原典と一致する。実機低消費動作・設定保持・Sample比較は未確認。

## 2026-11-09 EL／OL／FD Host実装と実機デバッグ予定

ユーザー指示により読出しを優先実装。Pico配置と実機デバッグは後日ERP全4種とまとめて実施する。今回はHost／Mockのみで、製品への送信は行っていない。

- EL_REFRESH_01／09／17／25、OL_REFRESH_01／09／17／25／33／41／49／57を正式ATE入口へ実装。引数なし。ATE名の開始番号は10進（17）で、NF DATAはルール②のASCII HEX（11）に変換。T2=100ms、応答82文字、START_NO一致を検証する。
- EL_01～32／OL_01～64のDATEHOUR?／ID?は対応する8件ブロックCacheだけを参照。日時は各欄のHEXを10進YYMMDDHHへ変換し、IDは10進。空履歴は00000000／255。別ブロックを自動取得しない。製品の閏日記録や時刻誤差をPicoが補正しない。
- FD_READ_xxxxxxは6桁ASCII HEXアドレスをそのままFDへ送信。T2=100ms、応答64文字を全桁HEX検証。FD_DATA?はFD Cacheの64文字を大文字小文字・先頭ゼロを含め保持して返す。FD Cacheは最新の1回分で、開始時に旧値をINVALIDにする。
- FD_DATA?を正式Queryとして本Masterへ追記。FUへの連携、アドレス丸め・範囲外のFF補完・自動Refreshは行わない。FDの範囲外挙動はOI-10継続。原典のFD／F0表記不一致はREAD-FD-01へ記録し、設計確認前の実機送信を保留する。
- Refresh開始時に対象のみINVALID。完全Decode後のみ対象をVALIDにし、失敗時は旧値を戻さない。HWEではDATA／STATUSもINVALID。CLの成功／ambiguousでは全EL／OL CacheをINVALIDにする既存処理を共用する。
- AR_REFRESH／AR QueryはOI-04／12／20等の仕様確定待ちで未実装を維持する。D2／D3／D4専用Queryは未定義のまま追加しない。
- Host／Mock全233件合格。詳細: tests/test_log_fd_read_commands.py、temp/read_commands_host_mock_20261109_run01.log。実機結果とは区別する。

## 2026-11-09 項目別PARAM設定のHost実装

形式: PARAM_<ITEM>_<VALUE>。VALUEは符号なしASCII 10進整数で、コマンド名内に指定する。追加引数・=指定・小数・符号・HEX表記は拒否する。先頭ゼロは許容する。

| ITEM | VALUEの範囲（10進整数） | 意味・単位 |
|---|---|---|
| `PS_ON_BACKUP` | 0～1 | 0=無効、1=有効 |
| `AC_LINK` | 0～1 | 0=無効、1=有効 |
| `AUTO_CHARGE` | 0～3 | 0=無効、1～3=有効レベル |
| `EVENT_ENABLE` | 0～1 | 0=無効、1=有効。原典EVENTのATE名 |
| `MAX_BACKUP_TIME` | 0～14 | 分。0=無制限 |
| `MIN_BACKUP_TIME` | 0～254 | 秒 |
| `RESTART_TIME` | 0～254 | 秒 |
| `BATT_LOW_THD` | 0～100 | ％。0=電源初期値 |
| `BATT_CAP_MAH` | 0～65534 | mAh。0=電源初期値 |
| `BATT_CAP_WH` | 0～254 | Wh。0=電源初期値 |

- 例: PARAM_AUTO_CHARGE_2、PARAM_MIN_BACKUP_TIME_15、PARAM_BATT_CAP_MAH_4900。原典EVENTは既存INFO Query名と同じEVENT_ENABLEを使用し、PARAM_EVENT_1という別名は追加しない。
- r1 p.19に基づき、指定項目だけを規定幅のASCII HEXへ変換し、未指定16項目領域を各欄最大値F～FFFF（変更なし）、予約18文字を0として合計50文字のSP DATAを作る。現在値を読み出して再構成せず、Cache未取得でも実行可能。自動D5は送らない。
- T2=100ms、正常応答DATA0文字、成功／ambiguous時にDATA／STATUS／INFOをINVALID化。明示INFO_REFRESH後、<ITEM>?で設定値を確認する。INFOの再取得だけではDATA／STATUSを更新しない。
- 仕様上の保護設定BATT_WNG_THD／BATT_ALM_THD／ADU_TEMP_THD／BBU_TEMP_THD／FAN_WNG_THDは項目別入口でERR:PARAMETER_PROTECTEDとして無送信拒否。CHG_IR_THDはPARAM-IR-01確認待ちでERR:PARAMETER_UNCONFIRMED。通常10項目以外は追加しない。
- 範囲外はERR:PARAMETER_RANGE、整数形式不正はERR:PARAMETER_VALUE、未知項目はERR:PARAMETER_UNKNOWN_ITEM、項目形式不正はERR:PARAMETER_FORMAT、余分な引数はERR:UNEXPECTED_PAYLOAD。いずれもCache変更・送信なし。
- 原典0の特別意味を別値へ置換せずそのまま送る。例えばBATT_LOW_THD=0を50へ自動変換しない。保護・充電・バックアップの製品動作成立をPicoで判定しない。
- 既存PARAM_SETの50文字一括方式とPARAM_RESETの契約は変更しない。項目別設定のHost／Mockを確認済み、Pico配置・実機送信は未実施。

2026-11-10実機結果追記: 通常10項目について各1代表値への変更→明示D5読戻し→元値復元を確認。設定試験の実行日時は11月9日18:08～18:09 JST、翌日の継続作業でログ解析・現在値再照合まで完了。対象欄以外のRAWを維持し、各復元後D5全100文字が一致。SP20件・D5 21件は正常、再送0、ログ破棄0。ATE最短間隔101.0453ms。上記「実機送信未実施」は実装時点の履歴であり、本追記で代表値試験まで確認済み。全境界値、実動作、電源切入保持は未確認。[項目別PARAM実機記録](Parameter_Item_Hardware_Test_20261110.md)。

## 2026-11-09 バッテリ診断BC Host実装

- r1 p.26の評価用コマンド。BATT_CHECK_STARTはBC DATA1、BATT_CHECK_STOPはBC DATA0。両方T2=6000ms、正常応答DATA30文字を検証する。STOPの空応答を受理する暫定FW吸収は行わない（OI-06継続）。
- STARTは送信前・未接続エラー前に旧BCをINVALIDにし、失敗しても戻さない。正常Transaction後にDATA／STATUSをINVALID、全30文字HEX検証と8結果項目のDecode完了後のみBCをVALIDとする。Decode失敗でもDATA／STATUSはINVALIDを保持。
- STOP成功／ambiguousはBC／DATA／STATUSをINVALID。STOP応答の診断データは完全性を検証するがBC CacheをVALIDにしない。SQE／PME／CME等の明確な拒否では、STARTのBC以外のCacheを保持し、STOPは従前Cacheを保持する。
- BC_MODE?／BC_V1?／BC_V2?／BC_I1?／BC_I2?／BC_TEMP?／BC_SOC?／BC_IR?はBC Cacheのみ参照し、自動Refreshも自動STARTも行わない。D0の寿命診断欄をBC Cacheへ昇格しない。
- MODEは受信1桁HEXを10進へ変換。0=データなし、1／2=充電測定、3=BC測定、11／12／13=各取得エラー（r1 p.40）。MODE13の詳細はOI-07継続。PicoはMODEで製品PASS／FAILを判定せず、受信した非ゼロ値を0へ補正しない。MODE取得エラーでもProtocol成功ならOKを返す。
- V1／V2はV、I1／I2はA（各RAW整数を1000で除算）、TEMPはsigned ℃、SOCはsigned ％、IRはmΩ。値や範囲をPicoで合否判定しない。
- 放電中・充電中等の受付条件はr1 p.17／18／26で規定。PicoでCacheから製品受付可否を推測せず、NF55GのSQE／PMEを返す。AUTO_CHARGE無効でもBCは実行される仕様なので、事前設定変更やCN／CFの自動送信をしない。
- Transactionは常に1件。STOPは処理中のSTARTへ割り込む緊急停止機能ではなく、通信完了後の別要求として扱う。ATEは応答完了後に次を送信し、6秒T2と規定再送を考慮したATE側timeoutを設定する。
- 全256件Host／Mock成功。Pico配置・実機送信・バッテリ接続評価は未実施。実機前の条件確認とOI-06／07の設計確認を残す。

## 2026-11-09 寿命情報設定SLの正式実装

2026-11-10実機確認: LIFE_SET_123による12.3％設定と、LIFE_SET_RAW=00000000による元値0.0％復元を、新規D0積算RAW000→07B→000で確認。SL正常応答DATA0文字、各46ms、cmd/rsp retry0、DATA無効化、STATUS／INFO維持、CSVのSD/PC SHA-256一致を確認。OFF期間欄はSLで変化し、寿命値の復元後も元に戻らない。通常値1点の確認であり、範囲外・不正RAW・4095・電源保持・製品動作は未確認。OI-08はOpen継続。[実機結果](Life_Set_Hardware_Test_20261110.md)。以降の未配置・未送信表記は実装時点の履歴。

- LIFE_SET_<VALUE>: 符号付き10進整数（0.1％単位）→最小3桁大文字HEX＋予約00000。0～4095検査・4095禁止・丸め・切捨てなし。123→07B00000、4095→FFF00000、4096→100000000（9文字）、-1→-0100000。不正数値書式と余分な引数は拒否する。
- LIFE_SET_RAW=<ASCII>: DATAを直接指定し、値・HEX・長さ・予約を検査しない。明示=の空DATAも送る。制御文字／非ASCIIはATE行・NFフレーム区切り維持のため拒否。共通ATE行長上限と行前後のstripは既存のまま。RAW内部空白は=形式で保持する。試験ロック・量産使用モード制限なし。
- 両入口ともSL、T2=100ms、正常応答DATA0文字。成功／ambiguousは既定どおりDATAだけINVALID、PME／SQE／CMEはCache維持。自動Refresh・値のCache反映・製品PASS／FAIL判定を行わない。
- r1 p.41の積算BATT_DEGを明示DATA_REFRESH→BATT_DEG_TOTAL?で確認。表示はRAW整数÷10、FFFは409.5。受理・PMEのどちらでも新規D0を読戻しに使う。設定値の根拠はD0積算欄で、LIFE_BATT_DEG?とは区別する。
- r1 p.23／32／39のOFF期間クリア条件を実機手順へ記載。元寿命値を戻してもOFF期間データは復元されない。試験準備でSC／D2／D3／D4を自動送信しない。
- OI-08継続、量産使用未確定。今回Pico追加配置・実製品送信なし。[実機試験手順](Life_Set_Hardware_Test_Procedure_20261109.md)を参照。
