# CHANGELOG

## Rev.0 - 2026-09-01
Initial Codex handoff baseline.

Included:
- ATE command architecture
- explicit Refresh + Cache
- Data Decode master
- Cache invalidation/post-check rules
- Pico software module boundaries
- Protocol state machine
- Command Retry / Response Retry separation
- ambiguous transaction policy
- Mock NF55G and host test plan
- Logger/SD formal specification
- FU hard prohibition
- ATE priority rule
- USB CDC detailed implementation deferred
- Fixed implementation phase order in `docs/Implementation_Plan.md`
- Defined development vs production source versioning policy

Initial implementation start:
- Added `src/config.py` constants for frame bytes, timing, retry, cache names, and invalidation policy.
- Added `src/models.py` lightweight shared model classes.
- Added `src/frame.py` for NF55G frame build/parse and BCC calculation.
- Added `src/nf55_decode.py` pure decoders for D0/D1/D2/D3/D4/D5/BC/EB/EL/OL/AR/FD.
- Added `src/cache_manager.py` for power-on invalid cache state, validate/invalidate, refresh failure, and control ambiguous/success invalidation.
- Added initial host `unittest` coverage for frame/BCC, cache, and decode basics.
- Expanded decoder unit tests to cover D0/D1/D2/D3/D4/D5/BC/AR/EL/OL/FD normal lengths, wrong lengths, key numeric conversions, status bit decode, FD raw preservation, and EL/OL START_NO mismatch.
- Added comprehensive D0 Golden Data assertions covering TIME, REALTIME, OFF, LIFE_CALC, LIFE_DIAG, ACCUMULATED, MFG raw/decode, PARAM raw/decode, and STATUS raw/decode.
- Added host-side Mock NF55G with `FakeClock`, `MockUART`, `ResponseFactory`, and scenario steps for ACK, NAK33, ACK_TIMEOUT, RESP_TIMEOUT, BCC NG, PME, SQE, and HWE.
- Added `src/nf55_protocol.py` transaction state machine covering WAIT_ACK, WAIT_RESPONSE, VALIDATE_RESPONSE, COMMAND_RETRY, RESPONSE_RETRY, SUCCESS, and FAILED paths with host unit tests.
- Added control command/cache integration for CHARGE_ON, CHARGE_OFF, BACKUP_ENABLE, OUTPUT_RESTART, PARAM_SET, and related control commands, with tests for success invalidation, parser rejection, PME/SQE no-invalidation, HWE/ambiguous invalidation, and no automatic post-refresh.
- Added Logger/SD core with RAM queue, host memory SD sink, TEST_START/TEST_END, LOG_CONT_START/LOG_CONT_STOP, SD_STATUS?, SD_USAGE?, LOG_DROP_COUNT?, SD_REINIT, forced drain on TEST_END, drop counting, and no write/flush while protocol busy.
- Recorded separate SD real-hardware debug checklist for Mount, CSV creation, Write, Flush, Close, continuous logging, card removal, write error, and reinitialization.
- Added Pico-side RTC command support for RTC_DATE?, RTC_TIME?, RTC_DATETIME?, RTC_SET_YYYYMMDD_HHMMSS, and RTC_CHECK? using a DS3231 abstraction, explicitly separate from NF55G SC/CLOCK_SYNC.
- Added Pico/MicroPython `DS3231I2CDevice` access for I2C0 GP20/GP21, including BCD datetime read/write and OSF clear, with host fake-I2C tests.
- Added and consolidated AD/AR Open Issue review notes, including interim FW analysis, into OI-16 through OI-21 plus OI-04/OI-05 refinements for production FW/design confirmation.
- Added HW-01 for the ADA-5703 PiCowbell GP4/GP5 physical conflict with Pico-2CH-RS232 NF55G UART1, and noted that disabling PiCowbell RTC in software is not sufficient.
- Added a first-step real-hardware debug notice and T8 pre-check requiring ADA-5703 GP4/GP5 physical isolation before final fixture UART/SD debug.
