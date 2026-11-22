　# HOST USB CDC受入試験 2026-11-22 Rev.1

## 現在の到達点

CDC中継の連続通信、idle切断/再接続、送信開始後切断とambiguous故障保持、手動RSTでの新boot/READY、設定復元、SD/RTC併用を実機確認した。NF55G D1との連続burst共存でSDログdropを発見し、Schedulerを修正した。全461回帰成功、親へ配置・再起動後SHA照合済み。修正後の実機共存再試験はHost RST操作待ち。

完成・量産受入・Open Issue Closeとはしない。QR Hostはユーザー回答で未接続。NF55G実機は接続・通電済み。

## 確認した事実と証拠

|試験|結果|根拠|
|---|---|---|
|起動診断|新Host nonce 8F576F91FDCD8F6B、120回H/h READY、decode異常0。Hのみ、機器Qなし|[H診断](reset_hello_probe.log)|
|実機連続IDN+ローカル照会|200/200成功、400応答の順序一致、Host A/T/R各200、同一session。中央値234ms、最大297msはburst全体|[結果](Acceptance_05/result.json)|
|idle切断反復|追加2条件とも未送信LINK_NOT_READY/AMBIGUOUS=0で停止。送信中切断の成功には数えない|[IDN連続中](InFlight_Disconnect_01/result.json)、[通常READ中](InFlight_Disconnect_READ_01/result.json)|
|再接続と測定|IDN/DCV/CONF原文、SD=OK、RTC=OK、drop=0。READ100/100成功、9.62224〜9.62229V、531〜750ms。精度/製品合否は評価しない|[結果](Readback_01/result.json)、[全応答](Readback_01/requests.json)|
|処理中切断|要求496でA→E=DISCONNECTED|1、T/Rなし、ATE AMBIGUOUS=1。自動再送なし|[結果](InFlight_Disconnect_Delayed_01/result.json)|
|故障保持|後続IDNは親でRECOVERY_REQUIRED/AMBIGUOUS=0、Host出力0 byte|[結果](fault_hold_idn/result.json)|
|デバッグ復帰|RST前FAULT、RST後nonce 78745BF38AB3C37E、READY10回連続。新接続のIDNは7355期待原文一致|[診断](active_disconnect_recovery_hello.log)、[IDN/復元](Trigger_Delay_restore/result.json)|
|一時設定の復元|TRIG:DELの元値+0.0000E+00を保存→5秒を読戻し→試験後0秒へ復元・読戻し一致。レンジ変更なし。5秒設定がREADを実際に5秒待機させたとの時間保証は行わない|[保存・復元状態](trigger_delay_original.json)、[設定時](Trigger_Delay_arm/result.json)|
|SD/RTC/ATE共存|50回READ+SD+RTC+drop照会、構文異常4種類→正常IDNが成功。drop0。CSV25,790 byte/416行、実機SHA一致、列崩れ0|[結果](Logger_Coexist_01/result.json)、[CSV検証](Logger_Coexist_01/csv_verification.json)|
|NF55Gとの共存（修正前）|21回目のREAD/D1/照会burstでdrop6、終了後drop8。D1は21回すべてOK、Retry0、SD/RTC OK。異常検出で停止・ログ終了|[結果](NF_Coexist_01/result.json)、[CSV分析](NF_Coexist_01/csv_analysis.json)|

H/READYとIDN一致は、その条件での確認結果であり、任意の遅延7355応答を全て排除する証明ではない。旧応答排除の一般受入はOpen。

## 発見・修正した問題

src/main.pyのservice_onceはATE要求を一つ処理すると無条件returnし、最終応答後のSD処理を次巡回まで延期していた。PCが最終応答直後に次burstを送る条件で、Logger排出の機会を失いRAM Queueが満杯になる。

最終応答後は既存server.has_work/通信busy判定へ進める。待ち要求・未送出応答・受信中の行があれば従来どおりATE優先でreturnし、それらがなければ同じ巡回でLogger.serviceへ到達する。flush条件、排出行数、Cache/Decode、NF55G/CDC protocol、Retry、通信中SD禁止を変更していない。

追加回帰2件で、修正前はdrop688とSD排出延期を再現し、修正後は連続50 burstでdrop0、SD write/flush時にATE work/通信busyがないことを確認。全Host Unit/Mock NF55Gは461件成功、9.859秒。

- [修正前の失敗](Scheduler_Before_Fix.log)
- [修正後の全回帰](Scheduler_After_Fix_Unit.log)
- [実機原本との差分](scheduler_deploy.diff)
- [配置manifest](Scheduler_Fix_01/manifest.json)、[配置操作](Scheduler_Fix_01/operations.json)
- [配置前全Flash](Scheduler_Fix_01/parent_flash_before.bin)、[元main](Scheduler_Fix_01/main_before.py)、[修正版main](Scheduler_Fix_01/main_candidate.py)

親個体69f7d45962cfdfad。配置前main SHA d7735c95e6e799d3818e0f05e561370c5b1d9226df6fabf5acde5a6dfc75b9cb、配置後15522 byte / SHA cbb7c94e70cf330c11af056a5f7ff7e05a31e11fc7228494450ce468a580a120。compile・再起動後実機SHA一致。現行Flash4MBをsave -a -v退避・verify、SHA60c55b66cf4472c14886e7093d202772175c78dcd7d55b4cd78c56a31be4262a。

## 残る受入・設計事項

- 修正後の実NF55G/7355/SD共存50回再試験とCSV照合。
- 長期負荷の正式時間・要求頻度・ATE応答時間上限は未確定。同期SD I/O開始後の新規ATE到着遅延の上限は今回保証していない。
- QR Host実機共存は未接続のため未実施。
- 量産用の手動RSTに依存しないHost復旧/監視/WDT/管理指令は未実装・方式未確定。既存faultを勝手に解除しない。
- 測定Cacheへの正式取得API/単位/取得token接続は別途未確定。確定済み中継契約どおり任意応答をCalibrationMeasurementsへ保存しない。
- USB-RELAY-HOTPLUG-01、USB-HOST-RESET-01、USB-CDC-SD-01等はOpen。旧記録のRST成立未確認は当時の事実として[Rev.0](Acceptance_Status_Rev0.md)へ保持。

現在は新SchedulerのRAM runtimeが同じ親nonce A45C01F31E63BA81で稼働。H診断120回は旧Host nonce 78745BF38AB3C37E/FAULTのまま終了し、新boot成立はまだ未確認。診断PCプロセスを終了しCOM6/7/22は解放済み。Host RST操作の回答待ち。機器の一時遅延は0秒へ復元済み。NF/CDC要求・測定・設定送信なしで待機。次の再開では親を再起動せず、ユーザーのHost RST後に同じ親runtimeから新しいH/IDNを照合してNF_Coexist_02を実行する。

## 変更ファイル

src/main.py（SD排出飢餓修正と日本語コメント）、tests/test_external_instrument_link.py（計5回帰追加）、CHANGELOG/Test_Specification/Software_Module_Interface/Logger_SD_Spec/Open_Issues、本文書と本フォルダの実機script/原文/退避。Host C FWと既存NF55G仕様・原典PDFは変更していない。

最終静的確認: 今回変更した追跡ファイルのgit diff --check成功（改行正規化warningのみ）、script/コード13ファイルのAST parse成功。
