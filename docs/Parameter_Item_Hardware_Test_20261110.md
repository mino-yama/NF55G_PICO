# 項目別PARAM 実変更・復元試験

確認日: 2026-11-10。設定試験はPC記録上2026-11-09 18:08:02～18:09:06 JSTに完了。11月10日の継続作業でSDログを分割回収・解析し、現在の設定を再読出しして照合した。

対象: 開発用Pico 2 COM6（69f7d45962cfdfad）、ATE COM20、NF55G FW S1.13。ユーザー申告のバッテリ・負荷未接続条件で実施。外部の充放電・バックアップ等の実動作確認と、RTC電池装着後の保持試験は今回の範囲外とした。

## 結果

| 項目 | 元値 | 試験値 | 復元値 | 変更・読戻し・復元 |
|---|---:|---:|---:|---|
| PS_ON_BACKUP | 1 | 0 | 1 | 正常 |
| AC_LINK | 0 | 1 | 0 | 正常 |
| AUTO_CHARGE | 2 | 1 | 2 | 正常 |
| EVENT_ENABLE | 0 | 1 | 0 | 正常 |
| MAX_BACKUP_TIME | 0 | 1 | 0 | 正常 |
| MIN_BACKUP_TIME | 15 | 16 | 15 | 正常 |
| RESTART_TIME | 15 | 16 | 15 | 正常 |
| BATT_LOW_THD | 50 | 51 | 50 | 正常 |
| BATT_CAP_MAH | 4900 | 4901 | 4900 | 正常 |
| BATT_CAP_WH | 36 | 37 | 36 | 正常 |

各項目を1つずつ変更し、INFO Cache無効化を確認後に明示D5で全26項目を取得。指定項目だけが試験値となり、残りは元値を維持した。各項目の直後に同じ項目別コマンドで元値へ戻し、全26項目を再照合した。

SD生フレームでもD5の100文字全体を比較し、変更時は対象欄のみ相違、各復元後は元の100文字と完全一致した。保護設定・CHG_IR_THD・製造情報・予約部に意図しない変更はなかった。項目別SPの送信DATA50文字は実装の生成値と全20回一致し、SP正常応答はすべてDATA0文字。

- ATE要求608件。前応答を受信してから次を送信し、実測最短送信開始間隔101.0453ms。
- SP 20 Transaction（変更10＋復元10）、D5 21 Transaction、全41件OK・command/response retryとも0・ambiguous=False。
- 送受信フレーム82件すべてBCC一致。
- TEST_END=OK、終了時Self CheckはTEST_LOGGER/TEST_LOG_DROPもOK、累積破棄0、SD OK、通信IDLE。
- SDログ88307 byte、ヘッダを含む1405行すべて14列。256 byte分割回収でSDとPCのSHA-256一致: `a84b49e6a92f9dedd7c5de77a71591e8d624397add8ee858c22ce38b532f37ee`。
- 継続作業時の現在値再読出しでも全26項目が元値と一致。Self Check/SD正常、通信IDLE。通常アプリ待受、COM6/COM20解放済み。

## 限界・残事項

確認済みは上表の代表値への設定・通信・読戻し・復元であり、全範囲・境界値・全ビット組合せの網羅ではない。製品動作、電圧・電流変化、AC切入後の保持、設定による保護・制御効果を判定していない。明日実施予定としていた実動作確認は、新たな接続・測定条件を確認して別途行う。RTC電池準備と保持試験も未完了。既存Open IssueはCloseしていない。

製品コード・Pico配置・仕様の変更なし。Host/Mock全体の再実行は行わず、ATE実機試験、SD/PC整合、フレームとデータの照合で検証した。

## 証跡

- [全ATE応答・項目別前後値](../temp/dev_acceptance_20261109_run01/param_actual_change.json)
- [SDとハッシュ照合済みCSV](../temp/dev_acceptance_20261109_run01/param_actual_20261109_180800_verified.csv)
- [全フレーム・RAW差分解析](../temp/dev_acceptance_20261109_run01/param_actual_verification.json)
- [継続作業時の現在値確認](../temp/dev_acceptance_20261109_run01/param_current_verify_20261110.json)
