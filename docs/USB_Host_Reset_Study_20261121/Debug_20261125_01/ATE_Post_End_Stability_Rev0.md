# TEST_END直後のATE応答安定化 Rev.0

2026-11-25 10:26–10:44 JST。7355個体246410099をPC直結CDC（COM26、9600/8N1、DTR/RTS ON）で比較。`READ?`→`:SYST:ERR?` を400/400回完了、IDN/CONFを含む802往復でCRLFを照合した。タイムアウト・再送・計器エラー0。READ間隔中央値2.720秒、応答406～438ms（中央値422ms）。第303回も406msで応答。CONF原文は治具経由と同じ約2V相当。測定値は40.427～40.439mVで通信確認用の記録。設定変更なし。PC直結には親Pico・Pico USB HOST・SD経路を含まず、USB再列挙後の別試行。治具経由の停止原因・400セット受入・親PicoのSD異常は未解決。次は治具経路に戻し、USB OUT ACKとIN応答を同時に観測して、途切れる区間を切り分ける。[照合結果](pc_cdc_comparison_20261125_102600_346260/verification.json)／[CDC送受信原文](pc_cdc_comparison_20261125_102600_346260/cdc.jsonl)

2026-11-25 10:24 JST。PC直結の再確認で7355 CDC `1334:0309`／COM26（USB serial `24641009900`）を認識。9600/8N1、DTR/RTS ONで `*IDN?` を1回送信し、47msで `ADC Corp.,7355,246410099,  A02` とCRLFの32byteが完全一致。PC直結でのUSB再列挙後の確認であり、停止前のPico Host経路・停止したREADの成否・根本原因・長時間安定性は未確認。READ送信・測定設定変更なし。[実機ログ](pc_cdc_idn_20261125_102431_261843.json)

2026-11-25 PC直結の初回確認。ユーザーのPC接続報告後、Serial列挙を2回実施したがADCMT CDC `1334:0309` は0件。Windowsの接続中PnP機器の検索でもADCMTのVID/PIDを確認できず、SerialはElecom COM5のみ。`*IDN?` の送信は0件。現段階ではUSB列挙までの切り分けが必要。7355のUSB端子／PC側接続と、7355の電源および現在のBUS表示を確認する。計器内部のREAD無応答との因果は不明。

2026-11-25 前面表示の確認。配線・電源を維持した状態で、ユーザー報告は `40.173 mV DC`、`RMT` 点灯、エラー表示なし。HOLDは未確認。第302セットの通信値は40.172 mV、第303セットの通信値は受信なし。前面の値が第303要求の処理で更新されたかは判断できない。比較用のPC直結CDCは過去の成功条件（同型VID/PID・9600/8N1・DTR/RTS ON）で同一個体のIDNを1回だけ確認する。USB接続の切替えで再列挙が発生するため、成功しても停止時点の状態がそのまま継続した証拠にはならない。[PC直結確認スクリプト](probe_7355_pc_cdc.py)

2026-11-25 10:11 JST。親Picoから外したカードをPCのF:で識別した。照合用T000243のSHA-256が前回退避と一致。今回のT000245～T000547をカードへ書き込まず、新規フォルダに303/303件コピーした。全件で実カードとPCコピーのSHA-256、14列、試行開始/終了マーカー、ATE側READ/SYST:ERR原文を照合した。内訳は完了302件とタイムアウトで終了した1件。PCでの回収成功により記録を保全したが、親Pico経由のSD初期化／読出しの問題と400セット未達は継続。[回収マニフェスト](endurance_20261125_095202_514101/pc_card_recovery_20261125_101155_449995/manifest.json)／[停止試行CSV](endurance_20261125_095202_514101/pc_card_recovery_20261125_101155_449995/20261125_100554_T000547.csv)

USB追加照合。第302セットはREAD 40.172mV／672msとSYST:ERR 0を受信。第303セットのREAD発行間隔3.065秒は、成功間隔の範囲2.360～3.765秒内。成功READの中央値625ms、95パーセンタイル672ms。HOSTのNAK計数はPIOのbulk IN受信バッファを観測しており、送信完了はUSB OUT側までの証拠。7355内部のSCPI受付・測定・応答生成のどこで止まったかはこのログだけでは確定しない。次は、障害状態を保持したまま7355の前面表示を記録し、PC直結CDCとの比較またはUSBアナライザでOUT ACK/IN応答を観測する。今回READ再送・HOSTリセットなし。

2026-11-25 09:52–10:06 JST。修正後に400セット耐久を再開し、302セットがATE・HOST・自己診断・SD状態の基準を通過。READは40.171～40.174mV、最長688ms。302件の終了直後自己診断は全件成功、最長156ms。第303セットのREADは要求607、ATEは10,031msで `ERR:EXT_TIMEOUT:AMBIGUOUS=1`。HOST A/T/Eの同一session・要求相関を確認。E原文は `TIMEOUT_RX0_T1_C0_XNONE_I9999_N9999_D0_S80_P5A_EP81_H1_K0_L0/64|1`。USB送信完了後、IN診断は9,999回すべてNAK、受信データなし。原因は未確定。停止まで再起動・再送なし。第303セットを追加測定なしで `TEST_END` し、失敗試行のCSVを閉じた。HOSTは同じnonceでFAULT。[試験結果](endurance_20261125_095202_514101/result.json)／[ATE TX/RX](endurance_20261125_095202_514101/ate.jsonl)／[HOST UART](endurance_20261125_095202_514101/host_uart.bin)

終了後のCSV回収は試行ID T000245～T000547を同定したが、SDディレクトリ読み出しで `OSError: read failed`。明示再認識は1回で停止し、`CARD_INIT` の `CMD0 failed: 63`、`MOUNT_ERR`、未マウントを記録。今回の303件のCSVはPC未回収で、400セット受入は不成立。親PicoはUSB REPL、測定器HOSTのFAULTを保持。SD異常と7355のIN NAK継続の因果関係は未確認。[CSV回収ログ](endurance_20261125_095202_514101/csv_export_20261125_100700_071239/csv_usb_raw.log)／[SD状態](endurance_20261125_095202_514101/parent_after_export_failure.log)

2026-11-25 実機追記。親Pico `69f7d45962cfdfad` の旧 `/src/main.py` と停止CSV T000242／T000243を退避し、すべて実機SHA-256と照合。修正を `/src/main.py` のみに配置し、MicroPython compileと実機SHA-256 `6e6fb7ee6baee16072665564d2fce1d4d6d119ae999e37561582729e96258f84` の一致を確認。旧ソースは実機 `/main_before_sd_idle.py` にも保持した。親の通常起動後、測定器HOST `.25.1` の通常RST受理と新nonce／READYを確認して、1セット実施。[配置・退避](parent_idle_fix_20261125_094745_260223/manifest.json)／[HOST再接続](parent_idle_fix_20261125_094745_260223/host_rebind.json)

修正後の単発試行は40.172mV、HOST A/T/Rの相関一致、TEST_END直後の自己診断とSD・drop・IDLE照合が成功。試行CSV T000244の最初の実機読み出しは `sd_card.readblocks` で `OSError: read failed`。当該試行終了後にSDを明示再認識してから回収でき、11データ行・14列・SHA-256一致。自己診断の改善は1セットの結果。SD読み出しの障害原因は未確定。[単発試行](endurance_20261125_094933_123874/result.json)／[初回回収エラー](parent_idle_fix_20261125_094949_286492/operations.jsonl)／[回収CSVとSHA-256](parent_idle_fix_20261125_095045_834346/manifest.json)

2026-11-25。400セット耐久は第1セットの `PICO_SELF_CHECK?` が12.031秒無応答で停止。7355のREAD、HOST UARTの要求相関、`TEST_END` は成功。単発事前試験でも同位置で再現し、後追い照会は正常。試行CSVの回収は未実施。[実機記録](Hardware_Test_Attempt_Rev0.md)

親Picoの旧処理は `TEST_END` 応答後、UARTに次要求がまだ到着していなければ、同じ巡回で同期SD再認識を開始する。実機sinkではアンマウント、SPI初期化、カード初期化、再マウントを同期実行する。旧処理が自己診断の到着前に再認識を始める順序をPC上で再現した。実機で応答が消えた直接原因は未確定。

親Picoの `src/main.py` で、自動再認識をATE応答・要求の処理後、連続250 msの通信待機を確認するまで延期した。途中でATE処理があれば待機を起点から数え直す。250 msは実機の直後照会を先に処理するための初回候補値。試行中と通信中は再認識せず、idle後の1回に限る。通常のログ排出と明示 `SD_REINIT` は従来どおり。同期再認識の開始後に到着した要求は、引き続き実機評価が必要。

`tests/test_runtime_integration.py` では、応答後120 msで到着する自己診断を再認識より先に返すこと、250 ms待機した後の一回実行、送信保留と待ち要求の優先、書込み障害からの復帰を検証。修正前の境界回帰は2失敗、修正後のHost Unit／Mock NF55Gは全535件成功。`git diff --check` 成功。[回帰ログ](sd_recovery_idle_regression_final.log)

実機には未配置。親Picoを再起動すると現在の測定器HOSTは旧親nonceに結び付いたままで、新親nonceの通常HELLOが `PARENT_RESTART` でfaultになることを実装で確認した。実機試験では失敗試行のCSVと親ソースを退避してから、親候補を配置し、親・HOSTを停止済み試行の外で再接続する。親ID・ソースhash・HOST版を確認し、単発の即時自己診断とCSV回収が通ってから新たな400セットを開始する。
