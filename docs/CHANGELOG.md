# CHANGELOG

## 2026-11-09 試験ログ・QR S/N命名・最終Self Check

- ATE要求と実行結果を既存NF55G RAW／transactionログへ追加。TEST_START後のQR末尾6桁をRAM連携し、終了時にS/N＋開始日時へ変更。未取得・不正時は日時名を維持し、命名衝突は既存ログを上書きしない。
- TEST_START／TEST_ENDはSD異常でも試験受付・終了のOKを返し、装置異常は最終Self Checkへ分離。TEST_LOGGER／TEST_LOG_DROPを保持し、終了後の復帰で直前試験の保存異常を消さない。
- Logger／ATE／Interface／Runtime／QR要件／Test仕様とOpen Issuesの確定済み部分を追記。IssueはCloseしない。Host／Mock全195件合格。Pico配置、新QR物理入力、実カードのrename・抜き差し・Timingは未実施。

## 2026-11-09 SD抜き差し・試験終了後復帰

- SDログ開始失敗時も試験期間を保持し、試験中・連続記録中のSD_REINITをERR:BUSYで拒否。SD異常は保持し、再挿入だけで記録を再開しない。
- TEST_END／LOG_CONT_STOP後、ATE応答・待ち要求とNF55G通信を優先し、待機時に1回だけ再認識。電源投入時の既存FATマウント、フォーマット禁止、SD異常でも通信継続を維持。
- 未保存Queueの持越しを防ぎ、破棄件数を計上。SD異常時の既存ATE応答形式は維持。Logger／ATE／Runtime／Test仕様を更新。
- Host／Mock全189件合格。Pico配置・実カード抜き差し・冷間起動・Timing検証は未実施。既存CMD0不具合とOpen Issuesは未解決。

## 2026-11-09 CH9350によるQR・測定器制御の変更意向

- 提示画像2点を原本コピー保存し、QRリーダーをBCR-TC2D1BKと記録。メーカー公式のUSB HID／Type-C／動作時230mAを確認し、QR要件と共通化案に反映。Type-C下流接続・給電・HID形式・7355との共存は未検証。コード変更・実機試験なし。
- 最新指摘によりQRとDMMをWaveshare側へ共通化する方針へ修正。RP2350-USB-A＋USBハブでHID／CDCを扱う案、機器識別・同時接続・片側切断等の確認項目を変更要求に反映。直前のQR用CH9350を残す案は経緯として扱う。資料上の対応と実機未検証を区別し、コード・試験結果は変更していない。
- 7355用追加マイコンをWaveshare製とするユーザー指定を記録。RP2350-USB-Aを第一候補に、CDCホスト用C/C++実装、R13等の現物照合、単体通信から治具連携へ進む開発案を追記。型番確定・実装・基板改造・実機試験は未実施。
- 追加回答により測定器をADCMT 7355、接続をUSBと確定。保存済み取扱説明書§6.4でUSBTMC／CDCを確認し、HID用CH9350では対応しないとの資料上の判断、別USBホスト構成案と残確認事項を追記。従来外部測定要求に変更案への参照を追加。構成採用・実装・実機試験は未実施。
- CH9350でQR読取とマルチメーター制御の両方を行う意向を別文書に記録。HID用途と測定器USB制御の互換性は未確認としてCH9350-06を追加。
- 要求記録のみ。コード・正式接続仕様は変更せず、Host／Mock／実機試験は未実施。

## 2026-11-07 D3/D4 Refresh Host実装

- `D3_REFRESH`と`D4_MAINT_READ`を共通Parser/Dispatcherへ接続し、仕様既定のNF CMD、T2、応答長でDecode後に各CacheをVALID化。
- D3/D4成功時とambiguous failure時にDATA Cacheを無効化する契約を統合テストで確認。Decode失敗時も対象CacheをINVALIDのまま維持。
- Host/Mock全183件成功。ATE個別Query名は未定義のため追加せず、Pico配置・実機HILは未実施。

## 2026-11-07 NF55 RAWのASCII表示

- NF55送受信RAWの `raw_ascii` をRAM Queueの書出し時に生成。印字可能文字を表示し、制御文字・非ASCIIを `\xHH`、バックスラッシュを `\\` として保持する。`raw_hex`や過去CSVは変更しない。
- 書込み前に通信busyを再確認。Host/Mock全176件合格。Picoへ配置し、MicroPythonでSC・ACK等の表示変換を確認。通信中を含む実機タイミングと新しいNF55 RAWのSD書込みは未検証。

## 2026-11-07 RTC基準SC実機確認

- 変更済み4モジュールを退避・配置し、PicoとのSHA-256一致を確認。RTC `20261107_153531` をSCで送信し、直後のD0日時も同値。後続RTCとの差は-1秒（逐次取得）。
- SC/D1/D0の保存RAWはBCC一致、再試行0回。停電後や長時間の保持は未確認。D2-PS-01とOI-03はOpenのまま。

## 2026-11-07 SC Host実装とTIME変換修正

- `CLOCK_SYNC`に明示10進日時を渡し、SC DATA各欄をASCII HEXに変換。正常応答DATA長0、不正入力の送信拒否、成功・成否不明時のDATA/STATUS無効化を追加。
- D0/D4のTIMEをASCII HEX数値から10進日時へ変換。既存の日時Mockデータも原典形式に修正。
- 実機D0の時刻欄 `1A0B03100730` を観測。修正前表示は `201A0B03_100730`、修正後のオフライン解釈は `20261103_160748`。SC送信・配置・保持確認・D2実機試験は未実施。
- Host/Mock全173件合格。SC単体の実機応答や時刻保持はまだ確認していない。
- OI-03とD2-PS-01は未解決。SCの時刻差はAC OFF時間計算へ影響し得るため、試験時刻は担当者が決定する。

## 2026-11-04 補正方式の選択要件

- ①コマンド＋数値による直接書込み、②測定値取得・ATE判定後の別の数値付き書込み、の両方式を利用可能とする要件を追加要求仕様・開発計画に明記。
- ①は7355読取りの事前実行を不要とし、②は取得時に自動書込みしない。両方式の検証予定を追記。書込みコマンド名称の共通化／分離は詳細設計で決定する。
- 既定の開発順序を維持。文書のみ更新し、Code／Test変更・Host／Mock・実機試験は未実施。

## 2026-11-04 追加機能の開発順序

- ユーザー指示により「現在の実機確認 → QRコード読取り → 7355連携による外部測定値取得・補正機能追加」をImplementation Plan、README、追加要求仕様に反映。
- 7355の通信仕様・アドレス設定の詳細化、実装・試験を後続ステップとして記録。資料はreference/ADCMT_7355_20261104に保存済み。既存Phaseの並び・Issueの状態は維持。
- 計画文書のみ更新。Code／Test変更なし。Host／Mock・実機試験は未実施。

## 2026-11-04 外部測定値による補正の追加要求

- 7355の通信仕様・アドレス設定を仕様化対象へ追加。設定項目、未確定値、受入確認項目を追加要求文書に記載し、CAL-EXT-03で管理。メーカー製品ページでGPIB+01／ADC・SCPI対応を確認。マニュアル本文・実機設定は未確認。

- 7.3の3対象・各2点の設定目安と、既存の数値指定方式に追加する外部実測値取込み要求を別文書へ記録。
- ユーザー指定のUART0／PIA5100／GPIB／7355接続、外部シャント抵抗・製品電圧の測定、ATE側の測定対象制御を記録。
- 追記確認: ①DISCHG_I／充電、②BATT_CHG／放電はユーザー確認済み。取得値をATEへ返して判定後、別の数値付き書込み指令でNF55Gへ書き込む。取得による自動書込みは行わない。
- 未確定の転送手順、補正点対応、換算・正式コマンド等をCAL-EXT-01/02で継続管理。既存AD/AR IssueはCloseしない。検証予定に取得だけでは書き込まないことと書込み指定値の使用を追加。
- 要求整理のみ。正式コマンド・Code／Testの機能追加は詳細確定待ち。Host／Mock・実機試験は未実施。

## 2026-10-14 RP2350-USB-A QR入力サンプル調査

- Waveshare公式デモZIPとTHLN33固定コミットの主要8ファイルをreference/RP2350_USB_A_research_20261014へ原典コピーとして保存。SHA-256を記録。
- HIDからASCIIへの変換、USB CDCとUARTの出力先、THLN33の13byteフレームとAZERTY配列をソース確認。既存QRの35文字＋LFへの変更案を調査資料へ整理。
- 基板抵抗に関する実装者の報告、依存版、実レポート形式と量産安定性をRP2350-QR-01/02としてOpen Issuesへ追記。今回基板の改造要否は未確定。
- 検証はソース比較、保存ファイルのハッシュ照合、文書差分チェック。実装変更なし。ビルド・Host/Mock再実行・実機試験は未実施。

## 2026-11-07 D2_REFRESH Host実装

- `D2_REFRESH`（NF CMD D2、T2=100ms、DATA 30文字）を共通Dispatcherへ追加し、OFF_PERIODをD2 Cacheへ保存。
- D2 Protocol SUCCESS時にDATA Cacheを無効化し、ambiguous failure時もD2/DATAを安全側で無効化。D2専用ATE Query名は未定義のため追加せず。
- 成功Decode、T2/長さ、Cache invalidation、Decode失敗、ambiguous timeoutを含む全Host/Mock 164件が合格。Pico未配置・実機D2 HIL未実施。

## 2026-11-07 DATA_REFRESH (D0) Host実装

- `DATA_REFRESH`をNF CMD D0、T2=600ms暫定、応答DATA 327文字で実装。全DATA QueryはCacheのみ参照し、自動Refreshしない。
- D0内STATUS/Manufacturing/ParameterをDATA以外のCacheへ昇格しない。TIMEのASCII HEX検証を追加し、Decode不完全時にDATAをVALIDにしない。
- OI-03は未解決のまま維持。D0 ACK後のCHARGE_END挙動をPico側で補正しない。D0実機HILは未実施。
- 全Host/Mock 164件合格後、D0 integration/decoder focused 34件合格。Pico配置および実機D0通信は未実施。

## 2026-09-28 実機デバッグ前のコード説明コメント

- `src/`の24 Pythonファイルと`firmware/main.py`、`firmware/sd_startup_probe.py`に日本語の概要コメントを追加。各モジュールの役割と、ATE受信から通信・Decode・Cache更新・ログ保存までの流れを説明。
- 主要処理には、FU拒否、再送の分離、EB処理、Refresh開始時のINVALID、Queryの自動Refresh禁止、通信中のRAM記録、QR単独試作の境界を追記。
- コメント追加前後で全26ファイルのASTとコメント・空行以外のトークンの一致を確認。仕様・実行ロジックの変更なし。
- 検証: `.venv\Scripts\python.exe -B -m unittest discover -s tests` — Host/Mock 161件成功。
- Picoへの配置・実機通信は未実施。既存の未コミット変更を保持し、Open Issuesは変更・Closeしていない。

## HOST TX0比較ログ: 前機器Usage残留の調査

- L-46Xはキーボード経由でもReport解析ログが出ない一方、keyboard登録とD2点灯を確認。公開FWの取得エラー無視・Usage残留を原因候補として調査記録とOpen Issuesへ追加。実機原因は未確定。

## HOST TX0診断受信の追加

- GP10/PIO0 SM1/230400bps専用診断スクリプトを追加。既存PIO受信のpin/baud/SM/bufferを引数化しQR用既定値を維持。
- 大容量リングのwrap/overflowと不正サイズ拒否のHost試験を追加。実機ログ取得結果は別途記録。

## QR認識切分け - L-46X単体再接続では回復せず

- キーボードなしの通常起動後、L-46Xのみ抜き差ししてもD2消灯のままとユーザー確認。調査書・手順・実機ログ・OI-23へ反映。
- キーボード先行認識条件との差を優先調査。特定FW不具合の断定・設定変更・コード変更は行わない。


## QR認識切分け - D2消灯後のL-46X再認識を確認

- キーボード取り外しでD2消灯、L-46X接続で再点灯をユーザー確認。調査書・手順・実機ログ・OI-23へ追記。
- 前機器の表示残留という説明を除外。電源投入直後との差の根本原因は未確定。コード変更なし。


## QR認識切分け - キーボード経由の回復条件

- キーボード接続後にL-46Xへ差し替えるとD2が点灯するとのユーザー報告を記録。調査書・試験手順・実機ログ・OI-23を更新。
- 取り外し中のD2消灯とリーダによる実データ再受信は未確認。履歴依存の候補として扱い、根本原因の断定や恒久対策化は行わない。コード変更なし。


## L-46X通常起動時の認識継続調査

- 通常起動でもD2消灯と確認。メーカー公開FWの認識条件と未確定事項をL46X_USB_Recognition_Investigation.mdへ記録。実機FW一致・根本原因は未確定。設定/コード変更なし。


## QR切分け追報 - L-46X長押し起動操作の確認

- ユーザーの「強制初期化」は電源投入時トリガ10秒以上長押しと確認し、試験手順・実機ログ・OI-23へ記録。設定への影響は原典未確認として保持。コード変更なし。


## QR切分け追報 - 電源再投入後のD2消灯再発

- 電源切/入でD2消灯、QRリーダ初期化とのユーザー報告を試験手順・実機ログ・OI-23へ記録。先の受信成功と起動再現性を区別。
- 初期化内容/操作順と起動後USB接続の比較は未確認。コード変更なし。


## QR再試験 - 35文字受信・分割・Cache・REPL表示成功

- COM14でQR_TEST READYを確認。US250A-CGXE-009491-10101A2623000001とLF（36byte）を受信し、6項目と先頭ゼロ保持を確認。
- QR手順・試験仕様・実機ログ・OI-23を更新。コード変更なし。SS/CSVは対象外。認識改善要因は未特定のためIssueはCloseしない。


## QR切分け実測 - キーボードABC+EnterをPicoで受信

- COM14でABC+LFの4byteを確認し、期待どおりQR_LENGTHとなった。ホストTX1→GP9 PIO受信とLF終端検出の動作を実測。
- 試験手順・実機ログ・試験仕様・OI-23に記録。L-46Xによる実QR受信は未確認。コード変更なし。


## QR切分け追報 - USBキーボード認識成功

- 通常USBキーボード接続時はD2点灯とユーザー確認。L-46X接続時との差を試験手順・実機ログ・OI-23へ記録。UART/Pico受信成功とは区別する。コード変更なし。


## QR切分け追報 - 給電確認とLED識別訂正

- HOST 5V/VBUS両端子への給電OKをユーザー確認として記録。
- LED取り違えの可能性から、以前のD2点灯・ホストHID認識済み判断を撤回し、確認待ちへ訂正。QR試験手順・実機ログ・OI-23を更新。コード変更なし。


## 2026-09-26 - HID認識確認とQR受信診断追加

- PCでのHID入力とホストD2点灯をユーザー確認。Picoの直近timeout時Cacheは原文0文字。
- 試験専用の受信byte数/先頭64byte/総受信数の表示を追加し、タイミング外入力と無受信・終端不足を切り分ける。Host159件合格、Pico上の応答Mock試験合格。


## 2026-09-26 - QR試験ATE応答のMicroPython互換性修正

- COM10送信後、応答バッファのbytearray部分削除がMicroPythonでTypeErrorとなり試験が停止。スライス再代入へ修正してPicoへ再配置。
- Host/Mock159件合格。Pico上で試験runをMockポートに接続し、2byteずつの分割応答がIDLE+CRLFとして完了することを確認（ATE_PARTIAL_TX_PICO_OK）。実QR受信は未確認。


## 2026-09-26 - QRホストへのVBUS/5V給電接続を記録

- ユーザー報告のPico VBUS→HOST VBUSおよび5V両端子の給電接続完了を、試験手順・OI-23・実機ログに反映。
- 電源実測とQR読取結果は未確認。コード変更なし。


## 2026-09-26 - QRテスト機OPTICON L-46Xを記録

- QR要件・試験手順・OI-23・実機ログにテスト機型番とCOM10=ATE/COM14=REPLを記録。
- USB HID設定・Enter付加と実読取は未確認。文書のみの更新でコード変更なし。


## 2026-09-26 - 接続済みQR用PIO受信を追加

- GP9 RX/GP8 idle HighのPIO受信adapterと専用start()を追加。ATE UART0と共存し、NF55G UART1は変更しない。
- Host/Mock159件合格。COM14へ試験専用3ファイルを追加し、PIO初期化とGP9/GP8 High、受信エラーなしを確認。確認後停止。
- main.py/既存srcは変更なし。手順・Interface/Test/Open Issues・実機ログを更新。光学QR読取とATE指示の実測は待機中。


## 2026-09-26 - QR用GPIO候補調査

- 既存コードとRTC/RS232/SD資料を照合し、TX=GP8（物理11番）・RX=GP9（物理12番）・GND=物理13番を候補としてQR試験手順に記録。実配線確認は未実施。
- UART1の別ピンであるためNF55G用UART1と独立使用できないこと、共存時はPIO UART実装が必要であることを明記。今回コード変更・GPIO初期化・実機試験なし。


## 2026-09-26 - QR単独受信試作

- ATE開始後の35文字受信、6項目固定位置分割、一時RAM Cache、REPL表示の独立試作を追加。英数字とハイフンを許可。
- QR取得はSS連携と分離し、正式Cache名/SS変換/本番統合は保留。LF/CRLF・10秒timeout・100ms入力無通信確認は試験設定。
- 保存済みマニュアル/図面を確認し、手順・関連仕様・OI-23・Host試験を更新。実機はCOM未検出、配線/リーダ設定待ち。
- Host/Mock: 156件合格（QR新規9件）。Python構文検査・git diff --check合格。実機配備・HID読取・REPL表示の実測は未実施。


## 2026-09-18 - QR製品REVと通信仕様の差異を確認事項として保持

- ユーザーがQR製品REV3桁とUNIT_REV4バイトの差異を認識し、確認事項として残すよう指定。OI-23とQR要件に通信仕様r1 p.22 §8.5.3の根拠を追記。
- ラベルと通信仕様の整合、格納・変換方法は未確定。補完処理やCode変更、IssueのCloseは行わない。


## 2026-09-18 - QR REVは製品REV

- ユーザー指定によりQR REVを製品REV（UNIT_REV対応）と明記し、FW_REVISIONとは区別。QR要件・ATE仕様・OI-23・試験仕様を更新。
- QR3桁からUNIT_REV4桁への格納規則は未確定。Code変更なし。


## 2026-09-18 - FW_REVISIONは仕様書との照合のみ

- FW_REVISIONがFW書き込み仕様書のREVSIONと一致することを確認する要件をQR要件・ATE仕様・試験仕様・OI-23に記録。SS書込み対象外を維持。
- 比較元仕様書・期待値・比較規則・照合担当は未確定。今回は要件記録のみで、Code変更や実機照合は行っていない。


## 2026-09-18 - 生産情報のSS書込み範囲確認

- 生産LOT・生産年月・S/N情報の書込み範囲をUNIT_REV～BBU_SRLの9項目としてユーザー確認を記録。QR要件、ATE仕様、OI-23、試験仕様を更新。
- 各項目への割当て、QRの製造年/製造週と生産年月の関係、REV変換は未確定のまま。Code変更なし。


## 2026-09-18 - SET_SERIAL書込み対象の記録

- ユーザー提示画像を保存し、SS対象9項目と画面SRL/既存SERIALの名称対応をQR要件・ATE仕様に記録。
- QR REV3桁と既存UNIT_REV4桁の変換、LOT/SERIAL対応、ADU/BBU取得元をOI-23に明記。FW_REVISIONはGET表示のみ。試験仕様と資料一覧を更新。
- 詳細未確定のためCode変更なし。


## 2026-09-18 - QR読取CacheとSSの紐付け方針

- ユーザー指定により、QR読取値の書込みコマンドをNF55G SSとし、保存Cache名と詳細フィールド紐付けは後日決定する方針を記録。
- QR要件、ATE/Cache/Test仕様、OI-23を更新。自動書込み禁止を維持し、Code変更・Cache追加・SS連携実装は行っていない。


## 2026-09-18 - QRフィールド6項目の桁数指定

- 製造年2桁、製造週2桁、製造号機6桁を追加。品名8桁・品目コード14桁・REV3桁と合わせた項目合計は35桁。
- QR要件、OI-23、試験仕様を更新。文字種・範囲・配置順・区切りは未確定で、受信全長や切出し位置は推測しない。Code変更なし。


## 2026-09-18 - QRフィールド3項目の桁数指定

- 品名8桁、品目コード14桁、レビジョン（REV）3桁をQR要件に記録し、OI-23と試験仕様を更新。
- その他の桁数、文字種、配置順・区切り等は未確定。部分仕様の記録のみで、Code変更・QR機能実装はなし。


## 2026-09-18 - ATE主導QR工程の詳細要件

- QR読取、原文取得、解析・妥当性検証、解析値取得、変換・明示書込み、必要時の明示読出し・照合を工程分離する要件とコマンド案を記録。
- QR原文・解析値・書込み結果のCSV記録、ATEへの異常コード返却を追加。自動書込み禁止とATEによる製品PASS/FAIL判定を維持。
- QR要件、ATE/Cache/Logger/Test仕様、OI-23を更新。名称・形式・ハード制御・照合担当は未確定。Codeと実行テストの追加は詳細確定後とし、今回も機能未実装。


## 2026-09-18 - 製品銘板図の保存

- 訂正されたDesktopのパスからNF55802-G_01.pdfをrequired_for_developmentへ保存し、SHA-256一致を確認。
- 参照資料一覧、QR要件、OI-23の未保存状態を更新。本文解析・Code変更なし。詳細仕様とOI-14/OI-23は未確定のまま。過去の未保存記録は当時の履歴として保持。


## 2026-09-18 - QR読取経路とCache利用要件の部分確定

- ATEのPico専用読取開始後、QRリーダと「かんたんUSBホスト HIDキーボード用」を介してPicoへ取り込みCacheする要件を記録。
- Cacheを後続のNF55G書込みとログファイル名に利用する。自動書込みは行わない。
- ATE/Cache/Logger仕様、将来の受入試験観点、OI-14/OI-23、参照資料一覧を更新。詳細仕様未確定のためCodeと実行テストの追加は保留し、機能を未実装と明記。
- USBホストマニュアルは保存済み。銘板図は指定元パスに存在せず未保存・未読。以前の記録は当時の状態として保持。


## 2026-09-18 - QR label read/write feature discussion recorded (no implementation)

- Recorded a new discussion: reading product label QR (revision/year/week/serial) and writing parsed values into NF55G, driven step-by-step by explicit ATE commands (proposed: `QR_SCAN`/`QR_GET`/`QR_PARSE`/`QR_DATA`/existing NF55G WRITE-READ/`QR_VERIFY`), with a proposed Pico-side `QR_RAW`/`REV`/`YEAR`/`WEEK`/`SERIAL`/`VALID`/`TIMESTAMP` cache.
- Product nameplate drawing `NF55802-G_01.pdf` was shared as future reference for the QR format but has not been added to `reference/`, and no textual field layout was provided.
- No code, command, or cache was implemented. Added `docs/Open_Issues.md` OI-23 to track all unconfirmed items (QR field layout, command/cache names, reader interface, and Pico 2 vs Pico 2 W hardware choice for a possible BLE HID Host reader).

## 2026-09-16 - Pico 2 hardware communication test

- Recorded the COM14 HIL results for microSD, DS3231 RTC, and two-channel RS232C in `docs/Real_Hardware_Test_Log.md`.
- SD passed after one retry and RTC passed; RS232C UART initialization passed but both loopback receive checks returned zero bytes. No NF55G command/control was transmitted.

## 2026-09-16 - RS232C loopback retest after wiring correction

- Re-ran the COM14 RS232C HIL after correcting the loopback wiring. CH0 and CH1 both passed 256-byte exact loopback and 100-frame stress with zero crosstalk.
- No NF55G command/control was transmitted.

## 2026-09-16 - Base board selection update

- Replaced the hardware baseline base board identification with SeeedStudio 103030397 (GPIO EXPANDER QUAD RASPBERRY PI PICO).
- Kept the existing UART, RTC, and microSD GPIO assignments unchanged; electrical and mechanical verification of the new base board remains a hardware follow-up.

## 2026-09-10 - Runtime clock, EB, ATE, and real SD integration

- Integrated shared Pico-compatible monotonic clock, bounded EB processing without Cache promotion/deadline resets, transaction exclusion, UART exception results, and protocol-level FU blocking.
- Added operator-confirmed CRLF ATE transport and cooperative scheduler, partial reply handling, RAM protocol traces, and transaction summaries.
- Added FAT CSV sink and HIL-derived SPI SD driver with CSD capacity, bounded waits, RTC filenames, owned bank rotation, deferred flush, and failure/reinit handling. Fixed host CSV CRLF corruption and deferred-flush recovery found by tests.
- Added 31 runtime Host/Mock tests; all 136 tests passed. Added `Runtime_Integration.md` and deployment entry-point candidate; updated related specifications. No Pico deployment or real NF55G communication was performed. Physical SD/firmware timing validation and Open Issues remain pending.

## 2026-09-10 - D1/D5 Refresh and Cache Query paths

- Added explicit D1/D5 read definitions and STATUS/INFO query allowlists; wired parser and FixtureApp to shared dispatcher handlers. Flags return 0/1, parameter values decimal, and manufacturing text preserves leading zeros.
- Refresh invalidates its target before communication and validates only after complete decode; invalid queries never transmit. Added HWE minimum invalidation and ambiguous UART OSError reporting with unavailable timing/retry metadata represented as None.
- Added 14 Host/Mock integration tests covering all 63 queries, failure/retry paths, invalidation, no-auto-refresh, and FU blocking. All 105 tests passed; no Pico deployment or NF55G transmission.
- Updated ATE/interface/test documentation and HIL readiness. Pico clock, EB, scheduler, real SD logger integration, and existing Open Issues remain pending.

## 2026-09-10 - Real NF55G HIL preparation

- Added `docs/NF55G_HIL_Preparation.md` with entry-gate status, wiring/firmware records, ordered firmware preparation, and an initial D1/D5 procedure for use only after the existing gates are met.
- Audited the current skeleton: missing Refresh/Query dispatch, production scheduler, Pico clock integration, EB handling, transaction re-entry/exception protection, and physical SD/RTC logger integration. Confirmed unsupported Refresh/Query responses in a host-only check; 91 passing tests do not cover these missing paths.
- Separated D0's open side-effect question, BC/control actions, AR/FD issues, and all FU prohibition from the initial read sequence. No NF55G transmission, firmware placement, specification relaxation, or Open Issue closure.
- Recorded operator confirmation of PC–Pico connection and loopback removal; FW revision remains undecided and product connection/power state is unconfirmed. Host/Mock regression: 91 tests passed; diff check passed.

## 2026-09-10 - SD initialization repeat check

- Three sequential SD mount probes and a 160-record basic I/O run passed under normal permissions on COM14; all exited 0. Logger readback: 161 lines, 160 writes, 5 flushes, 1 close, 0 drops; clean reinit OK.
- Recorded result payloads in the hardware log. No CMD0 recurrence was observed, but cold-start initialization and the original cause remain unverified. No runtime changes or Open Issue closures.

## 2026-09-10 - UART two-channel loopback verification

- Re-ran `pico_uart_hil.py --port COM14 --bytes 256 --frames 100` under normal permissions; exit 0. Both UARTs passed 256-byte exact loopback with zero crosstalk and 100 frames / 3500 bytes per channel.
- Recorded the command, raw result payload, operator-reported wiring, and limits in `docs/Real_Hardware_Test_Log.md`. A previous run's session was lost and is not used as evidence.
- No runtime/firmware changes, NF55G protocol commands, or Open Issue closures. Final-firmware HIL and the earlier SD initialization anomaly remain pending.

## 2026-09-09 - RTC/SD rerun port access

- Recorded initial COM14 access denial under both normal and elevated execution, then successful RTC scan/read after the operator released the port. User reports both RS232 channels shorted for loopback.
- Recorded an initial SD `CMD0 failed: 31`, followed by a successful mount-only probe and complete 160-record SD basic retry (161 lines, 160 writes, 5 flushes, 1 close, 0 drops, clean reinit OK). The initial SD anomaly remains unexplained; no firmware changes or Open Issue closures.
- Operator later clarified that the SD card was removed/reinserted between failure and recovery. Updated the hardware log: contact quality is a candidate, but reinsertion-related card-state changes are not ruled out.

## 2026-09-09 - Pico identity and deployment inventory

- Added `scripts/pico_inventory.py` for read-only MicroPython identity/filesystem inspection through `mpremote connect COM14 resume run`, with no automatic soft reset or peripheral initialization.
- Verified Pico 2 / RP2350, MicroPython v1.28.0, and a root containing only `/sd`; no root boot/main files or fixture source deployment were observed. SD contents and frozen modules were outside the inspection scope.
- Recorded raw output and the user's confirmation of current ADA-5703 GP4/GP5 physical disconnection in `docs/Real_Hardware_Test_Log.md`. HW-01 remains open for final inspection traceability; no NF55G commands were sent.

## 2026-09-09 - Windows development environment setup

- Added workspace VS Code settings for the local Python environment, unittest discovery, and cmd.exe terminals; added process tasks for Host/Mock tests and dependency checks. Store PowerShell still requires elevated execution in the observed tool environment; OS permissions were not changed.
- Created a local ignored `.venv` and added `requirements-dev.txt` for HIL, Word generation, and MicroPython tooling.
- Added `docs/Development_Environment.md` with cmd.exe setup commands and the current installation limitation; linked it from README.
- Initial restricted installation failed because pip ignored its package index. A subsequent user-authorized elevated installation succeeded into the local `.venv`; direct dependencies are pinned to pyserial 3.5, python-docx 1.2.0, and mpremote 1.29.0.
- Validation under normal permissions: all 91 Host/Mock tests passed, `pip check` found no conflicts, RTC/SD/UART HIL and mpremote help commands succeeded, and COM14 was enumerated. `git diff --check` passed. No hardware commands, protocol changes, or Open Issue closures were performed.

## 2026-09-07 - r1 development baseline adoption

- Adopted `reference/RW11用電源通信仕様書r1.pdf` (GVT-284454-001-00, first edition 2026/9/4) as the current baseline at user request; local SHA256 matches the existing impact review.
- Updated AGENTS.md to Rev.1, startup/handoff guidance, reference index, current Master/plan baseline references, and active issue guidance. D6 originals and historical review/test records remain available.
- Documented PS_OFF-only OFF_PERIOD updates and the corresponding real-NF55G checks. Existing ordinary wire formats and runtime code require no change from this revision; no product behavior is emulated in Pico.
- FU remains disabled, unresolved issues remain open, and the inspection discussion document remains a discussion rather than an adopted specification.
- Validation: Host Unit/Mock suite (`python -m unittest discover -s tests`) passed all 91 tests; `git diff --check` passed. Real NF55G r1 behavior remains unverified.

## 2026-09-07 - D6 to r1 specification review

- Added `docs/RW11_D6_to_R1_Impact_Review_20260907.md` with full 43-page text/image comparison, change list, implementation impact, and remaining verification.
- Added OI-22 for r1 BOOT update recovery wording/procedure confirmation; FU remains prohibited and existing issues remain open.
- No runtime, test, original-source, or baseline-rule changes. Existing host/mock suite: 91 tests passed. Real NF55G r1 behavior remains unverified.

## Rev.0 - 2026-09-01
Initial Codex handoff baseline.

Included:
- ATE command architecture
- explicit Refresh + Cache
- Data Decode master
- Cache invalidation/post-check rules
- Pico software module boundaries
- Protocol state machine
- Command Retry / Response Retry separation
- ambiguous transaction policy
- Mock NF55G and host test plan
- Logger/SD formal specification
- FU hard prohibition
- ATE priority rule
- USB CDC detailed implementation deferred
- Fixed implementation phase order in `docs/Implementation_Plan.md`
- Defined development vs production source versioning policy

Initial implementation start:
- Added `src/config.py` constants for frame bytes, timing, retry, cache names, and invalidation policy.
- Added `src/models.py` lightweight shared model classes.
- Added `src/frame.py` for NF55G frame build/parse and BCC calculation.
- Added `src/nf55_decode.py` pure decoders for D0/D1/D2/D3/D4/D5/BC/EB/EL/OL/AR/FD.
- Added `src/cache_manager.py` for power-on invalid cache state, validate/invalidate, refresh failure, and control ambiguous/success invalidation.
- Added initial host `unittest` coverage for frame/BCC, cache, and decode basics.
- Expanded decoder unit tests to cover D0/D1/D2/D3/D4/D5/BC/AR/EL/OL/FD normal lengths, wrong lengths, key numeric conversions, status bit decode, FD raw preservation, and EL/OL START_NO mismatch.
- Added comprehensive D0 Golden Data assertions covering TIME, REALTIME, OFF, LIFE_CALC, LIFE_DIAG, ACCUMULATED, MFG raw/decode, PARAM raw/decode, and STATUS raw/decode.
- Added host-side Mock NF55G with `FakeClock`, `MockUART`, `ResponseFactory`, and scenario steps for ACK, NAK33, ACK_TIMEOUT, RESP_TIMEOUT, BCC NG, PME, SQE, and HWE.
- Added `src/nf55_protocol.py` transaction state machine covering WAIT_ACK, WAIT_RESPONSE, VALIDATE_RESPONSE, COMMAND_RETRY, RESPONSE_RETRY, SUCCESS, and FAILED paths with host unit tests.
- Added control command/cache integration for CHARGE_ON, CHARGE_OFF, BACKUP_ENABLE, OUTPUT_RESTART, PARAM_SET, and related control commands, with tests for success invalidation, parser rejection, PME/SQE no-invalidation, HWE/ambiguous invalidation, and no automatic post-refresh.
- Added Logger/SD core with RAM queue, host memory SD sink, TEST_START/TEST_END, LOG_CONT_START/LOG_CONT_STOP, SD_STATUS?, SD_USAGE?, LOG_DROP_COUNT?, SD_REINIT, forced drain on TEST_END, drop counting, and no write/flush while protocol busy.
- Recorded separate SD real-hardware debug checklist for Mount, CSV creation, Write, Flush, Close, continuous logging, card removal, write error, and reinitialization.
- Added Pico-side RTC command support for RTC_DATE?, RTC_TIME?, RTC_DATETIME?, RTC_SET_YYYYMMDD_HHMMSS, and RTC_CHECK? using a DS3231 abstraction, explicitly separate from NF55G SC/CLOCK_SYNC.
- Added Pico/MicroPython `DS3231I2CDevice` access for I2C0 GP20/GP21, including BCD datetime read/write and OSF clear, with host fake-I2C tests.
- Added and consolidated AD/AR Open Issue review notes, including interim FW analysis, into OI-16 through OI-21 plus OI-04/OI-05 refinements for production FW/design confirmation.
- Added HW-01 for the ADA-5703 PiCowbell GP4/GP5 physical conflict with Pico-2CH-RS232 NF55G UART1, and noted that disabling PiCowbell RTC in software is not sufficient.
- Added a first-step real-hardware debug notice and T8 pre-check requiring ADA-5703 GP4/GP5 physical isolation before final fixture UART/SD debug.
- Recorded that 2026-09-04 Pico 2 SD/RTC real-hardware tests were performed with ADA-5703 GP4/GP5 physically isolated; HW-01 remains open for final fixture isolation/inspection traceability.
- Added `docs/Desktop_to_VSC_Migration_Plan.md` to define the Desktop Codex to VSC+Codex scope boundary, migration gate, current status, VSC start checklist, and required real-hardware records.
- Added `docs/Desktop_to_VSC_Migration_Plan.md` to `HANDOFF_MANIFEST.txt`.
- Added `reference/NF55G_VSC_Codex_Migration_Guide.md` as a supporting reference for ChatGPT -> Desktop Codex -> VSC+Codex staged migration, maintained until VSC+Codex handoff and retained as a record afterward.
- Added the VSC+Codex migration guide to `HANDOFF_MANIFEST.txt` as a supporting reference file and clarified generated migration/support notes in `reference/README_REFERENCE.md`.
- Added `scripts/pico_sd_hil.py` as a repeatable Pico 2 MicroPython SD HIL runner for SD mount, CSV write/readback, current logger queue-path verification, and clean SD reinitialization checks.
- Recorded 2026-09-07 Pico 2 SD logger queue-path verification in `docs/Real_Hardware_Test_Log.md`; host `tests.test_logger_sd` passed and Pico 2 SD queue/readback completed with 160 records, 5 flushes, 1 close, and 0 drops.
- Extended `scripts/pico_sd_hil.py` with configurable queue/load record count and an interactive card removal/reinsert mount probe; recorded a 2000-record Pico 2 SD logger load pass with 0 drops.
- Recorded Pico 2 microSD physical removal detection and post-reinsert remount/write/readback recovery; forced write-error injection remains pending.
- Recorded an inconclusive forced write-error attempt: physical removal after opening a MicroPython file did not surface a logger-visible write/flush error after either 1-record or 256-record attempts, so a lower-level fault-injection procedure is still required.
- Recorded final post-fault-attempt SD remount/write/readback recovery on Pico 2, confirming the card returned to normal operation after reinsertion.
- Re-ran Pico 2 SD removal/reinsert checks after the prior physical-removal timing was found uncertain; baseline write/readback, removed-card mount failure, post-reinsert remount, and post-reinsert logger write/readback all passed.
- Added `scripts/pico_uart_hil.py` for Pico 2 MicroPython RS232C 2ch loopback HIL checks and recorded CH0/CH1 init, 256-byte loopback, no-crosstalk, and 100-frame stress PASS results; 512-byte single-write behavior is recorded as a HIL buffering limit observation.
- Added host-testable Pico hardware/transport layer skeletons (`ate_uart.py`, `nf55_uart.py`, `diagnostic.py`, `command_parser.py`, `main.py`) plus tests for local routing, diagnostics, `FW_UPDATE` prohibition, and no-control behavior before NF55G connection.
- Added `scripts/pico_rtc_hil.py` and recorded a pre-NF55G readiness check: host tests passed, RTC/SD/UART HIL checks passed on Pico 2, and remaining work is gated on final fixture isolation evidence, final firmware path, and real NF55G availability.
- Revised Desktop-to-VSC migration and test plans for the 2026-09-07 boundary: Desktop Codex completed host/mock plus Pico 2 RTC/SD/UART REPL HIL; VSC+Codex takes over final firmware placement/build/flash, final-firmware reruns, low-level SD write-error fault injection, and Real NF55G HIL.


## 2026-09-10: Integrated Pico deployment

Deployed 23 Python files with matching SHA-256; real RTC/SD smoke, 64-row CSV readback after remount, RAM ATE CRLF/FU rejection, and scheduler run/stop passed. NF55G disconnected; observed NF55G TX zero. Device left in REPL; cold boot and physical ATE/NF55G tests pending.

Evidence and limitations: [Pico deployment](Pico_Deployment_20260910.md). Reproducible finite check: `scripts/pico_runtime_smoke.py`.


## 2026-09-10: SD startup diagnostics

Added RAM-only first-startup SD stage/error snapshot; no automatic retry, added delay or ATE format change. Soft-boot mount passed; cold-power failure cause remains unconfirmed. Host/Mock: 138 tests passed. See [investigation](SD_Startup_Investigation.md).


## 2026-09-10: Controlled SD cold-start comparison prepared

Added opt-in startup delay / CS-before-SPI settings (normal defaults unchanged) and temporary `firmware/sd_startup_probe.py`. Pico /main.py now selects DELAY_ONLY: 500 ms wait, original CS order, one CMD0 attempt. Cold-power result pending; normal entry point must be restored after investigation. Host/Mock: 139 tests passed. See [experiment matrix](SD_Startup_Investigation.md).


## 2026-09-10: DELAY_ONLY cold start failed; CS_ONLY selected

500 ms added wait with original CS/SPI order still returned CMD0 failed: 31, CARD_INIT, elapsed 625 ms. First-boot evidence captured before reset/reinit. Switched temporary Pico entry to CS_ONLY (0 ms added wait; GP17 High before SPI creation). CS_ONLY cold-power result pending. See [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: CS_ONLY cold start failed; combined condition selected

CS High before SPI creation with no added wait returned CMD0 failed: 31, CARD_INIT, elapsed 126 ms. Captured before reset/reinit. Temporary Pico entry now selects DELAY_AND_CS (500 ms wait, then CS High, then SPI creation). Combined cold-power result pending. No runtime logic change or Host test rerun for this case selection. See [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: SD startup comparison completed without improvement

DELAY_AND_CS cold start: CMD0 failed: 31, CARD_INIT, elapsed 627 ms; captured before reset/reinit. Baseline, delay-only, CS-only and combined cases all exhibited the same CMD0 failure. Tested 500 ms wait and CS-before-SPI are not established fixes. Restored normal firmware/main.py to Pico /main.py, retaining diagnostic support. Root cause remains open. No Host tests rerun for hardware measurement and entry restoration; last suite 139 passed. See [full evidence](SD_Startup_Investigation.md).


## 2026-09-10: Chat CMD0 diagnostic handoff validated

Corrected pre-mount diagnostic contamination: preserve first baseline mount failure, then probe only an unmounted CMD0 failure, without auto-remount. Bounded repeated-CMD0 method; actual regression tests replace synthetic assertions. Host/Mock 143 passed; Pico warm CMD0 10/10 idle responses, SD remount and existing 65-line CSV readback passed. Temporary diagnostic boot deployed for cold-power evidence; root cause unresolved. See [handoff validation](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: Verification-method handoff

Updated verify_sd_diagnostics.py to execute diagnostic regressions; aligned instructions to current 400 kHz baseline. Added simulated SPI constructor/command coverage for idle clocks, exact CMD0 frame, error preservation and timeout. Diagnostic 5 passed; full Host/Mock 144 passed. No Pico/runtime changes; see [verification handoff](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: CMD0_NO_PRE_FF hardware comparison prepared

Temporary Pico /main.py selects CMD0_NO_PRE_FF: only CMD0's CS-Low pre-command
FF byte is omitted. Other commands retain it. Initialization remains 400 kHz,
mode 0, 16 FF bytes with CS High, zero added wait and original CS/SPI ordering.
The driver default CMD0_PRE_DUMMY=True preserves normal behavior; only the
diagnostic entry overrides it. Startup snapshot includes cmd0_pre_dummy=False.
Post-failure probing still preserves the initial result; its CMD0 commands also
use this setting. No automatic remount or production workaround was added.

Host/Mock: 144 passed, with first-CMD0 byte sequence and failure/timeout checks
covering both pre-FF settings. Pico warm runtime smoke passed: RTC advancing,
64 CSV rows at /sd/BANK_A/20260910_114306.csv, zero drops, remount/readback,
RAM ATE CRLF and FU rejection, run/stop and zero observed NF55G TX bytes.
Evidence: temp/pico_no_ff_runtime_smoke.log and temp/pico_no_ff_warm_boot.log.
Cold-power result pending operator power-cycle; no claim of root-cause repair.
Earlier statements that this comparison was unimplemented are historical.


## 2026-09-10: RETRY_ONLY comparison prepared

Temporary diagnostic entry retains the SDCard object whose constructor failed,
via ObservedSDCard, and records the original mount error before follow-up.
PROBE_MODE=RETRY_ONLY issues one CMD0 on that same object/SPI: no SPI constructor
or init, no additional 128-clock train and no explicit retry delay. Ordinary
cmd() CS transitions and post-response FF clocks remain; "no extra clocks" does
not mean zero clocks between commands. SPI is deinitialized only after the probe.
CASE remains CMD0_NO_PRE_FF to keep the preceding trial's command bytes unchanged.
The baseline of this comparison is that preceding trial, not the original driver.

If first mount succeeds or no retained object exists, probing is skipped. No
automatic remount follows a failure. First evidence is not overwritten by a
successful follow-up. All additional probing is diagnostic, not production retry.

Host/Mock: 146 passed. New checks enforce retained-object reuse, exactly one
attempt, zero requested delay and no fallback reconstruction when object missing.
Pico warm test injected a software CMD0 error after a real 0x01 reply, confirmed
constructor-failure object retention, then obtained 0x01 from one same-SPI retry.
SD remount and existing 65-line CSV readback passed. This injected failure is NOT
a reproduced cold-power failure and does not establish a fix.
Evidence: temp/pico_retry_only_warm_injection.log; reproducible script:
scripts/pico_cmd0_retry_only_smoke.py. Warm boot evidence:
temp/pico_retry_only_warm_boot.log.

Pico /main.py and /sd_cmd0_probe.py contain the updated diagnostic module.
The next operator power-cycle must be captured before host reset/reinit; inspect
startup_sd_diagnostic and REPL global diagnostic_report, including probe_mode,
mode, attempts and results. Cold result pending; root cause remains unresolved.


## 2026-09-10: CLOCKS_ONLY comparison prepared

PROBE_MODE=CLOCKS_ONLY retains the failed card/SPI, drives CS High and writes
16 FF bytes (128 clocks), then sends one CMD0 with zero explicit delay. No SPI
constructor/init occurs before that retry; deinit is cleanup after the result.
CASE remains CMD0_NO_PRE_FF, matching RETRY_ONLY. Report includes mode, attempts,
delay_ms and extra_idle_bytes=16. First failure is retained without automatic remount.

Host/Mock: 147 passed. New test verifies CS High during all 16 writes, same SPI,
no reconstruction factory, then exactly one retry and cleanup. The warm Pico
smoke uses injected failure; cold-power evidence still requires a physical cycle.
Evidence paths: temp/pico_clocks_only_warm_injection.log and
temp/pico_clocks_only_warm_boot.log. No permanent workaround has been selected.


## 2026-09-10: Pico CLOCKS_ONLY verification record

Recorded COM14 preserved startup evidence (initial CMD0=31; follow-up=0x7F)
in Real_Hardware_Test_Log.md and SD_Startup_Investigation.md. This was a re-read,
not a new physical cold-start trial. Host/Mock 147 passed; firmware unchanged;
root cause remains open. Device left at friendly REPL.


## 2026-09-10: CLOCKS_ONLY physical power-cycle evidence

Recorded operator-confirmed power-cycle trial at 15:20 JST: initial CMD0=31,
retained-SPI follow-up after 128 clocks=0x7F, SD unmounted. Failure reproduced;
root cause remains open. Evidence and device REPL state recorded in hardware
log and SD investigation. No firmware changes; last Host/Mock run 147 passed.


## 2026-09-10: Deploy chat SD changes; Phase 1 passed

Deployed and byte-verified 24 files on Pico 2, with prior Python files backed up.
Host/Mock 147 passed; basic CMD0 at measured 100 kHz returned 0x01.
Phase 2 cold power cycle, Phase 3 five CASE cold trials and optional Phase 4
physical measurement remain pending. See Real_Hardware_Test_Log.md.


## 2026-09-10: Phase 2 cold mount succeeded; Phase 3 BASELINE ready

100 kHz / PULL_UP cold boot returned mounted=True, READY, OK, elapsed_ms=305.
Additional CMD0 probe skipped for mounted filesystem. Recorded first evidence;
deployed and byte-verified BASELINE variant for next physical power cycle.
No root-cause conclusion or Open Issue closure. See hardware test log.


## 2026-09-10: Phase 3 BASELINE cold mount passed

BASELINE cold boot: mounted=True, READY, OK, 304 ms. Initial evidence recorded;
follow-up CMD0 skipped. DELAY_ONLY entry deployed and byte-verified for trial 2/5.
No application source changes or Open Issue closure. See hardware test log.


## 2026-09-10: Phase 3 DELAY_ONLY cold mount passed

DELAY_ONLY cold boot: mounted=True, READY, OK, 806 ms including 500 ms wait.
Initial evidence recorded; follow-up CMD0 skipped. CS_ONLY entry deployed and
byte-verified for trial 3/5. No source change or Open Issue closure.


## 2026-09-10: Phase 3 CS_ONLY cold mount passed

CS_ONLY cold boot: mounted=True, READY, OK, 307 ms. Initial evidence recorded;
follow-up CMD0 skipped. DELAY_AND_CS entry deployed and byte-verified for trial
4/5. No application source change or Open Issue closure.


## 2026-09-10: Phase 3 DELAY_AND_CS cold mount passed

DELAY_AND_CS cold boot: mounted=True, READY, OK, 810 ms including 500 ms wait.
Initial evidence recorded; follow-up CMD0 skipped. CMD0_NO_PRE_FF entry deployed
and byte-verified for trial 5/5. No source change or Open Issue closure.


## 2026-09-10: Five-CASE cold-boot series completed

Final CMD0_NO_PRE_FF trial mounted successfully in 305 ms. All five CASEs
returned OK/READY with 100 kHz initialization and MISO PULL_UP. Recorded
evidence-backed comparison; no unique optimum or root cause established.
Optional physical MISO measurement remains unperformed. Diagnostic entry
retained; Pico at REPL with ATE loop stopped. Last Host/Mock: 147 passed.


## 2026-09-10: Restore normal baseline per user decision

Restored and byte-verified firmware/main.py as Pico /main.py; retained SD
100 kHz initialization and MISO PULL_UP, with no wait, original CS order,
and CMD0 pre-FF enabled. Normal warm mount check passed (333 ms), Host/Mock
147 passed. Left normal firmware running. Requested task complete; optional
voltage measurement unperformed, clock-only root cause not established.


## 2026-09-10: User omits MISO voltage measurement

Optional Phase 4 omitted by user decision. Recorded next step: physical ATE
UART integration on final firmware, followed by T9 entry review and D1/D5
product communication tests. No firmware changes or tests executed.


## 2026-09-17: Physical ATE UART0 verification on COM5

Recorded ID/RTC/SD/FW_UPDATE-rejection, split CRLF and 20/20 repeated ID
responses over Elecom RS232 at 115200 8N1. Initial ERR:ASCII preserved as an
unresolved observation; subsequent checks passed. No firmware changes or
NF55G product transactions; normal runtime left running.


## 2026-09-17: NF55G preconnection review

Recorded UART1 loopback removal and NF55G disconnection confirmed by operator.
Checked port availability and harness reference; physical wiring/power evidence
remains pending. No product communication or readiness approval.


## 2026-09-17: Operator wiring and power inspection recorded

Recorded GP4/GP5 isolation, correct CN24 wiring, harness/path checks and all-OFF
state as operator reports. Target FW remains unknown; detailed isolation,
battery state, shutdown method and individual identification remain pending.
No product communication or Open Issue closure.


## 2026-09-17: Sample 1 preconnection details

Recorded operator-provided SD-board GP4/GP5 removal/soldering method, battery
disconnected and test ID Sample 1. FW unknown; power shutdown method still
awaiting confirmation. No hardware operations or Open Issue closure.


## 2026-09-17: Power shutdown method recorded

Operator confirmed NF54G AC-DC / NF55G DC-DC configuration and NF54G AC switch
OFF as shutdown operation, with battery disconnected. Completed outstanding
physical-check response record; no product communication or power operation.


## 2026-09-17: T9 entry verification

Host/Mock 147 passed; 23 deployed Python files SHA256 matched. Integrated
RTC/SD/readback/FU rejection and software NF55 TX count=0 passed. Restored
normal runtime and verified physical COM5 local responses. Recorded scoped
Sample 1 D1/D5 entry readiness; no product transaction or Open Issue closure.

- 長押し起動の追加調査: メーカー作成第5版p.22に強制起動中はホストへ読取データを出力しない旨を確認。試験手順・実機ログ・OI-23へ追記。通常起動で再試験する。

## 2026-10-11 HID-UART置換実験の共通TEST準備

- CH9350/README.mdへDesktop原本を複製しSHA256一致を確認。資料原本は変更なし。
- CH9350/src/ch9350_capture.pyに受信器を外部から渡す時刻付きHEX表示を追加。importでGPIO初期化なし、TX送信なし、終了時解放、受信器の欠落情報をLOSSで明示。
- 共通受信ログのHost試験5件成功、既存Host/Mock 161件成功、mpremote起動確認成功。
- CH9350/docs/に手順と新基板の未実施評価表を追加。型番CH9359/CH9350の不一致とGP4/GP5 UART1競合等をOpen Issuesへ追加。
- IC依存のデコーダ・UART初期化とPico配置/実機評価は型番確認待ち。既存NF55G/ATE/QRソースとPico main.py/boot.pyは変更なし。

## 2026-10-11 CH9350確定・QR試験ポート割当て

- ユーザー訂正により対象ICをCH9350と確定。CH9350状態2/3/4の11byteキーボードフレームについて、分割/連結受信、押下/解放差分、Shift、US英数字・記号・Enter、不正/未完フレーム拒否を実装。
- NF55G用GP4/GP5を保持し、CH9350試験をGP9=PIO0/SM0受信115200bps/8N1、GP8=送信禁止High固定へ割当て。ハードUART1を使用しないため、NF55G UART設定は変更しない。
- HEXログ再生ツールと合成ログを追加。正式Cache、SS連携、製品PASS/FAIL、本番runtimeへの統合は対象外。
- 販売基板のTX電圧、DIP対応、電源容量、RX接続条件、115200bps実受信は未確認。既存NF55G/ATE/QR runtimeとPico main.py/boot.pyは変更なし。

## 2026-10-11 CH9350 DIP設定管理の追加

- 評価基本ProfileをEVAL-CH9350-STATE2（SEL=H、S1=H、S0=L、BAUD1=H、BAUD0=H、115200bps/8N1）として記録。
- 量産候補Profileを同じ論理のPROD-CH9350-STATE2として分離し、実機評価合格までは未承認と明記。状態0は互換性比較用で、状態2の試験結果と混在させない。
- 販売基板のDIP番号・ON/OFFとIC論理の対応は未確認のため、現物の導通・電圧測定欄、評価記録、量産固定記録を追加。DIP変更は電源OFFで行い、再投入後に確認する手順とした。
- 評価基板の詳細資料がなく、販売ホームページの記載を基にユーザーが提供した基板情報であることを追記。ホームページ画面・記載日時・DIP設定表原文は未保存とし、ICデータシート確認事項および現物測定結果と区別した。

2026-11-09 実機前レビュー: ATE transportで拒否したASCII／FRAME／LINE_TOO_LONGも、試験中はRECEIVE_ERRORとしてRAM記録する。保存できるのは受信層が保持したprefixであり、入力全体のRAW取得とは扱わない。Host／Mock回帰試験を追加。

2026-11-09 実機確認: 日時ログ、SD抜去時のWRITE_ERR・試験継続、再挿入中の復帰禁止、TEST_END後の復帰と異常履歴保持、次試験のログ再開を確認。D3正常（31ms・再送0）、D4はD4-TIM-01として継続。TEST_ENDの先行OKをEND_REQUESTに修正し、期限境界の部分RAW／ACK待ち異常byteも記録。Host／Mock全198件成功。詳細はReal_Hardware_Test_Log.md。

2026-11-09: D4量産不使用をユーザー指定として記録。r1 p.35に基づきCLEAR4種をParser／Builderへ接続し、CD／CL正常応答DATA0文字を検証。Host／Mockでは送信形式、T2、成功／ambiguous時のCache無効化、SQE、不正引数の無送信、異常応答へのplain NAKを試験する。実機結果はReal_Hardware_Test_Log.mdへ記録。

2026-11-09 CLEAR実機結果: POWER／BATT／ALL／LOGの4種がOK、19／19／20／19ms、再送0、BCC一致。CD後のDATA／STATUS無効化、CL後の全EL／OL無効化と96件の空ログ表現を確認。CLEAR_ALLは先行個別消去後の0維持を確認したもので、単独非ゼロ値消去は未検証。Host／Mock全203件合格。詳細・制限はReal_Hardware_Test_Log.md。
