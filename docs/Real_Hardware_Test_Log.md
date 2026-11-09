# Real Hardware Test Log
Revision: Rev.0-draft

## 2026-09-16 Pico 2 SD / RTC / RS232C communication test

### Scope
- Run the SD card, DS3231 RTC, and two-channel RS232C HIL checks on COM14.
- Do not connect to NF55G or transmit any NF55G command/control.

### Results
| Interface | Result | Details |
|---|---|---|
| microSD | PASS after retry | First `--records 160` run timed out waiting for a data token. A non-writing mount probe passed, then the serial retry passed: CSV readback, 160 logger records, 5 flushes, 1 close, 0 drops, and clean reinit. |
| DS3231 RTC | PASS | I2C0 GP20/GP21 scan found `0x68`; `check=True`; read `2026-09-16 17:14:43`, status `0x08`. |
| RS232C CH0 / UART0 | FAIL | Initialization passed at GP0/GP1, 115200 bps, 8N1, but loopback received 0/256 bytes. |
| RS232C CH1 / UART1 | FAIL | Initialization passed at GP4/GP5, 38400 bps, 8E1, but loopback received 0/256 bytes. |

### Assessment
- Pico 2 / RP2350 and the SD/RTC paths are operational in this run.
- RS232C transmit-side initialization is operational, but receive loopback was not observed on either channel. Confirm the RS232C-side TX/RX loopback wiring before repeating the test; this result is not evidence of NF55G communication failure.
- No NF55G unit was connected and no NF55G command/control was transmitted.

## 2026-09-16 Pico 2 RS232C loopback retest after wiring correction

### Verification
| Item | Result | Details |
|---|---|---|
| MicroPython identity | PASS | `micropython; rp2; Raspberry Pi Pico2 with RP2350` |
| UART0 / CH0 | PASS | GP0/GP1, 115200 bps, 8N1; 256/256 bytes, mismatch 0, crosstalk 0 |
| UART1 / CH1 | PASS | GP4/GP5, 38400 bps, 8E1; 256/256 bytes, mismatch 0, crosstalk 0 |
| Dual-channel stress | PASS | 100 frames; CH0 3500 bytes and CH1 3500 bytes |

### Assessment
- The RS232C loopback wiring correction resolved the previous receive-zero result.
- This test used loopback only. No NF55G unit was connected and no NF55G command/control was transmitted.

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


## 2026-09-17: Physical ATE UART0 check via COM5

PC adapter: Elecom USB-Serial Converter, VID:PID=056E:5004, COM5.
User identified connection to Pico UART0. Settings: 115200 baud, 8N1,
no software/hardware flow control, ASCII requests/responses terminated CRLF.
Pico USB REPL COM14 was not opened; no reset, deployment, or runtime interruption.
Last operator NF55G state was disconnected (2026-09-10); physical connection
was not independently reverified today. Only local commands below were sent.

First *IDN? request (TX 2a49444e3f0d0a) returned ERR:ASCII CRLF
(RX 4552523a41534349490d0a). Stopped initial sequence. One explicit ID recheck
returned NF55G_PICO_FIXTURE,Rev.0 CRLF without resetting Pico. Initial anomaly
cause remains unconfirmed; residual input is a hypothesis, not an established
cause. Do not characterize this session as an error-free first connection.

Subsequent validation:
- *IDN? -> NF55G_PICO_FIXTURE,Rev.0
- RTC_CHECK? -> OK
- SD_STATUS? -> OK
- FW_UPDATE -> ERR:FU_DISABLED
- Split '*IDN?\r' then '\n': no response during 100 ms read before LF;
  complete expected ID response after LF.
- 20 sequential ID requests: 20 exact expected CRLF responses.

Raw evidence:
- temp/ate_uart0_com5_20260917_120612.jsonl (initial error)
- temp/ate_uart0_com5_recheck_20260917_120638.json
- temp/ate_uart0_com5_validation_20260917_120707.jsonl

Physical ATE local command path demonstrated; initial ASCII anomaly remains
for repeat connection/power-cycle investigation if it recurs. No NF55G refresh,
control or FU frame requested. NF55G TX was not physically monitored, so zero
wire traffic is not claimed. No T9 product communication or product PASS/FAIL.
COM5 closed after tests; Pico normal runtime not interrupted. No source/device
files changed; Host/Mock not rerun for this hardware-only test (last 147 passed).


## 2026-09-17: NF55G preconnection inspection started

Operator confirms UART1 loopback removed and NF55G disconnected. COM5 Elecom
ATE adapter and COM14 Pico REPL enumerated. No NF55G command or hardware reset
performed in this inspection. Prior physical ATE checks are recorded above.
Reviewed NF55G_HIL_Preparation.md, Test_Specification.md T9 gate, HW-01 and
reference/NF55G_試験治具仕様書_添付資料_CN24通信ハーネス結線表.docx
(2026-08-28; cites historical D6, while project baseline remains r1).
Harness table: CN24 #1 RX-IN to fixture RS232 TXD; #2 TX-OUT to RXD;
#3 and #4 SG both to fixture RS232 SG. Verify numbering on actual housings/HRS
drawing, not apparent left/right. No GPIO-direct RS232 connection intended.

Pending operator evidence: final GP4/GP5 isolation location/method/inspection;
CN24 pin numbering, continuity and adjacent-pin short check; RS232 converter
path and SG connections; product identity/FW; actual power, load, battery and
output state, operator and shutdown method. Physical conditions cannot be
verified through COM enumeration. No connection readiness declared or Issue
closed. Worktree has uncommitted test records; T9 clean/synchronized gate
must also be satisfied before real product connection/transactions.


## 2026-09-17: Operator preconnection inspection results

Operator reports:
- GP4/GP5 physically isolated.
- CN24 wiring correct.
- Harness inspection: no problems.
- Communication path verified.
- Power/load conditions: all OFF.
- Target firmware revision unknown.
Earlier confirmation remains: UART1 loopback removed and NF55G disconnected.
These are operator inspection statements, not software measurements.
Do not infer battery disconnection from 'all OFF', assign a target serial
number, or infer an isolation location/method from 'physically isolated'.

Remaining details: exact GP4/GP5 isolation location/method for HW-01 record;
battery connected/disconnected state and actual power removal method; target
individual identifier (a temporary test ID may be supplied). FW stays UNKNOWN
until identified; no inferred FW compatibility or Open Issue closure.
Latest preconnection Host/Mock execution: 147 tests passed on 2026-09-17.
No serial commands, wiring changes, power operations or firmware deployment
performed while recording this response. Connection/transmission remains
pending completion of applicable T9 entry conditions, including record sync.


## 2026-09-17: Sample 1 identification and isolation details

Additional operator confirmation:
- GP4/GP5 isolation location/method, verbatim: SDカード基板のGP4,5を抜去してはんだ付け。
  This supplements the earlier explicit physical-isolation confirmation.
  No independent continuity measurement was performed by the assistant.
- Battery: not connected.
- Test individual identifier: Sample 1 (operator-assigned identifier).
- FW revision: still unknown.

Prior CN24/harness/communication-path confirmations and all-OFF state remain
applicable. UART1 loopback removed; NF55G remains disconnected as last reported.
The concrete power-removal/shutdown method has not yet been supplied.
No serial communication, reset, deployment or power operation in this step.
No Open Issue automatically closed. T9 record synchronization remains pending.


## 2026-09-17: Sample 1 power shutdown method confirmed

Operator identifies NF54G as the AC-DC section and NF55G as the DC-DC section.
The stated shutdown operation is NF54G AC switch OFF. Battery remains
unconnected; the previously reported power/load state is all OFF.
This completes the outstanding operator response about the shutdown method.
It is not a measurement of residual voltage or discharge time.

Target remains NF55G Sample 1, FW unknown. CN24 wiring, harness inspection,
RS232 path and SD-board GP4/GP5 physical isolation are operator-confirmed in
preceding entries; UART1 loopback removed, NF55G last reported disconnected.
No product connection, serial transmission, power operation or firmware change
was performed while recording this response. No Open Issue automatically closed.
Physical-check responses are now recorded; applicable T9 entry conditions,
including committing/synchronizing the test records, remain to be completed
before authorizing real product connection and communication.


## 2026-09-17: T9 entry verification for Sample 1

Verified against Test_Specification.md T9 entry conditions:
- Started clean at 3fb61ed; git pull --ff-only origin main: already up to date.
- Host T0-T7/Mock: 147 tests passed in this verification.
- Deployment selected: firmware/main.py -> /main.py, src/*.py -> /src/.
  All 23 active Python files SHA256-match current host source. Inventory:
  temp/t9_inventory_20260917.log. No firmware changes/deployment performed.
- Integrated deployed runtime: RTC advanced, SD 64 CSV rows exact readback,
  zero drops, remount/readback and run/stop passed. FW_UPDATE rejected.
  Observed NF55 UART wrapper write count=0 during smoke; this is software
  observation after app creation, not physical startup waveform measurement.
  Evidence: temp/t9_runtime_smoke_20260917.log.
- Restored normal boot; COM5 physical ATE ID/RTC/SD/FW_UPDATE all matched
  expected responses, including CRLF. No initial ASCII error on this check.
  Evidence: temp/t9_normal_boot_20260917.log, temp/t9_ate_final_20260917.json.
- HW-01 isolation method and operator inspection documented in preceding
  records (SD-board GP4/GP5 removal/soldering). Issue itself remains open;
  no inference of formal issue closure or independent measurement.
- NF55G_HIL_Preparation.md separates D1/D5 initial checks from controls,
  clear operations, calibration and D0. Use one transaction at a time;
  stop after final error and preserve raw evidence. FU remains prohibited.

Scope decision: ready for staged Sample 1 D1/D5 communication smoke once this
entry is committed/pushed and synchronization is confirmed. Not production
qualification. NF55G FW UNKNOWN remains recorded; D5 may identify it without
assuming r1 compatibility. Initial ERR:ASCII observation remains unresolved;
no failure recurred in this final local check. SD cold-boot causal isolation,
physical timing qualification and other Open Issues remain outside this gate.
Optional MISO voltage measurement is omitted by user decision.

Physical state per operator: NF55G not connected, UART1 loopback removed,
NF54G AC switch OFF, load/output OFF, battery disconnected. No NF55G command
was requested. Pico normal firmware left running and COM5/COM14 released.
Next physical step: connect confirmed CN24 harness with power OFF; report
connection completion before arranging power-on/receive observation and D1/D5.

## 2026-09-26 QR PIO受信準備
ユーザーがGP9(12番)←TX1、GP8(11番)→RX1、GND(13番)の接続完了を報告。
COM14のPico2/RP2350・MicroPython v1.28.0を確認。読み取り時PIO0_CTRL=0x0。
qr_reader.py/qr_pio_rx.py/pico_qr_receive_test.pyのみルートへ追加。既存main.py/srcは変更なし。
PIO初期化: QR_PIO_INIT OK GP9 1 GP8 1 RX 0 ERROR None。GP8はアイドルHighのみで送信なし、UART1は初期化しない。
確認後PIO停止・COM解放。USBホスト給電/リーダ設定/ATE指示と実際の光学読取は未確認。QR受信成功の記録ではない。

## 2026-09-26 QRテスト機の指定
ユーザー指定: OPTICON L-46Xをテスト機として使用。COM10からATEコマンドを送信し、COM14でPico REPLを監視。試験プロセスのIDLE表示を確認済み。型番指定をUSB HID設定確認やQR読取成功とは扱わない。

## 2026-09-26 QRホスト給電接続完了
ユーザー報告: Pico VBUS → HOST VBUSおよび5Vの両端子へ供給する必要があり、接続完了。信号線は既報のGP9←TX1/GP8→RX1/GND。電圧・電流の測定およびQR読取合格は未確認。

2026-09-26 QR試験: ATE応答後のbytearray item deletion TypeErrorをスライス再代入で修正。Host159件合格、Pico実機上のMockポートでrun()の2byte分割応答完了を確認。ATE_PARTIAL_TX_PICO_OK。光学QR読取の成功とは別。

2026-09-26切分け: ユーザーがPCのExcelへ入力できること、およびホストD2点灯を確認。直近のPico RAMはstate=ERROR, raw="", length=0, error=QR_TIMEOUT。文字がPicoの有効原文へ保存されていない。ホストUART出力/配線/PIO処理のどこが原因かは未確定。試験コードに受付中の受信byte数・先頭64byteと総受信数の診断表示を追加。受付前のデータはCacheへ昇格しない。今回の再試験のみtimeoutを30秒に延長する。

## QR給電OK・LED認識記録の訂正
ユーザー追報: HOST 5V・VBUS両端子への給電OK（数値未提示）。D1/D2を当初から取り違えた可能性があり、D1点灯・D2消灯/変化なしとの報告。以前のD2点灯によるホストHID認識確認は撤回し、未確認として扱う。PC ExcelへのHID入力確認とは区別する。9600bps/8N1は一致、実QR受信は未解決。

## USBキーボードによる認識切分け
ユーザー確認: 通常のUSBキーボード接続ではホストD2が点灯した。少なくとも当該キーボードを認識する機能は動作。L-46X接続時のD2消灯との差があり、L-46XのUSBモード/列挙相性/接続条件を優先調査する。ホスト全機能・UART送信・Pico受信の正常をこの結果だけで断定しない。

## USBキーボード入力のPico受信確認
COM14実測: QR_TEST READING → QR_TEST ERROR QR_LENGTH。QR_DIAG scan_bytes 4 raw_len 3 wire b'ABC\n'、QR_RX_TOTAL 4。通常USBキーボードからABC+Enterを受信し、ホストTX1→GP9 PIOの9600bps/8N1経路とLF終端検出を確認。QR_LENGTHは35文字要件に対し3文字だったための期待どおりの形式エラー。L-46Xの認識/実QR35文字読取の成功は未確認。

## QR再試験成功（COM14実測）
ATE開始後、QR_TEST READING → QR_TEST READYを確認。
原文: US250A-CGXE-009491-10101A2623000001
受信36byte = 本文35文字 + LF。QR_DIAG scan_bytes 36 raw_len 35。
分解値: 品名=US250A-C、品目コード=GXE-009491-101、製品REV=01A、製造年=26、製造週=23、製造号機=000001。
一時RAM CacheのREADYとREPL表示を確認。前回のドットを含む入力はQR_CHARで拒否され、今回の入力ではドットなしで正常完了した。入力が変わった理由は未確認で、許可文字規則は変更していない。
確認範囲はATE受付→QR経路からの受信→形式検証/分割→一時Cache/REPL表示。SS送信・CSV記録・量産Timing・全入力パターンを含むHIL完了ではない。L-46X認識が改善した要因は未特定のまま。

## QRホストの電源再投入後に認識再発
ユーザー追報: 電源を切り/入りするとD2が消灯した。QRリーダは初期化したとのこと。初期化が設定の工場出荷リセットか、電源投入時の起動処理か、および操作順・電源を切った対象は未確認。
先の35文字+LF受信成功は保持するが、電源再投入時の安定認識は未確認へ戻す。Pico試験main.pyは自動起動設定していないため、Picoの再起動後は別途試験start()が必要。ただしホストD2はUSB側の認識表示であり、ATE QR_SCANやPicoの試験開始をD2点灯の条件とは扱わない。
次はL-46Xを外した状態でホストを給電し、起動後にL-46Xを接続した場合のD2を確認して、接続済みでの電源投入との差を調べる。認識改善要因は未特定。仕様・FWの変更は行わない。

## L-46X初期化操作の詳細（ユーザー確認）
ユーザーが初期化操作を具体化: 電源投入時にトリガを10秒以上押して起動させる操作を実施し、「強制初期化」と説明。設定コードによる工場出荷リセットではない。この長押し操作による保存設定の変更範囲・USBモードへの影響は原典未確認。通常の電源投入と区別して記録する。

原典確認追記: メーカー作成L-46Xユーザーズマニュアル第5版p.22 §3.1.4「強制初期化」は、電源投入時トリガ10秒以上長押しを強制起動方法として説明する。ホストとの通信設定をせず読取可能にし、この強制起動中は読取データをホストへ出力しない。従って、この状態での成功音は通常通信復旧の証拠ではない。通常の受信試験はトリガを押さず電源投入し直して行う。先の35文字受信成功時の起動条件は未確定で、D2消灯の根本原因をこの操作だけに断定しない。出典（メーカー作成資料の販売店掲載版）: https://www.j-itecs.co.jp/wp/wp-content/uploads/2020/11/6dfa8720842f8ee09b40c16ba5909b4c.pdf

通常起動でもD2消灯とのユーザー報告。PC直結は現在不可。公開ホストFWの認識条件を確認し、L46X_USB_Recognition_Investigation.mdへ記録。起動後USB接続との比較は未確認、コード/設定変更なし。

## キーボード経由での認識回復（ユーザー報告）
キーボードを接続した後、キーボードを外してQRリーダに差し替えるとD2が点灯する。
これはキーボード認識を先行させた接続履歴に依存する回復条件の候補。ホスト内の状態、経過時間、USBリーダへの給電再投入等が同時に変わるため、ホストFWの不具合や特定の初期化不足と断定しない。
キーボードを外した後にD2が消灯し、L-46X接続後に再点灯するかは未確認。D2の前機器表示残りと、新機器認識を区別する。通常起動のL-46Xで再度35文字+LF受信できれば、実データ通信の回復も確認できる。
キーボード経由の操作は切分け手順であり、量産の起動手順や恒久対策には採用しない。根本原因と電源再投入後の再現性はOpenのまま。

## D2消灯・再点灯の確認（ユーザー追報）
キーボードを抜くとD2が一度消灯し、L-46Xを挿すと再点灯することをユーザーが確認。
前機器の認識表示が残っただけという説明は当該操作について除外できる。キーボード認識後のホストではL-46Xへの差し替えで新たな認識表示が成立する。
電源投入直後との違いがホスト内部状態、USB初期化タイミング、給電立上りのどれかは未確定。今回の認識回復状態での実データ再受信はまだ別途確認が必要。

## L-46X単体の抜き差しでは回復しない（ユーザー確認）
提案した比較手順（キーボードなしで通常電源投入→L-46Xだけを抜き差し）について、ユーザーがD2点灯しないと報告。
観測の整理: L-46X直接起動=認識表示なし、L-46X単体再接続=認識表示なし、キーボード認識→取り外しでD2消灯→L-46X接続=D2再点灯。
単なるL-46Xの再接続だけでは回復しない。キーボードを認識させる操作に関連したホスト状態/初期化経路を優先調査する。ただし試行回数、待ち時間、電源波形を揃えた反復比較は未実施であり、特定FW不具合と断定しない。
次の確証はホストのUSB初期化ログを失敗条件と成功条件で比較すること。公開FWと実機FWの同一性、診断出力の有効性と端子を確認してから取得方法を決める。診断のためのFW書換えや追加配線は未実施。

2026-09-26 HOST TX0診断: Host/Mock全161件合格、git diff --check合格（既存ファイルの改行警告のみ）。COM14への転送は接続不可で未完了。serial.tools.list_portsではCOM10のみ列挙、COM14は認識されていない。診断受信開始・230400bps実受信・ログ比較は未実施。Pico USB再接続後に転送から再開する。

2026-09-26 再接続後: COM14（USB VID:PID=2E8A:0005）を確認。qr_pio_rx.pyとpico_usb_host_debug.pyをPicoへ転送し、HOST_DEBUG READY GP10 physical14 230400 8N1 PIO0/SM1を実機で確認。診断受信待機を開始。開始時点ではHOST_TX0の受信出力なし。HOST実機の診断出力有効性とUSB認識失敗原因は未確認。専用診断中はATE QR_SCANを処理しない。

## 2026-09-26 TX0実測: L-46X再接続でD2消灯
GP10/230400bpsで実際の診断出力を取得。ユーザーは再接続後D2消灯と報告。
以下はCOM14の分割受信を連結した抜粋（受信開始から約84秒）。HOST_DEBUG LOSS表示なし。ただしUART全バイトの完全性は独立検証していない。
```text
Device at root hub 1 connected
initializing device at root hub port 1
Device class 0
Max packet size 64
VID/PID: 065a/a001
SetAddress: 16
Manufacturer String: Opticon
Model String: Opticon USB Barcode Reader
config total length: 0x0022
Configuration value: 1
Interface count: 1
Interface descriptor found
Interface 0
  Class 3
  Sub Class 1
  Interface Protocol 1
  Alternate Setting 0
  Endpoint Count 1
HID descriptor found
HID at Interface 0
  USB 1.11
  Country code 0x00
  TypeX 0x22
Endpoint descriptor found
Requesting report from interface 0
CALLBACK: dev[0] @16, is_attach=1
```
機器情報・HID interface取得までは進行。Report要求後にUsage等の解析出力およびkeyboard connected出力が観測されない。取得済み公開udev_hid.cはReport転送エラー時に解析前returnするためReport取得/解析段階を優先調査。ただし実機FW同一性・転送結果コード・受信長は不明で、エラー原因は断定しない。
次はPico/HOSTを通電したままキーボード接続→D2確認→取り外し→L-46X接続の比較ログを取得する。QR/SS試験は行わない。

## 2026-09-26 キーボード経由の比較ログ
ユーザー操作: L-46Xを外す→キーボードD2点灯→外す→L-46X再接続でD2点灯。COM14 TX0診断にも対応する接続/切断を確認（LOSS表示なし）。
- 約221秒: Dell KB216 Wired Keyboard、VID/PID 413c/2113、EP0最大8byte、interface 2個。Report要求後にUsage Keyboardとreport解析内容が出力され、CALLBACK: 1 keyboard(s) now connected。
- 約228秒: disconnect, 0 keyboard(s) now connected。
- 約232秒: Opticon USB Barcode Reader、065a/a001、EP0最大64byte、interface 1個。Requesting report from interface 0から約294ms後にattach callback。Usage/Report解析ログは今回もないがCALLBACK: 1 keyboard(s) now connectedが出力された。
- 先のD2消灯時もReport要求→attachが約293msで、解析ログなし。違いはkeyboard登録の有無。
取得済み公開コードとの照合: udev_hid.cのhiddevice_init_endpointはgetHIDDeviceReportの戻り値を無視する。Report取得エラーは解析前return。USBHost.cの確認した切断/再登録経路はiface usageをクリアしておらず、main.cの登録判定はiface.usage == Usage_KEYBOARD。従って前のキーボードのUsageが残り、Report取得が正常化しなくても登録される仮説が今回の差を説明する。実機FW同一性・実際のReport転送結果/長さ未確認のため原因確定ではない。
従前の「単なるD2表示残留ではない」は維持するが、新規登録の根拠に前機器の内部情報が残留する可能性は別問題として追加。D2点灯を完全なHID初期化成功とは扱わない。
次に専用診断を継続したままQRを1回読み、TX0のKeyEvt等を確認する。これはキー入力経路の診断であり、QR Cache/35文字受信の再試験ではない。HOST設定/FWは変更しない。

## 2026-09-26 QR読取時のTX0キーイベント確認
ユーザーがキーボード経由でD2点灯したL-46XでQRを1回読取。COM14で受信開始後473064～473158msに@16 KeyEvtのDown/Upを連続観測。冒頭D02,D18,U02/U18、続いてD02,D16等、末尾D1e,U1e,D28,U28。HOST_DEBUG LOSS表示なし。
これにより現在の接続状態ではL-46Xの読取に対応した入力をHOSTがキーイベントへ変換していることを確認。D2表示だけの確認から進展した。ただし今回の診断はTX0のみで、TX1の35文字本文・QR Cache・ATE応答は監視していない。今回の結果をQR受信試験全体の合格や電源再投入後の認識改善とは扱わない。
Report解析ログが無いのにキーボード経由で登録/入力処理できるという観測は、前機器Usage残留の仮説と整合するが、実機FW一致とReport取得失敗理由は未確定。恒久対策は未実施。診断受信は継続中。

## 2026-11-07 ATE UART0 retest after cable correction

- Operator reported the cable had been corrected. pySerial enumerated COM19 as
  Elecom USB-Serial Converter (VID:PID 056E:5004); COM14 remained the Pico USB
  REPL. The Windows serial-port inventory did not list COM19, but pySerial did.
- Opened COM19 at 115200 bps, 8N1, no flow control; DTR/RTS disabled. No bytes
  were pending before the test.
- Sent one local `*IDN?` request, TX=`2A49444E3F0D0A`. No response bytes arrived
  within 2 seconds. Stopped immediately; RTC_CHECK?, SD_STATUS?, and FW_UPDATE
  were not sent.
- Result: physical ATE UART0 response NOT VERIFIED after cable correction.
  The cause is undetermined; cable routing, Pico runtime state, and UART0
  receive/transmit wiring remain to be checked. No NF55G refresh, control, or
  FU command was requested. NF55G UART1 wire activity was not independently
  monitored. Pico power/runtime state and product wiring state were not
  re-inspected during this test.
- A preceding Python invocation failed in PowerShell argument parsing before
  opening COM19; it transmitted no data. The successful COM19 open and single
  request above were performed with the PowerShell SerialPort API.
- No source or device files were changed. Host/Mock tests passed 161/161 in
  this session. No Open Issue was closed.

Next: confirm that Pico normal runtime is active and verify the adapter's
RS232 path to UART0 GP0/GP1 against the harness drawing before another request.
Keep the NF55G unpowered and do not send product commands during this check.

## 2026-11-07 ATE UART0 local retest after UART0/1 correction

- Operator reported UART0/1 wiring was corrected. pySerial enumerated COM19 as
  Elecom USB-Serial Converter (VID:PID 056E:5004); COM14 was the Pico USB REPL.
- COM19 settings: 115200 bps, 8N1, no flow control; DTR/RTS disabled. No bytes
  were pending before the test. Each request and response used CRLF.
- `*IDN?` -> `NF55G_PICO_FIXTURE,Rev.0` (TX `2A49444E3F0D0A`, RX
  `4E463535475F5049434F5F464958545552452C5265762E300D0A`): PASS.
- `RTC_CHECK?` -> `OK` (TX `5254435F434845434B3F0D0A`, RX `4F4B0D0A`): PASS.
- `SD_STATUS?` -> `OK` (TX `53445F5354415455533F0D0A`, RX `4F4B0D0A`): PASS.
- `FW_UPDATE` -> `ERR:FU_DISABLED` (TX `46575F5550444154450D0A`, RX
  `4552523A46555F44495341424C45440D0A`): PASS for local FU blocking.
- This verifies the COM19-to-Pico UART0 local request/response path for these
  commands. No NF55G Refresh, control, or FU frame was requested. NF55G UART1
  wire activity was not independently monitored; no product communication
  result is claimed. Product D1/D5 testing was not run in this step.
- No source/device files changed. No Open Issue was closed.

## 2026-11-07 Sample 1 D1/D5 read-only communication smoke

- Operator confirmed the UART0/1 wiring correction. Operator-reported DUT state:
  Sample 1 connected and powered, load/output OFF, battery disconnected. COM19
  was used for ATE UART0 at 115200 bps, 8N1, no flow control, DTR/RTS disabled.
- Each ATE command was sent once with CRLF after confirming no pending RX bytes.
  All replies below were received with complete CRLF; no command was repeated.
- `STATUS_REFRESH` (D1): TX `5354415455535F524546524553480D0A`, RX
  `4F4B0D0A` (`OK`): PASS at ATE response level.
- `PS_ON?`: TX `50535F4F4E3F0D0A`, RX `310D0A` (`1`): cached STATUS query
  returned a value after D1.
- `INFO_REFRESH` (D5): TX `494E464F5F524546524553480D0A`, RX
  `4F4B0D0A` (`OK`): PASS at ATE response level.
- `FW_REV?`: TX `46575F5245563F0D0A`, RX `53312E3133200D0A` (`S1.13 ` with
  one trailing space before CRLF): cached INFO query returned a value after D5.
- No product control, SET/CLEAR, or FU command was sent. The ATE-side `OK` and
  cached values indicate successful command handling; this test did not capture
  NF55G UART raw frames, DATA length, BCC, ACK, retry counters, elapsed time,
  or physical UART1 waveforms. Do not treat this smoke as product PASS/FAIL or
  as confirmation that FW S1.13 is compatible with r1.
- No Open Issue was closed. Preserve the trailing space in the observed FW_REV
  response; do not normalize it without specification direction.

### D1/D5 cache-query sweep

- After the D1 and D5 refreshes above, queried every STATUS and INFO cache field
  once through COM19. The first automated attempt generated an empty CRLF line;
  it was ignored by the ATE server and returned no bytes. The corrected list was
  validated before opening COM19: 61 commands, first `BURST_ON?`, last
  `FAN_WNG_THD?`. No individual query caused another Refresh.
- Result: STATUS 37/37 and INFO 26/26 returned a value with complete CRLF;
  no timeout or `ERR:` response. `PS_ON?` and `FW_REV?` were included from the
  preceding D1/D5 check. Individual cache queries use the cache-only dispatcher
  path; no NF55G UART frame is generated by that path.
- Responses below are the exact ATE text values. Preserve leading zeroes and
  spaces; values are observations, not Pico product PASS/FAIL judgments.

| STATUS query | Response | INFO query | Response |
|---|---|---|---|
| `PS_ON?` | `1` | `FW_REV?` | `S1.13 ` |
| `BURST_ON?` | `0` | `UNIT_REV?` | `A5. ` |
| `BURST?` | `0` | `UNIT_LOT?` | `2610` |
| `PS_OFF_CHARGE?` | `0` | `UNIT_SERIAL?` | `000832` |
| `RESTART_READY?` | `0` | `ADU_REV?` | `0000` |
| `BACKUP_READY?` | `1` | `ADU_LOT?` | `0000` |
| `CHARGE_READY?` | `0` | `ADU_SERIAL?` | `000000` |
| `BATT_CHECK_RUN?` | `0` | `BBU_REV?` | `0000` |
| `CHARGE_OFF_STATUS?` | `0` | `BBU_LOT?` | `0000` |
| `CHARGE_ON_STATUS?` | `0` | `BBU_SERIAL?` | `000000` |
| `BATT_ON?` | `0` | `PS_ON_BACKUP?` | `1` |
| `BATT_LOW?` | `1` | `AC_LINK?` | `0` |
| `S_CHARGE_ON?` | `0` | `AUTO_CHARGE?` | `2` |
| `CHARGE_OK?` | `0` | `EVENT_ENABLE?` | `0` |
| `CHARGER_ON?` | `0` | `MAX_BACKUP_TIME?` | `0` |
| `FAN_WNG?` | `0` | `MIN_BACKUP_TIME?` | `15` |
| `ADU_TEMP_WNG?` | `0` | `RESTART_TIME?` | `15` |
| `OC_OFF_H?` | `0` | `BATT_LOW_THD?` | `50` |
| `PFC_OV?` | `0` | `BATT_CAP_MAH?` | `4900` |
| `FAN_FAIL?` | `0` | `BATT_CAP_WH?` | `36` |
| `BBU_TEMP_WNG?` | `0` | `CHG_IR_THD?` | `0` |
| `BBU_FAIL?` | `0` | `BATT_WNG_THD?` | `65` |
| `CHG_LV?` | `1` | `BATT_ALM_THD?` | `80` |
| `CHG_OV?` | `0` | `ADU_TEMP_THD?` | `85` |
| `CHG_OC?` | `0` | `BBU_TEMP_THD?` | `85` |
| `BATT_TEMP_WNG?` | `0` | `FAN_WNG_THD?` | `615` |
| `BATT_TEMP_ALM?` | `0` |  |  |
| `BATT_LV?` | `0` |  |  |
| `BATT_OV?` | `0` |  |  |
| `BATT_LIFE?` | `0` |  |  |
| `BATT_MCN?` | `0` |  |  |
| `BATT_P_FAIL?` | `1` |  |  |
| `BATT_DCN?` | `0` |  |  |
| `12V_OV?` | `0` |  |  |
| `12V_LV?` | `0` |  |  |
| `12V_OC?` | `0` |  |  |
| `12V_OC_OFF_L?` | `0` |  |  |

- In particular, observed status values include `BATT_LOW=1`, `CHG_LV=1`, and
  `BATT_P_FAIL=1` while the operator-reported battery was disconnected. These
  are preserved for design/ATE interpretation only; no failure conclusion or
  cache correction is made here.
- The sweep did not capture NF55G raw frames, BCC/ACK, retry/elapsed metrics, or
  physical UART1 waveforms. The response values are not product acceptance.

### D1/D5 rerun with RAM/SD Logger enabled

- Before starting, `SD_STATUS?` returned `OK`. Operator-reported DUT conditions
  remained Sample 1 connected/powered, load/output OFF, battery disconnected.
- Logger sequence on COM19, 115200 bps 8N1, CRLF:
  - `TEST_START` -> `OK`, TX `544553545F53544152540D0A`, RX `4F4B0D0A`.
  - `STATUS_REFRESH` (D1) -> `OK`, TX `5354415455535F524546524553480D0A`,
    RX `4F4B0D0A`.
  - `INFO_REFRESH` (D5) -> `OK`, TX `494E464F5F524546524553480D0A`,
    RX `4F4B0D0A`.
  - `TEST_END` -> `OK`, TX `544553545F454E440D0A`, RX `4F4B0D0A`.
- Post-close checks: `SD_STATUS?` -> `OK`; `LOG_DROP_COUNT?` -> `0`;
  `SD_USAGE?` -> `1245184/15910043648/0.008%` (used/capacity/percent).
- The Logger was active across both refresh transactions. Runtime trace hooks
  enqueue raw NF TX/RX and D1/D5 transaction summaries in RAM; TEST_END returned
  OK after its forced drain/flush/close path. No product control, SET/CLEAR, or
  FU command was sent. No individual STATUS/INFO queries were issued in this
  logging session.
- The CSV was not independently read back or matched against its expected
  record rows in this step; SD_USAGE is total filesystem usage, not a measured
  per-file size delta. Therefore this confirms Logger command/flush status and
  zero reported drops, but not the exact on-card raw frame contents. Preserve
  this limit in any subsequent HIL assessment.
- NF55G raw frame data, BCC/ACK, retry counts, elapsed timing, and UART1 physical
  waveforms were not separately captured by the host. The values above are ATE
  command/reply evidence, not product PASS/FAIL. No Open Issue was closed.

### Post-HIL local fixture diagnostics

- `PICO_SELF_CHECK?` -> `OK:ATE_UART=OK;NF55_UART=OK;RTC=OK;LOGGER=OK`
  (TX `5049434F5F53454C465F434845434B3F0D0A`): PASS for local component
  availability/status only.
- `COMM_STATUS?` -> `OK:state=IDLE`
  (TX `434F4D4D5F5354415455533F0D0A`): PASS; protocol was idle after D1/D5.
- `RETRY_COUNT?` -> `OK:cmd=0,rsp=0`
  (TX `52455452595F434F554E543F0D0A`): no retries reported for the last
  transaction. These are local diagnostics and do not send NF55G frames.
- No further NF55G command was sent in this step. At the time of this entry,
  D0/D2/D3/D4 and other refresh paths were not available through the deployed
  implementation; D0 side-effect interpretation remains OI-03. Subsequent D2
  implementation and HIL deployment attempt are recorded below. Continue to
  keep FU prohibited. Physical UART1 waveform capture remains deferred per the
  operator's decision.

## 2026-11-07 D2-enabled firmware deployment; Logger gate blocked HIL

- Repository baseline: commit `612bad8` (`feat: add D2 refresh support for
  off-period data`), `main` synchronized with `origin/main`, worktree clean
  before hardware inspection. Pico: RP2350 / MicroPython v1.28.0, unique ID
  `2d35a1e11ac125e3` on COM14. ATE adapter: COM19 Elecom, 115200 bps 8N1.
- Before opening REPL, COM19 local diagnostics reported
  `PICO_SELF_CHECK?=OK:ATE_UART=OK;NF55_UART=OK;RTC=OK;LOGGER=OK`,
  `COMM_STATUS?=OK:state=IDLE`, `SD_STATUS?=OK`, and `LOG_DROP_COUNT?=0`.
- Backed up the pre-deployment Pico `/src/` (23 files) and `/main.py` outside
  the repository at `NF55G_Pico_pico_backup_612bad8_20261107/`. SHA-256 for the
  old `/main.py`, `/src/nf55_command.py`, and `/src/command_dispatcher.py`
  matched device-side hashes before deployment.
- Deployed all 24 current `src/*.py` files and `firmware/main.py` to Pico
  `/src/` and `/main.py`. All 25 deployed files SHA-256-matched commit `612bad8`.
  Existing unrelated root QR/diagnostic files and the SD card contents were
  retained. Started the deployed application with `mpremote ... resume run`;
  no reset or product command was requested by the deployment itself.
- After app start, ATE local checks: `*IDN?` returned
  `NF55G_PICO_FIXTURE,Rev.0`; `PICO_SELF_CHECK?` returned
  `NG:ATE_UART=OK;NF55_UART=OK;RTC=OK;LOGGER=MOUNT_ERR`; `SD_STATUS?` returned
  `MOUNT_ERR`; `COMM_STATUS?` was `IDLE`; `LOG_DROP_COUNT?` was `0`.
- One local `SD_REINIT` attempt returned `ERR:MOUNT_ERR`. No `TEST_START`,
  `D2_REFRESH`, or `TEST_END` was sent. Therefore no D2 transaction was
  requested and the Logger-backed D2 HIL did not run. Do not infer NF55G D2
  response behavior or wire-level TX from this attempt.
- Stop condition: Logger/SD is not ready. Preserve the deployment backup and
  do not retry SD initialization or send D2 until the SD mount issue is
  diagnosed and `SD_STATUS?` / `PICO_SELF_CHECK?` report ready. No control,
  SET/CLEAR, or FU command was sent; no Open Issue was closed.
- Additional D2 send gate noted from the operator's 2026-11-07 review
  (`docs/D2_PS_ON_Review_20261107.md`, D2-PS-01 Open): r1 states D2 is not
  accepted in PS_OFF and is not accepted after PS_ON until NF55G-side SET CLOCK
  processing completes. After app restart the STATUS Cache was not refreshed;
  current PS_ON and SC completion were not established. Do not send D2 until
  those conditions are confirmed by the responsible test/design procedure.

### D2 precondition status read; D2 withheld

- After confirming local app response, queried `STATUS_REFRESH` once without
  Logger because `SD_STATUS?` remained `MOUNT_ERR`. ATE reply was `OK`
  (TX `5354415455535F524546524553480D0A`, RX `4F4B0D0A`). Then queried the
  refreshed STATUS Cache: `PS_ON?` -> `1` (TX `50535F4F4E3F0D0A`, RX `310D0A`).
- This establishes the observed PS_ON flag at this acquisition only. Since SD
  Logger was unavailable, no raw NF55G frame/BCC/ACK/retry record was saved to
  SD; the observation is limited to the ATE responses above.
- No evidence was available that NF55G-side SET CLOCK processing had completed
  after PS_ON. D2-PS-01 also remains Open regarding the r1 general-vs-D2-specific
  reception wording. `D2_REFRESH` was therefore not sent. No SC, power-state
  change, SET LIFE, control, CLEAR, or FU command was sent in this step.
- Resume D2 only after SD Logger is healthy and the responsible test/design
  procedure confirms the D2 acceptance condition, including SC completion.

## 2026-11-07 Post-D0 review and D2 precondition recheck

- D0 review: the two most recent Logger-captured D0 transactions were protocol
  OK, 327-character DATA with valid BCC, and no retry/ambiguous indication.
  Both returned CHARGE_END=0, including the first response. Thus no D0 transport
  or Decode fault was observed, but OI-03 (effect on a nonzero CHARGE_END) is
  still inconclusive and remains OPEN. This observation alone does not close
  OI-03 or establish product behavior.
- After the operator requested return to the main debug sequence, normal app
  preflight reported `LOGGER=MOUNT_ERR`, `SD_STATUS?=MOUNT_ERR`, while
  `COMM_STATUS?=IDLE`. No SD_REINIT or D2 command was sent in this step.
- For D2 acceptance context, sent `STATUS_REFRESH` once without Logger:
  TX `5354415455535F524546524553480D0A`, RX `4F4B0D0A` (`OK`). Then
  `PS_ON?` returned `1` (TX `50535F4F4E3F0D0A`, RX `310D0A`). This is only the
  PS_ON state at this STATUS acquisition; it does not evidence NF55G-side SET
  CLOCK completion.
- D2 was not sent. D2-PS-01 remains OPEN, SC completion is unconfirmed, and the
  Logger is unavailable. Resume D2 only after the Logger gate and the approved
  D2 acceptance/SC-completion procedure are satisfied. No control, SET/CLEAR,
  SC, or FU command was sent.

### D0 Logger rerun after SD card reinsertion

- After the operator reported the SD card had been removed and reinserted,
  normal D0-enabled app preflight passed: Logger/SD `OK`, protocol `IDLE`,
  drop count 0. Logger session was started; two `DATA_REFRESH` requests were
  issued, each followed by Cache-only `CHARGE_END?`; the first also queried
  `CHG_VOLT?`. `TEST_END` returned `OK`; post-session SD remained `OK`, drop
  count 0, usage `1507328/15910043648/0.009%`.
- CSV `/sd/BANK_A/20261107_143305.csv` was read back from the reinserted card.
  It contained 10 rows including header, 8 NF raw records, and two D0
  transaction summaries. Both D0 frames were 333 bytes with 327-character DATA;
  BCC verified (`2F` and `29`). Both transactions returned `OK`, command and
  response retries 0, `ambiguous=False`, elapsed 219ms and 236ms.
- Both raw D0 responses decoded to `CHG_VOLT=0` (`0000` HEX),
  `CHARGE_DATA=0`, and `CHARGE_END=0`. The first and second CHARGE_END values
  therefore showed no observed transition; because the first was already 0,
  this does not establish whether D0 ACK clears a nonzero CHARGE_END. OI-03
  remains Open and no product PASS/FAIL is assigned.
- The CSV logger records NF raw TX/RX and transaction summaries, not ATE Query
  replies. The host transcript for this run did not retain the CHG_VOLT/CHARGE_END
  ATE response lines, so the recorded field values above come from decoding the
  two stored raw D0 frames. No control, SET/CLEAR, SC, or FU command was sent.

### D0 Logger/CHARGE_END result after stale VFS recovery

- The earlier empty-output ATE loop command was not used as evidence. Subsequent
  local cache query showed DATA valid and `CHARGE_END?=0`; protocol was IDLE,
  SD status OK, and drop count 0. The run log was then closed with
  `TEST_END` -> `OK`.
- Read back `/sd/BANK_A/20261107_135211.csv`: 10 CSV rows including header,
  eight NF raw records, and two D0 transaction summaries. Both D0 frames had
  327-character DATA, 333-byte full frame, received/calculated BCC `23`, and
  valid BCC. Both transactions returned `OK`, command retry 0, response retry
  0, `ambiguous=False`, elapsed 215 ms and 214 ms.
- D0 DATA offsets 92..111 (LIFE_CALC) were `00001900000000000000` in both
  responses. Therefore both captured `CHARGE_DATA=0`, `CHARGE_END=0`. No change
  was observed between the two D0 responses. The first value was already 0, so
  this does not determine whether an initially asserted CHARGE_END would clear
  after D0 ACK; OI-03 remains OPEN and the effect is INCONCLUSIVE. No product
  PASS/FAIL judgment is made.
- ATE `CHARGE_END?` output was not captured in the host transcript; the two
  values above are decoded from SD-saved raw D0 responses, not from an ATE query.
  No CHARGE_OFF_CLEAR, SET LIFE, SC, or other control command was sent in this
  D0 sequence.
- Logger close verification: `TEST_END=OK`, `SD_STATUS?=OK`,
  `LOG_DROP_COUNT?=0`, `SD_USAGE?=1376256/15910043648/0.009%`. The CSV was read
  directly from the SD and parsed; NF raw BCC and D0 transaction summaries
  matched the records above.
- Mount investigation: before the successful run, `/sd` already exposed the
  15.9 GB card and prior CSV/BANK files, while a newly created sink failed at
  `VFS_MOUNT` with `OSError(1,)`, `mounted=False`, and no open Logger file.
  Explicitly unmounted the stale VFS mount, then `Logger.reinit()` returned
  `True`, stage `READY`; no files were removed. The identical failing symptom
  was consistent with a duplicate/stale VFS mount in that interpreter. This
  recovery establishes this session's mount issue, but does not close the
  separate cold-power CMD0 investigation.
- After CSV readback, the app was stopped for REPL inspection, the existing
  `/sd` VFS mount was released, and the normal D0-enabled app was restarted.
  Final local checks: self-check all OK, `SD_STATUS?=OK`, `COMM_STATUS?=IDLE`,
  `LOG_DROP_COUNT?=0`. No source deployment changes were made during this
  recovery; deployed firmware remains commit `441cb42`.

### DATA_REFRESH followed by CHG_VOLT query

- Post-restart preflight: `PICO_SELF_CHECK?` reported ATE/NF UART, RTC, LOGGER
  all OK; `SD_STATUS?=OK`, `COMM_STATUS?=OK:state=IDLE`,
  `LOG_DROP_COUNT?=0`.
- Logger sequence: `TEST_START` -> `OK`; `DATA_REFRESH` (D0) sent once -> `OK`
  (TX `444154415F524546524553480D0A`, RX `4F4B0D0A`); then `CHG_VOLT?` -> `0`
  (TX `4348475F564F4C543F0D0A`, RX `300D0A`); `TEST_END` -> `OK`.
- Post-test `SD_STATUS?=OK`, `LOG_DROP_COUNT?=0`,
  `SD_USAGE?=1441792/15910043648/0.009%`. The Logger was active over D0; this
  invocation's CSV has not yet been independently read back. Usage is total
  volume usage and not an exact per-file size measurement.
- `CHG_VOLT?=0` is the D0 Cache response. It is an observed decoded value only;
  Pico does not judge it as product PASS/FAIL. This test did not query
  `CHARGE_END?` after D0, so it provides no new evidence for OI-03. No control,
  SET/CLEAR, SC, or FU command was sent in this sequence. Physical UART1
  waveform capture remains deferred.

### D0/CHG_VOLT CSV readback

- After `TEST_END=OK`, the Pico service loop was stopped with Ctrl-C to inspect
  the card. `mpremote resume fs ls` showed the file at
  `/sd/BANK_A/20261107_140145.csv`. No reset, format, file write, delete, or
  NF55G command was performed during inspection.
- CSV readback contained the header plus five records: NF D0 TX, ACK RX, D0
  response RX, final ACK TX, and D0 transaction summary.
- Parsed raw response: full frame 333 bytes, DATA 327 ASCII characters, BCC
  received/calculated `2D` (match). D0 DATA `CHG_VOLT` field at offset 24 was
  `0000` HEX (=0); `LIFE_CALC` raw was `00001900000000000000`, with
  `CHARGE_DATA=0`, `CHARGE_END=0`. Transaction summary was `OK`, command retry
  0, response retry 0, elapsed 214ms, ambiguous False.
- The raw D0 CHG_VOLT value agrees with the ATE `CHG_VOLT?` response `0`.
  This verifies the saved frame and decoder value only; it is not external
  voltage/current evidence or product PASS/FAIL. Since CHARGE_END was already
  0 in this response, this record does not resolve OI-03.
- App is left at REPL after inspection; `/sd` remains mounted in this interpreter.
  Restart the normal entry after finishing SD inspection before further ATE use.

## 2026-11-07 SD mount failure recurred after D0 CSV inspection

- After the operator confirmed the SD contents had been reviewed, the D0 HIL
  session proceeded to resume the normal app. Before restart, an explicit
  `os.umount('/sd')` in the inspection REPL returned `OSError(EINVAL)`, meaning
  that REPL context did not have an active `/sd` mount to release.
- The next normal `firmware/main.py` startup snapshot reported
  `status=MOUNT_ERR`, `stage=CARD_INIT`, `error=OSError('CMD0 failed: -1',)`,
  `mounted=False`, `elapsed_ms=163`. `/sd` was empty and `statvfs('/sd')`
  described the internal 3 MiB filesystem. This differs from the earlier
  stale-VFS case (`VFS_MOUNT`, `OSError(1,)`) that recovered after unmounting
  the old VFS mount; the current failure is before VFS mount, at card CMD0.
- A single ATE `SD_REINIT` attempt returned `ERR:MOUNT_ERR`; no repeated retry
  was made. `COMM_STATUS?` was IDLE, `LOG_DROP_COUNT?=0`. No D0, NF55G control,
  SET/CLEAR, SC, or FU command was sent in this recovery attempt.
- D0 debugging is paused because Logger cannot start. Preserve the 2026-11-07
  D0 CSV and the external Pico backup. Before any further SD initialization,
  check the card seating and SD-board connections/power with the Sample in the
  operator-approved safe state. Then perform one controlled retry and capture
  its startup snapshot; do not format the card or delete existing SD files.
  Root cause of the recurring CMD0 no-response remains open.

## 2026-11-07 D0 / CHARGE_END Logger HIL after SD mount recovery

- D0-enabled source baseline: `441cb42`. After a soft-reset, the prior
  `PICO_SELF_CHECK?` and `SD_STATUS?` had reported `MOUNT_ERR`. A fresh
  `startup_sd_diagnostic` read showed `stage=VFS_MOUNT`,
  `error=OSError(1,)`, `mounted=False`. However `/sd` contained prior CSVs and
  BANK_A/B metadata, and `statvfs('/sd')` reported the 15.9 GB card capacity.
  The current Logger had `active=False` and no open file.
- In the same interpreter, explicitly unmounted the stale `/sd` VFS mount, then
  called the current Logger's `reinit()` once. It returned `True`; status became
  `OK`, mount stage `READY`, `last_error=None`, and existing `/sd` entries were
  still present. This identifies a stale/double VFS mount as the cause of this
  runtime's MOUNT_ERR. It does not resolve the separately observed cold-start
  CMD0 issue.
- Reused the D0-enabled app and started its service loop. Preflight passed:
  `PICO_SELF_CHECK?` all ATE/NF UART, RTC, LOGGER OK; `SD_STATUS?=OK`;
  `COMM_STATUS?=IDLE`; `LOG_DROP_COUNT?=0`.
- Logger-backed sequence produced two NF55G D0 transactions. CSV readback:
  `/sd/BANK_A/20261107_135211.csv`, 10 rows including header; 8 raw NF TX/RX
  rows and 2 transaction summaries. Both D0 frames were 333 bytes total with
  327-character DATA and valid BCC (`23` received/calculated). Both summaries:
  result `OK`, command retry 0, response retry 0, ambiguous False; elapsed
  215 ms and 214 ms respectively. `TEST_END=OK`, post-test SD status OK,
  drop count 0. These timings are observed elapsed values; configured D0 T2
  remains the provisional 600 ms limit.
- Both D0 DATA payloads contained LIFE_CALC raw
  `00001900000000000000` at DATA offset 92; decoded `CHARGE_DATA=0` and
  `CHARGE_END=0` for the first and second response. No transition was observed.
  Because the first captured value was already 0, this run cannot determine
  whether a nonzero CHARGE_END would be cleared by D0 ACK. OI-03 remains OPEN;
  no product behavior conclusion or PASS/FAIL is assigned.
- No NF55G control, SET/CLEAR, SC, or FU command was sent in this D0 sequence.
  The ATE-side CHARGE_END Query output was not captured in the host transcript;
  the two values above were decoded directly from independently saved raw D0
  response frames in the SD CSV.

### D2 precondition STATUS recheck

- On the operator's request, queried `STATUS_REFRESH` once over COM19 at
  115200 bps 8N1 with CRLF. TX `5354415455535F524546524553480D0A`, RX
  `4F4B0D0A` (`OK`). Then queried `PS_ON?`: TX `50535F4F4E3F0D0A`, RX
  `310D0A` (`1`). Both ATE replies had complete CRLF.
- This confirms PS_ON=1 at this STATUS acquisition only. The SD Logger remained
  unavailable (`MOUNT_ERR` from the preceding check), so no SD raw/BCC/ACK/
  retry trace was saved. No D2_REFRESH, SC, SET LIFE, control, CLEAR, or FU
  command was sent. D2-PS-01 remains Open; SET CLOCK completion is still not
  evidenced. Do not treat this STATUS result alone as D2 authorization.

## 2026-11-07 CHARGE_OFF control request and STATUS check

- Operator-reported Sample condition before request: battery disconnected,
  AC ON, output/load present. External charging-current measurement and an
  abnormal-stop procedure were reported as prepared. COM19 ATE UART settings:
  115200 bps, 8N1, CRLF, no flow control.
- Precondition `COMM_STATUS?` -> `OK:state=IDLE`
  (TX `434F4D4D5F5354415455533F0D0A`, RX
  `4F4B3A73746174653D49444C450D0A`).
- Sent `CHARGE_OFF` once (ATE mapping NF CMD `CF`, DATA `1`): TX
  `4348415247455F4F46460D0A`, RX `4F4B0D0A` (`OK`, complete CRLF).
  This is protocol transaction success only, not confirmation of current decay.
- Follow-up `STATUS_REFRESH` once: TX `5354415455535F524546524553480D0A`,
  RX `4F4B0D0A` (`OK`). Then `CHARGE_OFF_STATUS?`: TX
  `4348415247455F4F46465F5354415455533F0D0A`, RX `310D0A` (`1`).
- Per the cache invalidation rule, prior DATA/STATUS cache was invalidated on
  successful CF; the STATUS value above is from the explicit post-control D1.
- SD Logger remained `MOUNT_ERR`, so no SD trace, NF55G raw/BCC/ACK/retry/
  elapsed record was saved. External current measurement result was not supplied
  in this interaction. Do not claim product charging stopped or assign
  PASS/FAIL from the protocol `OK` or status flag alone. No additional control,
  CLEAR, SET, or FU command was sent. Physical waveform capture remains deferred.

## 2026-11-07 DATA_REFRESH (D0) Host implementation checkpoint

- Added the ATE `DATA_REFRESH` path for NF CMD D0 using provisional T2=600ms,
  expected DATA length 327, existing `decode_d0`, and DATA-only Cache update.
  The specified DATA Cache Query allowlist is wired to cache-only reads; D0's
  embedded STATUS, Manufacturing, and Parameter remain raw and are not promoted
  to their separate caches.
- Added ASCII-HEX validation for the 12-character D0 TIME field. D0 decode
  failure leaves DATA INVALID. OI-03 remains OPEN; no behavior was added to
  emulate or suppress any possible product-side CHARGE_END effect after D0 ACK.
- Host/Mock verification: `tests.test_read_cache_integration` plus
  `tests.test_decoder_complete` passed 34 focused tests; full Host/Mock suite
  passed 167 tests. Pylance reported no errors in touched Python files and
  `git diff --check` passed.
- Real D0 HIL was NOT run. The previously deployed Pico reported SD
  `MOUNT_ERR` after startup and `SD_REINIT` returned `ERR:MOUNT_ERR`, so Logger
  could not be enabled. D0 HIL also remains subject to OI-03 review. No D0 frame
  or other NF55G command was sent for this implementation checkpoint.

### D0 deployment/HIL retry with Logger gate

- Source baseline was commit `441cb42`, `main` synchronized with `origin/main`,
  and worktree clean before deployment. Target was Pico 2/RP2350, MicroPython
  v1.28.0, unique ID `2d35a1e11ac125e3` on COM14; ATE adapter COM19 at
  115200 bps 8N1.
- Before replacement, copied the existing D2 firmware `/src/` and `/main.py`
  outside the repository to `NF55G_Pico_pico_backup_preD0_441cb42_retry_20261107/`.
  The prior ATE runtime had to be interrupted with Ctrl-C to release COM14.
- Deployed the 24 Python modules under `/src/` and `firmware/main.py` as
  `/main.py`. All 25 deployed SHA-256 digests matched commit `441cb42`.
  Existing root QR/diagnostic files and SD contents were not removed.
- The deployed app started and `*IDN?` returned
  `NF55G_PICO_FIXTURE,Rev.0`. Preflight `PICO_SELF_CHECK?` returned
  `NG:ATE_UART=OK;NF55_UART=OK;RTC=OK;LOGGER=MOUNT_ERR`; Logger was not ready.
- Per the requested Logger gate, did not send `TEST_START` or `DATA_REFRESH`.
  No D0 NF55G frame was requested. Thus no D0 response or CHARGE_END change
  was observed; OI-03 remains open. Stop here until SD mount is diagnosed and
  `SD_STATUS?` plus `PICO_SELF_CHECK?` report OK. Then perform Logger-backed
  D0 once with before/after `CHARGE_END?` cache readings and record the
  transaction; do not infer product PASS/FAIL from the protocol result.

## 2026-11-07 SD recovery after app restart in existing interpreter

- After a COM14 transport error, the normal app was run again using `resume`.
  ATE self-check reported ATE/NF UART and RTC OK but LOGGER `MOUNT_ERR`;
  `SD_STATUS?=MOUNT_ERR`, `COMM_STATUS?=IDLE`, and `LOG_DROP_COUNT?=0`.
- The app loop was interrupted and the first-startup RAM snapshot read without
  resetting the interpreter: status `OK`, stage `READY`, mounted True, error
  None, elapsed 499 ms. This snapshot belongs to the first app startup in that
  interpreter, not necessarily the failed app instance. The failed instance's
  exact mount stage and exception were not captured.
- `/sd` exposed the existing CSVs, BANK_A/B and active-bank marker; statvfs
  reported the 15,910,043,648-byte card. This is consistent with an existing
  VFS mount, but does not by itself prove the failed instance's exception.
- With the failed app stopped and no logger session started in that instance,
  unmounted `/sd` once and created one new app. Its sink reported `READY`,
  `OK`, mounted True, error None, logger inactive and no open filename. Existing
  directory entries remained visible. No formatting, file deletion, `SD_REINIT`
  or NF55G command was performed.
- Started the recovered app's service loop without another mount. ATE reported
  `PICO_SELF_CHECK?=OK:ATE_UART=OK;NF55_UART=OK;RTC=OK;LOGGER=OK`,
  `SD_STATUS?=OK`, `SD_USAGE?=1507328/15910043648/0.009%`,
  `COMM_STATUS?=OK:state=IDLE`, and `LOG_DROP_COUNT?=0`. This is a warm recovery,
  not proof that the separate cold-start CMD0 failure has been resolved.

## 2026-11-07 Logger-backed D1 after SD recovery

- Preflight: `PICO_SELF_CHECK?` reported ATE UART, NF55 UART, RTC and LOGGER
  OK; `SD_STATUS?=OK`, `COMM_STATUS?=OK:state=IDLE`, `LOG_DROP_COUNT?=0`.
- `TEST_START` returned `OK`. One `STATUS_REFRESH` returned `OK` (ATE TX
  `5354415455535F524546524553480D0A`, RX `4F4B0D0A`); `PS_ON?` returned `1`
  (TX `50535F4F4E3F0D0A`, RX `310D0A`). `TEST_END` returned `OK`; all ATE
  responses had CRLF. Post-session SD remained OK, protocol IDLE, drop count 0.
- Read back `/sd/BANK_A/20261107_145729.csv` after stopping the loop. It
  contained D1 TX `024431033736`, ACK RX `06`, D1 response RX
  `024431323130313030303034303032303030033432`, ACK TX `06`, and one D1
  transaction summary. The existing frame parser verified CMD D1, DATA length
  15, DATA `210100004002000`, and BCC received/calculated `42`. Summary:
  `OK`, command retry 0, response retry 0, elapsed 26 ms, ambiguous False.
- Resumed the same app without reinitializing SD; `SD_STATUS?=OK`,
  `COMM_STATUS?=OK:state=IDLE`, `LOG_DROP_COUNT?=0`. PS_ON is an observation
  at D1 acquisition only; it does not demonstrate NF55G SET CLOCK completion.
  D2-PS-01 remains Open and D2 was not sent. No SC, control, SET/CLEAR, D0,
  FU or other NF55G command was sent in this sequence. No product PASS/FAIL
  was assigned. Host/Mock tests were not run for this hardware-only check.

## 2026-11-07 SC preparation: D0 TIME observation

- User reported that batteryless AC OFF/ON returns the NF55G calendar to
  2026-01-01 and requested SC with a test time instead of the current time.
  This report is not an independently verified power-cycle measurement.
- Preflight: self-check, SD and RTC OK; communication IDLE; drop count 0.
  `TEST_START=OK`, one `DATA_REFRESH=OK`, then `NF55_DATETIME?` returned
  `201A0B03_100730` and `CHARGE_END?=0`. `TEST_END=OK`, SD OK, drop count 0.
  ATE responses had CRLF. D0 ACK's potential CHARGE_END effect remains OI-03.
- r1 rule 2 encodes each TIME numeric field as ASCII HEX. The observed TIME
  `1A0B03100730` converts to `20261103_160748`; the deployed decoder had
  concatenated the HEX text rather than converting it. This is an offline
  conversion of the ATE observation; the D0 CSV has not been read back in this
  step, and this value must not be interpreted as the PC or Pico RTC time.
- Host changes for SC and TIME conversion are under test. SC was not sent,
  D2 was not sent, no AC power cycle was performed, and no product PASS/FAIL
  was assigned. SC can count time difference as AC OFF time; test time and
  resulting impact need operator confirmation before deployment and transmission.

## 2026-11-07 RTC-based SC and D0 readback

- On the operator's request, used the Pico DS3231 RTC value as the SC time.
  The previously observed NF55G time was 2026-11-03 16:07:48; the clock shift
  may affect AC OFF time calculations under r1. No AC power cycle was performed.
- Backed up the existing Pico `/src/command_parser.py`, `nf55_command.py`,
  `command_dispatcher.py`, and `nf55_decode.py` to
  `temp/pico_pre_sc_20261107_1530/`, then deployed the four changed files.
  Pico SHA-256 values matched the Host files. Existing SD contents were kept.
  Host source includes uncommitted changes and is not identical to commit 441cb42.
- Post-deployment preflight: ATE/NF UART, RTC and LOGGER OK; SD OK; protocol
  IDLE; drop count 0. `TEST_START=OK`. `RTC_DATETIME?=20261107_153531`;
  `CLOCK_SYNC 261107153531=OK`, then `STATUS_REFRESH=OK` and
  `DATA_REFRESH=OK`. `NF55_DATETIME?=20261107_153531`; a subsequent
  `RTC_DATETIME?=20261107_153532`. NF55 D0 minus the SC source was 0 seconds;
  NF55 D0 minus the later RTC reading was -1 second. These are sequential
  second-resolution readings, not an independent oscillator-accuracy test.
- `TEST_END=OK`; SD remained OK, protocol IDLE, drop count 0. Read back
  `/sd/BANK_A/20261107_153531.csv`: SC TX DATA `1A0B070F231F`, SC RX DATA
  length 0, D1 RX DATA length 15, and D0 RX DATA length 327 with TIME
  `1A0B070F231F`. Calculated and received BCC matched on every SC/D1/D0 frame.
  SC/D1/D0 transaction summaries were OK with command and response retries 0,
  ambiguous False, elapsed 22/26/216 ms respectively.
- After readback, released the closed SD mount and restarted the same firmware;
  self-check and SD OK, protocol IDLE, drop count 0. Immediate readback does
  not establish long-term or AC-off retention. D0 ACK's potential CHARGE_END
  effect remains OI-03. D2-PS-01 remains Open; no D2, other control, CLEAR or
  FU command was sent in this sequence. No product PASS/FAIL was assigned.

## 2026-11-07 NF55 RAW ASCII formatting

- Added deferred RAW ASCII formatting while preserving `raw_hex`; Host/Mock
  suite passed 176 tests. The previously saved SC/D1/D0 CSV was not modified;
  a separate local readable copy was generated from its `raw_hex` fields.
- Backed up Pico `/src/logger.py` to `temp/pico_logger_before_raw_ascii_20261107.py`,
  deployed the new file and verified its SHA-256 against the Host source.
  MicroPython conversion checks returned `\x02SC\x0313` for the SC response
  and `\x06` for ACK, and correctly escaped CSV special and non-ASCII bytes.
- After service restart, self-check and SD status were OK, communication IDLE,
  drop count 0. No NF55G command or product power operation was performed.
  A new NF55 RAW CSV and real-hardware communication timing remain unverified.

## 2026-11-07 Specified 2026-04-01 SC and D0 readback

- Operator requested `2026-04-01 00:00:00`. Preflight self-check and SD OK,
  communication IDLE, drop count 0. `TEST_START=OK`, then `RTC_DATETIME?`
  returned `20261107_155758`. Pico RTC was not changed.
- Sent `CLOCK_SYNC 260401000000` once; ATE returned `OK`. Then
  `STATUS_REFRESH=OK`, `DATA_REFRESH=OK`, and `NF55_DATETIME?` returned
  `20260401_000000`, zero seconds from the specified time at that acquisition.
  The subsequent Pico RTC read remained `20261107_155758`. All replies had CRLF.
- The prior SC test had set NF55G to November 2026. r1 says past timestamps
  receive PME, but NF55G time immediately before this SC and any intervening
  DUT power-cycle history were not checked in this test. Accordingly whether
  this was a past-time acceptance contrary to r1 is undetermined. Clock shift
  may affect AC OFF time calculations; no product PASS/FAIL is assigned.
- `TEST_END=OK`; SD OK, protocol IDLE, drop count 0. Read back
  `/sd/BANK_A/20261107_155758.csv` and copied it to
  `temp/20261107_155758_sc_20260401.csv`. Both SHA-256 values were
  `0b63384b232e9a89b049e3ed5c7b02a0601c678c999b87742c398ee90905bf14`.
  SC TX and D0 RX TIME fields were `1A0401000000`; SC RX DATA length 0,
  D1 RX length 15 and D0 RX length 327. All SC/D1/D0 frame BCCs matched;
  command and response retries were 0, ambiguous False, elapsed 21/27/214 ms.
  The RAW rows contained `raw_ascii` as well as `raw_hex`.
- ATE service resumed without SD reinitialization; self-check and SD OK,
  protocol IDLE, drop count 0. Long-term and AC-off time retention, waveform
  timing and OI-03 remain unverified. No D2, FU, CLEAR, or other control was
  sent, and no DUT power-cycle operation was performed during this sequence.

## 2026-11-07 D2 Logger-backed hardware check

- After the preceding SC setting and D0 readback, the operator reported no
  state change and no power off/on. Preflight self-check and SD were OK,
  communication IDLE, drop count 0, cached `PS_ON?=1`. The previously sent SC
  returned OK and its time was observed in D0; the D2-PS-01 specification
  interpretation remains Open and is not settled by this test.
- `TEST_START=OK`; one `STATUS_REFRESH=OK` followed by `PS_ON?=1`; one
  `D2_REFRESH=OK`. `RETRY_COUNT?=OK:cmd=0,rsp=0`. Cache-only
  `NF55_DATETIME?=ERR:CACHE_INVALID` after D2, consistent with DATA invalidation.
  All ATE replies were CRLF-terminated. `TEST_END=OK`; SD OK, protocol IDLE,
  drop count 0. No D0, SC, control, SET/CLEAR or FU was sent in this sequence.
- Read back `/sd/BANK_A/20261107_160445.csv` and copied it to
  `temp/20261107_160445_d1_d2.csv`; both SHA-256 values were
  `95bf3a73e8d2e0c2af6a87df8129c5ddc7ce8d0355ff61b521f7fef80084f212`.
  D2 TX DATA length 0, RX DATA length 30, DATA
  `041000000000000000000000000000`; received/calculated BCC `70`.
  All D1/D2 frame BCCs matched. D1/D2 transaction summaries were OK with
  command and response retries 0, ambiguous False, elapsed 27/36 ms.
  The CSV includes `raw_ascii` and `raw_hex`.
- Read D2 Cache from the same app while the loop was stopped: VALID, source D2;
  `AC_OFF_HOUR=104.0`, `PS_OFF_HOUR=0.0`, `AVE_OFF_TEMP=0`,
  `OFF_CHARGE_HOUR=0.0`, `AVE_CHARGE_TEMP=0`, `OFF_CHARGE=0`,
  `OFF_BATT_DEG=0.0`. DATA Cache remained invalid. These are observed values;
  the influence of prior SC or power history is not established, and Pico
  does not assign a product PASS/FAIL.
- Resumed the same app; self-check and SD OK, communication IDLE, drop count 0.
  Host/Mock tests were not rerun for this hardware-only check. Physical waveform
  timing and the D2 acceptance-condition interpretation remain open.

## 2026-11-07 PS_ON off-state observation

- On the operator's request to check OFF, preflight self-check and SD were OK,
  communication IDLE and drop count 0. `TEST_START=OK`, one explicit
  `STATUS_REFRESH=OK`, then `PS_ON?=0` (ATE TX `50535F4F4E3F0D0A`, RX
  `300D0A`, complete CRLF). This is the STATUS observation at D1 acquisition;
  it does not independently establish external supply or load voltage.
- `TEST_END=OK`; SD remained OK, communication IDLE, drop count 0. The SD CSV
  `/sd/BANK_A/20261107_161411.csv` was copied to
  `temp/20261107_161411_ps_off_d1.csv`; SHA-256 matched
  `9fbdaf7e59a09e8db940657556ddc80e06a3ff67ee1d814863e206c3993b3914`.
  D1 DATA was `010100000002000` (15 characters), BCC received/calculated `44`,
  command and response retries 0, elapsed 26 ms, ambiguous False.
- The app was resumed; SD OK, communication IDLE, drop count 0. No control,
  SC, D0, D2 or FU command was sent in this check. D2-PS-01 remains Open;
  no product PASS/FAIL was assigned. Host/Mock was not rerun for this
  hardware-only measurement.

## 2026-11-07 CHARGE_ON hardware check

- Operator requested CHARGE_ON first and physical confirmation by tester;
  reported battery disconnected, AC ON, output present and no load. Operator
  acknowledged the abnormal-stop preparation instruction. Actual tester
  reading and independent charging-current measurement were not yet provided.
- Preflight self-check and SD OK, communication IDLE, drop count 0.
  `TEST_START=OK`, then `STATUS_REFRESH=OK`. Pre-control cached values:
  `PS_ON=1`, `CHARGE_ON_STATUS=0`, `CHARGE_OFF_STATUS=0`, `BATT_P_FAIL=1`,
  `BATT_MCN=0`, `BATT_DCN=0`. The PS_ON observation differs from the earlier
  OFF check; the intervening physical operation or transition time is not
  recorded here. Do not equate any single status flag with an r1 diagnosis.
- One `CHARGE_ON` request (CN DATA `1`) returned `OK`. Immediate cache-only
  `CHARGE_ON_STATUS?=ERR:CACHE_INVALID`, then explicit `STATUS_REFRESH=OK`.
  Post-control values: `PS_ON=1`, `CHARGE_ON_STATUS=1`, `CHARGE_OFF_STATUS=0`,
  `CHARGER_ON=0`, `CHARGE_READY=0`. `TEST_END=OK`; SD OK, protocol IDLE,
  drop count 0. The status/OK do not establish actual current, voltage, or
  product PASS/FAIL. No automatic stop or other charging control was sent.
- Copied `/sd/BANK_A/20261107_162303.csv` to
  `temp/20261107_162303_charge_on.csv`; SHA-256 matched
  `ce0cbb7be7d2294ac290866fab80b3ddef026ce9fa9f9683ac0a5a592b501b75`.
  CN TX and RX both DATA `1`, BCC received/calculated `3F`; the preceding and
  following D1 responses had 15 DATA characters and matching BCC `42`/`43`.
  CN transaction: OK, command retry 0, response retry 0, 19 ms, ambiguous False.
- Resumed the same app; SD OK, communication IDLE, drop count 0. Wait for the
  operator's physical observation before a further charging command. No FU,
  SC, D0 or other control was sent. Host/Mock was not rerun for this
  hardware-only check; no Open Issue was closed.

## 2026-11-07 Charge command sequence without battery

- Operator requested continuing command checks and deferring electrical checks
  because no battery is connected. Earlier operator-reported setup: AC ON,
  output present, no load, battery disconnected. No measured voltage/current
  was supplied; product behavior and electrical safety are not inferred from
  the communication result.
- Preflight: self-check and SD OK, communication IDLE, drop count 0. Logger
  started; initial `STATUS_REFRESH=OK` yielded `PS_ON=1`,
  `CHARGE_ON_STATUS=1`, `CHARGE_OFF_STATUS=0`, `CHARGER_ON=0`.
- `CHARGE_ON_STOP` (CN DATA `0`) returned OK; after explicit D1,
  `CHARGE_ON_STATUS=0`, `CHARGE_OFF_STATUS=0`, `CHARGER_ON=0`.
  `CHARGE_OFF` (CF DATA `1`) returned OK; after D1, ON status 0, OFF status 1,
  charger 0. `CHARGE_OFF_CLEAR` (CF DATA `0`) returned OK; after D1, ON status
  0, OFF status 0, charger 0. PS_ON was 1 at each acquisition. Each control
  invalidated STATUS before the explicit D1, confirmed by cache-only
  `CHARGE_ON_STATUS?=ERR:CACHE_INVALID` after each operation.
- `TEST_END=OK`; SD OK, communication IDLE, drop count 0. Copied
  `/sd/BANK_A/20261107_162742.csv` to
  `temp/20261107_162742_charge_sequence.csv`; SHA-256 matched
  `13030f5d516bd6858730663c6f1b391c5dcb79201ed866b34c36e4cf1925f5ea`.
  CN `0`, CF `1`, CF `0` TX/RX DATA matched, all CN/CF/D1 frame BCCs matched;
  all transaction summaries were OK with command/response retries 0 and
  ambiguous False. CN elapsed 20 ms, CF operations 19 ms each.
- The app was resumed; SD OK, communication IDLE, drop count 0. No D0, D2,
  SC or FU was sent in this sequence. Protocol OK and status flags do not
  establish charging or cessation of current; external electrical checks are
  pending. Host/Mock was not rerun for this hardware-only measurement, and no
  Open Issue was closed.

## 2026-11-07 Commit 38a5648 deployment and ATE UART0 identity check

- After the operator's Pico power cycle, the deployed files were checked against
  commit `38a5648`. Initial inventory found three stale files; only
  `/src/command_dispatcher.py`, `/src/nf55_command.py`, and `/src/nf55_decode.py`
  were copied. Final SHA-256 comparison matched all 25 application files:
  `/main.py` and 24 `/src/*.py` files. Existing auxiliary files were retained.
- Sent one local identity query through COM19 (ATE): TX `*IDN?\r\n`, raw HEX
  `2A49444E3F0D0A`. Received raw HEX
  `4E463535475F5049434F5F464958545552452C5265762E300D0A`, decoded Ans
  `NF55G_PICO_FIXTURE,Rev.0\r\n`.
- This confirms the UART0 ATE request/response path and running fixture identity.
  No NF55G read, control, SC, D0, D2, D3, D4, or FU command was requested;
  product behavior and electrical PASS/FAIL were not assessed. Host/Mock was
  not rerun for this hardware-only check, and no Open Issue was closed.

## 2026-11-07 DATA Cache Query invalid-cache check

- Sent all 43 DATA Cache Query commands individually through COM19 at 115200
  bps, 8N1, each terminated by CRLF. No pending RX bytes were present before
  the run. `DATA_REFRESH` was not sent, so this checks query routing and the
  required invalid-cache behavior, not decoded product values.
- All 43 responses were complete CRLF lines with the same Ans:
  `ERR:CACHE_INVALID` (RX HEX `4552523A43414348455F494E56414C49440D0A`).
  There were 0 `ERR:UNKNOWN_CMD`, 0 timeouts, and 43 responses for 43 requests.
  Query commands reference Cache only; no NF55G command was requested.

| No. | ATE Query | Ans |
|---:|---|---|
| 1 | `NF55_DATE?` | `ERR:CACHE_INVALID` |
| 2 | `NF55_TIME?` | `ERR:CACHE_INVALID` |
| 3 | `NF55_DATETIME?` | `ERR:CACHE_INVALID` |
| 4 | `VOUT12?` | `ERR:CACHE_INVALID` |
| 5 | `IOUT12?` | `ERR:CACHE_INVALID` |
| 6 | `BATT_VOLT?` | `ERR:CACHE_INVALID` |
| 7 | `CHG_VOLT?` | `ERR:CACHE_INVALID` |
| 8 | `CHG_CURR?` | `ERR:CACHE_INVALID` |
| 9 | `BATT_CURR?` | `ERR:CACHE_INVALID` |
| 10 | `BATT_SOC_WH?` | `ERR:CACHE_INVALID` |
| 11 | `BATT_SOC_MAH?` | `ERR:CACHE_INVALID` |
| 12 | `BATT_TEMP?` | `ERR:CACHE_INVALID` |
| 13 | `ADU_TEMP?` | `ERR:CACHE_INVALID` |
| 14 | `BBU_TEMP?` | `ERR:CACHE_INVALID` |
| 15 | `FAN_RPM?` | `ERR:CACHE_INVALID` |
| 16 | `FAN_LEVEL?` | `ERR:CACHE_INVALID` |
| 17 | `AC_OFF_HOUR?` | `ERR:CACHE_INVALID` |
| 18 | `PS_OFF_HOUR?` | `ERR:CACHE_INVALID` |
| 19 | `AVE_OFF_TEMP?` | `ERR:CACHE_INVALID` |
| 20 | `OFF_CHARGE_HOUR?` | `ERR:CACHE_INVALID` |
| 21 | `AVE_CHARGE_TEMP?` | `ERR:CACHE_INVALID` |
| 22 | `OFF_CHARGE?` | `ERR:CACHE_INVALID` |
| 23 | `OFF_BATT_DEG?` | `ERR:CACHE_INVALID` |
| 24 | `CHARGE_DATA?` | `ERR:CACHE_INVALID` |
| 25 | `CHARGE_END?` | `ERR:CACHE_INVALID` |
| 26 | `LIFE_BATT_CHARGE?` | `ERR:CACHE_INVALID` |
| 27 | `LIFE_BATT_TEMP?` | `ERR:CACHE_INVALID` |
| 28 | `LIFE_BATT_DEG?` | `ERR:CACHE_INVALID` |
| 29 | `TOTAL_ADU_TEMP?` | `ERR:CACHE_INVALID` |
| 30 | `TOTAL_ADU_HOUR?` | `ERR:CACHE_INVALID` |
| 31 | `AC_FAIL_COUNT?` | `ERR:CACHE_INVALID` |
| 32 | `AC_LOW_COUNT?` | `ERR:CACHE_INVALID` |
| 33 | `BACKUP_COUNT?` | `ERR:CACHE_INVALID` |
| 34 | `BATT_DEG_TOTAL?` | `ERR:CACHE_INVALID` |
| 35 | `TOTAL_BATT_HOUR?` | `ERR:CACHE_INVALID` |
| 36 | `BATT_DISCHARGE_COUNT?` | `ERR:CACHE_INVALID` |
| 37 | `BATT_CHARGE_COUNT?` | `ERR:CACHE_INVALID` |
| 38 | `BATT_TTL_DISCHARGE?` | `ERR:CACHE_INVALID` |
| 39 | `BATT_TTL_CHARGE?` | `ERR:CACHE_INVALID` |
| 40 | `TOTAL_BATT_TEMP?` | `ERR:CACHE_INVALID` |
| 41 | `BATT_TEMP_AVE?` | `ERR:CACHE_INVALID` |
| 42 | `BATT_TEMP_MAX?` | `ERR:CACHE_INVALID` |
| 43 | `BATT_TEMP_MIN?` | `ERR:CACHE_INVALID` |

- This result is consistent with the Cache starting INVALID after power-on.
  To exercise value formatting and decoded values, an explicit `DATA_REFRESH`
  is required. OI-03 (D0/CHARGE_END side effect) remains open, so D0 was not
  sent as part of this query-only check. No Open Issue was closed.

## 2026-11-07 DATA_REFRESH and all DATA Cache Queries (COM19)

- The operator explicitly authorized D0 transmission. `TEST_START` returned
  `OK`, `DATA_REFRESH` returned `OK`, all 43 DATA Cache Queries returned a
  complete CRLF response, and `TEST_END` returned `OK`. No query timed out.
- D0 transaction: T2=600ms provisional, transaction result `OK`, command retry
  0, response retry 0, elapsed 238ms, ambiguous False. The D0 NF55G timestamp
  decoded as `20260401_021253`; this is the received product data, not an
  independently verified current time. Logger filename timestamp was
  `20261107_181051`.
- Host transcript with TEST_START, D0, every query and Ans, and TEST_END:
  [temp/20261107_181100_data_cache_ate.csv](../temp/20261107_181100_data_cache_ate.csv)
  (46 data rows, 4,250 bytes, SHA-256
  `2c76ae9bddf818daf892e239dc52c2364e0062f7a3fd4c181bfb0e76e00a4107`).
- Retrieved Pico SD logger CSV with D0 raw TX/RX and transaction row:
  [temp/20261107_181051_pico_sd.csv](../temp/20261107_181051_pico_sd.csv)
  (1,447 bytes, SHA-256
  `4adfc452a16dc4825a955e1fb07314a3c975cfe0e1894ae450730eb87e3a4664`).
- The 43 ATE Query Ans are preserved in the host transcript; the SD logger
  records NF55G raw frames and transaction metadata, not ATE Query lines.
  OI-03 remains Open despite this explicitly authorized test; no product
  PASS/FAIL was assigned and no other control, SC, D2, D3, D4, or FU command
  was sent.
- After copying the SD CSV, Pico was reset to restart `/main.py`. A final COM19
  `*IDN?` returned `NF55G_PICO_FIXTURE,Rev.0\r\n`, confirming ATE service
  resumed.

## 2026-11-09 通信ポート変更・ローカル応答確認

- ユーザー指定により、以後の本案件の接続はATE側COM20、Pico 2 USB保守側COM14とする。過去のCOM19等は当時の記録として維持する。
- 08:40 JSTのpySerial列挙: COM20=Elecom USB-Serial Converter（VID:PID 056E:5004）、COM14=Pico USB（VID:PID 2E8A:0005、SER 2D35A1E11AC125E3）。
- COM20: 115200bps／8N1／フロー制御なし、DTR・RTS無効。*IDN? → NF55G_PICO_FIXTURE,Rev.0、COMM_STATUS? → OK:state=IDLE、SD_STATUS? → OK。全応答CRLF完結。ATE↔Pico UART0の要求・応答を確認。
- COM14は開放状態でopen/read/close成功。受信0byte。実行中アプリを維持するため送信・Ctrl-C・REPL割込み・resetは行わず、USB REPLの双方向応答自体は今回未確認。
- ポートはいずれもclose済み。Picoへの配置、TEST_START／TEST_END、SD復帰、NF55GへのRefresh／Control／FU送信は実施していない。搭載FWと今回変更済みHostソースの一致は未確認。
- 実測原本: [通信確認JSON](../temp/serial_port_check_20261109.json)。再現用: [確認スクリプト](../temp/serial_port_check_20261109.py)。ハードウェア通信確認のためHost／Mock再実行なし。製品PASS/FAILは判定していない。

## 2026-11-09 変更レビュー・SD抜き差し・D3/D4実機確認

### 前提・配置・修正
- ユーザーが実機サンプル接続と電源ONを確認。ATE=COM20、Pico USB=COM14。QR/DMMはマイコン入手後の別開発・結合試験とする。
- Pico2/RP2350、MicroPython v1.28.0、unique ID 2d35a1e11ac125e3を確認。既存25ファイルを退避し、変更ソースを配置・読戻し一致確認。追加修正後も全25ファイル一致。[最終hash一覧](../temp/hil_20261109_run01/final_deployment_manifest.json)、[退避先](../temp/hil_20261109_run01/pico_before/)。作業ツリーの開発版でありcommit 38a5648と同一とは扱わない。
- レビューでATE受信層の拒否ログ漏れをRECEIVE_ERRORで補正。実機でTEST_ENDがBUSYなのに先行OKが残る問題を発見しEND_REQUESTへ修正。応答期限境界の部分RAW・ACK待ち異常byteも記録。T1/T2・再送・ACK/NAK・Cache昇格方針は変更していない。
- Host Unit Test／Mock NF55G Test全198件成功、git diff --check合格。配置時にsoft resetを2回実施。物理電源切入・フォーマット・既存ログ削除はしていない。

### 確認できた事実
- 日時ログ: TEST_START=OK、試験中SD_REINIT=ERR:BUSY、TEST_END=OK、最終Self Check正常・破棄0。[通常CSV](../temp/hil_20261109_run01/20261109_084638.csv)は9行（ATE要求・結果・終了前Self Check）。
- ユーザーのSD抜去完了後、WRITE_ERRを検出してもATE ID／RTC応答を継続。SD_REINITはERR:BUSY。同じカードの再挿入後も試験中はWRITE_ERRを保持。TEST_END後にSD OKへ復帰したが、Self CheckはLOGGER=OK;TEST_LOGGER=WRITE_ERR;TEST_LOG_DROP=19を保持。故障セッションCSVは開始部分のみ217byteであり、全ログ保存とは扱わない。
- 復帰後の次試験でログ作成を再開。正常な後続試験のTEST_LOG_DROPはOK。累積19件と各試験の破棄0件を区別。
- D3を1回実行しOK。DATA21文字、TX BCC74／RX BCC4C一致、cmd/rsp retry=0/0、elapsed31ms、ambiguous=False。D3 Cache VALID/source D3。LIFE_BATT_TEMP=25、CHARGE_DATA／CHARGE_END／LIFE_BATT_CHARGE／LIFE_BATT_DEG／EVENT_LOSTは0。DATA INVALID（開始前からINVALIDのためVALIDからの遷移の実機証明ではない）。[D3 CSV](../temp/hil_20261109_run01/20261109_084843.csv)。
- D4は2回のATE要求で確認（各要求に規定Command Retry1回）。両方ACK_TIMEOUT、ambiguous=True、elapsed114/115ms、D4とDATA Cache INVALID。後続完全フレームはDATA212文字・BCC一致。再確認ではACKから約102ms後に170byteの部分RAW、直後の再送ACK待ちで0x20を記録。[初回D4 CSV](../temp/hil_20261109_run01/20261109_084905.csv)、[再確認D4 CSV](../temp/hil_20261109_run01/20261109_085333.csv)。
- 初回D4後のTEST_ENDはERR:BUSYとなり、通信待機後の再要求で正常終了。初回CSVの先行OKは上記修正対象の原本として維持。[修正後通常CSV](../temp/hil_20261109_run01/20261109_085254.csv)ではEND_REQUESTと最終Self Checkを確認。
- 全CSV6本を回収。[SHA-256一覧](../temp/hil_20261109_run01/sd_file_manifest.json)、[ATEとPicoの実測原本](../temp/hil_20261109_run01/events.jsonl)。
- 最終状態: TEST終了、app.run稼働、COM20 ID応答正常、通信IDLE、SD OK、最終Self Check OK。PC側COM14/COM20はclose済み。最終配置時のsoft resetにより以前のCacheと累積drop countは初期化。過去の試験結果はPC記録に保持。

### 推測・未確認事項
- D4 Timingの根本原因は未確定。製品送出とPico受信負荷の切分けが必要。Pico上のPython Mock再生もRESP_TIMEOUTになったが、Mockの計算負荷を含むため実UARTの代替証拠ではない。Open Issue D4-TIM-01を追加。
- D3のLIFE_CALC clear、D4のAC_FAIL_COUNT clear副作用を踏まえて実施したが、前後比較での副作用検証はしていない。遅延D4をVALID Cacheへ昇格していない。
- SDなし電源投入／新規TEST_START、別カード交換、冷間CMD0、量産波形Timing、QR/DMM結合は未確認。製品PASS/FAILは判定していない。
- NF55Gへ送信した今回の試験対象はD3/D4のみ。SC・充電制御・D0・FU・追加CLEAR等は送っていない。D4内の製品時刻とPico/PCの現在時刻を混同しない。

## 2026-11-09 CLEAR4種の実装・実機確認

### 前提・変更
- ユーザー指定によりD4は副作用のため量産では使用しない。D4-TIM-01は未解決のまま保持し、今回はD4を送信していない。
- ユーザーがバッテリ未接続での通信テストを指定。COM20=ATE、COM14=Pico USB。r1 p.35のCDによる満充電情報等の消去・初期充電への影響を説明して確認した。
- Parser／BuilderへCLEAR_POWER（CD/1）、CLEAR_BATT（CD/2）、CLEAR_ALL（CD/0）、CLEAR_LOG（CL/DATAなし）を追加。CD T2=500ms、CL T2=1000ms、正常応答DATA0文字を適用。関連Cacheは成功／ambiguous時に無効化し、応答からCacheへ昇格しない。
- Host Unit Test／Mock NF55G Test全203件合格。正常、T2、Cache、SQE、不正引数の無送信、異常応答へのplain NAKを検証。
- 変更3ファイルを[退避](../temp/hil_clear_20261109_run01/pico_before_clear/)して配置、全25ファイルを読戻し一致確認。[配置hash](../temp/hil_clear_20261109_run01/final_deployment_manifest.json)。soft reset後のappを用いた。

### 確認できた事実
- CLEAR_POWER: CD DATA1、OK、19ms。電源稼働時間6→0、瞬断数350→0、バックアップ数74→0。バッテリ側接続時間6・放電回数269・積算放電量14604・積算充電量998等は維持。TOTAL_ADU_TEMPは161のまま（r1 p.41ではCD初期化不可）。
- CLEAR_BATT: CD DATA2、OK、19ms。接続時間6→0、放電回数269→0、積算放電量14604→0、積算充電量998→0、積算温度150→0、平均温度25→0。最高温度127→25、最低温度9→25。温度を含め全項目0とは扱わない。
- CLEAR_ALL: CD DATA0、OK、20ms。電源・バッテリの対象積算値は0を維持、TOTAL_ADU_TEMPは161、最高／最低バッテリ温度は25。先行POWER／BATTで対象値が既に0だったため、ALL単独で非ゼロ値を全消去する検証とは区別する。
- CD3種の直後、DATAのNF55_DATETIME?とSTATUSのPS_ON?はいずれもERR:CACHE_INVALID。その後、明示DATA_REFRESH（D0）／STATUS_REFRESH（D1）で再取得し前後を記録。Queryから自動Refreshしていない。
- CLEAR_LOG: CL DATAなし、OK、19ms。消去前にEL32件／OL64件を全12ブロック退避。直後は全EL／OL Cache INVALIDを確認し、再取得後に96件全て日時00000000・ID FFを確認。
- EL／OL取得は今回の診断スクリプトから共通Protocolを直接使用した。正式ATEのEL_REFRESH／OL_REFRESH入口を今回新規実装したことにはならない。履歴Noはr1ルール②に従い数値17→ASCII 11、25→19等で送信し、応答開始番号も照合。取得データから一旦VALID化してCL直後の無効化を確認し、その後の明示再取得でVALID化。
- CD／CLは全て正常応答DATA0文字、BCC一致、command retry0、response retry0、ambiguous=False。SD CSV4本の全NF55フレームもBCC一致。各試験のSelf Check正常、SD OK、ログ破棄0、通信IDLE。CLEAR_LOGは製品内部ログの消去であり、SDの試験CSVは保持した。

### 記録と未確認事項
- [前後値・時間・CSV hash集計](../temp/hil_clear_20261109_run01/clear_summary.json)、[ATE/Pico実測原本](../temp/hil_clear_20261109_run01/events.jsonl)、[消去前の製品ログ](../temp/hil_clear_20261109_run01/product_logs_before_clear.json)、[消去後](../temp/hil_clear_20261109_run01/product_logs_after_clear.json)。
- 実CSV: [POWER](../temp/hil_clear_20261109_run01/20261109_092553.csv)、[BATT](../temp/hil_clear_20261109_run01/20261109_092620.csv)、[ALL](../temp/hil_clear_20261109_run01/20261109_092639.csv)、[LOG](../temp/hil_clear_20261109_run01/20261109_092804.csv)。
- 電源切入後の保持、接続バッテリでの充電動作・保持情報・CHARGE_OK信号、CLEAR_ALL単独の非ゼロ値消去、異常状態での実機SQE／PMEは未確認。製品PASS/FAILは判定していない。
- D0のCHARGE_END副作用（OI-03）は未解決のまま。CD前後の状態保存・再取得としてD0を明示実行した。D4・SC・FU・充電制御・SDフォーマットは実施していない。

## 2026-11-09 Pico RTC ATEコマンド確認（製品コマンド送信なし）

- ユーザー指定: 製品に影響しないPico側コマンドから確認し、ログをtempへ順次コピーする。製品動作・出力に関わる今後の試験では、送信時に確認項目を伝え、ユーザーの実測結果を受け取る。
- COM20経由、115200bps/8N1/CRLF。RTC_DATE? → 20261109、RTC_TIME? → 094508。RTC_DATETIME?も20261109_094508、RTC_CHECK?はOK。PCの同時刻は約09:45:18 JSTで、設定前のRTCは約10秒遅れていたという観測。
- PC現在日本時間をもとにRTC_SET_20261109_094520を送信しOK。直後のRTC_DATETIME?=20261109_094520、RTC_DATE?=20261109、RTC_TIME?=094520、RTC_CHECK?=OK。設定指定値との秒差0、読戻し受信完了のPC時刻との差-1.260秒。秒分解能・逐次取得の比較であり、精密同期や長期精度の検証ではない。
- 読出し試験・設定試験を別のTEST_START/TEST_ENDで記録し、終了ごとにSDログをCOM14から回収してtemp直下へコピー・内容一致確認。日時ファイル名は各試験開始時のRTC値のため、設定試験のファイル名も設定前の時刻を保持。
- [読出しCSV](../temp/20261109_094507.csv): 13行、969byte、SHA256 11bca3a951c69cb591b00bf89f693196649d7727080b8d432eb3bdb4aa16cbea。
- [設定CSV](../temp/20261109_094510.csv): 15行、1098byte、SHA256 2a5d9f69cc69bbf0b764567043ec889016877d375cfa2984149ead92dff8bec3。
- [結果JSON](../temp/RTC_Test_Result_20261109_094516.json)、[TX/RXとPC時刻の原本](../temp/hil_rtc_20261109_094516/events.jsonl)。両CSVのNF55Gコマンド送信RAWは0件。NF55GのSC/CLOCK_SYNC・Refresh・制御は送信していない。
- 各試験のSelf Check正常、ログ破棄0、最終通信IDLE・SD OK。app.runを再開し、PC側COM14/COM20はclose済み。ファームウェア変更なし、Host/Mockの再実行なし（直前203件合格）。
- 未確認: 今回設定後の物理電源切入・バックアップ保持、長期RTC精度。過去のRTC電源保持試験と今回のATE設定試験は区別する。

## 2026-11-09 LOG_CONT_START／LOG_CONT_STOP実機確認

- ユーザー了承によりPico側の連続ログを確認。COM20=ATE、COM14=保守。NF55Gへコマンドを送らない条件で、RTC_DATE?／RTC_TIME?を繰り返した。ファームウェア変更なし、Host／Mock再実行なし。
- 1回目: LOG_CONT_START=OK、二重開始=ERR:BUSY、記録中SD_REINIT=ERR:BUSY。RTC日付・時刻を4組取得し、1秒間隔を置いて記録。停止前はactive=True、mode=CONT、test_running=False、queue=0、file_open=True、ファイルサイズ1297byteを確認。
- LOG_CONT_STOP=OK後、active=False、mode=None、queue=0、file_open=False、1351byteを確認。開始／RTC要求・結果／停止要求を含む23行を読戻し。[1回目CSV](../temp/20261109_095446.csv)、SHA256 7d298cb680231f227418ccf1c6831c08df6c0e2ae6c85ddc6ca12ba2b91c0621。
- 2回目: 再開始=OK、別の日時名ファイルを作成。RTCを2組取得、停止前649byte・queue0、LOG_CONT_STOP=OK後703byte・close済みを確認。[2回目CSV](../temp/20261109_095455.csv)は11行、SHA256 4e4335af297bf093719e0b9f05df7a3b60042566f1d352966474cc9f5b54848b。
- 各停止後にSDからPCへ回収し、temp直下へ順次コピー・内容一致確認。停止応答OKの原本はホストのTX/RX記録に保存する。CSVは停止要求までの記録であり、close後の応答を同じファイルへ追記していない。
- 2本ともNF55Gコマンド送信RAW0件、ログ破棄は開始前0→終了後0。最終COMM_STATUS=IDLE、SD_STATUS=OK、PICO_SELF_CHECK正常。Self CheckのTEST_LOGGER項目は直前のTESTセッション由来であり、今回CONT専用の最終履歴とは扱わない。
- 証跡: [TX/RX・Pico状態原本](../temp/hil_log_cont_20261109_095446/events.jsonl)、[結果JSON](../temp/hil_log_cont_20261109_095446/log_cont_result.json)。同一app.runを再開し、PC側の両ポートはclose済み。
- 確認範囲は短時間の開始・定期保存・停止・再開始。長時間記録、100MBロールオーバー、電源断保持、連続記録中の実カード抜去は今回未確認。
