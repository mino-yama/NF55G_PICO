# Pico Software Module / Interface Specification

2026-11-23 QR/SSモジュール: `qr_write_session.QRWriteSession`がQR HOST GP9/115200診断フレーム、試行・取得ID・最初の完成値・照会済み状態を管理。`serial_data_from_qr`は承認済みSS50文字だけを生成する。mainの協調ループから有界pollし、明示QR_WRITEを共通dispatcherの内部SERIAL_SET_RAWへ渡す。SS正常応答DATA0／T2=100ms、既存DATA/INFO失効を共用。main.active_appは起動済みappを実機診断で再利用し、UART/SDの二重初期化を避ける。QR_HOST_ENABLEDは既定False、実配線済み親のみ有効化。[API・制約](QR_Hardware_Integration_20261123_01/SS_Workflow_Spec_20261123_Rev0.md)。

2026-11-23 ADC取得adapter追加: calibration_acquisition.pyが7355固有検証と機能照会→READを担当し、CalibrationMeasurementsのpending_matchesで試行境界を照合する。mainは取得中に同じlinkを専有し、既存外部pending/ATE scheduler/Logger経路へ接続。全497回帰成功。NF55G書込み経路なし。[取得/照会・内部境界](ADC_Acquisition_20261123_01/ADC_Acquisition_Spec_Rev0.md)。

2026-11-23 HOST通常RST補正: 親はRST受理後の新boot確認まで通常要求を拒否し、管理INFOでは通常sessionをbindせず次の明示要求のH/hで確立する。HOSTの`relay_host_take_reset`はACK送出完了後一度だけtrueとなり、mainがwatchdog期限を毎巡回で再設定することを防ぐ。reset due／BUSYは通常再起動まで保持する。Code／Test／仕様を同時更新、全476回帰成功。[仕様・実機記録](USB_Host_Reset_Study_20261121/Host_Reset_Management_Spec_20261123_Rev0.md)。

2026-11-22 CDC下位診断: 実機.22.2の初回IDNがTIMEOUT_RX0_T1_C0_XNONE|1となった。自動再送なし・fault保持。候補.22.3は受信関数の戻り後に対象bulk INのNAK/PID/転送状態を観測し、TIMEOUT Eだけへ追記する。vendor原典・転送制御・fault規則は変更しない。Host/Mock全467件成功（19.094秒）、ARMビルド確認中・実機未配置。[記録](Parent_Host_Integration_20261122_01/USB_Lower_Diagnostic_Rev0.md)。


2026-11-22 CDC期限比較: .22.1で50回共存成功（CSV853行/D1 50件/drop0/SHA一致）。500回の2秒期限試験は116成功後117回目TIMEOUT、10秒期限試験も72成功後73回目TIMEOUT。両条件でD1 Retry0・SD/RTC OK・drop0、USB_RX_XFER/TX_XFER通知なし。DMMは連続OFF/IMM/trigger1/sample1/delay0/DCV/error0を読取り確認済み。TIMEOUT受信長/TX完成/応答完成/末尾を記録する候補.22.2を準備、全465回帰成功、ARM build/ELF/UF2照合成功・未配置。[最新診断](Parent_Host_Integration_20261122_01/Timeout_Snapshot_Diagnostic_Rev0.md)。

2026-11-22 転送診断候補（未配置）: meter-host-relay-20261122.1は対象CDCの非SUCCESS callbackをlinker wrapで観測し、USB_RX_XFER/USB_TX_XFERとしてfault保持・既存E通知する。SDK原典・成功処理・自動再送禁止を維持。全464回帰・ARM build・UF2 metadata・ELF driver tableのwrap pointerを照合。TIMEOUT根本原因は未確定。[診断記録](Parent_Host_Integration_20261122_01/Transfer_Error_Diagnostic_Rev0.md)。

2026-11-22 CDC/NF55G/SD共存修正: 実機でREAD+D1+ローカル照会の連続burst時にSDログdrop（21回目6件、終了後8件）を検出。最終ATE応答後の無条件returnにより次巡回までSDを延期し、次burstが先着するとLoggerが飢餓になる経路を回帰試験で再現（修正前drop688）。最終応答送出後は同じ巡回の既存has_work/通信busy判定へ進め、ATE待ち/未送出/受信中は優先、NF55G/外部通信中のSD禁止は維持。追加2件を含むHost Unit/Mock全461件成功（9.859秒）。修正版の実機配置・共存再試験を進行中。[受入記録](Parent_Host_Integration_20261122_01/Acceptance_Status_Rev1.md)。

2026-11-21 目的訂正（未実装）: 本件は機器本体のRESETではなくHostのキャッシュ/通信保持状態のリセット。管理入口での状態クリアとHost再起動を分離し、通常の機器本文へ転送しない構成を検討。[現行Rev.2](USB_Host_Reset_Study_20261121/Host_Communication_State_Reset_Rev2.md)。正式API/方式は未確定。

2026-11-21 管理入口の検討（未実装）: RUN配線を使わずHost監視/WDT/親UART RESETを検討。管理要求を通常Q/機器本文から分け、FAULT/USB未接続時も照合・受付し、親対象リンクを再確立する構成案。フレーム/ATE名/期限は未確定、既存契約を変更しない。[検討Rev.1](USB_Host_Reset_Study_20261121/Host_Supervision_and_Software_Reset_Rev1.md)。

2026-11-21 量産USB-B接続/切断要件（未実装）: CDCデバッグ完了後、7355のUSB-B切断/再接続を操作者の手動RESETに依存させないFW対応を行う。unmount fault、途中要求のambiguous/Cache INVALID、旧CDC応答/遅延callback隔離、Host/親session再確立、READY/IDN確認前のREAD禁止を含む。機器RESET/SCPI初期化は対象外。方式・成功条件・量産受入は[USB-RELAY-HOTPLUG-01](Open_Issues.md)でOpen管理し、現行FWへの変更はまだ行わない。

2026-11-20 ユーザー方針更新: RUNパッド施工は難しいため外部RESET配線/駆動回路は進めず、手動RESET/電源再投入をデバッグで選ぶ。GP14/22は汎用予備。初回起動前から記録し、異常→正常データを交互に送る受入を計画。形式不正後の受付継続と、timeout/切断等の規定fault保持を分けて判定する。今回は計画のみ、実機注入/コード変更なし。 [計画](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Error_Normal_Alternation_Plan_Rev0/Plan_and_Reset_Decision_Rev0.md)／[現行GPIO Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev1.md)。

2026-11-20 工数/GPIO並行計画: 測定原文取得/ATE返却は実機済み。残る数値・単位/Cache/正式ATE入口とAD実装は仕様回答後コード/Mock1〜2実働日、基本実機確認含2〜3実働日（概算12〜24時間、待ち/全量産受入は別）。親GPIOは既存予約のQR GP8/9と実装済み測定器GP12/13を配線基準として維持。現行測定器PIOはSM4/5で旧案の順序に注意。RESETは必須/制御方式未確定、GP14/22を親側予備候補として確保しHost RUN結線は回路確認後。今回コード/Flash/実配線変更なし。 [工数](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Effort_Estimate_Rev0.md)／[配線基準](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev0.md)。

2026-11-20 ユーザー補足による解釈訂正: 「試験者設定のレンジ」はATE側のコマンドで決定/設定する意味。前面手動設定を前提にせず、ATEが固定レンジ値またはAUTO条件を指定→Queryで設定確認→測定要求を送る。Pico/Hostは本文を中継し、指定値の独自置換/自動最適化を行わない。次の安定性試験もこの順序で実施する計画。今回は記録訂正のみ、実機送信/コード/Flash変更なし。 [現行方針Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Next_Steps_After_ATE_Range_Decision_Rev1.md)。

2026-11-20 USB-RELAY-CDC-BUF-01（Open）: 提示CONF?が36byteの不正文字列に復号。固定SDK CDCのrx配列はTX macro確保64byte/初期化RX深さ256byteという不一致を確認し、実FIFOで隣接領域書換えを再現。Host側TX/RX256整合+ビルド時guardへ修正、新FW.3をビルド中。回帰3件追加し全453件成功。提示崩れの実機因果/20V問題は未確定でCloseしない。 [修正記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Result_Rev0.md)。

2026-11-20 .2実機試行10で親経由7355識別中継成功。ATEへOK:EXT_RX:32:HEXを返しADC Corp.,7355,246410099,  A02+CRLFを原文保持。Host入力線にHとQ一件を正常捕捉、再送/レンジ/READなし。試行9の起動00byte付き照合成功と合わせ同期修正の効果を確認。全受入/Issue Closeとはせず切断復帰/実負荷等は残る。シリアルモニターCOM7/57600 8N1を解放済み。 [解決記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/Resolution_Rev0.md)。

2026-11-20 起動時UART不具合を実原文で再現し修正: Host GP1で00 00+正常H（計77byte）を取得。旧Cは一行として破棄しhなし。Host受信を@先頭から同期させ、CRC/長さ/session/重複/故障保持/再送禁止を維持。回帰4件を追加して全450件成功。FW .2をビルド中、実機未配置。電気的起源と実機因果の最終確認は残りIssueはOpen。 [修正記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/Result_Rev0.md)。

2026-11-20 中継adapter実装: ExternalInstrumentLink/FrameReader、PIO1 SM4 TX/SM5 RX、FixtureApp/ATE入口を接続。execute_ate_lineは外部要求の受付時だけNone（pending）を返し、service_onceで完成後にATEへ返す。ATEポートなしの場合はtake_external_responseで回収する。Hostのrelay_wire/relay_host/relay_mainを独立UF2へ実装。HELLOはchipid|FW|状態、起動nonceはos.urandom/SDK get_rand_64。Host実Cと親Pythonの往復を検証。実PIO/CDC受入は未実施。 [リンク実装記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Result_Rev0.md)。

2026-11-20 ユーザー承認により開発用親子UARTを115200/8N1、親PIO1 GP12 TX/GP13 RX、Host GP0 TX/GP1 RX、@X1のsession/request付きCRC-32フレームとして確定。ATE名・上限・応答形式も確定。external_instrument_contract.pyへ承認値、本文保持パーサー、フレームencode/decode、ATE応答表現を追加。I/O/nonce生成/接続照合・本番scheduler/Host C FWは未接続。PIO資源・現物配線・端子対応と実機受入は未検証。 [確定仕様 Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Interface_Spec_Rev1.md)。

2026-11-20 外部測定器中継の第1段階: src/external_instrument_relay.pyを追加。GPIO/通信書式非依存の内部token、原文保持、明示応答有無/期限、送受信完了分離、遅着/旧接続拒否を管理する。正式ATE/親子UART、FixtureApp/Host FWには未接続。リンク再確立はadapterによる旧データ排除を前提とし、本コアだけで実機の遅着排除を保証しない。 [実装記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Result_Rev0.md)。

2026-11-19追加回答を実装: シャント50A/50mV、取得mV、換算担当は親Pico。`CalibrationMeasurements.get_calibration(token)`は電流対象のmV測定値を同じ数値文字列のAとして返し、元値/単位も併記する。BATT_VはVを要求する。単位不一致では候補を返さず、Cache原文は変更しない。正式ATE/Host API・AD表現は未確定。[詳細](ADC_Calibration_Development_20261119.md)。

2026-11-19 ADC測定値のRAM基盤: `calibration_measurement.py`の`CalibrationMeasurements`を`FixtureApp.measurements`へ追加。`start_trial/end_trial/begin/complete/fail/get/discard`は内部APIで正式ATE/Hostフレームではない。試行と取得の対応を照合し、完成応答のDecodeは将来adapterの責務とする。TEST_START/再STARTとTEST_END成立に連動。DMM通信/換算/AD送信は未接続。[詳細](ADC_Calibration_Development_20261119.md)。

2026-11-16 DMM制御方針（未実装）: 7355のASCIIコマンドと設定/測定手順はATE担当。親は宛先付き要求の転送/取得相関/Cache/Logger、追加HostはCDC接続と送受信/timeout/機器状態を担当する。一般ASCII応答から校正値を自動採用せず、明示測定要求の結果のみ取得Cache候補とする。正式中継API・変換担当は未確定。[最新分担とデバッグ範囲](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/DMM_ATE_ASCII_Control_Debug_Plan_20261116_Rev0.md)。

2026-11-16親PIO UARTピン確認: 現行src/・旧試作・周辺基板原典と照合し、QRは親GP8 TX/GP9 RX、7355は親GP12 TX/GP13 RXを第一候補とする。追加2 UARTはPIO1 SM0～3（MicroPython ID4～7）の予約案で、旧PIO0試作から分離。現物配線・SM load・命令メモリ/IRQ/受信負荷は未確認、正式API/FW定数は未変更。[割付根拠・物理pin表](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Parent_PIO_UART_Pin_Check_20261116/Pin_Assignment_Rev0.md)。

2026-11-16追加基板資料: 7355用はRP2350-USB-A/Switch Science SKU10275、USB-A→7355 USB-B。GPIO12/13のPIO CDC Hostを別FWで開発する前提を[回路・改造・FW調査](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/RP2350_USB_A_20261116/Assessment_Rev0.md)に整理。メーカーHID→Device CDCデモを7355 CDC Host実装済みとは扱わない。既存QR FW・正式親子UART/APIの契約は変更していない。

2026-11-10追加要求（未実装）: QR／7355のUSBは下位Waveshare RP2350-USB-C、治具との指令・データは双方向UART。USB処理は下位、ATE受付・試験との相関・Cache／Logger連携・NF55G処理は治具、測定対象制御と最終判定はATEに分担する。治具側PIO RX＋TX、要求／完了／機器通知の分離と非blocking受渡しを設計候補とする。現行QR受信adapterはRXのみであり、追加リンク実装済みとは扱わない。[開発準備資料](USB_Host_SubMCU_Integration_Plan_20261110.md)／USB-SUB-01参照。既存モジュール・正式APIの契約は今回変更しない。

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
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

USB CDC command-console implementation is deferred. The output-only `ReplDebugSink` mirrors CSV rows accepted by the SD sink through pollable `sys.stdout` only when `config.REPL_LOG_ENABLED=True`; the default is False. It does not accept ATE commands or create a second command interface. A future `usb_console.py` may feed the shared command core, subject to ATE/NF55G priority and nonblocking output constraints.

## USB HOST Wiring Scope (2026-11-19)

The [USB HOST interconnect specification](USB_HOST_Interconnect_Spec.md) records the Pico 2 / Expander / interconnect board wiring for the QR-side Waveshare RP2350-USB-C Host and the external-instrument Waveshare RP2350-USB-A Host (WAVESHARE-30274). The latter uses USB-C for development, USB-A as the Host port to the instrument's USB-B through a user-provided cable, and external power.
The interconnect board is a physical marker for clarifying USB HOST-to-Pico connection points and wiring, and an aid for hardware-design/debug explanations. It will be used to document the Pico-side port connections for planned USB CDC development and the already-developed QR function.
This documentation does not change existing design policy, GPIO assignments, communication control, module responsibilities, or firmware. It does not implement USB CDC or change its existing development status; no USB HOST driver or new communication protocol is introduced by this update.
Specific pin numbers and wiring locations, including the RESET connection, remain unconfirmed under USB-INT-01. Do not invent values for `config.py` or infer RESET behavior from the presence of the signal.
Physical interconnect documentation is distinct from the `usb_transport.py` USB CDC maintenance implementation; the existing software scope remains unchanged.

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

ATE physical interface: UART0, GP0=TX／GP1=RX, 57600bps／8N1. NF55G UART1 remains independently configured at 38400bps／8E1.

## Core interfaces

2026-11-11試行管理: CommandDispatcherが再TEST_STARTを前試行終了→新試行開始として扱う。Logger.test_end(protocol_busy=False, reason='TEST_END')は通信延期時に旧状態を保持。Logger.trial_id／last_test_id／test_history（最新8件）で現試行と完了試行を区別する。FileSDSink.trial_high_watermarkは両BANKの既存試行番号とopen済み番号の最大値。FixtureAppは試行ID変化時にQRReceiver.cancelを呼び、旧受信完了を採用しない。新USB下位UARTの試行／要求ID照合は引き続き未実装。
Runtime統合の詳細と検証範囲: [Runtime Integration](Runtime_Integration.md)。

- `SystemClock.ticks_ms()/sleep_ms()` をprotocol/cache/logger/schedulerで共有。
- `FixtureApp.service_once()/run()/stop()` がATE受信、idle EB、背景Loggerを統括。
- `NF55Protocol.busy/communication_busy/last_result`、`service_idle()`、
  `poll_hook`（ATE収集のみ）、`trace_hook`（RAM記録のみ）を追加。
- `FileSDSink` と `PicoSDSink` は通信中の実I/Oを拒否する。実カードと最終タイミングはHIL待ち。

`CommandDispatcher.execute_refresh(ate_name, payload=None) -> CommandResult`

- D1/D5のみ対応。開始時に対象CacheをINVALID、完全Decode後にVALID。
- 結果には元のTransactionResultを保持する。Protocol成功後のDecode失敗では
  `CommandResult.ok=False`、`transaction.ok=True`、`error=DECODE`となる。
- protocol外へ漏れた `OSError` はUARTエラー、ambiguous=Trueとして返す。
  この場合、復元できないelapsed_msとretry数はNone（未取得）。0回・0msとは扱わない。

`CommandDispatcher.execute_query(ate_name, payload=None) -> CommandResult`

- STATUS 37項目・INFO 26項目。Cacheのみを参照し、protocolを呼ばない。
- `FixtureApp.execute_ate_line` は両経路をparserのREFRESH/QUERY分類から呼び出す。

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

## 2026-09-26 QR単独試作
src/qr_reader.py: GPIO非依存の固定位置分割・受信状態・試作用ATEコマンド。
scripts/pico_qr_receive_test.py: 外部から渡したATE/QR受信ポートをポーリングし、受信結果をUSB REPLへ表示。import時のGPIO初期化/自動起動なし。NF55G/SD/本番dispatcherへ接続しない。

2026-09-26: qr_pio_rx.pyを追加。PIO0/SM0、GP9 RX、GP8 idle High。pico_qr_receive_test.start()でUART0と独立PIO受信を起動し、終了時に解放。UART1は初期化しない。

## 2026-11-09 試験ログ・QR S/N・最終診断

- FixtureApp.accept_qr(raw): 当該試験中の完全な35文字QRを検証し、末尾6桁のASCII数字をLoggerへ渡す。SDアクセス・NF55G送信なし。FixtureApp.qr_readerはQRReceiver(on_ready=accept_qr)。物理入力の接続は別工程。
- Logger.set_serial(serial): 試験期間内のみ受理し、S/Nを試験単位で保持。test_startで前回値を消す。test_endのclose後に命名を確定し、last_test_filename／last_test_sd_status／last_test_drop_countを保持。
- FileSDSink.rename_closed(filename): close済みのログを同じBANK内で変更する。既存先を上書きしない。S/N名も再起動時の容量集計・ローテーション対象。
- TEST_ENDはSelf Checkを最終段で実行し、FixtureDiagnostics.last_test_self_checkへRAM保持。PICO_SELF_CHECK?で現在LOGGERと直前TEST_LOGGER／TEST_LOG_DROPを別項目で返す。SD復帰はこの後の待機時に行う。

## 2026-11-09 履歴／FDの共通読出し

nf55_command.resolve_read_command(ate_name)は(cmd, target_cache, t2_ms, response_length, request_data)を返す。EL／OLは許可済み開始番号、FD_READは6桁ASCII HEXを検証する。ParserとDispatcherが同じ解決処理を利用し、不正要求は送信・Cache操作前に拒否する。CACHE_QUERY_COMMANDSに履歴192個とFD_DATA?を登録し、Dispatcherは既存のQuery処理を共用する。decode_el／decode_olはDATEHOUR（10進）、DATEHOUR_RAW、IDを各recordへ返す。Dispatcherが全Decode後に番号別Queryフィールドを組み立て、ブロックCacheへ保存する。

2026-11-09 build_item_parameter_command(ate_name, payload=None): PARAM_<ITEM>_<VALUE>の通常10項目を検証し、NF55CommandSpec(SP, DATA50, T2=100ms, cache_action=SP)を生成する。Parserで接続確認前に検証し、Dispatcher経由の直接呼出しでもBuilderが再検証する。未指定項目は変更なしマスク、予約18文字は0。既存SP応答0文字とCache無効化を共用する。

2026-11-09 BC CONTROL: 開始／停止をParserからexecute_controlへ接続し、NF55CommandSpecはBC_START／BC_STOPの既存Cache actionを使用する。共通Control Core内で接続確認を行い、BC開始時の旧結果無効化が未接続でも成立するようmain.pyの先行接続判定を移した。BC開始だけdecode_bcの完全結果をBC Cacheへ保存。BC Queryは共通execute_queryを利用する。

## 2026-11-09 SL追加

build_life_command(ate_name, payload)がLIFE_SET_<符号付き10進整数>／LIFE_SET_RAW=<ASCII>をSLのNF55CommandSpecへ変換する。Parserと共通Control入口の両方で書式を検査し、値範囲・DATA長・HEX妥当性による送信制限は設けない。RAWの制御文字／非ASCIIは拒否。DispatcherはT2=100ms・正常DATA0文字を検証し、既存SL Cache規則を使用する。Queryからの自動通信・実製品判定・応答の補正は行わない。

## 2026-11-11 USBサブMCUの隔離した初回確認FW

firmware/usb_submcu_acceptanceにType_C1 USB CDC専用の開発FW dev-20261111.1を追加。既存src/の量産通信ループやQR／DMM内部UARTへ組み込まない。ID?／PING／UPTIME?／ECHOはこの確認FW専用で、正式ATE／内部リンクのコマンドではない。USB Host／PIO／UART／GPIO／LED／SD／RTCは初期化せず、製品判定・測定・NF55G指令を扱わない。95文字上限・ASCII・CR/LF/CRLF・接続切断時の部分行失効と依存版は[確認FW仕様](../firmware/usb_submcu_acceptance/README.md)を参照。COM21個体だけへ書込み・照合し、USB実機123チェックを再起動前後各1回成功。[受入記録](USB_SubMCU_FW_Acceptance_20261111/Result.md)。USB-SUB-01／02はOpen継続。

## 2026-11-11 Type_C2 Host用配線の原典照合

Type_C2のD+はGPIO12／R12、D−はGPIO13／R11。メーカーRP2350_USB_C=1のpin_dp=12／DPDMと一致する。Host側FWの実装前提として[回路条件Rev.0](USB_Host_SubMCU_Host_Circuit_Conditions_Rev0_20261111.md)を参照。現在のdev-20261111.1はHostを起動せず、内部UARTピン・APIも確定しない。

## USB SubMCU実機前準備（2026-11-11）

[QR単体Host probe仕様・段階手順](USB_SubMCU_Host_Preparation_20261111/Preparation_Rev0.md)を追加。列挙とHID原文のみ、診断はRAM／任意TX候補で正式UART仕様とは区別。欠落・破損ログを検査し、35文字一致や製品合格に昇格しない。2 Host制約USB-SUB-03を追加。既存ATE／NF55G／Cache契約は変更せず、実機書込み・施工は今回行わない。

## USB SubMCU UART版の準備完了（2026-11-11、実機未受入）

[UART診断仕様](USB_SubMCU_Host_Preparation_20261111/UART_FW_20261111/Specification_Rev0.md)と[ビルド・検証結果](USB_SubMCU_Host_Preparation_20261111/UART_FW_20261111/Result_Rev0.md)を追加。qr-uart-20261111.1は追加基板GP0／115200・8N1のTX専用。既存76byteレコードをHEXで返し、起動版・IDをUSB開始前に送出する。ログは原文取得だけでQR35文字一致・製品合格としない。Host／Mock301件とファイル検証は成功、UART実機・QR・2 Hostは未受入。ATE／NF55Gの契約と正式親子UARTは変更しない。

## USB SubMCU基板内の診断QR復元（2026-11-14）

qr-uart-20261114.2は実機確認した限定HID形式をCモジュールで35文字へ復元し、診断レコードkind12へ完成原文、kind13へ理由1byteを記録する。正式な治具UART・ATE・Cache・Logger・SSには接続しない。内部状態だけで部分文字列を保持し、異常・timeoutで失効、切断で初期化する。[診断仕様と検証](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/Decoder_FW_20261114/Specification_Rev0.md)。基板内CデコーダのHost再生は成功、実機配置と連続読取は次工程。

## 2026-11-14 QRリーダー設定変更に伴う診断版の復元

ユーザーがQRのAlt設定から英語キーボードへ変更し、Alt処理不要・復元・再試験を指示。直前の基板内復元診断実装は採用せず履歴へ保存、現行作業ソースと解析をqr-uart-20261114.1のHID原文取得版へ復元。正式親子UART・ATE／Cache／SSは変更しない。Host／Mock326件成功、実機書戻しと英語設定再採取は次工程。[状態・証跡](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/English_Keyboard_Retest_20261114/Restoration_Result_Rev0.md)。上の.2診断仕様・テスト結果は過去時点の履歴として保持。

## 2026-11-14 Alt方式の基板内診断デコードを再採用

ユーザーが英語設定調査を打ち切り、観測済みAlt方式をデコードして続行と指定。メーカー初期化は行わず、現行作業ソースを保存済みqr-uart-20261114.2へ復元。正式親子UART・ATE／Cache／Logger／SSは変更せず、まず診断kind12で35文字を出す限定構成とする。Host／Mock346件成功、実機は.1のため再配置後に確認する。[再開・状態](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/ALT_Decode_Resume_20261114/Resume_Result_Rev0.md)。

## 2026-11-14 固定接続の診断ストリーム追加

qr-fixed-20261114.1はGP0 TXのみ115200/8N1・既存76byte HEXレコードで、kind12完成35文字とkind13理由を継続送信する候補。原文kind6は抑止、64件FIFOは排出後再利用し、欠落はseq gapとkind14のdropで検知。kind14は24byte uint32×6（main回数/frame/drop/完成数/HID数/flags）、kind15はphase+uint32の5byte。正式親子UART／ATE／Cache／SSではない。起動待ち3000msとAlt inter-report5000msは診断仮値で正式タイミングに採用しない。[仕様](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/ALT_Decode_Resume_20261114/Fixed_FW_20261114/Specification_Rev0.md)。


## 2026-11-14 Host基板と親接続経路の分離方針

ユーザー指示によりQRは既存Host、7355は追加Hostとし、親Picoとの双方向UARTを独立2経路に分ける。1基板のnative＋PIO 2 Hostと、既存QR基板Type_C1の改造案は採用しない。親のATE UART0／NF55G UART1は維持し、PIO等のGPIO・SM・IRQ・bufferを確認してから割り当てる。経路別の起動識別・要求ID・取消・timeout・部分受信状態を持つ方針。ピン・baudrate・正式APIは未確定、診断TXを正式リンクに昇格させない。今回コード変更なし。[構成方針](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Split_Host_Architecture_Rev0.md)。
