# CSV列欠けの再現確認（2026-11-09）

## 結果

前回「SD CSVの列欠け」と報告したPARAMログは、SD原本では正常だった。COM6のraw REPLからCSV全体を一括HEX出力してPCへ回収する経路でバイト欠落が再現した。製品側LoggerのCSV生成不良とした見立てを訂正する。USB CDC、MicroPython出力、PC側受信のどの内部処理で欠落するかまでは未確定。

| ファイル | SD原本 | 以前のPCコピー | 今回の分割回収 |
|---|---:|---:|---|
| PARAM 20261109_174306.csv | 12657 byte | 12561 byte、96 byte不足 | SHA-256一致、ヘッダを含む201行すべて14列 |
| ERP 20261109_174034.csv | 8835 byte | 8803 byte、32 byte不足 | SHA-256一致、ヘッダを含む135行すべて14列 |
| 代表読出し／SC・D2／ローカル拒否 | 6356／6019／1311 byte | SD原本と一致 | すべて14列 |

PARAMの旧コピーは原本offset 8189から64 byte、12349から32 byteが欠落していた。前者はSP送信RAWのASCII末尾と列区切り・HEX先頭を含み、後者は別のATE記録の一部。元のPCコピーは上書きせず保持し、正常回収版は`_verified.csv`として別保存した。

同じPARAM原本を従来の一括HEX出力で3回回収した結果、PC側は12593／12593／12625 byteとなり、3回ともSD原本のSHA-256と不一致（不足64／64／32 byte）。ATEコマンドを送らない読取り操作だけで欠落を再現した。

正常回収版ではSP送信2件、応答2件、D5送受信3組の全10フレームのBCCが一致。項目別SP送信DATAは`PARAM_EVENT_ENABLE_0`の生成値と一致し、前・中・後のD5全100文字も一致した。ERPも全22フレームのBCCが一致し、欠けていた最終D1 Transaction行を正常に回収した。

## ATE実使用速度での確認

ユーザー指定は0.1秒に1コマンド送信・受信程度、それ以上の速度にしない。送信は前応答の受信完了を待ち、PC高分解能時計で前送信開始から101ms以上を確保した。

- 最終試験: COM20で117コマンド（D0/D1/D5、DATA/STATUS/INFO Query106件、試験開始終了・診断）。実測最短送信間隔101.0623ms。
- 通信正常、TEST_END=OK、Self CheckはTEST_LOG_DROP=OK、累積破棄0、SD OK、通信IDLE。
- SD `/sd/BANK_A/20261109_175842.csv` は14499 byte。ヘッダを含む239行すべて14列、取得したNF55フレーム6件のBCC一致。
- SDとPCのSHA-256は`92b6e1efe5a480e9abe98b8229fe02a18bba491fbc8ebbf7c93d6006dd295b29`で一致。回収スクリプト修正後の再回収でも同じサイズ・SHA-256を確認。
- 初回の100ms指定試験は旧PCタイマー／待ち処理で最短93msとなったため、指定条件を満たす根拠に採用しない。時計と待ち判定を修正して上記の最終試験を行った。初回記録も別ファイルで保持。

今回の速度・コマンド構成ではCSV列欠けとログ破棄は再現しなかった。長時間連続、別コマンド構成、SD状態の変化は未確認。以前の無間隔試験でPicoが報告した391件のログ破棄は別事象であり、PC回収欠落で説明しない。今後のATE実機試験は0.1秒以上の送信間隔と前応答受信完了を基本条件とする。

## 回収方法の対策と残事項

試験用回収スクリプトを256 byteずつの分割回収へ変更した。各ブロック長を確認し、SD側で計算した全体SHA-256とPC側計算値が一致したものだけを正常回収版として保存する。SD原本・過去のPCコピー・製品ファームウェアは変更していない。新たなSP書込みも行っていない。

LOGGER-CSV-01はPC回収経路の問題として記録を訂正し、内部の欠落箇所・恒久運用確認を残してOpen継続。LOGGER-BURST-01は実運用速度の追加証拠を記録しOpen継続。COM6の通常アプリを再開し、COM20のID応答を確認、両ポートを解放した。

## 証跡

- [PARAM原本照合・欠落位置](../temp/dev_acceptance_20261109_run01/csv_integrity_recheck.json)
- [他CSV監査と一括回収3回の再現](../temp/dev_acceptance_20261109_run01/audit_saved_csvs.json)
- [正常PARAM CSV](../temp/dev_acceptance_20261109_run01/param_20261109_174306_verified.csv)、[正常ERP CSV](../temp/dev_acceptance_20261109_run01/erp_20261109_174034_verified.csv)、[フレーム再解析](../temp/dev_acceptance_20261109_run01/verified_csv_analysis.json)
- [101ms以上のATE応答記録](../temp/dev_acceptance_20261109_run01/csv_100ms_strict_ate.json)、[CSV整合確認](../temp/dev_acceptance_20261109_run01/csv_100ms_strict_integrity.json)、[正常回収CSV](../temp/dev_acceptance_20261109_run01/verified_100ms_20261109_175842.csv)
- [修正した試験用回収スクリプト](../temp/dev_acceptance_20261109_run01/recover_focused_csv.py)

検証は実機回収の再現試験とATE/SDの整合確認。製品コード変更なしのためHost/Mock全体は再実行していない。
