# NF55G ADC校正手順 | 7355設定・測定・書込み・読戻し

2026-11-25。対象は現行のサンプル診断版（製品FW `S1.14B`、UNIT `000001`）。3回路のA/B各点で、7355の設定確認 → 実測 → Cache照会 → ATEによる採用判断 → 明示AD → 明示ARを行う。以下は現行ATEの操作手順。 [回路別コマンド仕様](Cache_Write_HIL_Rev1.md)／[実機結果](Rev1_Deployment_Check_20261125.md)

## 1. 開始と対象確認

ATEは親PicoのCOM5（57600 bps、8N1）に1行ずつASCIIで送信し、各応答を受けてから次へ進む。7355はUSB CDC・SCPI、直流電圧の入力端子はV/COMを使う。電流校正では50 A/50 mV（1 mΩ）シャント両端の電圧を測定する。BATT_Vでは対象のバッテリ電圧を直接測定する。

| 順 | 送信 | 確認 |
|---|---|---|
| 1 | `*IDN?`、`COMM_STATUS?`、`SD_STATUS?` | 親Pico識別、`OK:state=IDLE`、SD `OK` |
| 2 | `HOST_INFO? METER`、`EXT_QUERY 2000 *IDN?` | 測定器HOST `READY`、応答原文でADCMT 7355を確認 |
| 3 | `TEST_START` | `OK`。この試行のログを開始 |
| 4 | `INFO_REFRESH`、`FW_REV?`、`UNIT_SERIAL?` | D5成功、`S1.14B`、`000001` |

## 2. 7355を直流電圧の単発測定に設定

USB経由では、各設定の直後に照会を1本送り、応答を受けてから次の設定を送る。`EXT_SEND` の `OK:EXT_TX` は中継送信の成立を表す。計器設定は照会結果で確認する。`EXT_QUERY` の応答 `OK:EXT_RX:<バイト数>:<原文HEX>` はHEXをASCIIに戻して読む。 [ADCMT 7355製品・取扱説明書案内](https://www.adcmt.com/en/products/dmm/7355)／[取扱説明書 §6.8.4、6-42〜6-46](../../../reference/ADCMT_7355_20261104/7355-ope--foa-00000201a00-e.pdf)

| 設定 | 設定コマンド | 直後の照会 | 期待する計器応答 |
|---|---|---|---|
| 連続測定OFF | `EXT_SEND 2000 :INIT:CONT OFF` | `EXT_QUERY 2000 :INIT:CONT?` | `0` |
| 直流電圧DCV | `EXT_SEND 2000 :SENS:FUNC "VOLT:DC"` | `EXT_QUERY 2000 :SENS:FUNC?` | `"VOLT:DC"` |
| 即時トリガ | `EXT_SEND 2000 :TRIG:SOUR IMM` | `EXT_QUERY 2000 :TRIG:SOUR?` | `IMM` |
| トリガ回数1 | `EXT_SEND 2000 :TRIG:COUN 1` | `EXT_QUERY 2000 :TRIG:COUN?` | `00001` |
| サンプル数1 | `EXT_SEND 2000 :SAMP:COUN 1` | `EXT_QUERY 2000 :SAMP:COUN?` | `00001` |
| トリガ遅延0秒 | `EXT_SEND 2000 :TRIG:DEL 0` | `EXT_QUERY 2000 :TRIG:DEL?` | `+0.0000E+00` 相当 |

設定の処理完了を確認する場合は `EXT_QUERY 2000 *OPC?` の `1`、機器エラー確認は `EXT_QUERY 2000 :SYST:ERR?` の `+0,"No error"` を記録する。測定は後述の `CAL_MEASURE_… :READ?` から始める。別途 `:INIT` や `*TRG` を送る必要はない。

## 3. 測定点ごとの入力とレンジ

| 回路 | A点の目安 | B点の目安 | 7355の測定対象と固定レンジの目安 |
|---|---:|---:|---|
| `DISCHG_I` 放電電流 | 44 A | 0.3 A | シャント電圧44 mV／0.3 mV。200 mV級 |
| `BATT_CHG` 充電電流 | 1.85 A | 0.5 A | シャント電圧1.85 mV／0.5 mV。200 mV級 |
| `BATT_V` バッテリ電圧 | 8 V | 5 V | バッテリ電圧。20 V級 |

上表は測定・レンジ選択の目安。各点の実際の入力、負荷、製品状態を確認し、安定後に取得する。A/Bを製品のP1/P2に割り当てるのはATE側。 [各点の入力・負荷条件](../../Integrated_Hardware_Flow_20261123_Rev0.md#7-adとarを含む3系統2点補正)

**固定レンジを使う場合**

1. `EXT_SEND 2000 :SENS:VOLT:DC:RANG:AUTO OFF` → `EXT_QUERY 2000 :SENS:VOLT:DC:RANG:AUTO?` が `0`。
2. シャント測定の最小レンジ指定例は `EXT_SEND 2000 :SENS:VOLT:DC:RANG MIN`。5〜8 V測定の数値指定例は `EXT_SEND 2000 :SENS:VOLT:DC:RANG 10`。指定例はいずれも当該実機で未検証。直後に `EXT_QUERY 2000 :SENS:VOLT:DC:RANG?` で実レンジを読む。
3. `EXT_QUERY 2000 :CONF?` の機能・レンジ・分解能と `EXT_QUERY 2000 :SYST:ERR?` を記録し、ATEがそのレンジで測定するか判断する。校正手順が固定レンジを定めている場合はその条件に照合する。

**自動レンジを使う場合**

1. `EXT_SEND 2000 :SENS:VOLT:DC:RANG:AUTO ON` → `EXT_QUERY 2000 :SENS:VOLT:DC:RANG:AUTO?` が `1`。
2. 測定応答を取得した後、`EXT_QUERY 2000 :CONF?` で実際に選ばれたレンジを記録する。

実機では `:SENS:VOLT:DC:RANG 20` の指定に対して約200 Vが読み戻された。書込み時のレンジ記録は読戻し値を使用する。約2 Vの状態で8 Vを測定すると `ERR:CAL_MEASUREMENT_OVERRANGE` となった。 [BATT_Vの実機試験](Rev1_Deployment_Check_20261125.md#batt_v-aからp1の実機試行)／[レンジ設定・読戻し原文](17_batt_v_range_20v.log)

## 4. 各点の測定・書込み・照合

送信例は測定点A・書込先P1。B点やP2で実施する場合は、ATEが採用した測定点と製品の書込先を引数に指定する。同一試行で照会済みの最新値を使用する。

| 回路 | 測定 | Cache照会 | 書込み | 読戻し |
|---|---|---|---|---|
| `DISCHG_I` | `CAL_MEASURE_DISCHG_I A 4000 :READ?` | `CAL_MEASUREMENT_DISCHG_I? A` | `CAL_WRITE_DISCHG_I A P1` | `AD_VERIFY_DISCHG_I P1` |
| `BATT_CHG` | `CAL_MEASURE_BATT_CHG A 4000 :READ?` | `CAL_MEASUREMENT_BATT_CHG? A` | `CAL_WRITE_BATT_CHG A P1` | `AD_VERIFY_BATT_CHG P1` |
| `BATT_V` | `CAL_MEASURE_BATT_V A 4000 :READ?` | `CAL_MEASUREMENT_BATT_V? A` | `CAL_WRITE_BATT_V A P1` | `AD_VERIFY_BATT_V P1` |

1. 必要に応じて `STATUS_REFRESH` と状態照会を実行し、製品と実入力が対象点の条件であることを確認する。
2. `CAL_MEASURE_…` で7355のDCV確認とREADを実行する。`OK:CAL_MEASURE:<取得ID>` を受けたら、回路名と点だけで `CAL_MEASUREMENT_…?` を照会する。取得IDは記録に使い、コマンド引数に付けない。
3. Cache応答で符号、数値、単位、原文を確認する。電流2回路は測定mV→校正候補A（1 mΩなので数値同一）、電圧はV→V。ATEが実測値を採用した場合にだけ `CAL_WRITE_…` を送る。書込値は実測値をfloat32へ格納した `VALUE8`。
4. `OK:CAL_WRITE` を受けたら、別要求の `AD_VERIFY_…` でARを読む。返却される `VALUE8`、`REF8`、AD／ARのADCを保存し、ATEで照合する。S1.14Bの実機では8.1272 Vの書込みに対しARが整数8を返した。`OK:AD_VERIFY` は読戻しの通信成立を示す。小数を含む一致や内部保存の確認は別に記録する。
5. `ERR:CAL_MEASUREMENT_OVERRANGE` など取得失敗時は、その点の条件を確認して新しく測定する。ADが成否不明の場合は結果を記録し、同じ書込みを自動再送しない。

全点の操作が終わったら `TEST_END` → `PICO_SELF_CHECK?` → `SD_STATUS?` → `LOG_DROP_COUNT?`。自己診断の `TEST_LOGGER`／`TEST_LOG_DROP` とSD正常を確認し、ATE原文、採用値、AD／AR、試行CSVを保存する。 [試行とログの扱い](Bench_Handoff_Rev0.md)／[ARによる元値控えと復元の制約](Restore_Check_20261125.md)
