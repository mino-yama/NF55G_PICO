# 固定接続cold-start第2回 結果 Rev.0

2026-11-14（JST）。第1回後に固定配線のまま外部電源OFFで10秒以上待つ指示を行い、ユーザー「準備完了」。受信READY後に電源ONのみ、RST/BOOT・読取なしを指示してユーザー「完了」。認識確認後QR Aを1回だけ読み、ユーザー「完了」。

## 実機事実

- qr-fixed-20261114.1／A06FEA01012EC137。boot・board_id・mount各1件、途中再起動・切断なし。
- 待機phase1=24ms、configure前3037ms、configure成功3048ms、Host init成功3062ms、HID mount3606ms。RSTなしで自動認識。
- 起動後50488msにQR Aの完成文字列1件。35 byteが期待原文`Aa0-012345678901234567890123456789Z`と完全一致。
- heartbeat51件でmain/frameが継続増加、drop最大0。最後53575msで完成1・HID報告388。decode/init/receive/oversizeエラーなし。
- UART9395 byte、61レコード連番0～60、送信0。完成後3秒で取得終了・ポート閉。
- 先頭NUL1 byte継続。原文保持、解析時のみ明示分離。原文全体の形式正常とは判定しない。
- 原文SHA-256: `02edfdb1322f810ddfd0b7d8e346b4fad76658de595306418f067409d25d49cb`。

第2回も固定QR接続の電源ONからRSTなしで認識・正常読取が成立した。電源投入は現時点で2試行中2成功。起動待ちによる改善の再現例であり、原因特定・量産保証・全体受入・Open Issue Closeとはしない。
次は第3回cold-startと10分以上稼働中の読取を確認する。FW変更・再書込みなし。

[原文](scan_uart.raw)／[取得終了](capture_result.json)／[解析](Parsed_Rev0.json)／[照合](Comparison_Rev0.json)／[読取前起動検査](Startup_Inspection_Rev0.json)
