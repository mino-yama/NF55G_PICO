# Real Hardware Test Log

## 2026-11-14 実ATE・実NF55G総合テスト／終端CR統一による未受信解決

- ユーザー報告: 実ATEと実NF55Gを組み合わせて本日総合テストを実施。前日発生した「ATEへ値が返らない」問題は終端コードの相違が原因と判明し、CR（0x0D）へ統一して解決した。
- 関連原本: [20261114_092525_T000019.csv](F:/BANK_A/20261114_092525_T000019.csv)。原本は変更していない。ファイル先頭のtrial_id=T000019、TEST_START受付・論理OKを確認した。全行解析・ATE側受信rawの照合は今回実施していない。
- 確認範囲: 未受信の原因・解決はユーザーの実機確認に基づく。CSVのATE/TX/RESULTだけを物理送信完了・ATE受信の根拠にしない。総合テスト全項目の合否、初回ASCII異常、TEST_END後の遅延・遅着対応は今回の報告から推測しない。
- ATE-TX-01へ解決範囲と残課題を追記。コード・設定・実機配置は変更せず、Host／Mockは再実行していない。

2026-11-13以前のコミット済み記録は[変更前の履歴](history/Real_Hardware_Test_Log_Before_20261113.md)に保存。現在の記録と併せて参照する。

## 2026-11-13 入替えPico COM6／69f7d45962cfdfadを最新化

- ユーザー指定の元ATE用個体をID照合し、旧26ファイル退避・hash確認後に現行一式を配置。ate_server.py／ate_uart.py／config.py／src main.py／repl_sink.pyの5件が更新。26 Pythonのhash一致・実機compile成功、Host／Mock315件成功。
- 2秒timeout条件の初回実機は13/15。TEST_END直後に遅着を観測したため、10秒待ちで再確認し15/15成功。LOG_DROP_COUNT?=0は3201.859ms、SD／自己診断OK・drop0・REPL実出力確認・NF55G送信0byte。通常main.py再起動後7件成功。57600／8N1・CR・REPL ONで通常待受中。
- 終了直後3.20秒遅延と起動後初回914msは原因未確定で残件。ATE／PIA5100／GPIB実経路は未確認。[個体別配置記録・退避先](Pico_Swap_69f7d459_Update_20261113_Rev0.txt)。


## 2026-11-13 最新FW再配置・全件一致確認

- ユーザー依頼でCOM14／Pico ID `2d35a1e11ac125e3`の旧27ファイルを退避・hash照合後、現行src25 Python＋root main.pyの配置処理を実施。全26件が既に最新版と一致しておりUp to date、内容差分なし。再照合・実機compileも全件成功。
- Host／Mock315件成功、通常main.py再起動後のPC直結7件成功。57600／8N1・応答CR・REPL ONで通常待受中。初回ASCII異常・ATE／GPIB経路は未解決のまま。[確認記録](Pico_Latest_Update_20261113_Rev0.txt)。


## 2026-11-13 初回IDN ASCII異常の追加確認・PC設定復元

- クレジット追加後の再試験で、Host先行7F／FFは初回ERR:ASCII→次回正常を再現。実機RAMでUART受信前段を4条件・8件観測したが全件正常、不正byteなし。初期化直後要求は約1.04～1.05秒後に応答し、起動待ちを確認したがASCII異常の原因とは断定しない。
- 意図しないPC側config欠落をユーザー承認でCR／REPL ONへ復元。旧固定OFFテストもON／OFF直接検証へ復元しHost／Mock315件成功。実機FWファイルは変更せず、通常起動後7件成功、57600／8N1・CR・REPL ONで待受中。
- 実機の初回ASCII異常は今回未再現、原因未確定。物理電源再投入・普段のPCソフトでの再現時rawが残件。[追加確認記録](Startup_First_IDN_ASCII_20261113_Rev1.txt)。


## 2026-11-13 REPLログ既定OFFのconfig.py転送

- 対象はCOM14／Pico ID `2d35a1e11ac125e3`、ATEはCOM19。ATE `COMM_STATUS?`は事前にIDLEを応答したため、`src/config.py`のみを`/src/config.py`へ配置。他ファイルは変更していない。
- PC／Pico SHA-256一致: `dbb30eb3e08d4b9b94c095cdf66929d781e5cbf93997710a921c2dbadc404ff1`。Pico上で`REPL_LOG_ENABLED=False`、`ATE_BAUDRATE=57600`をimport読戻し確認。
- 転送後、現行のATE通信速度設定が未確認のためMain再起動は実施していない。従来115200bpsでCOM19 `*IDN?`を1回確認したが無応答。これは新設定57600bpsでMainを起動した確認ではなく、原因も未確定。ATE装置側を57600bpsへ設定・確認後、通常Main再起動とATE IDNを確認するまでATE通信／REPLミラーの運転確認は保留。

## 2026-11-13 ATE UART baudrate変更（ソース未配置）

- ユーザー指定によりATE UART0のbaudrate設定を115200から57600bpsへ変更し、`src/config.py`／`src/ate_uart.py`とUART初期化テストを更新。Host/Mock 309件成功。
- NF55G UART1=38400bps／8E1は変更していない。ATE側装置・GPIB側のbaudrate設定が57600bpsへ変更済みかは未確認。今回の変更ソースはPicoへ未配置で、COM14／COM19で新設定のloopback・応答確認も未実施。相手側を同値へ設定・確認するまでATE物理試験を開始しない。

## 2026-11-13 開発Pico入替え・最新MicroPython FW配置

- ユーザー指示: 以前デバッグに使用した開発Pico 2へ最新FWを配置。旧FWのバックアップは不要との指定のため、配置前ファイル退避は行わない。
- Windows COM14（USB CDC、VID/PID 2E8A:0005）を使用。REPLから読んだ`machine.unique_id()`は`2d35a1e11ac125e3`で、過去に開発用Picoとして記録された個体と一致。ATEはCOM19を使用。
- 旧`/src`を削除後、現行`src/`の25 Python modulesと`.gitkeep`を転送し、ルート`/main.py`を現行`firmware/main.py`へ配置。`/main.py`はmpremoteが`Up to date`と判定。Pico側hashはmain=`b0b2a60bdabebe7f7f576039755b6e135be3731f9a2470d991b95ca540a21b93`、src/main=`3ba7117e4a7cb626cea0e3d61320ed46aa99968a31956d6c5b1341d0bd39707a`、logger=`4898bcfde0568ecc7a38ab0eab8288b949fff296bd6b497badc57793ef6a90dd`、repl_sink=`7570da47e5fe8c9bd1be99a052ac7f9fa8d7cab06c86fcad3c8845ad62ac750b`、ate_uart=`b2ee951103d8f0b95d785a39e78a32c97457d0858f134d92c86f62f02d2825f6`、nf55_uart=`1aa7ece4beef1dae726b31ff000d0ad05680a6857732ebd9f0eee024b86f0b6b`。各hashはPC側対象ファイルと一致。Pico MicroPython上で`/src`内25 Python modulesすべてcompile成功。
- mpremoteから`firmware/main.py`を実行し常駐プロセスを起動。起動時にPython tracebackは確認されず、起動入口`/main.py`は変更していない。
- 初回はCOM19 `*IDN?`無応答。その後ユーザーがCOM19接続を報告した後の照会では`NF55G_PICO_FIXTURE,Rev.0`が応答。`COMM_STATUS?`=IDLE、`SD_STATUS?`=OK、drop0、Self CheckのATE_UART／NF55_UART／RTC／LOGGERが全てOK。
- ローカルのみの試行T000001: `TEST_START`=OK（150.69ms）、`RTC_CHECK?`=OK（27.76ms）、`*IDN?`=NF55G_PICO_FIXTURE,Rev.0（8.67ms）、`COMM_STATUS?`=IDLE（9.40ms）、`TEST_END`=OK（197.98ms）。終了Self CheckはTEST_LOGGER／TEST_LOG_DROPともOK、SD OK、drop0。NF55G Refresh／Control／FUは送信していない。
- TEST_END直後の`PICO_SELF_CHECK?`に742.86msを観測。続く待受時に同Queryを3回測定すると57.01／58.26／58.64ms、COMM_STATUS=IDLE、SD OK、drop0。直後値の原因は未確定であり、REPL排出またはSD flushへの因果を断定しない。ATE応答遅延の一時外れ値として残す。
- 今回NF55G本体は未接続。配置・起動とローカルLogger／REPL経路の確認であり、NF55G接続時の実機HIL／Transaction Timingは残件。旧root debug scripts（pico_qr_receive_test.py等）は残置し、現行`/main.py`からは起動しない。SD `/sd`領域の直接一覧・CSV独立読戻しは未実施。

## 2026-11-13 REPL/debugログ確認の実機前疎通

- 目的: 2026-11-13追加のREPL/debug sinkを配置する前に、既知のATE経路と通常待受を確認する。COM列挙だけで個体・機能の一致を断定しない。
- Windows列挙ではCOM6がUSB CDC（VID/PID 2E8A:0005、PnP status OK）。既存資料の治具Pico候補と一致するが、この場ではCOM6を開かず固有IDを再読していない。従来ATEポートCOM20はPnP status Unknownで、SerialPort.Openも「ポートが存在しません」で失敗。
- ユーザーがElecom変換器のCOM19をATE接続と現物確認。115200bps／8N1、DTR/RTS無効で`*IDN?\r\n`を1回送信したが、2秒で応答timeout。自動再送・別ポートへの送信はしていない。
- 結果: Pico個体ID／ATE ID応答／COMM_STATUS／SD状態は未確認。ATE待受またはポート対応の原因を特定できないため、以後のATEコマンドを停止した。COM6を開く・REPL割込み、ファイル配置、再起動、TEST_START、製品Refresh／Control、NF55G向け指令は未実施。REPL出力動作も未確認。
- 次段階はCOM19のATE信号経路とCOM6の治具Pico個体・通常起動状態を再照合し、ATE `*IDN?`応答が正常化してから非破壊の状態確認と配置手順へ進む。無応答の原因をポート間違い・FW停止等と決めつけず、再送やRESETで復帰させない。

2026-11-13再試行: Thonny終了後、COM6／COM19はWindows PnP status=OK。COM20はUnknownのまま。COM19がATE接続であることをユーザーが確認。COM19、115200bps／8N1、DTR/RTS無効で`*IDN?\r\n`を1回送信したが、2秒後の応答は空。自動再送・別コマンド送信なし。COM6を開く・固有ID取得・REPL割込み・ファイル退避／配置・Main起動・製品指令は未実施。ATE ID照合不成立のため、前述の識別・転送条件は未達。配線経路・ATE稼働状態・Pico通常起動状態は依然未確認であり、原因を断定しない。

## 2026-11-13 REPL/debug CSVミラー実機確認

- COM6でPico `unique_id=69f7d45962cfdfad`を読み、対象治具Picoと一致。通常アプリ停止状態で既存`/main.py`、`/src/main.py`、`/src/logger.py`をPCの`temp/pico_repl_mirror_before_20261113/`へ退避。
- `/src/main.py`、`/src/logger.py`、新規`/src/repl_sink.py`だけを配置。Pico側／PC側SHA-256一致: main.py=`3ba7117e4a7cb626cea0e3d61320ed46aa99968a31956d6c5b1341d0bd39707a`、logger.py=`4898bcfde0568ecc7a38ab0eab8288b949fff296bd6b497badc57793ef6a90dd`、repl_sink.py=`7570da47e5fe8c9bd1be99a052ac7f9fa8d7cab06c86fcad3c8845ad62ac750b`。MicroPython上の3ファイルcompile成功。起動入口`/main.py`は変更していない。
- `ReplDebugSink`単体を実機stdoutで確認。CSV headerと`REPL_MIRROR_PROBE`行が表示され、enabled=True、pending=0、drop=0。
- COM6上で通常`firmware/main.py`を起動し、出力監視はmpremoteを使用。COM19、115200bps／8N1から`*IDN?`=`NF55G_PICO_FIXTURE,Rev.0`。`COMM_STATUS?`=IDLE、`SD_STATUS?`=OK、初期`PICO_SELF_CHECK?`=ATE_UART/NF55_UART/RTC/LOGGERすべてOK、`LOG_DROP_COUNT?`=0。
- ATE `TEST_START`→`RTC_CHECK?`→`COMM_STATUS?`→`TEST_END`を各応答後150ms以上空けて実行。全応答OK。終了Self Checkは`TEST_LOGGER=OK;TEST_LOG_DROP=OK`、SD OK、drop0。Logger試行ID T000007。
- mpremoteのCOM6監視出力にCSV header、T000007の`TRIAL_START`、上記ATE REQUEST/RESULT、SELF_CHECK、`TRIAL_END_REQUEST`が表示された。NF55G Refresh／Control、設定変更、FUは送信していない。従って確認範囲はローカルATE処理とSD Logger行のREPLミラーであり、NF55G通信中の実機Timingではない。Thonny固有の表示試験も未実施。
- TEST終了後もMain監視を継続中でCOM6はmpremoteが占有しているため、SDファイル一覧を直接再読していない。保存成立はTEST_LOGGERとSD診断で確認。次回REPLを開く前に監視プロセスを停止し、通常アプリ再起動を確認する。

Thonny確認追記（ユーザー実機確認）: mpremoteを終了した後、ThonnyからCOM6へ接続。Shellに`MPY: soft reboot`を確認し、Main起動後の出力を監視した。ATE COM19から`TEST_START`、続けて`*IDN?`を実行し、提示されたShell出力にT000010のTRIAL_START、ATE TEST_START REQUEST／RESULT=OK、`*IDN?` REQUEST／RESULT=`NF55G_PICO_FIXTURE,Rev.0`が表示された。ユーザー報告によりThonny経由の表示確認を合格とする。追加の製品コマンドは未実施。soft rebootは実行中アプリを再起動するため、次回はTEST_END／IDLE確認後に行う。今回提示された抜粋には試行終了後のSelf Check／CSV独立読戻しは含まれない。

## 2026-11-13 TEST_START有無によるATEローカル処理時間比較

- 対象COM19、115200bps／8N1、各要求CRLF、要求間隔150ms。TEST_STARTなし／ありの各条件で`RTC_CHECK?`、`COMM_STATUS?`、`SD_STATUS?`を各6回実施。製品設定／制御コマンドは送っていない。
- TEST_STARTなし: RTC_CHECK?中央値28.40ms・最大29.38ms、COMM_STATUS?中央値9.47ms・最大11.00ms、SD_STATUS?中央値7.87ms・最大9.51ms。全応答正常。
- TEST_STARTあり: TEST_START=213.92ms、TEST_END=208.48ms。RTC_CHECK?中央値28.37ms・最大75.84ms、COMM_STATUS?中央値9.25ms・最大10.17ms、SD_STATUS?中央値8.34ms・最大9.35ms。全応答正常、終了診断OK、SD OK、drop0。
- 単発ではTEST_START=196.48ms、TEST_END=190.15ms。TEST_END直後のPICO_SELF_CHECK?に462.27msを観測したが、その後の待受状態で同Queryは57.26～59.13ms。背景保存との関係は分離測定しておらず、462msの原因は未確定。ほかの単発ローカルQueryはRTC_CHECK?=27.37ms、COMM_STATUS?=10.30ms、SD_STATUS?=7.32ms。
- ユーザー確認: 今回はNF55G本体を接続していない。TEST_STARTなしのSTATUS_REFRESH要求に対してPicoがD1 Transactionを試み、`ERR:ACK_TIMEOUT`、418.41ms、後続RETRY_COUNT?=`OK:cmd=1,rsp=0`を観測した。これは未接続時の応答であり、NF55G接続下のD1動作・通信性能を評価する結果ではない。再試行せず、INFO_REFRESH／D0等の後続NF55G Transactionは中止した。
- 最終状態はCOMM_STATUS=IDLE、SD OK、Self Check OK、LOG_DROP_COUNT=0、RETRY_COUNT=`cmd=1,rsp=0`。Logger開始有無でローカルQueryの大幅な定常遅延は観測しなかったが、PICO_SELF_CHECK?の一時遅延とRTC_CHECK?の単発外れ値は残る。NF55G接続時のRefresh／Transaction Timing、量産周期／負荷、Thonny Shellでの今回の反復ログ完全性は未確認。製品設定変更なし。NF55G接続状態での実機HILは残件。

## 2026-11-13 提供ATE CSVの応答配送・ACK_TIMEOUT調査

- ユーザー提供のT000053／T000054／T000055 CSVと`src/main.py`／`src/ate_server.py`を照合。`ATE,TX,RESULT`は応答生成時に記録され、UARTへの`reply`／`flush_reply`より前であるため、ATE物理送信・受信の証拠ではない。現行ATE CSVにはATE TX raw byte／UART.write受理長／残送量／flush完了がない。ユーザーがATE側で結果未受信と観測した事象は、CSVだけから成否判定できない。
- T000053のERP_SET_1_0／ERP_SET_0_0は`ERR:ACK_TIMEOUT`、cmd_retry=1、rsp_retry=0、ambiguous=True。再試行後または終了直後にSE応答フレームらしい受信行が複数あり、Transactionとの対応と設定適用の有無は未確定。後続のDATA_REFRESH／VOUT12?成功はその時点のDATA読取りを示すが、ERP設定値の復元確認ではない。状態が明示読戻しされるまでControl再送を行わない。
- T000053の`CLOCK_SYNC 20261109120000`は14桁でparser拒否。ユーザー申告どおり入力修正後、T000054／T000055には`CLOCK_SYNC 261109120000`の12桁入力とSC=OKを記録。T000053の拒否履歴を修正後結果で上書きしない。
- T000054／T000055にはSC／D0のNF55G raw応答とTransaction OKが記録される一方、ATE/TX RESULTは依然として物理出力証跡ではない。これらのログとATE側未受信観測の時刻対応・受信raw dataが揃っておらず、ATE送信の欠落箇所は未特定。
- 過去にはCOM19で`*IDN?`やローカルQueryの応答を実受信した記録があり、ATE timeoutも候補となる。長時間処理を含むATEコマンドの応答待ち時間が処理完了前に満了した可能性はあるが、今回のATE timeout設定・timeout時刻・遅着受信は未取得で原因確定していない。
- 次の調査はATE timeout設定と問題になったコマンド／送信時刻／timeout時刻を確認し、ローカル応答とNF55G Transactionを区別して実施する。Pico側UART送信記録・ATE側受信raw bytes・必要時の線上観測を同時突合する。NF55G設定Controlは再送しない。詳細は[Open Issues ATE-TX-01](Open_Issues.md)を参照。コード・テストは未変更。

## 2026-11-13 COM19 *IDN? 応答時間単発確認

- COM19をPCから直接115200bps／8N1で開き、DTR/RTS無効、受信前buffer空を確認後、`*IDN?\r\n`を1回送信。受信窓15秒に対し約219msで`NF55G_PICO_FIXTURE,Rev.0\r\n`を完全受信（RX HEX=`4e463535475f5049434f5f464958545552452c5265762e300d0a`）。自動再送なし。
- これはCOM19直結のPC単発試験であり、実ATEアプリからGPIBを介したtimeout・中継・遅着応答処理は測定していない。1標本のため応答時間保証やATE未受信原因の特定には使わない。Main側mpremote監視は稼働継続、製品コマンドは送信していない。ATE-TX-01はOpen継続。

## 2026-11-13 COM19 baudrate比較再試験

- COM19直結でDTR/RTS無効、各回CRLF・先行受信buffer clearとして、同一`*IDN?`を57600bpsと115200bpsで各1回送信。57600では3秒受信なし。続く115200では約263.54ms後に`ERR:ASCII\r\n`（RX HEX=`4552523a41534349490d0a`）で、期待IDNとは不一致。送信byte列は各回`2a49444e3f0d0a`。
- UART baud／framing／物理経路不整合を疑う観測だが、片道の不一致・遅着byteの対応は未確定。ATEアプリ/GPIBを介した試験でもなく、成功baudを確定しない。追加送信・NF55G製品コマンドなし。Main監視は維持。ATE-TX-01 Open継続。

## 2026-11-13 ATE→PIA5100経路の切り分け情報

- ユーザー観測: NF55G側UART1でオシロスコープ波形を確認。過去作成のRB01Gでは問題なし、PC serial通信でも問題なし。一方、ATE接続ではPico→PIA5100→ATE間の受信ができていないとのこと。
- UART1（NF55G側GP4/GP5）の波形はUART0（ATE側GP0/GP1）の信号を観測したものではない。RB01GとPC serialの機種・baudrate・配線・試験点の詳細は未提示のため、これらの成功条件をPIA5100/GPIB経路へ同一視しない。
- ATE用コード設定は57600bps／8N1へ変更済みだが、Pico上config.pyは転送したのみでMainの再起動確認は未実施。UART peripheralが以前の設定で動作中か、停止中かは未確認。PIA5100／ATE側のbaudrate・parity・stop bit・flow control・GPIB宛先／timeoutも未照合。
- 次回は全機器を同一設定（UART0 57600bps／8N1、終端CRLF）にそろえ、Mainを再起動後、ATE/GPIB→PIA5100→Pico UART0 RXと逆方向のPico UART0 TX→PIA5100→GPIB→ATEを個別に観測する。最初はローカル`*IDN?`のみを1回送り、Pico GP0/UART0 TX、PIA5100 RS232側、ATE/GPIB応答・timeout時刻を同時計測する。NF55G本体コマンドは送信しない。
- 現時点ではPIA5100が原因とは確定しない。ATE-TX-01はOpen継続。

## 2026-11-11 D1～D5各10回の時間測定

- COM6／unique_id=69f7d45962cfdfad、ATE COM20、製品S1.13、PS_ON=1／BATT_ON=0。D1／D2／D3／D5は通常ATE経路で各10回OK・再送0。ACK後完全応答平均／最大は14.0／15、22.0／23、18.6／34、58.9／74ms。D2前に日本時間のSC1回を明示実行し、測定母数へ含めていない。
- D4は既知の再送競合を避け、製品用設定を変えずにRAMだけの単発送信・最長1000ms観測で10回取得。DATA212文字・BCC正常、再送0、CacheをVALIDにしない。CSV時刻でACK後平均116.0ms、最大133ms、最小113ms、現行100ms以内0／10。通常D4 Transactionの成功や製品FW単独の違反とは扱わない。
- T000005／6のCSVは25195／10841byte、全14列、送受信計102フレームBCC一致、256byte分割回収・SD／PC SHA-256一致。別計算でも50標本の平均・最大が一致。試験終了時保存診断正常・破棄0、回収後通常待受・IDLE・SD正常を確認しCOM6／COM20解放済み。
- D3／D4の消去副作用を伴う測定。SL／その他SET・CLEAR・SS／FU、電源・負荷・バッテリ操作は行っていない。製品ソース・T2設定は変更なし。D4-TIM-01ほかOIはOpen継続。[結果・原本・スクリプト](Spec_Review_20261111/D1_D5_Timing_20261111_112941/Timing_Result_Rev0.md)。

## 2026-11-11 D0 T2 300msの配置と正常系10回

- COM6／unique_id=69f7d45962cfdfadの25ファイルを退避し、PCとの差分がconfig.pyだけであることを確認。config.pyのみ配置しSHA-256一致、読込済みD0 T2=300ms／期待327文字を確認した。Host／Mockは同日再実行287件成功済み。
- COM20／115200bps、製品FWはS1.13（末尾空白あり）、明示D1でPS_ON=1／BATT_ON=0。TEST_START→D1／D5→D0とDATA Queryを10回→TEST_END。D0全10回OK、ACK後完全応答180～182ms・平均180.8ms、Transaction194～195ms、cmd／rsp retry0、ambiguous=False。ソフトウェア時刻の実測であり、外部波形や製品PASS／FAILではない。
- T000004のCSV22229byte・201データ行は全14列、送受信24フレームBCC一致。256byte分割回収・SD／PC SHA-256一致。終了時TEST_LOGGER／DROP正常・破棄0・SD正常・IDLE、回収後も通常起動と診断正常を確認しCOM6／COM20を解放した。
- 開始時はATE ID応答なし。製品操作へ進まず、個体確認・退避・配置後の通常起動で応答復帰。初期無応答の原因は未確定。SC／SET／CLEAR／BC／SS／FU、負荷／電源操作は行っていない。量産全条件・実機異常系は未確認、OI-02はOpen継続。[実機結果・全証跡](Spec_Review_20261111/Hardware_D0_T2_300ms_Result_20261111.md)。

## 2026-11-11 再TEST_START修正版の配置・3試行ログ分離

- 事前に手順を提示後、COM6の治具IDを照合し、旧25ファイルを退避。logger／sd_sink／command_dispatcher／mainの4ファイルを配置してPC／Pico SHA-256一致を確認。その他srcの比較対象も配置前hash一致。Host／Mock284件成功。
- COM20でSTART→SC→D0→Query→10秒→再START→明示D0→Query→3回目START→明示D0→Query→ENDを実施。再STARTは両方OK（PC往復163.3／200.2ms）、直後の旧DATA QueryはCACHE_INVALID。SCとD0は再送0。
- T000001～3のCSV3本、前2本NEXT_TEST_START・最終TEST_END、各試行のTransactionと全行14列、全8フレームBCC、SD／PCのhash一致を確認。最終Self Check正常・TEST_LOGGER／DROP正常・累積破棄0・通信IDLE。通常待受復帰とCOM解放済み。
- QR／SS・SD異常系・量産Timing全般は未確認。TEST-SESSION-01はOpen継続。[詳細・配置台帳・CSV](Test_Interruption_20261111/Hardware_Deployment_Result_20261111.md)。

## 2026-11-09 ATE UART0 retest after cable correction

- Operator reported the cable had been corrected. pySerial enumerated COM19 as
  Elecom USB-Serial Converter (VID:PID 056E:5004); COM14 remained the Pico USB
  REPL. The Windows serial-port inventory did not list COM19, but pySerial did.
- Opened COM19 at 115200 bps, 8N1, no flow control; DTR/RTS disabled. No bytes
  were pending before the test.
- Sent one local `*IDN?` request, TX=`2A49444E3F0D0A`. No response bytes arrived
  within 2 seconds. Stopped immediately; RTC_CHECK?, SD_STATUS?, and FW_UPDATE
  were not sent.
- Result: physical ATE UART0 response NOT VERIFIED after cable correction.
  The cause is undetermined; cable routing, Pico runtime state, and UART0
  receive/transmit wiring remain to be checked. No NF55G refresh, control, or
  FU command was requested. NF55G UART1 wire activity was not independently
  monitored. Pico power/runtime state and product wiring state were not
  re-inspected during this test.
- A preceding Python invocation failed in PowerShell argument parsing before
  opening COM19; it transmitted no data. The successful COM19 open and single
  request above were performed with the PowerShell SerialPort API.
- No source or device files were changed. Host/Mock tests passed 161/161 in
  this session. No Open Issue was closed.

Next: confirm that Pico normal runtime is active and verify the adapter's
RS232 path to UART0 GP0/GP1 against the harness drawing before another request.
Keep the NF55G unpowered and do not send product commands during this check.

## 2026-11-07 ATE UART0 local retest after UART0/1 correction

- Operator reported UART0/1 wiring was corrected. pySerial enumerated COM19 as
  Elecom USB-Serial Converter (VID:PID 056E:5004); COM14 was the Pico USB REPL.
- COM19 settings: 115200 bps, 8N1, no flow control; DTR/RTS disabled. No bytes
  were pending before the test. Each request and response used CRLF.
- `*IDN?` -> `NF55G_PICO_FIXTURE,Rev.0` (TX `2A49444E3F0D0A`, RX
  `4E463535475F5049434F5F464958545552452C5265762E300D0A`): PASS.
- `RTC_CHECK?` -> `OK` (TX `5254435F434845434B3F0D0A`, RX `4F4B0D0A`): PASS.
- `SD_STATUS?` -> `OK` (TX `53445F5354415455533F0D0A`, RX `4F4B0D0A`): PASS.
- `FW_UPDATE` -> `ERR:FU_DISABLED` (TX `46575F5550444154450D0A`, RX
  `4552523A46555F44495341424C45440D0A`): PASS for local FU blocking.
- This verifies the COM19-to-Pico UART0 local request/response path for these
  commands. No NF55G read, control, SC, D0, D2, D3, D4, or FU command was requested;
  product behavior and electrical safety are not inferred from the communication
  result. NF55G UART1 wire activity was not independently monitored; no T9
  product communication or product PASS/FAIL assessment is claimed. Product D1/D5
  testing was not run in this step.
- No source/device files changed. The prior COM19 ATE UART0 test was not
  repeated. No Open Issue was closed.

## 2026-11-07 Sample 1 D1/D5 read-only communication smoke

- Operator confirmed the UART0/1 wiring correction. Operator-reported DUT state:
  Sample 1 connected and powered, load/output OFF, battery disconnected. COM19
  was used for ATE UART0 at 115200 bps, 8N1, no flow control, DTR/RTS disabled.
- Each ATE command was sent once with CRLF after confirming no pending RX bytes.
  All replies below were received with complete CRLF; no command was repeated.
- `STATUS_REFRESH` (D1): TX `5354415455535F524546524553480D0A`, RX
  `4F4B0D0A` (`OK`): PASS at ATE response level.
- `PS_ON?`: TX `50535F4F4E3F0D0A`, RX `310D0A` (`1`): cached STATUS query
  returned a value after D1.
- `INFO_REFRESH` (D5): TX `494E464F5F524546524553480D0A`, RX
  `4F4B0D0A` (`OK`): PASS at ATE response level.
- `FW_REV?`: TX `46575F5245563F0D0A`, RX `53312E3133200D0A` (`S1.13 ` with
  one trailing space before CRLF): cached INFO query returned a value after D5.
- No product control, SET/CLEAR, or FU command was sent. The ATE-side `OK` and
  cached values indicate successful command handling; this test did not capture
  NF55G UART raw frames, DATA length, BCC, ACK, retry counts, elapsed timing,
  or physical waveforms. Do not treat this smoke as product PASS/FAIL or
  as confirmation that FW S1.13 is compatible with r1.
- No Open Issue was closed. Preserve the trailing space in the observed FW_REV
  response; do not normalize it without specification direction.

### D1/D5 cache-query sweep

- After the D1 and D5 refreshes above, queried every STATUS and INFO cache field
  once through COM19. The first automated attempt generated an empty CRLF line;
  it was ignored by the ATE server and returned no bytes. The corrected list was
  validated before opening COM19: 61 commands, first `BURST_ON?`, last
  `FAN_WNG_THD?`. No individual query caused another Refresh.
- Result: STATUS 37/37 and INFO 26/26 returned a value with complete CRLF;
  no timeout or `ERR:` response. `PS_ON?` and `FW_REV?` were included from the
  preceding D1/D5 check. Individual cache queries use the cache-only dispatcher
  path; no NF55G command was requested.

| STATUS query | Response | INFO query | Response |
|---:|---|---|---|
| 1 | `NF55_DATE?` | `ERR:CACHE_INVALID` |  |
| 2 | `NF55_TIME?` | `ERR:CACHE_INVALID` |  |
| 3 | `NF55_DATETIME?` | `ERR:CACHE_INVALID` |  |
| 4 | `VOUT12?` | `ERR:CACHE_INVALID` |  |
| 5 | `IOUT12?` | `ERR:CACHE_INVALID` |  |
| 6 | `BATT_VOLT?` | `ERR:CACHE_INVALID` |  |
| 7 | `CHG_VOLT?` | `ERR:CACHE_INVALID` |  |
| 8 | `CHG_CURR?` | `ERR:CACHE_INVALID` |  |
| 9 | `BATT_CURR?` | `ERR:CACHE_INVALID` |  |
| 10 | `BATT_SOC_WH?` | `ERR:CACHE_INVALID` |  |
| 11 | `BATT_SOC_MAH?` | `ERR:CACHE_INVALID` |  |
| 12 | `BATT_TEMP?` | `ERR:CACHE_INVALID` |  |
| 13 | `ADU_TEMP?` | `ERR:CACHE_INVALID` |  |
| 14 | `BBU_TEMP?` | `ERR:CACHE_INVALID` |  |
| 15 | `FAN_RPM?` | `ERR:CACHE_INVALID` |  |
| 16 | `FAN_LEVEL?` | `ERR:CACHE_INVALID` |  |
| 17 | `AC_OFF_HOUR?` | `ERR:CACHE_INVALID` |  |
| 18 | `PS_OFF_HOUR?` | `ERR:CACHE_INVALID` |  |
| 19 | `AVE_OFF_TEMP?` | `ERR:CACHE_INVALID` |  |
| 20 | `OFF_CHARGE_HOUR?` | `ERR:CACHE_INVALID` |  |
| 21 | `AVE_CHARGE_TEMP?` | `ERR:CACHE_INVALID` |  |
| 22 | `OFF_CHARGE?` | `ERR:CACHE_INVALID` |  |
| 23 | `OFF_BATT_DEG?` | `ERR:CACHE_INVALID` |  |
| 24 | `CHARGE_DATA?` | `ERR:CACHE_INVALID` |  |
| 25 | `CHARGE_END?` | `ERR:CACHE_INVALID` |  |
| 26 | `LIFE_BATT_CHARGE?` | `ERR:CACHE_INVALID` |  |
| 27 | `LIFE_BATT_TEMP?` | `ERR:CACHE_INVALID` |  |
| 28 | `LIFE_BATT_DEG?` | `ERR:CACHE_INVALID` |  |
| 29 | `TOTAL_ADU_TEMP?` | `ERR:CACHE_INVALID` |  |
| 30 | `TOTAL_ADU_HOUR?` | `ERR:CACHE_INVALID` |  |
| 31 | `AC_FAIL_COUNT?` | `ERR:CACHE_INVALID` |  |
| 32 | `AC_LOW_COUNT?` | `ERR:CACHE_INVALID` |  |
| 33 | `BACKUP_COUNT?` | `ERR:CACHE_INVALID` |  |
| 34 | `BATT_DEG_TOTAL?` | `ERR:CACHE_INVALID` |  |
| 35 | `TOTAL_BATT_HOUR?` | `ERR:CACHE_INVALID` |  |
| 36 | `BATT_DISCHARGE_COUNT?` | `ERR:CACHE_INVALID` |  |
| 37 | `BATT_CHARGE_COUNT?` | `ERR:CACHE_INVALID` |  |
| 38 | `BATT_TTL_DISCHARGE?` | `ERR:CACHE_INVALID` |  |
| 39 | `BATT_TTL_CHARGE?` | `ERR:CACHE_INVALID` |  |
| 40 | `TOTAL_BATT_TEMP?` | `ERR:CACHE_INVALID` |  |
| 41 | `BATT_TEMP_AVE?` | `ERR:CACHE_INVALID` |  |
| 42 | `BATT_TEMP_MAX?` | `ERR:CACHE_INVALID` |  |
| 43 | `BATT_TEMP_MIN?` | `ERR:CACHE_INVALID` |  |

- This result is consistent with the Cache starting INVALID after power-on.
  To exercise value formatting and decoded values, an explicit `DATA_REFRESH`
  is required. OI-03 (D0/CHARGE_END side effect) remains open, so D0 was not
  sent as part of this query-only check. No Open Issue was closed.

## 2026-11-07 DATA_REFRESH and all DATA Cache Queries (COM19)

- The operator explicitly authorized D0 transmission. `TEST_START` returned
  `OK`, `DATA_REFRESH` returned `OK`, all 43 DATA Cache Queries returned a
  complete CRLF response, and `TEST_END` returned `OK`. No query timed out.
- D0 transaction: T2=600ms provisional, transaction result `OK`, command retry
  0, response retry 0, elapsed 238ms, ambiguous False. The D0 NF55G timestamp
  decoded as `20260401_021253`; this is the received product data, not an
  independently verified current time. Logger filename timestamp was
  `20261107_181051`.
- Host transcript with TEST_START, D0, every query and Ans, and TEST_END:
  [temp/20261107_181100_data_cache_ate.csv](../temp/20261107_181100_data_cache_ate.csv)
  (46 data rows, 4,250 bytes, SHA-256
  `2c76ae9bddf818daf892e239dc52c2364e0062f7a3fd4c181bfb0e76e00a4107`).
- Retrieved Pico SD logger CSV with D0 raw TX/RX and transaction row:
  [temp/20261107_181051_pico_sd.csv](../temp/20261107_181051_pico_sd.csv)
  (1,447 bytes, SHA-256
  `4adfc452a16dc4825a955e1fb07314a3c975cfe0e1894ae450730eb87e3a4664`).
- The 43 ATE Query Ans are preserved in the host transcript; the SD logger
  records NF55G raw frames and transaction metadata, not ATE Query lines.
  OI-03 remains Open despite this explicitly authorized test; no product
  PASS/FAIL judgment is assigned and no other control, SC, D2, D3, D4, or FU command
  was sent.
- After copying the SD CSV, Pico was reset to restart `/main.py`. A final COM19
  `*IDN?` returned `NF55G_PICO_FIXTURE,Rev.0`, confirming ATE service
  resumed.

## 2026-11-09 通信ポート変更・ローカル応答確認

- ユーザー指定により、以後の本案件の接続はATE側COM20、Pico 2 USB保守側COM14とする。過去のCOM19等は当時の記録として維持する。
- 08:40 JSTのpySerial列挙: COM20=Elecom USB-Serial Converter（VID:PID 056E:5004）、COM14=Pico USB（VID:PID 2E8A:0005、SER 2D35A1E11AC125E3）。
- COM20: 115200bps／8N1／フロー制御なし、DTR・RTS無効。*IDN? → NF55G_PICO_FIXTURE,Rev.0、COMM_STATUS? → OK:state=IDLE、SD_STATUS? → OK。全応答CRLF完結。ATE↔Pico UART0の要求・応答を確認。
- COM14は開放状態でopen/read/close成功。受信0byte。実行中アプリを維持するため送信・Ctrl-C・REPL割込み・resetは行わず、USB REPLの双方向応答自体は今回未確認。
- ポートはいずれもclose済み。Picoへの配置、TEST_START／TEST_END、SD復帰、NF55GへのRefresh／Control／FU送信は実施していない。搭載FWと今回変更済みHostソースの一致は未確認。
- 実測原本: [通信確認JSON](../temp/serial_port_check_20261109.json)。再現用: [確認スクリプト](../temp/serial_port_check_20261109.py)。ハードウェア通信確認のためHost／Mock再実行なし。製品PASS/FAILは判定していない。

## 2026-11-09 変更レビュー・SD抜き差し・D3/D4実機確認

### 前提・配置・修正
- ユーザーが実機サンプル接続と電源ONを確認。ATE=COM20、Pico USB=COM14。QR/DMMはマイコン入手後の別開発・結合試験とする。
- Pico2/RP2350、MicroPython v1.28.0、unique ID 2d35a1e11ac125e3を確認。配置25ファイルは13:18の配置マニフェストと全件一致。照合時のPCソースとは3ファイルに差分があるが、今回の受入では再配置していない。COM14既存機・COM20にはアクセスしていない。
- レビューでATE受信層の拒否ログ漏れをRECEIVE_ERRORで補正。実機でTEST_ENDがBUSYなのに先行OKが残る問題を発見しEND_REQUESTへ修正。応答期限境界の部分RAW・ACK待ち異常byteも記録。T1/T2・再送・ACK/NAK・Cacheの回帰試験を追加し、Host／Mock全284件成功。
- 変更3ファイルを[退避](../temp/hil_20261109_run01/pico_before/)、COM14へ配置。全25ファイルの読戻しSHA256が現行PCソースに一致。直前のCOM20配置マニフェストとも一致。MicroPython v1.28.0上でcompile25件、RAM Mock31ケース成功。製品コマンド送信なし。
- ユーザーの追加指示前の初期化確認ではRTC_CHECK=NG、SD_STATUS=MOUNT_ERR（CARD_INIT、CMD0 failed: -1）、自己診断はRTC=NG／LOGGER=MOUNT_ERR。これは確認時の応答であり、部品未装着・配線・カード等の原因は未確認。正常のCOM14機と混同しない。
- app.runのサービス5周期を確認してCOM6を解放済み。今回の電源再投入試験は未実施。Cacheは全INVALID、Logger／TESTは停止、確認区間のNF55G送信をガードし試行0、Transaction=None。製品コマンド・FU送信なし。コード変更・再配置なし、Host／Mock再実行なし（直前284件成功）。
- 証跡・次の試験は[受入確認記録](../temp/hil_20261109_run01/result_summary.json)、[実機証跡一式](../temp/hil_20261109_run01/events.jsonl)、[SDログ回収](../temp/hil_20261109_run01/20261109_084638.csv)、[SDログ再確認](../temp/hil_20261109_run01/20261109_085254.csv)、[TX/RX実測原本](../temp/hil_20261109_run01/product_logs_after_clear.json)。

## 2026-11-09 開発機COM6／ATE COM20でのNF55G接続確認

- ユーザーがNF55Gと治具の通信ケーブル接続済み・NF55G電源ONと回答。開発機COM6（固有ID 69f7d45962cfdfad）、ATE COM20で確認。COM20は115200bps／8N1／CRLF。ローカルの`*IDN?`=`NF55G_PICO_FIXTURE,Rev.0`、`RTC_DATETIME?`=`20261109_173249`、`COMM_STATUS?`=`OK:state=IDLE`、`SD_STATUS?`=`OK`。
- 製品への読出しを1回ずつ実施。`STATUS_REFRESH`（D1）=`OK`、続くCache Query `PS_ON?`=`1`、`RETRY_COUNT?`=`OK:cmd=0,rsp=0`。`INFO_REFRESH`（D5）=`OK`、続く`FW_REV?`=`S1.13`、再送0、通信IDLE。プロトコル上の正常応答であり製品PASS判定ではない。
- COM20がCOM6の開発機につながることを確認するため、COM6をraw REPLで停止し固有IDを読んだ間のCOM20 `*IDN?`は無応答。COM6の通常起動を再開した後のCOM20 `*IDN?`は正常応答。COM6／COM20は解放済み。
- NF55Gへ送信したのはD1/D5のみ。制御・設定・CLEAR・FU送信なし。製品出力・量産Timing・RTC電源断保持は未確認。詳細応答は[D1結果](../temp/dev_acceptance_20261109_run01/nf55_link_status.json)と[D5結果](../temp/dev_acceptance_20261109_run01/nf55_link_info.json)。

## 2026-11-09 開発機の実装済みATEコマンド実機デバッグ

- COM6開発機／COM20 ATE／FW S1.13、ユーザー申告でバッテリ・負荷なし。D0/D1/D5、EL全4ブロック、OL全8ブロックを取得し、DATA43・STATUS37・INFO26項目と各履歴Queryを照合。代表CSVのD0/D1/D5/EL/OL応答長327/15/100/82/82、BCC一致、再送0。
- D2はSC前に2回ERR:SQE。CLOCK_SYNC 261109174156=OK後はD2=OK・DATA30文字、再送0。NF55G日時は事前20260401_042601、設定後20261109_174156。受付条件の解釈はD2-PS-01でOpen継続。
- ERP4組合せを順に送信し、各SE後のSTATUS無効化と明示D1後のBURST/PS_OFF_CHARGE読戻し一致を確認。元の0/0へ復元。BURST_ON=0のままで外部バースト動作は未測定。
- 現行D5のParameter RAW50文字をPARAM_SETで同値書戻し、EVENT_ENABLE現値0を項目別SPで同値設定。各SP後INFO無効化、D5全26項目と100文字RAWが前・中・後で一致。両SP正常応答DATA0文字。項目別SPの送信RAW CSV行1件に列欠けがありLOGGER-CSV-01をOpenで追加。
- FW_UPDATE等のローカル拒否を確認し、拒否試験CSVにはNF55フレーム0。339応答の無間隔区間で試験ログ391件破棄・Self Check NG。75ms間隔の106 Queryおよび以後の区間は当該試験のdrop0。LOGGER-BURST-01をOpenで追加。
- 最終はPS_ON=1、BATT_ON=0、BURST/PS_OFF_CHARGE=0/0、SD OK、通信IDLE、累積drop0。製品PASS判定なし。コード・再配置なし、Host／Mock再実行なし（直前203件合格）。

## 2026-11-09 CSV列欠けの再現確認・前報訂正

- ユーザー指定のATE速度は0.1秒に1コマンド送受信程度、それ以上速くしない。最終試験は高分解能時計で送信間隔101ms以上を確保し、前応答完了を待った。117コマンド、実測最短101.0453ms、ログ破棄0・Self Check OK。継続時にプロセス完了と保存結果を確認した。
- SDの20261109_180800.csvを256 byte分割回収。88307 byte・1405行14列、SD/PC SHA-256一致。SP20件・D5 21件が正常、再送0、82フレームBCC一致。変更時は対象欄のみ変化、各復元後D5全100文字が一致。
- 08:02 JSTの現在値再確認でもINFO全26項目が元値と一致。Self Check/SD正常、通信IDLE、COM6/COM20解放。コード変更・再配置なし。実動作・電源切入保持・RTC電池保持は未確認。詳細は[項目別PARAM実機記録](Parameter_Item_Hardware_Test_20261110.md)。

## 2026-11-09 BURST／PS_OFF_CHARGE 継続準備

- Host／Mock全273件成功。COM20のローカル診断で通信IDLE、自己診断／RTC／SD正常、ログ破棄0を確認しポート解放。NF55G指令・設定変更・配置は実施していない。
- ERP全4組合せの通信・読戻し・復元は前回確認済み。今回の外部BURST動作とPS_OFF充電比較は、電源・バッテリ／負荷・信号操作条件をユーザーへ確認中。実動作成立は未確認、ERP-CONDITION-01はOpen継続。
- 証跡・次の試験は[ERP継続準備](ERP_Precheck_20261109.md)。変更は記録とローカル診断スクリプトのみ。

- 再開後、ユーザーがCOM6／COM20、NF55G電源ON・通信接続、バッテリ／負荷なし、BURST・PS_ON操作可能と回答。12:23 JSTの明示D1はPS_ON=1、BATT_ON=0、BURST_ON=0、BURST／PS_OFF_CHARGE=0/0、BC実行なし、再送0。TEST_END後自己診断／SD正常、破棄0、IDLE。外部BURST反転を依頼し操作回答待ち。設定変更なし。詳細・証跡は上記ERP継続準備へ追記。
- 12:25 JST、ユーザー申告BURST OFFで明示D1のBURST_ON=0を確認。PS_ON=1、ERP設定0/0、再送・破棄0、自己診断／SD正常、IDLE。操作前も0のため切替検出とは扱わず、次のBURST ON操作を依頼。設定変更なし。証跡は[ERP継続記録](ERP_Precheck_20261109.md)。
- 12:27～12:28 JST、BURST ON申告後もD1のBURST_ON=0。ERP_SET_1_0→明示D1で設定1/0、入力0を確認し、ERP_SET_0_0→D1で元値復元済み。終了時自己診断／SD正常、再送0、IDLE。ユーザー説明はONでGND接続。ユーザー側で開放／閉路とON/OFFを整理して試験するため操作待機。端子実測と原因は未確認、CSV回収・BCC照合は未完了。詳細・ATE JSONは[ERP継続記録](ERP_Precheck_20261109.md)。
