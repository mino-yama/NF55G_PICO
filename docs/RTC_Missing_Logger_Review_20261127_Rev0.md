# RTCなしでのSDログ開始不具合 確認結果

Date: 2026-11-27  
Revision: Rev.0  
範囲：確認のみ。製品コード・設定・Pico・既存仕様書は変更していない。

## 結論

指摘された不具合は存在する。RTCなしのフォールバック名がFileSDSinkの受理形式と一致せず、試験ログ・連続ログともSDファイルを開けない。TEST_STARTのATE応答はログ開始失敗を示すERRではなく、試験受付のOKになる点に注意する。

## 確認できた事実

- `src/logger.py:405`の`_filename()`は`rtc=None`で`{:014d}.csv`を生成する。通常のtick値では数字14桁＋拡張子で18文字となり、日時名の区切り`_`を含まない。
- `src/sd_sink.py:56`の`_log_name()`は、試行番号・S/Nを除いた日時部分に`YYYYMMDD_HHMMSS.csv`相当の19文字形式を要求する。「19文字だけ」ではなく、試行番号・S/N付き形式も許可するが、RTCなしのフォールバック形式は許可しない。
- TESTでは`_T000001`が追加されるものの、生成名は26文字であり、試行番号付き形式の条件（27文字以上、所定の区切り位置）を満たさない。
- `FileSDSink.open()`（149行以降）は実ファイルI/Oの前に`LoggerError('FILENAME')`を返す。`Logger._start()`はこれを捕捉し、`sd_status='FILENAME'`、`active=False`となる。
- `main.create_fixture_app()`（470～472行）はRTC初期化のValueError／OSErrorを捕捉して`rtc=None`を継続する。その値をLoggerへ渡すため、通常起動から到達可能な経路である。
- TEST_STARTはログ開始失敗後も`test_running=True`にする。Dispatcherは試験受付とログ保存状態を分離する既存仕様に従い`OK`を返す。開始失敗自体がATEのERR応答になるわけではない。
- LOG_CONT_STARTは`ERR:FILENAME`を返す。両モードともファイルは開かず、SD記録は開始しない。

## Hostでの再現

Picoへ接続せず、マウント済み相当の`FileSDSink(status='OK')`、`rtc=None`、tick値12345で確認した。名前検証で停止するため実SD／HostファイルへのログI/Oは行っていない。

| 項目 | TEST_START | LOG_CONT_START |
|---|---|---|
| openに渡す名前 | `00000000012345_T000001.csv` | `00000000012345.csv` |
| 文字数 | 26 | 18 |
| 名前検証 | 拒否 | 拒否 |
| ATE応答 | `OK` | `ERR:FILENAME` |
| Logger状態 | `FILENAME` | `FILENAME` |
| active／ファイルopen | False／なし | False／なし |
| test_running | True | False |

TEST_START後の`log()`は試験中かつ保存異常のため拒否され、破棄数が増える。CONT開始失敗後は`log()`自体がQueueへ受け付ける場合もあるが、active=FalseのためSDへ排出しない。この違いを「両方とも全行即時破棄」とまとめない。

比較確認として、MemorySDSinkは同じフォールバック名で開始成功した。同sinkは名前形式を検証しないため、MemorySDSinkだけを使うHost試験ではこの不整合を検出できない。

実行：[確認専用スクリプト](../tmp/check_rtc_missing_logger_20261127.py)  
結果：[再現出力JSON](../tmp/check_rtc_missing_logger_20261127_result.json)

logger.py／sd_sink.py／main.py／command_dispatcher.pyについて、正本ソース・配置候補・前回配置時の保存済み実機読戻しのSHA-256一致も確認した。従って前回配置した版にも同じ処理が含まれる。今回の確認でPicoを再読取りしたものではない。

## 未確認・未決定事項

現在の実機RTCが故障・未接続であるとは確認していない。前回配置時のSD状態OKだけでは、この不具合がないことの根拠にならない。

RTCなしの正式命名形式、再起動・tick周回時の衝突回避、BANK容量集計・循環対象への扱い、時刻不明の記録方法は今回決定しない。修正・実機配置・既存テスト変更は行わず、次の修正指示を待つ。
