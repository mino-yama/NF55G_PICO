# SD startup investigation — 2026-09-10

## Established observations

- First operator power-cycle check: application reached ATE receive loop but SD was not mounted.
  The original initialization exception was discarded, so the failed command is unknown.
- Explicit manual SD initialization afterwards succeeded on the same installed card.
- Diagnostic firmware soft-boot check: `status=OK`, `stage=READY`, `mounted=True`,
  `error=None`, `elapsed_ms=289`; existing SD files were visible. A soft reset does not establish cold-power behavior.
- No NF55G commands were requested. SD files were not removed or formatted.

## Diagnostic change

`FileSDSink.last_error` retains the original exception representation rather than
only the public error category. `PicoSDSink.mount_stage` identifies IMPORT,
UNMOUNT, SPI_SETUP, CARD_INIT, VFS_MOUNT, BANK_SETUP or READY.
`src.main.startup_sd_diagnostic` snapshots the first hardware initialization in
the current interpreter: status, stage, error, mounted and elapsed_ms (application
hardware initialization duration, not elapsed time since voltage rose).
The snapshot survives SD_REINIT and subsequent app creation until interpreter reset.
Records remain in RAM; no extra USB prints, SD writes, delays or retries are introduced.
ATE response formats remain unchanged. Startup still permits communication after SD failure.

Two new Host tests verify a single failing card initialization retains its exact
error and that first-failure evidence survives recovery while local ATE commands
remain usable. All 138 Host/Mock tests passed.

## Diagnostic cold-power measurement

Operator again reported power cycling on 2026-09-10. The diagnostic was read
before any software reset or SD reinitialization:

```text
status=MOUNT_ERR, stage=CARD_INIT, mounted=False, elapsed_ms=126
error=OSError('CMD0 failed: 31',)
```

The application had reached its receive loop. `/sd` was empty, with statvfs
reporting the internal flash filesystem. Failure is now localized to the first
CMD0 response (decimal 31 / 0x1F), before FAT mount or logger bank preparation.
126 ms is the measured hardware initialization duration, not time since power-on.

After saving this evidence, an explicit manual retry in the same powered state
succeeded: CMD0 returned 1, CMD8 returned 1, ACMD41 returned 1 then 0, OCR/CMD16/CMD9
returned 0. FAT capacity was 15,910,043,648 bytes. The first-failure snapshot remained
unchanged in RAM. This comparison does not distinguish elapsed power-settling time
from the effect of the preceding failed command sequence.

The probe was unmounted and the application recreated; SD_STATUS and RTC_CHECK
were OK (RTC 20260910_095705). Its receive loop was restarted and left running.
No runtime source/device file changes or Host test reruns were needed for this
measurement. Raw evidence: `temp/pico_sd_cold_boot_diagnostic_20260910.log` and
`temp/pico_sd_cold_failure_retry_20260910.log`.

## Next measurement

### Controlled experiment firmware prepared

`firmware/sd_startup_probe.py` is a temporary replacement for Pico `/main.py`.
Restore `firmware/main.py` after the investigation. The selected condition is
included in the first-startup RAM snapshot. The normal PicoSDSink defaults remain
zero added delay and the original SPI-before-CS ordering. Experimental delay is
bounded to 0..2000 ms and also applies if that experimental sink is explicitly
reinitialized; it is not a production timing setting.

| Case | Added wait before SPI/CS setup | CS set High before SPI creation | Cold-start result |
|---|---:|---|---|
| BASELINE | 0 ms | No | Previous build: CMD0=31 |
| DELAY_ONLY | 500 ms | No | CMD0=31; CARD_INIT failed, elapsed 625 ms |
| CS_ONLY | 0 ms | Yes | CMD0=31; CARD_INIT failed, elapsed 126 ms |
| DELAY_AND_CS | 500 ms | Yes | CMD0=31; CARD_INIT failed, elapsed 627 ms |

The comparison is complete; normal `firmware/main.py` has been restored to Pico
`/main.py` (0 ms added wait, original ordering). Diagnostic support remains in
the source, and the experimental entry is retained for reproducibility.
In the experimental cases the wait occurs after imports and before pin/SPI
initialization; it does not change CS ordering. The CS_ONLY condition establishes
GP17 output High immediately before constructing SPI0, with no added delay.
All conditions retain one CMD0 attempt, 400 kHz initialization and 128 idle clocks.
Use separate physical power cycles for each condition; do not remove the card.
One success is exploratory evidence only: repeat the relevant conditions and
baseline before selecting a permanent fix. A successful delay-only case would
support elapsed-startup-time sensitivity, not prove the supply voltage waveform.

Host/Mock: 139 tests passed, including all four condition sequences with one
injected failing card initialization each. No experiment changes NF55G commands.
Warm test evidence: `temp/pico_sd_delay_only_warm_20260910.log`.

DELAY_ONLY cold-start evidence: `temp/pico_sd_delay_only_cold_20260910.log`.
Captured before reset/reinit: case=DELAY_ONLY, startup_delay_ms=500,
cs_before_spi=False, status=MOUNT_ERR, stage=CARD_INIT, mounted=False,
error=OSError('CMD0 failed: 31',), elapsed_ms=625. The receive loop was running.
Adding 500 ms before SPI/CS setup did not resolve the failure in this trial;
this does not exclude other supply or signaling problems. No SD files were changed.
Next case changes only CS/SPI ordering relative to baseline, with zero added delay.

CS_ONLY cold-start evidence: `temp/pico_sd_cs_only_cold_20260910.log`.
Captured before reset/reinit: case=CS_ONLY, startup_delay_ms=0,
cs_before_spi=True, status=MOUNT_ERR, stage=CARD_INIT, mounted=False,
error=OSError('CMD0 failed: 31',), elapsed_ms=126. The receive loop was running.
CS High before SPI construction alone did not resolve the failure in this trial.
The two single-variable changes both failed; the combined condition is next.
This does not rule out earlier boot pin transitions, supply or signal-integrity issues.
DELAY_AND_CS waits 500 ms, then drives CS High, then constructs SPI; it does not
hold CS High throughout the preceding wait or from the instant power is applied.
Warm evidence: `temp/pico_sd_delay_and_cs_warm_20260910.log`.

DELAY_AND_CS cold-start evidence: `temp/pico_sd_delay_and_cs_cold_20260910.log`.
Captured before reset/reinit: case=DELAY_AND_CS, startup_delay_ms=500,
cs_before_spi=True, status=MOUNT_ERR, stage=CARD_INIT, mounted=False,
error=OSError('CMD0 failed: 31',), elapsed_ms=627. The receive loop was running.
All three experimental conditions failed on their single recorded cold-start
trials. Neither the selected 500 ms delay nor this CS ordering, alone or together,
resolved the failure. This is not proof that every timing/order change would fail.
No automatic retry was introduced and no permanent workaround was selected.

The normal root entry was restored after capturing evidence. Warm-start check
evidence: `temp/pico_sd_restored_warm_20260910.log`. The cold-power fault remains
unresolved. Next useful evidence is the first CMD0 MOSI/MISO/CS/SCK waveform and
card-supply voltage at power-up, compared with a successful warm initialization;
also consider boot-time pin states before Python and software SPI receive alignment.
Those are investigation targets, not established causes. No further physical
power cycles with unchanged conditions are requested at this stage.

Compare controlled cold starts with one variable changed at a time: delay before
first CMD0, then CS/SPI initialization ordering if needed. If failures persist,
capture CS/SCK/MOSI/MISO and card supply externally. These comparisons have not
yet been performed. The root electrical/timing cause remains unresolved.

For each diagnostic cold start, power-cycle without removing the card.
Before soft-reset, SD_REINIT or manual mounting, interrupt the loop and read:

```python
import src.main
print(src.main.startup_sd_diagnostic)
```

Use the recorded command/error to compare power-up/CS/clock sequencing and supply
behavior. Contact failure, supply
settling and SPI signaling remain hypotheses, not established causes.

Current driver provides 128 idle clocks at 400 kHz before one CMD0 attempt; no
explicit power-stabilization delay is present. This alone does not prove a timing
violation because interpreter startup and imports precede it. The upstream
[MicroPython SD driver](https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py)
allows multiple CMD0 attempts. That difference is a comparison point, not a reason
to hide the initial failure with automatic retries during this investigation.

Raw warm-boot evidence: `temp/pico_sd_soft_boot_diagnostic_20260910.log`.
The first diagnostic build reported elapsed_ms=0 because its clock had not been
sampled before initialization; the timer start was corrected and the repeated
check recorded 289 ms in the evidence file above before cold-boot use.
Backup files: `temp/pico_main_before_sd_diagnostic.py` and
`temp/pico_sd_sink_before_diagnostic.py`. No Open Issue was closed.
