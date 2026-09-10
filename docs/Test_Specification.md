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
