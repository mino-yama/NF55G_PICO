# 固定接続・cold-start第1回＋20回連続読取 結果 Rev.0

日付: 2026-11-14（JST）

## 確認できた事実

- ユーザーは電源OFFで固定配線完了と回答。受信READY後、外部5VのみON、RST/BOOTなしを指示し「電源ONした」と回答。その後A→Bを10組／20読取指示し「読み取り完了」と回答。
- 起動版qr-fixed-20261114.1、個体A06FEA01012EC137。boot／board_id各1件、途中再起動・切断・再mountの記録なし。
- 起動段階: 24ms待機開始、3037ms configure直前、3048ms configure成功、3062ms tuh_init成功。HID mountは3606ms。RSTなしで自動認識した。
- 完成kind12がちょうど20件。検証済みAとBの順序を交互に各10件、全件35 byte完全一致。余分な完成出力・前回断片混入なし。
- 最初の完成102721ms、最後164425ms、20読取の完成間隔全体61.704秒。最終heartbeat166575msで完成数20・HID報告累計7760を確認。HID原文自体は本版では送信しない。
- heartbeat164件でmain回数とPIO frame数が継続増加、drop最大0。初期化失敗・receive失敗・oversize・decodeエラーは0件。
- UART受信29723 byte／193レコード、連番0～192。64件FIFOを超えて排出・再利用できた。旧1024件を超える入力HID数を処理したが、新モードは原文報告を省略するため、送信レコード数と入力HID数は区別する。
- 原文先頭NUL 1 byteは継続。原文保持、解析時のみ明示指定で分離し、UART原文全体の形式正常とは判定しない。
- 取得は完成20件到達後3秒で終了、ポート閉。送信0 byte。
- 原文SHA-256: c2ce8089a1be7e20eb1e5e7f8ea48658e9e6928c972dde5ec1d70744bd78c7d3。

## 判定範囲・次工程

今回1試行で、QR固定接続の電源ONからRSTなしで認識し、20回連続読取が成立した。3000ms待ちが原因対策として確定したとはしない。複数回のcold-startと10分以上の連続稼働は未実施。ユーザーの限定目標に対する第1回成功として扱い、全体受入・量産保証・Open Issue Closeはしない。

次は同じ固定配線のまま外部電源OFFで10秒以上待ち、別受信を準備して第2回cold-startを確認する。Type_C1未接続を維持し、QR／UART配線は抜き差ししない。

[原文](scan_uart.raw)／[取得条件・終了](capture_result.json)／[全レコード解析](Parsed_Rev0.json)／[20件照合・heartbeat](Comparison_Rev0.json)／[読取前の起動検査](Startup_Inspection_Rev0.json)
