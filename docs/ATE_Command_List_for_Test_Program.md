# ATE Command List for Test Program
Revision: Rev.0-draft
Date: 2026-09-01

## 1. 目的
本書は、NF55G Pico 2 試験治具に対して ATE 試験プログラムから送信するコマンド一覧である。
試験プログラム作成者が、コマンド名、引数形式、応答形式、NF55G 通信有無、Cache 影響、および後続確認を確認するために使用する。

## 2. 適用範囲と注意
- 本書は `docs/ATE_Command_Master.md` Rev.0 を元にした試験プログラム作成者向け一覧である。
- 個別 Query は Cache のみ参照し、NF55G 通信を行わない。
- Refresh 系、Control/Set/Clear 系は NF55G Transaction を発生させる。
- Control/Set/Clear の `OK` は Protocol Transaction 成功のみを意味し、製品 PASS/FAIL や製品動作成立を意味しない。
- 製品動作成立確認は、ATE が `STATUS_REFRESH` と外部測定器で行う。
- `FW_UPDATE` は試験治具から NF55G へ送信しない。応答は `ERR:FU_DISABLED` とする。
- 未確定事項は `docs/Open_Issues.md` を参照し、試験プログラム側で確定扱いにしない。

## 3. 共通応答
| 条件 | ATE 応答 | 備考 |
|---|---|---|
| Refresh 成功 | `OK` | 対象 Cache が VALID になる。 |
| Control/Set/Clear 成功 | `OK` | Protocol 成功のみ。必要な後続確認を ATE が実施する。 |
| Query 成功 | 値 | 半角 ASCII 英数字、10 進数値、または FD の 64 ASCII HEX。 |
| Query 対象 Cache INVALID | `ERR:CACHE_INVALID` | 個別 Query から自動 Refresh しない。 |
| Parser/形式エラー | `ERR:<reason>` | 引数長、形式、未対応コマンドなど。 |
| NF55G エラー応答 | `ERR:CME` / `ERR:PME` / `ERR:SQE` / `ERR:HWE` / `ERR:MCM` / `ERR:FUE` | D6 error response を ATE へ返す。 |
| Timeout/BCC/Frame 最終異常 | `ERR:<reason>` | 実行成否不明時は `ambiguous=True` とし、関連 Cache を INVALID にする。 |
| FW_UPDATE | `ERR:FU_DISABLED` | NF55G へ `FU` を送信しない。 |

## 4. Refresh / Read コマンド
| ATE コマンド | 引数形式 | NF CMD | NF DATA | T2 | NF55G 通信 | 成功時 Cache | 後続 Query / 確認 | 注意 |
|---|---|---|---|---:|---|---|---|---|
| `DATA_REFRESH` | なし | `D0` | なし | 600 ms provisional | あり | `DATA` VALID | DATA Cache Query | D0 内の STATUS/INFO は各 Cache へ昇格しない。 |
| `STATUS_REFRESH` | なし | `D1` | なし | 100 ms | あり | `STATUS` VALID | STATUS Cache Query | EB Event では STATUS Cache を更新しない。 |
| `INFO_REFRESH` | なし | `D5` | なし | 100 ms | あり | `INFO` VALID | INFO Cache Query | Manufacturing 50 chars + Parameter 50 chars。 |
| `D2_REFRESH` | なし | `D2` | なし | 100 ms | あり | `D2` VALID | D2 専用確認 | 量産原則未使用。 |
| `D3_REFRESH` | なし | `D3` | なし | 200 ms | あり | `D3` VALID | D3 専用確認 | LIFE_CALC clear 副作用あり。 |
| `D4_MAINT_READ` | なし | `D4` | なし | 100 ms | あり | `D4` VALID | D4 専用確認 | AC_FAIL_COUNT clear 副作用あり。 |
| `AR_REFRESH` | なし | `AR` | なし | Open Issue | あり | `AR` VALID | AR Cache Query | OI-12: AR T2 final value 未確定。 |
| `FD_READ_xxxxxx` | `xxxxxx` = 6 桁 HEX address | `FD` | address | 100 ms | あり | `FD` VALID | FD Query / raw 参照 | FD は 32 byte を 64 ASCII HEX のまま扱う。 |
| `EL_REFRESH_01` / `09` / `17` / `25` | block start | `EL` | start no | 100 ms | あり | EL block VALID | `EL_<NN>_*?` | 8 records/block。START_NO 一致必須。 |
| `OL_REFRESH_01` / `09` / `17` / `25` / `33` / `41` / `49` / `57` | block start | `OL` | start no | 100 ms | あり | OL block VALID | `OL_<NN>_*?` | 8 records/block。START_NO 一致必須。 |

## 5. Control / Set / Clear コマンド
| ATE コマンド | 引数形式 | NF CMD | NF DATA | T2 | NF55G 通信 | 成功時 INVALID Cache | 推奨後続確認 | 注意 |
|---|---|---|---|---:|---|---|---|---|
| `PARAM_<ITEM>_<VALUE>` | item/value から 50 chars PARAM を生成 | `SP` | 50 chars | 100 ms | あり | `DATA` / `STATUS` / `INFO` | `INFO_REFRESH` | 詳細 item mapping は実装表と照合する。 |
| `PARAM_RESET` | なし | `RP` | なし | 100 ms | あり | `DATA` / `STATUS` / `INFO` | `INFO_REFRESH` | Parameter 初期化。 |
| `ERP_SET_0_0` 等 | mode fields | `SE` | `BURST+PS_OFF_CHARGE+00` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` | ERP 設定形式は Command Master に従う。 |
| `CLOCK_SYNC` | `YYMMDDHHMMSS` | `SC` | `YYMMDDHHMMSS` | 100 ms | あり | `DATA` / `STATUS` | `DATA_REFRESH` | Pico-side RTC 設定とは別。 |
| `SERIAL_<ITEM>_<VALUE>` | item/value から 50 chars SERIAL を生成 | `SS` | 50 chars | 100 ms | あり | `DATA` / `INFO` | `INFO_REFRESH` | ASCII text は leading zero を保持。 |
| `LIFE_SET_<VALUE>` | value + reserve | `SL` | 3 chars + reserve | 100 ms | あり | `DATA` | `DATA_REFRESH` | OI-08: out-of-range PME behavior 未確定。 |
| `BATT_CHECK_START` | なし | `BC` | `1` | 6000 ms | あり | `DATA` / `STATUS`; BC refreshed | BC Query | Protocol 成功後も ATE 側確認が必要。 |
| `BATT_CHECK_STOP` | なし | `BC` | `0` | 6000 ms | あり | `BC` / `DATA` / `STATUS` | `STATUS_REFRESH` | OI-06: current FW behavior 要確認。 |
| `CHARGE_ON` | なし | `CN` | `1` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部電流測定 | `OK` は充電成立を意味しない。 |
| `CHARGE_ON_STOP` | なし | `CN` | `0` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部電流測定 | `OK` は停止成立を意味しない。 |
| `CHARGE_OFF` | なし | `CF` | `1` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部電流測定 | `OK` は放電成立を意味しない。 |
| `CHARGE_OFF_CLEAR` | なし | `CF` | `0` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部電流測定 | `OK` は clear 成立を意味しない。 |
| `BACKUP_ENABLE` | なし | `BE` | なし | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部 12V 測定 | `OK` は出力成立を意味しない。 |
| `BACKUP_OFF` | なし | `BF` | なし | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部 12V 測定 | `OK` は停止成立を意味しない。 |
| `OUTPUT_RESTART` | なし | `OR` | なし | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部 12V 測定 | OI-09: restart active 時の挙動要確認。 |
| `CLEAR_ALL` | なし | `CD` | `0` | 500 ms | あり | `DATA` / `STATUS` / `BC` | `DATA_REFRESH` + `STATUS_REFRESH` | 積算/状態 clear 系。 |
| `CLEAR_POWER` | なし | `CD` | `1` | 500 ms | あり | `DATA` / `STATUS` / `BC` | `DATA_REFRESH` + `STATUS_REFRESH` | 電源系 clear。 |
| `CLEAR_BATT` | なし | `CD` | `2` | 500 ms | あり | `DATA` / `STATUS` / `BC` | `DATA_REFRESH` + `STATUS_REFRESH` | 電池系 clear。 |
| `CLEAR_LOG` | なし | `CL` | なし | 1000 ms | あり | all `EL` / `OL` | EL/OL refresh | Event / Operation log clear。 |
| `AD_<TYPE>_<POINT>_<VALUE>` | 係数種別/point/value | `AD` | 10 chars | Open Issue | あり | `DATA` / `AR` | `AR_REFRESH` | OI-05, OI-12 関連。 |
| `FW_UPDATE` | なし | `FU` | BLOCKED | - | なし | なし | なし | 常に `ERR:FU_DISABLED`。NF55G へ送信しない。 |

## 6. DATA Cache Query
事前に `DATA_REFRESH` が成功していること。各 Query は NF55G 通信を行わない。

| ATE Query | 応答形式 | 単位 / 備考 |
|---|---|---|
| `NF55_DATE?` | `YYYYMMDD` | NF55G D0 TIME。 |
| `NF55_TIME?` | `HHMMSS` | NF55G D0 TIME。 |
| `NF55_DATETIME?` | `YYYYMMDD_HHMMSS` | NF55G D0 TIME。 |
| `VOUT12?` | decimal | V。 |
| `IOUT12?` | decimal | A。 |
| `BATT_VOLT?` | decimal | V。 |
| `CHG_VOLT?` | decimal | V。 |
| `CHG_CURR?` | decimal | A。 |
| `BATT_CURR?` | decimal | A。 |
| `BATT_SOC_WH?` | signed decimal | %。 |
| `BATT_SOC_MAH?` | signed decimal | %。 |
| `BATT_TEMP?` | signed decimal | degC。 |
| `ADU_TEMP?` | signed decimal | degC。 |
| `BBU_TEMP?` | signed decimal | degC。 |
| `FAN_RPM?` | decimal | rpm。 |
| `FAN_LEVEL?` | decimal | step。 |
| `AC_OFF_HOUR?` | decimal | 0.1 h scale。 |
| `PS_OFF_HOUR?` | decimal | 0.1 h scale。 |
| `AVE_OFF_TEMP?` | signed decimal | degC。 |
| `OFF_CHARGE_HOUR?` | decimal | 0.1 h scale。 |
| `AVE_CHARGE_TEMP?` | signed decimal | degC。 |
| `OFF_CHARGE?` | decimal | %。 |
| `OFF_BATT_DEG?` | decimal | 0.1 % scale。 |
| `CHARGE_DATA?` | decimal | LIFE_CALC flag/value。 |
| `CHARGE_END?` | decimal | LIFE_CALC flag/value。 |
| `LIFE_BATT_CHARGE?` | decimal | %。 |
| `LIFE_BATT_TEMP?` | signed decimal | degC。 |
| `LIFE_BATT_DEG?` | decimal | 0.1 % scale。 |
| `TOTAL_ADU_TEMP?` | decimal | accumulated。 |
| `TOTAL_ADU_HOUR?` | decimal | hour。 |
| `AC_FAIL_COUNT?` | decimal | count。 |
| `AC_LOW_COUNT?` | decimal | count。 |
| `BACKUP_COUNT?` | decimal | count。 |
| `BATT_DEG_TOTAL?` | decimal | 0.1 % scale。 |
| `TOTAL_BATT_HOUR?` | decimal | hour。 |
| `BATT_DISCHARGE_COUNT?` | decimal | count。 |
| `BATT_CHARGE_COUNT?` | decimal | count。 |
| `BATT_TTL_DISCHARGE?` | decimal | mAh。 |
| `BATT_TTL_CHARGE?` | decimal | mAh。 |
| `TOTAL_BATT_TEMP?` | decimal | accumulated。 |
| `BATT_TEMP_AVE?` | signed decimal | degC。 |
| `BATT_TEMP_MAX?` | signed decimal | degC。 |
| `BATT_TEMP_MIN?` | signed decimal | degC。 |

## 7. STATUS Cache Query
事前に `STATUS_REFRESH` が成功していること。応答は原則 `0` / `1` の flag 値とする。

| ATE Query | 応答形式 | 備考 |
|---|---|---|
| `PS_ON?` | `0` / `1` | STATUS bit。 |
| `BURST_ON?` | `0` / `1` | STATUS bit。 |
| `BURST?` | `0` / `1` | STATUS bit。 |
| `PS_OFF_CHARGE?` | `0` / `1` | STATUS bit。 |
| `RESTART_READY?` | `0` / `1` | STATUS bit。 |
| `BACKUP_READY?` | `0` / `1` | STATUS bit。 |
| `CHARGE_READY?` | `0` / `1` | STATUS bit。 |
| `BATT_CHECK_RUN?` | `0` / `1` | STATUS bit。 |
| `CHARGE_OFF_STATUS?` | `0` / `1` | STATUS bit。 |
| `CHARGE_ON_STATUS?` | `0` / `1` | STATUS bit。 |
| `BATT_ON?` | `0` / `1` | STATUS bit。 |
| `BATT_LOW?` | `0` / `1` | STATUS bit。 |
| `S_CHARGE_ON?` | `0` / `1` | STATUS bit。 |
| `CHARGE_OK?` | `0` / `1` | STATUS bit。 |
| `CHARGER_ON?` | `0` / `1` | STATUS bit。 |
| `FAN_WNG?` | `0` / `1` | STATUS bit。 |
| `ADU_TEMP_WNG?` | `0` / `1` | STATUS bit。 |
| `OC_OFF_H?` | `0` / `1` | STATUS bit。 |
| `PFC_OV?` | `0` / `1` | STATUS bit。 |
| `FAN_FAIL?` | `0` / `1` | STATUS bit。 |
| `BBU_TEMP_WNG?` | `0` / `1` | STATUS bit。 |
| `BBU_FAIL?` | `0` / `1` | STATUS bit。 |
| `CHG_LV?` | `0` / `1` | STATUS bit。 |
| `CHG_OV?` | `0` / `1` | STATUS bit。 |
| `CHG_OC?` | `0` / `1` | STATUS bit。 |
| `BATT_TEMP_WNG?` | `0` / `1` | STATUS bit。 |
| `BATT_TEMP_ALM?` | `0` / `1` | STATUS bit。 |
| `BATT_LV?` | `0` / `1` | STATUS bit。 |
| `BATT_OV?` | `0` / `1` | STATUS bit。 |
| `BATT_LIFE?` | `0` / `1` | STATUS bit。 |
| `BATT_MCN?` | `0` / `1` | STATUS bit。 |
| `BATT_P_FAIL?` | `0` / `1` | STATUS bit。 |
| `BATT_DCN?` | `0` / `1` | STATUS bit。 |
| `12V_OV?` | `0` / `1` | STATUS bit。 |
| `12V_LV?` | `0` / `1` | STATUS bit。 |
| `12V_OC?` | `0` / `1` | STATUS bit。 |
| `12V_OC_OFF_L?` | `0` / `1` | STATUS bit。 |

## 8. INFO Cache Query
事前に `INFO_REFRESH` が成功していること。ASCII text は leading zero を保持する。

| ATE Query | 応答形式 | 備考 |
|---|---|---|
| `FW_REV?` | ASCII text | Firmware revision。 |
| `UNIT_REV?` | ASCII text | Unit revision。 |
| `UNIT_LOT?` | ASCII text | Unit lot。 |
| `UNIT_SERIAL?` | ASCII text | Unit serial。 |
| `ADU_REV?` | ASCII text | ADU revision。 |
| `ADU_LOT?` | ASCII text | ADU lot。 |
| `ADU_SERIAL?` | ASCII text | ADU serial。 |
| `BBU_REV?` | ASCII text | BBU revision。 |
| `BBU_LOT?` | ASCII text | BBU lot。 |
| `BBU_SERIAL?` | ASCII text | BBU serial。 |
| `PS_ON_BACKUP?` | decimal | Parameter。 |
| `AC_LINK?` | decimal | Parameter。 |
| `AUTO_CHARGE?` | decimal | Parameter。 |
| `EVENT_ENABLE?` | decimal | Parameter。 |
| `MAX_BACKUP_TIME?` | decimal | min。 |
| `MIN_BACKUP_TIME?` | decimal | sec。 |
| `RESTART_TIME?` | decimal | sec。 |
| `BATT_LOW_THD?` | decimal | %。 |
| `BATT_CAP_MAH?` | decimal | mAh。 |
| `BATT_CAP_WH?` | decimal | Wh。 |
| `CHG_IR_THD?` | decimal | mOhm。 |
| `BATT_WNG_THD?` | signed decimal | degC。 |
| `BATT_ALM_THD?` | signed decimal | degC。 |
| `ADU_TEMP_THD?` | signed decimal | degC。 |
| `BBU_TEMP_THD?` | signed decimal | degC。 |
| `FAN_WNG_THD?` | decimal | rpm。 |

## 9. BC / AR / EL / OL / FD Query
| ATE Query | 事前 Refresh | 応答形式 | 備考 |
|---|---|---|---|
| `BC_MODE?` | `BATT_CHECK_START` or BC refresh | decimal | BC mode。 |
| `BC_V1?` | `BATT_CHECK_START` or BC refresh | decimal | V。 |
| `BC_V2?` | `BATT_CHECK_START` or BC refresh | decimal | V。 |
| `BC_I1?` | `BATT_CHECK_START` or BC refresh | decimal | A。 |
| `BC_I2?` | `BATT_CHECK_START` or BC refresh | decimal | A。 |
| `BC_TEMP?` | `BATT_CHECK_START` or BC refresh | signed decimal | degC。 |
| `BC_SOC?` | `BATT_CHECK_START` or BC refresh | signed decimal | %。 |
| `BC_IR?` | `BATT_CHECK_START` or BC refresh | decimal | mOhm。 |
| `AR_DISCHG_I_P1_ADC?` / `REF?`, `P2_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |
| `AR_BATT_V_P1_ADC?` / `REF?`, `P2_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |
| `AR_ACDC12V_V_P1_ADC?` / `REF?`, `P2_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |
| `AR_BATT_CHG_P1_ADC?` / `REF?`, `P2_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |
| `AR_12VOUT_V_P1_ADC?` / `REF?`, `P2_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |
| `EL_<NN>_DATEHOUR?` | `EL_REFRESH_*` | `YYMMDDHH` or `00000000` | NN=01..32。No log は `00000000`。 |
| `EL_<NN>_ID?` | `EL_REFRESH_*` | decimal | NN=01..32。No log は `255`。 |
| `OL_<NN>_DATEHOUR?` | `OL_REFRESH_*` | `YYMMDDHH` or `00000000` | NN=01..64。No log は `00000000`。 |
| `OL_<NN>_ID?` | `OL_REFRESH_*` | decimal | NN=01..64。No log は `255`。 |
| `FD_DATA?` | `FD_READ_xxxxxx` | 64 ASCII HEX | FD は decode せず raw のまま返す。 |

## 10. RTC / Diagnostic / Logger コマンド
| ATE コマンド | 引数形式 | NF55G 通信 | 応答形式 | 備考 |
|---|---|---|---|---|
| `RTC_DATE?` | なし | なし | `YYYYMMDD` | Pico-side DS3231 を参照。 |
| `RTC_TIME?` | なし | なし | `HHMMSS` | Pico-side DS3231 を参照。 |
| `RTC_DATETIME?` | なし | なし | `YYYYMMDD_HHMMSS` | Pico-side DS3231 を参照。 |
| `RTC_SET_YYYYMMDD_HHMMSS` | date/time | なし | `OK` or `ERR:<reason>` | NF55G `SC` / `CLOCK_SYNC` とは別。 |
| `RTC_CHECK?` | なし | なし | `OK` / `NG` | RTC access check。 |
| `*IDN?` | なし | なし | ASCII text | Pico fixture identification。 |
| `PICO_SELF_CHECK?` | なし | なし | `OK` / `NG` / detail | Pico local self check。 |
| `NF_COMM_CHECK?` | なし | あり | `OK` / `ERR:<reason>` | NF55G communication smoke check。 |
| `COMM_STATUS?` | なし | なし | ASCII status | Last communication status。 |
| `RETRY_COUNT?` | なし | なし | decimal/detail | Command retry と Response retry は別管理。 |
| `TEST_START` | なし | なし | `OK` / `ERR:<reason>` | Logger session start。 |
| `TEST_END` | なし | なし | `OK` / `ERR:<reason>` | Logger queue drain / flush / close。 |
| `LOG_CONT_START` | なし | なし | `OK` / `ERR:<reason>` | Continuous logging start。 |
| `LOG_CONT_STOP` | なし | なし | `OK` / `ERR:<reason>` | Continuous logging stop。 |
| `SD_STATUS?` | なし | なし | `OK` / `NO_CARD` / `MOUNT_ERR` / `OPEN_ERR` / `WRITE_ERR` / `FULL` | SD failure は NF55G 通信を停止しない。 |
| `SD_USAGE?` | なし | なし | `used/limit` | 90% of SD capacity を運用上限とする。 |
| `LOG_DROP_COUNT?` | なし | なし | decimal | RAM Queue overflow/drop count。 |
| `SD_REINIT` | なし | なし | `OK` / `ERR:<reason>` | SD reinitialization。 |

## 11. 試験プログラム作成時の基本シーケンス
| 目的 | 推奨シーケンス | 判定主体 |
|---|---|---|
| 初期情報取得 | `INFO_REFRESH` -> INFO Query | ATE |
| 状態確認 | `STATUS_REFRESH` -> STATUS Query | ATE |
| 計測値確認 | `DATA_REFRESH` -> DATA Query + 外部測定 | ATE |
| Control 後確認 | Control command -> `STATUS_REFRESH` -> STATUS Query + 外部測定 | ATE |
| 設定変更後確認 | Set command -> `INFO_REFRESH` or `DATA_REFRESH` | ATE |
| ログ確認 | `EL_REFRESH_*` / `OL_REFRESH_*` -> EL/OL Query | ATE |

## 12. Word 出力
この Markdown から Word 形式のコマンド一覧を生成する場合は、リポジトリルートで次を実行する。

```powershell
C:\Users\m_yamada\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_ate_command_list_docx.py
```

出力先:
- `docs/ATE_Command_List_for_Test_Program.docx`

## 13. 参照仕様
- `AGENTS.md`
- `docs/ATE_Command_Master.md`
- `docs/Data_Decode_Master.md`
- `docs/Cache_Master.md`
- `docs/Logger_SD_Spec.md`
- `docs/Open_Issues.md`
