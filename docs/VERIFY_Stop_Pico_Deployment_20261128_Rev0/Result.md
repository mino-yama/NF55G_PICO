# VERIFY停止版 親Pico配置結果 Rev.0

Date: 2026-11-28
Status: deployed and readback-verified

## 対象と前提

- 親Pico 2／RP2350、COM6、unique ID `69f7d45962cfdfad`、MicroPython 1.27.0。
- ユーザー確認：ATE送信停止、PicoをNF55G本体から物理切離し、試験・通信idle。
- R3耐久400セットは配置前に完了。CSV回収プロセス停止後に配置した。
- 配置対象は`/src/main.py`、`/src/calibration_write.py`、`/src/command_parser.py`の3件だけ。
- config、`/main.py`、Logger、SD Sink、SDカード内容は上書き・削除していない。

## R3耐久完了ゲート

R3／40 mV設定で400/400セットを完了し、400件のCSVを回収・個別照合した。マニフェストは400/400 complete、全ファイル14列・各11データ行、計4,400行で、試行番号T000998～T001397を連番確認した。

- 7355応答400/400、機器ERRは全て`+0,"No error"`。
- HOST sessionは1種類、ATE自動再送・試験中リセットなし。
- SD OK、Logger drop 0。
- READ原文は39.2019～39.2576 mV、応答時間156～641 ms。
- TEST_STARTは2,703～9,218 ms、中央値6,875 ms。
- SD／PC実ファイルSHA-256、ATE応答原文、開始・終了記録を照合。

配置前ゲートとして、R3耐久400/400とCSV400件の照合完了を確認した。本耐久はADC取得・Loggerの限定受入で、実シャント校正精度や製品PASSを判定したものではない。

## 配置・確認

1. 配置前の3対象ファイルを`backup/`へ退避。実機SHA-256はmanifest記載のbackup hashと一致。
2. VERIFY停止版3ファイルを強制コピー。転送後にPicoから読み戻し、3ファイルすべてcandidate SHA-256と一致。
3. PicoのconfigはSHA-256 `2f130267ace958100ca5b3acbb4d10048b4ff858093ae8e78bb6ce379745c663`を保持。外部測定器、接続先HOST ID、QR、双方向QR、校正診断、ATE終端、AR T2などの既存値を変更していない。
4. Pico上で`calibration_write.py`と`command_parser.py`を個別compileし、AR_READの分類と旧VERIFY拒否を確認。main.pyの単独compile確認はREPL heap不足でMemoryErrorとなったが、続くハードリセットで通常起動し、ATE `*IDN?`に正常応答した。
5. ATE UARTから`*IDN?`=`NF55G_PICO_FIXTURE,Rev.0`、`AD_VERIFY_BATT_CHG A`=`ERR:VERIFY_DISABLED`を確認。`COMM_STATUS?`=IDLE、`SD_STATUS?`=OK、`LOG_DROP_COUNT?`=0。
6. `AR_READ`はパーサー分類までを確認。NF55Gに対するAR/ADその他の製品コマンドは送信していない。AR戻り値の実機応答は未試験。
7. VERIFY停止変更のHost/Mock全597件成功。Picoのアプリ常駐処理を再開し、ATEシリアルポートを閉じた。

ハッシュ詳細：[配置manifest](manifest.json)、[配置前backup](backup/)、[配置payload](payload/src/)、[Pico readback](readback/src/)。

## 残確認

- 実AR_READ応答のATE受信・判定は未実施。実測校正時に対象・点を確認した条件で実施する。
- 0/1分類はATE責任。現行の実測根拠はBATT_CHG Aの限定値で、1 A境界規則および他回路・全範囲への一般化は別途ATE手順で定義する。
- 実測校正精度、製品の内部小数保持、係数反映・電源再投入後保持はOpenのまま。
- ローカルにはRTC Logger等の別未コミット変更が残る。本配置コミットではVERIFY停止関連の変更だけを対象とする。
