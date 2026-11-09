# ATE Command Master

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.0

## 1. 共通原則
- ATE UARTの要求・応答終端はCRLF（2026-09-10ユーザー確認）。受信は分割可能。
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
| DATA_REFRESH | D0 | 600ms provisional | DATA | D0 327 chars |
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
- D0はNF CMD `D0`、DATAなし、T2=600ms暫定、応答DATA 327文字。完全Decode後にDATA CacheのみをVALIDにする。
  D0内STATUSはraw保持、Manufacturing/Parameterもraw保持とし、STATUS/INFO Cacheへ昇格しない。
- D0の各DATA QueryはDATA Cacheのみ参照し、自動Refreshしない。未取得・INVALID時は`ERR:CACHE_INVALID`。
- OI-03は未解決。PicoはD0後のCHARGE_END等の製品側副作用を推測・抑止・補正しない。ATE/設計側がr1/final FWとの整合を確認する。
- 引数なし。余分な引数・`=`指定は `ERR:UNEXPECTED_PAYLOAD`（Cache変更・送信なし）。
- Refreshは対象Cacheを先にINVALIDにし、D0=327文字/T2=600ms暫定、D1=15文字/T2=100ms、D5=100文字/T2=100msで通信する。
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
| ERP_SET_0_0 etc. | SE | BURST+PS_OFF_CHARGE+00 | 100 | DATA/STATUS | STATUS_REFRESH |
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

TEST_START後にQRを読み、試験終了のTEST_ENDで最終Self Checkを実行する。PICO_SELF_CHECK?には既存のATE_UART／NF55_UART／RTC／LOGGERに加え、試験終了後はTEST_LOGGER（その試験のSD保存状態）、TEST_LOG_DROP（OKまたは破棄件数）を含める。NGは装置異常であり製品FAILではない。復帰後も直前試験の異常を保持し、次のTEST_STARTで初期化する。TEST_START／TEST_ENDのOKはログ保存成功や製品PASSの意味ではない。

ログ名は日時を基本とし、試験中に取得したQRの末尾6桁の数字S/Nを終了時に付加する。正式QR取得コマンド・物理入力はOI-23で引き続き管理し、今回新設しない。

## 2026-11-09 D4運用とCLEAR試験

D4は副作用のため量産では使用しない。D4-TIM-01は未解決のまま保守課題として保持し、CLEAR試験を優先する。CLEAR_ALL／POWER／BATTはCDのDATA0／1／2、T2=500ms。CLEAR_LOGはCLのDATAなし、T2=1000ms。r1 p.35に従い正常応答はどちらもDATA0文字。成功と成否不明時は既存Cache規則に従い無効化し、応答から昇格しない。CDで満充電情報等が初期化され初期充電が動作し得るため、今回ユーザー確認済みのバッテリ未接続条件で通信試験する。

2026-11-09 CLEAR実機結果: POWER／BATT／ALL／LOGの4種がOK、19／19／20／19ms、再送0、BCC一致。CD後のDATA／STATUS無効化、CL後の全EL／OL無効化と96件の空ログ表現を確認。CLEAR_ALLは先行個別消去後の0維持を確認したもので、単独非ゼロ値消去は未検証。Host／Mock全203件合格。詳細・制限はReal_Hardware_Test_Log.md。
