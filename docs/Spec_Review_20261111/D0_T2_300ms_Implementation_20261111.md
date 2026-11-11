# D0 T2の300ms変更と検証記録

日付: 2026-11-11

実機確認追記（同日11:15 JST）: COM6の既存治具へconfig.pyのみ配置し、PC／Pico hashと実行中のT2=300msを確認。COM20でD0正常系10回がすべてOK、ACK後完全応答180～182ms、再送0。SD／PC CSV hash一致、破棄0、自己診断正常。通常待受復帰・COM解放済み。[実機結果と証跡](Hardware_D0_T2_300ms_Result_20261111.md)。以下の未配置・未実機記述は実装時点の履歴。量産全条件・実機異常系は未確認でOI-02はOpen継続。

ユーザーから、通信r2で300msへ統一されたD0のT2を先に修正する指示を受け、現行コードの600msを300msへ変更した。有効ACK受信後から応答を待つ時間であり、ATE全体の待ち時間ではない。

## 採用範囲

通信r2事前確認版（2026/10/19）p.17／28のD0 T2=300msだけを採用する。AGENTS.mdへこの部分採用を明記した。その他の基準はr1を維持し、T1=200ms暫定、他コマンドのT2、Command Retry最大1回、Response Retryとの分離、Cache契約は変更しない。

今回の修正はPC側リポジトリに反映した。Picoへの配置・製品への送信は行っていない。

## 変更ファイル

| ファイル | 変更内容と理由 |
|---|---|
| [src/config.py](../../src/config.py) | T2_D0_MS=300とし、日本語コメントにr2とユーザー指定の根拠を記載。nf55_command.pyのDATA_REFRESH定義はこの定数を参照するため、経路変更は不要 |
| [tests/test_read_cache_integration.py](../../tests/test_read_cache_integration.py) | 既存の送信契約を300msへ更新し、3件の境界・異常系を追加 |
| [AGENTS.md](../../AGENTS.md) | Rev.2。基本仕様にD0 T2だけのr2部分採用を明記 |
| [README.md](../../README.md) | 部分採用と現行D0 T2=300msを記載 |
| [ATE_Command_Master.md](../ATE_Command_Master.md) | DATA_REFRESHの表と送信契約を300msへ同期 |
| [Protocol_State_Machine.md](../Protocol_State_Machine.md) | Timingを300msへ更新。有効ACK後の監視を明記 |
| [Test_Specification.md](../Test_Specification.md) | 新しい送信契約、追加テストと結果を記載 |
| [Implementation_Plan.md](../Implementation_Plan.md) | OI-02の採用値を暫定値扱いする旧記述を更新 |
| [NF55G_HIL_Preparation.md](../NF55G_HIL_Preparation.md) | 今後のD0実機確認で使用するT2を300msへ更新。日付付きの過去記録は保持 |
| [Open_Issues.md](../Open_Issues.md) | OI-02へユーザー指定・実装反映と残る実機確認を記録。Closeしない |
| [CHANGELOG.md](../CHANGELOG.md) | 変更理由・テスト・配置状態を記録 |

この記録と[全Host／Mock実行ログ](D0_T2_300ms_Host_Mock_20261111.txt)を新規保存した。改訂仕様のReview_Rev0.md、過去の試験結果・退避ソース、日付／版付きの旧配布コマンド一覧は当時の記録として保持する。旧一覧にあるD0=600msは今回の変更前の値であり、今後の実装・試験は現行ATE_Command_Masterの300msを参照する。

## テスト結果

| 検証 | 結果 |
|---|---|
| `python -B -m unittest tests.test_read_cache_integration -v` | 関連29件成功、0.133秒 |
| `python -B -m unittest discover -s tests -v` | 全287件成功、4.797秒。従来284件＋新規3件 |
| ACK後299ms／300ms | ACKを7ms遅延させてT2始動点を確認。完全D0応答を再送なしで受理しDATAをVALIDへ更新 |
| 最終試行でACK後301ms | 初回無応答の後、期限超過をRESP_TIMEOUTとし、command retry=1、response retry=0、ambiguous=True。旧DATAはINVALID、個別Queryは無送信 |
| ACK後250msにEB | EBを独立ACKしてもD0期限を延長しない。各300msの監視を2回行い、仮想時計602msで最終RESP_TIMEOUT。STATUS／INFOは従前値を維持 |

Mockはフレーム全体を指定時刻に到着させるため、300msの実UART送出・受信処理時間を保証する結果ではない。ソースの設定・ATEからの呼出し・期限判定・安全側のCache失効を確認した。

## 残確認

- OI-02: 変更後ソースのPico配置、ACK後の完全応答受信時間、遅延・EB介在時と量産負荷時のTiming。Open継続。
- OI-01の装置側T1、OI-03の製品側CHARGE_END副作用、他のr2確認事項は従来どおり未確定。
- FU禁止、Picoで製品PASS／FAILを判定しないこと、Queryから自動Refreshしないこと、通信中のSD write／flush禁止を維持する。
