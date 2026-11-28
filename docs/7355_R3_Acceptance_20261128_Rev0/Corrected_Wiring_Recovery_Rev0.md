# 配線修正後の通信復旧・R3再開 Rev.0

2026-11-28。ユーザーより、前日の量産治具化でHOST GP0―親GP12、HOST GP1―親GP13と接続していたとの申告があり、正しい接続へ修正済みとの回答を受けた。

現行は親GP12 TX→HOST GP1 RX、HOST GP0 TX→親GP13 RX、GND共通。交換HOSTは73AD3A60D10514E9、通常FW meter-host-relay-20261125.2を継続し、親・HOSTの製品コードは今回変更していない。

## 通信復旧

修正後の管理INFOで新個体ID・版・起動nonce AA165DBC70E798C0・NOT_READYを取得し、親―HOST間の管理通信復旧を確認した。続いて通常管理コマンドHOST_RESETを1回だけ送信。RESET_ACCEPTED→RESET_DONEを確認し、新起動nonce 9290DB097E8BB8BA、READYへ遷移した。

通常ATE→親→HOST→7355のEXT_QUERYで識別原文`ADC Corp.,7355,246410099,  A02\r\n`の全32バイト一致を確認。IDLE、SD OK、drop0。[管理RESET・識別・ログ状態の証跡](corrected_usb_rebind_01/result.json)／[ATE原文](corrected_usb_rebind_01/ate.jsonl)。この前のCOM7占有による停止は通信復旧失敗とは混同しない。

旧基板と新基板の双方で無応答だった先行結果は、TX/RX逆接修正前の履歴として保持する。旧基板故障が立証されたとは扱わない。OI全体の受入条件を一括Closeしない。

## R3再開・200 mV入力

7355をADC・DCV・連続／即時・ヘッダなし・呼出解除・R3・PR4へATEから設定し、それぞれ照会した。入力源設定200 mVとのユーザー回答の条件でMD?原文は`+9.999999E+37`。CAL_MEASURE_DISCHG_I AはERR:CAL_MEASUREMENT_OVERRANGEとなり、Cacheに採用しなかった。TEST_END=OKで終了、製品AD／AR等は送信0件。[試行結果](corrected_r3_calibration_01/result.json)／[ATE原文](corrected_r3_calibration_01/ate.jsonl)。

R3の上限付近のため、入力を40 mVへ変更して有効範囲内で取得・耐久を確認するよう依頼中。400セットはまだ開始しない。補助USB-UARTは、この時点のPC列挙でCOM6・COM7以外は存在せず、変換器自身のUSB接続確認を依頼した。

校正取得ランナーは新個体IDを引数化し、補助UARTがない場合のCache照会無送信証跡を確認済みと扱わない。RN0の呼出解除は読戻しのメモリ件数を0固定せず、仕様どおりのRN0＋5桁を検証する。耐久ランナーは新個体ID引数へ対応し、旧個体IDなら試験開始前に停止する。

耐久ランナー模擬6件成功（400セット・399待機、設定無送信、異常停止・無再送、新ID成功、旧ID拒否）。[模擬結果](replacement_runner_tests.log)。実機400セット成功の代用にはしない。
