# Altデコード実機確認一覧 Rev.0

2026-11-14。qr-uart-20261114.2／基板A06FEA01012EC137、診断UART COM22・115200/8N1で実施。

|試験|確認結果|証跡|
|---|---|---|
|単回35文字|期待結果と一致|[詳細](run01_firmware_decode_single/Result_Rev0.md)|
|同一35文字を2回|期待結果と一致|[詳細](run02_firmware_decode_twice/Result_Rev0.md)|
|異なる35文字A→B|期待結果と一致|[詳細](run03_firmware_decode_different/Result_Rev0.md)|
|34文字不足→正常35文字|期待結果と一致|[詳細](run04_short_then_valid/Result_Rev0.md)|
|36文字超過→正常35文字|期待結果と一致|[詳細](run05_long_then_valid/Result_Rev0.md)|
|禁止文字入り→正常35文字|期待結果と一致|[詳細](run06_forbidden_then_valid/Result_Rev0.md)|

確認済み: 正常35文字の完成、読取間の状態復帰、文字数不足・超過・禁止文字の拒否と次読取への復帰。各試験の限定条件は詳細参照。全体受入完了を意味しない。

未確認: 終端欠落／timeout・切断復帰・長時間連続動作・文字種全網羅・正式親子UART／ATE・7355／2 Host。
継続課題: 起動先頭NUL 1 byte、電源投入だけでの起動差、量産給電保護。Open IssueをCloseしない。
診断容量1024件のため1起動2読取以内。追加試験は新たな受信準備とRST後に行う。現在の受信ポートは閉じている。
