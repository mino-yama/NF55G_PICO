# Cache / Invalidation / Post-Action Confirmation Master

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.0

## Cache list
DATA, STATUS, INFO, BC, AR, D2, D3, D4, EL_01, EL_09, EL_17, EL_25, OL_01, OL_09, OL_17, OL_25, OL_33, OL_41, OL_49, OL_57, FD.

Power-on: all INVALID.

## Rules
- Query never triggers NF55G communication.
- Refresh invalidates target before transaction.
- Refresh success -> VALID.
- Refresh failure -> remains INVALID.
- Never restore old cache after failed refresh.
- VALID means last fetch/decode was successful, not that the data is current now.
- Control response status does not update STATUS cache.
- 2026-11-11: 受付済みTEST_STARTごとに全製品CacheをINVALIDにする。再STARTでも同じ。拒否されたSTARTでは失効させない。自動Refreshは行わない。QR受信状態とログ用S/Nも新試行へ引き継がない。

## Master
| Command | Success VALID | Success INVALID | Post |
|---|---|---|---|
| DATA_REFRESH | DATA | - | DATA query |
| STATUS_REFRESH | STATUS | - | STATUS query |
| INFO_REFRESH | INFO | - | INFO query |
| SP | - | DATA/STATUS/INFO | INFO_REFRESH |
| RP | - | DATA/STATUS/INFO | INFO_REFRESH |
| SE | - | DATA/STATUS | STATUS_REFRESH |
| SC | - | DATA/STATUS | DATA_REFRESH |
| SS | - | DATA/INFO | INFO_REFRESH |
| SL | - | DATA | DATA_REFRESH |
| BC START | BC | DATA/STATUS | BC query |
| BC STOP | - | BC/DATA/STATUS | STATUS_REFRESH |
| CN | - | DATA/STATUS | STATUS_REFRESH + ext current |
| CF | - | DATA/STATUS | STATUS_REFRESH + ext current |
| BE | - | DATA/STATUS | STATUS_REFRESH + ext 12V |
| BF | - | DATA/STATUS | STATUS_REFRESH + ext 12V |
| OR | - | DATA/STATUS | STATUS_REFRESH + ext 12V |
| D2 | D2 | DATA | optional DATA_REFRESH |
| D3 | D3 | DATA | optional DATA_REFRESH |
| D4 | D4 | DATA | optional DATA_REFRESH |
| EL | target block | - | EL query |
| OL | target block | - | OL query |
| CD | - | DATA/STATUS/BC | DATA+STATUS_REFRESH |
| CL | - | all EL/OL | EL/OL refresh |
| AD | - | DATA/AR | AR_REFRESH |
| AR | AR | - | AR query |
| FD | FD | old FD | none |
| FU | - | - | ERR:FU_DISABLED |

## Error policy
- Parser rejection: cache unchanged.
- PME/SQE/CME/MCM: existing cache generally unchanged; refresh target remains INVALID if refresh already started.
- ACK_TIMEOUT/RESP_TIMEOUT/final BCC/FRAME/UART/COMM: apply ambiguous invalidation same as success-invalidates.
- HWE: DATA/STATUS invalid at minimum.

## QR Cache追加要件（2026-09-18、未実装）
ATEのPico専用読取開始コマンド後に取得したQR情報をPico側にCacheし、後続のNF55G書込みとログファイル名生成に利用する。
これはNF55Gから取得したINFO Cacheとは別の情報源であり、QR受信だけでINFOをVALIDにしない。
正式Cache名、フィールド、検証条件、再読取・timeout・製品交換時の扱いはOI-23で確定する。既存Hard Rulesの完全Decode・INVALID方針を満たす設計とする。
詳細: [QR読取要件](QR_Reader_Requirements.md)。

### QR原文と解析値（2026-09-18追加、未実装）
QR原文を保存し、ATEの解析指示により版数・製造年・製造週・製造号機等を分解・検証して各項目をCache保持する。
原文取得と解析値の有効性を区別し、部分Decodeや桁数・文字種・範囲不正の結果をVALIDな書込み用Cacheにしない。
ATEは原文取得/解析値取得の各指示で内容を確認する。QR情報とNF55G読出し情報の一致比較は製品PASS/FAIL判定ではない。
具体的な世代管理、再読取時の無効化範囲、照合対象読出しの識別はOI-23で確定する。

### SSへの紐付け方針（2026-09-18ユーザー指定）
読取値の保存Cache名は後日決定し、NF55GのSSコマンドへ紐付ける。各フィールドのSS DATAへの対応は未確定のまま保持する。ATEの明示指示による書込みと、既存SSのDATA/INFO無効化規則を維持する。今回の指定のみではCache追加やSS連携を実装しない。

## 2026-09-26 QR単独試験のRAM Cache
QRReceiverのraw/fields/stateは試験専用で、正式Cache名の確定ではない。開始時に旧値を無効化し、35文字+終端の完全受信・文字種確認後に6項目を同時公開する。
開始前/完了後の入力は破棄。失敗後は旧VALIDへ戻さない。文字列の先頭ゼロを維持。SS/INFOへの転用なし。

## 2026-11-09 EL／OL／FD読出し入口

EL／OLは開始番号に対応する1ブロックだけを開始時にINVALIDにし、START_NO一致と全8件Decode成功後にVALIDへ更新する。Queryは該当ブロックだけを参照し、他ブロックのVALIDを取得済みとは扱わない。FDは最新1回分の64文字を保持し、次のFD_READ開始時に旧値をINVALIDにする。通信失敗・Decode失敗後に旧値を復元しない。不正要求はCache変更前に拒否する。Queryから通信しない。CL後は全履歴がINVALIDとなり、必要ブロックを明示再取得する。ERPと併せた実機確認は後日、今回未実施。

2026-11-09 項目別PARAM: SPの既存無効化規則を共用し、成功／ambiguousでDATA／STATUS／INFOをINVALIDにする。PME／SQE／CME等の明確な拒否とParser拒否ではCacheを保持する。未指定項目は原典の最大値による変更なし指定で送り、INFO Cacheからの自動読出し・自動Refresh・旧値補完は行わない。

2026-11-09 BC実装: STARTは結果更新を伴うため旧BCを処理開始時にINVALID化する。START成功でDATA／STATUSをINVALID、全30文字・8項目Decode成功時だけBCをVALIDにする。STARTのSQE等でも旧BCを戻さない。STOP成功／ambiguousでBC／DATA／STATUSをINVALIDにし、STOP応答からBCを有効化しない。明確なSTOP拒否ではCache保持。BC Queryは保存済み結果のみ。D0結果やControl内Statusからの昇格なし。

## 2026-11-09 SL正式入口のCache契約

LIFE_SET_<VALUE>／LIFE_SET_RAWは既存SL規則を使用する。成功／ambiguous時はDATAだけINVALID。明確なPME／SQE／CMEでは旧Cacheを保持する。SL応答や指定値からCacheをVALIDにしない。後日の範囲外試験では、拒否時も明示DATA_REFRESHを行ってBATT_DEG_TOTAL?を取得し、旧Cacheを実読戻しと扱わない。他Cacheの規則変更なし。
