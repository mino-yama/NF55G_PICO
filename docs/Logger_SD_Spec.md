# Logger / SD Card Specification

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.0

## Hardware
2026-09-10: 実SD sink・Pico SPI driver・RTCファイル名・runtime busy guardを統合。
Host/Mock検証済み、統合版の実カード・電源断・通信遅延測定は未実施。
詳細と制限は [Runtime Integration](Runtime_Integration.md) を参照。
- Adafruit ADA-5703 PiCowbell Data Logger
- microSD 32GB
- FAT32
- Known hardware issue: ADA-5703 PCF8523 RTC/I2C circuitry is physically connected to GP4/GP5, which conflicts with Pico-2CH-RS232 NF55G UART1 on GP4/GP5. See `docs/Open_Issues.md` HW-01 before using this board in the final fixture.
- Intended SD-only pin use remains GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI after the GP4/GP5 conflict is resolved by hardware action.

## Format
- CSV
- 試験filename: `YYYYMMDD_HHMMSS_T000001.csv`。当該試行のQR末尾6桁を取得できた場合は終了時に`SSSSSS_YYYYMMDD_HHMMSS_T000001.csv`へ変更する（2026-11-11更新）。連続ログは従来の日時名。
- RTC source: Pico-side DS3231

## Production

2026-11-11更新: 試験中に次のTEST_STARTを受け付けた場合も試行の区切りとする。以下の旧TEST_START～TEST_ENDのみの記述は本更新に従う。
ATE sends:
- TEST_START
- TEST_END

One production test = one CSV file.
TEST_END performs forced queue drain, flush and close.

### TEST_START再受付（2026-11-11）

- 前試行の保存終了後に新規CSVを開く。再STARTのREQUESTは旧ログに区切りの要求として残し、新ログにもREQUESTとRESULTを記録する。TRIAL_START／TRIAL_END_REQUEST行のdetailに試行IDと区切り理由を記録する。close後の保存結果はRAMに保持し、閉じたCSVへ成功行を追記しない。
- Logger.test_start自体は記録中の直接再入を拒否する。前試行のtest_end(reason='NEXT_TEST_START')と次のtest_startの順序はCommandDispatcherが管理する。SD処理は同期型で、既存TEST_ENDと同様に待機中に行う。通信検出で延期した場合は新試行を作らずERR:BUSY。実機応答時間は未測定。
- 試行IDはT＋6桁以上の通し番号。mount時に両BANKの旧／新形式ログを調べ、新形式の既存最大番号とRAM採番の大きい方に1を加える。カード上の既存ログの復旧・継続は行わず、既存ファイルは上書きしない。
- 新形式名も容量集計とBANK循環削除の対象。旧日時名・旧S/N日時名も従来どおり対象とする。任意ファイルを採用・削除しない。
- 新試行前の未所属Queueは破棄計上して消去し、新試行へ流さない。旧試行の保存不能行も旧試行の破棄件数として保持する。SD異常の再認識は再START間に割り込ませない。
- 完了履歴logger.test_historyはRAMで最新8件。ID、終了区分、ファイル名、S/N、保存状態、破棄件数を保持する。超過分は古い順に除去しhistory_drop_countに計上。last_test_idとlast_test_*は最新完了試行を指す。専用ATE履歴Query・永続化は今回追加しない。
- 製品AC_OFFで試行を分割しない。Pico電源断時の途中データ保持・復旧は保証しない。SD保存失敗時の1試行1CSVは保証できないが、別試行のファイルへの追記は行わない。

## 試験ログと最終Self Check（2026-11-09）

- 手順: TEST_START → 試験中にQR読取り・各試験操作 → TEST_END → PICO_SELF_CHECK?。コマンド表記は既存のTEST_START／TEST_ENDを維持する。
- NF55Gの送受信RAWとtransaction結果に加え、ATEの論理要求・実行結果（Query・構文エラー等を含む）、当該QR原文をRAM Queue経由で保存する。ATE RESULTは共通コアの実行結果であり、UART送信完了を意味しない。
- 開始時にDS3231の日時名でファイルを作る。開始後に取得した完全な35文字QRの末尾6桁がASCII数字の場合、先頭ゼロを保持し、終了時のflush／close後に同じBANK内でS/N＋開始日時名へ変更する。試験外のQRと前回試験のS/Nは使用しない。
- S/N未取得・不正時は日時名のまま。途中ではリネームしない。変更先が既存の場合は上書きせず日時名のログを保持し、FILE_EXISTSを装置異常として報告する。SD書込み・close失敗時にも無理にリネームしない。
- TEST_END最終段でSDの認識確認（再マウントなし）と自己診断を行う。保存可能な場合はclose前のSELF_CHECK行をCSVへ記録し、flush／close／リネーム後の最終診断をRAMのdiagnostics.last_test_self_checkへ保持する。close後の結果は同じ閉じたCSVに追記できないため、PICO_SELF_CHECK?でATEへ報告する。
- PICO_SELF_CHECK?のLOGGERは現在の状態、TEST_LOGGERは直前試験の最終保存状態、TEST_LOG_DROPはその試験の破棄有無（正常はOK、異常は破棄件数）。終了後のSD復帰が成功しても直前試験の保存異常は保持する。次のTEST_STARTでも直前完了試行の診断を保持し、次の試行完了時に更新する（2026-11-11更新）。これらは検査装置の診断であり製品PASS/FAILではない。
- SD異常時は永続ログを保証できない。保存できない記録は破棄件数で通知し、試験・通信を継続する。S/Nを含むログも従来の所有BANK・容量管理の対象とする。
- QR受信完了はFixtureApp.qr_readerのon_readyからaccept_qrへ渡す。外部の確定した受信処理からaccept_qr(raw)を呼ぶこともできる。これはRAM連携のみ。新USBホストの選定・GPIO配線・物理受信ループ・正式QR ATEコマンドは未実装で、既存のOI-23／CH9350課題を維持する。

## Evaluation
- LOG_CONT_START
- LOG_CONT_STOP
Long-running file rollover size is configurable; 100MB recommended initial value.

## Flush
Normal flush condition:
- 1 second elapsed, OR
- 32 records accumulated,
whichever occurs first.

Hard rule:
No SD file write/flush during critical NF55G protocol states.
Protocol timing has priority; log records go to RAM queue.

## Capacity / rotation
Use 90% of SD capacity.
- BANK_A 45%
- BANK_B 45%
- Reserve 10%

Ping-pong:
A fills -> B
B fills -> erase/reuse old A
repeat

Implement as directories/logical banks on one FAT32 volume, not separate partitions.


## SD抜き差し・復帰処理（2026-11-09）

- 動作中の抜去・再挿入を考慮する。認識・書込み失敗でもNF55G通信と試験操作を継続可能とし、フォーマットは一切行わない。
- 電源投入時に既存FATの認識を1回試みる。失敗状態と初回診断を保持し、試験中の再認識・再マウント・周期的な復帰は行わない。
- 試験期間はTEST_STARTからTEST_ENDまでとし、ログ開始失敗時も試験期間として管理する。SD_REINITはこの期間および連続記録中にはERR:BUSYを返し、SDへアクセスしない。NF55G通信がIDLEでも禁止する。
- 抜去をI/Oエラーとして検出した後は異常状態を保持し、再挿入だけでは書込みを再開しない。カード検出端子はなく、抜去は次のI/Oまで検出されない場合がある。未保存行はLOG_DROP_COUNTへ計上し、別カードや次の試験へ持ち越さない。
- TEST_END／LOG_CONT_STOPで保存可能なQueueを排出・flush・closeし、記録期間を終了する。その後、ATE応答の送信と待ち要求を優先し、通信待機中に再認識を1回実行する。失敗しても自動反復しない。次の試験が開始された場合は、その試験の終了後まで復帰を割り込ませない。
- 終了後の復帰は新しいログファイルを自動作成せず、次のTEST_START／LOG_CONT_STARTで記録を開始する。待機中の明示SD_REINITも利用できる。
- TEST_START／TEST_ENDは試験の受付・終了を示すOKを返す。SD異常だけを理由にERRを返して試験を停止させない。通信busy／連続ログ中はERR:BUSY。試験中の再STARTは前試行を閉じて新試行へ切り替える（2026-11-11更新）。ログ異常は最終Self Check、現在の復帰状態はSD_STATUS?で報告し、製品不良判定と区別する（②③要求により前項の初期実装から更新）。
- Host／Mock検証済み。実カード抜去・再挿入、異常close／unmountからの復帰、冷間起動、ATE応答・通信Timingは実機検証が必要。既存CMD0問題の解決を意味しない。

## SD failure
SD failure must NOT stop product test or NF55G communication.
Latched states:
- OK
- NO_CARD
- MOUNT_ERR
- OPEN_ERR
- WRITE_ERR
- FULL

ATE maintenance commands:
- SD_STATUS?
- SD_USAGE?
- LOG_DROP_COUNT?
- SD_REINIT

## Multi-sink logger
Logger architecture supports:
- SD sink
- future USB sink
- REPL/debug sink

### REPL/debug mirror (2026-11-13)

- `src/config.py`の`REPL_LOG_ENABLED`で起動時に切替える。既定値は`False`でREPL sinkを生成せず、poll／USB stdout writeを行わない。デバッグ時に一時的に`True`へ変更して配置・再起動すると、TEST_START／LOG_CONT_START後にSD sinkが受理したCSV行を同じ14列・CSV escape形式でUSB REPL/debug sinkにも出力する。開始時にはCSV headerも出力Queueへ追加する。
- REPL出力はSD書込み後に複製し、NF55G通信中・ATE処理中は送信しない。`select.poll()`の書込可能通知をtimeout 0で確認し、1回のserviceにつき最大32文字だけ送る。REPL側Queueは4096 UTF-8 byteまでとする。
- REPL未接続／非pollable、切断、Queue満杯の場合はREPLコピーを破棄する。SD記録とATE/NF55G処理は継続し、SD sinkを記録の正本とする。REPL drop数は`ReplDebugSink.drop_count`に保持し、ATEの`LOG_DROP_COUNT?`には合算しない。
- USB書込み可能poll後の1回の`sys.stdout.write()`自体がUSB実装により待つ可能性までは排除できない。Timing影響を疑う比較や通常運用では`REPL_LOG_ENABLED=False`として再起動する。57600bps変更後の量産Timingは未測定。
- USB CDCはMicroPython REPLと共有される。REPLへ接続／`Ctrl+D`を送ると`MPY: soft reboot`が発生し、実行中アプリは再起動される。Thonnyは観察専用に使い、Shellへコマンドを入力しない。NF55G Transaction中のTiming影響は未確認。

### Thonnyでの実機確認手順（2026-11-13）

1. ATE側COM19で必要な試験を終了し、`TEST_END`応答と`COMM_STATUS?`=`OK:state=IDLE`を確認する。TEST_START中の状態でThonny接続／soft rebootを行わない。
2. COM6を使用しているmpremote等の監視プロセスを終了する。Thonnyとmpremoteから同じCOM6を同時に開かない。
3. REPL表示試験時だけ`src/config.py`の`REPL_LOG_ENABLED=True`をPicoへ配置し、ThonnyでMicroPython (Raspberry Pi Pico)とCOM6を選んでShellを接続する。Shellに`MPY: soft reboot`が出た場合はMain再起動後の出力を待つ。必要時のsoft rebootはShellにフォーカスしてCtrl+Dを押す。これはMainとMicroPython状態を再起動する操作である。通常運用／Timing比較ではFalseへ戻して配置・再起動する。
4. 通常起動後、ATE側COM19で`*IDN?`により治具応答を確認する。その後、ローカルな試験であれば`TEST_START`を送り、ATE要求／応答がCSV形式でThonny Shellにも流れることを確認する。個々のATEコマンドは前応答完了後に送信する。
5. 確認後はATEから`TEST_END`を送り、`PICO_SELF_CHECK?`、`SD_STATUS?`、`LOG_DROP_COUNT?`、`COMM_STATUS?`を確認する。Thonny Shellでは入力やCtrl+C/Ctrl+Dを行わない。

2026-11-13実機: COM6へ接続したThonnyで`MPY: soft reboot`後のMain起動とREPLログ表示を確認。ATE COM19でTEST_STARTと`*IDN?`を実行し、CSVヘッダー、TRIAL_START、ATE REQUEST／RESULTがShellに表示された。NF55G Refresh／Controlは含めていない。

USB logging must be non-blocking and may drop logs rather than delay ATE/NF55G.

Priority:
1. ATE
2. complete current NF55G transaction safely
3. mandatory internal processing
4. SD logger
5. REPL/debug USB mirror and future USB logger

## Suggested CSV fields
timestamp,category,direction,cmd,event,raw_ascii,raw_hex,bcc_rx,bcc_calc,bcc_ok,cmd_retry,rsp_retry,result,detail

### NF55 RAWの可読表記

- `raw_hex`は従来どおり受信・送信バイトの正本とする。
- `raw_ascii`は印字可能なASCIIを表示し、バックスラッシュは `\\`、それ以外のバイトは `\xHH`（大文字HEX）とする。例: `025343033133` は `\x02SC\x0313`、ACK `06` は `\x06`。
- CSVの引用符やカンマは通常のCSV引用規則で保存する。過去CSVは自動変更しない。
- 通信中のトレースは従来どおりRAM Queueへの追加のみ。ASCII変換は通信が落ち着いた後の書出し時に行い、変換後にも通信状態を確認する。Pico実機の遅延・量産Timingは別途検証する。


## 2026-09-10: SD startup diagnostics

Added RAM-only first-startup SD stage/error snapshot; no automatic retry, added delay or ATE format change. Soft-boot mount passed; cold-power failure cause remains unconfirmed. Host/Mock: 138 tests passed. See [investigation](SD_Startup_Investigation.md).


## 2026-09-10: Controlled SD cold-start comparison prepared

Added opt-in startup delay / CS-before-SPI settings (normal defaults unchanged) and temporary `firmware/sd_startup_probe.py`. Pico /main.py now selects DELAY_ONLY: 500 ms wait, original CS order, one CMD0 attempt. Cold-power result pending; normal entry point must be restored after investigation. Host/Mock: 139 tests passed. See [experiment matrix](SD_Startup_Investigation.md).


## 2026-09-10: SD startup comparison completed without improvement

DELAY_AND_CS cold start: CMD0 failed: 31, CARD_INIT, elapsed 627 ms; captured before reset/reinit. Baseline, delay-only, CS-only and combined cases all exhibited the same CMD0 failure. Tested 500 ms wait and CS-before-SPI are not established fixes. Restored normal firmware/main.py to Pico /main.py, retaining diagnostic support. Root cause remains open. No Host tests rerun for hardware measurement and entry restoration; last suite 139 passed. See [full evidence](SD_Startup_Investigation.md).


## 2026-09-10: Chat CMD0 diagnostic handoff validated

Corrected pre-mount diagnostic contamination: preserve first baseline mount failure, then probe only an unmounted CMD0 failure, without auto-remount. Bounded repeated-CMD0 method; actual regression tests replace synthetic assertions. Host/Mock 143 passed; Pico warm CMD0 10/10 idle responses, SD remount and existing 65-line CSV readback passed. Temporary diagnostic boot deployed for cold-power evidence; root cause unresolved. See [handoff validation](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: CMD0_NO_PRE_FF hardware comparison prepared

Temporary Pico /main.py selects CMD0_NO_PRE_FF: only CMD0's CS-Low pre-command
FF byte is omitted. Other commands retain it. Initialization remains 400 kHz,
mode 0, 16 FF bytes with CS High, zero added wait and original CS/SPI ordering.
The driver default CMD0_PRE_DUMMY=True preserves normal behavior; only the
diagnostic entry overrides it. Startup snapshot includes cmd0_pre_dummy=False.
Post-failure probing still preserves the initial result; its CMD0 commands also
use this setting. No automatic remount or production workaround was added.

Host/Mock: 144 passed, with first-CMD0 byte sequence and failure/timeout checks
covering both pre-FF settings. Pico warm runtime smoke passed: RTC advancing,
64 CSV rows at /sd/BANK_A/20260910_114306.csv, zero drops, remount/readback,
RAM ATE CRLF and FU rejection, run/stop and zero observed NF55G TX bytes.
Evidence: temp/pico_no_ff_runtime_smoke.log and temp/pico_no_ff_warm_boot.log.
Cold-power result pending operator power-cycle; no claim of root-cause repair.
Earlier statements that this comparison was unimplemented are historical.


## 2026-09-10: RETRY_ONLY comparison prepared

Temporary diagnostic entry retains the SDCard object whose constructor failed,
via ObservedSDCard, and records the original mount error before follow-up.
PROBE_MODE=RETRY_ONLY issues one CMD0 on that same object/SPI: no SPI constructor
or init, no additional 128-clock train and no explicit retry delay. Ordinary
cmd() CS transitions and post-response FF clocks remain; "no extra clocks" does
not mean zero clocks between commands. SPI is deinitialized only after the probe.
CASE remains CMD0_NO_PRE_FF to keep the preceding trial's command bytes unchanged.
The baseline of this comparison is that preceding trial, not the original driver.

If first mount succeeds or no retained object exists, probing is skipped. No
automatic remount follows a failure. First evidence is not overwritten by a
successful follow-up. All additional probing is diagnostic, not production retry.

Host/Mock: 146 passed. New checks enforce retained-object reuse, exactly one
attempt, zero requested delay and no fallback reconstruction when object missing.
Pico warm test injected a software CMD0 error after a real 0x01 reply, confirmed
constructor-failure object retention, then obtained 0x01 from one same-SPI retry.
SD remount and existing 65-line CSV readback passed. This injected failure is NOT
a reproduced cold-power failure and does not establish a fix.
Evidence: temp/pico_retry_only_warm_injection.log; reproducible script:
scripts/pico_cmd0_retry_only_smoke.py. Warm boot evidence:
temp/pico_retry_only_warm_boot.log.

Pico /main.py and /sd_cmd0_probe.py contain the updated diagnostic module.
The next operator power-cycle must be captured before host reset/reinit; inspect
startup_sd_diagnostic and REPL global diagnostic_report, including probe_mode,
mode, attempts and results. Cold result pending; root cause remains unresolved.


## 2026-09-10: CLOCKS_ONLY comparison prepared

PROBE_MODE=CLOCKS_ONLY retains the failed card/SPI, drives CS High and writes
16 FF bytes (128 clocks), then sends one CMD0 with zero explicit delay. No SPI
constructor/init occurs before that retry; deinit is cleanup after the result.
CASE remains CMD0_NO_PRE_FF, matching RETRY_ONLY. Report includes mode, attempts,
delay_ms and extra_idle_bytes=16. First failure is retained without automatic remount.

Host/Mock: 147 passed. New test verifies CS High during all 16 writes, same SPI,
no reconstruction factory, then exactly one retry and cleanup. The warm Pico
smoke uses injected failure; cold-power evidence still requires a physical cycle.
Evidence paths: temp/pico_clocks_only_warm_injection.log and
temp/pico_clocks_only_warm_boot.log. No permanent workaround has been selected.

## QR情報によるファイル名拡張（2026-09-18、未実装）
ユーザー指定により、PicoのQR読取Cacheをログファイル名に利用する。
2026-11-09追記: ログ命名については、TEST_START後に読むQR末尾6桁、S/N＋開始日時、未取得時は日時維持をユーザー確認。上記「試験ログと最終Self Check」に共通コアの実装を記載する。QRの物理受信・正式ATE仕様とSS連携は未確定のまま。
NF55G通信中のSD write/flush禁止とRAM Queue利用は継続する。
詳細: [QR読取要件](QR_Reader_Requirements.md)。

### QR工程のCSV記録（2026-09-18追加、未実装）
QR原文・解析値・NF55G書込み結果をCSVへ記録する。異常停止・再実行をATE側から追跡できる構成とする。
列名、エラーの記録形式、製品/工程/試行の識別、CSVエスケープはOI-23で確定する。
ログはRAM Queue経由とし、NF55G通信Timingを妨げない。QR情報をファイル名に使用する既定の追加要件も維持する。

2026-11-09 実機前レビュー: ATE transportで拒否したASCII／FRAME／LINE_TOO_LONGも、試験中はRECEIVE_ERRORとしてRAM記録する。保存できるのは受信層が保持したprefixであり、入力全体のRAW取得とは扱わない。Host／Mock回帰試験を追加。

2026-11-09 実機確認: 日時ログ、SD抜去時のWRITE_ERR・試験継続、再挿入中の復帰禁止、TEST_END後の復帰と異常履歴保持、次試験のログ再開を確認。D3正常（31ms・再送0）、D4はD4-TIM-01として継続。TEST_ENDの先行OKをEND_REQUESTに修正し、期限境界の部分RAW／ACK待ち異常byteも記録。Host／Mock全198件成功。詳細はReal_Hardware_Test_Log.md。

2026-11-09実機結果: 連続ログ開始・停止・再開始をPico側RTC照会で確認。記録中の定期保存、二重開始とSD_REINITの拒否、停止後close・Queue0、CSV読戻しとtempへのコピーを確認。2本で破棄0。長時間／100MBロールオーバーの検証は含まない。

## 2026-11-11 再START実機確認

修正版配置後、SC→D0→取得→10秒→再STARTと3試行の独立CSVを確認。前2本はNEXT_TEST_START、最終TEST_END、SD／PC hash一致・全行14列・破棄0・最終保存診断正常。再STARTのPC往復163.3／200.2ms。QR命名・保存異常系・量産Timing全般の検証ではない。[実機結果](Test_Interruption_20261111/Hardware_Deployment_Result_20261111.md)。
