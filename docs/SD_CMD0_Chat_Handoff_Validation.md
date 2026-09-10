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
