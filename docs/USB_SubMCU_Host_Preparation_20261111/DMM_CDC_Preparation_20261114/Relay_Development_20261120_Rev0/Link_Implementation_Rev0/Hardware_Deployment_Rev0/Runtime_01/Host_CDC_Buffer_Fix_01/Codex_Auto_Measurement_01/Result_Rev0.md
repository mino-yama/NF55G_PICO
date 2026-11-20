# Codex直接AUTO測定 結果 Rev.0

2026-11-20。ユーザーが電圧/配線を固定しCodexへ送受信を依頼し、シリアルモニターを閉じCOM7使用可能と回答。CodexがCOM7/57600 8N1、flowなし、DTR/RTS OFFから実行。

治具/7355 ID、DCV、連続OFF、開始状態のAUTO/CONFと機器エラー0を確認。IMM、トリガ1、サンプル1、遅延0を明示し、設定後Query/OPCを受信。AUTO ONの読戻し1とエラー0の後、READ?を1回送信。原文-02.91185E+00+CRLF（15byte）、測定値-2.91185Vを受信した。測定前後CONFはVOLT +1.999999E+01,+1.000000E-06、終了エラー0。全要求/原文を保存しCOM7解放済み。再送/電源/Flash/NF55G操作なし。

精度/製品PASSやレンジ指定の意味は判定しない。続いて同じユーザー固定入力でRANG20/200指定とAUTOの3条件比較へ進んだ。

[全送受信/時刻/原文/hash](Capture_Result.json)／[受信原文](all_rx.raw)。
