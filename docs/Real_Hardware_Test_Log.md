# Real Hardware Test Log
Revision: Rev.0-draft

## Critical notice before any real-hardware debug
- Before powering or wiring the final fixture stack, confirm ADA-5703 PiCowbell GP4/GP5 are physically isolated from the Pico header/UART lines.
- GP4/GP5 are reserved for Pico-2CH-RS232 NF55G UART1. Do not start NF55G UART loopback, UART initialization, or real NF55G connection checks with ADA-5703 GP4/GP5 still connected.
- ADA-5703 microSD may be used only as the SD function on GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI after the GP4/GP5 isolation is verified.
- 2026-09-04 real-hardware tests were performed with ADA-5703 GP4/GP5 physically isolated from the Pico header/UART lines.
- Track HW-01 until the final fixture physical cut/isolation method and inspection record are formally documented.

## 2026-09-02 Pico hardware smoke

### Scope
- T0-T7 host gate confirmation before hardware testing.
- Pico USB recognition check.
- Non-destructive USB response check.

### Preconditions
- Repository: `NF55G_Pico`
- Branch: `main`
- Hardware target: Raspberry Pi Pico 2 fixture bring-up path
- ADA-5703 GP4/GP5 isolation: physically isolated for 2026-09-04 tests; final fixture inspection record still required
- Real NF55G control commands: not executed

### Host gate
| Item | Result | Note |
|---|---|---|
| Host Unit Test / Mock NF55G Test | PASS | `python -m unittest discover -s tests -v`, 73 tests OK |

### USB recognition
| Item | Result | Note |
|---|---|---|
| Serial port enumeration | PASS | `COM12` detected |
| Windows device name | PASS | `USB シリアル デバイス (COM12)` |
| PNP Device ID | INFO | `USB\VID_1209&PID_3020&MI_00\6&1AC960C8&0&0000` |
| BOOTSEL / CircuitPython drive | NOT DETECTED | No `RPI-RP2`, `RP2`, `PICO`, or `CIRCUITPY` volume detected |

### USB REPL / command response
| Check | Command / action | Result | Note |
|---|---|---|---|
| REPL prompt check | newline, Ctrl-C, `print('CODEX_REPL_CHECK')` | NO RESPONSE | COM12 opened successfully, but no prompt/output returned |
| Non-destructive ID query | `*IDN?` | NO RESPONSE | No USB command response observed |
| Non-destructive RTC query | `RTC_CHECK?` | NO RESPONSE | No USB command response observed |

### Assessment
- PC-side USB CDC recognition is confirmed on `COM12`.
- Current connected device did not respond as MicroPython/CircuitPython REPL.
- Current connected device did not respond to the planned non-destructive ATE diagnostic commands over USB.
- This repository does not yet contain Pico hardware UART/I2C layer source or a UF2 firmware artifact, so T8 cannot proceed beyond USB recognition/response smoke without a target firmware image or source implementation.

### Next actions
1. Confirm which firmware is currently written to the Pico.
2. If MicroPython/CircuitPython bring-up is intended, verify REPL manually or reflash the intended interpreter/firmware.
3. If NF55G Pico fixture firmware is intended, add/build the Pico hardware UART/I2C layer and USB/ATE transport path before T8 loopback/I2C scan.
4. After a responsive firmware is available, run:
   - I2C scan for DS3231 at `0x68` on I2C0 GP20/GP21.
   - ATE UART GP0/GP1 loopback smoke.
   - NF55G UART GP4/GP5, 38400 bps, 8E1 loopback smoke.

### Open issue references
- OI-13: RTC HAT revision pin mapping, I2C scan `0x68` pending.
- OI-15: Detailed USB CDC/PySide6 protocol deferred.

## 2026-09-02 Pico MicroPython retest

### Scope
- Re-test USB REPL after MicroPython setup.
- Confirm MicroPython identity.
- Run non-destructive I2C scan for RTC bring-up.

### USB recognition
| Item | Result | Note |
|---|---|---|
| Serial port enumeration | PASS | `COM9` detected |
| Windows device name | PASS | `USB シリアル デバイス (COM9)` |
| PNP Device ID | INFO | `USB\VID_2E8A&PID_0005&MI_00\6&86DF33C&0&0000` |
| BOOTSEL / CircuitPython drive | NOT DETECTED | No `RPI-RP2`, `RP2`, `PICO`, or `CIRCUITPY` volume detected |

### MicroPython REPL
| Check | Result | Note |
|---|---|---|
| REPL banner | PASS | `MicroPython v1.28.0 on 2026-04-06` |
| Print smoke | PASS | `print('CODEX_REPL_CHECK')` returned `CODEX_REPL_CHECK` |
| Python identity | PASS | `sys.implementation.name` returned `micropython`; `sys.platform` returned `rp2` |
| Board identity | WARNING | `os.uname().machine` returned `Raspberry Pi Pico with RP2040` |
| CPU frequency | INFO | `machine.freq()` returned `125000000` |

### I2C scan
| Bus / Pins | Result | Note |
|---|---|---|
| I2C0 GP21/GP20, 100 kHz | NOT DETECTED | Scan result `[]`; expected DS3231 `0x68` not found |
| I2C1 GP27/GP26, 100 kHz | NOT DETECTED | Scan result `[]`; secondary check only |

### Assessment
- USB CDC and MicroPython REPL are now confirmed.
- Connected firmware identifies as Raspberry Pi Pico with RP2040, not Pico 2 / RP2350.
- DS3231 RTC at `0x68` was not detected on I2C0 GP20/GP21.
- Do not proceed to deeper T8 UART/I2C validation until board/firmware target is confirmed.

### Next actions
1. Confirm whether the connected board is Pico or Pico 2.
2. If the hardware is Pico 2, reflash the correct Pico 2 MicroPython UF2 before continuing.
3. Confirm RTC HAT/expander wiring and power, then repeat I2C0 scan for `0x68`.
4. After board and RTC detection are correct, proceed to UART loopback smoke checks.

## 2026-09-02 Pico continuation decision and UART init smoke

### Scope
- Continue bring-up on Raspberry Pi Pico / RP2040 for this session.
- Defer Pico 2 / RP2350 hardware debugging to the next session.
- Confirm UART peripheral initialization only; no real NF55G command/control executed.

### Decision
| Item | Result | Note |
|---|---|---|
| Temporary hardware target | ACCEPTED | Proceed with Pico / RP2040 for current MicroPython smoke checks |
| Pico 2 debug | DEFERRED | Pico 2 will be used in the next debug session |

### UART initialization
| Interface | Pins | Settings | Result | Note |
|---|---|---|---|---|
| ATE UART0 | TX GP0 / RX GP1 | 115200 bps, 8N1 | PASS | Peripheral init OK; `any()` returned 0 |
| NF55G UART1 | TX GP4 / RX GP5 | 38400 bps, 8E1 | PASS | Peripheral init OK; `any()` returned 0 |

### Assessment
- Pico / RP2040 MicroPython can initialize both planned UART pin groups.
- NF55G-side UART settings `38400 bps, 8E1` are accepted by MicroPython on this board.
- This is only a peripheral initialization smoke test. Loopback and real NF55G transaction checks remain pending.
- No `FU` or other NF55G control command was transmitted.

### Next actions
1. For UART loopback smoke, connect TX/RX pairs as directed and re-run loopback:
   - ATE side: GP0 <-> GP1.
   - NF55G side: GP4 <-> GP5.
2. Re-check RTC wiring/power and repeat I2C0 GP20/GP21 scan for DS3231 `0x68`.
3. Use Pico 2 / RP2350 in the next debug session before declaring T8 complete for the final hardware target.

## 2026-09-04 Pico 2 MicroPython hardware smoke

### Scope
- Continue T8 hardware smoke after changing hardware target to Raspberry Pi Pico 2.
- Confirm USB CDC / MicroPython REPL.
- Confirm DS3231 I2C detection.
- Confirm UART peripheral initialization only; no loopback wiring and no real NF55G command/control executed.

### USB recognition and MicroPython identity
| Item | Result | Note |
|---|---|---|
| Serial port enumeration | PASS | `COM14` detected |
| REPL banner | PASS | `MicroPython v1.28.0 on 2026-04-06` |
| Print smoke | PASS | `print('CODEX_PICO2_REPL_CHECK')` returned `CODEX_PICO2_REPL_CHECK` |
| Python identity | PASS | `sys.implementation.name` returned `micropython`; `sys.platform` returned `rp2` |
| Board identity | PASS | `os.uname().machine` returned `Raspberry Pi Pico2 with RP2350` |
| CPU frequency | INFO | `machine.freq()` returned `150000000` |

### I2C scan
| Bus / Pins | Result | Note |
|---|---|---|
| I2C0 GP21/GP20, 100 kHz | PASS | Scan result `['0x68']`; DS3231 expected address detected |
| I2C0 GP17/GP16, 100 kHz | NOT DETECTED | Scan result `[]`; alternate check only |
| I2C1 GP27/GP26, 100 kHz | NOT DETECTED | Scan result `[]`; alternate check only |
| I2C1 GP19/GP18, 100 kHz | NOT DETECTED | Scan result `[]`; alternate check only |

### UART initialization
| Interface | Pins | Settings | Result | Note |
|---|---|---|---|---|
| ATE UART0 | TX GP0 / RX GP1 | 115200 bps, 8N1 | PASS | Peripheral init OK; `any()` returned 0 |
| NF55G UART1 | TX GP4 / RX GP5 | 38400 bps, 8E1 | PASS | Peripheral init OK; `any()` returned 0 |

### Assessment
- Final hardware target Pico 2 / RP2350 is now confirmed over MicroPython.
- DS3231 RTC address `0x68` is detected on expected I2C0 GP20/GP21 wiring.
- Planned UART pin groups initialize successfully on Pico 2.
- This is not yet a UART loopback or real NF55G HIL transaction test.
- No `FU` or other NF55G control command was transmitted.

### Next actions
1. Run UART loopback smoke after wiring:
   - ATE side: GP0 <-> GP1.
   - NF55G side: GP4 <-> GP5.
2. Add or prepare the Pico hardware UART/I2C layer source before moving from smoke checks to fixture firmware behavior.
3. Real NF55G HIL remains pending until T8 loopback and hardware layer checks are complete.

## 2026-09-04 Pico 2 SD card hardware recognition

### Scope
- Confirm SD hardware/card recognition before UART loopback.
- Use ADA-5703 SD-only pins: GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI.
- Read-only SPI command checks. No file write, erase, format, or CSV creation executed.

### SPI / SD initialization
| Item | Result | Note |
|---|---|---|
| SPI pins | PASS | SPI0, SCK=GP18, MOSI=GP19, MISO=GP16, CS=GP17 |
| CMD0 | PASS | R1=`0x1`, card entered idle state |
| CMD8 | PASS | R1=`0x1`, tail=`000001aa`, SD v2 voltage pattern accepted |
| ACMD41 | PASS | Ready after 2 loops, last R1=`0x0` |
| CMD58 OCR | PASS | R1=`0x0`, OCR=`c0ff8000`, CCS=True, POWER_UP=True |
| CMD9 CSD | PASS | R1=`0x0`, token=`0xfe`, CSD=`400e00325b59000076997f800a4000ad` |
| CSD version | PASS | CSD v2 |
| Card capacity | INFO | 15918432256 bytes, 15.918 GB decimal, 14.825 GiB |

### Partition / filesystem recognition
| Item | Result | Note |
|---|---|---|
| LBA0 read | PASS | R1=`0x0`, token=`0xfe`, 512 bytes read |
| MBR signature | PASS | `55aa` |
| Partition 1 type | PASS | `0x0c` FAT32 LBA |
| Partition 1 start | INFO | LBA 8192 |
| Partition 1 sectors | INFO | 31082496 |
| FAT boot sector read | PASS | LBA 8192, R1=`0x0`, token=`0xfe`, 512 bytes read |
| FAT boot signature | PASS | `55aa` |
| FAT OEM | INFO | `MSDOS5.0` |
| Bytes per sector | PASS | 512 |
| Sectors per cluster | INFO | 128 |
| Filesystem label | PASS | `FAT32` |

### Assessment
- SD card hardware and card-level SPI recognition are confirmed on the intended GP16-GP19 SD pin set.
- The inserted card is readable as an SDHC/SD v2 card with CSD v2 and roughly 16 GB capacity.
- A valid MBR and FAT32 LBA partition were detected.
- This check did not mount the filesystem and did not create/write/flush a CSV file.
- ADA-5703 GP4/GP5 were physically isolated for this test, satisfying the local hardware condition for SD-only operation on GP16-GP19.
- HW-01 remains open only for final fixture documentation/inspection traceability.

### Next actions
1. Add or select the MicroPython/Pico firmware SD block-device driver path before mount/write testing.
2. Run SD mount, CSV creation, write, flush, close, removal, write-error, and reinitialization checks as the separate SD real-hardware debug checklist.
3. Continue UART loopback after SD mount/write plan is ready.

## 2026-09-04 Pico 2 DS3231 RTC read/write verification

### Scope
- Confirm DS3231 read over I2C0 GP20/GP21.
- Write PC current time to DS3231.
- Read back and verify date/time.

### Read check before write
| Item | Result | Note |
|---|---|---|
| I2C scan | PASS | `['0x68']` |
| Register read 0x00-0x12 | PASS | `42120001010100020b046f00c03f1c88001940` |
| Decoded datetime | INFO | `2000-01-01 00:12:42` |
| Status register 0x0F | INFO | `0x88` |
| Temperature raw 0x11/0x12 | INFO | `0x19 0x40` |

### Write and verify
| Item | Result | Note |
|---|---|---|
| Target PC time | INFO | `2026-09-04 13:22:57` |
| I2C scan before write | PASS | `['0x68']` |
| Before write datetime | INFO | `2000-01-01 00:13:32` |
| Write datetime registers 0x00-0x06 | PASS | Wrote seconds/minutes/hour/day/date/month/year in BCD |
| Clear OSF bit | PASS | Status register changed from OSF set state to `0x08` |
| After write register read 0x00-0x12 | PASS | `58221305040926020b046f00c03f1c08001940` |
| After write datetime | PASS | `2026-09-04 13:22:58` |
| Date verification | PASS | Same date as target |
| Time verification | PASS | +1 second from target, within 0-5 second tolerance |

### Assessment
- DS3231 read path over I2C0 GP20/GP21 is confirmed.
- DS3231 write path is confirmed.
- Read-back verification passed after setting PC current time.
- OI-13 RTC HAT revision pin mapping can be considered hardware-observed for this setup, but do not close the issue without human confirmation.

### Next actions
1. Add this DS3231 access pattern to the Pico hardware RTC layer when implementing fixture firmware.
2. Re-run RTC read/write verification after final fixture firmware is loaded.
3. Continue SD mount/write checks or UART loopback according to the next hardware-debug priority.

## 2026-09-04 Pico 2 fixture RTC layer verification

### Scope
- Add DS3231 access pattern to the Pico hardware RTC layer.
- Re-run read/write verification using the same access pattern on Pico 2 MicroPython.
- This check verifies the hardware device access class behavior, not the final full fixture firmware image.

### Implementation
| Item | Result | Note |
|---|---|---|
| `DS3231I2CDevice` | ADDED | Uses I2C0 SCL=GP21, SDA=GP20, address `0x68` by default |
| BCD datetime read | ADDED | Reads DS3231 registers `0x00` through `0x06` |
| BCD datetime write | ADDED | Writes seconds/minutes/hour/day/date/month/year to registers `0x00` through `0x06` |
| OSF clear | ADDED | Clears oscillator stop flag bit `0x80` in status register `0x0F` after setting time |
| Host fake-I2C tests | PASS | Added read/write/missing-device tests |

### Pico 2 verification
| Item | Result | Note |
|---|---|---|
| I2C scan | PASS | `['0x68']` |
| RTC check | PASS | `True` |
| Before write datetime | INFO | `2026-09-04 13:29:22`, status `0x08` |
| Target datetime | INFO | `2026-09-04 13:29:23` |
| After write datetime | PASS | `2026-09-04 13:29:24`, status `0x08` |
| Date verification | PASS | Same date as target |
| Time verification | PASS | +1 second from target, within 0-5 second tolerance |
| `src/rtc_driver.py` source execution | PASS | Source content executed on Pico 2 REPL; `DS3231I2CDevice()` check/read/write/read-back passed |
| Source execution before write | INFO | `20260904_133031`, status `0x08` |
| Source execution after write | PASS | Target `2026-09-04 13:31:30`; read-back `20260904_133131`, status `0x08` |

### Host test
| Item | Result | Note |
|---|---|---|
| RTC driver unit tests | PASS | 10 tests OK |
| Full host test suite | PASS | 76 tests OK |

### Assessment
- DS3231 hardware access pattern is now represented in the Pico RTC layer.
- The same access pattern was verified on Pico 2 MicroPython against the connected DS3231.
- Full final fixture firmware is not loaded yet; re-run this verification again after `main.py`/transport/scheduler integration is complete.

## 2026-09-04 Pico 2 SD mount/write/readback verification

### Scope
- Continue non-UART real-hardware checks.
- Verify the inserted SD card can be mounted as a FAT filesystem.
- Verify temporary CSV creation, write, flush, close, readback, removal, and unmount.
- Do not exercise card removal or forced write-error handling in this step because those require a separate physical/fault-injection procedure.

### Environment
| Item | Result | Note |
|---|---|---|
| Target board | INFO | Raspberry Pi Pico 2 / RP2350 |
| MicroPython | INFO | v1.28.0 |
| SD pins | INFO | SPI0: GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI |
| Card capacity | INFO | 31,090,688 sectors, 15,918,432,256 bytes |
| Existing card directory listing | INFO | `['System Volume Information']` |

### Verification
| Item | Result | Note |
|---|---|---|
| SD initialization | PASS | SDHC/SD v2 card initialized over SPI0 |
| FAT mount | PASS | Mounted at `/sd` |
| CSV create/write | PASS | Temporary `/sd/CODEX_SD.CSV` created |
| Flush/close | PASS | File flush and close completed without error |
| Readback | PASS | Readback matched written CSV content, `stat_size=37` |
| Temporary file removal | PASS | `/sd/CODEX_SD.CSV` removed |
| Unmount | PASS | `/sd` unmounted |
| Continuous CSV logging smoke | PASS | Temporary `/sd/CODEX_RUN.CSV`; 120 rows plus header, `stat_size=1791`, readback `lines=121` |
| Continuous logging readback | PASS | Last row `119,1961386,357`; readback structure matched expected row count/header/last sequence |
| Continuous logging cleanup | PASS | `/sd/CODEX_RUN.CSV` removed and `/sd` unmounted |

### Assessment
- SD card recognition and FAT filesystem mount/write/readback are confirmed on the intended GP16-GP19 pin set.
- This confirms basic filesystem I/O for SD logger bring-up.
- ADA-5703 GP4/GP5 were physically isolated for this test, satisfying the local hardware condition for SD-only operation on GP16-GP19.
- HW-01 remains open only for final fixture documentation/inspection traceability.

### Remaining non-UART real-hardware checks
1. Continuous logging duration/load check using the final logger queue path.
2. Card removal behavior.
3. Write-error behavior.
4. SD reinitialization behavior after removal/error.
5. Re-run SD logger verification after final fixture firmware is loaded.

## 2026-09-04 Pico 2 DS3231 backup battery verification

### Scope
- Verify DS3231 behavior after installing the RTC backup battery.
- Confirm pre-test reset/oscillator-stop state.
- Set RTC time, power-cycle Pico 2/main power, then confirm the RTC retained and advanced time on battery backup.

### Phase 1: before power cycle
| Item | Result | Note |
|---|---|---|
| I2C scan | PASS | `['0x68']` |
| Before set datetime | INFO | `2000-01-01 00:02:29` |
| Status register | INFO | `0x88`, `OSF=1` |
| Assessment before set | INFO | Reset/oscillator-stop evidence was present, consistent with previous no-battery condition |
| Target datetime | INFO | `2026-09-04 14:22:59` |
| After set datetime | PASS | `2026-09-04 14:23:00` |
| Status after set | PASS | `0x08`, `OSF=0` |

### Phase 2: after power cycle
| Item | Result | Note |
|---|---|---|
| Host read time | INFO | `2026-09-04 14:24:16` |
| I2C scan | PASS | `['0x68']` |
| RTC datetime after power cycle | PASS | `2026-09-04 14:24:18` |
| Status register | PASS | `0x08`, `OSF=0` |
| Reset-like date check | PASS | `False`; RTC did not return to `2000-01-01` |
| Temperature raw | INFO | `19c0` |

### Assessment
- DS3231 backup battery retention is confirmed for this power-cycle check.
- The RTC retained date/time and continued running while Pico 2/main power was off.
- Re-run this check after final fixture firmware is loaded and after any RTC wiring or board-stack change.

## 2026-09-07 Pico 2 SD logger queue-path verification

### Scope
- Continue SD card real-hardware checks before UART loopback / real NF55G HIL.
- Verify SD mount, CSV creation, write, flush, close, readback, and clean reinitialization using a repeatable host-side HIL runner.
- Verify the current `src/logger.py` queue/flush/close path on Pico 2 MicroPython with a Pico SD sink.
- No NF55G command/control was transmitted.
- Card removal and forced write-error injection were not executed in this step because they require separate physical/fault-injection handling.

### Environment
| Item | Result | Note |
|---|---|---|
| Target board | INFO | Raspberry Pi Pico 2 / RP2350 |
| Serial port | INFO | `COM14` |
| MicroPython access | PASS | REPL execution via `scripts/pico_sd_hil.py --port COM14` |
| SD pins | INFO | SPI0: GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI |

### Verification
| Item | Result | Note |
|---|---|---|
| Host logger/SD regression | PASS | `python -m unittest tests.test_logger_sd -v`, 10 tests OK |
| SD mount | PASS | Mounted at `/sd`; directory listing `['System Volume Information']` |
| CSV create/write/flush/close/readback | PASS | Temporary `/sd/CODEX_SD_HIL.CSV`; readback matched `seq,value\n1,abc\n` |
| Logger queue path | PASS | Executed current `src/logger.py` on Pico 2 with `PicoSDSink` |
| Logger continuous queue/readback | PASS | 160 queued records plus CSV header; `lines=161`, `writes=160`, `flushes=5`, `closes=1`, `drops=0` |
| Clean SD reinitialization | PASS | `PicoSDSink.reinit()` after clean close returned `status=OK` |
| Longer logger queue/load check | PASS | `scripts/pico_sd_hil.py --port COM14 --records 2000`; `lines=2001`, `writes=2000`, `flushes=63`, `closes=1`, `drops=0` |
| Card-present probe before removal test | PASS | `scripts/pico_sd_hil.py --port COM14 --interactive-removal`; initial `mount_probe` passed, then stopped at operator card-removal prompt |
| Card removal probe | PASS | With the microSD physically removed, `scripts/pico_sd_hil.py --port COM14 --probe` reported `mount_probe|FAIL|OSError: CMD0 failed: -1`, confirming card non-response detection |
| Reinsert/remount probe | PASS | After reinserting the microSD, `scripts/pico_sd_hil.py --port COM14 --probe` reported `mount_probe|PASS|['System Volume Information']` |
| Post-reinsert write/readback recovery | PASS | `scripts/pico_sd_hil.py --port COM14 --records 160`; CSV readback and logger queue path passed with `lines=161`, `writes=160`, `flushes=5`, `closes=1`, `drops=0` |
| Forced write-error after removal | INCONCLUSIVE | Delayed open-file probe was run after `CODEX_REMOVE_CARD_NOW`; both 1-record and 256-record write/flush attempts returned `status=OK`, `drops=0`, so MicroPython file/FAT buffering did not expose a logger-visible write error in this setup |
| Final post-fault-attempt reinsert/remount probe | PASS | After reinserting the microSD, `scripts/pico_sd_hil.py --port COM14 --probe` reported `mount_probe|PASS` |
| Final post-fault-attempt write/readback recovery | PASS | `scripts/pico_sd_hil.py --port COM14 --records 160`; CSV readback and logger queue path passed with `lines=161`, `writes=160`, `flushes=5`, `closes=1`, `drops=0` |

### Assessment
- The current host logger implementation can run on Pico 2 MicroPython when paired with a Pico SD sink.
- The logger queue path flushed and closed successfully without dropped records in this 160-record smoke/load check.
- The same path also passed a 2000-record load check with no dropped records.
- Physical card removal was detected as SD command failure, and reinsert/remount recovered successfully.
- Forced write-error injection through an already-open MicroPython file did not produce a logger-visible error, even after 256 write/flush attempts following physical removal.
- After the inconclusive write-error attempt, card reinsert/remount and normal logger write/readback recovered successfully.
- This strengthens the SD bring-up beyond the 2026-09-04 direct CSV smoke because it exercises the fixture logger queue semantics.
- Forced write-error behavior remains host-tested only; a lower-level block-device or power-fault procedure is needed before marking the hardware item PASS/FAIL.

### Remaining SD real-hardware checks
1. Define and run a lower-level SD write-error fault-injection procedure.
2. SD reinitialization behavior after confirmed write error.
3. Longer duration/load check if production logging rate or file rollover assumptions change.
4. Re-run SD logger verification after final fixture firmware is loaded.

## 2026-09-07 Pico 2 SD removal/reinsert retest

### Scope
- Re-run SD removal/reinsert checks because the prior physical removal timing was uncertain.
- Confirm baseline SD write/readback before removal.
- Confirm removed-card mount failure.
- Confirm post-reinsert remount and write/readback recovery.
- No NF55G command/control was transmitted.

### Verification
| Item | Result | Note |
|---|---|---|
| Baseline SD write/readback | PASS | `scripts/pico_sd_hil.py --port COM14 --records 160`; `lines=161`, `writes=160`, `flushes=5`, `closes=1`, `drops=0` |
| Card removal detection | PASS | With microSD physically removed, `scripts/pico_sd_hil.py --port COM14 --probe` reported `mount_probe|FAIL|OSError: CMD0 failed: -1` |
| Reinsert/remount probe | PASS | After reinserting the microSD, `scripts/pico_sd_hil.py --port COM14 --probe` reported `mount_probe|PASS` |
| Post-reinsert write/readback recovery | PASS | `scripts/pico_sd_hil.py --port COM14 --records 160`; CSV readback and logger queue path passed with `lines=161`, `writes=160`, `flushes=5`, `closes=1`, `drops=0` |

### Assessment
- The retest confirms removed-card detection through SD command failure.
- Reinsert/remount and normal logger write/readback recovered successfully.
- The first post-reinsert attempt accidentally ran two serial tests in parallel and one failed to open `COM14` with `PermissionError`; this was a host-port contention issue, not an SD hardware failure. The write/readback recovery was then rerun serially and passed.

## 2026-09-07 Pico 2 RS232C 2ch loopback verification

### Scope
- Continue T8 Pico hardware checks after SD/RTC bring-up.
- Verify Waveshare Pico-2CH-RS232 CH0 and CH1 through RS232C-side TX/RX loopback wiring.
- Verify UART0 ATE-side settings and UART1 NF55G-side settings.
- Verify basic channel independence / no observed crosstalk.
- No NF55G unit was connected and no NF55G command/control was transmitted.

### Preconditions
| Item | Result | Note |
|---|---|---|
| Host branch | INFO | `main` |
| Target board | PASS | Raspberry Pi Pico 2 / RP2350 over MicroPython REPL |
| Serial port | INFO | `COM14` |
| RS232C CH0 loopback | DONE | Operator reported TX/RX short completed before test |
| RS232C CH1 loopback | DONE | Operator reported TX/RX short completed before test |
| ADA-5703 GP4/GP5 isolation | ASSUMED | Required by T8 pre-check; 2026-09-04 setup had GP4/GP5 physically isolated, final fixture inspection record still tracked by HW-01 |

### Verification
| Item | Result | Note |
|---|---|---|
| UART HIL runner syntax | PASS | `python -m py_compile scripts\pico_uart_hil.py` |
| MicroPython identity | PASS | `micropython; rp2; Raspberry Pi Pico2 with RP2350` |
| UART0 init | PASS | `UART(0)`, GP0=TX, GP1=RX, 115200 bps, 8N1 |
| UART1 init | PASS | `UART(1)`, GP4=TX, GP5=RX, 38400 bps, 8E1 |
| CH0 loopback smoke | PASS | `tx=32`, `rx=32`, `mismatch=0`, `crosstalk=0` |
| CH1 loopback smoke | PASS | `tx=32`, `rx=32`, `mismatch=0`, `crosstalk=0` |
| CH0 loopback 256-byte pattern | PASS | `tx=256`, `rx=256`, `mismatch=0`, `crosstalk=0` |
| CH1 loopback 256-byte pattern | PASS | `tx=256`, `rx=256`, `mismatch=0`, `crosstalk=0` |
| Dual-channel stress | PASS | `frames=100`, CH0 `3500` bytes, CH1 `3500` bytes, no mismatch reported |
| 512-byte single-write observation | FAIL / LIMIT OBSERVED | CH0 `tx=512`, `rx=290`; CH1 `tx=512`, `rx=289`; stress frames still passed. Treat as MicroPython/UART buffering limit for this HIL method, not a D6 protocol failure. |

### Assessment
- Both RS232C channels initialized with the project-intended pin mapping and serial settings.
- RS232C-side loopback passed on both CH0 and CH1 at smoke, 256-byte pattern, and 100-frame stress levels.
- No crosstalk was observed in the passing loopback checks.
- The 512-byte single-write attempt exceeded the reliable single-chunk behavior of this MicroPython REPL HIL path; fixture firmware should avoid relying on large undrained UART writes and should keep protocol frame handling byte/packet oriented.
- Real NF55G HIL remains pending until the UART hardware layer / fixture firmware path is ready and safety procedure is reviewed.

## 2026-09-07 Pico 2 pre-NF55G readiness check

### Scope
- Complete all practical checks available before a real NF55G unit is connected.
- Add host-testable Pico hardware/transport layer skeletons and local command routing.
- Re-run RTC, SD, and UART HIL checks serially on `COM14`.
- Do not execute `NF_COMM_CHECK?` against hardware and do not transmit any NF55G command/control.

### Implementation
| Item | Result | Note |
|---|---|---|
| ATE UART transport skeleton | ADDED | `src/ate_uart.py`; UART0 byte transport, GP0/GP1, 115200 bps, 8N1 |
| NF55G UART transport skeleton | ADDED | `src/nf55_uart.py`; UART1 byte transport, GP4/GP5, 38400 bps, 8E1 |
| Local diagnostics skeleton | ADDED | `src/diagnostic.py`; fixture self-check, comm status, retry count helpers |
| Fixture bootstrap skeleton | ADDED | `src/main.py`; local component wiring without NF55G command transmission at init |
| ATE command parser | ADDED | `src/command_parser.py`; local/logger/RTC/diagnostic/control classification and `FW_UPDATE` forbidden category |
| RTC HIL runner | ADDED | `scripts/pico_rtc_hil.py`; DS3231 scan/check/read through MicroPython REPL |

### Verification
| Item | Result | Note |
|---|---|---|
| Host unit/integration tests | PASS | `python -m unittest discover -s tests -v`, 91 tests OK |
| Source syntax check | PASS | `python -m py_compile` for new hardware/parser/diagnostic/bootstrap modules and HIL scripts |
| RTC HIL | PASS | `scripts/pico_rtc_hil.py --port COM14`; DS3231 `0x68`, `check=True`, datetime `20260907_093839`, status `0x08` |
| SD HIL | PASS | `scripts/pico_sd_hil.py --port COM14 --records 160`; CSV readback and logger queue path passed with `lines=161`, `writes=160`, `flushes=5`, `closes=1`, `drops=0` |
| UART HIL | PASS | `scripts/pico_uart_hil.py --port COM14 --bytes 256 --frames 100`; CH0/CH1 loopback and stress passed, crosstalk `0` |
| `FW_UPDATE` local routing | PASS | Host tests confirm `FW_UPDATE` returns `ERR:FU_DISABLED` without requiring NF55G transport |
| Control command before NF55G connection | PASS | Host tests confirm control routing returns `ERR:NF55G_NOT_CONNECTED` when protocol is unavailable |
| `NF_COMM_CHECK?` before NF55G connection | PASS | Host tests confirm `ERR:NF55G_NOT_CONNECTED` |

### Assessment
- NF55G実機なしで進められる host-side implementation and Pico hardware HIL checks are complete for the current MicroPython bring-up path.
- RTC, SD, and RS232C 2ch loopback have been rechecked on the actual Pico 2 setup.
- The fixture still does not contain a final production firmware image/scheduler; `src/main.py` is a bootstrap skeleton and must be revisited when the firmware placement/build path is selected.
- Real NF55G HIL must wait for a real NF55G unit and a safety-reviewed connection procedure.

### Remaining before / at Real NF55G HIL
1. Record the final fixture ADA-5703 GP4/GP5 physical isolation method and inspection evidence for HW-01.
2. Select final firmware placement/build path and rerun RTC/SD/UART through that final image.
3. Connect real NF55G only after the above and start with read-only/non-control HIL checks.
