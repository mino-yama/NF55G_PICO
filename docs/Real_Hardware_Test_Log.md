# Real Hardware Test Log
Revision: Rev.0-draft

## Critical notice before any real-hardware debug
- Before powering or wiring the final fixture stack, confirm ADA-5703 PiCowbell GP4/GP5 are physically isolated from the Pico header/UART lines.
- GP4/GP5 are reserved for Pico-2CH-RS232 NF55G UART1. Do not start NF55G UART loopback, UART initialization, or real NF55G connection checks with ADA-5703 GP4/GP5 still connected.
- ADA-5703 microSD may be used only as the SD function on GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI after the GP4/GP5 isolation is verified.
- Track this as `docs/Open_Issues.md` HW-01 until the physical cut/isolation method and inspection result are recorded.

## 2026-09-02 Pico hardware smoke

### Scope
- T0-T7 host gate confirmation before hardware testing.
- Pico USB recognition check.
- Non-destructive USB response check.

### Preconditions
- Repository: `NF55G_Pico`
- Branch: `main`
- Hardware target: Raspberry Pi Pico 2 fixture bring-up path
- ADA-5703 GP4/GP5 isolation: must be confirmed before final fixture UART/SD debug
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
- ADA-5703 GP4/GP5 conflict remains governed by HW-01; SD-only pin operation GP16-GP19 is confirmed for this check.

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
