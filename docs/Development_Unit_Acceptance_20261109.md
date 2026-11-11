# 開発用Pico 2 RTC・SD受入確認 2026-11-09

関連する後続確認: [CSV列欠けの再現確認](CSV_Log_Recovery_Recheck_20261109.md)。SD原本は正常で、一括REPL回収時のPCコピー欠落と判明。ATE送信間隔0.1秒以上での再確認結果を記載。

## 対象と確認範囲

- 対象は開発用COM6、unique_id `69f7d45962cfdfad`、Raspberry Pi Pico 2 / RP2350、MicroPython v1.27.0（2025-12-09）。既存COM14機 `2d35a1e11ac125e3` とは別個体。
- ユーザーのRTC・SD装着完了報告に基づく受入確認。UF2・アプリの再配置は行わず、USB REPL経由でローカル共通Command Coreと周辺機器を確認した。ATE物理UART往復・NF55G製品通信の試験ではない。
- 初回は既存appがREPLグローバルに保持されていなかったため、二重マウントを避けraw REPLでsoft resetしてからappを1件生成した。物理電源切入とは区別する。
- 配置25ファイルのSHA-256は同日13:18のCOM6配置マニフェストと全件一致。照合時のPCソースとは22件一致し、command_dispatcher.py / command_parser.py / nf55_command.pyの3件に差分があった。今回は周辺機器受入であり、これらを上書き・同期していない。

## 確認できた事実

| 項目 | 結果 | 確認内容 |
|---|---|---|
| Pico 2識別・内部ファイル | 正常 | 固有ID・MicroPython版・配置25ファイルを取得。既存機と区別。 |
| RTC認識 | 正常 | I2C0 GP20 / GP21、0x68を検出。初期日時20000101_000426から2秒進行。 |
| RTC時刻設定・読戻し | 正常 | PC日本時間20261109_165650を指定し、読戻し同値、2.1秒待機後20261109_165652。RTC_CHECK=OK。 |
| RTC停止履歴 | 記録・解除 | 設定前status=0x88、設定後0x08。OSFが解除されたことを確認。長期精度・電池保持の証明とは別。 |
| SD初回認識 | マウント異常 | CARD_INITを通過しVFS_MOUNTでOSError(19)、MOUNT_ERR。先頭セクタのbytes3..10はEXFAT。既存FAT用実装ではマウント不可。 |
| SD初期化 | ユーザー許可後に実施 | 「現在のSDカードのFAT32初期化を許可する（全データ消去）」を受領。固有ID・241745920セクタ・EXFAT署名・未マウント・試験停止を再照合してVfsFat.mkfsを実行。約97.9秒で完了。 |
| SDマウント | 正常 | 初期化後SD_REINIT=OK、SD_STATUS=OK、mount_stage=READY。ファイルシステム容量123758739456byte。フォーマット対象は本開発機のカードのみ。 |
| 試験ログ開始・終了 | 正常 | TEST_START / TEST_END=OK。終了後active=False、test_running=False、Queue空。 |
| 試験中の再初期化拒否 | 正常 | SD_REINIT=ERR:BUSY。 |
| SD書込み・読戻し | 正常 | 専用マーカー64件を各1回読戻し。CSV全73データ行、5177byte。 |
| 再マウント後の保持 | 正常 | 終了後service_recoveryで再認識しCSV全内容・SHA-256一致。電源断保持とは別。 |
| 最終試験自己診断 | 正常 | ATE_UART / NF55_UART / RTC / LOGGER / TEST_LOGGER / TEST_LOG_DROPがOK。UART項目はオブジェクトの存在確認であり実配線往復ではない。 |
| ログ破棄 | 0件 | 累積0件、その試験0件。 |
| NF55G送信 | 送信指令なし | RTC・ログ試験中はUART writeをガードし試行0。TransactionはNone。CSVにNF55カテゴリの記録なし。FUを含む製品コマンドは送信していない。 |

SD原容量は241745920×512=123773911040byte（約124GB）。初期化前先頭512byteはPCへ保存したが、全カードのデータバックアップではない。初期化はユーザーの全データ消去許可に基づく。

試験CSV: `/sd/BANK_A/20261109_170035.csv`。PC回収後SHA-256 `204666d0fa7ecbbfc8f3c8427534b76cf92c382b1ddcf8a6031100d7d9a17bf2` が再マウント前後の実機値と一致。

## 電源切入確認と残事項

ユーザーが開発機のみUSBを含む全給電を約30秒外し、再接続したと2回報告。各回とも同一固有IDを照合し、boot時のstartup_sd_diagnosticと保存CSVを取得した。結果は次のとおり。

| 回 | RTC読出しと停止履歴 | SD起動とログ保持 |
|---|---|---|
| 1回目 | PC時刻2026-11-09 17:03頃、RTC=20000101_000028→000029、status=0x88。初期日時へ戻った。 | 起動329msでREADY、SD OK、保存CSVの5177byteとSHA-256一致。 |
| 2回目 | 時刻を20261109_170426へ再設定・読戻し後に再試験。PC時刻はcold.json参照、RTC=20000101_000013→000014、status=0x88。再度初期日時へ戻った。 | 起動543msでREADY、SD OK、同じCSVのサイズ・SHA-256一致。 |

再設定時にDS3231制御0x0E=0x1Cを読出し、EOSC(bit7)=0を確認。保存済みDS3231データシートp.13では発振有効の条件である。制御値の変更は行わず、時刻設定でOSFを解除してstatus=0x08となること、2.1秒後の進行を確認した。その後の2回目電源断でもOSFが再セットされた。

総合受入はRTC保持のため保留。SDの初期化・基本記録・2回の冷間起動・ログ保持は正常。RTCの通電中I2C通信・時刻設定・進行は正常だが、電源断中の保持は2回とも不成立（DEV-RTC-01）。RTC_CHECK / PICO_SELF_CHECKのRTC=OKはアクセスと暦の確認であり、OSFや電池保持を検証する実装ではないため、これだけで保持合格としない。

未確認の原因候補はバックアップ電池の装着・絶縁・極性・接触・電圧、VBATへの給電経路、基板状態。電池・VBATの実測値はなく、原因や部品故障を断定しない。ユーザーの「新しいRTCなので設定が必要」との回答に従って再設定したが、保持成立の証拠は得られていない。

最終は通電中の利用のため20261109_170706を再設定・読戻しし、同じ開発機のアプリ待受を再開してCOM6を解放済み。FAT32署名、SD_STATUS=OK、通信IDLE、Logger / TEST停止、破棄0を確認。時刻を再設定してもDEV-RTC-01の解決とは扱わない。

- 未確認: 長時間のRTC精度・SD記録、全容量書込み、カード抜去・再挿入、量産Timing、ATE / NF55Gの物理結合。
- 今回のexFATマウント異常を過去のCMD0問題と同一原因として扱わない。ハード故障・配線不良とは断定しない。既存Open IssueはCloseしない。
- 製品PASS / FAILを判定していない。

## 証跡

### 追加保持確認（2026-11-09 17:12 JST）

ユーザーのRTC_SET依頼で20261109_171043を設定し、OK・同値読戻し・1秒進行を確認した後、ユーザーが30秒の電源断を実施。3回目は時刻再設定やsoft resetより前にCOM6から読取り、RTC日時は20000101_000056→000057、RTC check=True、status=0x88だった。通電中アクセス・進行は正常だが、今回も日時保持は不成立。DEV-RTC-01はOpen継続、原因は未確定。SDはREADY、保存CSVのサイズ・SHA-256一致。確認後は時刻を変更せず通常起動のsoft rebootを発行してCOM6を解放した。証跡: [3回目の保持確認](../temp/dev_acceptance_20261109_run01/cold_run03.json)。

- [基板・配置情報](../temp/dev_acceptance_20261109_run01/inventory.txt)
- [初回RTC / SD確認](../temp/dev_acceptance_20261109_run01/preflight.json)
- [RTC設定・SD読取診断](../temp/dev_acceptance_20261109_run01/peripheral.json)
- [初期化結果](../temp/dev_acceptance_20261109_run01/format_result.json)
- [ログ試験結果](../temp/dev_acceptance_20261109_run01/logtest.json)
- [回収CSV](../temp/dev_acceptance_20261109_run01/20261109_170035.csv)
- [配置ソース比較](../temp/dev_acceptance_20261109_run01/source_comparison.json)
- [アプリ再開記録](../temp/dev_acceptance_20261109_run01/runtime_resume.txt)
- [電源切入1回目](../temp/dev_acceptance_20261109_run01/cold_run01.json)
- [時刻再設定・制御レジスタ](../temp/dev_acceptance_20261109_run01/rtc_config.json)
- [電源切入2回目](../temp/dev_acceptance_20261109_run01/cold.json)
- [最終状態・FAT32署名](../temp/dev_acceptance_20261109_run01/final.json)

ファームウェア実装変更なし。今回Host Unit Test / Mock NF55G Testは再実行せず、実機のRTC・SD確認を実施した。
