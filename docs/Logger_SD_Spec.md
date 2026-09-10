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
- filename: `YYYYMMDD_HHMMSS.csv`
- RTC source: Pico-side DS3231

## Production
ATE sends:
- TEST_START
- TEST_END

One production test = one CSV file.
TEST_END performs forced queue drain, flush and close.

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

USB logging must be non-blocking and may drop logs rather than delay ATE/NF55G.

Priority:
1. ATE
2. complete current NF55G transaction safely
3. mandatory internal processing
4. SD logger
5. future USB logger

## Suggested CSV fields
timestamp,category,direction,cmd,event,raw_ascii,raw_hex,bcc_rx,bcc_calc,bcc_ok,cmd_retry,rsp_retry,result,detail


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
