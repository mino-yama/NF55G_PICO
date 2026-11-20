# External instrument USB Host diagnostic firmware

This is a separate RP2350-USB-A project for CDC ACM Host evaluation. It does not modify or replace the QR Host firmware.

The IDN diagnostic firmware is limited to:

- PIO USB Host on GPIO12/13 and TinyUSB root port 1.
- CDC ACM enumeration and VID/PID/interface logging.
- 9600/8N1 line coding and DTR/RTS setup, with transfer completion checked.
- One `*IDN?` plus CRLF request to the expected 7355 VID/PID. It is never retried.
- Raw response bytes logged as hex through diagnostic UART0 TX on GP0 at 115200/8N1.

It does not initialize QR, accept parent-Pico commands, control the production ATE link, or transmit commands to the NF55G. It does not configure measurement ranges or perform measurement commands. The product identity query and external UART output are for standalone evaluation only.

## Single-point DC voltage evaluation profile

The separate `usb_submcu_external_meter_voltage_test.uf2` target (`meter-host-voltage-test-20261120.5`) is a one-run evaluation profile for one known low DC input. It uses SCPI over the same USB-A PIO Host and TX-only diagnostic UART. After a matching CDC device is mounted, it checks IDN, reads the existing system error queue, sets continuous initiation off, aborts, selects DC voltage, selects fixed 20 V range, checks the SCPI error queue, then queries `:CONF?` and requires its reported full-scale value to be between 19 V and 21 V before continuing. A different/unrecognized range stops the sequence before `:READ?`. It then sets immediate trigger and one trigger/sample, sets zero trigger delay, checks the error queue, sends exactly one `:READ?`, and checks the error queue once more. Each query is completed before the next command; commands are not retried. Any timeout, overflow, unexpected setting response, or nonzero SCPI error code stops the sequence. Version .1 stopped before READ because it rejected the valid quoted `"VOLT:DC"` response. Version .2 stopped because it text-compared `00001` with `1`; version .3 added numeric comparison but was not run. Version .4 also gates READ on the range readback.

This profile changes instrument state and does not restore prior settings. On completion it leaves DCV, fixed 20 V range, AUTO off, continuous initiation off, immediate trigger, trigger/sample count 1, and trigger delay 0. Record the initial state and arrange any required manual restoration. The observed `:CONF?` response for version .2 was `"VOLT +1.999999E+02,+1.000000E-05"`, which appears to indicate approximately 200 V rather than 20 V; confirm the instrument display and range command behavior. Version .4 stops before READ unless the returned full-scale field is approximately 20 V. The `:READ?` response is raw evidence only and does not assert measurement accuracy or product PASS. The existing `usb_submcu_external_meter_host.uf2` remains the IDN-only profile. Version .3 is installed but has not been run; do not power it with the instrument connected. Version .4 is preserved in the handoff archive. Version .5 is the new deployment candidate.

Build all profiles with `scripts/build_usb_submcu_external_meter_host.ps1`. The build is separate from `firmware/usb_submcu_host_probe` and uses the pinned Pico SDK 2.2.0, the existing reviewed Pico-PIO-USB source, and the local ARM GCC toolchain. The build script does not flash a board.

UF2 build artifacts and the initial deployment/verify record are in the build output and `build_manifest.json`. Before a hardware trial, verify the RP2350-USB-A board identity, R13 removal and surrounding components, and power isolation. The development USB-C and USB-A VBUS/VSYS are common on the board; do not connect PC power and the external supply simultaneously. The previous all-flash backup is in `docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/RP2350_USB_A_20261116/Flash_Backup_20261119/`.

Firmware build success and the recorded UF2 deployment do not prove USB enumeration, CDC communication, measurement accuracy, Host electrical acceptance, or production readiness. This project build script itself only builds and does not flash a board.
## 2026-11-20 handoff update

Version .5 extracts setting-number and CONF validation into `scpi_response_validation.c`, which is also compiled by native Host tests. It accepts zero-padded decimal settings while rejecting NaN/Inf, hexadecimal numbers, embedded NUL, malformed/incomplete/multiple CONF lines, and invalid resolution. The existing 19--21 V evaluation gate is unchanged; this is not an accuracy tolerance. The received approximately 200 V CONF response remains rejected even though the user reports a 20 V front-panel range. That discrepancy is Open Issue USB-CDC-RANGE-01. Commands and their order are unchanged.

Host Unit/Mock regression: 382 tests passed, including 7 new tests of the actual C validation module. This does not establish measurement accuracy, CDC hardware acceptance, or successful .5 hardware execution. No board was flashed in this handoff. See the [handoff record](../../docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Handoff_20261120_Rev0/Result_Rev0.md) for evidence, version history and resumption steps.

## Explicit-command UART relay profile (2026-11-20)

The independent `usb_submcu_external_meter_relay.uf2` target, version `meter-host-relay-20261120.1`, implements X1 on GP0 TX / GP1 RX at 115200/8N1. It performs CDC connection setup but sends no automatic IDN, range, or measurement commands. All instrument command bytes originate from explicit parent requests. X1 framing, CRC-32, boot session, request correlation and bounded queues are separate from the previous diagnostic/voltage-test targets. Plain diagnostic output is disabled on the relay UART.

The parent ATE entry supports `EXT_QUERY <timeout_ms> <body>` and `EXT_SEND <timeout_ms> <body>` asynchronously. Source configuration remains disabled until hardware preparation. A separate staged package enables it for HIL. Parent/Host startup identity and fail-stop recovery are documented in the [link implementation record](../../docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Result_Rev0.md). This firmware is built, not deployed or physically accepted. The existing voltage-test .5 and QR firmware are preserved.
