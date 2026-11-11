# Test Specification / Mock NF55G Specification

2026-11-11 D1～D5時間測定: D1／D2／D3／D5各10回の通常ATE取得はすべてOK・再送0、ACK後完全応答平均14.0／22.0／18.6／58.9ms、最大15／23／34／74ms。D4は再送なしのRAM観測で10回、平均116.0ms・最大133ms、全回で現行100ms超過。D4通常Transaction成功とは区別し、Cache非採用・製品用T2／ソース変更なし。全50標本・102フレームBCC、CSV hash・14列と別計算一致、破棄0・通常待受復帰済み。長時間・全動作状態・原因の確定は未実施。[測定結果と方式](Spec_Review_20261111/D1_D5_Timing_20261111_112941/Timing_Result_Rev0.md)。

2026-11-11 D0 T2=300ms実機追記: configのみ配置・hash確認後、S1.13／PS_ON=1／BATT_ON=0でD0正常系10回がOK、ACK後完全応答180～182ms、再送0。DATA327文字、CSV全14列・BCC・SD／PC hash一致、破棄0、通常待受復帰済み。実機の境界・EB競合・異常系と量産全条件は未確認。下記のD0未配置記述は実装時点の履歴。[実機結果](Spec_Review_20261111/Hardware_D0_T2_300ms_Result_20261111.md)。

## 2026-11-11 D0 T2の300ms化

ユーザー指定によりD0のT2だけ通信r2事前確認版p.17／28の300msを採用。tests/test_read_cache_integration.pyの送信契約を300msへ更新し、3件の境界・異常系テストを追加した。

- 有効ACKを7ms遅延させ、ACK後299／300msの完全D0応答を再送なしで受理し、DATAのみVALIDにする。
- 初回無応答後の最終試行でACK後301msとなる応答は採用せず、RESP_TIMEOUT、command retry=1、response retry=0、ambiguous=True。旧DATAは復元せず、Queryから追加送信しない。
- ACK後250msのEBを独立ACKし、元の300ms期限を延長しない。再送を含む仮想時計602msで最終RESP_TIMEOUTとし、STATUS／INFOへ昇格しない。

関連29件成功、全Host／Mock287件成功（4.797秒）。Mockのフレームは仮想時刻にまとめて到着するため、実UARTの送出時間・受信処理負荷の保証ではない。Pico配置と実機Timingは未実施。詳細は[変更・検証記録](Spec_Review_20261111/D0_T2_300ms_Implementation_20261111.md)を参照。

## 2026-11-11 再TEST_STARTの試行分離

Host／Mock284件成功（従来273件＋再START関連11件）。tests/test_trial_restart.pyで、同一秒3試行の実ファイル分離、QR／S/N非継承、前試行の部分QR受信破棄、全Cache失効、SC→D0→Query→10秒→再START、再START時のNF55G無送信、通信中・drain中・close guardの延期、SDなし／close異常時の履歴、CONT競合拒否、8件RAM履歴上限、再mount後の採番、旧／新形式のBANK容量集計・循環対象を確認する。既存QR命名テストの期待値は試行ID付きへ更新し、同名rename衝突で原本と新規ログの保持を継続検証する。

修正版の実機配置は未実施。実機では修正版配置hashを照合し、既存のSC→DATA_REFRESH→Query→10秒→再STARTと3回連続STARTを確認する。期待値は再START=OK、別CSV、旧DATA Query=ERR:CACHE_INVALID。新DATAはATEの明示Refresh後に取得する。保存異常・QR実入力・通信TimingはHost結果だけで合格としない。SSは今回対象外。[実装記録](Test_Interruption_20261111/Implementation_20261111.md)。

2026-11-10 SL通常値実機結果: LIFE_SET_123→D0 RAW07B／12.3％、元値RAW000を明示書戻し→D0 RAW000／0.0％。SL2回は正常応答DATA0文字・46ms・cmd/rsp retry0。各SL後のDATA無効化と明示Refresh、STATUS／INFO維持を確認。OFF期間は元に戻らない実測を記録。CSV91行14列・SD/PC SHA-256一致、終了時自己診断正常・drop0。通常値1点のみ、範囲外・保持・外部動作は未確認。直下の未送信記述は準備時点の履歴。[SL実機記録](Life_Set_Hardware_Test_20261110.md)。

2026-11-10 SL実機準備: Host／Mock273件再確認成功（2.496秒）。COM6へSL用3ファイルを配置、24ソースcompile・hash一致。COM20でD0元値RAW000／BATT_DEG_TOTAL?=0.0とOFF期間を退避し、CSVのSD/PC SHA-256一致を確認。SL自体は物理接続条件の確認待ちで未送信。通常値・復元の合格とは扱わない。[SL準備記録](Life_Set_Hardware_Test_20261110.md)。

2026-11-10追加試験計画（未実施）: QR／7355共通USB下位RP2350-USB-Cの電源・UART単体、QR完全一致、7355単体取得、USBハブ共存、治具PIO双方向UART、ATE／NF55G／Logger併用、取得と書込みの工程分離を順に確認する。遅延応答・重複・取消・切断・再起動・overflow・旧値不採用を含める。[開発準備資料](USB_Host_SubMCU_Integration_Plan_20261110.md)の§7に準備物・確認点・証跡を記載。正式通信仕様確定後にCode／Testを追加し、既存Host／Mock合格を新構成の実機合格に転用しない。

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。 ただしD0のT2のみ、2026-11-11ユーザー指定により通信r2事前確認版p.17／28の300msを採用。r2の他項目は一括採用しない。
Revision: Rev.1-draft

## Goal

2026-11-10 ATE終端変更: CR／LF／CRLF各終端でD0要求が1回だけ実行されること、定期CR単独で応答・受信待ち状態が残らず次の要求が正常なこと、分割CRLF・空行混在・Queue上限・ASCII／FRAME／長さ異常から各終端で復帰することをHost／Mockで確認する。応答はCRLFを維持する。
Before real NF55G connection, verify parser, protocol, decoder, cache, command integration and safety rules on host PC.

## Test levels
T0 Parser
T1 Frame/BCC
T2 Protocol state machine
T3 Decoder
T4 Cache
T5 Command integration
T6 Mock NF55G end-to-end
T7 Safety
T8 Pico hardware
T9 Real NF55G HIL

T0-T7 must pass before HIL.

## Current execution boundary as of 2026-09-07
Desktop Codex has completed the currently available pre-NF55G checks:
- Host T0-T7 baseline: 91 tests OK.
- Pico 2 RTC REPL HIL: DS3231 I2C0 GP20/GP21 address `0x68`, check/read OK.
- Pico 2 SD REPL HIL: mount, CSV write/readback, logger queue path, 2000-record load, card removal detection, and reinsert recovery OK.
- Pico 2 RS232C 2ch REPL HIL: CH0 GP0/GP1 115200 bps 8N1 loopback OK; CH1 GP4/GP5 38400 bps 8E1 loopback OK; 100-frame stress OK.
- Host-testable hardware/transport skeletons are present for ATE UART, NF55G UART, diagnostics, parser routing, and bootstrap.

VSC+Codex must continue from this boundary:
- Re-run host T0-T7 baseline after `git pull`.
- Decide final firmware placement/build/flash path.
- Re-run RTC/SD/UART checks through final fixture firmware, not only REPL HIL scripts.
- Keep Real NF55G disconnected until final firmware smoke and safety checklist are reviewed.

## T8 hardware pre-check
- Confirm ADA-5703 PiCowbell GP4/GP5 are physically isolated before starting final fixture debug.
- GP4/GP5 must be dedicated to Pico-2CH-RS232 NF55G UART1. Disabling the PiCowbell RTC in software is not sufficient.
- Confirm ADA-5703 SD operation uses only GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI after GP4/GP5 isolation.
- Reference: `docs/Open_Issues.md` HW-01.

## r1に基づくOFF期間データの実機確認

- r1 §13.5.1に従い、PS_OFF期間中のOFF期間データ更新を確認する。PS_ON中も継続更新されることを前提にしない。
- D0内OFF_PERIODとD2の対応を、取得時刻差を考慮して確認する。個別Queryでは自動Refreshしない。
- GET DATA2後のSET LIFEによるBATT_DEG以外のクリアと、途中のAC OFF/PS_OFFによる例外、バッテリ異常ではクリアされない条件を実NF55Gで確認する。
- これは製品側挙動のHIL確認項目。既存Host/Mockの合格を代替証拠にしない。FU禁止および既存の実機接続Gateは維持する。

## Required tests
### Runtime integration (2026-09-10)

`tests/test_runtime_integration.py` adds 31 tests; total Host/Mock count is 136.
Coverage: Pico-style ticks wrap, deadline edges, EB during ACK/response/retry/idle,
bounded buffers, UART errors/short writes, CRLF ATE receive/partial transmit,
SD scheduling/deferred flush/fault recovery, RTC CSV names and filesystem readback.
See `Runtime_Integration.md` for evidence and remaining real timing/SD HIL requirements.

### D0/D1/D5 common command path (2026-11-07)

`tests/test_read_cache_integration.py` covers the Host/Mock path through FixtureApp,
parser, dispatcher, protocol, decoder, and cache:
- D0/D1/D5 command IDs, empty DATA, D0=300ms/327 chars（2026-11-11改訂）, D1=100ms/15 chars, and D5=100ms/100 chars.
- D0 decoder validates TIME as ASCII HEX, keeps embedded STATUS/INFO raw-only, and populates only DATA Cache.
- All 43 DATA, 37 STATUS, and 26 INFO queries read cache without additional NF55G transmission.
- D0 protocol/decode failure leaves DATA INVALID; OI-03 product-side CHARGE_END behavior remains unresolved and is not emulated by Host code.
- All 37 STATUS and 26 INFO queries; flags 0/1, decimal values, leading-zero text.
- Invalidation before transmission; no invalid-query TX or automatic Refresh.
- No unrelated cache updates; missing hardware invalidates the requested target.
- Payload rejection without cache mutation/transmission; reserved fields remain unsupported.
- Decode failure/partial dictionary, NAK, timeout, BCC, wrong CMD/length, HWE, UART OSError.
- Response retry recovery with plain NAK and separate retry counters.
- Control invalidation followed by invalid Query; FW_UPDATE still has no NF55G TX.

Host/Mock total: 105 tests pass (14 added). This does not complete EB, scheduler,
Pico clock, SD integration, or final-firmware HIL gates.

### D2_REFRESH read path (2026-11-07)

`tests/test_read_cache_integration.py` covers the D2 path through FixtureApp,
dispatcher, protocol, decoder, and cache:
- D2 command ID, empty DATA, T2=100ms, exact 30-character response.
- D2 Cache invalidation before transmit and validation only after complete Decode.
- Successful D2 invalidates DATA per Cache_Master; unrelated STATUS/INFO remain unchanged.
- Ambiguous and malformed-response paths leave D2 INVALID and invalidate DATA when the D2 transaction may have completed.
- No D2 ATE individual-Query command is defined or inferred by this implementation.

Product HIL must execute D2 only through the supported `D2_REFRESH` entry after
the tested firmware is deployed. r1 says OFF_PERIOD is updated during PS_OFF;
compare against D0 only with acquisition-time separation recorded and OI-03
resolved by the responsible design authority. Pico does not judge returned
values or product PASS/FAIL.

### D3_REFRESH and D4_MAINT_READ

`tests/test_read_cache_integration.py` covers the documented D3/D4 read routes:
- D3 command, empty DATA, T2=200ms, exact 21-character response; D4 command, empty DATA, T2=100ms, exact 212-character response.
- ATE parser/dispatcher routing, target Cache invalidation before transaction, full Decode before validation, and DATA invalidation on success.
- Decode failure leaves the target Cache INVALID; ambiguous transaction failure leaves both the target and DATA Cache INVALID.
- No individual D3/D4 Query names are defined or inferred. These reads have LIFE_CALC/AC_FAIL_COUNT clear side effects and must only be issued explicitly.

Pico deployment and product HIL remain required. Protocol success does not confirm
product behavior or test PASS/FAIL.

### CLOCK_SYNC and TIME numeric encoding (2026-11-07)

Host/Mock tests cover decimal ATE datetime to six ASCII HEX SC fields, invalid
input with no transmission, zero-length SC response, ambiguous invalidation,
and D0/D4 TIME field conversion back to decimal. Hardware SC/D2 and time
retention remain unverified. SC can affect AC OFF time calculations; select
the test time with the operator and do not infer acceptance from the Pico RTC.

### Protocol
- normal ACK/response/ACK
- NAK30-36 then one command retry recovery
- second NAK final error
- ACK timeout recovery/final
- response timeout recovery/final
- response BCC NG -> Pico plain NAK -> NF55 response retry
- command retry count independent from response retry count
- CME/PME/SQE/HWE/MCM/FUE
- wrong STX/CMD/length/ETX/BCC
- partial frame
- EB while idle
- EB while waiting response without resetting T2 deadline

### Decoder
- D0 327 chars
- D1 15
- D2 30
- D3 21
- D4 212
- D5 100
- BC 30
- AR 140
- EL/OL 82
- FD 64 ASCII HEX
- signed values
- scale mV->V, mA->A, 0.1h, 0.1%

### Cache
- power-on invalid
- refresh start invalid
- success valid
- failure invalid
- invalid query does not transmit NF55G
- D0 does not update STATUS or INFO
- control invalidation matrix
- ambiguous invalidation

### Safety
- FW_UPDATE -> ERR:FU_DISABLED and NF55 TX count 0
- no automatic D0/D1 after control command
- Pico never converts product state to PASS/FAIL
- logger does not block protocol

### SD real-hardware debug
Run as a separate debug/HIL check after SD hardware arrives. Do not treat host
`MemorySDSink` tests as completion of these items.
- Mount
- CSV creation
- Write
- Flush
- Close
- Continuous logging
- Card removal
- Write error
- Reinitialization

NF55 RAWの`raw_ascii`はRAM Queueの書出し時に生成する。ASCII印字可能文字、
制御文字・非ASCII、バックスラッシュ、CSVのカンマ・引用符、および変換後に
通信がbusyになった場合の書込み待避をHost/Mockで検証する。`raw_hex`は変更しない。

Current SD status:
- PASS: mount, CSV creation, write, flush, close, continuous/logger queue logging, 2000-record load, card removal detection, reinsert/remount recovery.
- INCONCLUSIVE: forced write-error through an already-open MicroPython file did not surface a logger-visible error.
- VSC+Codex remaining item: define a lower-level write-error fault-injection method and verify SD reinitialization after confirmed write error.

### RTC real-hardware debug
- I2C scan on I2C0 GP20/GP21.
- DS3231 check/read.
- DS3231 set/readback.
- Backup battery retention after power cycle.
- Re-run after final firmware image/stack changes.

Current RTC status:
- PASS: I2C scan `0x68`, read/write, OSF clear, one power-cycle backup retention check, and 2026-09-07 readback.
- VSC+Codex remaining item: final firmware image rerun; do not close OI-13 without human confirmation.

### UART / RS232C 2ch real-hardware debug
- UART0 / CH0 init: GP0=TX, GP1=RX, 115200 bps, 8N1.
- UART1 / CH1 init: GP4=TX, GP5=RX, 38400 bps, 8E1.
- RS232C-side TX/RX loopback for CH0.
- RS232C-side TX/RX loopback for CH1.
- Channel independence / crosstalk check.
- Multi-frame stress check.
- Re-run after final firmware image/stack changes.

Current UART status:
- PASS: CH0 and CH1 REPL HIL loopback, 256-byte pattern, no crosstalk, 100-frame stress.
- LIMIT OBSERVED: 512-byte single-write REPL HIL attempt was partially received; treat as a MicroPython/UART buffering limit observation and keep production protocol handling byte/packet oriented.
- VSC+Codex remaining item: final firmware transport/scheduler rerun.

## T9 Real NF55G HIL entry gate
Do not connect or command a real NF55G until all are true:
- Desktop Codex changes are committed/pushed and VSC+Codex worktree is clean after pull.
- Host T0-T7 baseline passes in VSC+Codex.
- Final firmware image/build path is selected and recorded.
- RTC/SD/UART smoke passes through final firmware.
- ADA-5703 GP4/GP5 final physical isolation method and inspection record are documented for HW-01.
- Real NF55G HIL checklist separates read-only smoke from control command testing.
- `FW_UPDATE` / `FU` blocking path is verified before any NF55G control command sequence.

## Mock NF55G
Provide:
- MockUART
- FakeClock
- ResponseFactory
- Scenario engine
- stateful NF55 simulation for integration tests

Mock is a Pico test peer, not the authoritative product specification.


## 2026-09-10: Chat CMD0 diagnostic handoff validated

Corrected pre-mount diagnostic contamination: preserve first baseline mount failure, then probe only an unmounted CMD0 failure, without auto-remount. Bounded repeated-CMD0 method; actual regression tests replace synthetic assertions. Host/Mock 143 passed; Pico warm CMD0 10/10 idle responses, SD remount and existing 65-line CSV readback passed. Temporary diagnostic boot deployed for cold-power evidence; root cause unresolved. See [handoff validation](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: Verification-method handoff

Updated verify_sd_diagnostics.py to execute diagnostic regressions; aligned instructions to current 400 kHz baseline. Added simulated SPI constructor/command coverage for idle clocks, exact CMD0 frame, error preservation and timeout. Diagnostic 5 passed; full Host/Mock 144 passed. No Pico/runtime changes; see [verification handoff](SD_CMD0_Chat_Handoff_Validation.md).


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

## QR機能の受入観点（2026-09-18、仕様確定後に実装）
以下は将来の試験要求であり、既存テストの合格はQR機能の動作確認を意味しない。
- ATEの読取開始前には読取結果を新しい有効Cacheとして取り込まない。
- Pico専用読取開始とQR受信ではNF55Gへの送信が発生せず、読取完了後にCacheを利用できる。
- 後続の明示ATE指示により、確定したフィールド/コマンド対応でNF55Gへ書き込む。FUは送信しない。
- ログ名が確定したQR Cacheと対応し、別製品の情報を再利用しない。
- timeout、不正/部分受信、再読取、製品交換、未読時のログ開始、ファイル名重複の試験はOI-14/OI-23の回答に基づいて具体化する。
- Host Unit/Mock NF55Gに加え、実リーダ・USBホスト・PicoによるHILを実施する。

### 工程別の追加受入観点（未実装）
- 読取後に原文を取得でき、解析後に版数・製造年・製造週・製造号機等をATEへ返せる。
- 桁数・文字種・範囲の各不正を検出し、部分解析値をVALIDにせず、不正値を書込みに使用しない。
- QR_SCAN/QR_GET/QR_PARSE/QR_DATAだけではNF55G書込みが発生しない。
- 有効な解析値の変換結果が確定したNF55G書込み形式に一致する。
- 必要時の明示READと照合が一致/不一致を正しく扱い、自動Refreshも製品PASS/FAIL判定も行わない。
- QR原文・解析値・書込み結果をCSVから追跡でき、各工程異常が確定したエラーコードでATEに返る。
- 再実行・製品交換時に古い解析値や読出し値が混入しない。ログ待ちでNF55G通信Timingを阻害しない。
具体的な試験データと期待値はOI-23の確定後にCodeと同時追加する。

### QRフィールド長の受入観点（2026-09-18追加、未実装）
- 品名8桁、品目コード14桁、REV3桁、製造年2桁、製造週2桁、製造号機6桁を桁数検証の基準とする。項目合計35桁を、区切り・終端を含む受信文字列全長とはみなさない。
- レイアウト確定後、各フィールドの規定長と1桁不足/超過を検証する。規定長のみでは文字種・範囲を含む全体の妥当性合格としない。
- 文字種、切出し位置、空白埋め、文字コードは未確定のため、推測した実行テストやパーサを追加しない。

### QR CacheとSSの連携（詳細確定後に実装）
保存Cache名とフィールド対応の決定後、ATEの明示指示によりQR解析値がSS DATAへ正しく変換されること、読取だけではSSが送信されないこと、SS後の既存DATA/INFO無効化規則が維持されることを検証する。

### SS書込み項目の受入観点（詳細確定後に実装）
- UNIT/ADU/BBUのREV・LOT・SERIALの9項目について確定した値の取得元・変換・配置を検証する。
- QR REV3桁からUNIT_REV4桁への変換は人間が確認した規則で検証し、未確定の末尾文字やゼロ値を補完しない。
- 画面のGET値を既定書込値としない。FW_REVISIONを今回のQR書込み対象に含めない。

- 生産LOT・生産年月・S/N情報の書込み対象範囲がUNIT_REV～BBU_SRLの9項目であることを確認する。製造週と生産月の関係は未確定のため、週から月への推測変換を試験期待値にしない。

### FW_REVISION照合（詳細確定後に実装）
- 明示INFO_REFRESH後のFW_REV?読出し値をFW書き込み仕様書のREVSIONと比較し、確定した比較規則で一致/不一致を検証する。
- 比較元仕様書・版・期待値と照合担当は未確定。表示例S1.10を期待値として固定しない。
- FW_REVISION照合によるSS書込み・FU送信・Queryからの自動Refreshを行わない。Cache INVALID時の既存エラーとRefresh失敗を扱い、古い値で照合成功としない。

- QRのREVを製品REVとしてUNIT_REVへ対応させ、FW_REVISIONの期待値として使用しないことを検証する。3桁から4桁への格納方法は未確定のため推測しない。

## 2026-09-26 QR単独試作のHost検証
tests/test_qr_reader.pyで固定位置・先頭ゼロ、全分割境界、開始前/2件目破棄、超過/不足/文字種異常、CRLF不正、期限切れ、再開始INVALID、busy/cancel/Query、FU禁止とハイフン方針を検証する。
上記の「文字種・切出し位置未確定」は当時の記録。今回ユーザー指定で順序/35文字/英数字とハイフンが確定し、この範囲の試作を許可された。実機試験の合格とは別。

2026-09-26: PIOリングwrap、満杯時の破棄、フレーム異常時の破棄をHostで3件追加し全159件合格。COM14でPIO初期化・待機Highを確認。実際のHID QR→ATE受付→REPL表示は未確認。

2026-09-26 QR試験: ATE応答後のbytearray item deletion TypeErrorをスライス再代入で修正。Host159件合格、Pico実機上のMockポートでrun()の2byte分割応答完了を確認。ATE_PARTIAL_TX_PICO_OK。光学QR読取の成功とは別。

## USBキーボード入力のPico受信確認
COM14実測: QR_TEST READING → QR_TEST ERROR QR_LENGTH。QR_DIAG scan_bytes 4 raw_len 3 wire b'ABC\n'、QR_RX_TOTAL 4。通常USBキーボードからABC+Enterを受信し、ホストTX1→GP9 PIOの9600bps/8N1経路とLF終端検出を確認。QR_LENGTHは35文字要件に対し3文字だったための期待どおりの形式エラー。L-46Xの認識/実QR35文字読取の成功は未確認。

## QR再試験成功（COM14実測）
ATE開始後、QR_TEST READING → QR_TEST READYを確認。
原文: US250A-CGXE-009491-10101A2623000001
受信36byte = 本文35文字 + LF。QR_DIAG scan_bytes 36 raw_len 35。
分解値: 品名=US250A-C、品目コード=GXE-009491-101、製品REV=01A、製造年=26、製造週=23、製造号機=000001。
一時RAM CacheのREADYとREPL表示を確認。前回のドットを含む入力はQR_CHARで拒否され、今回の入力ではドットなしで正常完了した。入力が変わった理由は未確認で、許可文字規則は変更していない。
確認範囲はATE受付→QR経路からの受信→形式検証/分割→一時Cache/REPL表示。SS送信・CSV記録・量産Timing・全入力パターンを含むHIL完了ではない。L-46X認識が改善した要因は未特定のまま。

2026-09-26 HOST TX0診断: Host/Mock全161件合格、git diff --check合格（既存ファイルの改行警告のみ）。COM14への転送は接続不可で未完了。serial.tools.list_portsではCOM10のみ列挙、COM14は認識されていない。診断受信開始・230400bps実受信・ログ比較は未実施。Pico USB再接続後に転送から再開する。

## SD抜き差し・終了後復帰（2026-11-09）

Host／Mock: SD未認識のTEST_START後もD1取得が成功し、試験中のSD_REINITがERR:BUSYとなること。抜去検出後に再挿入しても試験中に再認識・書込みを再開しないこと。TEST_END後のATE応答と待ち要求を優先して1回だけ復帰し、失敗時の周期再試行がないこと。通信busy中の復帰は待機し、次のTEST_STARTで記録を再開すること。

実機未実施: SDなし電源投入→試験継続、記録中の抜去→通信継続、試験中の再挿入→復帰なし、TEST_END後の再認識→次回ログ作成、未挿入での終了、別カードへの交換、close／unmount失敗、既存ファイル保持、フォーマットが行われないことを確認する。ATE応答時間・NF55G通信TimingとLOG_DROP_COUNTも記録する。

## 2026-11-09 試験ログ・QR命名・最終Self Check

Host／Mock: 試験開始後のQR受信callbackから末尾6桁を取得し、実ファイルをS/N＋開始日時名へ変更すること。先頭ゼロ、未取得／不正値の日時維持、試験外／前回S/N不使用、命名衝突時の既存／新規ログ保持、再mount後のS/Nファイル容量集計を検証する。ATE要求・Query結果・拒否結果・QR原文・終了前Self Check行をCSVで確認する。SDなしでもTEST_START／TEST_ENDがOK、NF55G通信継続、最終Self Checkが装置NGを報告し、復帰成功でもTEST_LOGGER異常を保持すること。終了時の認識確認失敗とclose失敗も検証する。

実機未実施: 新QR入力との接続、開始後の光学読取り、最終S/Nファイルの存在とCSV内容、SDなし／試験中抜去／再挿入、最終Self CheckのATE表示と製品判定分離、flush／close／rename失敗、通信Timingを確認する。

2026-11-09 実機前レビュー: ATE transportで拒否したASCII／FRAME／LINE_TOO_LONGも、試験中はRECEIVE_ERRORとしてRAM記録する。保存できるのは受信層が保持したprefixであり、入力全体のRAW取得とは扱わない。Host／Mock回帰試験を追加。

2026-11-09 実機確認: 日時ログ、SD抜去時のWRITE_ERR・試験継続、再挿入中の復帰禁止、TEST_END後の復帰と異常履歴保持、次試験のログ再開を確認。D3正常（31ms・再送0）、D4はD4-TIM-01として継続。TEST_ENDの先行OKをEND_REQUESTに修正し、期限境界の部分RAW／ACK待ち異常byteも記録。Host／Mock全198件成功。詳細はReal_Hardware_Test_Log.md。

2026-11-09: D4量産不使用をユーザー指定として記録。r1 p.35に基づきCLEAR4種をParser／Builderへ接続し、CD／CL正常応答DATA0文字を検証。Host／Mockでは送信形式、T2、成功／ambiguous時のCache無効化、SQE、不正引数の無送信、異常応答へのplain NAKを試験する。実機結果はReal_Hardware_Test_Log.mdへ記録。

2026-11-09 CLEAR実機結果: POWER／BATT／ALL／LOGの4種がOK、19／19／20／19ms、再送0、BCC一致。CD後のDATA／STATUS無効化、CL後の全EL／OL無効化と96件の空ログ表現を確認。CLEAR_ALLは先行個別消去後の0維持を確認したもので、単独非ゼロ値消去は未検証。Host／Mock全203件合格。詳細・制限はReal_Hardware_Test_Log.md。

2026-11-09実機: ATE経由RTC_DATE?／RTC_TIME?とPC現在JSTによるRTC_SET_YYYYMMDD_HHMMSS・読戻しを確認。設定値との秒差0、直後PCとの差-1.260秒。RTCコマンドはPico専用でSCへ連動しない。詳細とログはReal_Hardware_Test_Log.md。今後、製品動作／出力の確認を伴う送信時はユーザーへ観測項目を伝え、実測結果を受け取る。

2026-11-09実機: LOG_CONT_START／STOPを2回確認。CONT状態、停止前の定期保存、二重開始・SD_REINITのBUSY拒否、停止時closeとQueue0、日時別ファイルでの再開始、ログ破棄0を確認。RTC要求・応答を記録し、CSVをtempへ順次コピー。長時間／100MBロールオーバーは未確認。詳細はReal_Hardware_Test_Log.md。

## 2026-11-09 次試験計画：PARAM_SET同一値書戻し（未実施）

### 選定と範囲
- 次対象は既存ATEコマンドPARAM_SET（NF SP）。r1 p.19の50文字設定DATAと、p.38のD5読出し値を使う。現行値をそのまま送り、設定通信・Cache無効化・読戻し一致を先に確認する。設定変更動作そのものの検証とは区別する。
- PARAM_RESET（RP）は初期値への変更を伴うため次段階に分離。D4は量産不使用として今回送信しない。保護しきい値・自動充電等を別値へ変更しない。

### 実機前の準備
1. SP正常応答DATA0文字の厳密検証を追加する。現行DispatcherはSC/CD/CLのみexpected_length=0であり、SPは長さ未指定。Code／Host Test／Docs／CHANGELOGを合わせ、異常DATA長・SQE・不正引数・ambiguousとCache規則を検証してから配置する。RPにも同じ原典上の0文字応答契約があるが、その対応・実機試験は別段階とする。
2. 現行Picoソースを退避して配置・全ファイルhash照合。COM20=ATE、COM14=USB保守を使用し、SD正常・通信IDLEを確認する。
3. ユーザーにAC／バッテリ／負荷／出力の現状態と電圧観測方法を確認する。出力変化の許容値は設計またはユーザーの条件を使い、Picoで製品PASS/FAILを決めない。

### 試験手順
1. *IDN?、COMM_STATUS?、SD_STATUS?、PICO_SELF_CHECK?を確認後、TEST_START。
2. INFO_REFRESH（D5）とSTATUS_REFRESH（D1）を明示実行。D5 DATA100文字・BCCを検証し、後半50文字のPARAMETERをreserve18文字も含めRAW保存する。製造情報前半50文字も保存。表示用10進Queryから送信文字列を再構成しない。
3. 読出しRAWの桁数・文字種・項目範囲を原典r1と照合し、符号化不明・範囲外等があれば送信前に停止してIssueへ記録。前値と送信候補50文字の一致を照合する。
4. 送信直前にユーザーへ「現行設定と同値のPARAM_SETを送信する。12V出力電圧、出力断・再起動の有無を監視し、結果を返してほしい」と通知し、監視準備後にPARAM_SET <取得した50文字>を1回送信する。仕様のCommand Retry最大1回は別管理し、ATEから反復送信しない。
5. Protocol結果、ACK、BCC、応答DATA0文字、T2=100ms、cmd/rsp retry、elapsed、ambiguousを保存。OKを製品動作成立とは扱わない。
6. RefreshせずFW_REV?（INFO）とPS_ON?（STATUS）がERR:CACHE_INVALIDであることを確認。NF55_DATETIME?（DATA）もINVALIDを確認するが、送信前からINVALIDの場合はVALIDからの遷移を証明したとは扱わない。
7. ユーザーから送信時の実機観測結果を受け取る。異常があれば後続操作を止め、実測値・時刻・現状態を記録する。
8. 異常がなければINFO_REFRESH／STATUS_REFRESHを明示実行し、D5後半50文字が送信前と完全一致、製造前半50文字が変わっていないこと、STATUS変化を確認する。個別QueryはCacheのみ参照する。
9. TEST_END→PICO_SELF_CHECK?／SD_STATUS?／LOG_DROP_COUNT?。SD CSVとATE送受信・設定前後RAW・ユーザー実測結果をtemp直下へ順次コピーし、hash一致を確認。アプリ稼働・通信IDLEとポート解放を確認する。

### 中断・復旧・残確認
- timeout／FRAME／BCC最終異常では実行成否不明として扱い、DATA／STATUS／INFOのINVALIDを保持。盲目的な再書込み・PARAM_RESET・製品電源切入は行わない。
- 読戻し不一致時は原本・受信値・実測を保存して原因確認。元設定の復元が必要なら、保存済みRAWと回復した通信状態を確認して別の明示操作として行う。推測で値を補完しない。
- 本試験は同一値書戻しであり、設定値の実変更・電源切入保持・保護動作・PARAM_RESETは未確認のまま。計画作成のみで実機送信・コード修正は今回行っていない。

2026-11-09 PARAM_SET実機前準備: r1 p.19のSP正常応答DATA0文字をDispatcherで厳密検証する。非空応答のplain NAK・最終FRAME異常、SQE、ACK_TIMEOUTとDATA/STATUS/INFOの無効化／保持をHost試験へ追加。今回の試験はD5の現行設定RAW50文字を同値で書き戻す。RPは別段階。

2026-11-09 PARAM_SET同値書戻し実機結果: 現行D5の設定RAW50文字をreserve込みで退避・同値送信し、SP正常応答DATA0文字、72ms、BCC一致、再送0を確認。INFO/STATUS無効化と再取得後の設定・製造情報の完全一致を確認。ユーザー報告は出力変化・瞬断・再起動なし（電圧数値未提示）。ログ3本をtemp直下へ順次コピー。Host／Mock全206件成功。設定の実変更・保持・RPは未確認。詳細はReal_Hardware_Test_Log.md。

2026-11-09 PARAM_RESET準備: r1 p.21に従いRP正常応答DATA0文字をDispatcherで厳密検証。空応答・T2=100ms、非空応答plain NAK、SQE、ACK_TIMEOUTとCache規則を回帰試験に追加。現在のD5 RAW50文字を退避→RP初期値読出し→元RAWをSPで復元→完全一致確認の順で実機試験する。RESETは全項目を数値0にする意味ではなく、電源初期値へ戻す。

## 2026-11-09 SET ERP実装・Sample併用試験準備

### Host／Mockの確認対象

- ERP_SET_1_0→SE DATA1000、ERP_SET_0_0→SE DATA0000、T2=100ms、正常応答DATA15文字。
- 成功・ACK／応答timeout・最終BCC／FRAME異常でDATA／STATUSを無効化。他Cacheは保持。SQE／PMEでCache保持。
- 応答長0／14／16文字の拒否とplain NAK、BCC応答再送とCommand Retryの分離、Command Retry上限1回。
- 不正名・余分な引数の無送信、Queryの自動Refresh禁止、SE応答からSTATUSへの昇格禁止、明示D1後のBURST?取得。
- 実行対象: tests/test_erp_commands.py（10テスト、全4コマンドをsubTestで確認）および既存Host／Mock全体。

### Sample併用の実機試験（未実施）

1. 今回の3モジュール（command_parser.py／nf55_command.py／command_dispatcher.py）を含むソースをPicoへ配置し、旧ファイル退避と読戻しhash照合を行う。配置前後のSample識別、NF55G FW版、治具版、AC／PS_ON／バッテリ／負荷条件を記録する。
2. 出力電圧、瞬断・再起動の観測方法とSampleの比較条件を確認する。製品の低消費動作を検証する場合は、設計条件に基づくPS_OFF条件と入力電力／電流測定を別途準備する。今回の手順で電源断や配線変更を自動実行しない。
3. TEST_START後、PICO_SELF_CHECK?／COMM_STATUS?／SD_STATUS?を確認。STATUS_REFRESH→BURST?／BURST_ON?／PS_OFF_CHARGE?／PS_ON?で設定前を記録。DATAが開始前からINVALIDなら無効化遷移の実証とは扱わない。
4. ERP_SET_1_0を1回要求。送信DATA1000、応答DATA15文字・BCC、elapsed、cmd/rsp retry、ambiguousを保存。直後のBURST?／PS_OFF_CHARGE?がERR:CACHE_INVALIDであることを確認する。
5. 明示STATUS_REFRESH後、BURST?=1／PS_OFF_CHARGE?=0を確認。BURST_ON?と出力電圧・入力電力／電流・瞬断／再起動の観測値をSample条件と対応づけて記録する。BURST_ONはBURST入力信号の受信状態で、仕様上バースト有無に依存しない（r1 p.30）。BURST_ON=1を実際のバースト動作成立の判定に使わず、外部測定で確認する。
6. 異常がなければERP_SET_0_0を1回要求し、DATA0000と同じ通信／Cache項目を記録。明示STATUS_REFRESH後、BURST?=0／PS_OFF_CHARGE?=0を確認して同条件で外部測定する。
7. TEST_END→PICO_SELF_CHECK?／SD_STATUS?／LOG_DROP_COUNT?。SD CSVとATE TX/RX、設定前後値、Sample比較値、操作者観測を案件のtempへ保存する。
8. 終了後の設定はBURST=0／PS_OFF_CHARGE=0となる。設定前が異なる場合の復元方法・最終設定は担当者が確認する。追加実装したERP_SET_0_1／ERP_SET_1_1でPS_OFF_CHARGE=1の保存済み元設定へ復元できる。自動復元せず、BURST／PS_OFF_CHARGEの保存値に対応するコマンドをATEが明示送信し、STATUS_REFRESH後に両設定を確認する。

timeout／最終FRAME／BCC異常では成否不明としてCache INVALIDを保持し、盲目的なATE反復要求をせず記録・状態確認を行う。設定反映と低消費動作成立、Protocol OKと製品PASSを分ける。実機結果はReal_Hardware_Test_Log.mdへ記録する。

2026-11-09 ERP全4組合せ対応: ERP_SET_0_1→SE DATA0100、ERP_SET_1_1→SE DATA1100を追加。既存ERP専用10テストを4組合せへ拡張し、送信形式・T2・D1読戻しの両設定・異常時のCache・再送分離・不正要求無送信を確認。Host／Mock全220件成功（7.416秒）。ログ: temp/erp_all_modes_host_mock_20261109_run01.log。Pico配置・Sample実機試験は未実施。

## 2026-11-09 読出し優先実装とERP同時デバッグの記録

### ユーザー指定

読出しコマンドを優先実装し、実機デバッグはERP全4種と同時に後日実施する。今回はPico配置・実機送信・Sample試験を行わない。既存ERPのHost／Mock確認済み状態と、実機未確認を区別して引き継ぐ。

### Host／Mock結果

tests/test_log_fd_read_commands.pyに13テストを追加し、全233件成功（5.717秒）。全12ブロックと全96履歴の両Query、開始番号10進→HEX、日時HEX→10進、ID FF→255、空履歴、FDアドレスとRAW64文字保持、開始前INVALID、失敗時旧値復元禁止、ブロック独立、CL後全ブロック無効化、異常長・不正HEX・日時異常・START_NO不一致、不正要求の無送信、T2・ACK／応答timeout・再送分離、HWE、未接続を確認。記録: temp/read_commands_host_mock_20261109_run01.log。

### 後日の実機デバッグ対象と順序

1. 現行Picoソース退避、配置ファイルhash照合、Sample／FW／信号・負荷条件を記録。通信IDLE、SD、自己診断を確認する。
2. TEST_START後、EL4ブロック・OL8ブロックを明示取得。各ブロックの全8件をQueryし、ATE送信・NF RAW・START_NO・日時変換・ID・T2・再送・Cache範囲を照合。読出しで履歴消去や自動CLを行わない。
3. FDはREAD-FD-01の正式IDと、読出し可能アドレス・OI-10の取扱いを担当者が確認してから実施。FD_READとFD_DATA?の64文字、次取得での置換、失敗時INVALIDを確認。FUは送信しない。
4. ERPは本書のSample手順に従い全4組合せを確認。BURST／PS_OFF_CHARGEの元値退避、明示D1読戻し、外部測定、終了時の明示復元を行う。BURST_ONだけで実動作成立を判定しない。
5. TEST_END後、最終Self Check・SD・drop count、通信IDLEを記録。SD CSV、ATE TX/RX、Sample観測、設定前後、ファイルhashを案件tempへ保存。実機結果はReal_Hardware_Test_Log.mdへ追記する。

ARは仕様確認待ちで今回未実装。BC診断開始などの制御追加、未定義Query、CL自動実行、製品PASS／FAIL判定は今回の読出し実装へ追加しない。

## 2026-11-09 項目別PARAM設定

- 通常10項目を実装。tests/test_parameter_item_commands.pyの10テストで、各項目の0／上限、10進→規定幅HEX、他項目Fと予約0、先頭ゼロ、範囲外・未変更sentinel・小数・符号・HEX・未知項目・余分な引数の拒否を確認。
- 保護5項目と未確定CHG_IR_THDの無送信拒否、INFO未取得でも自動D5なし、成功／ambiguousのDATA／STATUS／INFO無効化、SQE／PME／CMEのCache保持、応答0文字、plain NAK、Command Retry／Response Retry分離、未接続時の構文拒否、明示INFO_REFRESH後のQueryを確認。
- Host／Mock全243件成功（7.565秒）。記録: temp/parameter_items_host_mock_20261109_run01.log。Pico配置・実機設定は未実施。
- 後日実機確認では対象項目・変更値・影響と元設定復元方法を担当者と確認し、INFO_REFRESHで元値を保存してから1項目ずつ実行、D5読戻しと非対象項目の保持、外部出力観測、終了時の明示復元を記録する。INFO読戻しで電源初期値指定0が0のまま返る仕様を値の補完で変えない。
- 先の「ERPと履歴読出しのデバッグは後日まとめて実施」の記録を維持する。今回の項目別設定もHostのみ確認済みとして区別し、実機で確認済みとは扱わない。保護設定は変更せず、CHG_IR_THDはPARAM-IR-01の設計確認後に扱う。

## 2026-11-09 バッテリ診断開始・停止と結果Query

- tests/test_battery_check_commands.pyへ13テスト追加、Host／Mock全256件成功（6.585秒）。記録: temp/battery_check_host_mock_20261109_run01.log。
- BC開始1／停止0、両方応答30文字・T2=6秒、開始前BC INVALID、完全8項目のみ公開、停止後BC無効と停止応答非採用、Query無送信、MODE13／未解釈MODEの受信値公開、0データ、符号・単位変換、SQE／PME／CMEのCache保持範囲、timeout・最終FRAME・HWEの無効化、NAKと再送分離、不正引数・未接続・BUSYを検証。
- START成功はDATA／STATUS INVALID、BC VALID。BC Queryは保存結果で、STATUSのBATT_CHECK_RUN?は別Cacheのため必要なら明示STATUS_REFRESHする。D0からBCを自動生成しない。
- STOP空応答・29／31文字は拒否し、予約領域を含む不正HEXもDECODE失敗とする。Partial DecodeをBCへ保存しない。MODE取得エラーであってもProtocol OKと区別し、Picoによる製品判定・値補正を行わない。
- 実機試験は未実施。評価用BCで充電DCIR測定が動作するため、接続バッテリ・充放電・負荷・外部観測・復旧手順を確認する。AUTO_CHARGEの設定に関係なくBCが実行される仕様を踏まえ、Picoから事前CN／CF／PARAM変更を自動送信しない。
- OI-06（STOP現FW）／OI-07（MODE13詳細）はOpen継続。START処理へのSTOP割込みを想定せず、Transaction完了後の別コマンドとして扱う。ATEの応答待ち時間にはT2と規定再送を考慮する。
- 先のERP／読出しの後日デバッグ予定を保持し、BCも今回Hostのみ確認済みとして記録する。Pico配置・実機確認は別途、条件確認後に行う。

2026-11-09 BC最終回帰: 引数なし契約としてBATT_CHECK_START=／BATT_CHECK_STOP=の空追加指定もERR:UNEXPECTED_PAYLOADで送信前拒否する試験を追加。最終コードのHost／Mock全256件成功（7.088秒）。最終記録: temp/battery_check_host_mock_20261109_run02.log。

## 2026-11-09 13:12 COM14配置後の確認状態

- 先の各実装時点における「Pico配置未実施」は履歴。ユーザー指示により変更5ファイルの配置を完了し、対象25ファイルの読戻しSHA256一致、Pico上compile25件、RAM Mock31ケース成功を確認した。最終Host／Mockは256件成功のまま（製品コード追加変更なし）。
- 実ハード初期化後のローカル自己診断・RTC・SD・未取得Cache応答・不正要求拒否を確認。NF55G送信をガードした確認区間の送信試行は0。通常app.runを開始しCOM14を解放済み。
- 製品コマンドの実通信、Sample外部測定、ATE物理往復、電源再投入は今回未確認。ERP／履歴読出しをまとめて後日デバッグする予定と、FD／PARAM／BCに関する既存の条件・Open Issueを維持する。取得前CacheはINVALIDなので、実機試験では明示Refresh／取得を行う。
- 詳細: [実機記録](Real_Hardware_Test_Log.md)、[配置照合](../temp/pico_debug_deploy_20261109_run01/deployment_manifest.json)、[起動結果](../temp/pico_debug_deploy_20261109_run01/runtime_result.json)。

## 2026-11-09 COM6開発機への配置と組立後の確認引継ぎ

- COM6／unique_id=69f7d45962cfdfadへ現行25ファイルをクリーン配置し、全読戻しSHA256一致。COM14配置済みソースとも同一。MicroPython v1.27.0上のcompile25件・RAM Mock31ケース成功、製品通信未実施。
- ユーザー指示により作業範囲はPico書込みまで。RTC・SDはハード組立後に確認する。組立前の初期化応答（RTC NG／SD MOUNT_ERR）から原因・故障を断定しない。組立後はRTC_CHECK、SD_STATUS、自己診断と既定のLogger確認を行い、今回の配置確認と区別して実機記録へ追記する。
- [配置・退避・起動記録](Real_Hardware_Test_Log.md)を参照。

## 2026-11-09 寿命情報設定SL

- tests/test_life_set_commands.pyの12テストを追加。通常値0／1／123／4094／4095、先頭ゼロ、上限超過4096／65535、負数、RAW不正HEX・予約非0・小文字・長さ異常・空DATA・内部空白が指定どおり送信されることを確認。PME／SQE／CMEの無補正とCache保持、ACK／応答timeout・HWEのambiguousとDATA無効化、Command Retry最大1回・Response Retry分離・plain NAK、非空成功応答拒否、構文不正・制御文字・未接続・BUSYを検証。
- 明示D0後のBATT_DEG_TOTAL?、Query無送信、DATAのみ更新、STATUS／INFO非昇格、範囲外PME／受理後のMock読戻しを確認。模擬の応答と値は実機結果ではない。
- Host／Mock全268件成功（5.237秒）。記録: temp/life_set_20261109_run01/host_mock.log。量産使用未確定、OI-08継続。ユーザー指定により今回は実装・試験手順作成まで。Pico追加配置・Sample実送信なし。
- 後日手順: [SL範囲外書込み・読戻し・復元](Life_Set_Hardware_Test_Procedure_20261109.md)。元値退避とOFF期間データ副作用を記録し、明示読戻しで実挙動を確認する。

## 2026-11-11 再START修正版の実機正常系結果

事前提示手順で対象4ファイルを配置・hash照合。COM20でSC→D0→Query→10秒→再STARTと3試行を確認。再STARTはOK、各開始直後の旧DATA QueryはINVALID、明示Refresh後は新データ取得成功。CSV3本の試行ID・区切り理由・Transaction分離、全行14列、SD／PC hashとNFフレームBCC一致。保存診断正常・破棄0。再STARTのPC往復163.3／200.2ms。QR実入力・SS・実機保存異常系・量産Timing全般は含まない。[実機結果](Test_Interruption_20261111/Hardware_Deployment_Result_20261111.md)。

## 2026-11-11 USB SubMCU単体確認FWの受入

隔離したUSB CDC確認FW dev-20261111.1について、scripts/usb_submcu_acceptance_hil.pyでUSB serial A06FEA01012EC137とBUILD 583b3b6ba99e14bfを照合して試験する。確認項目は識別、CR／LF／CRLF、分割／連結、95文字境界、過長・不正ASCII行の拒否と復帰、空行無応答、100件連番echo、DTR切断／再接続時の部分行失効。書込み後・USB経由再起動後の各123チェック成功、Host／Mock287件成功、元Flash全2MB退避・verifyと配布UF2書込みverifyを確認した。[原文証跡・結果](USB_SubMCU_FW_Acceptance_20261111/Result.md)。物理的な電源再投入・QR／7355 Host・UART・電気保護・併用Timingは試験範囲外。この診断USB仕様を内部リンクの正式仕様へ流用しない。

## 2026-11-11 Type_C2 Host電気受入の具体化案

[Host回路条件Rev.0](USB_Host_SubMCU_Host_Circuit_Conditions_Rev0_20261111.md)のH0〜H5で、部品変更の人間確認・写真、無給電施工、1系統給電、電流保護、電圧・突入・読取時負荷、両向き、QR完全一致、後続7355共存を分けて記録する。D+=GPIO12／R12、D−=GPIO13／R11を期待配線とし、R13のD+プルアップとCC Rd／Rpを照合する。微細DB_Nの測定は必須としない。デバッグPC給電と機器用Expander5V・1A供給枠を切り替え、同時直結しない。VBUS常時直結の固定機器限定評価を、接続検出・給電制御を伴う最終Sourceの合格へ読み替えない。今回は資料照合のみで、改造・Host実機試験は未実施。

## USB SubMCU実機前準備（2026-11-11）

[QR単体Host probe仕様・段階手順](USB_SubMCU_Host_Preparation_20261111/Preparation_Rev0.md)を追加。列挙とHID原文のみ、診断はRAM／任意TX候補で正式UART仕様とは区別。欠落・破損ログを検査し、35文字一致や製品合格に昇格しない。2 Host制約USB-SUB-03を追加。既存ATE／NF55G／Cache契約は変更せず、実機書込み・施工は今回行わない。

## USB SubMCU UART版の準備完了（2026-11-11、実機未受入）

[UART診断仕様](USB_SubMCU_Host_Preparation_20261111/UART_FW_20261111/Specification_Rev0.md)と[ビルド・検証結果](USB_SubMCU_Host_Preparation_20261111/UART_FW_20261111/Result_Rev0.md)を追加。qr-uart-20261111.1は追加基板GP0／115200・8N1のTX専用。既存76byteレコードをHEXで返し、起動版・IDをUSB開始前に送出する。ログは原文取得だけでQR35文字一致・製品合格としない。Host／Mock301件とファイル検証は成功、UART実機・QR・2 Hostは未受入。ATE／NF55Gの契約と正式親子UARTは変更しない。
