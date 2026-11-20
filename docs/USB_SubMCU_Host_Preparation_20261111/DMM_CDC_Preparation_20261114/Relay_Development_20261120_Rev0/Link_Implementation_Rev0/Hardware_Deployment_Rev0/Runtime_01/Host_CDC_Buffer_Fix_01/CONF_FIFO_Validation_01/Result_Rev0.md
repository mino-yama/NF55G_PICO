# .3累積Query実機検証 結果 Rev.0

2026-11-20。ユーザーの通常接続復帰・7355/外部電源ON・シリアルモニター終了の完了後に実行。

## 確認事実

COM7 ELECOM 056E:5004、57600/8N1、flowなし、DTR/RTS OFF。治具ID照合後、IDN/FUNC/INIT:CONT/AUTO/CONFの5Queryを12周（計60件）実行。最後にSYST:ERR?を1回記録。ATE要求総数62件、機器応答合計1035byteで256byte FIFOを累積で複数周する量を受信。各応答の宣言長/実長/CRLF/書式/機種と、同じQueryの原文一致を全周で確認。全件成功、再送なし。COM7解放済み。

復号値: FUNCは引用符付きVOLT:DC、INIT:CONTは0、AUTOは1。CONFは全12回とも

"VOLT +1.999999E+01,+1.000000E-06"

とCRLFの36byteで一致。エラーは+0,No errorとCRLF。先行の999ET...という崩れは今回再現しなかった。設定変更/ABOR/READ/測定/NF55G通信は行っていない。

## 結論と限界

SDK実FIFOで確定した64byte確保/256byte初期化の不一致を修正した.3で、実機累積Queryの原文保持を確認した。ソフト回帰453件、ARM build/Flash verifyと合わせて修正後の確認を実施。

今回のAUTO=ON/約20V読戻しは現在の観測であり、前回AUTO=OFF/RANG20後と同じ条件ではない。固定20Vへの切替や前面レンジ一致、測定精度/測定動作の成功とは扱わない。USB-CDC-RANGE-01とUSB-RELAY-CDC-BUF-01等は人間確認なしにCloseせず検証結果を追記する。次はユーザーがAUTO OFF→読戻し、RANG20→CONF→SYST:ERR?を各応答後に逐次送信し、前面表示を併せて確認する。範囲の独自変換/機器設定の自動補完は行わない。

[全Query/原文/時刻/hash](Capture_Result.json)／[全ATE受信](all_rx.raw)。
