# ATEから測定値を直接指定するADC校正

2026-11-26 山田承認: ARのT2は同等の保存情報読出し（D5／EL／OL）に合わせ、有効ACK受信後100msに確定。src/config.pyのT2_AR_MS=100を現行AD_VERIFYのAR通信へ適用する。従来のAR診断用1000msおよびAR T2未確定の記載は承認前の履歴。AD書込みの診断用T2=1000msは継続し、ARのCommand Retryなし・別指令読戻し・Cache非採用も維持する。OI-12の待ち時間の決定事項は山田承認により解決。製品側の実応答時間の実機検証、REF表現・小数保持・ATEへの返却仕様（OI-04）、長さ・順序の正式確認（OI-20）は別管理とする。AR_REFRESH／AR Cache Queryはこの変更では追加しない。


Revision: Rev.0
Date: 2026-11-26

人が測定器を読み、ATEから `AD_<TYPE>_<POINT>_<VALUE>` を指定してNF55Gへ送る方式を、2026-11-26ユーザー指示により採用確定とする。自動取得した測定Cacheを明示採用するCAL_WRITEも併用する。今回の確定は直接指定方式の採用であり、製品側の正式AD／AR仕様・量産受入の完了とは区別する。

## 入力と使用条件

例 `AD_4_1_1.85` は充電電流のPoint 1へ1.85 Aを指定する。コマンド全体をASCIIで送り、行末CRLF、応答を待って次の行を送る。

応答終端は親FWのATE_RESPONSE_TERMINATORに従い、現行ソース既定はCR。CR／LF／CRLFの設定に合わせてATEを受信させる。要求のCRLFと機器原文中のCRLF、UARTでは送出しないGPIBのEOIを区別する。

| 引数 | 指定内容 |
|---|---|
| TYPE | 1=DISCHG_I、2=BATT_V、3=ACDC12V_V、4=BATT_CHG、5=12VOUT_V。回路名でも指定可能。現行診断の対応表を使用し、製品正式仕様の承認とは区別。 |
| POINT | 1／2。P1／P2も使用可能。測定点A／Bとの対応はATEで指定する。 |
| VALUE | 人が読んだ実測値を10進数で指定。電流TYPE1／4はA、電圧TYPE2／3／5はV。単位文字を付けない。符号・小数・E/e指数表記を受け付ける。 |

`AD_BATT_CHG_P1_1.85` も同じ指定。下線で各項目を区切る。VALUEは生HEXではない。シャント表示から電流を指定する場合は人またはATEがA値へ換算する。50 A／50 mVならI[A]=U[mV]。Picoは直接指定値を再測定・単位換算・Cache補完しない。

現時点は既存サンプル診断条件を維持する。CALIBRATION_SAMPLE_ENABLED=True、TEST_START成立、同一試行のINFO_REFRESHでFW_REV=S1.14B／UNIT_SERIAL=000001であることが必要。ソース既定はFalse。測定器接続・CAL_MEASURE・CAL_MEASUREMENT?・取得ID・照会済みCacheは不要。ADの診断T2=1000ms、ARのT2=100ms（2026-11-26 山田承認）。AD／ARのCommand Retryなし。ADの正式T2は未確定。今回、実機配置・書込み・デバッグは行わない。

## 送信と応答

Picoは指定値を有限のIEEE754 float32へ変換し、ビッグエンディアン8桁ASCII HEX（VALUE8）で送る。AD DATAはTYPE1文字＋POINT1文字＋VALUE8文字の計10文字。例のDATAは `413FECCCCD`。

正常応答は `OK:AD_WRITE:<TYPE>:<POINT>:<VALUE8>:<AD_ADC十進値>:<計算値欄原文HEX>`。例のVALUE8は3FECCCCD。製品応答の計算値欄8文字は16桁HEXにして保持する。フレーム・対象・ADCが正しければ計算値欄の非HEX文字も原文として返す。OKは通信成立を意味し、校正PASS・小数保持・即時の係数反映を保証しない。

NaN／Inf／OL、単位付き、カンマ区切り、生HEX、float32のオーバーフロー、非ゼロ値がゼロになるアンダーフローは送信前に拒否する。通常のfloat32表現丸めは生じる。物理範囲・符号・値の採否はATEが判断し、Picoで3.3 A制限、絶対値化、範囲への丸め込みを行わない。

| 条件 | 応答と扱い |
|---|---|
| 引数不正 | ERR:AD_ARGUMENTS／AD_TYPE／AD_POINT／AD_VALUE（各理由にERR:を付ける）。製品送信なし。 |
| 診断無効 | ERR:CAL_WRITE_DISABLED。製品送信なし。 |
| 試行なし・個体不一致 | ERR:CAL_NO_ACTIVE_TRIAL／ERR:CAL_SAMPLE_IDENTITY。製品送信なし。 |
| 別通信中 | ERR:BUSY。製品送信なし。 |
| 製品拒否・通信異常 | ERR:AD_WRITE_<理由>:AMBIGUOUS=0/1。自動再送なし。 |
| AD応答の対象・内容不正 | ERR:AD_WRITE_RESPONSE:AMBIGUOUS=1。書込み済みの可能性を残す。 |

正常・成否不明時はDATA／ARをINVALIDにし、同回路のDMM Cache A／Bと照会済み記録も失効させる。AD応答からAR／STATUS／INFOを更新しない。正常に対象・ADCを検証できた書込みだけを同試行の読戻し比較元として記録する。同じ対象・点の後続書込みが成否不明なら先行の比較元は破棄する。

## ATEの実行順

| 順序 | ATE送信または操作 | 確認内容 |
|---|---|---|
| 1 | 対応FW・診断設定、接続製品、元補正値と復元方法を確認 | 対象サンプルの条件を確認する。 |
| 2 | TEST_START → INFO_REFRESH → FW_REV? → UNIT_SERIAL? | 各応答を待ち、S1.14B／000001を確認。 |
| 3 | 対象回路・補正点の製品条件を設定し、測定器を人が読む | 回路・Point・符号・A／V・値を確認する。 |
| 4 | AD_4_1_1.85 | ADを一回送信。応答のTYPE／POINT／VALUE8／ADC／原文を記録。 |
| 5 | AD_VERIFY_BATT_CHG P1 | 別指令のAR。書込みVALUE8、AR REF8、AD ADC、AR ADCをATEへ返す。 |
| 6 | ATEで照合し、補正後の実測も確認 | REF8の整数化で小数一致を保証できなければ照合未成立と記録。合格を補完しない。 |
| 7 | 次点は条件を設定し直して新値を人が読み、別AD | 異常・成否不明なら停止。前回値の自動補完・自動AD再送なし。 |
| 8 | DATA_REFRESHと必要Query・外部測定、TEST_ENDとログ確認 | 係数反映・補正成立・再投入保持を別項目として確認。 |

読戻しは回路名付きAD_VERIFYを使用する。TYPE3は `AD_VERIFY_ACDC12V_V P1`、TYPE5は `AD_VERIFY_12VOUT_V P1`。Point 2ならP2を指定する。旧互換の `AD_VERIFY BATT_CHG P1` は従来の限定比較であり、本方式の共通手順には使わない。AR_REFRESH／AR Cache Queryは未実装のまま。自動ARは行わない。

## 記録と残確認事項

試行ログへATE入力原文、source=ATE_DIRECT、回路・Point・入力VALUE、VALUE8、AD DATA、AD結果・応答原文HEX・再送情報を記録する。人が値を読み違えなかったことをPicoが保証するものではない。最終判定はATEが行う。

TYPE5種×Point2種の送信経路は模擬確認の対象。実製品の全点確認とは区別する。製品の正式T2・REF表現・小数保持・係数反映・保持・受入条件はOI-04／05／12／16～21で継続し、今回Closeしない。PARAM_RESETのRPは、確認済みS1.13／S1.15_r1ではSPの設定・閾値だけを初期化し、ADC校正値を初期化しない。S1.14BのRP前後保持は別途実機確認する。
