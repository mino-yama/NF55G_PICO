# Pico Software Module / Interface Specification

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
