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

## 2026-09-09 Pico 2 identity, deployed files, and isolation confirmation

### Scope and setup
- Record time: 2026-09-09 17:36 JST (08:36 UTC), immediately after inspection.
- Repository HEAD: `fca57e6cca82576f312de8d33761eeb6d7954b8d`; local development-environment changes and the inventory script were uncommitted.
- USB port: COM14; VID:PID `2E8A:0005`; serial `2D35A1E11AC125E3`.
- User explicitly confirmed that ADA-5703 GP4/GP5 are currently physically cut/disconnected.
  This is operator-reported evidence, not an agent visual inspection or continuity measurement.
  Exact cut locations, photographs, and final fixture inspection record were not provided; HW-01 remains open.
- Other wiring and whether a real NF55G is physically attached were not independently checked.
- Read-only inventory executed from host into RAM; no file placement, flash, SD mount,
  UART/I2C/SPI initialization, or NF55G command was performed by the inspection script.
- `resume` avoids mpremote's automatic soft reset. Entering REPL interrupts any running application;
  this inspection did not restart application code.

### Executed command
```bat
.venv\Scripts\python.exe -B -m mpremote connect COM14 resume run scripts\pico_inventory.py
```

### Raw response (exit code 0)
```text
PICO_INVENTORY_BEGIN
IMPLEMENTATION|(name='micropython', version=(1, 28, 0, ''), _machine='Raspberry Pi Pico2 with RP2350', _mpy=7942, _build='RPI_PICO2', _thread='unsafe')
VERSION|3.4.0; MicroPython v1.28.0 on 2026-04-06
PLATFORM|rp2
UNAME|(sysname='rp2', nodename='rp2', release='1.28.0', version='v1.28.0 on 2026-04-06 (GNU 14.2.0 MinSizeRel)', machine='Raspberry Pi Pico2 with RP2350')
UNIQUE_ID|2d35a1e11ac125e3
FREQ|150000000
CWD|/
SYS_PATH|['', '.frozen', '/lib']
DIR|/sd
PICO_INVENTORY_END
```

### Assessment and next action
- PASS: USB REPL and Pico 2 / RP2350 MicroPython v1.28.0 identity; CPU frequency 150 MHz.
- INFO: root contains only `/sd`; no root `boot.py`, `main.py`, or `/lib` directory.
  No deployed fixture source files were found in the inspected filesystem scope.
  `/sd` contents and firmware-frozen modules were not inspected; an `/sd` directory alone does not prove an SD mount.
- INFO: current GP4/GP5 disconnection confirmed by user; final fixture inspection traceability remains HW-01.
- No product PASS/FAIL assessment, NF55G control or FU transmission, or cache modification.
  This inventory does not exercise the firmware FU-blocking path.
- Next: Pico-only RTC/SD checks, then UART loopback after loopback wiring and NF55G disconnection are confirmed.
  Final firmware placement/scheduler integration and final-firmware HIL remain pending.

## 2026-09-10 SD initialization repeat check

- Completed by 08:16:53 JST, COM14, normal permissions; same Pico/SD setup as the preceding checks.
- Requested the card remain inserted throughout. No removal, power cycle, or firmware reset was requested or performed by the agent.
  This tests repeated software initialization, not cold power-on behavior.
- Executed sequentially: `.venv\Scripts\python.exe -B scripts\pico_sd_hil.py --port COM14 --probe`
  three times, then `.venv\Scripts\python.exe -B scripts\pico_sd_hil.py --port COM14 --records 160`.
- All four processes exited 0. Local raw captures: `temp/sd_probe_20260910_1.txt`,
  `temp/sd_probe_20260910_2.txt`, `temp/sd_probe_20260910_3.txt`, `temp/sd_basic_20260910.txt` (git-ignored).
- Each probe reported the same result payload:
```text
CODEX_SD_HIL_BEGIN
mount_probe|PASS|['System Volume Information', '00000001406554.csv', '00000001470803.csv', '00000002075576.csv', '00000002204345.csv']
CODEX_SD_HIL_END
```
- Subsequent basic I/O result payload:
```text
CODEX_SD_HIL_BEGIN
mount|PASS|['System Volume Information', '00000001406554.csv', '00000001470803.csv', '00000002075576.csv', '00000002204345.csv']
csv_create_write_flush_close_readback|PASS|'seq,value\n1,abc\n'
logger_queue_flush_close_readback|PASS|lines=161, writes=160, flushes=5, closes=1, drops=0
sd_reinit_after_clean_cycle|PASS|status=OK
CODEX_SD_HIL_END
```
- PASS: three consecutive mount/unmount probes, CSV exact readback, 160-record logger path,
  and clean-cycle reinitialization. No CMD0 anomaly recurred in this run.
- The previous `CMD0 failed: 31` remains unexplained; these passes do not establish contact failure
  as the cause or validate first initialization after power-on. No Open Issue was closed.
- Existing HIL code was used without modification; no NF55G/FU command, cache operation,
  or product PASS/FAIL assessment. Normal completion removes test CSVs and unmounts the card.

## 2026-09-10 UART two-channel loopback verification

- Execution: approximately 08:05-08:07 JST, COM14, normal permissions.
- Repository HEAD: `fca57e6cca82576f312de8d33761eeb6d7954b8d`; staged development environment and earlier hardware log changes were preserved.
- Pico identifies as MicroPython / rp2 / Raspberry Pi Pico2 with RP2350.
  Firmware version was v1.28.0 in the preceding inventory; this UART script does not re-read its version.
- Setup: operator reports both channels (user labels Ch1/Ch2) shorted for loopback;
  ADA-5703 GP4/GP5 physically cut/disconnected per preceding operator confirmation.
  Script labels are CH0=UART0 GP0/GP1 and CH1=UART1 GP4/GP5.
- The prior turn's execution session was no longer available and its result could not be recovered.
  No PASS is assigned to that lost run; this entry records the new completed run.

Command:
```bat
.venv\Scripts\python.exe -B scripts\pico_uart_hil.py --port COM14 --bytes 256 --frames 100 > temp\uart_hil_20260910.txt 2>&1
```

Result: exit code 0. Result payload below omits only REPL transport bytes;
the local raw capture is `temp/uart_hil_20260910.txt` (git-ignored).

```text
CODEX_UART_HIL_BEGIN
stress_progress|INFO|frames_done=10
stress_progress|INFO|frames_done=20
stress_progress|INFO|frames_done=30
stress_progress|INFO|frames_done=40
stress_progress|INFO|frames_done=50
stress_progress|INFO|frames_done=60
stress_progress|INFO|frames_done=70
stress_progress|INFO|frames_done=80
stress_progress|INFO|frames_done=90
stress_progress|INFO|frames_done=100
micropython_identity|PASS|micropython; rp2; Raspberry Pi Pico2 with RP2350
uart0_init_115200_8n1|PASS|GP0=TX, GP1=RX
uart1_init_38400_8e1|PASS|GP4=TX, GP5=RX
uart0_ch0_loopback|PASS|tx=256, rx=256, mismatch=0, crosstalk=0
uart1_ch1_loopback|PASS|tx=256, rx=256, mismatch=0, crosstalk=0
dual_channel_stress|PASS|frames=100, ch0_bytes=3500, ch1_bytes=3500
CODEX_UART_HIL_END
```

- PASS: UART0 115200 bps 8N1 and UART1 38400 bps 8E1 initialize and loop back exactly.
- PASS: 256-byte initial patterns match, other-channel received bytes are zero.
- PASS: 100 frames per channel, 3500 bytes per channel, tested alternately (not simultaneous saturation).
- Both UART peripherals are deinitialized by the script on normal completion.
- Test patterns only: no NF55G protocol/control/FU command was generated. No product PASS/FAIL,
  cache behavior, or firmware FU-blocking path was evaluated.
- Scope is REPL HIL, not final fixture firmware. No firmware file placement or runtime source change.
- Remaining: final fixture isolation inspection traceability (HW-01), final firmware integration,
  final-firmware RTC/SD/UART tests, and previously observed SD initialization anomaly.
  Open Issues remain open.

## 2026-09-09 RTC/SD rerun - initial COM14 access failure

- Time: approximately 17:38 JST (08:38 UTC).
- Setup: same Pico 2 / MicroPython v1.28.0 as the preceding inventory;
  user reports both channels (user labels Ch1/Ch2) shorted for loopback.
  GP4/GP5 isolation remains user-confirmed as above; no new visual inspection.
- Command: `.venv\Scripts\python.exe -B scripts\pico_rtc_hil.py --port COM14`.
- Both normal and user-authorized elevated execution failed at serial port open, exit code 1:
  `could not open port 'COM14': PermissionError(13, ..., None, 5)` (access denied).
- Port enumeration still identifies COM14, VID:PID `2E8A:0005`, serial `2D35A1E11AC125E3`.
- Result: RTC NOT RUN; SD NOT RUN. This is a host port access failure, not an RTC/SD hardware failure.
  Another program holding the port is possible but not established.
- Requested the user disconnect any COM14 serial monitor/REPL before retrying.
  No RTC/SD operation or NF55G/FU command was transmitted by these failed attempts.

### Retry after operator released COM14

- Operator reported the COM14 connection was disconnected; the same RTC command then succeeded under normal permissions.
  This is consistent with port contention, although the previous owning process was not identified.
- RTC observation: 2026-09-09 17:39:26 as read from DS3231. Same Pico 2 / RP2350,
  MicroPython v1.28.0 and repository revision as the preceding inventory; no firmware placement.
- RTC uses I2C0 GP20/GP21 at 100 kHz; SD uses SPI0 GP16-GP19 with GP17 CS.
- User also confirmed the microSD card was inserted after the first SD initialization failure.
- Subsequent operator clarification: the card was physically removed and reinserted once
  between the initial `CMD0 failed: 31` and recovery. Recovery therefore followed physical
  intervention, not merely a software retry. Contact quality is a candidate cause, but
  contact changes and card-state changes from reinsertion have not been distinguished.
- USB REPL scripts executed sequentially. Ch1/Ch2 loopback wiring is operator-reported;
  UART loopback was outside this RTC/SD execution scope.

| Execution | Result | Evidence |
|---|---|---|
| RTC scan/check/read | PASS | Address `0x68`, check `True`, datetime `20260909_173926`, status `0x08`; exit 0 |
| SD basic 160-record first attempt | FAIL at initialization | `OSError: CMD0 failed: 31`; exit 1; CSV operations not reached |
| SD mount-only probe | PASS | Existing directory listing returned; exit 0 |
| SD basic 160-record retry | PASS | CSV exact readback, logger 161 lines including header, 160 writes, 5 flushes, 1 close, 0 drops; clean reinit OK; exit 0 |

Commands (all successful runs under normal permissions):
```bat
.venv\Scripts\python.exe -B scripts\pico_rtc_hil.py --port COM14
.venv\Scripts\python.exe -B scripts\pico_sd_hil.py --port COM14 --records 160
.venv\Scripts\python.exe -B scripts\pico_sd_hil.py --port COM14 --probe
.venv\Scripts\python.exe -B scripts\pico_sd_hil.py --port COM14 --records 160
```

Raw result payloads (REPL transport control bytes omitted):
```text
CODEX_RTC_HIL_BEGIN
micropython_identity|PASS|micropython; rp2; Raspberry Pi Pico2 with RP2350
i2c0_gp20_gp21_scan|PASS|['0x68']
ds3231_check|PASS|True
ds3231_read_datetime|PASS|20260909_173926, status=0x08
CODEX_RTC_HIL_END

CODEX_SD_HIL_BEGIN
EXCEPTION|FAIL|OSError: CMD0 failed: 31
CODEX_SD_HIL_END

CODEX_SD_HIL_BEGIN
mount_probe|PASS|['System Volume Information', '00000001406554.csv', '00000001470803.csv', '00000002075576.csv', '00000002204345.csv']
CODEX_SD_HIL_END

CODEX_SD_HIL_BEGIN
mount|PASS|['System Volume Information', '00000001406554.csv', '00000001470803.csv', '00000002075576.csv', '00000002204345.csv']
csv_create_write_flush_close_readback|PASS|'seq,value\n1,abc\n'
logger_queue_flush_close_readback|PASS|lines=161, writes=160, flushes=5, closes=1, drops=0
sd_reinit_after_clean_cycle|PASS|status=OK
CODEX_SD_HIL_END
```

### Limits and remaining work
- Basic RTC read and SD I/O are verified through REPL HIL. The initial SD CMD0 response anomaly
  remains unexplained; recovery after the operator's card reinsertion is not evidence of a permanent fix.
  Record recurrence and investigate card/connection/initialization behavior if it returns.
- RTC set/write, reference-clock accuracy, battery retention, long-duration SD logging,
  card removal, and low-level write-error injection were not tested in this run.
- The successful SD script removes its temporary test CSV files and unmounts `/sd` on completion.
- No NF55G/FU command was sent. No final fixture firmware, production communication timing,
  firmware FU-blocking path, or product PASS/FAIL was assessed. No Open Issue was closed.
- Next: UART loopback verification using confirmed channel mapping, followed by final firmware integration/testing.


## 2026-09-10: Integrated Pico deployment

Deployed 23 Python files with matching SHA-256; real RTC/SD smoke, 64-row CSV readback after remount, RAM ATE CRLF/FU rejection, and scheduler run/stop passed. NF55G disconnected; observed NF55G TX zero. Device left in REPL; cold boot and physical ATE/NF55G tests pending.

Evidence and limitations: [Pico deployment](Pico_Deployment_20260910.md). Reproducible finite check: `scripts/pico_runtime_smoke.py`.


## 2026-09-10: Operator power-cycle check

After the operator reported power cycling, COM14 was inspected without a soft
reset or SD reinitialization. Passive USB capture was empty. Ctrl-C produced a
traceback through `/main.py` -> `src.main.main()` -> `run()` -> `service_once()`
-> ATE receive pumping, proving automatic application startup reached the loop.
This KeyboardInterrupt was deliberately generated by the inspection.

Cold-start SD verification FAILED: `/sd` was empty and statvfs reported the
internal 3 MiB filesystem (768 x 4096 bytes), not the SD filesystem. Reading the
previous CSV returned ENOENT. The startup code catches mount failures, so the
original SD initialization exception was not retained; CMD0 failure or contact
trouble cannot be concluded from this check.

An explicit manual PicoSDSink mount retry then succeeded (15,910,043,648 bytes).
The probe was unmounted and a fresh FixtureApp was created: SD status OK,
RTC_CHECK OK, RTC 20260910_094726. Its run loop was started and the USB connection
closed without interrupting it. No NF55G command was requested by the inspection.
Current state: application running after manual restart, RTC/SD OK at restart.
Cold-start SD initialization remains unresolved; successful retry does not pass
the cold-start requirement. No runtime source or device files were changed.

Local evidence: `temp/pico_power_on_20260910.log`,
`temp/pico_sd_restart_20260910.log`. No Host tests rerun for this hardware-only
inspection and documentation update.


## 2026-09-10: SD startup diagnostics

Added RAM-only first-startup SD stage/error snapshot; no automatic retry, added delay or ATE format change. Soft-boot mount passed; cold-power failure cause remains unconfirmed. Host/Mock: 138 tests passed. See [investigation](SD_Startup_Investigation.md).


## 2026-09-10: Diagnostic cold-power failure reproduced

Initial RAM snapshot: CARD_INIT, MOUNT_ERR, mounted=False, OSError(CMD0 failed: 31), hardware initialization elapsed 126 ms. Captured before reset/reinit. Manual retry in the same powered state returned CMD0=1 and mounted SD successfully. Original failure snapshot retained. Application restarted, SD/RTC OK, receive loop running. NF55G commands were not requested. Root cause remains unconfirmed; see [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: Controlled SD cold-start comparison prepared

Added opt-in startup delay / CS-before-SPI settings (normal defaults unchanged) and temporary `firmware/sd_startup_probe.py`. Pico /main.py now selects DELAY_ONLY: 500 ms wait, original CS order, one CMD0 attempt. Cold-power result pending; normal entry point must be restored after investigation. Host/Mock: 139 tests passed. See [experiment matrix](SD_Startup_Investigation.md).

## 2026-09-10 SPI Initialization Correction: 100kHz + MISO PULL_UP

### Problem Statement
- 2026-09-04 and 2026-09-10 cold-boot diagnosis: SD card initialization failed with `CMD0 failed: 31` (R1 response = 0x1F, multiple error bits set).
- Soft reboot diagnosis (REPL after successful main): CMD0 returned 0xff (no response), then subsequent cold-boot attempts confirmed SD presence but CMD0 behavior remained inconsistent.
- Root cause hypothesis: SPI initialization speed and MISO signal integrity.
- Hardware: ADA-5703 PiCowbell (GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI).

### Analysis
| Issue | Evidence | Impact |
|-------|----------|--------|
| Initial baudrate mismatch | Implementation was 400 kHz; RW11用電源通信仕様書 r1 specifies ~100 kHz for CMD0 phase | Signal quality degradation; timing-sensitive SD response loss |
| MISO line signal | Diagnostic C showed MISO initial value = 0 (Low); expected = 1 (High) | Possible missing external pullup on ADA-5703 MISO; internal Pico pullup insufficient |
| Phase 1 → Phase 2 transition | Direct 400 kHz → 25 MHz transition without 100 kHz intermediate phase | Violates SD bus voltage/timing transient safety margin |

### Implementation (147 host tests PASS)

#### Change 1: SDCard.__init__() baudrate parameter
```python
# Before
def __init__(self, spi, cs, baudrate=400000, clock=None):
# After
def __init__(self, spi, cs, baudrate=100000, clock=None):
```
**File**: `src/sd_card.py:16`
**Impact**: Initialization sequence now runs at 100 kHz, matching specification Phase 1; high-speed 25 MHz used only after card init complete.

#### Change 2: PicoSDSink.mount() - MISO pullup
```python
# Before
spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))

# After
miso = Pin(16, Pin.IN, Pin.PULL_UP)
spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=miso)
```
**File**: `src/sd_sink.py:248-250`
**Impact**: Pico internal pullup now active on MISO, ensuring High level when SD not driving; addresses ADA-5703 external pullup gap.

#### Change 3: Diagnostic probe consistency
```python
# Before
card.init_spi(400000)

# After
card.init_spi(100000)

# Also
report['baudrate'] = 100000  # (was 400000)
```
**File**: `firmware/sd_startup_probe.py:73, 31`
**Impact**: Diagnostic CMD0 probe now runs at same speed as production; report records actual baudrate for audit trail.

### Host Validation
| Check | Result | Note |
|-------|--------|------|
| Unit test suite | PASS | 147/147 tests including new Pin.PULL_UP mocking |
| SD card initialization | PASS | Simulated SPI with 100 kHz init rate |
| Diagnostic multi-attempt | PASS | Probe logic and R1 bit-name recording verified |
| Mock NF55G protocol | PASS | No regression in command/response cycle |

### Deployment (Pico 2)
| File | Source → Pico 2 Destination | Mode |
|------|-----------|------|
| `firmware/sd_startup_probe.py` | → `/main.py` | Replace (diagnostic run) |
| `src/sd_card.py` | → `/src/sd_card.py` | Copy (modified) |
| `src/sd_sink.py` | → `/src/sd_sink.py` | Copy (modified) |
| `src/__init__.py` | → `/src/__init__.py` | Copy (all other files in src/) |
| (All other `/src/` files) | → `/src/` | Copy unchanged |

**Pico 2 final folder structure after deployment:**
```
/
├── main.py                 ← firmware/sd_startup_probe.py
├── src/
│   ├── __init__.py
│   ├── sd_card.py          ← src/sd_card.py (100kHz + imports)
│   ├── sd_sink.py          ← src/sd_sink.py (PULL_UP + imports)
│   ├── pico_clock.py
│   ├── main.py
│   ├── logger.py
│   └── ... (other modules)
```

### Expected Improvement
| Before Fix | After Fix | Indicator |
|-----------|-----------|-----------|
| CMD0 → 0x1F / 0xff | CMD0 → 0x01 (Idle) | Successful initialization |
| Cold boot failure | Cold boot success | `mounted: True, stage: READY` |
| MISO always Low | MISO High when idle | Signal integrity confirmed |
| Phase 1 timing risk | Phase 1 at 100 kHz | Specification compliance |

### Next Actions (Hardware Validation)
1. **Phase 1 (Basic)**: REPL CMD0 test at 100 kHz with PULL_UP → check response (expect 0x01, not 0xff/0x1F).
2. **Phase 2 (Cold Boot)**: Power cycle Pico 2 → check SD mount success (`mounted: True`, `stage: READY`).
3. **Phase 3 (CASE patterns)**: Run 5x CASE variants (BASELINE, DELAY_ONLY, CS_ONLY, DELAY_AND_CS, CMD0_NO_PRE_FF) with cold-boot to identify if one CASE is preferred.
4. **Phase 4 (PULL_UP effect)**: Optional MISO voltage measurement to confirm pullup is effective.

### Risk Assessment
- **BACKWARD COMPAT**: Default `baudrate=100000` is a breaking change for any external code that relies on 400 kHz init. Mitigated: internal to fixture firmware; no external dependency.
- **PRODUCTION TIMING**: 100 kHz init phase may increase cold-boot latency by ~10–20 ms. Acceptable because SD mount is not time-critical in production.
- **HARD RESET EDGE**: If 0x1F persists after this fix, root cause is not SPI speed/MISO level; next hypothesis should address power-supply sequencing or SD card state retention across soft reboot (see Open Issues).

### References
- Spec: RW11用電源通信仕様書 r1 (initial 100 kHz requirement)
- Diagnostic: [SD Startup Investigation](SD_Startup_Investigation.md)
- Code: Git commits `a0cefd7`, `8cb8fd6`
- Host tests: 147/147 PASS
- Hardware readiness: Pending Phase 1–4 validation



## 2026-09-10: DELAY_ONLY cold start failed; CS_ONLY selected

500 ms added wait with original CS/SPI order still returned CMD0 failed: 31, CARD_INIT, elapsed 625 ms. First-boot evidence captured before reset/reinit. Switched temporary Pico entry to CS_ONLY (0 ms added wait; GP17 High before SPI creation). CS_ONLY cold-power result pending. See [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: CS_ONLY cold start failed; combined condition selected

CS High before SPI creation with no added wait returned CMD0 failed: 31, CARD_INIT, elapsed 126 ms. Captured before reset/reinit. Temporary Pico entry now selects DELAY_AND_CS (500 ms wait, then CS High, then SPI creation). Combined cold-power result pending. No runtime logic change or Host test rerun for this case selection. See [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: SD startup comparison completed without improvement

DELAY_AND_CS cold start: CMD0 failed: 31, CARD_INIT, elapsed 627 ms; captured before reset/reinit. Baseline, delay-only, CS-only and combined cases all exhibited the same CMD0 failure. Tested 500 ms wait and CS-before-SPI are not established fixes. Restored normal firmware/main.py to Pico /main.py, retaining diagnostic support. Root cause remains open. No Host tests rerun for hardware measurement and entry restoration; last suite 139 passed. See [full evidence](SD_Startup_Investigation.md).


## 2026-09-10: Chat CMD0 diagnostic handoff validated

Corrected pre-mount diagnostic contamination: preserve first baseline mount failure, then probe only an unmounted CMD0 failure, without auto-remount. Bounded repeated-CMD0 method; actual regression tests replace synthetic assertions. Host/Mock 143 passed; Pico warm CMD0 10/10 idle responses, SD remount and existing 65-line CSV readback passed. Temporary diagnostic boot deployed for cold-power evidence; root cause unresolved. See [handoff validation](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: Cold first failure followed by successful diagnostic CMD0

BASELINE first mount failed at CMD0=31 (CARD_INIT, MOUNT_ERR, elapsed 19 ms). Automatic post-failure raw probe recorded 10/10 CMD0=1 replies; original failure remained preserved, with no automatic SD remount. Probe reconstructs SPI and supplies extra idle clocks, so this is not proof of a simple one-command retry fix. Captured before host reset/reinit. See [handoff cold evidence](SD_CMD0_Chat_Handoff_Validation.md). No source/device changes or Host tests for this hardware measurement.


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


## 2026-09-10: Optional voltage measurement omitted by user; next test

User explicitly elected not to perform Phase 4 MISO voltage measurement.
It is omitted by decision, not a failed or pending requirement of the SD task.
SD deployment, five-CASE cold checks and normal baseline restoration are complete.
No physical voltage/signal-integrity result or clock-only root cause is claimed.

Next step is final-firmware physical ATE UART integration verification, before
real NF55G transactions. Prior RAM-peer CRLF/FU tests and REPL UART loopback
are not evidence of the final physical ATE receive/scheduler path. Confirm the
current ATE RS232 adapter COM port and NF55G disconnection before executing.
USB COM14 is Pico REPL, not the ATE UART port. Use UART0 GP0/GP1, 115200 8N1,
through the RS232 interface. Initial local commands: *IDN?, RTC_CHECK?,
SD_STATUS?, FW_UPDATE (must return ERR:FU_DISABLED; never send FU to NF55G).
Keep existing GP4/GP5 isolation requirement in effect.
After required final-firmware checks and T9 entry conditions are satisfied,
proceed to D1 STATUS_REFRESH/cache queries then D5 INFO_REFRESH/cache queries.
No product communication or device operation was performed in this planning
step; no Open Issue closed. Refer to Test_Specification.md and
NF55G_HIL_Preparation.md for remaining entry conditions.


## 2026-09-10: Paused pending ATE RS232C preparation

User confirmed ATE connects to Pico UART0 and NF55G remains disconnected.
PC serial enumeration found only Pico USB REPL COM14 (VID:PID 2E8A:0005);
no separate ATE RS232 adapter COM port was available. User requested stop
while preparing ATE RS232C equipment. No physical ATE test was executed.
Pico normal baseline firmware was left running; SD verification is complete.
Resume with PC-side ATE adapter identification and physical UART0 integration
checks after equipment is ready. Optional MISO voltage measurement is omitted
by user decision. No new hardware operations at this pause/commit step.
