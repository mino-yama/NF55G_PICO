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


## 2026-09-10: Chat CMD0 diagnostic handoff validated

Corrected pre-mount diagnostic contamination: preserve first baseline mount failure, then probe only an unmounted CMD0 failure, without auto-remount. Bounded repeated-CMD0 method; actual regression tests replace synthetic assertions. Host/Mock 143 passed; Pico warm CMD0 10/10 idle responses, SD remount and existing 65-line CSV readback passed. Temporary diagnostic boot deployed for cold-power evidence; root cause unresolved. See [handoff validation](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: Cold first failure followed by successful diagnostic CMD0

BASELINE first mount failed at CMD0=31 (CARD_INIT, MOUNT_ERR, elapsed 19 ms). Automatic post-failure raw probe recorded 10/10 CMD0=1 replies; original failure remained preserved, with no automatic SD remount. Probe reconstructs SPI and supplies extra idle clocks, so this is not proof of a simple one-command retry fix. Captured before host reset/reinit. See [handoff cold evidence](SD_CMD0_Chat_Handoff_Validation.md). No source/device changes or Host tests for this hardware measurement.


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


## 2026-09-10: CLOCKS_ONLY preserved startup diagnostic rechecked

Read COM14 without host reset, SPI reinitialization, remount, or firmware upload.
The preserved snapshot reports CMD0_NO_PRE_FF / CLOCKS_ONLY, CARD_INIT,
MOUNT_ERR, mounted=False, CMD0 failed: 31, elapsed_ms=12. The retained-SPI
follow-up reports 16 additional CS-High FF bytes (128 clocks), one attempt,
zero explicit delay, baudrate=400000, result=127 (0x7F), skipped=None,
error=None. This is not the expected idle reply 0x01; error=None only indicates
that the diagnostic itself did not raise an exception.

This session re-read existing startup evidence, matching the earlier
pico_clocks_only_cold_diagnostic.log; no new physical power cycle was performed
or verified. Do not count it as another independent cold-start trial.
SD_STATVFS alone does not demonstrate an SD mount when mounted=False.
Evidence: temp/pico_clocks_only_observed_20260910_151802.log.

Host/Mock: python -m unittest discover -s tests -p 'test_*.py': 147 passed.
No firmware/source changes; no NF55G commands sent. Device left at friendly
REPL after diagnostic acquisition; the ATE receive loop was not restarted.
Cold-power root cause remains unresolved; no Open Issue closed and no
production workaround selected. A new cold-start trial requires an operator
physical power cycle followed by evidence capture before reset/reinitialization.


## 2026-09-10: CLOCKS_ONLY operator power-cycle trial at 15:20 JST

Operator explicitly confirmed power off/on completion. Captured COM14 startup
state before any host reset, SPI reinitialization, remount or firmware upload.
The running app was interrupted solely to read the preserved diagnostic.
Pico identified as Raspberry Pi Pico2 with RP2350, MicroPython v1.28.0.

Initial snapshot: CMD0_NO_PRE_FF, CLOCKS_ONLY, cmd0_pre_dummy=False,
startup_delay_ms=0, cs_before_spi=False, CARD_INIT, MOUNT_ERR, mounted=False,
OSError('CMD0 failed: 31',), elapsed_ms=12.
Follow-up: retained SPI, 16 CS-High FF bytes (128 clocks), baudrate=400000,
attempts=1, delay_ms=0, result=127 (0x7F), skipped=None, error=None.
The follow-up did not return idle 0x01. error=None is not initialization success.
SD_STATVFS is not evidence of an SD mount when mounted=False.

This independent operator power-cycle trial reproduced the recorded failure;
extra clocks on the retained SPI did not recover in this trial. Root cause
remains unresolved; do not infer a permanent workaround or close an Open Issue.
Evidence: temp/pico_clocks_only_powercycle_20260910_152000.log.
No source/device-file changes or NF55G commands. Device left at friendly REPL;
ATE receive loop is stopped. Host/Mock not rerun for this hardware-only capture;
last run in the preceding verification: 147 passed.


## 2026-09-10: Chat 100 kHz / PULL_UP deployment and Phase 1

Deployed firmware/sd_startup_probe.py to /main.py and all 23 direct src files
(22 Python modules plus .gitkeep) to /src/. Host CPython __pycache__ artifacts
were excluded. All 24 deployed files matched host bytes on readback.
Previous main.py and 22 Python modules backed up in
 temp/sd_100k_deploy_20260910_152536/; transfer.log records operations.
No application source changes were made in this deployment session.
Old /sd_cmd0_probe.py is not the deployed entry and must not be used for these
phases; Phase 1 directly imports the updated /src/sd_card.py.

Host/Mock: 147 tests passed before deployment.
Phase 1: PASS. Fresh REPL interpreter, unmounted SD, GP17 High before SPI setup,
GP16 Pin.IN/PULL_UP, SPI0 reported baudrate=100000, polarity=0, phase=0,
128 CS-High clocks, CMD0_PRE_DUMMY=True, one CMD0 returned 1 (0x01).
Evidence: temp/pico_phase1_100k_result.log; script: temp/pico_phase1_100k.py.
This warm basic response does not prove a cold mount fix or isolate which
parameter mattered. No NF55G commands were issued.

Phase 2: pending physical power cycle after this deployment. Boot entry selects
CMD0_NO_PRE_FF / CLOCKS_ONLY. Read with temp/read_100k_cold.py before any reset,
remount or additional initialization; expect mounted=True and stage=READY.
Phase 3: pending Phase 2, then five operator cold-power trials in order BASELINE,
DELAY_ONLY, CS_ONLY, DELAY_AND_CS, CMD0_NO_PRE_FF. Change only CASE between trials;
keep 100 kHz, PULL_UP and CLOCKS_ONLY constant, preserve first startup separately
from follow-up probes. Target duration about 15 minutes depends on operator
power cycles. One successful trial cannot establish a robust optimal pattern.
Phase 4: optional physical MISO voltage measurement, not performed; software
PULL_UP configuration alone is not voltage measurement evidence.

Pico left at REPL after Phase 1 with diagnostic boot installed; ATE loop stopped.
Cold-start root cause remains open. Earlier claims that 100 kHz is required by
RW11 r1, that pullup effectiveness is guaranteed, or that continued failure
excludes speed/signal integrity are not established by this hardware test.


## 2026-09-10: Phase 2 100 kHz / PULL_UP cold boot PASS; Phase 3 prepared

Operator confirmed physical power cycle after deployment. Captured before host
reset, remount or SPI reinitialization at 15:30 JST on COM14.
CASE=CMD0_NO_PRE_FF, PROBE_MODE=CLOCKS_ONLY, startup_delay_ms=0,
cs_before_spi=False, cmd0_pre_dummy=False. First snapshot: status=OK,
stage=READY, mounted=True, error=None, elapsed_ms=305 (hardware initialization).
Follow-up results=[] and skipped=FILESYSTEM_MOUNTED: no diagnostic CMD0 was sent
to the mounted card. Report attempts=1 is configuration, not an executed count.
SD_STATVFS=(65536, 65536, 242768, 242752, 242752, 0, 0, 0, 0, 255).
Evidence: temp/pico_100k_cold_20260910_153041.log.

Phase 2 expectation met in this single independent trial. This does not isolate
100 kHz from PULL_UP or establish repeated cold-start reliability/root cause.
No Open Issue closed. No NF55G commands issued.

Phase 3 trial 1/5 prepared: /main.py now selects BASELINE; 100 kHz, PULL_UP and
CLOCKS_ONLY remain unchanged. Derived entry differs from host diagnostic source
only in CASE selection; firmware/sd_startup_probe.py remains CMD0_NO_PRE_FF.
Backup, exact variant and verified readback: temp/phase3_baseline_100k/.
Next operator physical power cycle is required before capturing BASELINE.
Remaining order: DELAY_ONLY, CS_ONLY, DELAY_AND_CS, CMD0_NO_PRE_FF.
Phase 4 physical voltage measurement remains optional and unperformed.
Pico left at REPL, ATE loop stopped. No application source changes; Host/Mock
not rerun for hardware capture and CASE selection (last run: 147 passed).


## 2026-09-10: Phase 3 trial 1/5 BASELINE PASS; DELAY_ONLY prepared

Operator confirmed physical power cycle. Read COM14 without host reset,
remount or SPI reinitialization. First snapshot: case=BASELINE,
probe_mode=CLOCKS_ONLY, cmd0_pre_dummy=True, startup_delay_ms=0,
cs_before_spi=False, status=OK, stage=READY, mounted=True, error=None,
elapsed_ms=304. Probe results=[] and skipped=FILESYSTEM_MOUNTED;
no follow-up CMD0 executed. Initialization setting remains 100 kHz with PULL_UP.
Evidence: temp/pico_100k_cold_20260910_153334.log.

Phase 3 progress: BASELINE 1/1 successful trial; DELAY_ONLY, CS_ONLY,
DELAY_AND_CS, CMD0_NO_PRE_FF still pending in this five-CASE series.
Phase 2 separately recorded CMD0_NO_PRE_FF success (305 ms).
These single observations do not establish an optimal pattern or root cause.

Prepared trial 2/5: /main.py selects DELAY_ONLY (500 ms startup delay,
original CS/SPI ordering, CMD0 pre-FF enabled); all other diagnostic settings
unchanged. Device entry byte-verified. Backup and readback: temp/phase3_delay_only_20260910_153435/.
Host firmware/sd_startup_probe.py unchanged. Next physical power cycle needed.
Pico left at REPL; ATE loop stopped. No NF55G commands issued by this test.
No application source changes or Host/Mock rerun for hardware capture and CASE
selection; last suite 147 passed. Open Issues remain open; Phase 4 unperformed.


## 2026-09-10: Phase 3 trial 2/5 DELAY_ONLY PASS; CS_ONLY prepared

Operator confirmed physical power cycle. Captured COM14 first startup without
host reset, remount or SPI reinitialization. Snapshot: case=DELAY_ONLY,
probe_mode=CLOCKS_ONLY, cmd0_pre_dummy=True, startup_delay_ms=500,
cs_before_spi=False, status=OK, stage=READY, mounted=True, error=None,
elapsed_ms=806 (includes 500 ms wait). Probe results=[] and
skipped=FILESYSTEM_MOUNTED; no follow-up CMD0 executed.
Initialization remains configured at 100 kHz with MISO PULL_UP.
Evidence: temp/pico_100k_cold_20260910_153859.log.

Phase 3 results so far: BASELINE succeeded at 304 ms; DELAY_ONLY succeeded at
806 ms, each one cold trial. Additional delay has not demonstrated a reliability
benefit in these observations; optimal pattern and root cause remain undecided.
CS_ONLY, DELAY_AND_CS, CMD0_NO_PRE_FF remain pending in this five-CASE series.

Prepared trial 3/5: /main.py selects CS_ONLY (zero added wait, GP17 High before
SPI creation, CMD0 pre-FF enabled); other diagnostic settings unchanged.
Backup and byte-verified readback: temp/phase3_cs_only_20260910_153938/.
Host firmware/sd_startup_probe.py unchanged. Next physical power cycle required.
Pico left at REPL; ATE loop stopped. No NF55G commands issued by this test.
No application source changes or Host/Mock rerun for hardware capture and CASE
selection; last suite 147 passed. No Open Issue closed. Phase 4 unperformed.


## 2026-09-10: Phase 3 trial 3/5 CS_ONLY PASS; DELAY_AND_CS prepared

Operator confirmed physical power cycle. Captured COM14 first startup without
host reset, remount or SPI reinitialization. Snapshot: case=CS_ONLY,
probe_mode=CLOCKS_ONLY, cmd0_pre_dummy=True, startup_delay_ms=0,
cs_before_spi=True, status=OK, stage=READY, mounted=True, error=None,
elapsed_ms=307. Probe results=[] and skipped=FILESYSTEM_MOUNTED;
no follow-up CMD0 executed. Initialization remains configured at 100 kHz with
MISO PULL_UP. Evidence: temp/pico_100k_cold_20260910_154437.log.

Phase 3 results: BASELINE 304 ms, DELAY_ONLY 806 ms (500 ms wait included),
CS_ONLY 307 ms, each one successful cold trial. These observations do not
establish a reliability advantage or optimal pattern; root cause remains open.
DELAY_AND_CS and CMD0_NO_PRE_FF remain pending in this five-CASE series.

Prepared trial 4/5: /main.py selects DELAY_AND_CS (500 ms wait, then GP17 High
before SPI creation, CMD0 pre-FF enabled); other diagnostic settings unchanged.
Backup and byte-verified readback: temp/phase3_delay_and_cs_20260910_154517/.
Host firmware/sd_startup_probe.py unchanged. Next physical power cycle required.
Pico left at REPL; ATE loop stopped. No NF55G commands issued by this test.
No application source changes or Host/Mock rerun for hardware capture and CASE
selection; last suite 147 passed. No Open Issue closed. Phase 4 unperformed.


## 2026-09-10: Phase 3 trial 4/5 DELAY_AND_CS PASS; CMD0_NO_PRE_FF prepared

Operator confirmed physical power cycle. Captured COM14 first startup without
host reset, remount or SPI reinitialization. Snapshot: case=DELAY_AND_CS,
probe_mode=CLOCKS_ONLY, cmd0_pre_dummy=True, startup_delay_ms=500,
cs_before_spi=True, status=OK, stage=READY, mounted=True, error=None,
elapsed_ms=810 (includes 500 ms wait). Probe results=[] and
skipped=FILESYSTEM_MOUNTED; no follow-up CMD0 executed.
Initialization remains configured at 100 kHz with MISO PULL_UP.
Evidence: temp/pico_100k_cold_20260910_154608.log.

Phase 3 results: BASELINE 304 ms, DELAY_ONLY 806 ms, CS_ONLY 307 ms,
DELAY_AND_CS 810 ms, each one successful cold trial. The delayed cases include
500 ms wait. No reliability advantage or optimal pattern is established.
CMD0_NO_PRE_FF remains pending as trial 5/5 of this series.

Prepared trial 5/5: /main.py now matches firmware/sd_startup_probe.py exactly,
selecting CMD0_NO_PRE_FF (zero wait, original CS/SPI ordering, omit CMD0 pre-FF).
Other diagnostic settings unchanged. Backup and byte-verified readback:
temp/phase3_no_pre_ff_20260910_154647/.
Next physical power cycle required. Pico left at REPL; ATE loop stopped.
No NF55G commands issued by this test. No application source changes or
Host/Mock rerun for hardware capture and CASE selection; last suite 147 passed.
Root cause unresolved, no Open Issue closed. Phase 4 unperformed.


## 2026-09-10: Phase 3 trial 5/5 PASS and five-CASE summary

Operator confirmed physical power cycle. Final CMD0_NO_PRE_FF first snapshot
captured on COM14 without reset, remount or SPI reinitialization:
status=OK, stage=READY, mounted=True, error=None, elapsed_ms=305,
startup_delay_ms=0, cs_before_spi=False, cmd0_pre_dummy=False.
CLOCKS_ONLY report results=[] and skipped=FILESYSTEM_MOUNTED; no additional
CMD0 executed. All five trials kept 100 kHz initialization and MISO PULL_UP.

| CASE | Cold mount | Elapsed ms (includes wait) | Evidence |
|---|---|---:|---|
| BASELINE | OK / READY | 304 | temp/pico_100k_cold_20260910_153334.log |
| DELAY_ONLY | OK / READY | 806 | temp/pico_100k_cold_20260910_153859.log |
| CS_ONLY | OK / READY | 307 | temp/pico_100k_cold_20260910_154437.log |
| DELAY_AND_CS | OK / READY | 810 | temp/pico_100k_cold_20260910_154608.log |
| CMD0_NO_PRE_FF | OK / READY | 305 | temp/pico_100k_cold_20260910_162927.log |

Each row is one independent operator power-cycle trial. All five cold mounts
succeeded; delayed cases include the configured 500 ms wait. Phase 2 separately
also succeeded with CMD0_NO_PRE_FF at 305 ms (not counted as a Phase 3 row).

Phase 1 basic CMD0: passed (0x01 at 100 kHz).
Phase 2 cold boot: passed. Phase 3 five-CASE acquisition: completed, 5/5 mounted.
No unique optimal pattern is established by one trial per CASE. BASELINE had
the smallest observed duration (304 ms), but differences of 1-3 ms among the
no-wait cases do not establish superiority. Extra delay, CS reordering and
CMD0 pre-FF omission showed no success advantage in this series. Treat BASELINE
as a candidate for repeated validation, not an approved production selection.
100 kHz and PULL_UP changed together; their individual effects and the original
failure's root cause remain unresolved. No Open Issue closed.

Phase 4 optional physical MISO voltage measurement not performed; no instrument
reading is available. Software PULL_UP setup alone does not prove idle voltage
or signal integrity. Physical measurement requires operator/instrument evidence.

Recorded only evidence and comparison; application/device files unchanged in
this final capture. /main.py remains the CMD0_NO_PRE_FF diagnostic entry matching
firmware/sd_startup_probe.py, not the normal production entry. Pico left at
friendly REPL; ATE receive loop stopped. No NF55G commands issued by this test.
Host/Mock not rerun for this hardware-only capture; last suite 147 passed.


## 2026-09-10: User selected baseline; normal entry restored, task complete

User requested return to baseline and completion after successful five-CASE
trials. Retained 100 kHz SD initialization and MISO PULL_UP. Normal defaults:
startup_delay_ms=0, cs_before_spi=False, CMD0_PRE_DUMMY=True.
Copied firmware/main.py to Pico /main.py and verified byte equality by readback.
Previous diagnostic entry backed up under temp/baseline_restore_20260910_163239/.
The diagnostic source remains available on host, but is not the boot entry.
No application logic/source changes were made in this restoration.

Normal-entry warm boot verification: status=OK, stage=READY, mounted=True,
error=None, elapsed_ms=333, no added wait, original CS order. CMD0_PRE_DUMMY=True
verified. NORMAL_BASELINE_CHECK_PASS recorded. Normal app run loop observed
before diagnostic interruption; final soft boot issued to leave normal firmware
running, with no subsequent interruption or boot exception in the capture window.
Evidence: temp/pico_baseline_normal_warm_boot.log.
This is a soft-boot restoration check, not another physical cold-start trial;
prior BASELINE physical cold trial succeeded at 304 ms.
Host/Mock rerun: 147 tests passed (unittest discover -s tests -p 'test_*.py').
No NF55G test commands sent during restoration.

Requested deployment/CASE testing/baseline restoration is complete. Optional
Phase 4 physical voltage measurement was not performed; no further power cycle
requested for this task. Combined 100 kHz + PULL_UP improvement was observed,
but clock-only causality and original fault mechanism remain unproven.
Baseline selection is user-authorized; no unresolved design Open Issue closed
and no product PASS/FAIL judgment made.
