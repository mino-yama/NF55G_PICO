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
