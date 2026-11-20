# 電源投入前からのHost入力採取 試行8 結果 Rev.0

2026-11-20。COM22/Host GP1とCOM7/ATEを外部電源OFFから待受開始。WAITING_FOR_POWER_ON_CONFIRMATIONを確認して電源ONを案内し、ユーザー「投入完了」通知後にgateファイルを作成、治具IDとEXT_QUERYを各1回実行した。

## 確認事実

治具IDはNF55G_PICO_FIXTURE,Rev.0。EXT_QUERY 2000 *IDN?はTIMEOUT/AMBIGUOUS=0。Host入力線は77byteを採取。先頭00 00の2byteに続き、75byteのCRC/形式正常なH（session=CA0039AA6F16E52D0000000000000000）があった。余分な2byteとHの間にCRLFはない。捕捉例外なし。両ポート解放済み。Q/SCPI/レンジ/READ/NF55G通信/自動再送/Flash変更なし。

## C engine再現と限界

同じ実原文を変更前のrelay_host_uartへ入力すると、CRLFまで77byteを累積してx1_decodeが不正形式として破棄し、h応答を出さない。変更前回帰2件は期待どおり失敗（実原文の全78分割境界でhなし、親縦通しも無応答）。この受信不具合を再現した。00 00が発生する電気的起源/波形は未確認で推測しない。実機Host内部で同一データが受信されたことと修正後の実機中継成立は、書込み後試験で確認する。IssueはOpen維持。

[起動からの受信原文](host_rx.raw)／[decode結果](Host_RX_Capture.json)／[ATE送受信](Capture_Result.json)／[修正と回帰テスト](../Host_UART_Sync_Fix_01/Result_Rev0.md)。
