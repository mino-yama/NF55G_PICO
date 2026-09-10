# 実物 NF55G 試験準備

作成日: 2026-09-10。状態: 接続・送信前の準備資料。T9 実行許可を意味しない。

基準は `AGENTS.md`、RW11用電源通信仕様書 r1、各 Master、
`Test_Specification.md` の T9 entry gate、`Desktop_to_VSC_Migration_Plan.md`。
本書は既存仕様の変更ではなく、実装不足と試験準備の記録である。

## 現在の到達点

| 項目 | 状態・根拠 |
|---|---|
| Git baseline | `6dc2328` を origin/main に push 済み |
| Host/Mock | Runtime統合後136件合格。全仕様・実機タイミングの網羅を意味しない |
| Pico | COM14、Pico 2/RP2350、MicroPython v1.28.0（9/9 inventory） |
| Pico配置ファイル | 9/9時点のルートは `/sd` のみ。最終治具ソース未配置 |
| RTC REPL HIL | 0x68 検出、日時読み出し成功 |
| SD REPL HIL | 初回 CMD0異常後、抜き差しで回復。9/10はマウント3回と160件I/O成功 |
| UART REPL HIL | 両ch 256バイト一致、混信0、各100フレーム成功 |
| GP4/GP5 | ユーザーが物理切断済みと確認。最終切断箇所・検査記録はHW-01に残る |
| 接続・FW申告 | PC–Pico接続済み、ループバック解除済み。搭載FW版数は未定との回答。NF55G本体との接続・電源状態は未確認 |
| 最終ファームウェア | 時計/EB/ATE/実SD統合コードと起動entry候補を追加。Host検証済み、Pico未配置・実機未検証。T9 gate未達 |

## 実装確認で分かった接続前の不足

以下はRuntime統合前の監査記録。2026-09-10に時計・EB・排他/UART例外・ATE受信・実SDを
実装し、Host/Mockで検証した。最新状態と実機で残る制約は [Runtime Integration](Runtime_Integration.md) を参照。

| 箇所 | 現状 | 接続前に必要な作業・検証 |
|---|---|---|
| `src/main.py` | 起動してself-checkを返す骨格。ATE受信ループなし | UART行受信・応答・スケジューラを統合。ATE優先、transaction 1件を保証 |
| parser/dispatcher | D1/D5 RefreshとSTATUS/INFO全QueryをHost実装・検証済み | その他のRefresh/Query、最終firmwareとの接続は継続 |
| `src/nf55_protocol.py` | 実時計未指定時は `time.monotonic()` を使用。deadlineは通常の加算・比較 | Pico用clockを明示的に統合し、ticks wrapを含むtimeout処理をHost/Picoで検証 |
| protocol EB | `eb_events` はあるが、受信EBを分離処理する経路がない | EB別処理・ACK・STATUS非更新・元のT2維持を実装してMock故障注入で確認 |
| protocol排他/例外 | `transact`入口のbusy拒否なし、UART例外をTransactionResultへ変換する処理なし | 再入を防止し、UART異常時ambiguous・cache invalidation・復帰状態を検証 |
| Logger | 標準sinkは `MemorySDSink`、ファイル名はticks由来 | 実SD sinkとDS3231時刻を統合。通信中write/flush禁止、SD故障時通信継続を検証 |
| 診断 | `NF_COMM_CHECK?` は常にNOT_CONNECTED。自己診断は実SD mountの証拠にならない | 診断の実体・報告内容を整合させる。NF通信診断の詳細は仕様に従い扱う |

実装前のHost実測（履歴、NF55G送信なし。以下UNKNOWN_CMDはD1/D5実装前の結果）:
```text
*IDN? -> NF55G_PICO_FIXTURE,Rev.0
FW_UPDATE -> ERR:FU_DISABLED
STATUS_REFRESH -> ERR:UNKNOWN_CMD
INFO_REFRESH -> ERR:UNKNOWN_CMD
PS_ON? -> ERR:UNKNOWN_CMD
FW_REV? -> ERR:UNKNOWN_CMD
NF_COMM_CHECK? -> ERR:NF55G_NOT_CONNECTED
logger_sink -> MemorySDSink
```

D1/D5実装後、未接続のRefreshは `ERR:NF55G_NOT_CONNECTED`、未取得のSTATUS/INFO
Queryは `ERR:CACHE_INVALID`。Mock応答を用いたRefresh/全63 Queryは検証済み。

これらは現段階の実装不足であり、Masterの要件を緩和する理由にはしない。
仕様上の未確定事項は既存Open Issuesで扱い、設計回答を推測しない。

## ファームウェア準備の作業順

1. D1/D5 Refresh/QueryのHost/Mock経路は完了。その他のPhase 7/8不足は継続する。
2. Pico時計・EB・排他・UART例外は統合しHost/Mock検証済み。実機タイミング確認を行う。
3. Phase 9/10の実SD sink・RTC時刻は統合コード追加済み。統合版の実カード検証を行う。
4. Phase 11のATE受信・応答・schedulerは統合コード追加済み。実機未接続で起動時TX=0、
   `FW_UPDATE`に対する`ERR:FU_DISABLED`とNF55G側TX=0を確認する。
5. 当面の配置候補は既存MicroPython上の `/src/` パッケージと薄い起動エントリー。
   配置ファイル一覧・hash・Git revision・起動/停止/復旧手順を確定して記録する。
   この候補は未実施であり、現在の `src/main.py` をそのまま量産版として配置しない。
6. NF55G未接続で、統合した同一ファームウェア経由のRTC/SD/UART試験を行う。
7. 下記の接続前チェックとT9 gateを満たしてから製品試験へ進む。

## 接続前チェック記録

| 確認項目 | 記入欄 |
|---|---|
| 日時・担当者 | 未記入 |
| 製品型式・個体識別・搭載FW版 | 型式/個体識別は未記入、搭載FW版数は未定との回答 |
| 製品電源・負荷・バッテリ・出力状態と操作担当者 | 未記入 |
| Pico firmware一覧/hash/Git revision | 未確定 |
| 同一firmwareのRTC/SD/UART smoke・FU遮断証拠 | 未実施 |
| HW-01の切断箇所・方法・検査結果 | 物理切断済みとの申告あり、詳細未記録 |
| NF55G側ループバック短絡の撤去 | ユーザーがループバック解除済みと申告。最終接続時に対象chを照合 |
| ATE側ループバック短絡の撤去 | 同上。PC–Pico接続済み（接続方式は今回未指定） |
| CN24ハーネス結線表の版・端子方向・TX/RX/GND導通 | 未確認 |
| RS232変換基板経由の接続・電気レベル・接地 | 未確認 |
| COM14専有、ATE用PC/装置ポート番号 | 未確認 |
| 配置/記録コミットpush、開始時worktree clean | 開始時に再確認 |

NF55GはPico-2CH-RS232のUART1（GP4/GP5、38400 bps、8E1）、
ATEはUART0（GP0/GP1、115200 bps、8N1）。USB COM14はPico REPLでありATE UARTとは別。
CN24のピン番号・ハーネス接続は原典の結線表を実物と照合し、本書では推測しない。
製品接続後に既存UARTループバック用パターン試験を実行しない。

## 初回の製品通信手順案（gate達成後）

次のATEコマンドとATE UART受信経路はHost/Mock検証済み。統合版はPico未配置・未検証のため、
現在のPico上でこの手順を実行できる状態ではない。

| 順番 | 操作 | 確認・記録 |
|---|---|---|
| 1 | 接続前にlocal ID/RTC/SD診断とFU遮断試験 | 実装済みの経路を使用し、NF55G TX=0を確認 |
| 2 | 接続後、送信前の受信状態を観測 | EBが来た場合は既定の別処理、STATUS非更新。製品状態を記録 |
| 3 | `STATUS_REFRESH`（D1）を1件 | DATA 15文字、T2 100ms、raw/BCC/ACK/retry/elapsed/ambiguous |
| 4 | `PS_ON?` 等のSTATUS個別Query | 直前のcache値、追加NF55G送信なし |
| 5 | `INFO_REFRESH`（D5）を1件 | DATA 100文字、T2 100ms、INFOのみ更新 |
| 6 | `FW_REV?` 等のINFO個別Query | rawとdecodeの対応、追加NF55G送信なし |

T1は200ms暫定（OI-01）。製品応答差・timeoutをPico側の独断補正で吸収しない。
最終エラーになった時点で次の試験コマンドを停止してrawを保存する。
内部Command Retryは既存仕様どおり最大1回、Response Retryとは別管理し、手動の連打はしない。

## 初回手順から分ける項目

- D0: OI-03（ACK後CHARGE_ENDへの影響）を確認する観測計画を別途作成。
  D0を無条件に副作用なしと扱わない。T2は600ms暫定（OI-02）。
- D2/D3/D4: 状態・cacheへの影響を仕様どおり扱う。特にD3/D4にはclear副作用がある。
- BC: BATT_CHECK_START/STOPを単なる読出しに含めない。負荷・製品動作を伴う別試験。
- AR: OI-04/OI-12/OI-20に従いREF raw保持、T2・形式の設計確認を分離。
- FD: 許可アドレスの根拠を記録してから実施（OI-10）。任意アドレス走査をしない。
- EL/OL: ブロック指定とraw/decode照合の個別手順を作る。
- Control/SET/CLEAR/AD: 電源・負荷・外部計測・停止手順を確認した別試験。
- `FU`: 常時禁止。製品接続後の試し送信も行わない。

## 一件ごとの保存項目

日時、製品識別/FW、Pico Git/hash、配線状態、ATE入力/出力、TX/RX raw HEX、
BCC、ACK/NAK、Command/Response retry数、T1/T2設定、elapsed、ambiguous、
cache前後、EB、SD/Logger状態・drop数、外部測定、関連Issue、次の操作。
通信中はRAM Queueへ保存し、通信終了後にSDへ出力する。
Protocol SUCCESSと製品動作のPASSを混同しない。最終製品判定はATE側。

## 残確認

SDの初回 `CMD0 failed: 31` は原因未特定。通電中の再初期化成功と電源投入直後の
成功を区別して記録する。最終firmware smokeで再確認し、再発時は原因を切り分ける。
HW-01や製品FW関連IssueのCloseは人間確認後とし、この準備資料で自動的にCloseしない。
