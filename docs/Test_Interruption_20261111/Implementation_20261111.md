# 再TEST_STARTの前試行保存・新試行開始：実装記録

2026-11-11 / 状態: ソース修正・Host／Mock284件成功、Pico配置と正常系3試行の実機確認済み。[実機結果](Hardware_Deployment_Result_20261111.md)。以下の実機未確認記述は配置前時点であり、残範囲は実機結果を参照。

## 変更内容

受付済みTEST_STARTごとに独立した試行を開始する。試験中なら前試行のQueueを排出・flush・closeし、当該試行のS/Nがあれば命名を確定してから次試行を開始する。終了区分はNEXT_TEST_START。製品PASS/FAIL・電源瞬断・実際の中断理由は判断しない。

- `src/command_dispatcher.py`: 再STARTの保存→開始の順序と全製品Cache失効。通信中・CONT記録中はBUSY。保存が通信のため延期された場合、新試行を作らずBUSYを返す。自動再要求はしない。
- `src/logger.py`: 試行ID、完了ID、終了区分付きRAM履歴（最新8件）、保存診断保持、Queue分離。未排出・未flushがある通信延期時は旧状態を保持。保存異常時は旧試行の異常と破棄を保持し、新試行は記録不能状態で受付可能とする。
- `src/sd_sink.py`: `YYYYMMDD_HHMMSS_T000001.csv`／`SSSSSS_YYYYMMDD_HHMMSS_T000001.csv`を受理。旧形式とともに容量集計・循環処理し、mount時の最大試行番号を採番へ渡す。既存CSVへの追記・上書きはしない。
- `src/main.py`: 新試行が成立した時に旧QR受信状態をキャンセル。新CSVにもSTARTのREQUEST／RESULTを記録。前試行のQR原文は旧CSVに残り、新試行のS/Nは未取得となる。
- `tests/test_trial_restart.py`: 新規11件。`tests/test_runtime_integration.py`: 試行ID付き名と同一秒の別ファイル生成に期待値を更新し、rename衝突保護も維持。

試行番号は6桁以上の通し番号。新LoggerのRAM番号とSD両BANKの既存最大番号の大きい方へ1を加える。Pico電源断後の途中データ保持・未終了試行復旧は実装しない。既存ログがない場合の番号再利用はあり得るが、既存CSVは上書きしない。旧CSVに試行IDを追記する移行処理も行わない。

完了履歴の保持件数8は初期実装値。超過分は古い順に除去してhistory_drop_countに計上する。PICO_SELF_CHECK?のTEST_LOGGER／TEST_LOG_DROPは最新完了試行を指し、STARTで消さず、次の完了時に更新する。ID対応と複数試行履歴はlogger.last_test_id／test_historyで確認できる。専用ATE履歴Queryは追加していない。

## 検証結果

実行: `.venv/Scripts/python.exe -B -m unittest discover -s tests -q`

Host Unit／Mock NF55G: **284件成功**。実ファイルを使った同一秒3試行、各試行1つだけの識別行、QR非継承、再mount後の採番と原本保護、容量集計・BANK循環も確認した。MockではSC→D0→Query→仮想10秒→再STARTがOKとなり、旧DATAがINVALIDになり、再START／QueryからNF55Gへ追加送信しないことを確認した。

従来273件のうち、仕様変更に伴うファイル名・同一秒開始の期待値を更新。新規11件は正常分離に加え、通信busy、保存途中の通信、close時COMM_BUSY、SDなし、closeエラー、CONT競合、履歴上限を含む。単なるファイル数だけでなく、前試行の行が新CSVへ入らないことと、保存異常履歴を検証する。

## 未確認・残Issue

- 実機配置と正常系再STARTは確認済み（PC往復163.3／200.2ms）。同期保存のため待ち時間はカードに依存し、異なるSD・記録量・量産Timing全般は継続調査。通信優先ガードは維持するが、進行中の同期SD I/Oを途中でプリエンプトする実装ではない。
- 新USB下位UART経由のQR／DMM要求ID照合は未実装。今回のQR対策は現行QRReceiverの受信状態を失効する範囲。新経路の遅延応答はその結合時に試行／要求IDで対応する。
- SS開発および空シリアル時のSS拒否実装は保留。方針は維持し、OI-23のSSフィールドを推測しない。
- SD異常時はCSV作成・永続保存を保証しない。別試行のCSVに混ぜず、状態・破棄を保持する。
- TEST-SESSION-01はOpen継続。応答喪失後の再送も、現行引数なしSTARTでは新たに受付すれば別試行となる。

## 実機確認の完了と残確認

修正版配置hash照合、初回START→SC→D0→Query→10秒→再START、3回目STARTとTEST_ENDを実機確認済み。再START=OK、旧DATA Query=ERR:CACHE_INVALID、明示Refresh後の新取得、独立CSV3本、SD／PC hash一致、保存診断正常・破棄0を確認した。旧プログラムの実測は[変更前の結果](Hardware_Start_Repeat_Result_20261111.md)として保持する。

原典資料・既存証跡は変更していない。実機配置とSC／D0送信は後続の承認済み実機デバッグで実施した。結果と配置前退避は[実機結果](Hardware_Deployment_Result_20261111.md)を参照。

## 完了・継続調査の整理（2026-11-11）

完了: 再STARTの試行分離修正、関連Code／Test／Docs／CHANGELOG、Host／Mock284件、Pico配置hash照合、正常系3試行実機確認、CSV原本照合、tempへの再回収。回収先はリポジトリ内`temp/Test_Interruption_20261111/recovered_20261111/`で、tempはGit管理対象外。正本証跡は本案件内verified_20261111_095036へ保持する。

継続調査: QR実入力とS/N付き命名の実機結合、新USB下位UARTの遅延応答相関、実SD異常時の保存・復帰、カード差・記録量・量産Timing、ATE応答喪失時のSTART再送識別。SS／空シリアル拒否は後続開発へ保留。これらを未確認のまま完了扱いにせず、TEST-SESSION-01はOpenを維持する。

## コミット範囲の検証（2026-11-11）

既存の別作業（BC／ERP／SL／履歴読出し等の追加とUSB下位マイコン資料）を含めず、今回の再START対応だけをGit indexへ抽出した。indexのsrc／tests／firmwareを別フォルダへ展開してHost／Mockを実行し、226件成功。作業ツリー全体の284件成功は、既存の未コミット追加機能を含む結果であり、件数差はテスト失敗ではない。実機配置台帳は当時の作業ツリー版のhashを記録しているため、部分コミットした共有ファイルのhashと一致することを意味しない。

CSVと配置前退避は案件内.gitattributesで改行変換を無効化し、SD／Pico原本のバイト列を保持する。temp再回収は従来どおりGit対象外。既存の別作業の変更は作業ツリーに残す。
