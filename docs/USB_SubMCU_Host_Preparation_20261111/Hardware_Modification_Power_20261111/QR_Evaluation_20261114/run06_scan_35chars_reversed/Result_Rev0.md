# Type_C2反転向き 35文字QR照合結果 Rev.0

日付: 2026-11-14／向きB（前回run05の向きAからプラグ反転）

## 結果

- 電源OFFでType_C2側QRプラグを反転する案内にユーザーが準備完了と回答。受信READY後に電源ON、受信0byte観測後にRST＋3秒待ち＋同じQR1回読取を案内し、ユーザーが完了と回答。
- qr-uart-20261114.1／A06FEA01012EC137、VID:E851／PID:1001、HID記述子63byteを取得。
- 60523byte、393レコード、HID report388件、連番0～392、1024件未満、エラーレコードなし。
- 期待35文字とPC側復元35文字が完全一致。期待値から別経路で生成したHID全388件とも一致。
- Alt＋テンキー5桁の35文字、Enter1回、キー解放まで取得。先頭NULは警告として保持。
- 向きAとBのHID入力列は全件一致。起動後msが異なるためrawファイル全体は別hash。
- 採取は92.828秒、最終受信後5秒無通信、送信0、終了時COM22閉。

[原文](scan_uart.raw)／[フレーム解析](scan.json)／[35文字照合](decoded_35chars_result.json)／[期待列による再照合スクリプト](verify_known_scan.py)／[採取結果](capture_result.json)／[両向き比較](../Both_Orientations_Comparison_20261114.json)。

これは既知QRを両向き各1回・RST後に読んだ確認。FW内文字列デコーダ、任意QR、連続・長時間読取、PCと機器の共存、電源投入のみの確実な起動、電気・保護の全受入を意味しない。Open Issueは維持。
