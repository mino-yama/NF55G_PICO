# Pico Software Module / Interface Specification

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

USB CDC detailed implementation is deferred. Architecture should allow a future `usb_console.py` to feed the same command core.

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
