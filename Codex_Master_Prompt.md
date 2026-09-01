# Codex Master Prompt - NF55G Pico 2

You are starting development of the NF55G Pico 2 production-test fixture.

## Mandatory startup procedure
1. Read `AGENTS.md` first and treat it as the highest-level development rule.
2. Read `README.md`.
3. Read all documents under `docs/`.
4. Read the final NF55G specification and original communication specification under `reference/`.
5. Treat NF55G source under `reference/` as evidence for implementation differences, not permission to silently override the formal specification.
6. Do NOT start implementation immediately.

## First task
Before writing code, produce a review report containing:
1. Your understanding of the system architecture.
2. ATE command categories.
3. NF55G command mapping.
4. Cache list and official update source.
5. Protocol state machine summary.
6. Command Retry vs Response Retry explanation.
7. Ambiguous execution handling.
8. Safety hard rules.
9. Open Issues list.
10. Any contradiction, missing information, or implementation blocker.

Do not infer answers to Open Issues.

## After human approval
Create an implementation plan only, using this order:
1. models/config
2. BCC/frame helpers
3. decoder
4. cache manager
5. Mock NF55G / FakeClock
6. protocol state machine
7. ATE parser/dispatcher
8. NF55 command builder
9. logger/SD
10. RTC
11. Pico UART/I2C hardware integration
12. HIL

## Development rules
- Small tasks and small commits.
- Code + tests + docs together.
- Run host tests after every meaningful change.
- Do not implement product PASS/FAIL.
- Do not send FU.
- Do not auto-refresh.
- Do not close Open Issues without human input.
- Do not implement detailed USB CDC/PySide6 in the initial phase.
