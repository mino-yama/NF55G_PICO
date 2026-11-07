# Test Specification / Mock NF55G Specification

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.1-draft

## Goal
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

### D1/D5 common command path (2026-09-10)

`tests/test_read_cache_integration.py` covers the Host/Mock path through FixtureApp,
parser, dispatcher, protocol, decoder, and cache:
- D1/D5 command ID, empty DATA, 100ms T2 and exact response length.
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
