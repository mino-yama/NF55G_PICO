# Open Issues
Revision: Rev.0
Codex must NOT close these by inference.

| ID | Issue | Rev.0 implementation |
|---|---|---|
| OI-01 | Pico-side T1 final value | 200 ms provisional |
| OI-02 | D0 T2 list=300ms vs detail=600ms | use 600 ms provisional |
| OI-03 | Current FW may clear CHARGE_END after D0 ACK | implement D6 non-destructive D0; confirm FW |
| OI-04 | AR REF 8-char final wire format | preserve raw8; pluggable decoder |
| OI-05 | AD runtime coefficient immediate reflection vs reboot | no automatic reboot; confirm |
| OI-06 | BC=0 STOP current FW behavior | implement spec; confirm final FW |
| OI-07 | BC MODE=13 response details | expose received data; confirm |
| OI-08 | SL out-of-range PME behavior | spec/FW confirmation |
| OI-09 | OR request while restart already active | current FW SQE; confirm |
| OI-10 | FD out-of-range address | current FW FF fill; confirm formal behavior |
| OI-11 | EB timing while command transaction active | keep original deadline; HIL confirm |
| OI-12 | AR T2 final value | confirm before final release |
| OI-13 | RTC HAT revision pin mapping | verify I2C scan 0x68 on received hardware |
| OI-14 | UNIT_ID source for future filename extension | product FW read vs barcode undecided |
| OI-15 | Detailed USB CDC/PySide6 protocol | deferred phase |
