# ATE要求終端の対応記録

日付: 2026-11-10

## 確定した要求と変更

ATEの終端は保証できないというユーザー指示により、コマンド＋CR、コマンド＋LF、コマンド＋CRLFをすべて受理する。定期CR単独は無応答で無視する。

`src/ate_server.py` を変更し、CRまたはLFを受信した時点で行を確定する。空のCR／LFでは要求を作成せず、LF待ち状態も保持しない。CRLFのLFは空行として無視され、分割到着でも二重実行しない。応答終端はCRLFのまま。文字列D0の別名追加は行わず、NF CMD D0のATE入口はDATA_REFRESHを維持する。

CR単独が空状態に届いた場合に無視する仕様であり、途中まで受信済みのコマンドに届いたCRは終端となる。送信元でコマンド途中に定期CRを割り込ませないこと。

## Host／Mock

`.venv\Scripts\python.exe -B -m unittest discover -s tests`：273件成功。

各終端でD0を1回だけ実行、定期CR後の受信残留なし・次要求正常、分割CRLFと空行混在、各終端でASCII／FRAME／長さ異常から復帰、Queue上限を検証。既存の分割受信テストはCR時点で確定する期待値へ更新した。

## 開発機への配置

COM6でPico ID `69f7d45962cfdfad` を確認し、`/src/ate_server.py` だけを置換して再起動。読戻しでPCファイルとのバイト一致を確認。他モジュールは配置していない。

- 配置SHA-256: `9f3546f9e2eb9f41656bcd8d5f18fcb7903743d92f98d9f16f5cea3f3b073940`
- 旧モジュール保存先: `temp/dev_acceptance_20261109_run01/ate_server_before_eol_20261110.py`
- 修正前実機結果は `ATE_D0_Line_Ending_Hardware_Test_20261110.md` に保持。

ATE_Command_Master、Test_Specification、CHANGELOG、Open_Issuesを更新。ATE-EOL-01は人間確認前のためOpenを維持する。

## 修正後の実機確認

COM20、2026-11-10 08:20:50～08:21:29 JST、全48送信。最短送信間隔115.549ms。[送受信証跡](ATE_Line_Ending_Fix_Evidence_20261110.json)。

| 入力 | 結果 |
|---|---|
| DATA_REFRESH＋CR／LF／CRLF | すべてOK、後続DATA_REFRESHもOK |
| CR単独10回の定期送信 | 全10回無応答、直後のDATA_REFRESHはOK |
| 空CRLF | 無応答、後続正常 |
| DATA_REFRESH＋CR、その後LFを別送 | CR時点でOK、LFは無応答、後続正常 |
| D0単体＋各終端 | いずれもERR:UNKNOWN_CMD、後続正常 |

終了時COMM_STATUS=IDLE、retry cmd/rsp=0、SD_STATUS=OK、自己診断全項目OK、ログ破棄は開始・終了とも0。COM6／COM20解放済み。NF生フレームの採取や長時間SD負荷試験は今回行っていない。RTC電池保持も今回の確認対象外。
