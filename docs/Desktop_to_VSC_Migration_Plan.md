# Desktop Codex to VSC+Codex Migration Plan
Revision: Rev.0-draft
Date: 2026-09-04

## 1. Purpose
本書は、Desktop 版 Codex で実施する開発範囲と、VSC+Codex へ移行して実機を使用する範囲を明確にし、移行時点のステータス、Gate、引き継ぎ資料、残 Issue を管理するための文書である。

## 2. Migration Decision
Desktop 版 Codex から VSC+Codex への移行は可能であり、現計画と矛盾しない。

理由:
- `docs/Implementation_Plan.md` は T0-T7 を host PC unit/integration test、T8/T9 を実機依存 Gate として定義している。
- Desktop 版 Codex は host/mock 開発、仕様整理、Pico 単体 smoke、文書更新に適している。
- VSC+Codex は実機 UART wiring、Pico firmware 配置、REPL/serial 操作、NF55G 実機 HIL、長時間 SD logger、故障注入を継続する環境として適している。

ただし、移行後も `AGENTS.md` の Hard Rules を最上位ルールとし、D6 仕様との差異を Pico 側で独断吸収しない。

## 3. Scope Boundary

### Desktop Codex scope
- T0 Parser
- T1 Frame/BCC
- T2 Protocol state machine
- T3 Decoder
- T4 Cache
- T5 Command integration
- T6 Mock NF55G end-to-end
- T7 Safety
- Pico 2 単体での非破壊 smoke:
  - USB CDC / MicroPython REPL recognition
  - DS3231 I2C scan/read/write
  - SD SPI recognition, FAT mount, CSV write/readback
  - UART peripheral initialization

### VSC+Codex scope
- T8 Pico hardware continuation:
  - ATE UART0 GP0/GP1 loopback
  - NF55G UART1 GP4/GP5 38400 bps 8E1 loopback
  - final fixture firmware transport/scheduler integration
  - SD logger final queue path duration/load test
  - SD card removal, write-error, reinitialization tests
  - final fixture GP4/GP5 isolation inspection record
- T9 Real NF55G HIL:
  - D0/D1/D5/BC/AR/EL/OL/FD read confirmation
  - EB timing measurement
  - control command tests only after safety procedure approval
  - Open Issue confirmation against production FW/design

## 4. Current Status at Migration Preparation

### Repository status
| Item | Status | Note |
|---|---|---|
| Branch | INFO | Confirm with `git branch --show-current` at handoff time |
| Uncommitted changes | WARNING | `docs/ATE_Command_List_for_Test_Program.docx` was already modified before this document update; do not overwrite without confirming ownership |
| Host test suite | PASS | 2026-09-04: `python -m unittest discover -s tests -v`, 76 tests OK |

### Phase status
| Phase | Status | Evidence / Note |
|---:|---|---|
| 1 共通モデル・定数 | COMPLETE for host baseline | `src/models.py`, `src/config.py`, host tests |
| 2 BCC / Frame Builder / Parser | COMPLETE for host baseline | T1 tests pass |
| 3 Data Decoder | COMPLETE for host baseline | T3 tests pass for D0/D1/D2/D3/D4/D5/BC/AR/EL/OL/FD |
| 4 Cache Manager | COMPLETE for host baseline | T4 tests pass |
| 5 Mock NF55G | COMPLETE for host baseline | T6 tests pass |
| 6 Protocol State Machine | COMPLETE for host baseline | T2/T7 protocol tests pass |
| 7 ATE Command Parser / Dispatcher | PARTIAL/COMPLETE for covered host commands | Control/cache/RTC/logger paths covered; final transport integration pending |
| 8 NF55G Command Builder | PARTIAL | AD/AR and production FW confirmation remain open |
| 9 Logger / SD | HOST COMPLETE, HARDWARE PARTIAL | Host queue/sink tests pass; Pico SD mount/write/readback verified; removal/error/reinit pending |
| 10 RTC | HOST COMPLETE, HARDWARE PARTIAL | DS3231 I2C/read/write/battery verified; re-run after final firmware pending |
| 11 Pico UART Hardware Layer | PENDING/PARTIAL | UART peripheral init verified; loopback and final hardware layer source pending |
| 12 Real NF55G Integration | PENDING | No real NF55G HIL transaction executed |

### Hardware status
| Item | Status | Note |
|---|---|---|
| Pico 2 / RP2350 identity | PASS | MicroPython v1.28.0, `Raspberry Pi Pico2 with RP2350` observed |
| DS3231 on I2C0 GP20/GP21 | PASS | Address `0x68` detected; read/write verified |
| DS3231 backup battery | PASS for one power-cycle check | Re-run after final firmware and stack changes |
| SD on GP16-GP19 | PASS basic I/O | SPI recognition, FAT mount, CSV write/readback, continuous smoke verified |
| ADA-5703 GP4/GP5 conflict | OPEN | GP4/GP5 physically isolated during tests; final fixture inspection record still required |
| ATE UART0 loopback | PENDING | GP0 <-> GP1 |
| NF55G UART1 loopback | PENDING | GP4 <-> GP5, 38400 bps, 8E1 |
| Real NF55G connection | NOT STARTED | Control commands not executed |

## 5. Migration Gate
VSC+Codex へ移行する前に、以下を確認する。

| Gate | Condition | Status |
|---|---|---|
| M1 | `AGENTS.md`、Master docs、Open Issues が最新である | READY |
| M2 | Host test suite が PASS している | READY: 76 tests OK on 2026-09-04 |
| M3 | 実機前提の残作業が T8/T9 として分離されている | READY |
| M4 | 未確定事項が `docs/Open_Issues.md` に残っている | READY |
| M5 | VSC 側で使う handoff checklist がある | READY with this document |
| M6 | Git worktree の未コミット変更の所有者が明確である | ACTION REQUIRED: existing docx modification |

## 6. VSC+Codex Start Checklist
VSC+Codex 側の最初の作業で以下を行う。

1. `AGENTS.md` を最上位ルールとして読む。
2. `HANDOFF_MANIFEST.txt` に記載された core handoff files を読む。
3. 本書の Current Status と Migration Gate を確認する。
4. `git status --short` を確認し、Desktop 版 Codex からの未コミット差分とユーザー差分を混同しない。
5. `python -m unittest discover -s tests -v` を再実行し、T0-T7 baseline を再確認する。
6. `docs/Real_Hardware_Test_Log.md` の最新 T8 記録を確認する。
7. GP4/GP5 の最終 fixture isolation 状態を目視または検査記録で確認してから UART/NF55G 実機接続へ進む。
8. UART loopback を ATE 側、NF55G 側の順に行う。
9. final fixture firmware の transport/scheduler 統合後、RTC/SD を再検証する。
10. Real NF55G HIL は T8 loopback と安全手順確認後に開始する。

## 7. VSC+Codex First Work Items
優先順:

1. `docs/ATE_Command_List_for_Test_Program.docx` の既存変更の扱いを確認する。
2. UART loopback 手順を `docs/Real_Hardware_Test_Log.md` に追記できる形で実行する。
3. Pico hardware UART/I2C/SD transport layer source または final firmware placement path を決める。
4. SD removal/write-error/reinitialization の安全な fault-injection 手順を作る。
5. Real NF55G HIL checklist を control command safety procedure と分離して作る。

## 8. Required Records During VSC+Codex Work
VSC+Codex で実機作業を行うたびに、以下を記録する。

- Date/time
- Hardware stack and firmware image/source revision
- Wiring state, especially GP4/GP5 isolation
- Executed command or script
- Raw serial frame or raw response where relevant
- Result: PASS/FAIL/INFO/WARNING
- Whether NF55G control command was sent
- Whether `FU` was blocked
- Cache invalidation impact if applicable
- Open Issue reference
- Next action

## 9. Risks and Controls
| Risk | Control |
|---|---|
| Desktop/VSC 間で未コミット差分が混ざる | 移行時に `git status --short` と差分所有者を確認する |
| 実機差異を Pico 実装で吸収してしまう | `docs/Open_Issues.md` に記録し、人間確認まで Close しない |
| GP4/GP5 conflict が再発する | UART/NF55G 作業前に final fixture isolation record を必須にする |
| Query が自動 Refresh を呼ぶ | T5/T7 host tests と code review で維持する |
| Control command を安全手順前に実行する | T9 checklist で read-only HIL と control HIL を分離する |
| Logger/SD が通信 timing を阻害する | final firmware で protocol busy 中の SD write/flush 禁止を再検証する |

## 10. Open Issue Handling
移行により Open Issue を Close しない。

特に VSC+Codex 移行後に確認が必要な項目:
- OI-03: D0 ACK 後の CHARGE_END 挙動
- OI-04/OI-16 through OI-21: AD/AR final FW/design
- OI-11: EB timing while command transaction active
- OI-12: AR T2 final value
- OI-13: RTC pin mapping confirmation record
- HW-01: GP4/GP5 final fixture isolation method and inspection record

## 11. Handoff Summary
現時点では、Desktop 版 Codexで PICO 単体および host/mock の事前確認を進め、VSC+Codex で T8 continuation と T9 Real NF55G HIL を行う分担に問題はない。

移行時の最重要条件は、未コミット差分の所有者確認、T0-T7 再実行、GP4/GP5 isolation record、Real NF55G control command safety procedure の 4 点である。
