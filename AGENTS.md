# AGENTS.md
# NF55G Pico 2 試験治具 - Codex 開発ルール
Revision: Rev.1
Date: 2026-09-07

## 1. 目的
本リポジトリは、Raspberry Pi Pico 2 を用いた NF55G 試験治具ソフトウェアを開発するための正本である。
Codex は本ファイルを最上位ルールとして扱い、仕様書・原典資料・Open Issues と矛盾する変更を独断で行ってはならない。

## 2. 最上位 Hard Rules
1. RW11用電源通信仕様書 r1（`reference/RW11用電源通信仕様書r1.pdf`、GVT-284454-001-00、初版 2026/9/4）を基本仕様とする。D6は過去比較用として保持する。
2. 暫定 NF55G FW と r1 仕様の差異を、Pico 側で勝手に吸収しない。
3. 未確定事項は `docs/Open_Issues.md` に残し、Codex 判断で確定・Close しない。
4. `FU` は試験治具から絶対に NF55G へ送信しない。ATE から `FW_UPDATE` を受けても `ERR:FU_DISABLED` を返す。
5. Pico は製品 PASS/FAIL を判定しない。Pico は通信・変換・Cache・Logger・RTC を担当し、最終判定は ATE 側が行う。
6. ATE 個別 Query から自動 Refresh を行わない。
7. Control/SET/CLEAR 後は指定 Cache を INVALID にする。
8. Control Response 内の Status を `STATUS` Cache へ昇格させない。
9. D0 内の Status を `STATUS` Cache へ昇格させない。
10. D0 内の Manufacturing/Parameter を `INFO` Cache へ昇格させない。
11. EB Event で `STATUS` Cache を更新しない。
12. Command Retry と Response Retry を別管理する。
13. Pico から NF55G Response に対して送る NAK は plain `0x15` とし Reason Code を付けない。
14. Pico 側 Command Retry 最大回数は 1 回。
15. `ACK_TIMEOUT`, `RESP_TIMEOUT`, 最終 BCC/FRAME 異常等で実行成否不明の場合は `ambiguous=True` とし、関連 Cache を安全側で INVALID にする。
16. Protocol SUCCESS は製品動作成功/PASS を意味しない。
17. ATE を最優先する。USB 保守コンソールや SD Logger が量産 Timing を阻害してはならない。
18. NF55G Transaction は常に 1 件のみ。同時実行禁止。
19. USB CDC 詳細実装は初期開発範囲外。ただし将来共通 Command Core を利用できる構造とする。
20. Logger/SD/USB 出力は NF55G 通信 Timing を阻害しない。通信中の SD write/flush は禁止し RAM Queue を使用する。
21. Refresh 開始時は対象 Cache を先に INVALID にする。失敗しても旧値へ戻さない。
22. Partial Decode の結果を VALID Cache に保存しない。
23. 仕様変更時は Code / Test / Docs / CHANGELOG を同時更新する。
24. 原典資料を勝手に書き換えない。
25. Open Issue の設計回答を推測しない。

## 3. 優先順位
1. 本 `AGENTS.md`
2. 最終 NF55G 仕様資料
3. RW11用電源通信仕様書 r1（初版 2026/9/4）
4. `docs/ATE_Command_Master.md`
5. `docs/Data_Decode_Master.md`
6. `docs/Cache_Master.md`
7. `docs/Protocol_State_Machine.md`
8. `docs/Software_Module_Interface.md`
9. `docs/Logger_SD_Spec.md`
10. `docs/Test_Specification.md`
11. `docs/Open_Issues.md`
12. 暫定 NF55G FW source（差異確認用）

## 4. Codex の変更手順
- 変更前に関連仕様を読む。
- 変更内容を小さな単位に分ける。
- Host Unit Test / Mock NF55G Test を実行する。
- 失敗時は仕様を変えず、まず実装を修正する。
- 仕様上の矛盾を見つけた場合は Open Issue を追加し、人間確認を求める。
- 完了時に変更ファイル、変更理由、実行 Test、Test 結果、残 Issue を報告する。
