# RTC異常時ログ改修 親Pico配置・実SDデバッグ結果

Date: 2026-11-28  
Revision: Rev.0  
結果：配置・実SDデバッグ・ハードリセット後の採番引継ぎ確認を完了。常駐アプリを再開し、COM6を解放した。

2026-11-28追試：保存後の実電源OFF／ON、PCシリアル経由30試行、実SD異常系6件も確認した。[追加実機結果](../RTC_Fallback_Log_Extended_Test_20261128_Rev0/Result.md)を参照。以下の未実施記載は本記録作成時点の履歴と区別する。書込み途中の電源断等は引き続き未実施。

## 1. 対象と配置確認

- 親Pico COM6／unique_id=`69f7d45962cfdfad`／MicroPython v1.27.0。
- 試験・Logger・NF55G通信が停止中、SD状態OKを確認して着手した。
- [実装版](../RTC_Fallback_Log_Implementation_20261128_Rev0/Result.md)の変更4件（log_filename.py、logger.py、sd_sink.py、src/main.py）を配置。
- 配置前ハッシュが11月27日配置版と一致することを確認した。変更前3件、実機config、RTC driver、起動/main.py、校正設定の計7件を[backup](backup/)へ保存し、実機ハッシュと照合。
- 一時領域へ転送し、MicroPython構文検査とMemorySDSinkによる仮ID作成・S/N付加の実行確認後に切り替えた。
- 変更4件を[readback](readback/)へ読み戻し、候補とSHA-256一致。未変更部分を含むアプリ対象37件も期待ハッシュと一致した。
- 通常再起動後と実SDデバッグ後にも37件を照合し、設定・他のアプリファイルを保持したことを確認。

保持値：外部測定器=True、QR=True、双方向QR試験モード=False、サンプル校正=True、ATE終端CR、AR T2=100ms、REPL_LOG=True。config.py・calibration_limits.py・起動用/main.pyは書き換えていない。

配置元は新規21件を含むHost Unit／Mock NF55G全596件成功の候補と一致する。今回の配置中に同じHost全体試験を再実行したものではない。

## 2. 実SDのデバッグ方法

通常の`/sd/BANK_A`／`/sd/BANK_B`を操作対象にせず、実SD内の専用領域`/sd/rtc_debug_20261128_rev0/`へ独立したFileSDSinkを作成して検証した。試験データと所有マーカーはこの専用領域に残し、通常ログを循環削除する操作は行っていない。

RTCなし・読取り失敗・無効日時は、試験用LoggerへNone／例外を返すオブジェクト／不正日時を返すオブジェクトを渡して模擬した。実RTCの取外し・時刻設定・レジスタ変更は行っていない。製品通信のためのATE指令、AD／AR／CAL_WRITE／SSは送信していない。

## 3. 実機で確認できた結果

| ケース | 実SDでの結果 |
|---|---|
| 両BANK・S/N付き・0 byteの採番対象 | BANK_BにS/N付きT000040、C000041の0 byteファイルを作成。再走査で最大41を取得 |
| RTCなしTEST | `NO_RTC_T000042.csv`を開いて記録。終了時に`000001_NO_RTC_T000042.csv`へ変更、IDを保持 |
| RTCなしCONT | `NO_RTC_C000043.csv`へ記録・正常close |
| RTC読取り例外 | READ_ERRORを保持し、T000044へ保存。SD記録を開始できた |
| 無効日時 | INVALIDを保持し、T000045へ保存。架空の日時を付加しない |
| RTCなしCONT分割 | C000046からC000047へ切り替え、Queueの行を保存 |
| 通信busyの延期 | busy模擬中はservice=0、終了処理も延期。解除後に残行を保存してclose、drop=0 |
| ハードリセット後 | 実SDを新しいsinkで再走査して最大47を取得。次のTESTは48で、`000002_NO_RTC_T000048.csv`へ保存 |
| 旧試験ファイル保全 | 再起動前の試験ファイル8件は、再起動後の新規保存前後ともSHA-256一致 |
| CSV回収 | 前後計9ファイルをPCへ回収し実SDハッシュと照合。0 byteの準備用2件を除く全CSVが14列、データ7行のtimestampはすべて空欄 |

最大番号41→42～47→ハードリセット→48という引継ぎを実SDで確認した。単なるRAM上のカウンタ継続ではない。

前後9ファイルのうち、2件は採番確認用の0 byte、C000046は分割前のヘッダーのみであり、これを記録欠落と数えない。C000047には分割とbusy延期の2データ行を確認した。

最後に実RTCの読取り可能状態、実アプリの試験・通信停止を確認した。時刻の精度や電池保持の評価ではない。同じactive_app.run()を再開し、再開直後にTracebackがないことを確認して保守ポートを閉じた。

## 4. 証跡

- [manifestと配置前・期待ハッシュ](manifest.json)
- [配置直後ハッシュ](after_apply_hashes.json)／[デバッグ後ハッシュ](final_hashes.json)
- [全操作ログ](operations.jsonl)
- [再起動前の実SD結果](hil_before_reset.json)／[再起動後の実SD結果](hil_after_reset.json)
- [CSV列数・空欄・行数の照合](csv_verification.json)
- [再起動前CSV](sd_csv_before_reset/)／[再起動後CSV](sd_csv_after_reset/)
- [完了状態](result.json)
- [配置・デバッグ用スクリプト](../../scripts/deploy_rtc_fallback_20261128.py)

実機内の変更前退避先は`/rtc_log_before_20261128_rev0/src/`。新規log_filename.pyには変更前ファイルが存在しない。従来の実機バックアップ領域は削除していない。

## 5. 残確認・制限

- 実施した再起動はmachine.reset()によるハードリセットであり、外部電源のOFF／ONではない。
- 実RTCを物理的に未接続とする起動、電池保持、OSF、長時間電源断は未検証。
- 書込み中・名前変更途中の実電源断、FAT破損時の挙動、通常BANKでの実容量循環は未検証。Host試験の異常注入結果と区別する。
- 実ATEによる長時間・複合負荷、応答時間の量産受入は未実施。今回の保存結果を製品の校正PASSへ転用しない。
- 削除済みログや別SDを含む永久欠番、独立した同時書込み主体に対する排他保証は追加していない。

RTC-LOG-01～04は、配置と今回の限定実機結果を追記したうえでOpenを維持する。
