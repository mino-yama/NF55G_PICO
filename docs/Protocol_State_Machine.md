# Error Handling / Retry / Protocol State Machine

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.0

## Purpose
One NF55G transaction is managed as explicit states so that ACK/NAK, timeouts, response retransmission, errors, and ambiguous execution are deterministic.

## States
IDLE
PREPARE
TX_COMMAND
WAIT_ACK
WAIT_RESPONSE
RECEIVE_RESPONSE
VALIDATE_RESPONSE
TX_RESPONSE_ACK
TX_RESPONSE_NAK
WAIT_RESPONSE_RETRY
COMMAND_RETRY
SUCCESS
FAILED

## Normal sequence
IDLE -> PREPARE -> TX_COMMAND -> WAIT_ACK
ACK -> WAIT_RESPONSE -> RECEIVE_RESPONSE -> VALIDATE_RESPONSE
valid -> TX_RESPONSE_ACK -> SUCCESS -> IDLE

## Command Retry
Trigger:
- NF55G NAK30/31/32/33/35/36
- T1 ACK timeout
- T2 response timeout (Rev.0 permits one command retry)

Pico max command retry = 1.

## Response Retry
If NF55G response BCC/frame is invalid:
- Pico sends plain NAK 0x15 only.
- Pico does NOT immediately resend command.
- Wait for NF55G response retransmission.
- command_retry_count and response_retry_count are separate.

## Timing
- Pico T1 = 200 ms provisional.
- T2 starts after valid ACK.
- D0 T2 = 600 ms provisional.
- BC T2 = 6000 ms.
- Use deadline/ticks calculation, not decrementing sleeps.

## Error response
Valid NF55G error response frame receives ACK, then transaction result is failure:
CME, PME, SQE, HWE, MCM, FUE.

## Ambiguous
True for:
- ACK_TIMEOUT
- RESP_TIMEOUT
- final BCC/FRAME failure
- UART/COMM
- HWE treated safe-side

False for:
- parser rejection
- final NAK30-36
- CME/PME/SQE/MCM

Ambiguous control failure invalidates related caches.

## EB
EB is asynchronous.
- Decode and ACK separately.
- Never update STATUS cache.
- If EB arrives while waiting for normal response, do not reset original T2 deadline.
- Detailed real-unit timing remains Open Issue.

## State transition summary
| Current | Event | Next |
|---|---|---|
| IDLE | command | PREPARE |
| PREPARE | ready | TX_COMMAND |
| TX_COMMAND | sent | WAIT_ACK |
| WAIT_ACK | ACK | WAIT_RESPONSE |
| WAIT_ACK | NAK + retry | COMMAND_RETRY |
| WAIT_ACK | timeout + retry | COMMAND_RETRY |
| WAIT_ACK | final fail | FAILED |
| WAIT_RESPONSE | frame start | RECEIVE_RESPONSE |
| WAIT_RESPONSE | T2 timeout + retry | COMMAND_RETRY |
| RECEIVE_RESPONSE | complete | VALIDATE_RESPONSE |
| VALIDATE_RESPONSE | valid | TX_RESPONSE_ACK |
| VALIDATE_RESPONSE | BCC/frame NG | TX_RESPONSE_NAK |
| TX_RESPONSE_NAK | sent | WAIT_RESPONSE_RETRY |
| WAIT_RESPONSE_RETRY | response retry | VALIDATE_RESPONSE |
| WAIT_RESPONSE_RETRY | final fail | FAILED |
| TX_RESPONSE_ACK | sent | SUCCESS |
| SUCCESS/FAILED | result returned | IDLE |
