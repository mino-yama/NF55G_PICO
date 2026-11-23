# 追加実機デバッグ結果 2026-11-22 Rev.0

## 確認できた事実

現在の配線を変更せず、DATA/INFO CacheとNF55G読取り・ATE・SD・RTCの同時動作を確認した。設定書込み・FW更新・CDC機器要求なし。D2/D3/D4には消去等の副作用があるため実行していない。

- DATAの43項目、INFOの26項目は、明示INVALID状態で全69個別QueryがERR:CACHE_INVALIDとなった。
- DATA_REFRESH(D0)とINFO_REFRESH(D5)の成功後、全69項目を2巡・138照会。各応答は保持Cacheのフィールドと一致し、Refreshなしの2巡間で値は変わらなかった。
- D0だけでSTATUS/INFO CacheをVALIDへ昇格させず、D5だけではDATA/STATUSを更新しないことを最初の実機取得で確認。
- D0/D1/D5読取り、RTC_CHECK?、SD_STATUS?、LOG_DROP_COUNT?の組合せを20回連続実施し、全応答が期待値と一致。
- 実機Transactionは計62件（D0=21、D1=20、D5=21）。すべて成功、Command/Response Retryとも0。個別Queryで追加Transactionなし。
- 保存CSVは86,861 byte、971レコード（ヘッダー除く）。ATEの661イベントは要求・応答内容・順序が全件一致、NF55G Transactionログ62件もすべてOK/Retry0。実機と取得CSVのSHA一致、旧ログのSHA前後一致。drop=0、Queue=0。
- 終了時は親runtime停止、外部PIO SM4/5停止、NF55G IDLE、Logger停止、CDC faultと親nonceを保持。dispatcherの観測proxyは元へ戻した。

## 診断処理の問題と回収

試験要求・応答の確認を終えた後、診断結果の一括json.dumpsで11,696 byteのメモリ確保に失敗した。実機コードfinally内では、Logger停止とdispatcher復元を済ませてからの出力で発生した。後続で停止状態・復元済みを再確認し、追加機器要求を送らず保持RAM結果を小分けに回収。CSVの全件照合も完了した。初回result.jsonはINCOMPLETEの履歴として保持し、回収後の集計はrecovered_result.jsonへ別保存した。

診断proxyのinitial_query_metadata_sameは、次のDATA_REFRESHがDATAをINVALIDにした後に採取していたためFalseとなった。この値は「QueryがCacheを書換えた」証拠ではなく、観測位置が不適切だったため今回の判定から除外した。保持値との一致・2巡の値一致・Transaction追加なしは別証跡で確認できた。DATA/INFOのQuery単独でupdated_msが不変かを今回の測定で断定しない。先行のSTATUS試験ではQuery後のupdated_ms不変を確認済み。

回収後、今回と直前RTC/Cache試験で追加した診断用RAM変数・proxy参照だけを削除しgc.collectを実施。アプリ、Cache、Logger、既存Protocol、故障状態は保持。診断コードのメモリ不足を製品通常動作のメモリ不足と混同しない。長時間のメモリ挙動は別途未確認。

## 残っている事実・未確認事項

最大exchange時間は1,641 ms。LOG_CONT_STOP後のSD/ログ状態照会での遅延が先行試験と同程度に観測された。複数照会全体のPC時間であり、単一指令のMCU処理時間ではない。Logger停止後のservice_recovery→reinit経路はソースで確認できるが、遅延への寄与は未計測で原因を断定しない。

今回もCDC faultは解除しておらず、CDCの長時間受信停止は未解決。QR実機は明日取付け予定で未確認。EL/OL/FD、破壊を伴う通信異常、製品設定変更・ADC書込み・電源断耐性は今回未実施。製品PASS/FAILや全Open Issue完了とはしない。

## 証跡

- [回収後の集計](recovered_result.json)
- [全Transaction・実機状態](device_snapshot.json)
- [ATE要求・応答](requests.json)
- [一括出力失敗の原記録](device_stdout.raw)
- [分割回収出力](recovery_stdout.raw)
- [診断RAM片付け](diagnostic_cleanup_stdout.raw)
- [明日の修正引継ぎ](Tomorrow_Fixes_Handoff_20261123_Rev0.md)
