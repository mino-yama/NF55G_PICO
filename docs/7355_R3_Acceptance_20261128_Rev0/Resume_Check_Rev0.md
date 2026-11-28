# 受入再開指示後の現接続確認 Rev.0

2026-11-28。「現在動作環境にはあるので至急」との指示を受け、現在のポートを実機照会した。過去の無応答記録だけで停止せず、情報管理経路と通常中継経路をそれぞれ新規に確認した。

| 経路 | 実測結果 |
|---|---|
| COM7の治具IDN | NF55G_PICO_FIXTURE,Rev.0 |
| 通信／SD／ログ欠落 | IDLE／OK／0 |
| HOST_INFO? METER | ERR:HOST_TIMEOUT、1,015 ms |
| EXT_QUERY 2500 *IDN? | ERR:EXT_TIMEOUT:AMBIGUOUS=0、2,516 ms |
| 列挙ポート | COM6（親）、COM7（ATE）、COM23（CH341診断） |

証跡：[管理照会と治具状態](ate_resume_ready_01.json)、[通常中継の識別照会](resume_idn_01.json)、[親リンク状態](parent_resume_ready_01.log)。管理INFOだけの問題とはいえず、このPCから治具を経由して7355までの通信成立は未確認。識別照会は明示1件で、自動再送・測定・設定変更・校正書込みは行っていない。

ユーザー回答は「PC→ATE入口→PICO→HOST→7355経由で実行」。同じ経路を使用し、PC直結へ切り替えなかった。通信成功の申告とは区別する。

## 指定経路での受入ランナー実行

- 400セット用ランナーを、ADC・要求レンジR3・入力源設定200 mV・セット間1秒・COM7／COM23で起動。[耐久ランナー結果](endurance_20261128_170805_782993/result.json)はSTOPPED、stopped_trial=0、completed_trials=0。HOST_INFOの応答フレームが得られず、試行開始前に停止した。[ATE記録](endurance_20261128_170805_782993/ate.jsonl)。メタデータのR3／200 mVは要求条件であり、今回レンジ設定や読戻しに到達したことを意味しない。
- 校正取得ランナーも起動。[校正取得ランナー結果](calibration_resume_01/result.json)はSTOPPED、ERR:HOST_TIMEOUT、取得データ0件。HOST情報の照合前に停止したため、測定器設定変更・TEST_START・CAL_MEASURE・製品校正書込みは未実行。[ATE記録](calibration_resume_01/ate.jsonl)。

両ランナーの開始前チェックは実行済みだが、R3での校正取得・耐久本体は未開始。異常を無視して400回要求を繰り返したり、別経路の結果を受入へ加算したりしていない。前提通信を復旧してから、別の実行記録で再開する。
