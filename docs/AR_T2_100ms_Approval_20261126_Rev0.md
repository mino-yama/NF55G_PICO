# AR T2=100msの承認反映・検証結果

Date: 2026-11-26

## 2026-11-26 ARのT2を100msへ確定（山田承認）

- 保存情報を読むD5／EL／OLと同じく、有効ACK受信後のAR T2を100msに確定。config.T2_AR_MSを追加し、SampleCalibrationWriteのARだけへ適用。AD診断T2=1000msは維持。
- 新規tests/test_ar_timing.pyで、ACKが20ms後・応答が送信119ms後（ACK後99ms）なら正常、121ms後（ACK後101ms）ならtimeoutとなることを、回路名付き／旧互換AD_VERIFYの両入口で検証。timeout時のAR再送なし・AR Cache非昇格、および500ms後のAD応答受理も確認。時刻はFakeClockによる模擬値で実機測定ではない。
- 関連18件成功（2.311秒）。全Host Unit／Mock NF55G 569件成功（24.018秒）。ログ: tmp/ar_t2_100ms_host_mock_20261126.log。git diff --check成功（改行コード警告のみ）。
- OI-12のT2決定は承認によりResolved。OI-04の返却契約・小数保持、OI-20の正式長さ・順序等と実機Timing検証は継続。AR_REFRESH／AR Cache Queryの追加なし。
- 次回の親Pico配置候補はAD_Direct_Pico_Preparation_20261126_Rev1。34ファイルが原本とバイト一致しmanifest SHA-256一致。Rev.0は履歴として保持。実機配置・校正値変更は未実施。

変更理由は山田承認による同種読出しとの待ち時間統一。変更コードはsrc/config.py、src/calibration_write.py、追加テストはtests/test_ar_timing.py。仕様・OI・試験仕様・CHANGELOGを同時更新した。

次回手順は[配置候補Rev.1](AD_Direct_Pico_Preparation_20261126_Rev1/README.md)。旧版の配置候補は更新しない。校正値を変更する検証は実機とATEで、実電流などの校正条件を整えて実施する。
