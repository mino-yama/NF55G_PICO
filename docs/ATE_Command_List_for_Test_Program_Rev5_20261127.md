# ATE Command List for Test Program

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D0のT2のみ2026-11-11ユーザー指定によりr2事前確認版p.17／28の300msを採用する。r2の他項目は一括採用しない。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.5
Date: 2026-11-27

2026-11-27 校正改版を実装：校正点はA/B、Cache書込みは回路＋点の一重指定、直接ADもA/B指定へ切替。必須3回路×A/Bの上下限をルートcalibration_limits.pyで管理し、送信直前に共通検証する。旧形式は拒否。現行契約は[校正実装仕様Rev.0](Calibration_AB_Implementation_20261127_Rev0.md)を優先する。以下の過去日付の旧点表記・実装許可待ちは履歴であり現行書式ではない。サンプル個体限定・AR小数保持等のOpen Issueは維持。親Picoへの配置・起動・保護処理確認は完了。[親Pico配置結果Rev.1](Calibration_AB_Pico_Deployment_20261127_Rev1/Result.md)参照。実測校正は未実施。

## 1. 目的
本書は、2026-11-27時点の開発状況に基づき、NF55G Pico 2 試験治具に対して ATE 試験プログラムから送信するコマンド一覧である。
試験プログラム作成者が、コマンド名、引数形式、応答形式、NF55G 通信有無、Cache 影響、および後続確認を確認するために使用する。

## 2. 適用範囲と注意
- 本書は `docs/ATE_Command_Master.md` と2026-11-27までの追加仕様・実装・実機記録を元にした試験プログラム作成者向け一覧である。
- 個別 Query は Cache のみ参照し、NF55G 通信を行わない。
- Refresh 系、Control/Set/Clear 系は NF55G Transaction を発生させる。
- Control/Set/Clear の `OK` は Protocol Transaction 成功のみを意味し、製品 PASS/FAIL や製品動作成立を意味しない。
- 製品動作成立確認は、ATE が `STATUS_REFRESH` と外部測定器で行う。
- `FW_UPDATE` は試験治具から NF55G へ送信しない。応答は `ERR:FU_DISABLED` とする。
- 未確定事項は `docs/Open_Issues.md` を参照し、試験プログラム側で確定扱いにしない。

### 実装有無の凡例

- 「実装有無」の ※ はATEから実行できる機能を示す。空欄は正式ATE機能として未実装。実機確認済み・量産使用可を意味しない。
- 実装状況は2026-11-26の共通Command Coreおよび親Picoの追加ATE入口を基準とする。予定コマンドの通信・Cache・応答欄は設計内容であり、空欄の機能を現在実行できる意味ではない。
- FW_UPDATEの ※ は禁止応答処理の実装を示す。FU送信機能ではない。
- ATE要求はCRLFで送る。応答終端はATE_RESPONSE_TERMINATORに従い、現行ソース既定はCR。CR／LF／CRLFから設定するためATEの受信設定を配置FWに合わせる。ATEは応答完了後に次のコマンドを送る。NF55G Transactionは常に1件とする。
- ATE側UARTは57600bps、8 data bits、parityなし、1 stop bit。NF55G側38400bps／8E1と混同しない。
- 略語・用語は第15節、使用例と注意事項は第14節、実機確認範囲は第16節を参照する。
- QR／測定器の追加機能は対応FW・配線・有効設定が必要。ソース既定はQR_HOST_ENABLED=False／EXTERNAL_INSTRUMENT_ENABLED=False／CALIBRATION_SAMPLE_ENABLED=False／QR_HOST_ARM_ENABLED=False。評価機への配置実績と、任意の治具で利用可能な状態は区別する。
- 最新の追加入口は第10.1～10.6節、ATEの順序付き操作手順は第14.13～14.18節に示す。※は条件付き診断入口にも付けるため、使用条件を必ず確認する。
- 本改訂はATE実機確認の準備資料であり、今回の実機デバッグ・FW配置は行わない。現行ソースと配置済みFWは別に確認する。

### 実機確認を始める前の確認

ATE接続は57600bps／8N1、要求はCRLF、応答は配置FWの設定に従う（現行ソース既定CR）。コマンドを並列送信せず、一行の応答完了を待つ。NF55G側は38400bps／8E1。以下の表は使用可否を切り分ける入口であり、動作確認の完了を宣言するものではない。

| 機能 | 実機確認前に確認する条件 | 今回の資料での扱い |
|---|---|---|
| 製品RefreshとQuery | 接続製品、治具FW、RTC、SD、ATE経路 | 既存の正式入口。既存制約を維持。 |
| 7355取得 | ADC言語／USB CDC、対応親FW、測定器HOST 20261125.2、外部測定器有効 | 第14.13～14.14節。7355の現行運用はADC。 |
| Cache採用の校正ADとAR | CALIBRATION_SAMPLE_ENABLED、同一試行のD5でS1.14B／000001、照会済み測定Cache | 特定サンプル診断。直接指定は第10.6節。量産承認とは区別。第14.16節。 |
| QRからSS | QR_HOST_ENABLED、QR用HOST・スキャナー・配線、対象ラベルをATEで照合 | 現行単方向はARMED応答。第14.15節。 |
| 双方向QR候補 | QR_HOST_ARM_ENABLEDと対応HOST・双方向配線 | PENDING応答の試験モード。正式採用・待ち条件は未確定。第14.17節。 |

*IDN?だけで全モジュールの版と有効設定を確認できるとは扱わない。配置記録・設定値と照合する。TEST_STARTの実機実績は最長11.218秒であり、T2をATEの全体待ち時間に流用しない。量産ATEの待ち時間は別途確認する。

## 3. 共通応答
| 条件 | ATE 応答 | 備考 |
|---|---|---|
| Refresh 成功 | `OK` | 対象 Cache が VALID になる。 |
| Control/Set/Clear 成功 | `OK` | Protocol 成功のみ。必要な後続確認を ATE が実施する。 |
| Query 成功 | 値 | 半角 ASCII 英数字、10 進数値、または FD の 64 ASCII HEX。 |
| Query 対象 Cache INVALID | `ERR:CACHE_INVALID` | 個別 Query から自動 Refresh しない。 |
| Parser/形式エラー | `ERR:<reason>` | 引数長、形式、未対応コマンドなど。 |
| NF55G エラー応答 | `ERR:CME` / `ERR:PME` / `ERR:SQE` / `ERR:HWE` / `ERR:MCM` / `ERR:FUE` | r1 error response を ATE へ返す。 |
| Timeout/BCC/Frame 最終異常 | `ERR:<reason>` | 実行成否不明時は `ambiguous=True` とし、関連 Cache を INVALID にする。 |
| FW_UPDATE | `ERR:FU_DISABLED` | NF55G へ `FU` を送信しない。 |

## 4. Refresh / Read コマンド
| ATE コマンド | 引数形式 | NF CMD | NF DATA | T2 | NF55G 通信 | 成功時 Cache | 後続 Query / 確認 | 注意 | 実装有無 |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `DATA_REFRESH` | なし | `D0` | なし | 300 ms | あり | `DATA` VALID | DATA Cache Query | D0 内の STATUS/INFO は各 Cache へ昇格しない。 | ※ |
| `STATUS_REFRESH` | なし | `D1` | なし | 100 ms | あり | `STATUS` VALID | STATUS Cache Query | EB Event では STATUS Cache を更新しない。 | ※ |
| `INFO_REFRESH` | なし | `D5` | なし | 100 ms | あり | `INFO` VALID | INFO Cache Query | Manufacturing 50 chars + Parameter 50 chars。 | ※ |
| `D2_REFRESH` | なし | `D2` | なし | 100 ms | あり | `D2` VALID | D2 専用確認 | 量産原則未使用。 | ※ |
| `D3_REFRESH` | なし | `D3` | なし | 200 ms | あり | `D3` VALID | D3 専用確認 | LIFE_CALC clear 副作用あり。 | ※ |
| `D4_MAINT_READ` | なし | `D4` | なし | 100 ms | あり | `D4` VALID | D4 専用確認 | AC_FAIL_COUNT clear 副作用あり。量産では使用しない。D4-TIM-01継続。 | ※ |
| `AR_REFRESH` | なし | `AR` | なし | Open Issue | あり | `AR` VALID | AR Cache Query | OI-12: AR T2 final value 未確定。 |  |
| `FD_READ_xxxxxx` | `xxxxxx` = 6 桁 HEX address | `FD` | address | 100 ms | あり | `FD` VALID | FD Query / raw 参照 | FD は 32 byte を 64 ASCII HEX のまま扱う。 | ※ |
| `EL_REFRESH_01` / `09` / `17` / `25` | block start | `EL` | start no | 100 ms | あり | EL block VALID | `EL_<NN>_*?` | 8 records/block。START_NO 一致必須。 | ※ |
| `OL_REFRESH_01` / `09` / `17` / `25` / `33` / `41` / `49` / `57` | block start | `OL` | start no | 100 ms | あり | OL block VALID | `OL_<NN>_*?` | 8 records/block。START_NO 一致必須。 | ※ |

## 5. Control / Set / Clear コマンド
| ATE コマンド | 引数形式 | NF CMD | NF DATA | T2 | NF55G 通信 | 成功時 INVALID Cache | 推奨後続確認 | 注意 | 実装有無 |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `PARAM_<ITEM>_<VALUE>` | 項目名と10進整数をコマンド名内に指定 | `SP` | 50 chars | 100 ms | あり | `DATA` / `STATUS` / `INFO` | `INFO_REFRESH` | 通常10項目に対応。第14.10節参照。 | ※ |
| `PARAM_SET` | 50 chars PARAM 全体 | `SP` | 50 chars | 100 ms | あり | `DATA` / `STATUS` / `INFO` | `INFO_REFRESH` | 第14.3節参照。正常応答 DATA 0文字。 | ※ |
| `PARAM_RESET` | なし | `RP` | なし | 100 ms | あり | `DATA` / `STATUS` / `INFO` | `INFO_REFRESH` | SPの動作設定・閾値を既定値へ戻す。確認済み製品FWではADC校正値は対象外。S1.14Bの保持実機確認は別途。 | ※ |
| `ERP_SET_0_0` | なし | `SE` | `0000` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` | バースト無効／PS_OFF充電無効。第14.8節参照。 | ※ |
| `ERP_SET_1_0` | なし | `SE` | `1000` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` | バースト有効／PS_OFF充電無効。第14.8節参照。 | ※ |
| `ERP_SET_0_1` | なし | `SE` | `0100` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` | バースト無効／PS_OFF充電有効。第14.8節参照。 | ※ |
| `ERP_SET_1_1` | なし | `SE` | `1100` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` | バースト有効／PS_OFF充電有効。第14.8節参照。 | ※ |
| `CLOCK_SYNC` | `YYMMDDHHMMSS`（10進日時） | `SC` | 各日時欄を2桁ASCII HEXへ変換 | 100 ms | あり | `DATA` / `STATUS` | `DATA_REFRESH` | Pico-side RTC 設定とは別。第14.2節参照。 | ※ |
| `SERIAL_<ITEM>_<VALUE>` | item/value から 50 chars SERIAL を生成 | `SS` | 50 chars | 100 ms | あり | `DATA` / `INFO` | `INFO_REFRESH` | ASCII text は leading zero を保持。 |  |
| `LIFE_SET_<VALUE>` | 符号付き10進整数、0.1％単位 | `SL` | 最小3桁HEX＋予約00000 | 100 ms | あり | `DATA` | `DATA_REFRESH` → `BATT_DEG_TOTAL?` | 範囲外も無補正送信。第14.12節、OI-08継続。 | ※ |
| `LIFE_SET_RAW=<ASCII>` | SL DATAを直接指定 | `SL` | 長さ・HEX・値の制限なし | 100 ms | あり | `DATA` | `DATA_REFRESH` → `BATT_DEG_TOTAL?` | 不正値・不正長・予約部の実機試験に使用。 | ※ |
| `BATT_CHECK_START` | なし | `BC` | `1` | 6000 ms | あり | `DATA` / `STATUS`; BC refreshed | BC Query | 評価用。結果はBC Queryで確認。第14.11節参照。 | ※ |
| `BATT_CHECK_STOP` | なし | `BC` | `0` | 6000 ms | あり | `BC` / `DATA` / `STATUS` | `STATUS_REFRESH` | 評価用。応答30文字、BCはINVALID。OI-06継続。 | ※ |
| `CHARGE_ON` | なし | `CN` | `1` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部電流測定 | `OK` は充電成立を意味しない。 | ※ |
| `CHARGE_ON_STOP` | なし | `CN` | `0` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部電流測定 | `OK` は停止成立を意味しない。 | ※ |
| `CHARGE_OFF` | なし | `CF` | `1` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部電流測定 | `OK` は放電成立を意味しない。 | ※ |
| `CHARGE_OFF_CLEAR` | なし | `CF` | `0` | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部電流測定 | `OK` は clear 成立を意味しない。 | ※ |
| `BACKUP_ENABLE` | なし | `BE` | なし | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部 12V 測定 | `OK` は出力成立を意味しない。 | ※ |
| `BACKUP_OFF` | なし | `BF` | なし | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部 12V 測定 | `OK` は停止成立を意味しない。 | ※ |
| `OUTPUT_RESTART` | なし | `OR` | なし | 100 ms | あり | `DATA` / `STATUS` | `STATUS_REFRESH` + 外部 12V 測定 | OI-09: restart active 時の挙動要確認。 | ※ |
| `CLEAR_ALL` | なし | `CD` | `0` | 500 ms | あり | `DATA` / `STATUS` / `BC` | `DATA_REFRESH` + `STATUS_REFRESH` | 積算/状態 clear 系。 | ※ |
| `CLEAR_POWER` | なし | `CD` | `1` | 500 ms | あり | `DATA` / `STATUS` / `BC` | `DATA_REFRESH` + `STATUS_REFRESH` | 電源系 clear。 | ※ |
| `CLEAR_BATT` | なし | `CD` | `2` | 500 ms | あり | `DATA` / `STATUS` / `BC` | `DATA_REFRESH` + `STATUS_REFRESH` | 電池系 clear。 | ※ |
| `CLEAR_LOG` | なし | `CL` | なし | 1000 ms | あり | all `EL` / `OL` | EL/OL refresh | Event / Operation log clear。 | ※ |
| `AD_<TYPE>_<A/B>_<VALUE>` | 人が読んだA/Vの10進値を直接指定 | `AD` | TYPE1＋POINT1＋float32 HEX8 | 診断1000 ms | あり | `DATA` / `AR`、同回路DMM A/B | 回路名付き`AD_VERIFY`を別送信 | 方式採用確定。サンプル診断条件あり。第10.6／14.18節。正式T2等はOpen。 | ※ |
| `FW_UPDATE` | なし | `FU` | BLOCKED | - | なし | なし | なし | 常に `ERR:FU_DISABLED`。NF55G へ送信しない。 | ※ |

## 6. DATA Cache Query
事前に `DATA_REFRESH` が成功していること。各 Query は NF55G 通信を行わない。

| ATE Query | 応答形式 | 単位 / 備考 | 実装有無 |
| --- | --- | --- | --- |
| `NF55_DATE?` | `YYYYMMDD` | NF55G D0 TIME。 | ※ |
| `NF55_TIME?` | `HHMMSS` | NF55G D0 TIME。 | ※ |
| `NF55_DATETIME?` | `YYYYMMDD_HHMMSS` | NF55G D0 TIME。 | ※ |
| `VOUT12?` | decimal | V。 | ※ |
| `IOUT12?` | decimal | A。 | ※ |
| `BATT_VOLT?` | decimal | V。 | ※ |
| `CHG_VOLT?` | decimal | V。 | ※ |
| `CHG_CURR?` | decimal | A。 | ※ |
| `BATT_CURR?` | decimal | A。 | ※ |
| `BATT_SOC_WH?` | signed decimal | %。 | ※ |
| `BATT_SOC_MAH?` | signed decimal | %。 | ※ |
| `BATT_TEMP?` | signed decimal | degC。 | ※ |
| `ADU_TEMP?` | signed decimal | degC。 | ※ |
| `BBU_TEMP?` | signed decimal | degC。 | ※ |
| `FAN_RPM?` | decimal | rpm。 | ※ |
| `FAN_LEVEL?` | decimal | step。 | ※ |
| `AC_OFF_HOUR?` | decimal | 0.1 h scale。 | ※ |
| `PS_OFF_HOUR?` | decimal | 0.1 h scale。 | ※ |
| `AVE_OFF_TEMP?` | signed decimal | degC。 | ※ |
| `OFF_CHARGE_HOUR?` | decimal | 0.1 h scale。 | ※ |
| `AVE_CHARGE_TEMP?` | signed decimal | degC。 | ※ |
| `OFF_CHARGE?` | decimal | %。 | ※ |
| `OFF_BATT_DEG?` | decimal | 0.1 % scale。 | ※ |
| `CHARGE_DATA?` | decimal | LIFE_CALC flag/value。 | ※ |
| `CHARGE_END?` | decimal | LIFE_CALC flag/value。 | ※ |
| `LIFE_BATT_CHARGE?` | decimal | %。 | ※ |
| `LIFE_BATT_TEMP?` | signed decimal | degC。 | ※ |
| `LIFE_BATT_DEG?` | decimal | 0.1 % scale。 | ※ |
| `TOTAL_ADU_TEMP?` | decimal | accumulated。 | ※ |
| `TOTAL_ADU_HOUR?` | decimal | hour。 | ※ |
| `AC_FAIL_COUNT?` | decimal | count。 | ※ |
| `AC_LOW_COUNT?` | decimal | count。 | ※ |
| `BACKUP_COUNT?` | decimal | count。 | ※ |
| `BATT_DEG_TOTAL?` | decimal | 0.1 % scale。 | ※ |
| `TOTAL_BATT_HOUR?` | decimal | hour。 | ※ |
| `BATT_DISCHARGE_COUNT?` | decimal | count。 | ※ |
| `BATT_CHARGE_COUNT?` | decimal | count。 | ※ |
| `BATT_TTL_DISCHARGE?` | decimal | mAh。 | ※ |
| `BATT_TTL_CHARGE?` | decimal | mAh。 | ※ |
| `TOTAL_BATT_TEMP?` | decimal | accumulated。 | ※ |
| `BATT_TEMP_AVE?` | signed decimal | degC。 | ※ |
| `BATT_TEMP_MAX?` | signed decimal | degC。 | ※ |
| `BATT_TEMP_MIN?` | signed decimal | degC。 | ※ |

## 7. STATUS Cache Query
事前に `STATUS_REFRESH` が成功していること。応答は原則 `0` / `1` の flag 値とする。

| ATE Query | 応答形式 | 備考 | 実装有無 |
| --- | --- | --- | --- |
| `PS_ON?` | `0` / `1` | STATUS bit。 | ※ |
| `BURST_ON?` | `0` / `1` | 外部BURST信号の受信状態。実バースト動作の有無とは別。 | ※ |
| `BURST?` | `0` / `1` | バーストの有効設定。ERPの第1指定値。 | ※ |
| `PS_OFF_CHARGE?` | `0` / `1` | PS_OFF充電の有効設定。ERPの第2指定値。 | ※ |
| `RESTART_READY?` | `0` / `1` | STATUS bit。 | ※ |
| `BACKUP_READY?` | `0` / `1` | STATUS bit。 | ※ |
| `CHARGE_READY?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_CHECK_RUN?` | `0` / `1` | STATUS bit。 | ※ |
| `CHARGE_OFF_STATUS?` | `0` / `1` | STATUS bit。 | ※ |
| `CHARGE_ON_STATUS?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_ON?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_LOW?` | `0` / `1` | STATUS bit。 | ※ |
| `S_CHARGE_ON?` | `0` / `1` | STATUS bit。 | ※ |
| `CHARGE_OK?` | `0` / `1` | STATUS bit。 | ※ |
| `CHARGER_ON?` | `0` / `1` | STATUS bit。 | ※ |
| `FAN_WNG?` | `0` / `1` | STATUS bit。 | ※ |
| `ADU_TEMP_WNG?` | `0` / `1` | STATUS bit。 | ※ |
| `OC_OFF_H?` | `0` / `1` | STATUS bit。 | ※ |
| `PFC_OV?` | `0` / `1` | STATUS bit。 | ※ |
| `FAN_FAIL?` | `0` / `1` | STATUS bit。 | ※ |
| `BBU_TEMP_WNG?` | `0` / `1` | STATUS bit。 | ※ |
| `BBU_FAIL?` | `0` / `1` | STATUS bit。 | ※ |
| `CHG_LV?` | `0` / `1` | STATUS bit。 | ※ |
| `CHG_OV?` | `0` / `1` | STATUS bit。 | ※ |
| `CHG_OC?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_TEMP_WNG?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_TEMP_ALM?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_LV?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_OV?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_LIFE?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_MCN?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_P_FAIL?` | `0` / `1` | STATUS bit。 | ※ |
| `BATT_DCN?` | `0` / `1` | STATUS bit。 | ※ |
| `12V_OV?` | `0` / `1` | STATUS bit。 | ※ |
| `12V_LV?` | `0` / `1` | STATUS bit。 | ※ |
| `12V_OC?` | `0` / `1` | STATUS bit。 | ※ |
| `12V_OC_OFF_L?` | `0` / `1` | STATUS bit。 | ※ |

## 8. INFO Cache Query
事前に `INFO_REFRESH` が成功していること。ASCII text は leading zero を保持する。

| ATE Query | 応答形式 | 備考 | 実装有無 |
| --- | --- | --- | --- |
| `FW_REV?` | ASCII text | Firmware revision。 | ※ |
| `UNIT_REV?` | ASCII text | Unit revision。 | ※ |
| `UNIT_LOT?` | ASCII text | Unit lot。 | ※ |
| `UNIT_SERIAL?` | ASCII text | Unit serial。 | ※ |
| `ADU_REV?` | ASCII text | ADU revision。 | ※ |
| `ADU_LOT?` | ASCII text | ADU lot。 | ※ |
| `ADU_SERIAL?` | ASCII text | ADU serial。 | ※ |
| `BBU_REV?` | ASCII text | BBU revision。 | ※ |
| `BBU_LOT?` | ASCII text | BBU lot。 | ※ |
| `BBU_SERIAL?` | ASCII text | BBU serial。 | ※ |
| `PS_ON_BACKUP?` | decimal | Parameter。 | ※ |
| `AC_LINK?` | decimal | Parameter。 | ※ |
| `AUTO_CHARGE?` | decimal | Parameter。 | ※ |
| `EVENT_ENABLE?` | decimal | Parameter。 | ※ |
| `MAX_BACKUP_TIME?` | decimal | min。 | ※ |
| `MIN_BACKUP_TIME?` | decimal | sec。 | ※ |
| `RESTART_TIME?` | decimal | sec。 | ※ |
| `BATT_LOW_THD?` | decimal | %。 | ※ |
| `BATT_CAP_MAH?` | decimal | mAh。 | ※ |
| `BATT_CAP_WH?` | decimal | Wh。 | ※ |
| `CHG_IR_THD?` | decimal | mOhm。 | ※ |
| `BATT_WNG_THD?` | signed decimal | degC。 | ※ |
| `BATT_ALM_THD?` | signed decimal | degC。 | ※ |
| `ADU_TEMP_THD?` | signed decimal | degC。 | ※ |
| `BBU_TEMP_THD?` | signed decimal | degC。 | ※ |
| `FAN_WNG_THD?` | decimal | rpm。 | ※ |

## 9. BC / AR / EL / OL / FD Query
| ATE Query | 事前 Refresh | 応答形式 | 備考 | 実装有無 |
| --- | --- | --- | --- | --- |
| `BC_MODE?` | `BATT_CHECK_START` 成功後 | decimal | BC mode。 | ※ |
| `BC_V1?` | `BATT_CHECK_START` 成功後 | decimal | V。 | ※ |
| `BC_V2?` | `BATT_CHECK_START` 成功後 | decimal | V。 | ※ |
| `BC_I1?` | `BATT_CHECK_START` 成功後 | decimal | A。 | ※ |
| `BC_I2?` | `BATT_CHECK_START` 成功後 | decimal | A。 | ※ |
| `BC_TEMP?` | `BATT_CHECK_START` 成功後 | signed decimal | degC。 | ※ |
| `BC_SOC?` | `BATT_CHECK_START` 成功後 | signed decimal | %。 | ※ |
| `BC_IR?` | `BATT_CHECK_START` 成功後 | decimal | mOhm。 | ※ |
| `AR_DISCHG_I_A_ADC?` / `REF?`, `B_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |  |
| `AR_BATT_V_A_ADC?` / `REF?`, `B_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |  |
| `AR_ACDC12V_V_A_ADC?` / `REF?`, `B_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |  |
| `AR_BATT_CHG_A_ADC?` / `REF?`, `B_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |  |
| `AR_12VOUT_V_A_ADC?` / `REF?`, `B_ADC?` / `REF?` | `AR_REFRESH` | decimal / raw8 or decoded | OI-04: REF final wire format 未確定。 |  |
| `EL_<NN>_DATEHOUR?` | `EL_REFRESH_*` | `YYMMDDHH` or `00000000` | NN=01..32。No log は `00000000`。 | ※ |
| `EL_<NN>_ID?` | `EL_REFRESH_*` | decimal | NN=01..32。No log は `255`。 | ※ |
| `OL_<NN>_DATEHOUR?` | `OL_REFRESH_*` | `YYMMDDHH` or `00000000` | NN=01..64。No log は `00000000`。 | ※ |
| `OL_<NN>_ID?` | `OL_REFRESH_*` | decimal | NN=01..64。No log は `255`。 | ※ |
| `FD_DATA?` | `FD_READ_xxxxxx` | 64 ASCII HEX | HEX全桁検証後、大文字小文字と先頭ゼロを保持する。 | ※ |

## 10. RTC / Diagnostic / Logger コマンド
| ATE コマンド | 引数形式 | NF55G 通信 | 応答形式 | 備考 | 実装有無 |
| --- | --- | --- | --- | --- | --- |
| `RTC_DATE?` | なし | なし | `YYYYMMDD` | Pico-side DS3231 を参照。 | ※ |
| `RTC_TIME?` | なし | なし | `HHMMSS` | Pico-side DS3231 を参照。 | ※ |
| `RTC_DATETIME?` | なし | なし | `YYYYMMDD_HHMMSS` | Pico-side DS3231 を参照。 | ※ |
| `RTC_SET_YYYYMMDD_HHMMSS` | date/time | なし | `OK` or `ERR:<reason>` | NF55G `SC` / `CLOCK_SYNC` とは別。 | ※ |
| `RTC_CHECK?` | なし | なし | `OK` / `NG` | RTC access check。 | ※ |
| `*IDN?` | なし | なし | ASCII text | 現行応答 NF55G_PICO_FIXTURE,Rev.0。識別文字列だけで配置版の一致を判断しない。 | ※ |
| `PICO_SELF_CHECK?` | なし | なし | `OK:<detail>` / `NG:<detail>` | Pico local self check。試験終了後の TEST_LOGGER / TEST_LOG_DROP を含む。 | ※ |
| `NF_COMM_CHECK?` | なし | あり | `OK` / `ERR:<reason>` | NF55G communication smoke check（未実装）。現状は常に ERR:NF55G_NOT_CONNECTED、NF55G送信なし。 |  |
| `COMM_STATUS?` | なし | なし | 例 `OK:state=IDLE` | 現在のProtocol状態。実通信成立・製品動作成功の判定ではない。 | ※ |
| `RETRY_COUNT?` | なし | なし | 例 `OK:cmd=0,rsp=0` | 直前Transactionの値。Command retry と Response retry は別管理。 | ※ |
| `TEST_START` | なし | なし | `OK` / `ERR:<reason>` | 試行開始／再開始。全製品Cacheと旧CAL／QR取得値を失効。試験中の再STARTは前試行保存後に新規試行。SD異常でも受付可、保存成功保証ではない。 | ※ |
| `TEST_END` | なし | なし | `OK` / `ERR:<reason>` | Logger queue drain / flush / close。最終Self Checkを実行。OKはログ保存成功を意味しない。 | ※ |
| `LOG_CONT_START` | なし | なし | `OK` / `ERR:<reason>` | Continuous logging start。 | ※ |
| `LOG_CONT_STOP` | なし | なし | `OK` / `ERR:<reason>` | Continuous logging stop。 | ※ |
| `SD_STATUS?` | なし | なし | `OK` / `NO_CARD` / `MOUNT_ERR` / `OPEN_ERR` / `WRITE_ERR` / `FULL` | SD failure は NF55G 通信を停止しない。 | ※ |
| `SD_USAGE?` | なし | なし | `used_bytes/capacity_bytes/used_percent%` | 90% of SD capacity を運用上限とする。 | ※ |
| `LOG_DROP_COUNT?` | なし | なし | decimal | RAM Queue overflow/drop count。 | ※ |
| `SD_REINIT` | なし | なし | `OK` / `ERR:<reason>` | SD reinitialization。試験中・連続記録中は ERR:BUSY。第14.7節参照。 | ※ |

### 10.1 外部測定器中継と開発用HOST管理

NF55G通信は行わない。中継先は7355、HOST管理先は測定器用HOSTマイコンであり、機器本体のRESETではない。

| ATEコマンド | 引数 | 正常応答 | 主な注意 | 実装有無 |
|---|---|---|---|---|
| `EXT_QUERY <期限ms> <本文>` | 1～10000ms、ASCII本文最大192byte | `OK:EXT_RX:<byte数>:<大文字HEX>` | 原文を中継し、応答原文はCRLFを含めHEXで返す。測定Cacheには保存しない。 | ※ |
| `EXT_SEND <期限ms> <本文>` | 同上 | `OK:EXT_TX` | 機器への送信完了。設定成立は別のQueryで確認する。 | ※ |
| `HOST_INFO? METER` | 対象はMETERのみ | `OK:HOST_INFO:<ID>:<FW>:<NONCE>:<STATE>` | 通常EXTと別の管理照会。RST後の新起動確認時は下記応答。 | ※ |
| `HOST_RESET METER` | 対象はMETERのみ | `OK:HOST_RESET_ACCEPTED:<ID>:<旧NONCE>` | 受理ACK。再起動完了とは区別する。自動再送しない。 | ※ |
| RST後の`HOST_INFO? METER` | 同一個体・新起動を照合 | `OK:HOST_RESET_DONE:<ID>:<旧NONCE>:<新NONCE>:<STATE>` | DONEだけでUSB READY／7355測定再開を保証しない。 | ※ |

中継の失敗形式はERR:EXT_<理由>:AMBIGUOUS=0/1。HOST管理はERR:HOST_<理由>等で返す。RST送出後にACKがなければERR:HOST_RESULT_UNKNOWNとして保持し、追加RSTで上書きしない。BOOTSEL、QR HOST管理、量産自動復旧は未実装。

### 10.2 校正用の外部測定値取得とCache照会

回路はDISCHG_I／BATT_CHG／BATT_V、測定点はA／B、期限は1～10000ms。現行7355では末尾MD?を使用する。取得と照会はAD／ARを送信しない。

| ATEコマンド | 引数と用途 | 正常応答 | NF55G通信とCache | 実装有無 |
|---|---|---|---|---|
| `CAL_MEASURE_<回路> <AまたはB> <期限ms> MD?` | 回路名指定の現行取得入口 | `OK:CAL_MEASURE:<取得ID>` | NF通信なし。同点旧値を先に失効、完全取得のみ保存。 | ※ |
| `CAL_MEASUREMENT_<回路>? <AまたはB>` | 現試行の同回路・点の最新値を照会 | 下記の測定応答 | Cacheのみ。書込み用の照会済み記録を付ける。 | ※ |
| `CAL_MEASURE <回路> <AまたはB> <期限ms> MD?` | 従来の対象引数形式も利用可能 | `OK:CAL_MEASURE:<取得ID>` | 同上。 | ※ |
| `CAL_MEASUREMENT? <取得ID>` | 現試行の有効IDを指定 | 下記の測定応答 | Cacheのみ。書込み用の照会済み記録を付ける。 | ※ |

測定応答は `OK:CAL_MEASUREMENT:<ID>:<回路>:<AまたはB>:<測定値>:<測定単位>:<校正候補>:<校正単位>:<原文HEX>`。取得ID形式は試行世代8桁HEX－取得連番8桁HEX－回路－点。回路名方式でもIDは応答とログに残る。

MD?経路はF?→INIC?→TRS?→RN?→MSR?初回クリア→新しいEOM待ち→MD?の順。全処理に単一総期限を適用する。READ?／:READ?のSCPI経路はコード上残るが、7355現行運用の手順には使用しない。失敗はERR:CAL_<理由>、中継の成否不明はAMBIGUOUSを保持する。再取得で旧値は失効し、失敗しても戻さない。TEST_END成立・再STARTでIDは失効する。

### 10.3 QR確認後の明示SS書込み

| ATEコマンド | 引数 | 正常応答 | NF55G通信とCache | 実装有無 |
|---|---|---|---|---|
| `QR_SCAN <期限ms>` | 100～60000ms、現在TEST試行 | `OK:QR_ARMED:<取得ID>` | NF通信なし。旧値を破棄して最初の完全35文字を固定。受付応答であり取得完了ではない。 | ※ |
| `QR_GET? <取得ID>` | 現試行のREADY ID | `OK:QR_GET:<取得ID>:<原文35文字>` | 保存原文の照会だけ。これだけでは書込み可にならない。 | ※ |
| `QR_DATA? <取得ID>` | 同上 | `OK:QR_DATA:<取得ID>:<SS DATAの100桁HEX>` | 保存送信候補の照会と照会済み記録。 | ※ |
| `QR_WRITE <取得ID>` | 同一試行・READY・QR_DATA?照会済み | `OK:QR_WRITE:<取得ID>` | SS DATA50文字、T2=100ms。成功／成否不明はDATA／INFO INVALID。実行結果を得た取得IDは消費する。 | ※ |
| `QR_CANCEL` | なし | `OK` | 取得失効、NF送信なし。 | ※ |

取得IDは起動nonce16HEX・試行世代・取得連番を含むQ付き文字列。ATEはQR_DATA?の内容を確認した後、同じIDでQR_WRITEを別送信する。QR_STATUS?／QR_PARSE／QR_VERIFY／直接SERIAL書込みは正式入口として未実装。内部SERIAL_SET_RAWもATEには公開しない。

代表エラーはERR:QR_READING（取得待ち）、ERR:QR_TIMEOUT、ERR:QR_DISABLED、ERR:QR_NO_TRIAL、ERR:QR_STALE_ID、ERR:QR_NOT_REVIEWED、ERR:QR_CONSUMED。取得待ちの照会では同一IDを保持し、READYの応答を得るまで値を採用しない。通信成否不明はERR:QR_WRITE:<理由>:AMBIGUOUS=1。BUSYなど実行前の拒否と、実行結果後のID消費を区別する。

### 10.4 サンプル診断用の校正書込みと明示読戻し

下表は通常ATE経路に実装した条件付き診断入口。CALIBRATION_SAMPLE_ENABLEDは既定False。同一の有効TEST試行でINFO_REFRESHし、FW_REV=S1.14B／UNIT_SERIAL=000001であることが必要。人の読取り値の直接指定ADは第10.6節。AR_REFRESH／AR Cache Queryは引き続き未実装。

| ATEコマンド | 引数と用途 | 正常応答 | NF55G通信とCache | 実装有無 |
|---|---|---|---|---|
| `CAL_WRITE_<回路> <AまたはB>` | 最新の照会済み測定Cacheを明示採用 | `OK:CAL_WRITE:<VALUE8>:<AD_ADC十進値>:<計算値欄の原文HEX>` | AD DATA10文字／応答16文字。成功・成否不明時に測定値を失効しDATA／ARをINVALID。 | ※ |
| `AD_VERIFY_<回路> <AまたはB>` | 同試行の正常書込み記録に対する明示AR | `OK:AD_VERIFY:<回路>:<点>:<VALUE8>:<REF8>:<AD_ADC>:<AR_ADC>` | AR応答140文字から対象欄を返す。AR CacheはVALIDにしない。 | ※ |
| `CAL_WRITE <取得ID>` | 取得ID式診断。BATT_CHG Aに限定、点はIDから使用 | `OK:CAL_WRITE` | 上記と同じAD。別の点指定は拒否。 | ※ |
| `AD_VERIFY BATT_CHG A` | 互換用。書込み値とAR整数値・ADCを比較 | `OK:AD_VERIFY` または `ERR:AD_VERIFY_MISMATCH` | 別の明示AR。小数喪失により不一致になり得る。 | ※ |

回路はDISCHG_I／BATT_CHG／BATT_V、診断TYPEはそれぞれ1／4／2。回路＋A/Bだけを指定し、Cache点と書込み先の取り違えを防ぐ。A→通信点1、B→通信点2は内部で変換する。ADは校正候補を有限のfloat32へ変換したビッグエンディアン8桁HEX（VALUE8）で送る。ATEが測定値の採否と製品合否を判断し、Picoは指定された回路・A/Bの書込み保護範囲を検査する。

AD診断T2=1000ms、ARは有効ACK後100ms。いずれもCommand Retryなし。書込みから自動ARは行わず、AD_VERIFYを別送信する。回路名付きAD_VERIFYのOKはAR受信成立であり、値の一致や校正PASSではない。VALUE8とREF8は表現が異なる可能性があり、HEX文字列の単純一致で合否を決めない。S1.14Bの実測診断では小数の書込み0.50／1.85／1.86／2.25 Aに対しAR REF8は0／1／1／2。内部の小数保持は未確認。

範囲外はERR:CAL_WRITE_RANGE、不正設定はERR:CAL_WRITE_SETTINGSで無送信拒否する。数値正本はルートcalibration_limits.py。

主な拒否はERR:CAL_WRITE_DISABLED、ERR:CAL_NO_ACTIVE_TRIAL、ERR:CAL_SAMPLE_IDENTITY、ERR:CAL_WRITE_NOT_QUERIED、ERR:CAL_WRITE_VALUE、ERR:AD_VERIFY_NO_WRITE、ERR:BUSY。通信異常はERR:CAL_WRITE_<理由>:AMBIGUOUS=0/1、AD正常フレームの応答内容不正はERR:CAL_WRITE_RESPONSE:AMBIGUOUS=1。AR timeoutはERR:AD_VERIFY_TIMEOUT、形式不正はERR:AD_VERIFY_RESPONSE。成否不明時はADを自動再送せず停止し、原文・対象・値・ログを保全する。

### 10.5 双方向QR受付の試験モード

通常モードのコマンド名・取得IDは維持する。試験モードではQR_SCANが `OK:QR_PENDING:<取得ID>` を返す。これはHOST受付応答待ちであり、読取り開始完了ではない。QR_GET?／QR_DATA?はHOST応答待ちでERR:QR_ARMING、同一受付ID照合後の読取り待ちでERR:QR_READING、完成後に通常のQR_GET／QR_DATA応答を返す。期限はQR_SCANからの全時間で、ARMING後にリセットしない。

旧読取りをHOSTで破棄して同じ受付IDの応答を確認する候補実装。QR_HOST_ARM_ENABLED=Falseが既定であり、現在の単方向配置にPENDINGを期待しない。対応HOSTと配線・設定を確認する。量産採用とATEの待ち条件はOI-23で未確定。手順は第14.17節。

### 10.6 人の読取り値をATEから直接指定するAD

2026-11-26ユーザー指示により採用確定。人が測定器を読んだ値をATEへ記載し、NF55Gへ送る方式。CAL_WRITEの測定Cache方式も併用する。

| ATEコマンド | 引数 | 正常応答 | 使用条件 | 実装有無 |
|---|---|---|---|---|
| `AD_<TYPE>_<A/B>_<VALUE>` | TYPE=1～5または回路名、点=A/Bのみ、VALUE=A/Vの10進数 | `OK:AD_WRITE:<TYPE>:<A/B>:<VALUE8>:<AD_ADC十進値>:<計算値原文HEX>` | CALIBRATION_SAMPLE_ENABLED=True、同試行D5でS1.14B／000001を確認。DMM・測定Cache不要。 | ※ |

TYPEは1=DISCHG_I、2=BATT_V、3=ACDC12V_V、4=BATT_CHG、5=12VOUT_V。電流TYPE1/4はA、電圧TYPE2/3/5はV。例AD_4_A_1.85とAD_BATT_CHG_A_1.85は同じ1.85 Aの書込み。符号・小数・E/e指数表記を受け付け、単位文字・生HEXを入力しない。有限float32へ変換し、TYPE1＋POINT1＋VALUE8の10文字を送る。例のNF DATAは413FECCCCD。測定器の再読取り、Cache補完、Picoでの単位換算はしない。

必須3回路×A/Bは設定ファイルの上下限を送信直前に検査する。範囲外はERR:AD_WRITE_RANGE、不正設定はERR:AD_WRITE_SETTINGS。拒否時は無送信でCacheを消費しない。TYPE3/5の保護範囲は未指定。

診断T2=1000ms、AD Command Retryなし。正常／成否不明時はDATA／ARと同回路DMM A/B Cacheを失効する。STATUS／INFOはAD応答から更新しない。入力不正はERR:AD_ARGUMENTS／ERR:AD_TYPE／ERR:AD_POINT／ERR:AD_VALUEで無送信拒否。診断無効・試行なし・個体不一致・BUSYは既存の校正診断エラー。通信失敗はERR:AD_WRITE_<理由>:AMBIGUOUS=0/1、内容不正はERR:AD_WRITE_RESPONSE:AMBIGUOUS=1。再送せず停止する。

TYPE表・送信形式・1000msは現行診断の実装条件。直接方式の採用は、製品側正式仕様・量産受入・サンプル制限解除の承認とは区別する。AD_VERIFYは別指令。第14.18節とdocs/AD_Direct_ATE_20261126_Rev0.mdを参照。

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

本Rev.5の正本はMarkdown。既存Word Rev.4は履歴であり、校正の現行コマンドは本書と校正実装仕様を参照する。

## 13. 参照仕様
- `AGENTS.md`
- `docs/ATE_Command_Master.md`
- `docs/Data_Decode_Master.md`
- `docs/Cache_Master.md`
- `docs/Logger_SD_Spec.md`
- `docs/Open_Issues.md`

- `docs/ADC_Acquisition_20261123_01/ADC_Acquisition_Spec_Rev0.md`
- `docs/ADC_Acquisition_20261123_01/Result_Rev0.md`
- `docs/USB_Host_Reset_Study_20261121/Host_Reset_Management_Spec_20261123_Rev0.md`
- `docs/USB_Host_Reset_Study_20261121/Debug_20261123_01/Next_Step_Result_20261123_Rev0.md`
- `docs/QR_Hardware_Integration_20261123_01/SS_Workflow_Spec_20261123_Rev0.md`
- `docs/QR_Hardware_Integration_20261123_01/SS_Write_Readback_Result_20261123_Rev0.md`

## 14. 試験指示書 第7節に対応する使用例と注意事項

### 14.1 D0 / D1 Cache取得と詳細問い合わせ手順

PicoはNF55Gから取得した情報をCache（一時保存領域）に保持する。ATEは最初にRefreshコマンドで情報を取得し、その後、個別Queryで必要な項目を問い合わせる。個別QueryだけではNF55Gと通信しない。

以下の数値は説明用であり、試験の期待値・判定基準ではない。要求末尾にCRLFを付加し、応答は配置FWの終端設定で受信する（現行ソース既定CR）。各応答を受けてから次を送信し、RefreshのOKを確認してから個別Queryへ進む。エラー時はその段階で正常シーケンスを中断し、取得値として扱わない。

| 順序 | ATE送信 | Pico応答例 | 処理内容 |
|---|---|---|---|
| 1 | `DATA_REFRESH` | `OK` | NF55GへD0を送信しDATA Cacheを更新する。 |
| 2 | `VOUT12?` | `12.0` | 保存済みの12V出力電圧（V）を取得する。 |
| 3 | `BATT_VOLT?` | `8.0` | 保存済みのバッテリ電圧（V）を取得する。 |
| 4 | `BATT_TEMP?` | `25` | 保存済みのバッテリ温度（degC）を取得する。 |
| 5 | `STATUS_REFRESH` | `OK` | NF55GへD1を送信しSTATUS Cacheを更新する。 |
| 6 | `PS_ON?` | `1` | 保存済みのPS_ON状態を取得する。 |
| 7 | `BATT_ON?` | `1` | 保存済みのバッテリ接続状態を取得する。 |

- 同じRefresh後の個別Queryは、その取得時点の保存値を返す。負荷・電源・充電条件の変更後、または現在値が必要な場合はATEが再度Refreshする。VALIDでも現在状態との一致を保証しない。
- DATA_REFRESHではSTATUS / INFO Cacheを更新しない。状態はSTATUS_REFRESH、製造情報・設定値はINFO_REFRESHで取得する。D0内Status・Manufacturing・Parameter、Control応答内Status、EB Eventを他Cacheへ昇格しない。
- Refresh開始時に対象CacheをINVALIDにする。通信・Decode失敗後は旧値へ戻さず、Partial DecodeをVALIDにしない。
- ERR:CACHE_INVALIDは値として扱わず、必要なRefreshを明示実行してから問い合わせ直す。失敗したRefreshの後にQueryを継続して判定しない。
- Control / Set / Clear後は指定CacheがINVALIDになる。ATEが再取得してから確認する。ACK_TIMEOUT / RESP_TIMEOUT / 最終BCC・FRAME異常等の成否不明時も、操作が実行された可能性があるため関連CacheをINVALIDにする。ATEでの再実行は副作用を考慮する。
- OKはProtocol処理の成功を示し、製品動作成立やPASSを意味しない。製品判定はATEが外部測定値と合わせて行う。
- D0のT2は300ms（2026-11-11指定、OI-02はOpen継続）。CHARGE_ENDへの製品側副作用はOI-03として確認継続中。Picoは仕様差を補正しない。

### 14.2 7.1 情報の書込み 時間設定とFW確認

CLOCK_SYNCは、ATEが指定する10進日時でNF55Gの時計を設定する。形式は CLOCK_SYNC YYMMDDHHMMSS または CLOCK_SYNC=YYMMDDHHMMSS。年は2000～2099。Pico側RTCの設定・自動参照は行わない。

| 順序 | ATE送信 | Pico応答例 | 確認内容 |
|---|---|---|---|
| 1 | `CLOCK_SYNC 261109120000` | `OK` | 2026年11月9日12時00分00秒を指定する例。 |
| 2 | `DATA_REFRESH` | `OK` | 製品日時を明示再取得する。 |
| 3 | `NF55_DATETIME?` | `20261109_120000` | 読戻し例。実際の値は処理時間に応じて進む。 |
| 4 | `INFO_REFRESH` | `OK` | 製造情報・設定値を取得する。 |
| 5 | `FW_REV?` | 取得したFW版数 | ATEがFW書き込み仕様書のREVSIONと照合する。 |

- 日時は例示であり、そのまま実機へ送信しない。ATEは実行時に設定すべき日時を指定する。SCはAC OFF時間計算に影響するため、指定時刻と製品状態を管理する。過去時刻は製品側でパラメータエラーとなる仕様。
- 各日時欄を2桁ASCII HEXへ変換してSCへ送信する。例: ATE指定 260102030405 → NF DATA 1A0102030405。T2=100ms、正常応答DATAは0文字。成功・成否不明時はDATA / STATUSをINVALIDにする。
- Pico側RTCを設定する場合は RTC_SET_YYYYMMDD_HHMMSS を使用する。NF55GのSCとは別操作。
- FW_REVISIONはFW版数であり、QRの製品REV / UNIT_REVとは別項目。SS書込み対象ではない。比較元仕様書のファイル・版・期待値・比較規則はOI-23で確定する。FUは送信しない。

製造情報の直接指定コマンドSERIAL_<ITEM>_<VALUE>は引き続き未実装。2026-11-23に追加したQR_WRITEは、QRからUNITの3欄だけを生成してSSへ書き込む別入口である。REV3＋空白1文字→UNIT_REV4、YYWW→UNIT_LOT4、号機6文字→UNIT_SERIAL6とし、週から月へ変換しない。FW／ADU／BBU／予約はFの変更なし指定を送る。「それ以降は0000」として一律にゼロを書かない。第14.15節参照。

書込み後はINFO_REFRESHを明示し、UNIT_REV?／UNIT_LOT?／UNIT_SERIAL?を指定値と比較する。末尾空白・先頭ゼロを保持する。ADU_REV?／ADU_LOT?／ADU_SERIAL?、BBU_REV?／BBU_LOT?／BBU_SERIAL?は非対象欄の保持確認に使う。直接指定で9項目を書き込む契約、QR遅着境界などの未確定事項はOI-23等に残し、部分実装をもってCloseしない。

### 14.3 7.2 初期設定の確認とPARAM_SET

INFO_REFRESHで取得した設定値を、ATEが試験指示書の初期設定値と比較する。初期設定の確認と、PARAM_RESETによる初期化は別の操作である。PARAM_RESETは全項目を数値0にする操作ではない。

| 順序 | ATE送信 | Pico応答例 | 確認内容 |
|---|---|---|---|
| 1 | `INFO_REFRESH` | `OK` | 設定値を取得する。 |
| 2 | `PS_ON_BACKUP?` | 取得した設定値 | 試験指示書の期待値と比較する。 |
| 3 | `AUTO_CHARGE?` | 取得した設定値 | 試験指示書の期待値と比較する。 |
| 4 | `MAX_BACKUP_TIME?` | 取得した設定値 | 単位はmin。他の設定項目も第8節のQueryで確認する。 |

実装済みのPARAM_SETは、設定領域全体の50文字を指定する方式。1項目だけを変更する場合は、通常10項目に対応したPARAM_<ITEM>_<VALUE>方式を使用できる（第14.10節）。

| 順序 | ATE送信 | Pico応答例 | 処理内容 |
|---|---|---|---|
| 1 | `PARAM_SET <50文字の設定データ>` | `OK` | SPへ50文字全体を送信する。 |
| 2 | `INFO_REFRESH` | `OK` | 設定を明示再取得する。 |
| 3 | 変更項目の個別Query | 取得した設定値 | ATEが指定値との一致を確認する。 |

- 上記の <50文字の設定データ> は説明用の置換箇所であり、その文字列自体を送信しない。PARAM_SET=<50文字の設定データ>形式も受け付ける。
- 現行実装は50文字のASCII長を検証する。各値の符号化・範囲・未変更項目・予約領域は、ATEが通信仕様とData Decode Masterに従って管理する。Picoが全設定値を検証・補完する意味ではない。
- NF CMD=SP、T2=100ms、正常応答DATAは0文字。成功・成否不明時はDATA / STATUS / INFOをINVALIDにする。Queryによる自動Refreshは行わない。
- INFO_REFRESHによる読戻しだけではSTATUS / DATAは更新されない。必要な状態・計測値は各Refreshで再取得する。

### 14.4 7.3 電流 / 電圧の補正

試験指示書の条件と数値を以下に保持する。「付近」「近傍」は設定目安であり、合否許容範囲には置き換えない。① / ②の充放電表記は提示内容を保持する。

| 補正対象 | 動作条件 | A | B |
|---|---|---|---|
| バッテリ放電電流 DISCHG_I | バッテリ充電 | 44 A付近（DC5.2 V、12 V:15 A近傍） | 0.3 A付近（DC5.2 V、12 V:0 A近傍） |
| バッテリ充電電流 BATT_CHG | バッテリ放電 | 1.85 A付近（バッテリ電圧7.2 V近傍） | 0.5 A付近（バッテリ電圧10.6 V近傍） |
| バッテリ電圧 BATT_V | 充電時 | 8 V付近（バッテリ電圧8 V近傍） | 5 V付近（バッテリ電圧5 V近傍） |

手順例: ATEでA点条件を設定 → 安定後に実測 → ATEで実測値を確認 → 実測値を付加した書込み指示 → B点も同様に実行 → 補正情報の読戻し・補正後測定を確認する。

- 目安値を実測値の代用にせず、各点で実測した値を指定してSETする。
- 校正点はA/Bを一度だけ指定する。書込み前に必須3回路の上下限を検査する。サンプル診断用CAL_WRITE／AD_VERIFYは第10.4節・第14.16節、測定取得は第14.14節に従う。取得・照会だけではADを書き込まない。
- 現行の診断ATE入口は、取得して照会済みのCacheを回路名・A/B点で明示採用する。人の読取り値を直接指定するAD入口は第10.6／14.18節。取得や照会から自動書込みしない。
- AD形式、数値表現、補正点、範囲、反映・保持、AR読戻しはOI-04 / OI-05 / OI-12 / OI-16～OI-21、外部測定はCAL-EXT-01～03で確認する。取得・照会は第10.2節の採用済み契約に従う。サンプル診断入口の実装を正式なAD／AR仕様の確定とは扱わない。
- QR用RP2350-USB-Cと測定器用RP2350-USB-Aを別HOSTとする現行構成で限定実機確認済み。旧CH9350案／ハブ結合案を現行手順として用いない。構成・確認範囲は第16節を参照する。

### 14.5 7.4 電圧 / 電流 / 温度 / FAN回転の確認

ATEが測定条件を設定して安定後、DATA_REFRESH成功を確認し、次の個別Queryを実行する。条件変更後は再度DATA_REFRESHを行う。

| 確認対象 | 個別Query | 単位 |
|---|---|---|
| 出力電圧 / 電流 | `VOUT12?` / `IOUT12?` | V / A |
| バッテリ電圧 | `BATT_VOLT?` | V |
| 電流 | `CHG_CURR?` / `BATT_CURR?` | A |
| 温度 | `BATT_TEMP?` / `ADU_TEMP?` / `BBU_TEMP?` | degC |
| FAN回転数 | `FAN_RPM?` | rpm |

電流Queryと補正対象DISCHG_I / BATT_CHGとの対応は、名称だけで推測せずData Decode Masterと測定条件を照合する。外部測定値との比較方法・許容差・安定時間は試験仕様で定義し、PicoのQuery値だけで製品PASSを判定しない。

### 14.6 7.5 データのクリア

試験完了後、試験指示書の対象データをクリアする。指示書の操作名とATEへ送信する正式コマンド名を区別する。

| 試験指示書 | 現行ATEとの対応 | 注意 |
|---|---|---|
| CLEAR_DATA | 同名ATEコマンドは未実装。CLEAR_ALL / CLEAR_POWER / CLEAR_BATTとの対応は消去範囲の確認後に確定する（ATE-CLEAR-01）。 | CLEAR_ALLを自動的な別名として扱わない。 |
| CLEAR_LOG | 実装済みのCLEAR_LOG（NF CMD=CL） | NF55G内部履歴の消去。PicoのSD試験CSVは消去しない。 |

- 消去後に値を確認する場合は対象情報を明示RefreshしてからQueryする。初期化後の値は全項目が0になるとは限らない。
- CD成功・成否不明時はDATA / STATUS / BC、CL成功・成否不明時は全EL / OLをINVALIDにする。
- CDで満充電情報等が初期化され、初期充電が動作し得る。実機試験済みのバッテリ未接続条件と、量産の接続条件を区別する。
- EL / OLの正式ATE Refresh / Queryを実装済み。CLEAR_LOG後の確認は必要ブロックを明示再取得して行う。以前の診断スクリプトでの実績と今回の正式ATE入口のHost確認を区別し、実機デバッグはERPと同時に後日実施する。
- D4は副作用のため量産では使用しない。D4をクリア確認の代替読出しとして採用しない。

### 14.7 試験終了時の自己診断とSD復帰

| 順序 | ATE送信 | Pico応答例 | 確認内容 |
|---|---|---|---|
| 1 | `TEST_START` | `OK` | 試験期間開始。ログ保存の成功を意味しない。 |
| 2 | 試験に必要な実装済みコマンド | 各応答 | 第7節に対応する書込み・確認・クリアを行う。 |
| 3 | `TEST_END` | `OK` | Queue処理・flush・close後の最終Self Checkを行う。 |
| 4 | `PICO_SELF_CHECK?` | `OK:<詳細>` または `NG:<詳細>` | 装置状態と直前試験の保存状態をATEが確認する。 |
| 5 | `SD_STATUS?` | 現在のSD状態 | 試験終了応答後、待機時の復帰結果を確認する。 |

- <詳細>などの説明文字列は応答構文の説明であり、そのままの通信値ではない。Self CheckにはATE_UART / NF55_UART / RTC / LOGGER、試験終了後はTEST_LOGGER / TEST_LOG_DROPを含む。
- TEST_START成立時は全製品Cache・旧CAL／QR取得値を失効する。試験中の再STARTは旧Queue排出・flush・close後に新しいT番号の試行を開始し、旧Queueを新CSVへ持ち越さない。同一秒でもファイルを分離する。通信busy／保存延期／連続記録競合はBUSYとして新規試行を作らない。
- TEST_START / TEST_ENDはSD異常でも試験受付・終了のOKを返す。OKはログ保存成功・製品PASSを意味しない。通信中など実行条件を満たさない場合はERR:BUSYとなる。TEST_ENDがBUSYの場合は終了済みとせず、待機後に明示再要求する。
- TEST_END後はTEST_LOGGER（その試験の保存状態）とTEST_LOG_DROP（OKまたはその試験の破棄件数）を確認する。現在のLOGGERがOKでも直前試験の保存異常は消えない。次のTEST_STARTで履歴を初期化する。
- LOG_DROP_COUNT?は累積破棄件数であり、試験単位のTEST_LOG_DROPと区別する。Self CheckのNGは装置異常であり、Picoによる製品FAIL判定ではない。UART項目のOKだけで製品との実通信成立を判断しない。
- TEST_START～TEST_END（SD開始失敗時も含む）および連続記録中のSD_REINITはERR:BUSY。再挿入だけで試験中の記録を再開しない。
- TEST_END / LOG_CONT_STOP後、ATE応答・待ち要求とNF55G通信を優先した待機時に1回だけSDを再認識する。直後のQuery時点では復帰処理前の場合がある。SD_STATUS?で現在状態を確認し、待機後も異常なら試験外でSD_REINITを明示する。フォーマットは行わない。
- 通信中のSD write / flushは行わずRAM Queueを使用する。SD異常でもNF55G通信を停止しない。
- TEST_START後に取得したQR末尾6桁S/Nをログ名へ付加するRAM連携は実装済み。未取得・不正時は日時名を維持する。2026-11-23には正式QR入口・親GP9受信・SS書込みとログ名付加を限定実機確認済み。旧HOST内遅着境界と再投入保持の受入完了を意味しない（第14.15節、OI-14 / OI-23継続）。

### 14.8 バーストとPS_OFF時の充電を指定する

ATEには ERP_SET_<バースト設定>_<PS_OFF充電設定> のコマンド名を送信する。各設定は0=無効、1=有効で、毎回2項目とも指定する。バースト設定を切り替えるときも、維持したい充電設定を併せて指定する。コマンド名の後ろへ引数や1000などのDATAを追加しない。

| ATEへ送信するコマンド | バースト設定 | PS_OFF時の充電 | Picoが送るSE DATA | 用途 |
|---|---|---|---|---|
| `ERP_SET_0_0` | 無効 | 無効 | `0000` | バーストとPS_OFF充電を両方無効にする。 |
| `ERP_SET_1_0` | 有効 | 無効 | `1000` | r1が指定する低消費電力用の設定にする。 |
| `ERP_SET_0_1` | 無効 | 有効 | `0100` | バーストを無効にしてPS_OFF充電を許可する。 |
| `ERP_SET_1_1` | 有効 | 有効 | `1100` | バーストを有効にしてPS_OFF充電を許可する。 |

- SE DATAは4文字のASCII。左から1文字目がBURST、2文字目がPS_OFF_CHARGE、後ろ2文字が予約領域00。後ろ2文字はPicoが自動付加する。ATEは上表のコマンド名だけを送信する。
- PS_OFF充電の「有効」は充電を許可する設定。自動充電設定、バッテリ・温度等の充電条件、強制充電停止状態などにより、実際には充電が始まらない場合がある。ERP_SET_0_1／ERP_SET_1_1はCHARGE_ONの代わりではなく、CHARGE_OFF状態を解除するコマンドでもない。
- 0000はバーストだけでなくPS_OFF充電も無効にする。PS_OFF充電を有効のままバーストを切り替える場合は、ERP_SET_0_1とERP_SET_1_1を使う。
- r1 p.21の初期値欄は両方1だが、現在の設定を初期値と推定しない。試験前にSTATUS_REFRESH後のBURST?／PS_OFF_CHARGE?を保存し、復元時は保存値に対応するコマンドを明示指定する。Picoによる自動復元は行わない。

以下はPS_OFF充電を無効から有効へ変更し、バーストは無効を指定する例。各行の応答完了を待ち、要求にはCRLFを付加し、応答は配置FWの終端設定で受信する。

| 順序 | ATE送信 | Pico応答例 | 処理と確認 |
|---|---|---|---|
| 1 | `ERP_SET_0_1` | `OK` | バースト無効、PS_OFF充電有効を指定する。 |
| 2 | `STATUS_REFRESH` | `OK` | 設定後の状態をD1で明示再取得する。 |
| 3 | `BURST?` | `0` | バースト無効の設定を確認する。 |
| 4 | `PS_OFF_CHARGE?` | `1` | PS_OFF充電有効の設定を確認する。 |

- 4コマンドともT2=100ms、正常応答DATAは状態情報15文字。成功・成否不明時にDATA／STATUSをINVALIDにする。SE応答内StatusをSTATUS Cacheに転用せず、自動Refreshしない。直後のQueryはERR:CACHE_INVALIDとなるため、上例のようにSTATUS_REFRESHを明示する。
- 設定の読戻しはBURST?／PS_OFF_CHARGE?で確認する。BURST_ON?は外部BURST信号の受信状態であり、バースト有無に依存しない（r1 p.30）。実際の低消費動作・充電動作は外部測定で確認し、Picoは製品PASS／FAILを判定しない。
- 通信エラーまたは読戻し不一致時は正常シーケンスを中断して記録する。成否不明でATEから盲目的に同じ要求を繰り返さない。バックアップ中のSEは受付不可の仕様（r1 p.17）。Sample比較の信号・負荷条件と最終設定はERP-CONDITION-01で確認する。

### 14.9 エラー履歴と操作履歴とFWデータを読み出す

履歴は1回に8件を取得する。ELはエラー履歴32件、OLは操作履歴64件。Refresh名の開始番号は10進2桁で指定する。例えばEL_REFRESH_17は履歴17～24を取得し、PicoがNF DATAをASCII HEXの11へ変換する。ATEからEL_REFRESH_11へ置き換えない。

| 目的 | ATE送信例 | 正常応答例 | 説明 |
|---|---|---|---|
| エラー履歴1～8を取得 | `EL_REFRESH_01` | `OK` | EL_01ブロックだけを更新する。 |
| 履歴1の日時を確認 | `EL_01_DATEHOUR?` | `26110916` | 2026年11月9日16時の例。 |
| 履歴1のIDを確認 | `EL_01_ID?` | `9` | IDは10進で返す。 |
| 操作履歴57～64を取得 | `OL_REFRESH_57` | `OK` | OL_57ブロックだけを更新する。 |
| 履歴64のIDを確認 | `OL_64_ID?` | `255` | 履歴なしのID例。日時は00000000。 |
| FWデータを取得 | `FD_READ_000000` | `OK` | 指定アドレスから32byte分を取得する例。実機アドレスは担当者が確認する。 |
| 取得済みFWデータを参照 | `FD_DATA?` | 64文字ASCII HEX | 最新のFD Cacheをそのまま返す。 |

- ELの開始番号は01／09／17／25、OLは01／09／17／25／33／41／49／57。他番号や引数は拒否する。個別履歴番号はEL_01～32、OL_01～64で、対応ブロックの取得が必要。別ブロックを自動取得しない。
- ログ日時は各欄のHEXから10進YYMMDDHHへ変換する。例: RAW 1A0B0910→26110916。空履歴は日時00000000とID255。製品側の閏日記録・SC前の誤差をPicoで補正しない。
- 各Refreshは対象Cacheを先にINVALIDにし、T2=100ms・応答長EL/OL82文字、FD64文字とDecodeを確認後にVALIDへ更新。EL/OLは応答開始番号の一致も検証する。失敗時は旧値を復元しない。
- QueryはCacheのみを参照し、未取得・INVALIDはERR:CACHE_INVALID。CL後は全EL/OLがINVALIDになるため必要ブロックを明示Refreshする。読出しから自動CLEAR_LOGを実行しない。
- FD_READの末尾は6桁ASCII HEX。FD_DATA?は64文字を保持し、次のFD_READで置き換える。FUは送信しない。範囲外をPicoでFF補完しない。FDの本文IDとバイト表の不一致はREAD-FD-01、範囲外挙動はOI-10で確認し、FD実機送信は正式ID確認後とする。
- 実装済みはHost / Mock確認を意味する。今回の正式読出し入口とERP全4種の実機デバッグはユーザー指示により後日まとめて実施し、この未配置記述はRev.1作成時点の記録。現行の確認範囲は第16節参照。AR_REFRESH／AR Cache Queryは未実装のまま。診断用の別指令AD_VERIFYは第10.4節に従う。

### 14.10 パラメータを1項目ずつ設定する

ATEからPARAM_<ITEM>_<VALUE>を送信する。ITEMは次表の項目名、VALUEは10進整数で指定する。例えばPARAM_MIN_BACKUP_TIME_15は15秒を指定し、PicoがSPの対象欄へ0Fを格納する。ATEから15をHEXに置き換えたり、コマンド後ろに引数を追加したりしない。

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

| 順序 | ATE送信 | Pico応答例 | 処理と確認 |
|---|---|---|---|
| 1 | `PARAM_AUTO_CHARGE_2` | `OK` | 自動充電方式を有効レベル2に設定する。 |
| 2 | `INFO_REFRESH` | `OK` | 設定をD5で明示再取得する。 |
| 3 | `AUTO_CHARGE?` | `2` | ATEが指定値との一致を確認する。 |

- 各項目のVALUEはコマンド名の最後に指定する。例: PARAM_BATT_CAP_MAH_4900、PARAM_EVENT_ENABLE_1。原典のEVENTに対応する正式ATE項目名はEVENT_ENABLE。PARAM_EVENT_1という別名は使用しない。
- 指定項目だけを変更する。未指定項目へは原典r1 p.19の最大HEX値F～FFFF（変更なし）、予約18文字へは0を設定して50文字を生成する。INFO Cacheから旧値を補完せず、事前の自動INFO_REFRESHも行わない。元値が必要な場合はATEが試験前に明示取得する。
- MAX_BACKUP_TIME=0は無制限、BATT_LOW_THD／BATT_CAP_MAH／BATT_CAP_WHの0は電源初期値指定。0を既定の数値へ自動置換しない。変更なし指定用の最大HEX値をVALUEとして指定する方式ではない。
- AUTO_CHARGEは自動充電方式の設定。設定のOKだけで充電開始を保証せず、CHARGE_OFFによる強制停止をこのコマンドで解除したことにもならない。出力・充電・バックアップへの影響を試験条件と合わせて管理する。
- T2=100ms、正常応答DATAは0文字。成功・成否不明時はDATA／STATUS／INFOをINVALIDにする。設定後はINFO_REFRESH成功後に対象の<ITEM>?を確認する。状態や計測値は別のSTATUS_REFRESH／DATA_REFRESHが必要。Queryで自動取得しない。
- 範囲外はERR:PARAMETER_RANGE、整数表記不正はERR:PARAMETER_VALUE、未知項目はERR:PARAMETER_UNKNOWN_ITEM、項目形式不正はERR:PARAMETER_FORMAT、余分な引数はERR:UNEXPECTED_PAYLOAD。拒否時はNF55G送信・Cache変更なし。小数、符号、0x等のHEX表記は使用しない。
- BATT_WNG_THD／BATT_ALM_THD／ADU_TEMP_THD／BBU_TEMP_THD／FAN_WNG_THDは原典の変更禁止項目として、項目別入口ではERR:PARAMETER_PROTECTEDで拒否する。CHG_IR_THDは値0の意味をPARAM-IR-01で設計確認中のためERR:PARAMETER_UNCONFIRMEDで拒否する。
- 通常10項目のHost / Mock検証済み。Rev.1作成時点ではPico配置・実機送信未実施。今回の照合で項目別の製品設定成立を新たに確認したとはしない。実機試験では元値退避・1項目ずつの変更・非対象項目保持・外部観測・明示復元を記録する。既存PARAM_SETの一括方式やPARAM_RESETとは別の操作として扱う。

### 14.11 バッテリ診断を実行して結果を取得する

BATT_CHECK_STARTでNF55G内の充電DCIR測定を実行し、返された寿命診断データをBC Cacheへ保存する。BATT_CHECK_STOPは停止を指示する。r1 p.26で評価用とされており、量産の製品PASS／FAILはATEが別途判定する。Pico配置・バッテリ接続での実機確認は未実施。

| ATEコマンド | NF DATA | 正常応答 | Cacheの扱い |
|---|---|---|---|
| `BATT_CHECK_START` | `1` | BC DATA30文字、ATEへOK | 処理開始時に旧BCをINVALID。成功時DATA／STATUSをINVALID、完全Decode結果だけBCをVALID。 |
| `BATT_CHECK_STOP` | `0` | BC DATA30文字、ATEへOK | 成功・成否不明時にBC／DATA／STATUSをINVALID。停止応答をBCへ保存しない。 |

両コマンドとも引数なし、T2=6秒。ATEは各応答完了を待って次のコマンドを送る。ATE側timeoutはT2に加えて規定のCommand Retry／Response Retryも考慮する。STOPは進行中のTransactionを即時中断する割込み機能ではなく、通信完了後の別要求として扱う。

| 順序 | ATE送信 | Pico応答例 | 確認内容 |
|---|---|---|---|
| 1 | `BATT_CHECK_START` | `OK` | 診断結果の通信・完全Decodeが成功したことを確認する。 |
| 2 | `BC_MODE?` | `3` | BCコマンドによる測定モードの例。 |
| 3 | `BC_V1?` | `8.0` | 測定電圧1の例、単位V。 |
| 4 | `BC_IR?` | `100` | DCIRの例、単位mΩ。ATEが条件・判定基準と照合する。 |

| 結果Query | 値と単位 |
|---|---|
| `BC_MODE?` | 10進整数。0=データなし、1／2=充電測定、3=BC測定、11／12／13=各取得エラー。 |
| `BC_V1?`／`BC_V2?` | V。RAW mVを1000で除算する。 |
| `BC_I1?`／`BC_I2?` | A。RAW mAを1000で除算する。 |
| `BC_TEMP?` | signed ℃。 |
| `BC_SOC?` | signed ％。 |
| `BC_IR?` | mΩ。 |

- QueryはBC Cacheだけを参照し、NF55G通信・自動STARTを行わない。未取得・開始失敗後・停止後はERR:CACHE_INVALID。D0の寿命診断データをBC Cacheへ昇格しない。
- MODE13はBC取得エラーのデータであり、Protocol Transactionが成功すればSTARTはOKを返し、BC_MODE?は13を返す。OKを診断成功・製品PASSと扱わない。受信値の自動ゼロ補完やPASS／FAIL判定はしない（OI-07継続）。
- STARTは旧BCを処理開始時に無効化する。SQE等で開始が拒否された場合も旧BCを再利用しない。STOPのSQE等の明確な拒否では従前Cacheを保持するが、停止成立の証拠にはしない。timeout・最終BCC／FRAME異常では実行成否不明として関連Cacheを無効化する。
- STOPの正常応答も30文字。空応答を成功扱いする暫定FW吸収は行わず、OI-06の設計確認と実機検証を残す。停止後の状態は必要ならSTATUS_REFRESH後のBATT_CHECK_RUN?等で確認する。自動D1は送信しない。
- r1では充電中・放電中等に受付不可。AUTO_CHARGE無効でもBCは実行される。事前のCN／CF・パラメータ変更や受付条件の推測をPicoで行わず、NF55GのSQE／PMEをATEへ返す。実機前にバッテリ・負荷・外部観測・復旧条件を担当者が確認する。

### 14.12 寿命情報設定 LIFE_SET／SL

量産使用は未確定だが正式ATE入口として実装する。LIFE_SET_123は12.3％を表し、SL DATA=07B00000。LIFE_SET_4095はFFF00000（保守用電源識別値）。0～4095の検査による拒否や桁切捨ては設けず、LIFE_SET_4096は100000000の9文字を送る。負数-1は-0100000として送る。3桁HEXには0～4095以外の数値を格納できないため、上限超過は長さ異常も伴う。

LIFE_SET_RAW=GGG00000では不正HEXをそのまま送り、LIFE_SET_RAW=は空DATA、LIFE_SET_RAW=FFFは3文字を送る。RAWはHEX・値・予約・長さを検査しない。制御文字・非ASCIIを除き、既存ATE行長上限と行前後の空白除去は共通のまま。通常設定とRAWに使用モードや試験ロックは設けない。

T2=100ms、正常応答DATA=0文字。成功／ambiguous後はDATA INVALID、PME／SQE／CMEではCache維持。どちらも自動読戻しせず、明示DATA_REFRESH後にBATT_DEG_TOTAL?を読む。読戻しの根拠はr1 p.41の積算BATT_DEG（SET LIFE値）。PME後も新規D0を取得し、旧Cacheを読戻しと混同しない。Queryは0.1％変換済みなのでFFFは409.5と表示される。

SLは条件によりOFF期間データをクリアするため、前後のD0 RAWと元の寿命値を退避し、終了時は元RAW3文字＋00000を明示復元する。OFF期間データは寿命値復元では戻らない。実機PME・受理／切捨て等はOI-08として継続し、Picoで製品判定・応答補正をしない。

実機手順: Life_Set_Hardware_Test_Procedure_20261109.md。後続の2026-11-10実機結果Life_Set_Hardware_Test_20261110.mdでは、バッテリ／負荷未接続のS1.13でLIFE_SET_123（12.3％）→明示D0→元RAW000復元→明示D0を確認。SL2回OK／再送0、OFF期間RAWは寿命値復元後も戻らないことを確認した。範囲外・不正RAW・保守識別値・再投入保持は未検証、OI-08はOpen継続。

### 14.13 外部測定器の設定とHOST通常リセット

ATEが試験条件に従って固定レンジまたはAUTOを決定し、EXT_SENDで設定、EXT_QUERYで設定を読戻し、明示測定へ進む。Pico／HOSTは本文や指定レンジを独自補正しない。本文に機器終端を含めず、ATE行にはCRLFを付ける。現行7355の機器本文MD?等をHEX化する必要はない。EXT_QUERYの応答HEXは復号して扱い、機器エラーと中継エラーを分ける。設定例は第14.16節。

例: EXT_QUERY 2000 *IDN? → OK:EXT_RX:<byte数>:<原文HEX>。EXT_SENDのOK:EXT_TXだけで設定成立・測定成功を判定しない。中継は自動再送しない。timeout後は成否不明／faultを確認し、同じ測定や設定を無条件に繰り返さない。2026-11-25にADC・20 V・セット間1秒の400セット耐久を受入済み。過去のSCPI無応答原因、200 mV耐久、他機種への互換性は未確認。

開発用RSTはHOST_INFO? METER → HOST_RESET METER → HOST_INFO? METERの順とする。各応答を待ち、ACCEPTEDとDONEを分ける。新nonce確認前は通常中継を再開しない。新nonce照合後も既存fault／ambiguousを自動解除したとは扱わず、明示通信でREADY・識別応答等を確認する。親Pico・NF55G・7355本体をリセットする指令ではない。

### 14.14 測定値を取得しATEで確認する

| 順序 | ATE送信または操作 | 確認内容 |
|---|---|---|
| 1 | `TEST_START` | OKを確認。製品Cacheおよび前試行の取得値は失効する。 |
| 2 | ATEで動作条件・レンジを設定し読戻し確認 | 機器設定はEXT_SEND／EXT_QUERY。取得自身は設定を変更しない。 |
| 3 | `CAL_MEASURE_BATT_V A 4000 MD?` | OK:CAL_MEASURE:<取得ID>を受ける。4秒は例示で、試験条件に従って指定する。 |
| 4 | `CAL_MEASUREMENT_BATT_V? A` | 対象・点・単位・原文・校正候補をATEで照合する。 |
| 5 | 必要なら別点を明示取得、終了後`TEST_END` | 使用済み試行のIDを次の製品へ持ち越さない。 |

DISCHG_I／BATT_CHGは7355のV原文を厳密に1000倍してmVへ正規化し、50A／50mVシャントにより同じ数値をAの校正候補として返す。BATT_VはV／V。符号・仮数桁を保持し、float丸め・絶対値化を行わない。原文HEXはCRLF付きV表記のまま。OL等は数値構文が成立しても採用しない。

取得失敗後は同点旧値へ戻さず、旧取得IDも採用しない。CAL_MEASUREMENT?は再測定しない。測定値採用後の明示ADと別指令ARは第14.16節で行う。取得から自動書込みしない。量産での点対応・正式REF表現は未確定。

### 14.15 QR原文と送信内容を確認してUNITへ書き込む

| 順序 | ATE送信または操作 | 正常時と確認内容 |
|---|---|---|
| 1 | `TEST_START`、必要な`INFO_REFRESH`と事前Query | 製造情報・設定の元値を別途記録する。 |
| 2 | `QR_SCAN 10000` | OK:QR_ARMED:<取得ID>。10秒は例示。受付後に対象ラベルを読む。 |
| 3 | `QR_GET? <取得ID>` | READING中は取得待ち。同じIDでREADYの原文応答を確認する。 |
| 4 | `QR_DATA? <同じ取得ID>` | SS DATA100桁HEXを復号し、対象製品・REV・LOT・号機・変更なし領域をATEで確認する。 |
| 5 | `QR_WRITE <同じ取得ID>` | ATEが採用した場合だけ送信。OK:QR_WRITE:<ID>はSS通信成功。 |
| 6 | `INFO_REFRESH`→`UNIT_REV?`／`UNIT_LOT?`／`UNIT_SERIAL?` | SSではINFOを失効するため、明示D5後に一致を確認する。 |
| 7 | 必要な非対象欄のQuery、`TEST_END`と最終Self Check | 非対象欄保持・ログ状態を確認する。 |

QRは型式8＋品目コード14＋REV3＋YY2＋WW2＋号機6の計35文字。型式・品目コード・REV値を例示値に固定しない。実機確認原文US250A-CGXE-009491-101A1.2601000001ではUNIT_REV=`A1. `（末尾空白）、UNIT_LOT=`2601`、UNIT_SERIAL=`000001`となる。REV3文字の右にASCII空白0x20を1文字追加する。A03ならA03<SP>、B7.ならB7.<SP>であり、前詰め・ゼロ埋め・末尾空白削除をしない。D5の4バイトと照合する。FW6／ADU14／BBU14／予約2はF埋めの変更なし指定。型式・品目コードはSSへ格納しない。

最初の完全1件を固定し、2件目で差し替えない。QR_GET?だけで書込み可能にはならない。QR_DATA?で内容が不適合ならQR_CANCELを明示する。実行結果を得たQR_WRITEは成功・明示拒否・成否不明とも取得IDを消費し、再使用を拒否する。書込み前BUSY／未接続拒否は無送信で保持する。TEST_END成立・再STARTでも失効する。

通常の単方向モードでは親UART到着済みの旧データを開始時に破棄するが、HOST内処理中の旧QRは受付後に届き得る。771ms／1080ms遅着の実機記録がある。ATEは予定製品の型式・品目・REV・LOT・号機と照合し、不一致ならQR_CANCELし、対象ラベルを改めて読む。旧QR識別の双方向候補は第14.17節に示す。電源再投入後の製造情報保持・RST不要cold-start・製造号機重複管理も今回の限定確認外。QR HOSTのINFO／RESETは利用できない。

### 14.16 ADC校正をATEから順に実行する

この節はS1.14B／UNIT 000001の診断入口を対象とする。実機書込みは後日のデバッグで行う。書込み前に製品の元補正データと復元方法を確認し、対象回路・試験条件・校正点A/Bを確認する。動作条件と保護範囲は校正実装仕様に従う。

| 順序 | ATE送信または操作 | 応答と次へ進む条件 |
|---|---|---|
| 1 | 治具FW・設定、7355のADC言語とUSB CDCを確認 | 外部測定器有効、診断有効、対応親FW／HOSTを配置記録で確認。無効ならここで停止。 |
| 2 | `*IDN?` → `PICO_SELF_CHECK?` → `SD_STATUS?` → `LOG_DROP_COUNT?` → `HOST_INFO? METER` | 各応答を保存。治具・測定器HOST・ログの事前状態をATEが確認。 |
| 3 | `TEST_START` → `INFO_REFRESH` → `FW_REV?` → `UNIT_SERIAL?` | 各応答を待つ。S1.14B／000001でなければ本診断書込みは停止。 |
| 4 | 7355を下記の設定表で設定・照会 | EXT_TXだけで進まず、DCV・連続・即時・ヘッダ・メモリ呼出・レンジの一致を確認。 |
| 5 | ATEで対象回路のA点条件を設定し安定を待つ | 目標値と実測値を混同しない。3回路の条件は第14.4節と試験指示に従う。 |
| 6 | 例 `CAL_MEASURE_BATT_CHG A 4000 MD?` | OK:CAL_MEASURE:<ID>。ERRなら旧Cacheを採用せず停止。 |
| 7 | `CAL_MEASUREMENT_BATT_CHG? A` | 対象／点／符号／測定単位mV／校正単位A／原文をATEで確認し採用。 |
| 8 | `CAL_WRITE_BATT_CHG A` | OK:CAL_WRITE:<VALUE8>:<AD_ADC>:<計算値原文HEX>を保存。AD一回。製品PASSにはしない。 |
| 9 | `AD_VERIFY_BATT_CHG A` | OK:AD_VERIFY:BATT_CHG:A:<VALUE8>:<REF8>:<AD_ADC>:<AR_ADC>を保存。ATEが表現を考慮して照合。小数を整数REFで一致確認できなければ照合未成立として停止・記録。 |
| 10 | B点の条件設定→`CAL_MEASURE_BATT_CHG B 4000 MD?`→`CAL_MEASUREMENT_BATT_CHG? B`→`CAL_WRITE_BATT_CHG B`→`AD_VERIFY_BATT_CHG B` | 取得・照会・書込み・読戻しで同じ点を指定し、各段階で応答と値を確認。A点失敗を残して自動継続しない。 |
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

失敗時は後続書込みを止める。取得失敗は再測定する場合もATEの明示操作とし、必ず新値を照会する。AD成功／成否不明では元測定Cacheは失効するため、同じCacheでの再書込みはしない。AR照合できない場合に丸め・絶対値化・許容差をPico側で補完しない。直接AD入口を第14.18節に追加したが、ARの整数REFから失われた小数の元値を復元できるとは扱わない。復元方法未確認の製品へ書き込まない。

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

### 14.18 人が測定器を読んでATEから直接校正値を書く

測定器とPicoの接続は不要。測定値の正しさ、単位、対象回路、校正点A/Bは人とATEで確認する。自動取得方式と直接方式を同じ製品・点へ同時実行しない。

| 順序 | ATE送信または操作 | 応答と確認内容 |
|---|---|---|
| 1 | 対応FW・診断有効設定、元補正値と復元方法を確認 | 現時点はS1.14B／000001のサンプル診断。 |
| 2 | TEST_START → INFO_REFRESH → FW_REV? → UNIT_SERIAL? | 各応答を待って対象個体を確認。 |
| 3 | 対象回路・補正点の条件を設定して安定を待ち、人が測定器を読む | 目安値ではなく実測値を使う。電流はA、電圧はVを指定。 |
| 4 | 例 `AD_4_A_1.85` | 充電電流A点へ1.85 A。OK:AD_WRITE:4:A:3FECCCCD:<ADC>:<計算値原文HEX>を確認・記録。 |
| 5 | `AD_VERIFY_BATT_CHG A` | 明示ARのVALUE8／REF8／AD ADC／AR ADCを保存。OKは受信成立であり一致やPASSとは別。 |
| 6 | ATEが読戻しと補正後測定を照合 | 小数がAR整数REFで一致確認できなければ照合未成立として記録し停止。丸めで合格にしない。 |
| 7 | 次点の条件設定→人の新値読取り→別のAD→別のAD_VERIFY | 例えば充電B点が0.50 AならAD_4_B_0.50。値は例であり、そのまま実機へ送らない。 |
| 8 | 必要なDATA_REFRESH／個別Query、外部測定、TEST_ENDとログ確認 | 補正成立・係数反映・再投入保持は別検証。実機デバッグは後日。 |

実測値が44.25 Aなら放電A点の例はAD_1_A_44.25、実測電圧8.12679 VならバッテリA点の例はAD_2_A_8.12679。TYPE3／5も同じ書式。読戻しはAD_VERIFY_DISCHG_I、AD_VERIFY_BATT_V、AD_VERIFY_ACDC12V_V、AD_VERIFY_BATT_CHG、AD_VERIFY_12VOUT_VへA／Bを別引数で指定する。必須校正は従来の3回路であり、TYPE3／5を必須工程に追加する指示ではない。

NaN／Inf／OL・単位付き・生HEX・float32 overflow／非ゼロunderflowを拒否する。通常のfloat32丸めは生じるためVALUE8を実送信値として記録する。Picoで物理範囲制限・絶対値化・値の自動補完を行わない。書込み正常／成否不明後は同回路の旧DMM A/B Cacheを再使用しない。成否不明・応答不正は再送せず、先行書込みを比較元にした誤照合も禁止する。

ログには人が入力したATE原文、source=ATE_DIRECT、回路・A/B点・入力値・VALUE8・AD DATA・応答原文・再送情報を残す。取得CacheのIDを人の実測記録の代わりに作らない。人が値を読み違えていないことの確認と最終PASS/FAILはATE側で行う。

## 15. 略語と用語

| 表記 | 説明 |
|---|---|
| ATE | 自動試験装置。本書ではPicoへ指令を送る試験プログラム側。 |
| NF CMD | PicoからNF55Gへ送信する製品側コマンド。例 D0 / D1 / SP。 |
| NF DATA | 製品側コマンドに付加するデータ。ATEの引数を仕様に従って変換する場合がある。 |
| T1 / T2 | T1はCommand ACK待ち、T2は有効ACK受信後の応答待ち時間。ATE全体の応答タイムアウトとは別。T1=200msは暫定、D0 T2=300msは2026-11-11採用値。 |
| Query / Refresh | 保存値の参照 / NF55Gと通信して保存値を更新する操作。 |
| Cache | Pico内に保持する取得済みデータ。一時保存領域。 |
| VALID / INVALID | 完全取得・Decode成功済み / 参照不可。VALIDは現在値との一致保証ではない。 |
| Protocol / Transaction | 通信手順 / 1件の要求から応答処理までの通信単位。同時実行は1件のみ。 |
| Protocol SUCCESS / OK | 通信手順の成功。製品動作成立や製品PASSとは別。ローカルコマンドのOKは各処理の受付・完了を示す。 |
| Control / Set / Clear | 製品制御 / 設定 / 消去。対象Cacheの無効化と後続確認が必要。 |
| ACK / NAK | 受信確認 / 否定応答。PicoからNF55G応答へ返すNAKはplain 0x15でReason Codeを付けない。 |
| BCC / FRAME | フレームの検査値 / 通信データの形式。異常時は再送・成否不明の扱いがある。 |
| Command Retry / Response Retry | コマンド再送 / 応答再送。別々に管理する。PicoのCommand Retry上限は1回。 |
| ambiguous | 実行成否不明。操作が実行された可能性を考慮し関連CacheをINVALIDにする。 |
| ASCII HEX / decimal | 16進数をASCII文字で表した形式 / 10進数。FDは64 ASCII HEXを保持する設計。 |
| CRLF | CR=0x0D、LF=0x0A。要求例はCRLF。応答は設定依存で現行ソース既定CR。 |
| Decode / raw / chars | 通信値の解釈・変換 / 未変換データ / 文字数。 |
| Manufacturing / Parameter / reserve | 製造情報 / 設定値 / 予約領域。 |
| FW / RTC / SD | ファームウェア / 時計回路 / ログ保存用メモリカード。 |
| BC / AR / EL / OL / FD / EB | バッテリチェック / 補正情報読出し / イベント履歴 / 操作履歴 / Flashデータ読出し / 非同期イベント通知。 |
| Open Issue / provisional | 未確定事項 / 暫定値。確定扱いにしない。 |

## 16. 実機確認範囲と量産使用上の制約

2026-11-27までのREADME／CHANGELOG、実装・テストと実機結果を照合した範囲を示す。既存項目の個別条件は2026-11-09時点の確認記録を保持し、下表に直近進捗を追加する。仕様文書中の過去時点の「未実施」は、その後の実機記録と区別する。通信確認は製品PASSや量産承認を意味しない。

| 対象 | 確認できた事実 | 未確認事項 / 使用制約 |
|---|---|---|
| D0 / D1 / D5とDATA / STATUS / INFO Query | 実機通信・個別Queryの応答記録あり。 | D0 CHARGE_END副作用はOI-03継続。全実条件・量産Timingの検証とは別。 |
| D2_REFRESH | SC実施後、PS_ON=1で通信・30文字Decode成功。2026-11-11の通常ATE経路で10回成功。 | D2-PS-01受付条件解釈はOpen。量産原則未使用。専用ATE Query未定義。 |
| D3_REFRESH | 通信・21文字Decode成功。2026-11-11の通常ATE経路で10回成功。 | LIFE_CALC clearの前後比較は未確認。専用ATE Query未定義。 |
| D4_MAINT_READ | 旧試験2要求は最終ACK_TIMEOUT。2026-11-11の製品T2非変更・再送なし・Cache非採用RAM観測では完全応答10回、ACK後全件100ms超過／最大133ms。 | D4-TIM-01継続。量産では使用しない。T2を独断で延長しない。 |
| ERP_SET_0_0 / 1_0 / 0_1 / 1_1 | 全4組合せをHost / Mockで検証。 | COM14／COM6へ配置・hash照合済み。Sample実機試験は未実施。充電有効は充電開始を保証しない。 |
| CLOCK_SYNC | SC送信とD0日時読戻しの実機記録あり。 | 長期保持・電源切入後などは別途確認。指定時刻の影響を管理する。 |
| PARAM_<ITEM>_<VALUE> | 通常10項目の範囲・未変更マスク・SP応答・CacheをHost / Mockで検証済み。 | 項目別入口はCOM14／COM6へ配置済み、実製品設定は未実施。保護5項目とCHG_IR_THDは対象外。 |
| PARAM_SET / PARAM_RESET | 同値書戻し、EVENT_ENABLE変更→初期化、元RAW50文字復元・読戻しを確認。 | 全設定項目の実変更・保持・保護動作の網羅試験ではない。 |
| CLEAR_POWER / BATT / ALL / LOG | 4種の通信、CD後Cache、CL後全EL / OL無効化と空ログを確認。 | ALLは先行個別消去後の0維持。単独での非ゼロ値全消去、バッテリ接続条件での影響は未確認。 |
| BACKUP_ENABLE | 非バックアップ状態でSQEでなくOKを受信。前後D1同値、ユーザー報告は出力変化・瞬断・再起動なし。 | BE-ACCEPT-01継続。数値電圧・波形、バックアップ動作成立・実放電は未確認。 |
| BATT_CHECK_START / STOPとBC Query | BC 30文字、T2=6秒、開始結果採用・停止時無効化をHost / Mockで検証。 | 評価用。COM14／COM6へ配置済み、実機未実施。OI-06 / 07はOpen。 |
| CHARGE系 / BACKUP_OFF / OUTPUT_RESTART | Host / Mockで処理・Cache規則の検証あり。 | 本一覧の照合で実機動作成立の記録を確認していない。記録不在だけで未実施や原因を断定しない。OI-09等継続。 |
| RTC / 診断 / FW_UPDATE拒否 | RTC読書き・FU禁止等の記録あり。2026-11-10の向き修正後、一回の電源切断・再投入で保持と3秒進行、OSF=0を確認。 | 電源断時間・電池電圧・長時間保持は未測定。DEV-RTC-01はOpen。NF_COMM_CHECK?の実通信は未実装。 |
| SD / Logger | 試験中の抜去・再挿入、終了後復帰、異常履歴保持、短時間連続記録を確認。 | 長時間・ロールオーバー・冷間起動・量産Timingなどは別途確認。 |
| EL / OL | 診断スクリプトの実機実績に加え、正式ATE Refresh / QueryをHost / Mockで検証済み。 | 今回の正式ATE入口の実機デバッグはERPと同時に後日実施。 |
| FD_READ / FD_DATA? | 6桁HEX要求、64文字保持、Cache・異常系をHost / Mockで検証済み。 | READ-FD-01のID表記とOI-10はOpen。正式ID確認後に実機デバッグする。 |
| LIFE_SET_<VALUE> / LIFE_SET_RAW | 2026-11-10、S1.13・バッテリ／負荷未接続で12.3％設定→D0読戻し→元0.0％復元。再送0、CSVのSD／PC SHA一致。 | OFF期間RAWは元値に戻らない。範囲外・不正RAW・保守識別値・外部動作・保持は未検証。量産使用未確定、OI-08継続。 |
| D0 T2=300ms | 2026-11-11、S1.13・PS_ON=1／BATT_ON=0で10回成功、ACK後180～182ms、再送0。 | 長時間・異常系・EB競合・量産全条件は未受入。OI-02／03継続。 |
| EXT中継／HOST通常RST | .23.2配置・INFO→RST→INFOで新nonce確認、後続の明示IDN成功。READ10回とREAD＋D1＋SD＋RTCの50burst成功、drop0、通信中SD write/flush0。 | 11月25日にADC・20 V・1秒間隔で400/400セット受入済み。timeout／再送／再起動／drop0、SD CSV400件SHA一致。過去SCPI無応答原因、200 mV耐久、他機種・量産復旧全般は未確認。 |
| CAL取得／照会 | 2026-11-23、BATT_Vの2試行・4取得、再取得後旧ID拒否・終了失効・Query無送信を確認。AD送信0。 | 11月25日ADC経路のBATT_V取得とR3 overrange時の旧Cache失効・R5再取得を確認。AD／ARなし。実シャント・3回路2点通し・CAL-EXT残件は継続。 |
| QR→SS→D5 | 2026-11-23、S1.14Bで2連続読取りの最初の値固定、SS一回、UNIT3欄完全一致。FW／ADU／BBU／予約／設定不変。CSV80記録・14列・SHA一致、drop0。 | 11月25日A/B別試行の取得・旧ID失効、再起動後初回取得を確認。11月26日A03<SP>／B7.<SP>のSS→D5一致。旧QR遅着は再現し、双方向は別の候補試験。保持・量産全体受入／OI-14・23は継続。 |

本改訂の直接指定AD追加後、Host Unit Test / Mock NF55G Test全567件成功。実機未配置。既存の直近記録では全557件成功（2026-11-26、双方向QR候補）。11月25日ADC経路は548件、回路名校正入口は543件成功。これらは既存記録であり、本改訂に伴う実機再試験の結果ではない。Rev.1時点の全268件成功は過去実績として保持する。主な対象はD0～D5の取得・完全Decode・Cache、Control / Clearの無効化、SC変換、SP / RP空応答、FU禁止、ATE CRLF、Logger / SD復帰・最終Self Check。実機確認範囲は上表に従い、Host合格から実機成立を推測しない。

追加参照: docs/Protocol_State_Machine.md、docs/Test_Specification.md、docs/Real_Hardware_Test_Log.md、docs/QR_Reader_Requirements.md、docs/Calibration_External_Measurement_Requirements_20261104.md、docs/CH9350_QR_DMM_Plan_20261109.md。

### 直近追加機能の実機確認範囲

| 対象 | 確認できた事実 | 未確認事項と停止条件 |
|---|---|---|
| CAL_WRITE／AD_VERIFY | S1.14BのBATT_CHG A人工値診断で小数REF切捨てを観測。回路名入口3回路とA/B固定対応・範囲保護はHost／Mockで確認。 | 実シャント→ADC取得→AD→ARの全通し、新回路名版の実測書込み、他回路・点・再投入保持は未完。診断有効・個体一致・照会済みが必要。 |
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
- `docs/AD_Direct_ATE_20261126_Rev0.md`
- `src/command_parser.py`、`src/main.py`、`src/calibration_acquisition.py`、`src/calibration_write.py`、`src/config.py`

## 17. 改訂履歴

| 版数 | 日付 | 変更内容 |
|---|---|---|
| Rev.0-draft | 2026-09-01 | 初版。元Markdown / Wordを保持する。 |
| Rev.1 | 2026-11-09 | 実装有無の ※、PARAM_SET、SC指定、自己診断・SD復帰、7.1～7.5の例文、略語、実機範囲・量産制約を追加。既存一覧の構成・表現を基本維持。未確定事項は確定しない。 |
| Rev.1 追記 | 2026-11-09 | ERP全4組合せを実装済みとして個別掲載。第14.8節へ指定値の読み方、用途、設定後の確認例、元設定の復元と充電許可の注意を追加。 |
| Rev.1 読出し追記 | 2026-11-09 | EL／OL全12ブロックと個別履歴Query、FD読出しを実装済みへ更新。第14.9節に使用例とCache・符号化・FD確認事項を追記。実機デバッグはERPと同時に後日実施。 |
| Rev.1 項目別設定追記 | 2026-11-09 | PARAM通常10項目を実装済みへ更新。第14.10節に範囲・10進指定例・他項目保持・読戻しと拒否対象を追加。Host / Mock全243件合格、実機未実施。 |
| Rev.1 BC追記 | 2026-11-09 | BC開始／停止と8結果Queryを実装済みへ更新。第14.11節へ評価用、MODE、単位、Cache・6秒T2・停止時の制約を追加。全256件合格、実機未実施。 |
| Rev.1 SL追記 | 2026-11-09 | 寿命設定とRAW入口を正式実装。第14.12節と別紙に範囲外送信・読戻し・復元を追記。全268件合格、量産未確定、OI-08継続。SLのPico配置・製品送信は未実施。 |
| Rev.2 | 2026-11-23 | D0 T2=300ms、ATE 57600bps、EXT中継・測定器HOST管理・CAL取得照会・QR確認後SS書込みを反映。使用例、失効・成否不明・実機限定範囲を更新。AD/ARと直接SERIALは未実装、既存IssueはCloseしない。 |
| Rev.3 | 2026-11-26 | 7355のADC運用・回路名取得照会・サンプル診断ADと別ARを反映。ATEの順序付き校正手順、QR受付からSS・D5照合、双方向QR候補の待ち分岐、実機前提と停止条件を追記。400セット受入と11月26日QR進捗を反映。実機デバッグ・FW配置は本改訂では実施しない。 |
| Rev.4 | 2026-11-26 | 人が測定器を読み、ATEからADのTYPE／POINT／VALUEを直接指定する方式を採用確定・実装。第10.6／14.18節に手順・応答・制約を追記。Cache方式は併用。PARAM_RESETの対象範囲を明記。製品側未確定Issueと実機デバッグは継続。 |

| Rev.5 | 2026-11-27 | 校正点A/B統一、二重指定廃止、別Python定数による必須6点保護。旧形式拒否、境界包含・不正設定拒否。実機配置未実施。 |
