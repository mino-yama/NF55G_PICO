# 直接指定ADの実装と確認結果

Date: 2026-11-26
Revision: Rev.0

ユーザー指定により、人が読んだ測定値を `AD_<TYPE>_<POINT>_<VALUE>` でATEから直接指定する方式を採用確定し、通常ATE経路へ追加した。測定Cacheを採用するCAL_WRITE方式も維持する。製品FW・原典は変更せず、実機への配置・書込み・デバッグは行っていない。

## 変更ファイルと目的

| ファイル | 変更内容 |
|---|---|
| src/calibration_write.py | TYPE／POINT／10進値の解析とfloat32変換、直接AD、Cache方式との共通送信、別AR、失効・成否不明・原文ログ。 |
| src/command_parser.py | AD直接指定を校正書込みの入口へ接続。 |
| src/main.py／src/config.py | 既存の診断条件を直接方式と共有する旨を日本語コメントへ反映。設定値の変更なし。 |
| tests/test_direct_ad.py | 新規10件の回帰テスト。 |
| docs/AD_Direct_ATE_20261126_Rev0.md | ユーザー確定方式、入力・応答・手順・現行診断条件・残確認事項。 |
| docs/ATE_Command_Master.md／docs/Cache_Master.md | 採用方式、実装入口、直接ADによるCache失効を追記。 |
| docs/Open_Issues.md | 直接指定方式の採用確定と製品側の残確認事項を区別。IssueのCloseなし。 |
| docs/Test_Specification.md／docs/CHANGELOG.md | 回帰確認範囲と結果を記録。 |
| docs/ATE_Command_List_for_Test_Program_Rev4_20261126.md／.docx | 直接方式を実装済みとして第10.6／14.18節に順序付き説明。PARAM_RESETの対象と現行応答終端も明記。旧Rev.3は保持。 |
| scripts/build_ate_command_list_rev3_docx.py | 版のファイル名を引数指定して、同じA3横形式で再生成可能にした。 |
| README.md | 最新版リンクをRev.4へ更新。 |

## 模擬確認

最終Host Unit／Mock NF55Gは567件成功、24.379秒。既存557件と直接ADの新規10件を含む。関連する直接ADと既存CAL_WRITEの16件も先に成功した。git diff --check成功。Rev.4のMarkdown表41個の列数と直接AD入口の掲載を確認した。

新規テストでは5 TYPE×2点の送信フレーム、負の小数、回路名・数値TYPEとP1/P2・数値Point、指数指定、入力不正・非有限値・overflow／underflowの無送信拒否を確認した。DMM接続・測定Cacheなしでの実行、別ARの読戻し、DATA／ARと同回路A/B測定値の失効、診断・試行・個体・BUSY gate、後続timeoutと旧比較元破棄、対象不一致応答、UART例外・Command Retry禁止、入力値と送信原文のログを確認した。

全回帰ログはリポジトリ内 `tmp/ad_direct_host_mock_20261126.log`。機器との実通信ではない。Wordの表示は確認用PDFへ出力して確認し、確認用PDFとPNGはtmp内に保持する。

## 未確認事項

現行の実機用入口はCALIBRATION_SAMPLE_ENABLED=True、現試行のD5照合でS1.14B／000001のサンプルに限定。通常ソース既定Falseは変更していない。診断T2=1000ms、ADのCommand Retryなし。

今回確定したのは人の読取り値をATEから直接指定する方式。製品の正式AD／AR契約、REF小数保持・係数反映・保持・正式T2・量産受入はOI-04／05／12／16～21で継続。全回路・全点の実機成立や量産承認を模擬成功から推定しない。
