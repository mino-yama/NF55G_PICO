# Pico runtime integration / Host-Mock verification

Date: 2026-09-10. Status: Host/Mock verified; Pico deployed and RTC/SD manual smoke passed.
Existing r1 baseline and AGENTS.md remain authoritative. No NF55G command was requested.
See [deployment evidence and remaining checks](Pico_Deployment_20260910.md).

## Integrated modules

| Module | Responsibility |
|---|---|
| `pico_clock.py` | SystemClock: CPython monotonic / MicroPython ticks_ms + ticks_diff, accumulated monotonic milliseconds |
| `nf55_protocol.py` | Single-transaction guard, UART errors/short writes, EB separation, bounded receive frames, trace callbacks, idle receive service |
| `nf55_event.py` | EB CURRENT/CHANGE raw fields and timestamp; bounded queue of 32, overflow count, no Cache reference |
| `ate_server.py` | CRLF line assembler and partial response writes; 512-byte line, 8 queued commands |
| `main.py` | ATE receive pumping, command execution, idle EB service, RTC sampling, deferred Logger service |
| `sd_card.py` | HIL-derived SPI SD block driver: 400kHz initialization, 25MHz data, CSD capacity, OCR addressing, bounded card waits |
| `sd_sink.py` | FAT mount, CSV escaping, real file I/O, usage, owned BANK_A/B rotation, latched failures |
| `logger.py` | RAM queue, runtime busy checks on disk operations, DS3231 filenames, continuous-file rollover |
| `firmware/main.py` | Optional deployed root entry point invoking `src.main.main()` |

### ATE wire behavior

The operator confirmed **CRLF** termination on 2026-09-10.
UART0 remains 115200 bps / 8N1; request and reply end in `\r\n`.
The host should send one command and await its complete reply before sending another.
The bounded pending queue tolerates short bursts; it does not provide unlimited pipelining or hardware flow control.

- Commands may arrive in fragments. LF alone does not execute a command.
- Empty CRLF lines are ignored.
- Oversized/invalid-ASCII/malformed lines are discarded through CRLF, then return
  `ERR:LINE_TOO_LONG`, `ERR:ASCII`, or `ERR:FRAME` respectively.
- UART0 RX buffer: 4096 bytes; UART1 RX buffer: 2048 bytes. Reads are nonblocking.
- The NF55G polling hook only collects ATE bytes; it never executes a second transaction.
- A reply is fully written before the next command is executed. Unsent suffixes are retained on short writes.
- ATE work takes precedence over background Logger service.

### Clock and protocol

All runtime modules share one SystemClock. On Pico it accumulates `ticks_diff` between samples,
so existing absolute-deadline arithmetic uses a nonwrapping elapsed value. The scheduler samples every iteration;
the firmware must not suspend clock sampling for half the platform ticks period or longer.

- T1=200ms remains provisional; T2 and the command/response retry rules are unchanged.
- Transactions return to IDLE on completion/failure. Reentry returns BUSY without transmission.
- FU is rejected at the protocol entry as well as the ATE command path, including byte-form inputs.
- UART OSError or short write returns UART, ambiguous=True with actual elapsed/retry counters.
- EB is recognized during WAIT_ACK, WAIT_RESPONSE, response retry, and idle operation.
  Valid EB receives ACK; malformed EB receives plain NAK. EB never resets the enclosing deadline
  or consumes the normal response retry counter, and never updates STATUS/INFO.
- Partial idle frames expire after 100ms (development receive timeout using T2_DEFAULT_MS);
  full frames are capped at 512 bytes. Final EB timing validation remains OI-11.
- EB queue overflow drops the new event and increments `events.drop_count`; valid frames are still ACKed.
- Trace hooks queue raw TX/RX HEX in RAM. RTC is sampled outside communication; raw trace records
  also contain monotonic ticks. Transaction summary records contain elapsed time, retries, and ambiguous.

### Real SD integration

PicoSDSink uses SPI0 GP16/17/18/19 and mounts existing FAT at `/sd`; it never formats the card.
Capacity comes from CSD and filesystem statvfs. No automatic CMD0 retry conceals initialization failures.
Read-token/write-busy waits are limited to 1000ms; initialization loops are finite.
The block driver uses individual sector commands even for multi-sector requests.

- Files use DS3231 `YYYYMMDD_HHMMSS.csv`. An existing same-second file returns FILE_EXISTS;
  it is not overwritten. Without a valid RTC, session creation can fail while communication remains available.
- CSV fields containing commas/quotes/newlines are quoted. Binary UTF-8 writes avoid host newline translation.
- BANK_A and BANK_B each target 45% of filesystem capacity; 10% remains reserved. Bank rotation
  occurs between files. TEST sessions do not silently roll over mid-test; long CONT files roll over at 100MiB by default.
- Existing bank directories without `.nf55_logger` ownership markers are not adopted.
  Only logger-shaped CSV files in the inactive owned bank are removed during rotation; other names are preserved.
- Active bank is recorded in `.nf55_active_bank`. A missing/invalid record with existing logs causes mount failure
  instead of guessing which bank can be erased. Power loss during marker replacement requires inspection/recovery;
  the implementation does not claim power-fail atomicity for FAT.
- SD operation entry points and Logger draining check NF55G busy/pending receive state.
  Interrupted draining retains unsent rows and resumes deferred flushes after communication.
- SD write/flush/close errors latch status. SD_REINIT ends the current Logger session, counts queued records
  as dropped, closes best-effort, remounts, and requires a new TEST_START/LOG_CONT_START.
- There is no card-detect input: absent-card and initialization failures may both appear as MOUNT_ERR.

## Host/Mock verification

Command: `.venv\Scripts\python.exe -B -m unittest discover -s tests`

**136 tests passed**: existing 105 plus 31 runtime integration tests in `tests/test_runtime_integration.py`.
Tests use fake clocks/UARTs and a temporary host filesystem, not COM14 or real NF55G.

| Area | Evidence |
|---|---|
| Clock wrap | Artificial 256ms wrapping timer still produces 400–409ms final ACK timeout with one retry |
| Deadline boundary | D1 response at 100ms accepted; response beyond deadline does not produce success |
| EB interleaving | EB before ACK and during response/retry independently ACKed; STATUS unchanged |
| T2 preservation | EB at 10/20/29ms with T2=30ms does not extend two-attempt timeout beyond 62ms |
| EB invalid/overflow | BCC, length, nonhex failures NAKed; 32-entry limit and drops checked |
| UART failures | Short writes and OSError return ambiguous; retry count retained; following transaction/local diagnostics recover |
| ATE transport | Fragmented CRLF, partial TX, oversized/non-ASCII lines, queued input during NF55G transaction |
| SD scheduling | No write/flush/close/reinit when communication is busy; deferred flush resumes |
| SD failures | Mount ownership refusal, injected write/flush/close failures, reinit recovery, ATE/NF55G continuity |
| Files | Exact CSV readback including embedded CRLF/quotes, RTC filename, collision preservation, rollover, bank persistence |
| Block driver | CSD/sector count and block size, bounded write-busy wait |

The tests exposed and fixed Windows CSV newline expansion and a deferred-flush corner case where
the last queued row had already been written when communication deferred its flush.

## Hardware work remaining

This is integration code, not a production timing qualification. Synchronous FAT/SPI calls cannot be preempted
by Python scheduler logic once started. Host guards prove no SD calls start in known communication states;
they do not establish latency when a real EB/ATE byte arrives during an SD call. Measure this using final
firmware, actual SD cards, and external timing capture before permitting production communication.

Pico deployment and the integrated RTC/SD manual smoke now passed on the installed card.
Physical ATE UART HIL, first-power-on SD behavior, removal/fault injection,
and final GP4/GP5 inspection remain unverified. The previous CMD0 anomaly remains unexplained.
The new SD driver's capacity, file writes and remount/readback passed on this card;
this does not qualify other cards or power-on conditions.
Existing T9 entry gates and Open Issues remain in effect.

Verified deployment layout (device left stopped in REPL; automatic startup pending):
```text
/main.py       <- firmware/main.py
/src/*.py      <- src/ package, including __init__.py
/sd/           <- existing FAT SD mount point
```

Keep NF55G disconnected for initial integrated firmware checks. First load/import the package under REPL,
inspect diagnostics and verify zero NF55G command TX, then test the scheduler with a controlled ATE/Mock peer.
Only install the automatic root entry point after startup/stop/recovery behavior is verified.

Reference checked for the block-device contract: [MicroPython VFS documentation](https://docs.micropython.org/en/latest/library/vfs.html#block-devices).
