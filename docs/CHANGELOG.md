# CHANGELOG

## 2026-09-10 - Runtime clock, EB, ATE, and real SD integration

- Integrated shared Pico-compatible monotonic clock, bounded EB processing without Cache promotion/deadline resets, transaction exclusion, UART exception results, and protocol-level FU blocking.
- Added operator-confirmed CRLF ATE transport and cooperative scheduler, partial reply handling, RAM protocol traces, and transaction summaries.
- Added FAT CSV sink and HIL-derived SPI SD driver with CSD capacity, bounded waits, RTC filenames, owned bank rotation, deferred flush, and failure/reinit handling. Fixed host CSV CRLF corruption and deferred-flush recovery found by tests.
- Added 31 runtime Host/Mock tests; all 136 tests passed. Added `Runtime_Integration.md` and deployment entry-point candidate; updated related specifications. No Pico deployment or real NF55G communication was performed. Physical SD/firmware timing validation and Open Issues remain pending.

## 2026-09-10 - D1/D5 Refresh and Cache Query paths

- Added explicit D1/D5 read definitions and STATUS/INFO query allowlists; wired parser and FixtureApp to shared dispatcher handlers. Flags return 0/1, parameter values decimal, and manufacturing text preserves leading zeros.
- Refresh invalidates its target before communication and validates only after complete decode; invalid queries never transmit. Added HWE minimum invalidation and ambiguous UART OSError reporting with unavailable timing/retry metadata represented as None.
- Added 14 Host/Mock integration tests covering all 63 queries, failure/retry paths, invalidation, no-auto-refresh, and FU blocking. All 105 tests passed; no Pico deployment or NF55G transmission.
- Updated ATE/interface/test documentation and HIL readiness. Pico clock, EB, scheduler, real SD logger integration, and existing Open Issues remain pending.

## 2026-09-10 - Real NF55G HIL preparation

- Added `docs/NF55G_HIL_Preparation.md` with entry-gate status, wiring/firmware records, ordered firmware preparation, and an initial D1/D5 procedure for use only after the existing gates are met.
- Audited the current skeleton: missing Refresh/Query dispatch, production scheduler, Pico clock integration, EB handling, transaction re-entry/exception protection, and physical SD/RTC logger integration. Confirmed unsupported Refresh/Query responses in a host-only check; 91 passing tests do not cover these missing paths.
- Separated D0's open side-effect question, BC/control actions, AR/FD issues, and all FU prohibition from the initial read sequence. No NF55G transmission, firmware placement, specification relaxation, or Open Issue closure.
- Recorded operator confirmation of PC–Pico connection and loopback removal; FW revision remains undecided and product connection/power state is unconfirmed. Host/Mock regression: 91 tests passed; diff check passed.

## 2026-09-10 - SD initialization repeat check

- Three sequential SD mount probes and a 160-record basic I/O run passed under normal permissions on COM14; all exited 0. Logger readback: 161 lines, 160 writes, 5 flushes, 1 close, 0 drops; clean reinit OK.
- Recorded result payloads in the hardware log. No CMD0 recurrence was observed, but cold-start initialization and the original cause remain unverified. No runtime changes or Open Issue closures.

## 2026-09-10 - UART two-channel loopback verification

- Re-ran `pico_uart_hil.py --port COM14 --bytes 256 --frames 100` under normal permissions; exit 0. Both UARTs passed 256-byte exact loopback with zero crosstalk and 100 frames / 3500 bytes per channel.
- Recorded the command, raw result payload, operator-reported wiring, and limits in `docs/Real_Hardware_Test_Log.md`. A previous run's session was lost and is not used as evidence.
- No runtime/firmware changes, NF55G protocol commands, or Open Issue closures. Final-firmware HIL and the earlier SD initialization anomaly remain pending.

## 2026-09-09 - RTC/SD rerun port access

- Recorded initial COM14 access denial under both normal and elevated execution, then successful RTC scan/read after the operator released the port. User reports both RS232 channels shorted for loopback.
- Recorded an initial SD `CMD0 failed: 31`, followed by a successful mount-only probe and complete 160-record SD basic retry (161 lines, 160 writes, 5 flushes, 1 close, 0 drops, clean reinit OK). The initial SD anomaly remains unexplained; no firmware changes or Open Issue closures.
- Operator later clarified that the SD card was removed/reinserted between failure and recovery. Updated the hardware log: contact quality is a candidate, but reinsertion-related card-state changes are not ruled out.

## 2026-09-09 - Pico identity and deployment inventory

- Added `scripts/pico_inventory.py` for read-only MicroPython identity/filesystem inspection through `mpremote connect COM14 resume run`, with no automatic soft reset or peripheral initialization.
- Verified Pico 2 / RP2350, MicroPython v1.28.0, and a root containing only `/sd`; no root boot/main files or fixture source deployment were observed. SD contents and frozen modules were outside the inspection scope.
- Recorded raw output and the user's confirmation of current ADA-5703 GP4/GP5 physical disconnection in `docs/Real_Hardware_Test_Log.md`. HW-01 remains open for final inspection traceability; no NF55G commands were sent.

## 2026-09-09 - Windows development environment setup

- Added workspace VS Code settings for the local Python environment, unittest discovery, and cmd.exe terminals; added process tasks for Host/Mock tests and dependency checks. Store PowerShell still requires elevated execution in the observed tool environment; OS permissions were not changed.
- Created a local ignored `.venv` and added `requirements-dev.txt` for HIL, Word generation, and MicroPython tooling.
- Added `docs/Development_Environment.md` with cmd.exe setup commands and the current installation limitation; linked it from README.
- Initial restricted installation failed because pip ignored its package index. A subsequent user-authorized elevated installation succeeded into the local `.venv`; direct dependencies are pinned to pyserial 3.5, python-docx 1.2.0, and mpremote 1.29.0.
- Validation under normal permissions: all 91 Host/Mock tests passed, `pip check` found no conflicts, RTC/SD/UART HIL and mpremote help commands succeeded, and COM14 was enumerated. `git diff --check` passed. No hardware commands, protocol changes, or Open Issue closures were performed.

## 2026-09-07 - r1 development baseline adoption

- Adopted `reference/RW11用電源通信仕様書r1.pdf` (GVT-284454-001-00, first edition 2026/9/4) as the current baseline at user request; local SHA256 matches the existing impact review.
- Updated AGENTS.md to Rev.1, startup/handoff guidance, reference index, current Master/plan baseline references, and active issue guidance. D6 originals and historical review/test records remain available.
- Documented PS_OFF-only OFF_PERIOD updates and the corresponding real-NF55G checks. Existing ordinary wire formats and runtime code require no change from this revision; no product behavior is emulated in Pico.
- FU remains disabled, unresolved issues remain open, and the inspection discussion document remains a discussion rather than an adopted specification.
- Validation: Host Unit/Mock suite (`python -m unittest discover -s tests`) passed all 91 tests; `git diff --check` passed. Real NF55G r1 behavior remains unverified.

## 2026-09-07 - D6 to r1 specification review

- Added `docs/RW11_D6_to_R1_Impact_Review_20260907.md` with full 43-page text/image comparison, change list, implementation impact, and remaining verification.
- Added OI-22 for r1 BOOT update recovery wording/procedure confirmation; FU remains prohibited and existing issues remain open.
- No runtime, test, original-source, or baseline-rule changes. Existing host/mock suite: 91 tests passed. Real NF55G r1 behavior remains unverified.

## Rev.0 - 2026-09-01
Initial Codex handoff baseline.

Included:
- ATE command architecture
- explicit Refresh + Cache
- Data Decode master
- Cache invalidation/post-check rules
- Pico software module boundaries
- Protocol state machine
- Command Retry / Response Retry separation
- ambiguous transaction policy
- Mock NF55G and host test plan
- Logger/SD formal specification
- FU hard prohibition
- ATE priority rule
- USB CDC detailed implementation deferred
- Fixed implementation phase order in `docs/Implementation_Plan.md`
- Defined development vs production source versioning policy

Initial implementation start:
- Added `src/config.py` constants for frame bytes, timing, retry, cache names, and invalidation policy.
- Added `src/models.py` lightweight shared model classes.
- Added `src/frame.py` for NF55G frame build/parse and BCC calculation.
- Added `src/nf55_decode.py` pure decoders for D0/D1/D2/D3/D4/D5/BC/EB/EL/OL/AR/FD.
- Added `src/cache_manager.py` for power-on invalid cache state, validate/invalidate, refresh failure, and control ambiguous/success invalidation.
- Added initial host `unittest` coverage for frame/BCC, cache, and decode basics.
- Expanded decoder unit tests to cover D0/D1/D2/D3/D4/D5/BC/AR/EL/OL/FD normal lengths, wrong lengths, key numeric conversions, status bit decode, FD raw preservation, and EL/OL START_NO mismatch.
- Added comprehensive D0 Golden Data assertions covering TIME, REALTIME, OFF, LIFE_CALC, LIFE_DIAG, ACCUMULATED, MFG raw/decode, PARAM raw/decode, and STATUS raw/decode.
- Added host-side Mock NF55G with `FakeClock`, `MockUART`, `ResponseFactory`, and scenario steps for ACK, NAK33, ACK_TIMEOUT, RESP_TIMEOUT, BCC NG, PME, SQE, and HWE.
- Added `src/nf55_protocol.py` transaction state machine covering WAIT_ACK, WAIT_RESPONSE, VALIDATE_RESPONSE, COMMAND_RETRY, RESPONSE_RETRY, SUCCESS, and FAILED paths with host unit tests.
- Added control command/cache integration for CHARGE_ON, CHARGE_OFF, BACKUP_ENABLE, OUTPUT_RESTART, PARAM_SET, and related control commands, with tests for success invalidation, parser rejection, PME/SQE no-invalidation, HWE/ambiguous invalidation, and no automatic post-refresh.
- Added Logger/SD core with RAM queue, host memory SD sink, TEST_START/TEST_END, LOG_CONT_START/LOG_CONT_STOP, SD_STATUS?, SD_USAGE?, LOG_DROP_COUNT?, SD_REINIT, forced drain on TEST_END, drop counting, and no write/flush while protocol busy.
- Recorded separate SD real-hardware debug checklist for Mount, CSV creation, Write, Flush, Close, continuous logging, card removal, write error, and reinitialization.
- Added Pico-side RTC command support for RTC_DATE?, RTC_TIME?, RTC_DATETIME?, RTC_SET_YYYYMMDD_HHMMSS, and RTC_CHECK? using a DS3231 abstraction, explicitly separate from NF55G SC/CLOCK_SYNC.
- Added Pico/MicroPython `DS3231I2CDevice` access for I2C0 GP20/GP21, including BCD datetime read/write and OSF clear, with host fake-I2C tests.
- Added and consolidated AD/AR Open Issue review notes, including interim FW analysis, into OI-16 through OI-21 plus OI-04/OI-05 refinements for production FW/design confirmation.
- Added HW-01 for the ADA-5703 PiCowbell GP4/GP5 physical conflict with Pico-2CH-RS232 NF55G UART1, and noted that disabling PiCowbell RTC in software is not sufficient.
- Added a first-step real-hardware debug notice and T8 pre-check requiring ADA-5703 GP4/GP5 physical isolation before final fixture UART/SD debug.
- Recorded that 2026-09-04 Pico 2 SD/RTC real-hardware tests were performed with ADA-5703 GP4/GP5 physically isolated; HW-01 remains open for final fixture isolation/inspection traceability.
- Added `docs/Desktop_to_VSC_Migration_Plan.md` to define the Desktop Codex to VSC+Codex scope boundary, migration gate, current status, VSC start checklist, and required real-hardware records.
- Added `docs/Desktop_to_VSC_Migration_Plan.md` to `HANDOFF_MANIFEST.txt`.
- Added `reference/NF55G_VSC_Codex_Migration_Guide.md` as a supporting reference for ChatGPT -> Desktop Codex -> VSC+Codex staged migration, maintained until VSC+Codex handoff and retained as a record afterward.
- Added the VSC+Codex migration guide to `HANDOFF_MANIFEST.txt` as a supporting reference file and clarified generated migration/support notes in `reference/README_REFERENCE.md`.
- Added `scripts/pico_sd_hil.py` as a repeatable Pico 2 MicroPython SD HIL runner for SD mount, CSV write/readback, current logger queue-path verification, and clean SD reinitialization checks.
- Recorded 2026-09-07 Pico 2 SD logger queue-path verification in `docs/Real_Hardware_Test_Log.md`; host `tests.test_logger_sd` passed and Pico 2 SD queue/readback completed with 160 records, 5 flushes, 1 close, and 0 drops.
- Extended `scripts/pico_sd_hil.py` with configurable queue/load record count and an interactive card removal/reinsert mount probe; recorded a 2000-record Pico 2 SD logger load pass with 0 drops.
- Recorded Pico 2 microSD physical removal detection and post-reinsert remount/write/readback recovery; forced write-error injection remains pending.
- Recorded an inconclusive forced write-error attempt: physical removal after opening a MicroPython file did not surface a logger-visible write/flush error after either 1-record or 256-record attempts, so a lower-level fault-injection procedure is still required.
- Recorded final post-fault-attempt SD remount/write/readback recovery on Pico 2, confirming the card returned to normal operation after reinsertion.
- Re-ran Pico 2 SD removal/reinsert checks after the prior physical-removal timing was found uncertain; baseline write/readback, removed-card mount failure, post-reinsert remount, and post-reinsert logger write/readback all passed.
- Added `scripts/pico_uart_hil.py` for Pico 2 MicroPython RS232C 2ch loopback HIL checks and recorded CH0/CH1 init, 256-byte loopback, no-crosstalk, and 100-frame stress PASS results; 512-byte single-write behavior is recorded as a HIL buffering limit observation.
- Added host-testable Pico hardware/transport layer skeletons (`ate_uart.py`, `nf55_uart.py`, `diagnostic.py`, `command_parser.py`, `main.py`) plus tests for local routing, diagnostics, `FW_UPDATE` prohibition, and no-control behavior before NF55G connection.
- Added `scripts/pico_rtc_hil.py` and recorded a pre-NF55G readiness check: host tests passed, RTC/SD/UART HIL checks passed on Pico 2, and remaining work is gated on final fixture isolation evidence, final firmware path, and real NF55G availability.
- Revised Desktop-to-VSC migration and test plans for the 2026-09-07 boundary: Desktop Codex completed host/mock plus Pico 2 RTC/SD/UART REPL HIL; VSC+Codex takes over final firmware placement/build/flash, final-firmware reruns, low-level SD write-error fault injection, and Real NF55G HIL.


## 2026-09-10: Integrated Pico deployment

Deployed 23 Python files with matching SHA-256; real RTC/SD smoke, 64-row CSV readback after remount, RAM ATE CRLF/FU rejection, and scheduler run/stop passed. NF55G disconnected; observed NF55G TX zero. Device left in REPL; cold boot and physical ATE/NF55G tests pending.

Evidence and limitations: [Pico deployment](Pico_Deployment_20260910.md). Reproducible finite check: `scripts/pico_runtime_smoke.py`.


## 2026-09-10: SD startup diagnostics

Added RAM-only first-startup SD stage/error snapshot; no automatic retry, added delay or ATE format change. Soft-boot mount passed; cold-power failure cause remains unconfirmed. Host/Mock: 138 tests passed. See [investigation](SD_Startup_Investigation.md).


## 2026-09-10: Controlled SD cold-start comparison prepared

Added opt-in startup delay / CS-before-SPI settings (normal defaults unchanged) and temporary `firmware/sd_startup_probe.py`. Pico /main.py now selects DELAY_ONLY: 500 ms wait, original CS order, one CMD0 attempt. Cold-power result pending; normal entry point must be restored after investigation. Host/Mock: 139 tests passed. See [experiment matrix](SD_Startup_Investigation.md).


## 2026-09-10: DELAY_ONLY cold start failed; CS_ONLY selected

500 ms added wait with original CS/SPI order still returned CMD0 failed: 31, CARD_INIT, elapsed 625 ms. First-boot evidence captured before reset/reinit. Switched temporary Pico entry to CS_ONLY (0 ms added wait; GP17 High before SPI creation). CS_ONLY cold-power result pending. See [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: CS_ONLY cold start failed; combined condition selected

CS High before SPI creation with no added wait returned CMD0 failed: 31, CARD_INIT, elapsed 126 ms. Captured before reset/reinit. Temporary Pico entry now selects DELAY_AND_CS (500 ms wait, then CS High, then SPI creation). Combined cold-power result pending. No runtime logic change or Host test rerun for this case selection. See [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: SD startup comparison completed without improvement

DELAY_AND_CS cold start: CMD0 failed: 31, CARD_INIT, elapsed 627 ms; captured before reset/reinit. Baseline, delay-only, CS-only and combined cases all exhibited the same CMD0 failure. Tested 500 ms wait and CS-before-SPI are not established fixes. Restored normal firmware/main.py to Pico /main.py, retaining diagnostic support. Root cause remains open. No Host tests rerun for hardware measurement and entry restoration; last suite 139 passed. See [full evidence](SD_Startup_Investigation.md).


## 2026-09-10: Chat CMD0 diagnostic handoff validated

Corrected pre-mount diagnostic contamination: preserve first baseline mount failure, then probe only an unmounted CMD0 failure, without auto-remount. Bounded repeated-CMD0 method; actual regression tests replace synthetic assertions. Host/Mock 143 passed; Pico warm CMD0 10/10 idle responses, SD remount and existing 65-line CSV readback passed. Temporary diagnostic boot deployed for cold-power evidence; root cause unresolved. See [handoff validation](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: Verification-method handoff

Updated verify_sd_diagnostics.py to execute diagnostic regressions; aligned instructions to current 400 kHz baseline. Added simulated SPI constructor/command coverage for idle clocks, exact CMD0 frame, error preservation and timeout. Diagnostic 5 passed; full Host/Mock 144 passed. No Pico/runtime changes; see [verification handoff](SD_CMD0_Chat_Handoff_Validation.md).


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
