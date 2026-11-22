# USB bulk IN受信0 byteのソース経路調査 Rev.0

日付: 2026-11-22。NF55G Pico治具、測定器用HOST。ユーザー指定の「優先1: USB受信処理の追跡」を実施。ソース調査のみで、FW/実機を変更していない。

## 結論

受信要求の投入→PIO USBのIN処理→完了イベント→CDC FIFO→中継engineまでを追跡した。現在の実機記録だけでは停止箇所は確定しない。ただし、以下の停止/待機経路が固定ソース上に存在する。

1. NAK継続と期待DATA PID不一致は転送完了/失敗イベントを発生させず、次USBフレームで同じ転送を継続する。したがってUSB_RX_XFERが出ないTIMEOUTと両立する。
2. CDCの受信要求投入が失敗し、FIFOも空の場合、アプリはreadを呼ばず、受信再投入を試みない。投入失敗の直接通知もない。無受信のまま上位TIMEOUTに至る経路がある。
3. 下位転送完了イベントが上位へ届かない場合、下位has_transfer=0と上位busy=1の食い違いが残り、CDC FIFOへ到達しない可能性がある。
4. RX0はengineへ取り込んだbyte数。期限判定がFIFO読出しより先なので、期限境界でFIFOにデータが存在していてもRX0として通知し得る。

1〜4はいずれもソース上の条件付き経路であり、本件で実際に発生したという意味ではない。NAK自体や単発のPID不一致を直ちに異常とは扱わない。既存.22.3の観測値で絞れる部分と、追加観測が必要な部分を下記に分ける。

## 調査対象と実機証拠

- 固定SDK: tools/usb_submcu/pico-sdk-2.2.0、同梱TinyUSB。PIO USB: firmware/usb_submcu_host_probe/vendor/pico-pio-usb。build.ninjaのrelayターゲットにこれらのコンパイル元が登録されていることを確認した。
- 現在の作業ツリーは候補meter-host-relay-20261122.3。実機の直近記録は.22.2で、A/T/E、TIMEOUT_RX0_T1_C0_XNONE|1。Qは*IDN?を1回、再送なし。[実機記録](timeout_snapshot_confirmed_idn/result.json)、[前段診断](Timeout_Snapshot_Diagnostic_Rev0.md)。
- .22.3は未配置という最新記録。既存467試験成功/ARM build成功を今回の調査による試験実績として数え直さない。[候補manifest](USB_Lower_Diagnostic_Candidate/manifest.json)、[配置前状態](USB_Lower_Diagnostic_Rev0.md)。
- 今回は実機を照会していない。実機の現在電源・接続・稼働状態は新たに確認していない。

## 正常経路（固定ソースの行番号）

| 段階 | 処理と重要な条件 | 根拠 |
|---|---|---|
| 受信口を開く | CDCのbulk INをstream.rxへ登録 | cdc_host.c:724〜737 |
| 最初の受信投入 | mount callbackの後、tu_edpt_stream_read_xferを呼ぶ。戻り値は検査しない | cdc_host.c:768〜779 |
| 受信領域/所有権 | FIFO空き>=64、claim成功で最大ep_bufsizeを投入。本設定RX FIFO256/ep_buf64なので、空なら64 byteの要求 | tusb.c:430〜461、tusb_config.h |
| HCDへ渡す | usbh_edpt_xferがbusy=1にし、HCD→pio_usb_host_endpoint_transfer→transfer_startへ。HCD失敗時はbusy/claimedを0へ戻す | usbh.c:895〜930、hcd_pio_usb.c:125〜127、pio_usb_host.c:418〜435 |
| PIO受信予約 | app_buf/total_lenを設定、actual_len=0、has_transfer=true | pio_usb.c:379〜400 |
| フレーム処理 | 1ms timerでframeを処理。timer_active、root初期化/接続/非suspend、endpoint size、has_transfer、非abortが実行条件 | pio_usb_host.c:44、212〜277、312〜317 |
| IN取引 | IN token送信、受信/CRC確認、期待DATA0/1一致時だけbufferへコピー | pio_usb_host.c:474〜502、pio_usb.c:149〜202 |
| 下位完了 | actual_len加算・toggle反転、short packetまたは要求長到達で完了bit設定、has_transfer=false | pio_usb.c:403〜442 |
| 完了イベント | frame末尾でIRQ handler→HCD event queue→tuh_task_extが処理、busy/claimed解除→CDC callback | pio_usb_host.c:297〜301、hcd_pio_usb.c:162〜195、usbh.c:538〜584 |
| FIFO格納と次投入 | CDC callbackがFIFOへ格納、アプリrx callbackを呼び、次の受信を投入 | cdc_host.c:673〜710、tusb_private.h:143〜146 |
| engineへ渡す | mainのservice_usb_rxがFIFOを最大64 byte読む→relay_host_rxが応答へ蓄積。CRLFかつTX完了でR | relay_main.c:179〜187、relay_host.c:179〜212 |

ここでのcdc_host.c/usbh.c/tusb.c/hcd_pio_usb.c/tusb_private.hは固定SDK同梱TinyUSB、pio_usb.c/pio_usb_host.cは上記vendorを指す。末尾に各ファイルへのリンクを掲載する。

空のtuh_cdc_rx_cbは原因を示さない。固定SDKがその直前にFIFOへ格納し、アプリは別途pollして読む設計である。

## 停止・待機候補の評価

| 候補 | ソースで確認できた条件 | 本件との関係・未確認事項 |
|---|---|---|
| A: NAK継続 | pio_usb_host.c:493〜494は何も完了させず次frameへ | HOST mainは動作でき、TIMEOUT/失敗callbackなしと整合。NAKを実観測したわけではない |
| B: DATA PID不一致 | 同:486〜492。CRC成立のDATAでも期待toggleと違うとコピー/加算/完了なし | 同じ受信0/失敗callbackなしと整合。下位はPID照合前にACKし得るが、これ自体は重複DATA処理でも起こる。継続不一致や原因は未確認 |
| C: 受信の未投入 | read_xferのclaim/HCD失敗等で0を返す。CDCの初回/次回投入は戻り値未検査 | appはFIFO>0の時だけtuh_cdc_readを呼ぶ。FIFO0ではread経由の再投入もなく、正常復帰手段がない。投入失敗の実発生は未確認 |
| D: 完了イベント未到達 | 下位完了はhas_transferを解除、上位busy解除はeventを処理する時 | HCD queue投入失敗やevent未処理等なら不一致が残り得る。queue_eventは失敗時TU_ASSERTでreturnし、hcd_event_handlerは返値を扱わない。queue満杯の記録はない |
| E: root/timer/abort条件 | timer停止、root非接続/suspend、has_transfer=0、abortでINを呼ばない | IN無活動候補。OUT Tはその時点までのOUT完了のみを示し、その後のIN進行を保証しない |
| F: 期限境界/FIFO未回収 | mainはtuh_task_ext→relay_host_poll→service_usb_rxの順。relay_host_rx入口でも期限判定 | poll時点で期限ならFIFOを読む前にRX0のEを作れる。受付からの期限の意味を変える理由にはせず、FIFOの状態を追加観測すべき |
| G: 受信ループ停止 | pio_usb.c:173/193のRX完了IRQ待ちに絶対期限がなく、173のbuffer添字にも上限検査がない | コード上の潜在停止/破損経路。ただし同一HOSTから期限Eが実際に返った今回の記録を、恒久的なIRQ内停止だけで説明しにくい。発生・破損は未確認 |

HCD失敗時にbusyが必ず残るという説明は誤り。usbh.c:926〜927でbusy/claimedを戻している。残る問題は、その後に受信を再投入する契機がない場合である。

## .22.3で分けられる範囲と限界

| .22.3の観測 | 次の切分け |
|---|---|
| I増加、N増加、D=0 | 下位IN呼出がありNAKが見えた。機器待ち/機器が応答を用意しない理由等は別調査 |
| D増加、engine RX0 | 下位はCRC成立DATA等を返した。Dは0 byte DATAも含むため、D>0だけで有効payload受信とはしない。返却長・各PID照合結果・完了通知を確認 |
| I=0、H=0 | 未投入、既に完了してevent待ち、endpoint特定失敗などを分ける。EP=0は診断対象未特定であり、受信未投入の証明ではない |
| I=0、H=1 | root/timer/abort条件や計数対象の特定を確認。開始/復帰時刻が不明なので一つに断定しない |
| H=0、actual_len>0、engine RX0 | 下位にデータ履歴がある候補。長さは次転送開始まで残るため、現在要求との時刻相関、完了event/CDC FIFOを確認 |

KはTIMEOUT時点の期待toggle、Pは最後に観測したPIDで、同じ取引の照合対とは限らない。K/PだけでPID不一致を確定しない。各成功受信はtoggleを反転させる。I/N/DはQ送信開始後のみの計数で、mount直後からQ前までの受信停止は見えない。今回の初回IDN失敗ではこの観測開始前の状態も重要。

.22.3で不足する観測は、初回/次回IN投入の結果、上位busy/claimed、FIFO available、HCD完了event回数、CDC完了callback回数、個々の受信長/期待PID一致数、root/timer/abort状態。これらは追加候補であり、本調査では実装しない。無条件受信再投入、toggle強制反転、fault自動解除は原因確認前に加えない。

## 次に行う最小の切分け

1. まず既存.22.3で1回の明示IDNのI/N/D/EP/H/K/Lを取得し、初期状態と終了状態を比較する。実機配置・起動は別作業で、今回は行っていない。
2. I/N/Dの結果に従い、未投入なら初回投入/claim、DATAなら長さ/PID/完了event、下位完了ならCDC callback/FIFOの順で必要箇所だけを観測する。
3. 上記のソース分岐をPC上で再現する試験は「優先2」の後続作業。本調査で未実施。装置への同一要求再送を伴わずに検証できる。

## 変更・検証・残Issue

新規調査資料と[読取りソース11件のSHA-256一覧](USB_Bulk_IN_Source_Trace_20261122_Rev0_Hashes.json)を保存し、Open_Issues/CHANGELOGに調査結果を追記した。アプリ/vendor/SDK/テスト/既存候補UF2・原典は変更していない。実機アクセス・FW配置・コマンド送信・Host Unit/Mock再実行なし。文書リンク、候補manifest全12ソースのhash一致、差分形式の確認は成功。原因未確定のため関連IssueはOpen継続。

## ソースリンク

- [relay_main.c](../../firmware/usb_submcu_external_meter_host/relay_main.c)、[relay_host.c](../../firmware/usb_submcu_external_meter_host/relay_host.c)、[guard](../../firmware/usb_submcu_external_meter_host/relay_cdc_guard.c)、[USB設定](../../firmware/usb_submcu_external_meter_host/tusb_config.h)
- [cdc_host.c](../../tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src/class/cdc/cdc_host.c)、[tusb.c](../../tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src/tusb.c)、[tusb_private.h](../../tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src/common/tusb_private.h)
- [usbh.c](../../tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src/host/usbh.c)、[hcd_pio_usb.c](../../tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src/portable/raspberrypi/pio_usb/hcd_pio_usb.c)
- [pio_usb.c](../../firmware/usb_submcu_host_probe/vendor/pico-pio-usb/src/pio_usb.c)、[pio_usb_host.c](../../firmware/usb_submcu_host_probe/vendor/pico-pio-usb/src/pio_usb_host.c)
