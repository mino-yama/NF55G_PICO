# Test Specification / Mock NF55G Specification
Revision: Rev.0

## Goal
Before real NF55G connection, verify parser, protocol, decoder, cache, command integration and safety rules on host PC.

## Test levels
T0 Parser
T1 Frame/BCC
T2 Protocol state machine
T3 Decoder
T4 Cache
T5 Command integration
T6 Mock NF55G end-to-end
T7 Safety
T8 Pico hardware
T9 Real NF55G HIL

T0-T7 must pass before HIL.

## Required tests
### Protocol
- normal ACK/response/ACK
- NAK30-36 then one command retry recovery
- second NAK final error
- ACK timeout recovery/final
- response timeout recovery/final
- response BCC NG -> Pico plain NAK -> NF55 response retry
- command retry count independent from response retry count
- CME/PME/SQE/HWE/MCM/FUE
- wrong STX/CMD/length/ETX/BCC
- partial frame
- EB while idle
- EB while waiting response without resetting T2 deadline

### Decoder
- D0 327 chars
- D1 15
- D2 30
- D3 21
- D4 212
- D5 100
- BC 30
- AR 140
- EL/OL 82
- FD 64 ASCII HEX
- signed values
- scale mV->V, mA->A, 0.1h, 0.1%

### Cache
- power-on invalid
- refresh start invalid
- success valid
- failure invalid
- invalid query does not transmit NF55G
- D0 does not update STATUS or INFO
- control invalidation matrix
- ambiguous invalidation

### Safety
- FW_UPDATE -> ERR:FU_DISABLED and NF55 TX count 0
- no automatic D0/D1 after control command
- Pico never converts product state to PASS/FAIL
- logger does not block protocol

### SD real-hardware debug
Run as a separate debug/HIL check after SD hardware arrives. Do not treat host
`MemorySDSink` tests as completion of these items.
- Mount
- CSV creation
- Write
- Flush
- Close
- Continuous logging
- Card removal
- Write error
- Reinitialization

## Mock NF55G
Provide:
- MockUART
- FakeClock
- ResponseFactory
- Scenario engine
- stateful NF55 simulation for integration tests

Mock is a Pico test peer, not the authoritative product specification.
