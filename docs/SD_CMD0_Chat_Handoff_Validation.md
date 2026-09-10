# Chat handoff validation — 2026-09-10

Handoff was found as local edits to `src/sd_card.py`,
`firmware/sd_startup_probe.py` and new `test_sd_card_diagnostics.py`.
No separate Chat conversation was accessed.

## Review and corrections

The supplied script ran diagnostics before the first normal mount, changed SPI
speed to 100 kHz, and then attempted normal startup. That result could not be
treated as an untouched cold-start mount. Its five Host checks passed, but the
mock check did not call `diagnose_cmd0_multi`; it analyzed a hardcoded list.
The diagnostic logger was local and unserviced, so its RAM queue was not durable evidence.

Preserved the CMD0 multi-attempt and R1-label functionality, with these changes:

- Record the normal first mount at baseline settings (400 kHz, no added delay,
  original CS ordering) before extra CMD0 traffic.
- Run the follow-up probe only for an unmounted CMD0 failure with communication idle.
  Never reset a mounted card. Do not remount automatically afterwards.
- Store first-startup evidence and follow-up results separately in RAM; print only
  after probing. Follow-up success never overwrites the failed startup snapshot.
- Follow-up probe reconstructs raw SPI at 400 kHz and sends 128 idle clocks,
  then 10 CMD0 commands separated by 50 ms. These are diagnostic repetitions,
  not production retries; they change card state and do not prove the root cause.
- Remove unnecessary manual method binding and unsupported Pin cleanup calls.
  Raise CS and deinitialize SPI after the probe.
- Bound method inputs to 1..20 attempts and 0..1000 ms between attempts.
- Replace the standalone test entry with execution of actual regression tests.
  Do not infer contact/CRC/power causes solely from the displayed R1 bit names.

## Validation

- Original submitted checks: 5/5 passed before corrections (limited coverage above).
- Full corrected Host/Mock suite: **143 passed**.
- New four tests execute the real repeated-command method with error/timeout/idle
  responses, validate exact CMD0 arguments and delays, enforce bounds, prohibit
  probing mounted/non-CMD0 failures, preserve first evidence and verify cleanup.
- Pico/MicroPython warm diagnostic: **10/10 CMD0 replies were 0x01**.
- Following probe cleanup, real SD mount succeeded; capacity 15,910,043,648 bytes.
  Existing `/sd/BANK_A/20260910_094306.csv` read back with 65 lines.
- No SD formatting/deletion, NF55G command request, commit or push was performed.

Raw warm evidence: `temp/pico_chat_cmd0_warm_validation.log`.
Diagnostic entry warm boot also passed, recording `FILESYSTEM_MOUNTED` with no
extra CMD0 results; hardware initialization took 191 ms and 184 ms on the two
observed soft starts (`temp/pico_chat_cmd0_probe_warm_boot.log`).
Reproducible warm-only test: `scripts/pico_cmd0_diagnostic_smoke.py`.
Original handoff script/test backups are in ignored `temp/chat_*_original.py`.

## Current device and next cold-start test

Pico `/main.py` is now the corrected temporary diagnostic entry, CASE=BASELINE.
`/sd_cmd0_probe.py` is the same diagnostic module for the manual warm test.
Restore `firmware/main.py` after investigation. The earlier normal-entry restoration
was superseded by this explicitly requested handoff validation.

After a physical power cycle, read both **before reset/reinit**:

```python
import sys
print(sys.modules['src.main'].startup_sd_diagnostic)
print(diagnostic_report)  # REPL globals; __main__ is not in sys.modules on this Pico
```

The report also prints once on USB after probing. A warm successful startup skips
probing with `FILESYSTEM_MOUNTED`. A failed cold startup may retain MOUNT_ERR even
if the follow-up CMD0 responses succeed; this is intentional evidence preservation.
The firmware will then run the ATE loop. It is a diagnostic build, not a production
timing qualification. The initial power-on CMD0=31 cause remains unresolved.

## Cold-power result after handoff

Operator reported power cycling. Before any host reset/reinitialization, RAM
snapshot showed BASELINE, CARD_INIT, MOUNT_ERR, mounted=False,
`OSError('CMD0 failed: 31',)`, elapsed_ms=19 (hardware initialization duration).
The automatic post-failure probe had completed: **10/10 replies were 0x01**, at
400 kHz with 50 ms between attempts. Its copied first-startup failure matched the
runtime snapshot; SD remained unmounted as designed, and the ATE loop was running.

This proves successful CMD0 reception after the initial failed initialization,
not success of a single unchanged retry: the diagnostic reconstructs SPI and
provides another 128 idle clocks first. It does not separate SPI receive state,
card state, extra clock effects or elapsed time. No permanent retry fix is selected.

The first host read hit KeyError when looking for `__main__` in sys.modules.
Reading `diagnostic_report` from REPL globals succeeded without reset/reinit;
the inspection instructions above are corrected. This was a host inspection
error, not a firmware startup exception.

Evidence: `temp/pico_chat_cmd0_cold_diagnostic_complete.log`; original inspection
error retained in `temp/pico_chat_cmd0_cold_diagnostic.log`. A subsequent explicit
manual app restart is recorded separately in
`temp/pico_chat_cmd0_cold_manual_restart.log`, preserving both RAM records.
The temporary diagnostic root entry remains installed for future investigation.

## Additional verification-method handoff

The subsequently supplied `verify_sd_diagnostics.py` was reviewed and executed.
Its original import/label/syntax checks passed, but it did not exercise CMD0
serialization or response polling, and its suggested 100 kHz did not match the
current 400 kHz baseline. The original is backed up at
`temp/chat_verify_sd_diagnostics_original.py`.

The updated entry runs five executable diagnostic regression tests and compiles
the probe without executing it. It uses paths relative to its own location,
returns a failing exit status for failed checks, and does not access hardware.

```text
.venv\Scripts\python.exe -B verify_sd_diagnostics.py
.venv\Scripts\python.exe -B -m unittest discover -s tests
```

Results: diagnostic tests **5 passed**; full Host/Mock suite **144 passed**.
New simulated SPI coverage executes the SDCard constructor and cmd implementation:
CS High while sending 16 FF bytes, 400 kHz mode 0 configuration, CS Low, the existing
extra FF, CMD0 bytes `40 00 00 00 00 95`, FF response polling, and CS release.
It checks both bounded no-response polling and immediate failure on R1=31 even
if a later simulated byte would be 1. These are software checks, not wire captures.

No runtime source, device files or cold-start settings changed in this handoff.
Removing the extra FF remains an unperformed comparison. R1 labels alone do not
establish a physical CRC/power/wiring fault; the cold-power cause is still open.


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


## 2026-09-10: CMD0_NO_PRE_FF cold-power result

Operator power-cycled. Before any host reset/reinit, the initial snapshot was
case=CMD0_NO_PRE_FF, cmd0_pre_dummy=False, startup_delay_ms=0,
cs_before_spi=False, CARD_INIT, MOUNT_ERR, mounted=False,
OSError('CMD0 failed: 31',), elapsed_ms=20 (hardware initialization duration).
Post-failure diagnostic replies were 10/10 0x01 at 400 kHz; the failed initial
snapshot remained unchanged. SD was unmounted and the ATE loop had been running.

Removing only CMD0's CS-Low pre-command FF did not resolve this cold-power trial.
This does not identify the cause: the successful diagnostic also reconstructs SPI
and sends another 128 CS-High clocks. Those effects remain to be separated.
No production workaround selected; no source/device-file changes in this check.
Evidence: temp/pico_no_ff_cold_diagnostic.log. An explicit manual app restart
then confirmed SD_STATUS=OK and RTC_CHECK=OK, preserving both RAM records and
restarting the receive loop; evidence: temp/pico_no_ff_cold_manual_restart.log.
The temporary CMD0_NO_PRE_FF diagnostic boot remains installed; cold-power fault
is unresolved. Host tests were not rerun for this hardware-only measurement.


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


## 2026-09-10: RETRY_ONLY cold-power result

Before host reset/reinit, initial snapshot showed CMD0_NO_PRE_FF, RETRY_ONLY,
cmd0_pre_dummy=False, zero added wait, original CS/SPI ordering, CARD_INIT,
MOUNT_ERR, mounted=False, CMD0 failed: 31, hardware initialization elapsed 20 ms.
The single same-object/SPI follow-up returned **127 (0x7F)**, not 0x01.
Report: mode=RETRY_ONLY, attempts=1, delay_ms=0, skipped=None, error=None,
results=[(1, '0x7f', 127, ... , False)]. error=None means the diagnostic itself
did not raise; it does not mean the CMD0 succeeded.

No SPI rebuild/init or separate 128-clock train preceded this follow-up; ordinary
cmd() CS transitions and release clocks still occurred. One unchanged-object
retry did not recover in this trial. Earlier reconstruction-plus-clocks probes
returned 0x01; SPI reconstruction and extra clocks remain unseparated. Changed
R1 bit patterns alone do not establish an electrical or CRC cause.

Evidence: temp/pico_retry_only_cold_diagnostic.log. Subsequent explicit manual
app restart confirmed SD_STATUS=OK and RTC_CHECK=OK and resumed the receive loop,
retaining both RAM records (temp/pico_retry_only_cold_manual_restart.log).
The temporary RETRY_ONLY diagnostic entry remains installed. No source/device
changes or Host tests for this hardware-only measurement; no permanent retry
workaround selected and cold-power root cause remains unresolved.
Next comparison target: SPI reconstruction without an extra idle-clock train,
or an extra idle-clock train on the retained SPI, with first evidence preserved.


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
