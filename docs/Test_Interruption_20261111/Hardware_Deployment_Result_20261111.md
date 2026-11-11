# 再START修正版：Pico配置・実機デバッグ結果

実施: 2026-11-11 09:49～09:51 JST。結果: 事前提示した範囲で期待動作を確認。通常待受へ復帰、COM6／COM20解放済み。

## 配置確認

- 対象: 既存治具Pico 2、COM6、unique_id=69f7d45962cfdfad。ATEはCOM20／115200bps。USB下位マイコンCOM21は操作していない。
- 事前に[手順](Hardware_Deployment_Test_Procedure_20261111.md)をチャットで提示し、その後実行。通信IDLE確認後のTEST_ENDで記録終了、SD・Self Check正常、破棄0を確認した。
- 配置直前のHost Unit／Mock NF55Gは284件成功。
- Pico内main.py／boot.py／srcの計25ファイルを[時刻別backup](deployment_20261111_094958/backup)へ退避。変更対象4ファイル以外の比較対象srcは、退避時点でPCとhash一致。
- `/src/logger.py`、`/src/sd_sink.py`、`/src/command_dispatcher.py`、`/src/main.py`のみ更新し、各Pico側SHA-256とPC側の一致を確認した。起動入口main.py／boot.pyは変更しない。
- [配置前後のhash・退避台帳](deployment_20261111_094958/deployment.json)。配置失敗やrollbackは発生していない。

## 実機シーケンス

| 操作 | 結果 |
|---|---|
| 初回TEST_START | OK、応答172.3ms |
| CLOCK_SYNC 261111095038（SC） | OK、製品Transaction 23ms、再送0 |
| DATA_REFRESH→時刻・電圧・電流等のQuery | OK、製品時刻20261111_095038、VOUT12=12.014、IOUT12=0.056、BATT_VOLT=0.003 |
| 最後のデータ取得後の待機 | 単調時計で10.000374秒 |
| 2回目TEST_START | **OK、応答163.3ms** |
| NF55_DATETIME?／VOUT12? | 両方ERR:CACHE_INVALID |
| 明示DATA_REFRESH→Query | OK、新規時刻20261111_095049 |
| 3回目TEST_START | **OK、応答200.2ms** |
| NF55_DATETIME?／VOUT12? | 両方ERR:CACHE_INVALID |
| 明示DATA_REFRESH→Query | OK、新規時刻20261111_095052 |
| TEST_END | OK、応答180.2ms |
| 終了診断 | Self Check OK、TEST_LOGGER=OK、TEST_LOG_DROP=OK、SD OK、累積破棄0、通信IDLE |

ATE送信開始間隔の実測最短は163.5ms。各要求は前応答後150ms以上空けた。応答時間はPCからの送信開始～CRLF応答受信完了で、USB／OS／UART転送を含む。今回の値から量産Timing全般の合格とは判断しない。

SC／D0の製品Transactionは、SC=23ms、D0=194／215／192ms。いずれもProtocol OK、ambiguous=False、Command Retry／Response Retryとも0。測定値は通信値であり、外部測定による製品PASS/FAIL確認ではない。

## 1試行1CSVの確認

| 試行 | CSV | サイズ | データ行 | 終了区分 |
|---|---|---:|---:|---|
| T000001 | 20261111_095037_T000001.csv | 2802byte | 27 | NEXT_TEST_START |
| T000002 | 20261111_095049_T000002.csv | 2742byte | 28 | NEXT_TEST_START |
| T000003 | 20261111_095051_T000003.csv | 3031byte | 30 | TEST_END |

3本はすべて`/sd/BANK_A/`。各ファイルに対応するTRIAL_STARTが1件、TRIAL_END_REQUESTが1件あり、試行IDとファイル名が一致。第1試行はSCとD0、第2・3試行は各D0だけのTransactionを確認した。再STARTの要求は旧ログに区切り要求として記録され、新ログにも開始要求として記録される仕様であり、この重複は試行データの混在とは区別する。

全行14列、SC／D0の送受信8フレームはすべてBCC一致。再STARTおよび旧CacheへのQueryからNF55Gへの自動Refresh／追加コマンド送信はなかった。

CSVは256byte単位で回収し、3本すべてSD／PCのサイズとSHA-256一致を確認。SD原本は変更していない。回収のため終了後にREPLへ入り、回収後は通常起動へ戻した。再起動前の試験診断はATE証跡に保存済み。再起動後もID応答、通信IDLE、SD OK、Self Check OK、破棄0を確認した。

## 証跡

- [ATE全送受信・応答時間・10秒待機](Restart_Fix_Sequence_20261111_095036.json)
- [CSV解析・hash・NFフレームとTransaction](verified_20261111_095036/csv_analysis.json)
- [第1試行CSV](verified_20261111_095036/20261111_095037_T000001.csv)、[第2試行CSV](verified_20261111_095036/20261111_095049_T000002.csv)、[第3試行CSV](verified_20261111_095036/20261111_095051_T000003.csv)
- [配置スクリプト](deploy_restart_fix.py)、[3試行シーケンス](run_restart_fix_sequence.py)、[分割回収スクリプト](recover_restart_fix_csv.py)
- [変更前の再START拒否結果](Hardware_Start_Repeat_Result_20261111.md)

## 残事項と変更範囲

今回の正常SD・逐次ATE条件では、再STARTによる前試行保存→新試行開始、3本のログ分離、旧DATA失効を確認した。実機で修正を要する異常は見つからず、前回作成した修正版をそのまま配置した。今回新規の製品ソース修正はない。

QR実入力・QR付き命名、新USB下位UARTの旧応答照合、SD抜去／close失敗等の実機異常系、量産Timing全条件は未検証。これらは今回の正常系確認から成立を推定しない。SS開発・空シリアルのSS拒否実装は保留。TEST-SESSION-01は人間確認前のためOpenを維持する。
