# Open Issues

## TEST-SESSION-01: 試験中断とTEST_START再受信時のデータ分離（Open、2026-11-11）

2026-11-11完了整理: 再START修正・Pico配置・正常系3試行・ログ回収は完了。懸念事項は継続調査とし、QR実入力／新USB要求相関、実SD異常系、量産Timing全般、START再送識別を残す。SSは保留。temp再回収3本もSD原本hash一致。詳細と完了範囲は[実装記録](Test_Interruption_20261111/Implementation_20261111.md)を参照。IssueはCloseしない。

2026-11-11修正版実機確認: 事前提示手順に従いCOM6へ4ファイル配置、旧25ファイル退避、配置hash一致。COM20でSC→D0→Query→10秒→再STARTと3試行を実施し、再START両方OK、旧DATA失効、独立CSV3本・SD／PC hash一致、保存診断正常・破棄0を確認した。再STARTのPC往復163.3／200.2ms。通常待受へ復帰・COM解放済み。[詳細](Test_Interruption_20261111/Hardware_Deployment_Result_20261111.md)。下記の実機未配置記述は過去時点。QR／SS・新USB要求相関・実機保存異常系・量産Timing全般は未確認で、IssueはOpenを維持する。

2026-11-11修正開始指示後: 再STARTの前試行保存→新試行開始をソースに実装。試行ID付きCSV、旧Queue・QR／S/N非継承、全製品Cache失効、保存延期時BUSY、前試行の保存診断と最新8件RAM履歴、既存BANKからの採番・容量管理を更新。Host／Mock284件成功。修正版の実機配置・Timing確認は未実施。SS開発は保留し、正式SS／新USB経路の要求相関は未実装。[実装記録](Test_Interruption_20261111/Implementation_20261111.md)。以下の未実装・着手待ち記述は変更前の履歴。残項目確認前のためOpen継続。

2026-11-11実機観測: ユーザー指定のTEST_START→SC→DATA_REFRESH→データ取得→10秒待機→再TEST_STARTをCOM20で実施。SC／D0成功、再STARTはERR:BUSY、通信IDLEで、同じCSVに記録された。TEST_END後の保存診断OK・破棄0、回収CSVのSD／PC hash一致。QR／SS未実施、src／tests／firmware変更・配置なし。[結果と証跡](Test_Interruption_20261111/Hardware_Start_Repeat_Result_20261111.md)。SS開発は保留し、本結果を基に開発着手のユーザー判断を待つ。IssueはOpen継続。

- ユーザー要求: 自律Refresh／PS_ON?／疎通確認で中断を推定せず、TEST_STARTの繰返しとTEST_ENDを基にQR／シリアルとTEST Logを保全する。まず混在調査と方針検討を行い、ソースへ即時反映しない。
- 確認事実: 現行の二重TEST_STARTはERR:BUSYで前回分を閉じない。Hostで、その後の操作続行と別QR受理により1本のログへ2試行分が入り、後のS/Nで命名されることを再現。QR受信途中にTEST_END→次STARTとし、旧QR完了が新試験へ採用される経路も再現。製品Cacheは試験境界で失効しない。QR→SS連携は未実装であり、製品への誤書込みを実証したものではない。
- 採用基本方針（2026-11-11ユーザー指定）: 受付済みTEST_STARTごとに独立した試行IDを付け、1試行1CSVとすることを最重要要件とする。1回目、2回目、3回目を同じファイルへ追記しない。前回分を終了指示未受信として保全し、QRの履歴保持と書込み利用資格を分ける。製品PASS/FAILや中断理由は推定しない。詳細設計・実装は未実施。
- 要求対象外（同日ユーザー指定）: 試験中は複数回のAC_OFFがあるため、製品電源瞬断の検出を要求しない。AC_OFFを試行分割の根拠にしない。Pico電源断時の途中データ消失は許容し、保持・復旧を要求しない。ただし通常動作での試行混在と既存CSVの追記・上書きは許容しない。
- QR／SS追加確定（同日ユーザー指定）: 製品交換を識別できないためQRは次試行へ引き継がない。同一製品の再試験もQRを再取得し、ATEの明示指示で再度SSを実行する。新試行の書込みシリアルが空ならエラーを返してSSをNF55Gへ送信しない。前回値や既定値で補完しない。前試行のQR履歴は前試行に保存する。正式エラーコード・空の具体的判定・SSフィールド対応は未確定でOI-23と関連する。
- 残確認事項: START再送の識別方法、最終中断後に次指示がない場合、切替え受付／保存完了応答、ID生成・命名衝突、保存診断履歴、製品Cache失効の具体化、SS空シリアルの判定・エラー詳細。方針採用だけでIssueをCloseせず、QR正式Pico連携の組込み前に修正する推奨時期と未実装状態を維持する。
- [案件調査と方針案Rev.0](Test_Interruption_20261111/Investigation_and_Policy_Rev0.md)。Host／Mock273件成功。実機未検証、src／tests／firmware変更・配置なし。OI-14／OI-23／USB-SUB-01と関連し、独断でCloseしない。

## ATE-EOL-01: CR単独受信の残留と後続コマンドへの影響（Open、2026-11-10）

2026-11-10方針確定: ユーザーが「要求はCR／LF／CRLFをすべて受理、定期CR単独は無視」と指定。旧CRLF限定方針を変更し、空行を無応答で破棄する受信処理へ修正した。応答はCRLFを維持。以下の未確定記述・旧実機結果は修正前の履歴。修正後の検証・配置は[対応記録](ATE_Line_Ending_Fix_20261110.md)を参照。人間確認前のためOpenを維持する。

- ユーザー指定確認項目: INFOのCR／LF／CRLF終端、コマンドなしCR定期送信の無視可否と後続正常コマンドへの影響。
- ホスト確認事実: CR単独は空コマンドとして実行されないが受信状態に残り、後続の正常CRLFコマンド1件がERR:FRAMEとなる。空CRLFは無視される。INFO単体は未登録でERR:UNKNOWN_CMD。
- 未確認・未確定: COM20実機での定期CR送信、SD処理への実際の影響、CRLF限定仕様とCR単独無視要求の扱い。実装変更・実機配置なし。独断でCloseしない。
- 詳細: [ATE終端文字・CR単独の確認](ATE_Line_Ending_Check_20261110.md)。

ATE-EOL-01追記（2026-11-10、Open継続）: COM20実機でD0入口DATA_REFRESHのCR／LF／CRLFを確認。CR／LF単独とCR単独10回定期送信後は、後続DATA_REFRESHが1回ERR:FRAME、次はOK。CRLF・空CRLF後・分割CRLFは正常。最短送信間隔113.966ms、終了時通信IDLE／SD・自己診断OK、破棄0。上記の定期CR実機確認は実施済みとなるが、SD滞留の実測と処置方針は未確定。コード変更なし。[実機結果と処置案](ATE_D0_Line_Ending_Hardware_Test_20261110.md)。


## BE-ACCEPT-01: 非バックアップ状態でのBE受付（2026-11-09、Open）

- 確認事実: r1 p.17はBEの受付をPS_OFF=不可、バックアップ中=可と記載。今回D1でPS_ON=1／BATT_ON=0を確認後、10:29:53 JSTにBACKUP_ENABLEを1回送信したところ、SQEでなく正常応答DATA15文字・OK（26ms、再送0、BCC一致）だった。前後のD1全フィールドは一致し、BACKUP_READY=1を維持。バッテリ未接続はユーザー報告。元PARAMはPS_ON_BACKUP=1。
- ユーザー観測: 出力変化・瞬断・再起動なし。電圧数値・波形は未提示。
- 未確認: 受付条件とPS_ON／BATT_ONの対応、r1 p.23の待機状態説明およびp.43の装置動作例との解釈、今回FWと最終仕様との整合。設計担当者の回答が必要。今回だけで製品FW不具合とは断定しない。
- 方針: PicoでOKをSQEへ置換せず、実応答を保持する。BF・OR・停電操作を追加して辻褄を合わせない。バックアップ中のBE正常動作・実放電は未確認。詳細は[実機記録](Real_Hardware_Test_Log.md)、[証跡](../temp/hil_backup_enable_20261109_run01/result_summary.json)。

Revision: Rev.0
Codex must NOT close these by inference.

## D4受信Timingの実機確認 2026-11-09

2026-11-09ユーザー指定: 副作用があるためD4は量産では使用しない。以下のTiming問題はCloseせず、保守時の課題として保持し、CLEAR試験を優先する。

- D4-TIM-01（Open）: D4_MAINT_READを2セッションで確認し、両方ACK_TIMEOUT、command retry 1、response retry 0、ambiguous=True。D4／DATA CacheはINVALID。T2=100msは変更していない。
- 確認事実: ACKはTXの6／7ms後。再確認ではACKから約102ms後、218byteフレームの170byteを部分RAWに記録。直後のCommand RetryのACK待ちでは0x20を観測し、最終ACK_TIMEOUT。後続の完全D4フレームはDATA212文字・BCC一致。elapsed114／115ms。
- 推測: T2内に応答処理が完了せず、再送時に前応答と競合している可能性。送出開始／完了、UART残量、Pico CPU負荷の寄与は未確認。FW違反と断定しない。
- 要確認: r1のT2定義と最終FW Timing、線上のACK／応答時刻、Pico受信バックログと処理負荷。Pico上のPython Mock再生もRESP_TIMEOUTだが、Mock負荷があり実UARTの証拠ではない。
- T2延長・遅延D4のCache昇格・ACK仕様変更はしない。設計確認後に再試験する。実測はtemp/hil_20261109_run01/events.jsonl。独断でCloseしない。

## 2026-11-09 試験ログ・自己診断の追加要求への対応

- OI-14／OI-23の一部要求をユーザー確認: ログ用S/NはTEST_START後に読むQR末尾6桁、命名はS/N＋開始日時、未取得時は日時維持。共通コアのRAM連携と終了時リネームを実装。両IssueはCloseしない。
- 未完了: 新USBホスト／物理受信ループ／正式QR ATEコマンドの接続、実カードでの命名・抜き差し・close・復帰・Timing検証。QRとSSの対応は今回確定していない。
- TEST_ENDの装置Self Checkを追加。SD異常でも試験受付を継続し、製品判定と装置診断を分離。既存CMD0不具合は未解決のまま。

## D2とPS_ON受付条件の確認 2026-11-07

- D2-PS-01（Open）: r1 p.18 §7.2(2)はPS_ON時にシーケンス／パラメータエラーを返さないと記す一方、p.17 §7.1注1はPS_ON後SET CLOCK処理完了までD2を受け付けないと記し、p.32 §10.6.1はSET CLOCK受信前にシーケンスエラーを返すと明記する。総則とD2個別条件の適用関係、SC未完了時の実FW応答を設計確認する。Pico側でSC自動送信や受付条件の補完を追加せず、独断でCloseしない。詳細: [D2とPS_ONの影響確認](D2_PS_ON_Review_20261107.md)。今回実機試験は未実施。

## 外部測定値による補正の追加要求 2026-11-04

- CAL-EXT-03（Open）: ユーザー指示により7355の通信仕様・アドレス設定を仕様化対象へ追加。採用GPIBアドレス、設定／保持／照合方法、ADC／SCPI選択、正確なコマンド、終端／EOI、応答表現、測定・timeout設定、異常復帰を確定する。メーカー製品ページではGPIBが+01オプション、ADC／SCPI対応と確認したが、実機搭載・マニュアル本文は未確認。値を推測で設定しない。GPIB制御経路はCAL-EXT-01と併せて確認。

- CAL-EXT-01（Open）: ユーザー指定はPico 2 UART0↔PIA5100↔GPIBのATE接続と、7355による外部シャント抵抗／製品電圧の測定。測定対象はATEが制御する。GPIB制御権、PIA5100のモード、7355読出し手順、ATE指令と測定応答の識別・中継方法は未確認。接続構成だけでPicoからの直接読出し可能と断定しない。
- CAL-EXT-02（Open）: 2026-11-04ユーザー確認により①DISCHG_I／充電、②BATT_CHG／放電は記載どおりで確定。取得と書込みは別コマンドとし、読取値を一旦ATEへ返して判定した後、ATEが改めて書込みコマンド＋数値を送る。取得による自動書込みは行わない。残事項はA/BとP1/P2対応、シャント換算の担当・符号・丸め、返却値の形式・単位、測定の鮮度、正式コマンド／応答／失敗時動作。既存AD/ARのOI-04/OI-05/OI-16～OI-21はOpenを維持する。
- 詳細: [追加要求記録](Calibration_External_Measurement_Requirements_20261104.md)。要求整理のみ。実装・機器仕様確認・実機試験は未実施。

## RP2350-USB-A QR入力経路の調査 2026-10-14

- RP2350-QR-01（Open）: THLN33のHID→ASCII/UART公開実装とWaveshare公式HID→ASCII/USB CDCデモを取得・ソース確認。THLN33は13byteバイナリ出力・AZERTY有効のため既存35文字＋LF受信とは互換でない。文字列UART出力への変更、リーダ配列・レポート形式、依存版の整合を確認する。ビルド・実機試験は未実施。
- RP2350-QR-02（Open）: 実装者からR13除去とD+/D-各15kΩプルダウン追加の報告あり。今回基板の版・回路・実装との一致は未確認。改造要否を推測で確定しない。電源容量・再接続・電源再投入の安定性も評価する。
- 詳細: [RP2350-USB-Aサンプル調査](RP2350_USB_A_HID_UART_Research_20261014.md)。OI-14/OI-23およびCH9350評価課題はOpenを維持する。

## 既存の未確定事項

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

- CH9350-06機器指定（2026-11-09、Open継続）: ユーザー提示画像から今回のQRリーダーをサンワサプライBCR-TC2D1BKと記録。公式仕様はUSB HID／Type-C／動作時230mA。Waveshare＋ハブ案のType-C下流データ接続、給電、HIDレポート・配列・終端、35文字受信、7355との共存を確認する。旧L-46Xの動作実績と区別する。

- CH9350-06最新方針（2026-11-09、Open継続）: ユーザー指摘によりQRと7355の両機能をWaveshare側で扱う。QR用CH9350を残す直前の案を修正。RP2350-USB-A 1枚＋USBハブでHID／CDCを共存させる案を優先検討する。TinyUSBとPico-PIO-USBのHID／CDC／Hub対応は資料確認済みだが、今回の機器・ハブ・基板版での同時動作は未検証。機器識別、バッファ、給電、切断復帰、治具との共通通信形式・Timingを確認し、型番・配線・正式APIは未確定のまま維持する。以下の追記は方針変更の経緯として保持する。

- CH9350-06追加指示（2026-11-09、Open継続）: 7355用追加マイコンはWaveshare製を使用する。型番は未指定で、RP2350-USB-Aを第一候補として提案。CDCホスト用C/C++実装、基板版・R13・VBUSの確認、7355との単体通信、治具へのUART／PIO接続とTimingが未検証。公式HID→CDCデモのCDCはPC向け出力で、測定器側CDCホスト対応の確認とは扱わない。詳細は[開発案](CH9350_QR_DMM_Plan_20261109.md)。

- CH9350-06追記（2026-11-09、Open継続）: ユーザーが測定器をADCMT 7355、接続をUSBと確定。保存済み英文取扱説明書§6.4（PDF104ページ）でUSBTMC／CDC対応を確認。CH9350はキーボード／マウスHID用のため、記載機能では7355のUSB制御に対応しないと判断。7355用のCDC／USBTMC対応USBホスト構成、実機FW・BUS設定・通信手順、既存ATE通信との共存は未確定。人間による構成確認・選定が必要であり、IssueはCloseしない。

- CH9350-06（Open、2026-11-09）: ユーザーからCH9350でQR読取とマルチメーター制御の両方を行いたいとの変更意向あり。CH9350はHID用途であり、7355等のUSB測定器制御への対応は未確認。測定器型式・USBクラス・転送方式、基板数と接続構成、従来PIA5100／GPIB経路の置換範囲を確認する。詳細は[変更要求記録](CH9350_QR_DMM_Plan_20261109.md)。対応可能とは確定せず、実装・正式仕様の切替えは未実施。

- CH9350-01（確認済み）: 2026-10-11ユーザー訂正により対象ICをCH9350と確認。状態2/3/4の11byteキーボードフレーム用デコーダと合成試験を追加した。販売基板固有仕様と実機互換性の確認は継続する。
- CH9350-02（Open）: GP4/GP5 UART1はNF55G専用として保持する。CH9350試験はGP9=PIO0/SM0受信115200bps/8N1、GP8=送信禁止High固定へ割り当てる。GP8/GP9のハードUART1機能は使わない。販売基板のTX電圧、DIP対応、電源容量、RX接続条件は未確認。既存QRのGP9/9600bps PIOの成功を新基板115200bpsの成功とみなさない。
- CH9350-03（Open）: CH9350資料p.7に下位機・状態2/3/4の単方向通信ではRXDをGNDにする条件あり。READMEのUART RX/TX接続候補との差は販売基板仕様と実動作で確認する。未知の基板端子を独断で短絡せず、モード/状態通知の応答要否も推測しない。
- CH9350-04（Open）: 評価基本設定をSEL=H/S1=H/S0=L/BAUD1=H/BAUD0=HのEVAL-CH9350-STATE2、量産候補を同論理のPROD-CH9350-STATE2として記録。販売基板DIP番号とON/OFFから各論理への対応は未確認で、現物測定後に確定する。量産候補は連続読取・再接続・電源再投入・電気評価の合格後に承認し、作業者判断で切り替えない。詳細はCH9350/docs/dip_switch_settings.md。
- CH9350-05（Open）: 評価基板固有の回路図・取扱説明書・DIP設定表は未入手。2026-10-11ユーザーから、販売ホームページ記載内容を基に基板情報をメモした旨の説明あり。DIP搭載、端子表示等はユーザー提供情報として記録し、ホームページ画面・記載日時・DIP設定表原文は未保存。ICデータシート確認事項および現物測定結果と区別し、記録がないことだけで仕様や設定を断定しない。
- 手順/結果: CH9350/docs/test_environment.md、CH9350/docs/test_results.md。OI-23および旧USBホスト調査はOpenを維持。NF55G既存プログラムとPico main.py/boot.pyは変更・配置していない。
