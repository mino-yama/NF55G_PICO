# 11月27日打合せ 校正機能の実装仕様・結果

Revision: Rev.0  
Date: 2026-11-27

今回の「実装を進めて下さい」を改版案Rev.2の組込み実装指示として適用した。案件フォルダはNF55G_Picoを継続する。原典・過去の改版案・設定候補・配置済み実機は変更していない。本書が現在のソースの校正契約であり、過去資料の「実装許可待ち」は当時の履歴とする。

## ATE入口と点の対応

| 用途 | 現在の書式 | 応答 |
|---|---|---|
| 測定 | `CAL_MEASURE_<回路> <A/B> <期限ms> MD?` | 従来どおり。自動ADなし |
| 照会 | `CAL_MEASUREMENT_<回路>? <A/B>` | 従来どおり。Cacheのみ |
| Cache採用 | `CAL_WRITE_<回路> <A/B>` | `OK:CAL_WRITE:<VALUE8>:<AD_ADC>:<計算値原文HEX>` |
| 人の実測値直接指定 | `AD_<TYPE>_<A/B>_<VALUE>` | `OK:AD_WRITE:<TYPE>:<A/B>:<VALUE8>:<AD_ADC>:<計算値原文HEX>` |
| 明示読戻し | `AD_VERIFY_<回路> <A/B>` | `OK:AD_VERIFY:<回路>:<A/B>:<VALUE8>:<REF8>:<AD_ADC>:<AR_ADC>` |
| 取得ID式診断 | `CAL_WRITE <取得ID>` | `OK:CAL_WRITE`。BATT_CHG A限定、点はID内のAを使用 |
| 整数照合診断 | `AD_VERIFY BATT_CHG A` | 従来の整数REF・送信float32・ADC比較。量産の小数保持確認へ転用しない |

TYPEは1=DISCHG_I、2=BATT_V、3=ACDC12V_V、4=BATT_CHG、5=12VOUT_V。回路名指定も維持する。直接指定のVALUEはA/Vの10進実測値で、DMM接続・Cache不要。内部記録とAR decoderのキーもA/Bとし、通信生成箇所だけA→1、B→2へ変換する。製品通信・EEPROMを変更していない。

旧P1/P2引数、直接ADの数値点1/2、Cache書込みの点二重指定は拒否する。旧取得ID式にも点を追加できない。引数拒否は`ERR:CAL_WRITE_ARGUMENTS`／`ERR:AD_VERIFY_ARGUMENTS`／`ERR:AD_POINT`。旧形式を自動的に読み替える別経路は設けない。

## 必須校正回路と書込み保護

| 回路 | 動作条件 | A：基準／許可範囲 | B：基準／許可範囲 |
|---|---|---|---|
| DISCHG_I | バッテリ充電 | 44 A／35.2～52.8 A（DC5.2 V、12 V：15 A近傍） | 0.3 A／0.24～0.36 A（DC5.2 V、12 V：0 A近傍） |
| BATT_CHG | バッテリ放電 | 1.85 A／1.48～2.22 A（バッテリ7.2 V近傍） | 0.5 A／0.4～0.6 A（バッテリ10.6 V近傍） |
| BATT_V | 充電時 | 8 V／6.4～9.6 V | 5 V／4～6 V |

基準値は固定送信値ではない。各点で取得・確認した実測値を採用する。これは書込み保護であり、製品精度の合否規格ではない。TYPE3/5には未指定の範囲を追加せず、既存の有限float32・診断条件を維持する。必須3回路だけを保護する範囲であり、TYPE3/5の保護規格はOpenのまま。

数値の正本はルートの[calibration_limits.py](../calibration_limits.py)。Picoの`/calibration_limits.py`として配置し、`src/calibration_guard.py`からimportする。更新はLOWER/UPPERとSETTINGS_REVを編集し、配置後にPicoを再起動する。動作中の自動再読込み・更新コマンドは追加しない。元の設定候補は履歴保持。

送信直前に必須6点の設定すべてを検証する。版が空、定数欠落、数値以外（bool含む）、NaN/Inf、float32範囲外・非ゼロのアンダーフロー、下限＞上限、読込み失敗は`ERR:CAL_WRITE_SETTINGS`／`ERR:AD_WRITE_SETTINGS`で必須3回路を無送信拒否する。設定ファイルが欠落・構文不良でも他の治具機能は起動できる。

元の10進入力を、設定値の10進表記とfloat変換前に比較し、下限以上・上限以下を許可する。次に送信float32値を同じfloat32へ変換した上下限と比較する。35.2等の境界はfloat32表現への通常丸めを許可するが、元入力が境界外ならfloat32で境界と同値になっても拒否する。クリップ・目標値置換はしない。

Cache方式は単位換算済み候補A/Vへ適用し、電流のDMM原文VへA規格を直接適用しない。直接指定は入力A/Vへ適用する。範囲外は`ERR:CAL_WRITE_RANGE`／`ERR:AD_WRITE_RANGE`。既存の不正値エラーは維持する。

送信前拒否はCache・照会済み記録・正常書込み比較元を消費しない。RAM Loggerへ回路・A/B・候補値・設定版・拒否理由を残す。正常書込みログにも設定版を残す。新しい鮮度期限は設けず、同試行・最新取得・照会済みという既存条件を維持する。

## 維持する制約

CALIBRATION_SAMPLE_ENABLED既定False、有効なTEST試行、同試行INFOのS1.14B／UNIT 000001照合を維持する。量産向けの制限解除ではない。Cache方式は照会済みの最新Cacheだけを書き込む。

正常／成否不明時のDATA／AR INVALID、測定Cache破棄、AD直接方式の同回路A/B失効、STATUS／INFO非昇格を維持する。ADのCommand Retryなし、診断T2=1000ms、ARは別指令・ACK後T2=100ms・Command Retryなし・AR Cache非採用。PicoのOKは製品PASSではない。FU送信禁止とNF55G単一Transactionを維持する。

## 検証と未確認事項

変更ファイル：

- `src/command_parser.py`：A/B単一点指定、旧形式拒否、取得IDから点を決定。
- `src/calibration_write.py`：書込み先・保持記録・応答・ログのA/B統一、共通範囲保護、設定版の記録。
- `src/calibration_guard.py`（新規）／`calibration_limits.py`（新規）：不正設定・境界・送信float32検証と、編集可能な設定正本。
- `src/nf55_decode.py`：ARキーをA/Bに統一。長さ・レコード順序・原文保持は維持。
- `tests/test_calibration_guard.py`（新規）／`test_calibration_write.py`／`test_direct_ad.py`／`test_ar_timing.py`／`test_decoder_complete.py`／`test_external_instrument_link.py`：新書式・保護・実際の送信点対応を検証。
- `README.md`、ATE／Decode／Cache／Module／Testの各Master、`Open_Issues.md`、`CHANGELOG.md`：現行仕様・実装状態・残事項を更新。試験担当者向け一覧はRev.5を新規保存し、旧版を保持。

`python -m unittest discover -s tests`によりHost Unit／Mock NF55G全575件成功（40.781秒）。必須6点の上下限包含、境界外微小差、全書込み入口、旧形式拒否、不正設定、拒否時のCache保持、単位換算経由の6点送信とAR読戻し、成否不明時失効・再送なしを確認した。実行結果は[試験ログ](../tmp/calibration_ab_20261127_tests.log)を参照。

実機配置・MicroPython実機import・実電流／実電圧を伴う書込み・実ATE移行は未実施。ARの小数保持・係数反映・電源再投入後保持・製品側正式契約は未確認のまま。CAL-GUARD-01～04、OI-04等を独断でCloseしない。検証済みのソース実装と未実施の実機確認を区別する。
