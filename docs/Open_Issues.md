# Open Issues
Revision: Rev.0
Codex must NOT close these by inference.

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
過去のAD/ARレビューにあるD6参照は当時の比較記録として保持する。r1への基準切替は既存Issueの解決・Closeを意味しない。

| ID | Issue | Rev.0 implementation |
|---|---|---|
| OI-01 | Pico-side T1 final value | 200 ms provisional |
| OI-02 | D0 T2 list=300ms vs detail=600ms | use 600 ms provisional |
| OI-03 | Current FW may clear CHARGE_END after D0 ACK | retain existing non-destructive D0 policy; confirm r1/final FW interpretation |
| OI-04 | AR REF/value8 final wire format and ATE return policy | Fixture draft keeps REF as raw8/open; interim FW appears to use IEEE754 float raw HEX. Decide raw/decode/both before final ATE release. |
| OI-05 | AD runtime coefficient immediate reflection vs reboot | Interim FW writes EEPROM and computes response-local slope, but runtime coefficient globals may not update immediately. No automatic reboot; confirm final behavior. |
| OI-06 | BC=0 STOP current FW behavior | implement spec; confirm final FW |
| OI-07 | BC MODE=13 response details | expose received data; confirm |
| OI-08 | SL out-of-range PME behavior | spec/FW confirmation |
| OI-09 | OR request while restart already active | current FW SQE; confirm |
| OI-10 | FD out-of-range address | current FW FF fill; confirm formal behavior |
| OI-11 | EB timing while command transaction active | keep original deadline; HIL confirm |
| OI-12 | AR T2 final value | confirm before final release |
| OI-13 | RTC HAT revision pin mapping | verify I2C scan 0x68 on received hardware |
| OI-14 | QR Cacheからのログファイル名生成 | 2026-09-18ユーザー指定によりQR読取Cacheをログファイル名に利用する。採用フィールド、命名形式、使用不可文字、重複時処理、未読時処理、TEST_STARTとの順序は未確定。OI-23参照。Openを維持する。 |
| OI-15 | Detailed USB CDC/PySide6 protocol | deferred phase |
| OI-16 | AD request/response wire format mismatch | Fixture draft defines AD as 10-char DATA control/set command; interim FW request is `TYPE1+POINT1+VALUE8` and success response is `TYPE1+POINT1+ADC6+CALC8`. Confirm r1/production FW/design expectation. |
| OI-17 | AD/AR target mapping and 12VOUT_I coverage | Fixture draft/decoder expose five AR systems; interim FW implements the same five targets, while `12VOUT_I` has a runtime coefficient but no AD/AR EEPROM slot. Confirm final target list and ATE names. |
| OI-18 | AD POINT/VALUE validation and rejection policy mismatch | Fixture docs leave POINT/VALUE validation open; interim FW uses POINT `1/2`, clamps out-of-range VALUE, and may not explicitly reject unsupported TYPE/POINT. Define final PME/SQE/clamp behavior. |
| OI-19 | AD persistence/write timing and EEPROM error behavior | Interim FW stores `correct_t` to EEPROM and returns after write check; final commit timing, busy behavior, retention, write-cycle limits, and HWE behavior need confirmation. |
| OI-20 | AR response length/order final confirmation | Fixture draft and interim FW both indicate 140 DATA chars: five targets x two points x `(ADC6 + REF/value8)`. Verify final production FW order/length before fixing ATE query behavior. |
| OI-21 | AD calibration preconditions and HIL acceptance criteria | Fixture docs assign PASS/FAIL to ATE and external measurement; interim FW has no visible AD-specific state checks. Define allowed state/load/output/charger interlocks and measurement correlation criteria. |
| OI-22 | r1 BOOT update interruption recovery wording and procedure | r1 p.37 section 12.5.2 removes D6 automatic recovery within 1 second and requires BOOT retry writing, but the introduction still describes differing automatic-recovery availability and (1) duplicates USER wording in (2). Design must confirm the supported recovery sequence and applicable FW. FU remains prohibited in the Pico fixture; this does not block ordinary communication development. See `RW11_D6_to_R1_Impact_Review_20260907.md`. |
| HW-01 | ADA-5703 GP4/GP5 and Pico-2CH-RS232 UART1 pin conflict | Adafruit ADA-5703 PiCowbell PCF8523 RTC/I2C circuitry is physically connected to GP4=SDA and GP5=SCL, while Waveshare Pico-2CH-RS232 fixes NF55G UART1 to GP4=TX and GP5=RX. 2026-09-04 real-hardware SD/RTC tests were performed with ADA-5703 GP4/GP5 physically isolated. Keep open until the final fixture physical cut/isolation method and inspection record are formally documented. |
| OI-23 | QR読取・Cache・NF55G書込み連携 | 2026-09-18ユーザー指定: 製品銘板図 NF55802-G_01.pdf のQRをリーダで読み、かんたんUSBホスト HIDキーボード用を介してPicoへ取り込む。ATEの読取開始コマンド後に読み取り、Pico側にCacheする。読取開始はPico専用コマンド。後続のATE指示によるNF55Gファームウェアのコマンドでの書込み、およびログファイル名にCacheを利用する。読取による自動書込みは行わない。詳細は QR_Reader_Requirements.md。銘板PDFとUSBホストマニュアルはreference/local_hardware_reference_20260904/required_for_development/に保存済み。2026-09-26に銘板図とUSBホストの受信関連仕様を確認。資料入手のみで本IssueをCloseしない。桁数は品名8桁・品目コード14桁・REV3桁・製造年2桁・製造週2桁・製造号機6桁（項目合計35桁）をユーザー指定として記録。2026-09-26: ユーザーが6項目の配置順と区切りなし35文字、英数字とハイフン許可を指定。単独QR受信・分割・一時Cache・REPL試作を先行し、SS連携は別工程とする。未確定: 許容範囲、年の解釈、正式ATEコマンド/応答/timeout、Cache名と寿命、USBホスト〜Picoの接続/ピン/電気条件、SSへの各フィールド対応、ログ命名規則。書込みコマンドはSSに確定し、保存Cache名は後日ユーザーが決定して紐付けを具体化する。生産LOT・生産年月・S/N情報の書込み範囲はUNIT_REV～BBU_SRLとユーザー確認。QRの製造年/製造週と「生産年月」の関係および各項目への割当ては未確定で、週から月を推測しない。提示SET_SERIAL画面のSS対象はUNIT/ADU/BBUそれぞれのREV・LOT・SERIALの9項目（画面SRLは既存SERIALに対応）。FW_REVISIONはFW書き込み仕様書のREVSIONと一致するかの照合のみで、SS対象外。比較元仕様書のファイル/版/期待値、比較規則、照合担当は未確定。QR REVは製品REVとしてUNIT_REVに対応し、FW_REVISIONとは別項目。QRの製品REV3桁と通信仕様r1 p.22 §8.5.3のUNIT_REV4バイトとの差異はユーザー認識済み。ラベルと通信仕様の整合および3桁から4バイトへの格納・変換方法を確認事項として継続管理する（末尾文字・空白等を推測補完しない）。年/週からLOTへの対応、号機からSERIALへの対応、ADU/BBU値の取得元は要確認。表示された末尾ピリオドやゼロ値を自動補完・既定値として採用しない。ユーザー提示の工程案はQR_SCAN/QR_GET/QR_PARSE/QR_DATA/既存WRITE/必要時READ/QR_VERIFYまたはATE照合。分解・桁数/文字種/範囲検証・書込み変換・CSVへの原文/解析値/書込み結果記録・ATEへの異常コード返却を要件として追記。名称は案。照合担当、リーダ開始指示方式、変換規則、エラーコード表、CSV列/試行識別も未確定。Picoでの一致照合を採用しても製品PASS/FAILはATEが判定する。従来のBLE案は今回の採用経路ではない。Openを維持。今回のユーザー許可によりQR単独試作のみ先行し、正式Cache/SS連携は保留。2026-09-26ユーザーがGP9←TX1/GP8→RX1/GND接続完了を報告。COM14でPIO初期化成功。テスト機はユーザー指定OPTICON L-46X。COM10=ATE、COM14=REPL。Pico VBUSからHOST VBUSと5V両方への給電接続完了をユーザー確認。HOST 5V/VBUS給電はユーザー確認OK（数値未提示）。D1/D2取り違えの可能性により以前のホストHID認識済み判断は撤回、現在D1点灯/D2消灯の報告。ATE開始受付は確認済みだがQR受信0byteでtimeout。通常USBキーボード接続ではD2点灯をユーザー確認。ABC+EnterについてPico実測4byte（ABC+LF）、QR_LENGTHを確認し、キーボード→ホスト→GP9受信経路の動作を確認。後続再試験で35文字+LF受信、6項目分割、RAM Cache READYとREPL表示まで成功。実測原文はUS250A-CGXE-009491-10101A2623000001。その後ユーザーが電源切/入でD2消灯再発、QRリーダ初期化を報告。初期化操作は電源投入時のトリガ10秒以上長押しとユーザー確認。メーカー作成第5版p.22 §3.1.4で強制起動中はホストへ読取データを出力しないことを確認。通常起動と区別する。保存設定への影響の詳細と認識再発の根本原因は未確定。電源操作対象/順序と、通常起動後USB挿入との比較は未確認。その後、キーボード接続→取り外し→L-46X接続でD2点灯するとユーザー報告。キーボード取り外し時のD2消灯とL-46X接続時の再点灯をユーザー確認済み。前機器の表示残留とは区別できた。L-46X単体の抜き差しではD2が点灯しないこともユーザー確認。キーボード認識を先行させる条件との差を優先調査する。今回状態での実データ再受信と、電源投入直後との差の原因は継続調査。認識改善の要因・給電品質・安定性は未確定。正式Cache/SS連携等を含む本IssueはOpenを維持する。手順はQR_Receive_Test.md。 |

## AD/AR consolidated review notes

Reviewed documents:
- `AGENTS.md`
- `README.md`
- `docs/ATE_Command_Master.md`
- `docs/ATE_Command_List_for_Test_Program.md`
- `docs/Data_Decode_Master.md`
- `docs/Cache_Master.md`
- `docs/Protocol_State_Machine.md`
- `docs/Software_Module_Interface.md`
- `docs/Test_Specification.md`
- `docs/Implementation_Plan.md`
- `docs/Program_State_Transition_Diagram.md`
- `docs/Real_Hardware_Test_Log.md`
- `docs/CHANGELOG.md`
- `reference/RW11用電源通信仕様書d6.pdf`
- `reference/NF55G_試験治具仕様書_Rev0_正本.docx`
- `reference/NF55G_試験治具仕様書_添付資料_CN24通信ハーネス結線表.docx`
- `reference/NF54191-G_S1.docx`
- `reference/開発手順(ChatGPT→Codex引き渡し).docx`

Interim FW source checked:
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_define.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_tbl.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_serial.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_global.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_global.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_input.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_init.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_eeprom.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_eeprom.c`

Consolidation map:
- OI-16 merges former OI-16, OI-20, and OI-29. The issue is one wire-format mismatch: fixture draft command/response expectation vs interim FW implementation.
- OI-17 merges former OI-17, OI-24, and OI-32. The issue is one target-list/mapping question: five AR systems vs runtime-only `12VOUT_I`.
- OI-18 merges former OI-18, OI-19, OI-27, and OI-28. The issue is one validation-policy question: accepted POINT/VALUE range and error/clamp behavior.
- OI-19 keeps former OI-21. Persistence/write behavior is separate from protocol field layout.
- OI-20 keeps the AR order/length part of former OI-24. REF representation and ATE return policy are tracked in OI-04 to avoid duplication.
- OI-21 merges former OI-22 and OI-26. Calibration preconditions and HIL acceptance belong together because both must be confirmed with production FW and design.
- OI-05 absorbs former OI-23 and OI-31. The issue is one reflection-timing question: EEPROM update vs runtime coefficient update vs reboot.

Detailed AD/AR differences:
- AD request/response format: `ATE_Command_Master.md` and `ATE_Command_List_for_Test_Program.md` define ATE command `AD_<TYPE>_<POINT>_<VALUE>` mapped to NF CMD `AD` with 10-char DATA, while interim FW parses DATA as `TYPE1 + POINT1 + VALUE8`. Current fixture docs treat AD as a control/set command, but interim FW returns success DATA `TYPE1 + POINT1 + ADC6 + CALC8`. Final production FW/D6-design expectation is not yet confirmed.
- AD VALUE/AR REF numeric representation: fixture docs intentionally keep AR `REF8` raw/open and do not finalize AD VALUE encoding. Interim FW uses `aschex_to_float()` and `float_to_aschex()`, which indicates IEEE754 float bit pattern encoded as 8 ASCII HEX chars. Endianness, ATE decoded display, and raw preservation policy must be decided.
- AD target mapping: fixture decoder and interim FW both indicate five calibration targets: `DISCHG_I`, `BATT_V`, `ACDC12V_V`, `BATT_CHG`, and `12VOUT_V`. Interim FW comments are narrower, describing battery voltage adjustment, and `12VOUT_I` has a runtime coefficient but no AD/AR EEPROM record. Final design must confirm whether `12VOUT_I` is intentionally non-adjustable.
- AD POINT/range handling: fixture docs leave POINT and VALUE validation as open design items. Interim FW maps POINT `1` to `point1/ad1` and POINT `2` to `point2/ad2`; unsupported TYPE/POINT may fall through without explicit PME/SQE, and out-of-range VALUE is clamped rather than rejected. Production FW must define whether invalid input is rejected, clamped, or treated as sequence/parameter error.
- AD persistence and reflection timing: interim FW writes calibration records to EEPROM and checks write completion, but successful AD appears to calculate response-local values without visibly updating runtime measurement coefficient globals such as `gf_batt_v_coeff`. This differs from an ATE expectation that immediate `AR_REFRESH` or subsequent measurements reflect AD. Confirm whether reboot, re-init, delay, or explicit refresh path is required.
- AR response shape: `Data_Decode_Master.md` defines AR as 140 DATA chars: five systems x two points x `(ADC6 + REF8)`. Interim FW matches 140 DATA chars and full frame length 146, ordered `DISCHG_I`, `BATT_V`, `ACDC12V_V`, `BATT_CHG`, `12VOUT_V`. This agreement still needs final production FW confirmation before the ATE query behavior is fixed.

Implementation cautions for AD/AR:
- Do not translate between tentative FW behavior and r1/design intent inside Pico. If interim FW behavior differs, expose it as an Open Issue and confirm with production FW/design.
- Keep AD implementation provisional until OI-16 through OI-21 and OI-04/OI-05 are answered. Parser strictness should follow the confirmed final format, not Codex inference.
- AD success or ambiguous failure must invalidate `DATA` and `AR`. ATE individual Query must not auto-refresh; ATE must explicitly run `AR_REFRESH` after AD.
- Do not update `AR` cache from AD response data unless final FW explicitly defines AD response as AR-equivalent.
- Do not update `STATUS` or `INFO` cache from AD/AR side effects, response status, D0 embedded status, or EB events.
- Treat AD `OK` as protocol success only. Calibration correctness, product behavior, and measurement PASS/FAIL remain ATE/design responsibility.
- For HIL, log raw AD frame DATA, AD result, retry counts, ambiguous flag, elapsed time, AR raw response, decoded ADC values, REF raw values, and external measurement values.
- Before final release, test each AR system, P1/P2, nominal/min/max/out-of-range AD values, malformed AD fields, power-cycle retention, immediate AR after AD, delayed AR after AD, and reboot-required behavior if applicable.

## 2026-09-26 キーボード経由の比較ログ
ユーザー操作: L-46Xを外す→キーボードD2点灯→外す→L-46X再接続でD2点灯。COM14 TX0診断にも対応する接続/切断を確認（LOSS表示なし）。
- 約221秒: Dell KB216 Wired Keyboard、VID/PID 413c/2113、EP0最大8byte、interface 2個。Report要求後にUsage Keyboardとreport解析内容が出力され、CALLBACK: 1 keyboard(s) now connected。
- 約228秒: disconnect, 0 keyboard(s) now connected。
- 約232秒: Opticon USB Barcode Reader、065a/a001、EP0最大64byte、interface 1個。Requesting report from interface 0から約294ms後にattach callback。Usage/Report解析ログは今回もないがCALLBACK: 1 keyboard(s) now connectedが出力された。
- 先のD2消灯時もReport要求→attachが約293msで、解析ログなし。違いはkeyboard登録の有無。
取得済み公開コードとの照合: udev_hid.cのhiddevice_init_endpointはgetHIDDeviceReportの戻り値を無視する。Report取得エラーは解析前return。USBHost.cの確認した切断/再登録経路はiface usageをクリアしておらず、main.cの登録判定はiface.usage == Usage_KEYBOARD。従って前のキーボードのUsageが残り、Report取得が正常化しなくても登録される仮説が今回の差を説明する。実機FW同一性・実際のReport転送結果/長さ未確認のため原因確定ではない。
従前の「単なるD2表示残留ではない」は維持するが、新規登録の根拠に前機器の内部情報が残留する可能性は別問題として追加。D2点灯を完全なHID初期化成功とは扱わない。
次に専用診断を継続したままQRを1回読み、TX0のKeyEvt等を確認する。これはキー入力経路の診断であり、QR Cache/35文字受信の再試験ではない。HOST設定/FWは変更しない。

## CH9350副作業: 新HID-UART基板（2026-10-11）

- CH9350-01（確認済み）: 2026-10-11ユーザー訂正により対象ICをCH9350と確認。状態2/3/4の11byteキーボードフレーム用デコーダと合成試験を追加した。販売基板固有仕様と実機互換性の確認は継続する。
- CH9350-02（Open）: GP4/GP5 UART1はNF55G専用として保持する。CH9350試験はGP9=PIO0/SM0受信115200bps/8N1、GP8=送信禁止High固定へ割り当てる。GP8/GP9のハードUART1機能は使わない。販売基板のTX電圧、DIP対応、電源容量、RX接続条件は未確認。既存QRのGP9/9600bps PIOの成功を新基板115200bpsの成功とみなさない。
- CH9350-03（Open）: CH9350資料p.7に下位機・状態2/3/4の単方向通信ではRXDをGNDにする条件あり。READMEのUART RX/TX接続候補との差は販売基板仕様と実動作で確認する。未知の基板端子を独断で短絡せず、モード/状態通知の応答要否も推測しない。
- CH9350-04（Open）: 評価基本設定をSEL=H/S1=H/S0=L/BAUD1=H/BAUD0=HのEVAL-CH9350-STATE2、量産候補を同論理のPROD-CH9350-STATE2として記録。販売基板DIP番号とON/OFFから各論理への対応は未確認で、現物測定後に確定する。量産候補は連続読取・再接続・電源再投入・電気評価の合格後に承認し、作業者判断で切り替えない。詳細はCH9350/docs/dip_switch_settings.md。
- CH9350-05（Open）: 評価基板固有の回路図・取扱説明書・DIP設定表は未入手。2026-10-11ユーザーから、販売ホームページ記載内容を基に基板情報をメモした旨の説明あり。DIP搭載、端子表示等はユーザー提供情報として記録し、ホームページ画面・記載日時・DIP設定表原文は未保存。ICデータシート確認事項および現物測定結果と区別し、記録がないことだけで仕様や設定を断定しない。
- 手順/結果: CH9350/docs/test_environment.md、CH9350/docs/test_results.md。OI-23および旧USBホスト調査はOpenを維持。NF55G既存プログラムとPico main.py/boot.pyは変更・配置していない。
