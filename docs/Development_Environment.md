# Windows 開発環境

## 導入

Python 3.12 を使用する。リポジトリのルートで、コマンドプロンプト
(`cmd.exe`) から実行する。仮想環境の activate は不要。

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

`.venv/` は既存の `.gitignore` で除外済み。
`.vscode/settings.json` で Python の既定インタープリターに `.venv` を設定済み。
VS Code で別のインタープリターを選択済みの場合は、Python: Select Interpreter から
`.venv\Scripts\python.exe` を選択する。

## VS Code のプロジェクト設定

- 新規ターミナルと自動タスク用シェルは `cmd.exe /d` を使用。
  既に開いているターミナルには反映されないため、新規ターミナルを開く。
- unittest を有効にし、`tests/test_*.py` を検出する。
- Tasks: Run Test Task から `NF55G: Host and Mock tests` を実行できる。
- Tasks: Run Task の `NF55G: Check Python dependencies` で依存関係を検査できる。
- 上記タスクは `.venv` の Python を直接実行するため、activate は不要。
- 設定の適用先はこの VS Code ワークスペース。Codex のコマンド実行シェルを
  変更する設定ではないため、Codex では引き続き `cmd.exe` を明示して実行する。
- Store 版 `pwsh.exe` は権限昇格時には起動成功、通常権限ではアクセス拒否。
  今回の設定は起動制限自体の修復ではなく、確認済みのシェルを使う開発設定である。

Host/Mock テストは標準ライブラリのみで動作する。
`pyserial` は既存 HIL スクリプト、`python-docx` は Word 文書生成で使用する。
`mpremote` は今後の MicroPython 配置・REPL 操作用であり、既存 HIL スクリプトの必須依存ではない。
直接依存は導入確認済みのバージョンに固定している。

## 通信せずに行う起動確認

```bat
.venv\Scripts\python.exe -B scripts\pico_rtc_hil.py --help
.venv\Scripts\python.exe -B scripts\pico_sd_hil.py --help
.venv\Scripts\python.exe -B scripts\pico_uart_hil.py --help
.venv\Scripts\python.exe -m mpremote --help
.venv\Scripts\python.exe -m serial.tools.list_ports -v
```

`--help` の成功や COM ポートの列挙は、実機動作の確認を意味しない。
実機試験は `Test_Specification.md`、`Desktop_to_VSC_Migration_Plan.md`、
`Open_Issues.md` の条件に従う。

## 2026-09-09 導入状況

- 通常権限の `cmd.exe` で Python 3.12.3 が動作。
- プロジェクト内に `.venv` を作成済み。
- 通常権限での初回導入時、pip は `Ignoring indexes: https://pypi.org/simple`、
  `0 location(s) to search for versions of pyserial`、
  `No matching distribution found for pyserial` を報告した。
- 検索先の明示や一時的な pip 設定の切り分けでも解消しなかった。
  インデックスが無効になる設定元は未特定。
- その後、ユーザーの指示で権限昇格による pip install を実行し、取得・導入に成功。
  導入先はプロジェクト内の `.venv`。
- 導入済み: pyserial 3.5、python-docx 1.2.0、mpremote 1.29.0。
  間接依存: lxml 6.1.3、platformdirs 4.11.8、typing_extensions 4.16.0。
- 導入後は通常権限に戻して `.venv` の Host/Mock 91件合格、`pip check` 不整合なし、
  HIL 3本と mpremote の `--help` 成功、COM14 検出を確認。
- `pwsh.exe` の起動時にアクセス拒否が発生するため、この環境では `cmd.exe` を使用。
- Pico firmware 配置、REPL 操作、実機 HIL は今回未実施。Open Issues は変更しない。

今後の再導入時に同じ取得制限が発生する場合は、取得可能な実行環境で導入するか、
適合する wheel 一式を用意して
`pip install --no-index --find-links <wheelフォルダ> -r requirements-dev.txt` で導入する。
