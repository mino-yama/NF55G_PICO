# NF55G Pico 2 Implementation Plan

2026-11-20 ユーザー方針更新: RUNパッド施工は難しいため外部RESET配線/駆動回路は進めず、手動RESET/電源再投入をデバッグで選ぶ。GP14/22は汎用予備。初回起動前から記録し、異常→正常データを交互に送る受入を計画。形式不正後の受付継続と、timeout/切断等の規定fault保持を分けて判定する。今回は計画のみ、実機注入/コード変更なし。 [計画](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Error_Normal_Alternation_Plan_Rev0/Plan_and_Reset_Decision_Rev0.md)／[現行GPIO Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev1.md)。

2026-11-20 工数/GPIO並行計画: 測定原文取得/ATE返却は実機済み。残る数値・単位/Cache/正式ATE入口とAD実装は仕様回答後コード/Mock1〜2実働日、基本実機確認含2〜3実働日（概算12〜24時間、待ち/全量産受入は別）。親GPIOは既存予約のQR GP8/9と実装済み測定器GP12/13を配線基準として維持。現行測定器PIOはSM4/5で旧案の順序に注意。RESETは必須/制御方式未確定、GP14/22を親側予備候補として確保しHost RUN結線は回路確認後。今回コード/Flash/実配線変更なし。 [工数](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Effort_Estimate_Rev0.md)／[配線基準](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev0.md)。

2026-11-20 ユーザー補足による解釈訂正: 「試験者設定のレンジ」はATE側のコマンドで決定/設定する意味。前面手動設定を前提にせず、ATEが固定レンジ値またはAUTO条件を指定→Queryで設定確認→測定要求を送る。Pico/Hostは本文を中継し、指定値の独自置換/自動最適化を行わない。次の安定性試験もこの順序で実施する計画。今回は記録訂正のみ、実機送信/コード/Flash変更なし。 [現行方針Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Next_Steps_After_ATE_Range_Decision_Rev1.md)。

2026-11-20 ユーザー決定: 最適レンジは試験者が設定し、レンジ追加調査はここまでとする。中継は明示コマンド/原文を維持し自動最適化/独自補正しない。レンジ読戻し差の記録は保持し中継継続のブロッカーにしない。次は固定入力/試験者レンジでの安定性→timeout/切断/清浄復帰→ATE/NF55G/SD共存受入。その後、正式API等を確認してADC測定Cache/ATE確認後別指令ADへ接続する。今回は説明/記録のみ。 [方針・次工程](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Next_Steps_After_Operator_Range_Decision_Rev0.md)。

2026-11-20 親配置完了: COM6/unique_id 69f7d45962cfdfadの既存26ファイルを退避・SHA照合後、配置対象30ファイルを実機SHA照合（追加/更新8）。実機RAM検証と配置後import成功。通常起動せずREPL停止、PIO4/5はinactive。Host/親の配置は完了したが、配線と実機中継受入は未実施。[親配置結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Parent_Deployment_01/Result_Rev0.md)。以下の親未配置記述は配置前の状態として保持。

2026-11-20 後続配置: Host BFCF2EDB84B0B37Fへmeter-host-relay-20261120.1を書込み、Flash verifyと書込み後版照合に成功。旧.5全Flash退避・照合済み。BOOTSELのままrebootせず、親Picoは未配置・実機中継未試験。[Host配置結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Host_Deployment_01/Result_Rev0.md)。以下のHost未配置記述は配置前の状態として保持。

2026-11-20 中継リンクのコード結合を実施。親ATE非同期受付・PIO UART、独立Host中継UF2、Host上の実C/Python相互運用まで完了。全446件成功、ARM build/link成功。未配置の実機確認用パッケージと配線/配置/初回IDN手順を準備。次は個体/無給電配線照合・バックアップ・配置・実機縦通し。レンジ検証は保留。 [リンク実装記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Result_Rev0.md)。

2026-11-20 通信契約Rev.1をユーザー確定。承認値とATE要求/応答・親子フレームcodecを実装し、次は両adapter/Host CとATE入口・schedulerへの接続を進める。仕様承認を現物配線・実機疎通の完了とは扱わない。 [確定仕様 Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Interface_Spec_Rev1.md)。

2026-11-20 中継着手: レンジ検証を保留し、外部測定器の要求相関/原文/期限を扱う内部コアを実装、全401件成功。正式ATE/親子UART契約の具体案を提示し、合意後にadapter/Host/ATE入口を結合する。現在は実機中継未完成。 [実装記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Result_Rev0.md)。

2026-11-19最新指示: 新製品FWへの追従変更は保留するが、3系統のADC校正治具機能は開発を進める。測定Cacheの内部基盤と試行境界の失効を先行実装。正式ATE/Host API・シャント換算・AD/AR契約を確定後、中継/取得→ATE確認→Cache利用AD送信→実機検証へ進める。[確定事項・実装と残事項](ADC_Calibration_Development_20261119.md)。

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.0
Date: 2026-09-01

## 1. Purpose
本計画は、NF55G Pico 2 試験治具ソフトウェアの実装順を固定し、各 Phase の成果物、参照仕様、完了条件、テスト観点を明確にするためのものである。

本計画はコード実装を開始するものではない。実装時は必ず `AGENTS.md`、各 Master 仕様、Open Issues を再確認する。

## 2. Global Rules
- 実装順は本書の Phase 1 から Phase 12 までの順に固定する。
- 暫定 NF55G FW と r1 仕様の差異を Pico 側で勝手に吸収しない。
- 未確定事項は `docs/Open_Issues.md` に残し、Codex 判断で Close しない。
- Pico は製品 PASS/FAIL を判定しない。
- ATE 個別 Query から NF55G 通信や自動 Refresh を行わない。
- `FW_UPDATE` / `FU` は NF55G へ送信せず、`ERR:FU_DISABLED` を返す。
- Host Unit Test / Mock NF55G Test を先行し、T0-T7 合格後に実機統合へ進む。

## 3. Phase Overview

| Phase | Name | Main Output | Primary Test Level |
|---:|---|---|---|
| 1 | 共通モデル・定数 | `models.py`, `config.py` の設計確定 | T0/T4 前提 |
| 2 | BCC / Frame Builder / Parser | NF55G frame 純粋処理 | T1 |
| 3 | Data Decoder | D0/D1/D2/D3/D4/D5/BC/AR/EL/OL/FD decode | T3 |
| 4 | Cache Manager | Cache valid/invalid/metadata/invalidation | T4 |
| 5 | Mock NF55G | Host integration 用 MockUART/FakeClock/Scenario | T6 前提 |
| 6 | Protocol State Machine | ACK/NAK/Retry/Timeout/EB/ambiguous 制御 | T2/T7 |
| 7 | ATE Command Parser / Dispatcher | ATE ASCII command routing | T0/T5 |
| 8 | NF55G Command Builder | NF CMD table / DATA builder | T5 |
| 9 | Logger / SD | Non-blocking queue + SD sink 設計 | T7 |
| 10 | RTC | DS3231 driver / RTC ATE command | T5/T8 |
| 11 | Pico UART Hardware Layer | Pico UART physical I/O | T8 |
| 12 | 実機統合 | Real NF55G HIL / timing validation | T9 |

## 4. Detailed Plan

### 2026-11-04 追加開発の順序（ユーザー指定）

現在の作業から追加機能への順序を以下とする。既存Phase 1～12の並びは維持する。

1. 現在の実機確認を進め、結果と残課題を記録する。
2. QRコード読取りの開発・実機確認を進め、結果と残課題を記録する。
3. その後、7355連携による外部測定値取得・補正機能を追加する。

第3ステップの対象は、7355の通信仕様・GPIBアドレス設定、PIA5100経由の測定値取得とATEへの返却、およびATE判定後の別の数値付き補正書込み指令によるNF55Gへの書込みとする。取得時の自動書込みは行わない。

補正は①コマンド＋数値による直接書込み、②測定値取得コマンドでATEへ返却・判定後に測定値書込みコマンド＋数値で書込み、の両方式を選択可能とする。①に測定値取得の事前実行を要求しない。詳細設計・実装・Host／Mock／実機確認では両方式を対象とし、追加機能の開発順序は上記を維持する。

現時点は追加要求と資料の保存までとし、7355機能の詳細仕様化・実装・試験は上記順序で後続作業として扱う。資料の保存だけで通信仕様確定や試験完了としない。着手時はCAL-EXT-01～03および既存AD/ARのOpen Issuesを確認し、Code／Test／Docs／CHANGELOGを対応させて更新する。

参照: [追加要求仕様](Calibration_External_Measurement_Requirements_20261104.md)、[保存した7355資料一覧](../reference/ADCMT_7355_20261104/manifest.json)。各ステップの詳細な完了条件・実施日は未確定であり、本追記は完了を意味しない。

### Phase 1: 共通モデル・定数
目的:
- 以後の全 Phase が共有する型、列挙、定数、エラー分類を先に固定する。

参照仕様:
- `docs/Software_Module_Interface.md`
- `docs/Protocol_State_Machine.md`
- `docs/Cache_Master.md`
- `docs/Open_Issues.md`

成果物:
- TransactionResult の項目定義。
- Cache 名、Transaction error、NAK reason、Protocol state の定義。
- T1/T2 暫定値、retry 最大値、expected length の定数テーブル設計。
- Open Issue 由来の provisional 値を明示するコメント方針。

完了条件:
- 後続 Phase が独自の文字列定数やエラー分類を増殖させない状態になっている。
- OI-01、OI-12など未確定のタイミング値を「確定値」として扱っていない。D0のT2は2026-11-11ユーザー指定により300msへ改訂し、OI-02は実機Timing確認を残す。

テスト観点:
- 定数テーブルと仕様表の対応確認。
- Cache 名、Command 名、Error 名の typo 検出。

### Phase 2: BCC / Frame Builder / Parser
目的:
- NF55G 通信 frame の組み立て、受信 frame validation、BCC 計算を純粋関数として実装可能にする。

参照仕様:
- `README.md` NF55G communication
- `docs/Protocol_State_Machine.md`
- `docs/Test_Specification.md`

成果物:
- BCC 計算仕様: CMD ID から ETX まで XOR、STX は除外。
- Command frame builder。
- Response frame parser。
- ACK/NAK/plain byte と frame の責務分離。
- 不正 STX/CMD/length/ETX/BCC/partial frame のエラー分類。

完了条件:
- UART や retry に依存しない純粋処理として検証できる。
- Pico から response NG に対して送る NAK は plain `0x15` とする前提が守れる。

テスト観点:
- T1 Frame/BCC 全項目。
- wrong STX/CMD/length/ETX/BCC。
- partial frame。

### Phase 3: Data Decoder
目的:
- NF55G response DATA を ATE 返却用データへ変換する純粋 decoder を作る。

参照仕様:
- `docs/Data_Decode_Master.md`
- `docs/ATE_Command_Master.md`
- `docs/Open_Issues.md`

成果物:
- D0 327 chars decode。
- D1 STATUS 15 chars decode。
- D2/D3/D4/D5/BC/AR/EL/OL/FD decode。
- Signed 8bit、scale、ASCII text、leading zero preserve の方針。
- EB decode は CURRENT/CHANGE を別保持し、STATUS Cache 更新と分離。
- AR REF は OI-04 により raw8 preserve + pluggable decoder とする。

完了条件:
- decoder は Cache を更新しない。
- partial decode を VALID Cache に保存できないインターフェースになっている。
- D0 内 STATUS/Manufacturing/Parameter を STATUS/INFO Cache へ昇格しない設計が維持できる。

テスト観点:
- T3 Decoder 全項目。
- signed values。
- mV->V、mA->A、0.1h、0.1% scale。
- FD 64 ASCII HEX unchanged。

### Phase 4: Cache Manager
目的:
- 明示 Refresh と Cache Query の分離、および invalidation matrix を実装可能にする。

参照仕様:
- `docs/Cache_Master.md`
- `docs/ATE_Command_Master.md`
- `docs/Protocol_State_Machine.md`

成果物:
- Power-on all INVALID。
- invalidate / invalidate_many / validate / is_valid / get / metadata。
- Refresh start 時に先に INVALID。
- Refresh failure 時に旧値へ戻さない。
- Control/SET/CLEAR 成功時および ambiguous failure 時の invalidation matrix。

完了条件:
- Query は Cache のみ参照し、NF55G 通信を呼べない。
- Control response status、D0 status、EB current status を STATUS Cache に昇格しない。

テスト観点:
- T4 Cache 全項目。
- ambiguous invalidation。
- parser rejection では cache unchanged。

### Phase 5: Mock NF55G
目的:
- 実機接続前に host 上で protocol、parser、decoder、cache、command integration を検証できる相手役を作る。

参照仕様:
- `docs/Test_Specification.md`
- `docs/Protocol_State_Machine.md`

成果物:
- MockUART。
- FakeClock。
- ResponseFactory。
- Scenario engine。
- stateful NF55G simulation。
- EB injection scenario。

完了条件:
- Mock は試験用 peer であり、製品仕様の正本として扱わない。
- r1 仕様と暫定 FW 差異を Mock 都合で Pico 実装に吸収しない。

テスト観点:
- T6 Mock NF55G end-to-end。
- ACK/NAK/timeout/BCC NG/error frame/EB scenario。

### Phase 6: Protocol State Machine
目的:
- NF55G transaction を常に 1 件だけ実行し、ACK/NAK/retry/timeout/response retry/ambiguous を決定論的に処理する。

参照仕様:
- `docs/Protocol_State_Machine.md`
- `docs/Cache_Master.md`
- `docs/Test_Specification.md`

成果物:
- `transact(cmd, data, t2_ms, expected_length) -> TransactionResult`。
- explicit state machine。
- Command Retry 最大 1 回。
- Response Retry と Command Retry の別管理。
- deadline/ticks ベースの T1/T2。
- NF55G error response frame 受信時は ACK 後に failure。
- EB は非同期処理し、通常 response の T2 deadline を reset しない。

完了条件:
- 同時 transaction 禁止が守られている。
- ACK_TIMEOUT、RESP_TIMEOUT、final BCC/FRAME、UART/COMM、HWE で ambiguous=True になる。
- final NAK30-36、CME/PME/SQE/MCM は ambiguous=False になる。

テスト観点:
- T2 Protocol state machine 全項目。
- T7 Safety の protocol 関連項目。

### Phase 7: ATE Command Parser / Dispatcher
目的:
- ATE ASCII command を構文解析し、Cache Query、Refresh、Control、Diagnostic、Logger、RTC へ明確に振り分ける。

参照仕様:
- `docs/ATE_Command_Master.md`
- `docs/Software_Module_Interface.md`
- `docs/Cache_Master.md`

成果物:
- ATE command syntax parser。
- command dispatcher。
- Cache Query handler。
- Refresh handler。
- Control/Set/Clear handler。
- Diagnostic command handler。
- `FW_UPDATE` -> `ERR:FU_DISABLED` path。

完了条件:
- 個別 Query から自動 Refresh しない。
- `FW_UPDATE` で NF55G TX count が 0 になる。
- Control command の `OK` は Protocol Transaction 成功のみを意味し、製品 PASS を示さない。

テスト観点:
- T0 Parser。
- T5 Command integration。
- T7 Safety。

### Phase 8: NF55G Command Builder
目的:
- ATE command から NF55G CMD/DATA/t2/expected_length/cache policy を生成する表を整備する。

参照仕様:
- `docs/ATE_Command_Master.md`
- `docs/Data_Decode_Master.md`
- `docs/Cache_Master.md`
- `docs/Open_Issues.md`

成果物:
- D0/D1/D2/D3/D4/D5/AR/FD/EL/OL command mapping。
- SP/RP/SE/SC/SS/SL/BC/CN/CF/BE/BF/OR/CD/CL/AD mapping。
- PARAM/SERIAL/AD/LIFE/FD/EL/OL の parameter validation。
- T2/expected_length table。
- Success invalidation/post check policy table への接続。

完了条件:
- `FU` は command table に送信用として存在しない、または blocked として扱われる。
- AD、AR、BC、FD など Open Issue 付き項目は暫定実装であることが追跡できる。

テスト観点:
- T5 Command integration。
- range/format invalid parser rejection。
- cache policy と command result の接続。

### Phase 9: Logger / SD
目的:
- NF55G protocol timing を阻害しない logging architecture を作る。

参照仕様:
- `docs/Logger_SD_Spec.md`
- `docs/Software_Module_Interface.md`
- `docs/Test_Specification.md`

成果物:
- RAM queue。
- SD sink。
- future USB/debug sink interface。
- TEST_START/TEST_END file lifecycle。
- LOG_CONT_START/LOG_CONT_STOP lifecycle。
- 1 sec or 32 records flush policy。
- BANK_A/B + reserve capacity strategy。
- SD failure latched state。

完了条件:
- critical NF55G protocol states 中に SD write/flush しない。
- SD failure が product test や NF55G communication を止めない。
- LOG_DROP_COUNT を取得できる。

テスト観点:
- logger does not block protocol。
- SD_STATUS?/SD_USAGE?/LOG_DROP_COUNT?/SD_REINIT。
- queue overflow/drop。

### Phase 10: RTC
目的:
- Pico-side DS3231 を時刻源として、ATE RTC command と logger timestamp を提供する。

参照仕様:
- `README.md`
- `docs/ATE_Command_Master.md`
- `docs/Logger_SD_Spec.md`
- `docs/Open_Issues.md`

成果物:
- DS3231 driver。
- RTC_DATE?/RTC_TIME?/RTC_DATETIME?。
- RTC_SET_YYYYMMDD_HHMMSS。
- RTC_CHECK?。
- logger filename timestamp integration。

完了条件:
- OI-13 の I2C scan 0x68 は実機確認待ちとして扱う。
- RTC failure が NF55G communication を停止しない設計になっている。

テスト観点:
- host fake RTC。
- invalid datetime parser。
- T8 Pico hardware で I2C scan 確認。

### Phase 11: Pico UART Hardware Layer
目的:
- ATE UART と NF55G UART の physical byte I/O を Pico 実機上で接続する。
- 2026-09-07 時点で Desktop Codex により REPL HIL の RS232C 2ch loopback は完了済み。VSC+Codex では final firmware 経由で再確認する。

参照仕様:
- `README.md`
- `docs/Software_Module_Interface.md`
- `docs/Protocol_State_Machine.md`

成果物:
- ATE UART: GP0/GP1 ASCII transport。
- NF55G UART: GP4/GP5, 38400 bps, 8E1。
- UART read/write abstraction。
- timeout/deadline 用 tick source。
- future USB CDC が command core を再利用できる構造。
- `src/ate_uart.py` / `src/nf55_uart.py` host-testable transport skeleton。
- `scripts/pico_uart_hil.py` REPL HIL runner。

完了条件:
- UART layer は command meaning を判断しない。
- ATE 優先順位が scheduler 上で守れる。
- NF55G transaction 同時実行禁止が hardware layer でも破られない。
- RS232C CH0/CH1 loopback は Desktop Codex で PASS 済み。ただし final firmware scheduler/transport 経由の再確認を VSC+Codex で行う。

テスト観点:
- T8 Pico hardware。
- loopback。
- framing/parity error handling。
- REPL HIL と final firmware の差異確認。

### Phase 12: 実機統合
目的:
- Real NF55G と接続し、T9 HIL と timing validation を行う。
- NF55G 実機が未準備の場合は、final firmware smoke、safety checklist、handoff readiness までを先に完了させる。

参照仕様:
- 全 Master 仕様。
- `docs/Open_Issues.md`

成果物:
- Real NF55G HIL test checklist。
- D0/D1/D5/BC/AR/EL/OL/FD 読み出し確認。
- Control command は安全確認済み手順から段階的に実施。
- EB timing 実測。
- Logger/SD + protocol timing 同時確認。
- Open Issues の確認結果記録。ただし Close は人間確認後。

完了条件:
- T0-T7 合格後にのみ実施。
- T8 hardware smoke 合格後にのみ実施。
- final firmware 経由の RTC/SD/UART smoke 合格後にのみ実施。
- GP4/GP5 final fixture isolation method and inspection record を HW-01 に対応付けて記録してから実施。
- 実機差異は Open Issue または仕様更新案として記録し、Pico 側で勝手に吸収しない。

テスト観点:
- T9 Real NF55G HIL。
- T1/T2 provisional timing の妥当性。
- OI-03、OI-05、OI-06、OI-07、OI-09、OI-10、OI-11、OI-12、OI-13 の確認。

## 5. Phase Gates

| Gate | Condition |
|---|---|
| G1 | Phase 1-4 完了。Pure unit tests で model/frame/decode/cache が通る。 |
| G2 | Phase 5-6 完了。Mock NF55G で protocol state machine が通る。 |
| G3 | Phase 7-8 完了。ATE command から NF55G transaction/cache response まで host integration が通る。 |
| G4 | Phase 9-10 完了。Logger/RTC が protocol timing を阻害しない。 |
| G5 | Phase 11 完了。Pico RTC/SD/UART REPL HIL smoke test が通る。VSC+Codex で final firmware 経由の再確認を行う。 |
| G6 | Phase 12 完了。Real NF55G HIL の結果と残 Open Issues が記録されている。 |

## 6. Initial Test Execution Policy
- Phase 1-8 は host PC unit/integration test を主対象にする。
- T0-T7 は HIL 前の必須 gate とする。
- 実機依存の T8/T9 は Mock NF55G test 合格後に限定する。
- Desktop Codex で完了済みの REPL HIL は pre-NF55G evidence として扱う。
- VSC+Codex 移行後、final firmware image/build path が決まったら RTC/SD/UART を final firmware 経由で再実行する。
- NF55G 実機接続は final firmware smoke と safety checklist 後に限定する。
- 仕様矛盾を見つけた場合は実装で吸収せず、`docs/Open_Issues.md` に追記する。

## 7. Documentation Update Policy
- 仕様変更時は Code / Test / Docs / CHANGELOG を同時更新する。
- 本計画の Phase 順を変更する場合は、人間確認後に本書と README の Development order を同時更新する。
- 実機統合で判明した差異は、Open Issue、仕様書、テスト仕様のいずれに反映すべきかを明記してから更新する。

## 8. Source Versioning Policy

### 8.1 Development Phase
開発段階では、ソースファイル内に細かい変更履歴や個別版数を持たせない。

正本:
- Git history
- `docs/CHANGELOG.md`
- 各仕様書の `Revision`

ソースファイルに記載してよい情報:
- module name
- 対応する主要仕様書名
- 対応する仕様 `Revision`

ソースファイルに記載しない情報:
- ファイル内変更履歴
- 日付ごとの修正ログ
- Git commit と重複する詳細履歴
- Codex 作業単位の履歴

目的:
- 開発中の頻繁な変更でソースヘッダと実態が乖離することを防ぐ。
- 変更履歴の正本を Git と CHANGELOG に一本化する。
- Review 時は仕様、テスト、差分に集中する。

### 8.2 Production Release Phase
量産リリース時には、マイナー変更、現地修正、保守差分を追跡するため、ソース側にも版数管理情報を持たせる。

量産リリース移行時に決める項目:
- ソースファイル単位の `Module Version` 表記形式。
- 全体 FW version と module version の関係。
- マイナー変更時に module version を上げる条件。
- ソース内 version と `docs/CHANGELOG.md`、Git tag、release artifact の対応方法。
- 量産リリース後の hotfix / field fix / manufacturing variant の扱い。
- 量産移行時の手順書が必要。作成は今後の量産移行準備で実施する。

量産リリース時の推奨ヘッダ例:

```python
# NF55G Pico 2
# Module: nf55_protocol
# Module Version: 1.0.0
# Spec: Protocol_State_Machine Rev.0
# Product Release: FW-1.0.0
```

注意:
- 量産リリース前にこの形式を先行適用しない。
- Module Version は仕様差分や保守差分を追跡するための情報であり、Git / CHANGELOG / release tag の代替ではない。
- Module Version 運用開始時は、対象ファイル、初期 version、更新条件を人間確認後に確定する。

### 8.3 Release Gate
Phase 12 完了後、量産リリース候補を作る前に Source Versioning Gate を設ける。

Gate 条件:
- 全体 FW version naming が決まっている。
- Git release tag naming が決まっている。
- Module Version を持たせる対象ファイルが決まっている。
- Module Version 更新条件が決まっている。
- `docs/CHANGELOG.md` と release artifact の対応が確認できる。

## 2026-11-09 D4運用とCLEAR試験

D4は副作用のため量産では使用しない。D4-TIM-01は未解決のまま保守課題として保持し、CLEAR試験を優先する。CLEAR_ALL／POWER／BATTはCDのDATA0／1／2、T2=500ms。CLEAR_LOGはCLのDATAなし、T2=1000ms。r1 p.35に従い正常応答はどちらもDATA0文字。成功と成否不明時は既存Cache規則に従い無効化し、応答から昇格しない。CDで満充電情報等が初期化され初期充電が動作し得るため、今回ユーザー確認済みのバッテリ未接続条件で通信試験する。

## 2026-11-18 S1.15_r1受入の追加計画
[S1.15_r1検証スケジュール](S1.15_r1/Verification_Schedule_20261118.md)を追加。現行追加開発の段階1/4/5/6へV01〜09を割り当て、Phase 12/T9で新FWの単独・総合受入を実施する。段階0の7355単体確認を先行する順序は維持。日付・実機完了は未確定。
