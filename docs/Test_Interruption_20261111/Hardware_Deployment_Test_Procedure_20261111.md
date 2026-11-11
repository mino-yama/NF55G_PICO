# 再START修正版：Pico配置・実機試験手順

2026-11-11。ユーザーへ実行前にチャットで提示した手順を記録する。

1. COM6のUSB serial／machine.unique_id=69f7d45962cfdfad、COM20のID応答を照合。通信IDLEを確認し、TEST_ENDで既存の記録期間を終了させ、SD／Self Check／破棄件数を記録する。
2. COM6の通常アプリを停止し、resetせずraw REPLへ入る。main.py／boot.py／src各ファイルを案件内の時刻別backupへコピーする。配置対象4ファイル（logger.py、sd_sink.py、command_dispatcher.py、main.py）の配置前とPCのSHA-256を記録する。
3. Host／Mock合格後、対象4ファイルだけを/srcへ配置し、Pico側SHA-256とPCの一致を確認する。不一致時は試験を開始しない。main.py／boot.py等の入口は変更しない。
4. 通常起動後にID、通信IDLE、RTC、SD、Self Checkを確認。TEST_START→CLOCK_SYNC（SC、送信時の日本時間）→DATA_REFRESH→NF55_DATETIME?／VOUT12?／IOUT12?／BATT_VOLT?を順次実施する。
5. 最後のデータ取得後、PC単調時計で10秒待機して再TEST_START。期待値OK。その直後の旧DATA QueryはERR:CACHE_INVALIDを期待する。これは自動Refreshなしの確認である。
6. 明示DATA_REFRESH→データ取得後、3回目のTEST_START。再度Cache失効を確認し、明示DATA_REFRESH→取得→TEST_ENDを実施する。
7. 最終PICO_SELF_CHECK?／SD_STATUS?／LOG_DROP_COUNT?／COMM_STATUS?で保存診断正常・破棄0・通信IDLEを確認。各指令の応答時間と送信間隔を記録する。
8. TEST_END後にSD CSVを256byteずつ回収し、SD側SHA-256とPC側を照合する。独立した試行IDのCSVが3本、前2本の終了区分NEXT_TEST_START、最終TEST_ENDであることと、各試行のSC／D0／Queryが他ファイルへ混在しないこと、全行14列、NFフレームBCC・retryを確認する。
9. 通常アプリを再開し、ID応答を確認してCOM6／COM20を解放する。

ATE指令は前応答後0.1秒以上空ける。機器ID・配置hash不一致、応答timeout、予期しない通信／保存異常では後続製品操作を止め、状態を記録する。SC以外の製品設定、SS／FU、バッテリ操作、SD抜去・電源断試験は行わない。製品PASS/FAIL判定は含まない。QR実入力は新USB経路未実装のため今回は含めない。
