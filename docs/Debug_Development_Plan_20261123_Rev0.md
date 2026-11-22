# 11月23日 デバッグ項目・手順・開発案件 Rev.0

作成: 2026-11-22。実施予定: 2026-11-23。案件: NF55G Pico試験治具。

## 競合確認の結論

今回のソース調査と日程整理は文書/記録の追加のみで、既存コード・改善・候補FWを変更していない。作業ツリーの診断候補.22.3について、保存manifestの全12ソースhashと固定UF2のhashが一致した。今回の作業による候補の差替え/破損は確認されなかった。[照合記録・18ソースの基準hash](Debug_Development_Plan_20261123_Rev0_Baseline.json)。

ただし、これから行うRST実装は診断と同じファイル/処理に触るため、「競合箇所がない」「実行時も無干渉」とはまだいえない。下表の機能を保持して統合し、試験で確認する。診断のみの.22.3とRST追加版は別バージョン/別成果物として保存し、原因調査用の比較基準を残す。

| 既存変更/案件 | RSTと重なる場所 | 保持・検証する内容 |
|---|---|---|
| CDC下位診断.22.3 | relay_main.c、relay_host.c、CMakeLists.txt | TIMEOUTのRX/T/C/末尾、I/N/D/EP/H/K/L、guardと受信wrapperのlink/RAM配置を保持 |
| idle切断復帰 | relay_host.c、external_instrument_link.py | 未送信LINK_NOT_READY/ambiguous=0の次回受付と、送信後切断のambiguous fault保持を維持 |
| SD排出飢餓改善 | src/main.py、同じATE scheduler | 最終応答後のSD排出機会を維持。RST待ちをblockingループにせず、ATE/NF55G通信中のSD禁止を維持 |
| X1フレーム/親リンク | relay_wire、Python contract、親link | H/Qの既存意味、CRC/上限、nonce/要求相関を保持。管理を通常Q/SCPIと混在させない |
| QR実機取付け | 親GP8/9、QR用HOST FW/PIO | 測定器用GP12/13・SM4/5と区別。QR FWへ測定器用UF2を配置しない。資源・IRQ・配線を照合 |
| ADC/AD/AR | 将来のmain/dispatcher/Cache拡張 | 正式契約未確定の書込み・照合機能をRST改修へ混ぜない |

Git作業ツリーには既存の未コミット変更/未追跡ファイルがある。HEADへの復帰や旧sourceの上書きで整える作業はしない。別ビルドでも同一ファイル名のUF2が生成されるため、保存先/版/hashを区別する。

## 22日終了時点の確認結果と未完了

- 診断用HOST: 直近実機記録.22.2、初回IDNでTIMEOUT_RX0_T1_C0_XNONE|1。候補.22.3は未配置/未受入。固定UF2 SHA-256は7a817134cffdf124197c68d958cfe9b5a96a98dbe308c8d5dd5a63e121e98ef2。
- [ATE/SD単独](ATE_SD_Check_20261122_181740/Result_Rev1.md): 100 burst、109 exchanges、419応答、不正入力4条件後の復帰、drop0/Queue0、CSV820行/hash一致。NF/CDC通信は送っていない。単独合格と複合負荷合格を区別する。
- [RTC/STATUS Cache](RTC_Cache_Check_20261122_183202/result.json): RTC進行/OSF=false、Cache INVALID時37照会・VALID時74照会、明示D1一回、Query由来NF送信0、Queryでmetadata不変。他Cache不変。RTC時刻の高精度校正を保証する試験ではない。
- 記録上の最終状態は親停止・測定器PIO SM4/5停止・CDC fault保持。QRは未接続、23日取付け予定という記録。現在の電源/配線/COMは本計画作成時に再確認していない。
- 旧引継ぎの「親修正未配置」は当時の記録で、後続の[統合結果](Parent_Host_Integration_20261122_01/Result_Rev0.md)で進展済み。古い引継ぎだけを根拠に旧候補を再配置しない。

## 開発案件一覧と優先順位

| ID | 案件 | 23日に行うこと | 完了/継続の区切り |
|---|---|---|---|
| DEV-23-01 | 測定器HOST通常RSTコマンド | 既存UARTに管理受付/個体照合/通常再起動/親対象リンク再照合を実装 | PC試験・ARM build・実機で新nonce確認。通信再開可否は別判定 |
| DBG-23-01 | USB受信0 byte切分け | 変更なし.22.3の基準観測とRST統合版の診断保持確認 | I/N/D/EP/H/K/LとA/T/R/Eを記録、停止層を絞る。TIMEOUTなら停止して記録 |
| DBG-23-02 | QR取付け・単独入力 | 山田による取付け後、配線/個体/正常・不正QR/試行分離/ログ確認 | 既存仕様の入力成立、前試行残留なし。未確定の正式API/SS紐付けは確定扱いしない |
| DBG-23-03 | ATE/NF55G/CDC/SD/RTC共存 | 単独動作が成立した構成で段階的に再開 | 各応答相関・Retry・drop・Queue・CSV一致を確認 |
| DEV-23-02 | USB受信停止の再現/修正候補 | 観測に応じてNAK/PID/受信未投入/eventをPCで個別再現 | 原因を再現した候補だけ別版で修正。SDK/vendor一括更新なし |
| HW-23-01 | 給電維持・信号切断・外部操作 | 山田がハード検討 | 条件が決まってからBOOTSEL書込み運用へ反映。通常RST開発とは独立 |
| HOLD-01 | BOOTSELコマンド | 検討継続、実装日は未指定 | 給電維持PC接続の条件と併せて実装計画化 |
| HOLD-02 | 測定Cache→AD/AR個別照合 | 設計確認事項を維持 | ARの小数欠落・正式API/T2/製品FW等の回答後。実機書込みを行わない |
| HOLD-03 | 自動WDT/量産自動復旧/QRのRST | 今回の通常RSTへ追加しない | 別実装・別受入。QR管理RX実配線/実装は未確認 |

DEV-23-01はユーザー指定の23日実装対象。DBG-23-01/02を重点デバッグとし、DBG-23-03は前提が成立した範囲で行う。一日で全件完了とは約束せず、停止条件に達した案件は証拠を残し、独立して行える案件へ進む。

## 手順1: 開始時の基準固定（実機送信前）

1. AGENTS.md、Open Issues、本計画、[通常RST提案](USB_Host_Reset_Study_20261121/Development_Reset_Bootsel_Command_Proposal_20261122_Rev0.md)、[受信経路調査](Parent_Host_Integration_20261122_01/USB_Bulk_IN_Source_Trace_20261122_Rev0.md)を参照する。
2. git statusと上記基準hashを比較。差があれば変更理由を照合し、既存変更を保持して23日の基準manifestを別名で保存する。
3. 親69f7d45962cfdfad、測定器HOST BFCF2EDB84B0B37Fを実機IDで確認。QR HOSTは接続/個体を別に確認する。COM6/7/22等の過去番号を固定前提にしない。FW版・親source hash・runtime/Logger/PIO状態を記録する。
4. .22.3の固定UF2・ELF・manifestを比較基準として保持。23日の候補/実機退避/試験rawは本案件内の新規実行フォルダへ保存する。実機親には有効化差分がある可能性があるため、workspaceのmainを丸ごと配置しない。

## 手順2: RST実装とPC検証（実機状態に依存せず進める）

1. 管理要求/応答、対象METER、起動世代/個体照合、BUSY拒否、期限と結果不明の扱いを小さな実装仕様にまとめ、Code/Test/Docs/CHANGELOGを同時更新する。既存契約のH/Qを書き換えて代用しない。コマンド名は提案段階なので確定内容を一覧に記載する。
2. 管理受付を通常fault/USB readyのgateより前へ設ける。FAULT・USB未接続でもHOSTが応答可能なら受付可能、要求中はBUSY。RSTは通常再起動に限定し、機器本体のRESET/SCPI/BOOTSELへ転送しない。
3. ACK送出と再起動を有限期限の状態機械にし、親全体を止めない。古い/重複要求を実行せず、ACK欠落でも自動再送しない。受理と再起動完了を分ける。
4. 親側は対象リンクの旧session/パーサー/キューを整理し、同一個体の新nonceを確認する。既存ambiguousやCache INVALIDを安全側で保持し、旧要求を再送しない。
5. 実C/親Mockで正常・FAULT・USB未接続・BUSY・CRC不正・旧nonce・別個体・重複・ACK欠落/送出期限の各条件を検証する。通常Q本文内のRESETで誤実行しないことも確認する。
6. `.venv/Scripts/python.exe -B -m unittest discover -s tests -v`で全Host Unit/Mockを実行し、23日のログへ保存する。既存467件に加え新規試験を含む件数/結果を記録する。
7. 固定SDK2.2.0でARM buildを行う。既存build scriptはbuild先と版情報を更新し得るので固定候補を保護し、新版UF2/ELF/版/hashを別保存する。CDC guardと受信wrapperの実呼出/RAM配置、診断文字列、RST APIのlinkを確認する。

## 手順3: 診断基準とRST実機確認

1. 可能なら変更なし.22.3で先に1回のIDN基準観測を取得する。親停止・PIO入力化→電源/信号の現行書込み条件→対象照合/全Flash退避/verify→固定候補load/verify→通常配線復元/起動照合の順。手動BOOTSEL等の初回導入操作は既存手順に従い、山田のハード案を推測して同時給電しない。
2. 基準版を起動できない場合は、その理由を記録し、PC上のRST実装を先行する。RST統合版だけで受信が改善しても原因修正とは判定しない。
3. 新nonce/FW/対象を確認後、`EXT_QUERY 2000 *IDN?`を明示1回。ATEとHOST rawを同時記録し、A/T/R/E・I/N/D/EP/H/K/Lを保存する。TIMEOUT後に同じ起動でQuery/READを繰返さない。
4. RST統合版を別版として退避/配置/verifyする。通信idleからRSTを1回要求し、ACK→同一個体/新nonce照合を確認する。親全体の再起動・NF55Gへの送信・機器設定変更が発生していないことを確認する。
5. USB未接続状態のRSTと、既に確保したFAULT状態からのRSTを条件別に確認する。FAULTを作るためだけの未計画な抜線や測定再送は行わない。実機で作れない条件はMock結果と区別して残す。
6. 再起動確認とUSB READY/機器応答の再開確認を別項目とする。旧機器応答境界が不明な場合はRECOVERY_REQUIRED維持。RST成功だけで測定Cache/製品PASSを成立させない。

## 手順4: USB受信0 byteの観測分岐

| 観測 | 次に調べる対象 |
|---|---|
| I/N増加・D0 | INは動きNAKを観測。機器が応答を用意する条件/時刻を確認 |
| D増加・engine RX0 | 0 byte DATAも区別し、返却長/期待PID一致/完了eventを追う |
| I0・H0 | EP特定、初回/次回IN投入の結果、上位busy/claimed、完了event/FIFOを確認 |
| I0・H1 | root接続/suspend、timer、abort、計数の対象/開始時刻を確認 |
| 下位actual>0・engine RX0 | 現要求との時刻相関、CDC callback/FIFO、期限先行判定を確認 |

必要箇所だけ追加観測/Mockを別候補へ作る。toggle強制反転、無条件IN再投入、fault解除による見かけの復帰を先に加えない。診断によるTiming変化も残す。

## 手順5: QR取付け後の単独確認

1. 山田の取付け完了後、無給電で配線/給電系統/基板個体を照合し、計画した条件で起動する。親GP8/9のQR経路と測定器PIO/USB GPIOを区別する。
2. QR既存FW/設定と受信経路を確認。既知35文字QRを1回読み、原文・長さ・6項目の分解結果を既知値と照合する。機器により終端/出力方式が異なるため、既存仕様/実FWを基準にする。
3. 不正長/文字・部分入力/timeout・次の正常入力を条件別に確認し、前試行の原文/解析値/番号が残らないことを確認する。試行開始/終了とログへの番号対応も確認する。
4. 正式なQR Cache/SS紐付け・ATE名称が未確定な部分は既存の試作入口での受信結果と区別する。QRを読んだだけでNF55GへS/N/SS等を書き込まない。

## 手順6: 段階的な共存・ログ照合

1. ATE/SD単独とRTC/Cacheは22日の成功記録を基準にし、関連コードを変更した時に回帰する。
2. CDCが通常応答を取得できる構成で、まず単発IDN→ユーザー指定設定の確認→明示READ一回を別段階で確認する。レンジや設定を自動選択/復元しない。
3. 正常ならREAD/NF55G D1/SD/RTCを含む50回の有限共存試験を行う案とする。応答相関・D1 Retry・SD drop/Queue/CSV/hashを確認し、最初の異常で停止する。50回成功は長期安定性/量産受入の完了ではない。
4. QR単独合格後にQR入力を共存条件へ追加する。連続負荷500回等は初回TIMEOUTの切分け後に段階拡張する。2秒→10秒の単純延長だけでは既存の停止を解消しなかった履歴を引き継ぐ。

## 停止条件・記録・終了時

対象ID/版/hash不一致、BUSY/FAULTの予期せぬ解除、成否不明、drop増加、応答相関不一致、旧データ混入、電源条件不明では対象試験を止める。製品合否をPicoで判断せず、NF55G FUは送らない。旧記録の欠落だけで実施/原因を断定しない。

各runは個体/FW/source/UF2 hash、開始状態、親/HOST nonce、操作1回ごとの時刻、ATE/HOST raw、結果/ambiguous、機器設定の前後、CSV/hash/drop/Queue、終了状態を保存する。変更ファイル/理由・Host Unit/Mock結果・ARM検証・実機結果・残Issueを更新する。試験用変更は実施前に復元対象を特定し、復元後も確認する。

本計画作成時の実施は差分/依存箇所の読取り・hash照合・文書作成のみ。テスト再実行、FW build/配置、実機通信、スケジュール自動実行は行っていない。関連IssueはOpenを維持する。
