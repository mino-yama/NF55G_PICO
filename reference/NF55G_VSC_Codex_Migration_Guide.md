# NF55G Pico 2 VSC+Codex Migration Guide
Date: 2026-09-04
Scope: ChatGPT / Desktop Codex / VSC+Codex staged workflow reference
Status: Reference material, maintained until VSC+Codex handoff; retained as a record after handoff

## 1. Purpose
本書は、NF55G Pico 2 試験治具開発を以下の段階で進める場合に、環境移行をスムーズに行うための説明・注意書きである。

| Stage | Main environment | Main work |
|---|---|---|
| 1 | ChatGPT | 資料集め、仕様整理、方針検討、Open Issue 洗い出し |
| 2 | Desktop Codex | host/mock 開発、Pico 単体 smoke、文書・テスト整備 |
| 3 | VSC+Codex | Pico 実機接続、UART loopback、final firmware integration、Real NF55G HIL |

この文書は直接の開発仕様ではなく、移行作業の参考資料である。実際の開発判断では、必ず `AGENTS.md`、各 Master docs、`docs/Open_Issues.md`、`docs/Desktop_to_VSC_Migration_Plan.md` を優先する。

VSC+Codex への引き渡し時点までは進捗に合わせて本書を更新してよい。引き渡し後は原則として記録として保管し、以降の実機作業の正本記録は `docs/Real_Hardware_Test_Log.md`、`docs/Open_Issues.md`、`docs/CHANGELOG.md` に残す。

## 2. Migration Policy
Desktop Codex から VSC+Codex への移行は、実機作業に入る段階で行う。

推奨境界:
- Desktop Codex: T0-T7 host/mock test、Pico 単体 smoke まで。
- VSC+Codex: T8 Pico hardware continuation、T9 Real NF55G HIL。

移行時に重要なこと:
- 実機差異を Pico 側で勝手に吸収しない。
- 未確定事項は `docs/Open_Issues.md` に残す。
- 実機作業結果は `docs/Real_Hardware_Test_Log.md` に記録する。
- 仕様変更時は Code / Test / Docs / CHANGELOG を同時更新する。
- `FU` は絶対に NF55G へ送信しない。

## 3. Pre-Handoff Checks
VSC+Codex を始める前に、Desktop Codex 側または通常 Git 操作で以下を確認する。

```powershell
git status --short
git branch --show-current
git log -1 --oneline
python -m unittest discover -s tests -v
```

確認項目:
- 作業ブランチが想定通りである。
- 未コミット差分が残っていない、または所有者と内容が明確である。
- 最新 commit が GitHub に push 済みである。
- host test suite が PASS している。
- `docs/Desktop_to_VSC_Migration_Plan.md` が存在する。

2026-09-04 時点の基準:
- Branch: `main`
- Latest pushed commit at guide import: `a9841a9 docs: add VSC handoff migration plan`
- Host tests: 76 tests OK

## 4. VSC Environment
VSC 側で開くフォルダ:

```text
C:\Users\m_yamada\OneDrive\My Document\NF55G\NF55G_Pico
```

推奨:
- VS Code で上記フォルダを直接開く。
- Codex 拡張または VSC+Codex の作業対象も同じフォルダにする。
- GitHub remote が `https://github.com/mino-yama/NF55G_PICO.git` であることを確認する。
- Python test 実行用に通常 Python が使える状態にする。
- Pico 接続用にシリアルポートを確認できる環境を用意する。

Git remote 確認:

```powershell
git remote -v
```

最新化:

```powershell
git pull
```

テスト:

```powershell
python -m unittest discover -s tests -v
```

## 5. Git Workflow
VSC+Codex 移行後も、作業単位ごとに commit / push する。

推奨フロー:

```powershell
git status --short
git pull
python -m unittest discover -s tests -v
git add -- <changed files>
git commit -m "<type>: <summary>"
git push
```

注意:
- 実機ログだけの更新でも、重要な実測結果なら commit する。
- `docs/Open_Issues.md` を Close する判断は人間確認後に行う。
- Word/docx は内容変更か体裁変更かを commit message または作業メモで明確にする。
- Desktop Codex と VSC+Codex の両方で同時に未コミット編集を持たない。

Desktop Codex 側へ反映する方法:
1. VSC+Codex 側で commit / push する。
2. Desktop Codex 側で `git pull` する。
3. Desktop Codex 側で差分確認、ログ確認、レビューを行う。

これにより、Desktop Codex 側から経過観察やレビューを継続できる。

## 6. Pico Connection
VSC+Codex で実機作業に入る前に、Pico 2 と周辺基板の状態を確認する。

確認済み構成:
- Target board: Raspberry Pi Pico 2 / RP2350
- MicroPython: v1.28.0
- DS3231 RTC: I2C0 GP20/GP21, address `0x68`
- SD: SPI0 GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI
- ATE UART0: TX GP0 / RX GP1, 115200 bps, 8N1
- NF55G UART1: TX GP4 / RX GP5, 38400 bps, 8E1

最重要注意:
- ADA-5703 PiCowbell の GP4/GP5 は Pico-2CH-RS232 の NF55G UART1 と競合する。
- 2026-09-04 の SD/RTC テストは GP4/GP5 を物理的に分離した状態で実施済み。
- 最終 fixture では GP4/GP5 の分離方法と検査記録を残す。
- GP4/GP5 分離が確認できるまで、NF55G UART loopback や Real NF55G 接続を始めない。

## 7. Serial Port Check
Windows 側で Pico の COM ポートを確認する。

```powershell
Get-CimInstance Win32_SerialPort | Select-Object DeviceID,Name,Description,PNPDeviceID
```

確認観点:
- Pico 2 が USB serial device として認識される。
- COM 番号を記録する。
- MicroPython REPL に入れるか確認する。
- 実機ログには COM 番号、firmware identity、実行日時を残す。

MicroPython REPL で確認する代表例:

```python
import sys, os, machine
print(sys.implementation.name)
print(sys.platform)
print(os.uname().machine)
print(machine.freq())
```

期待:
- `micropython`
- `rp2`
- `Raspberry Pi Pico2 with RP2350`

## 8. First Documents to Read in VSC+Codex
作業開始直後に読む順序:

1. `AGENTS.md`
2. `HANDOFF_MANIFEST.txt`
3. `docs/Desktop_to_VSC_Migration_Plan.md`
4. `docs/Implementation_Plan.md`
5. `docs/Test_Specification.md`
6. `docs/Real_Hardware_Test_Log.md`
7. `docs/Open_Issues.md`
8. 作業対象に応じた Master docs

特に `AGENTS.md` の Hard Rules は常に最優先とする。

## 9. First VSC+Codex Work Items
推奨順:

1. `git pull` で最新化する。
2. `git status --short` で作業ツリーを確認する。
3. `python -m unittest discover -s tests -v` で T0-T7 baseline を確認する。
4. `docs/Real_Hardware_Test_Log.md` の最新記録を読む。
5. GP4/GP5 の物理分離を確認する。
6. ATE UART0 GP0/GP1 loopback を行う。
7. NF55G UART1 GP4/GP5 38400 bps 8E1 loopback を行う。
8. final fixture firmware の transport/scheduler integration に進む。
9. RTC/SD を final firmware 経由で再検証する。
10. Real NF55G HIL は read-only 系から開始する。

## 10. Real-Hardware Test Record Rules
VSC+Codex で実機作業をしたら、原則として `docs/Real_Hardware_Test_Log.md` に記録する。

記録する項目:
- Date/time
- Hardware stack
- Firmware image/source revision
- Git commit hash
- COM port
- Wiring state
- GP4/GP5 isolation state
- 実行した command/script
- raw frame/raw response
- PASS/FAIL/INFO/WARNING
- NF55G control command を送信したか
- `FU` が block されたか
- cache invalidation への影響
- 関連 Open Issue
- 次の作業

実機ログの原則:
- 成功だけでなく、失敗・無応答・違和感も記録する。
- 実機差異を見つけたら実装で吸収せず、Open Issue に接続する。
- Control command は安全手順が確定してから段階的に行う。

## 11. Real NF55G HIL Cautions
Real NF55G 接続前に必要な確認:
- T0-T7 host tests PASS
- T8 UART loopback PASS
- GP4/GP5 isolation record
- 電源、GND、TX/RX、レベル、RS232 結線確認
- `FU` 送信禁止経路の維持
- control command safety procedure

Real NF55G HIL の順序:
1. 接続・電源・無送信状態確認
2. read-only query/refresh
3. raw frame logging
4. D0/D1/D5/BC/AR/EL/OL/FD 読み出し確認
5. EB timing observation
6. logger/SD と protocol timing の同時確認
7. control command は安全確認後

禁止:
- 最初から control command を実行しない。
- 仕様未確定項目を Pico 側で補正しない。
- Protocol SUCCESS を製品 PASS と扱わない。
- Query から自動 Refresh しない。

## 12. Stage Responsibilities

### ChatGPT
向いている作業:
- 資料の要約
- 仕様比較
- 設計方針の相談
- Open Issue 候補の整理
- 試験観点の洗い出し

注意:
- 最終判断はリポジトリ正本に反映してから扱う。
- 推測で Open Issue を Close しない。

### Desktop Codex
向いている作業:
- host/mock 実装
- unit/integration test
- 仕様文書更新
- Pico 単体 smoke の記録
- VSC 側 push 後のレビュー・経過観察

注意:
- 実機操作が必要な作業は VSC+Codex に寄せる。
- Desktop 側で未コミット編集を持ったまま VSC 側で同じファイルを編集しない。

### VSC+Codex
向いている作業:
- Pico 接続
- serial/REPL 作業
- UART loopback
- final firmware 配置
- Real NF55G HIL
- 実機ログ記録

注意:
- 実機作業前に必ず `AGENTS.md` と最新ログを読む。
- 作業単位ごとに commit / push し、Desktop 側で観察できる状態にする。

## 13. Recovery Notes

### Git が混乱した場合
まず状態確認だけ行う。

```powershell
git status --short
git log --oneline -5
git diff --stat
```

注意:
- `git reset --hard` は安易に使わない。
- 未コミット変更の所有者を確認する。
- Word/docx の差分は内容変更か体裁変更か確認する。

### Pico が見えない場合
- USB ケーブルを確認する。
- BOOTSEL 状態か通常起動か確認する。
- Windows Device Manager または COM port listing を確認する。
- firmware が Pico 用か Pico 2 用か確認する。

### REPL が応答しない場合
- COM port が正しいか確認する。
- 他の terminal/VS Code extension がポートを掴んでいないか確認する。
- MicroPython firmware identity を再確認する。

### I2C/RTC が見えない場合
- GP20/GP21 wiring を確認する。
- DS3231 power/GND を確認する。
- address `0x68` scan を再実行する。
- final firmware 後は再検証する。

### SD が mount できない場合
- GP16-GP19 wiring を確認する。
- card format が FAT32 か確認する。
- card removal/write-error test と通常 mount failure を区別する。

### UART が動かない場合
- GP0/GP1 と GP4/GP5 を取り違えていないか確認する。
- TX/RX crossing を確認する。
- NF55G 側は 38400 bps, 8E1 を確認する。
- GP4/GP5 conflict が再発していないか確認する。

## 14. Minimum Prompt for VSC+Codex Handoff
VSC+Codex で作業を始めるときは、以下を最初の依頼文に含めるとよい。

```text
AGENTS.md を最上位ルールとして読み、HANDOFF_MANIFEST.txt と docs/Desktop_to_VSC_Migration_Plan.md を確認して下さい。
VSC+Codex では T8 Pico hardware continuation から開始します。
最初に git status、git pull、host test 再実行、docs/Real_Hardware_Test_Log.md の最新確認を行って下さい。
GP4/GP5 isolation を確認するまで NF55G UART loopback と Real NF55G 接続へ進まないで下さい。
実機結果は docs/Real_Hardware_Test_Log.md、未確定事項は docs/Open_Issues.md、変更履歴は docs/CHANGELOG.md に記録して下さい。
```

## 15. Conclusion
ChatGPT で資料集め・仕様固め、Desktop Codex で開発・デバッグ、VSC+Codex で実機テストという段階運用は妥当である。

成功させる鍵は、Git を同期点にすること、実機ログを残すこと、Open Issue を勝手に閉じないこと、GP4/GP5 の物理 conflict を毎回確認することである。
