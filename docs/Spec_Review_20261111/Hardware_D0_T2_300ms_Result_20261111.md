# D0 T2 300msの実機配置と正常系試験結果

実施日: 2026-11-11。準備・配置は11:12以降、ATE試験は11:15:12～11:15:33 JST。

D0 T2=300msを治具Picoへ配置し、ATE経由のD0取得10回がすべて成功した。Pico内でのACK受信から完全応答受信までの記録値は180～182msで、今回の観測では300ms以内だった。Command Retry／Response Retryは各0、ログ破棄0。CSVを回収・照合後、通常待受へ復帰しCOM6／COM20を解放した。

## 配置と接続の確認

| 項目 | 確認結果 |
|---|---|
| 治具 | COM6、Pico unique_id=69f7d45962cfdfad、USB VID/PID=2E8A:0005 |
| ATE | COM20、115200bps、ID応答NF55G_PICO_FIXTURE,Rev.0 |
| 製品FW | 明示INFO_REFRESH後のFW_REV?は末尾空白を含む`S1.13 ` |
| 製品状態 | 明示STATUS_REFRESH後、PS_ON=1、BATT_ON=0 |
| 配置前退避 | main.py＋srcの25ファイルを時刻別backupへ保存。PCとの比較可能なsrcで不一致はconfig.pyだけ |
| 配置対象 | `/src/config.py`のみ。T2_D0_MS=600から300へ変更。その他ソースは上書きしていない |
| 配置後SHA-256 | `e20defbba549d9f79161f6cc265bdc8f782a556249392381e6e2681b3eaf7384`、PC／Pico一致 |
| 実行中の値 | CSV回収前、読み込まれていたsrc.configのT2_D0_MS=300、READ_REFRESH_COMMANDSのD0契約=300ms／327文字を確認 |
| USB下位基板 | COM21はポート一覧の確認だけで、接続・設定・配置を行っていない |

開始時はCOM20の`*IDN?`に3秒以内の完全応答がなく、製品試験指令へ進まずCOM6で個体・配置内容を確認した。config配置と通常起動後はID応答・通信IDLE・RTC／SD／自己診断正常・破棄0を確認できた。初期無応答の原因は確定しておらず、T2変更で原因が解消したとは判断しない。

実機前のHost／Mockは同日11:09の再実行で287件成功（4.128秒）。今回、製品用ソース・テストコードへの追加修正は行っていない。

## 実施シーケンス

TEST_STARTで独立ログを開始し、旧VOUT12?がERR:CACHE_INVALIDになることを確認した。D1とD5を明示取得して状態・FWを記録後、DATA_REFRESH→NF55_DATETIME?／VOUT12?／IOUT12?／BATT_VOLT?→破棄件数確認を10回実行した。最後にTEST_ENDと自己診断・SD・破棄件数・通信状態を確認した。

全要求は前応答受信後150ms以上空けた。ATE送信開始間隔の実測最短は171.5663ms。NF55Gへの実コマンドはD1、D5、D0×10だけで、Queryからの追加Refreshはなかった。SC／SET／CLEAR／BC／SS／FU、電源・バッテリ・負荷の操作は行っていない。

## D0の受信時間

単位はms。ACKと完全フレームの時刻はPicoのRAM Loggerが記録したticks_msから算出した。Transaction時間はPicoが返すelapsed_msであり、ATEのPC往復時間とは異なる。

| 回 | Command送信→ACK受信 | ACK受信→完全応答受信 | Transaction全体 |
|---:|---:|---:|---:|
| 1 | 7 | 181 | 194 |
| 2 | 5 | 182 | 195 |
| 3 | 7 | 180 | 194 |
| 4 | 6 | 181 | 195 |
| 5 | 6 | 181 | 195 |
| 6 | 5 | 182 | 195 |
| 7 | 6 | 181 | 194 |
| 8 | 6 | 180 | 194 |
| 9 | 7 | 180 | 194 |
| 10 | 7 | 180 | 195 |

ACK後の平均は180.8ms、最大182ms、300msに対する今回観測上の最小余裕は118ms。応答DATAは毎回327文字、全10回Protocol OK、ambiguous=False、command retry=0、response retry=0だった。

これらはソフトウェアの受信処理・記録時刻であり、線上の波形測定ではない。製品出力値の外部計測や製品PASS／FAIL判定は含まない。

## 保存と終了状態

| 項目 | 結果 |
|---|---|
| SD原本 | `/sd/BANK_A/20261111_111513_T000004.csv` |
| 試行 | T000004、TRIAL_START／TRIAL_END_REQUEST各1件、終了区分TEST_END |
| 回収 | 256byte分割、22229byte、SD／PCのSHA-256一致 |
| CSV | データ201行＋ヘッダ、すべて14列 |
| SHA-256 | `ecf925bd724aa4f496940571a176412f2c18dc8e5b16906811c8cf8febe7d86b` |
| フレーム | D1／D5／D0の送受信24フレームすべてBCC一致 |
| 試験終了時 | TEST_LOGGER=OK、TEST_LOG_DROP=OK、累積破棄0、SD正常、通信IDLE |
| 回収後 | 通常起動へ戻し、ID／通信IDLE／SD／自己診断正常・破棄0を再確認。COM6／COM20解放済み |

## 残る確認

今回確認できた範囲は、現在のS1.13・PS_ON=1／BATT_ON=0・逐次ATE要求の正常系10回である。意図的な300ms超過・通信破損・EB競合、長時間連続、他FW／他負荷／充放電状態、量産Timing全般は未検証。境界・異常系はHost／Mockの証拠と区別する。

OI-02には配置と今回の正常系結果を追記し、残条件の確認を残してOpenを維持する。OI-01、OI-03、初期ATE無応答の原因およびその他Issueは今回解決した扱いにしない。

## 証跡

- [開始時のATE確認](hardware_20261111_111224/preflight.json)、[配置前の25ファイル台帳](hardware_20261111_111224/inventory.json)、[退避config](hardware_20261111_111224/backup/src/config.py)
- [配置hashと結果](hardware_20261111_111224/deployment.json)、[config差分](hardware_20261111_111224/config_diff.txt)、[通常起動後の診断](hardware_20261111_111224/after_deployment_preflight.json)
- [ATE全送受信・時間](hardware_20261111_111224/ate_sequence.json)
- [CSV回収・BCC・Transaction・時間解析](hardware_20261111_111224/csv_analysis.json)、[回収CSV](hardware_20261111_111224/20261111_111513_T000004.csv)
- [ATE試験スクリプト](hardware_20261111_111224/run_d0_test.py)、[分割回収・解析スクリプト](hardware_20261111_111224/recover_and_analyze.py)
