# ADC取得・Cache照会 実装・実機進捗 Rev.0

2026-11-23。23日スケジュールの次工程。基準258b800から開始し、ユーザーが採用したCAL_MEASURE／CAL_MEASUREMENT?を実装・親へ配置した。QRハード結合待ちの間に独立部分を開発。

## 実装とHost検証

- 新規`src/calibration_acquisition.py`: 7355固有のDCV機能確認→READ、単一総期限、数値形式のOL／演算エラー拒否、厳密なV→mV換算、取得ID・試行照合。
- `calibration_measurement.py`: pending token照合口を追加。
- `command_parser.py`／`main.py`: 採用済み取得・照会を非blockingで接続。取得中の外部link専有／SD通信busy、CAL取得結果のRAM経由ログを追加。AD/AR/SS/FU送信経路は追加しない。
- 新規adapter/core試験15件、native C／親ADC試験7件、QR採取検証5件を含め、全503件成功（18.692秒）。[最終全回帰](Host_Mock_Final.log)。途中の497／498件のログも保持。
- [取得・照会の詳細仕様](ADC_Acquisition_Spec_Rev0.md)。電流3対象の換算・A/B、単位違い、OL、失敗後旧ID失効、総期限、取消、試行切替、Query無送信をHostで検証。実シャント接続の電流測定は未実施。

## 配置

親の実配置30sourceを[退避](parent_before/src)し、実機SHA照合。新規1＋変更3の計4ファイルを候補固定・実機compile／hash検証後renameし、合計31sourceを実機照合。[manifest](deployment_manifest.json)、[配置操作](deployment_operations.jsonl)。configの実機True、HOST FW .23.2は保持。

親／HOSTを再起動せずmoduleを読込み直し、既存UART／SD／RTC／Logger／製品Cache／外部linkを新appへ引き継いだ。SDを再初期化・二重マウントせず、親nonce `f2caeb2e46c95f01`／HOST nonce `CBFA8C2C4F42C7BA`とsessionを維持。[切替結果](activate_execution.log)。MicroPython上でも文字列によるV→mV換算を確認。

## 実ATEで確認できた事実

| 項目 | 結果 |
|---|---|
| 試行前取得 | NO_ACTIVE_TRIAL、機器要求なし |
| 第1試行A | 取得ID 00000001-00000001-BATT_V-A、+09.62071E+00 V |
| 第1試行B | 取得ID 00000001-00000002-BATT_V-B、+09.62071E+00 V |
| A再取得 | 取得ID 00000001-00000003-BATT_V-A、+09.62072E+00 V。旧A IDはINVALID |
| 第2試行A | 取得ID 00000002-00000004-BATT_V-A、+09.62071E+00 V。旧試行IDはINVALID |
| Query／不正本文 | Cacheのみの複数照会、不正`:CONF?`取得拒否で追加Qなし |
| 機器実送信 | 機能照会／READ各4、合計8 Q。HOST A/T/R各8、request/session相関一致 |
| 試行終了 | 測定Cache0枠、Logger停止、TEST期間終了、drop0／Queue0 |
| NF／SD | NF送信試行0、SD記録54件／flush5、通信中write/flush試行0 |

これは既存DCV入力での取得ソフト確認であり、実際の8V/5V補正点への設定・製品校正ではない。NF55GへADを書いていない。

## 診断停止・回収と未完了

取得・照会シーケンス完了後、親診断の最終assertが停止した。[初回結果](hardware_result.json)、[親出力](hardware_parent.log)。原因は試験コードが「製品Cacheは試験前後不変」と誤って要求したこと。既存dispatcherのTEST_STARTは全製品Cacheを失効する仕様であり、事前VALIDだったSTATUSがINVALIDになることが正しい。仕様／本番処理は変更せず、既存規則の回帰を追加した。

保持RAMを追加機器要求なしで回収し、全製品CacheがINVALID、NF0、fault=false、取得値0、Logger/drop/Queue正常を確認。[assert診断](hardware_assertion_diagnostic.log)、[保持RAM](hardware_recovered_parent.log)。[別名回収結果](hardware_recovered_result.json)は`ADC_HIL_RECOVERED_CSV_PENDING`。

残るSDログ2本の読戻し時点で親COM6がOS一覧から消失。原因は未確認。親の通常USB接続復帰待ちであり、取得を再実行しない。

- `/sd/BANK_A/20261123_131505_T000020.csv`
- `/sd/BANK_A/20261123_131511_T000021.csv`

CSVの実機／PC SHA一致・列・4取得ログの照合は未完了で、成功とは記録しない。`recover_verify_hardware.py`は再取得せず既存データから再開する。USB切離し前の最終確認はPIO4/5停止・入力化、Logger停止、NF送信禁止guard保持。現在の電源／runtimeは再接続後に再確認する。

## 次工程と残Issue

親接続復帰後、実ID／起動状態を確認してCSV2本を回収する。QR側は[結合確認準備](../QR_Hardware_Integration_20261123_01/Preparation_Rev0.md)へ進む。GPIO／現在FWと診断wireを照合し、正式QR Cache／SS仕様を推定しない。

CAL-EXT-02は取得／照会の部分を確定したがOpen継続。A/B↔P1/P2、AD/AR表現・小数読戻し・極性、QR/SS変換、量産全条件は未回答／未受入。今回追加コードは未コミット・未プッシュ。
