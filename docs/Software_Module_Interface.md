# Pico Software Module / Interface Specification
Revision: Rev.0

## Module layout
```text
src/
├─ main.py
├─ config.py
├─ ate_uart.py
├─ command_parser.py
├─ command_dispatcher.py
├─ nf55_uart.py
├─ nf55_protocol.py
├─ nf55_command.py
├─ nf55_decode.py
├─ nf55_event.py
├─ cache_manager.py
├─ rtc_driver.py
├─ logger.py
├─ diagnostic.py
└─ models.py
```

USB CDC detailed implementation is deferred. Architecture should allow a future `usb_console.py` to feed the same command core.

## Responsibilities
- main.py: init and scheduler only.
- ate_uart.py: ATE ASCII transport only.
- command_parser.py: syntax/parameter parsing.
- command_dispatcher.py: route to handlers.
- nf55_uart.py: physical byte I/O only.
- nf55_protocol.py: frame/BCC/ACK/NAK/retry/T1/T2/state machine.
- nf55_command.py: NF command table and wire DATA creation.
- nf55_decode.py: pure decode only.
- nf55_event.py: EB event handling only.
- cache_manager.py: cache valid/invalid/data/metadata.
- rtc_driver.py: DS3231 command wrapper, fake device, and Pico I2C0 GP20/GP21 hardware device access.
- logger.py: queue + sinks.
- diagnostic.py: fixture self-check; no product judgement.
- models.py: shared data structures.

## Core interfaces
`nf55_protocol.transact(cmd, data, t2_ms, expected_length) -> TransactionResult`

TransactionResult:
- ok
- cmd
- response_data
- error
- nak_reason
- command_retry_count
- response_retry_count
- ambiguous
- elapsed_ms
- raw_response

CacheManager:
- invalidate(name)
- invalidate_many(names)
- validate(name, data, source_cmd)
- is_valid(name)
- get(name)
- metadata(name)

DS3231RTC:
- date()
- time()
- datetime()
- set_from_ate(YYYYMMDD_HHMMSS)
- check()

DS3231I2CDevice:
- read_datetime()
- set_datetime(RTCDateTime)
- check()
- read_status()

Default Pico hardware pins:
- I2C0 SCL GP21
- I2C0 SDA GP20
- Address `0x68`

## Hard boundaries
- Decode module never updates cache.
- UART layer never decides command meaning.
- Command query never auto-refreshes.
- Logger never blocks protocol.
- Product PASS/FAIL is not implemented.
- ATE has priority over future USB console.
