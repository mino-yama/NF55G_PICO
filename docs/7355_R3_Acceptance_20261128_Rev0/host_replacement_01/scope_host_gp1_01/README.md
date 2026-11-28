# HOST GP1波形到達の観測 Rev.0

2026-11-28。親RST後のATE応答復帰を確認し、ユーザーがHOST接続・外部給電・GP1オシロ観測準備完了と回答。7355 USBは未接続の条件で、HOST_INFOを10回だけ明示発行した。

[結果](result.json)：10回ともATEからERR:HOST_TIMEOUTを受信し、最後のCOMM_STATUSもIDLE。要求の反復と停止は完了したが、HOSTからの正しい情報応答は得られていない。[全ATE原文](ate.jsonl)。

HOST GP1の波形到達はユーザーの観測結果待ち。親GP12の波形は、先行するHOST取り外し時にユーザーが確認済み。HOST未接続でのGP13 Highを受信故障の証拠にしない。[先行観測・親RST記録](../scope_ate_repeat_01/Observation_Rev0.md)。

FW・PIO・信号配線はこの反復試験では変更していない。R3測定・製品指令は送信していない。
