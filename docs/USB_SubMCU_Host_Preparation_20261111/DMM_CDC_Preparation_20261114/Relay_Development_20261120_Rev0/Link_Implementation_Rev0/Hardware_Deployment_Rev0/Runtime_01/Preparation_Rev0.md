# 中継実機試行1 接続準備 Rev.0

2026-11-20 JST。ユーザーから親子UART/GND結線完了の報告を受領。現物の端子位置・導通はまだ独立確認していない。

現在のPnP一覧は親USB COM6（69F7D45962CFDFAD）とUSB-SERIAL CH341 COM22。以前ATEに使用したELECOM USB-Serial Converter（当時COM20）は検出されていない。現行ATEの設定は57600/8N1、flow controlなし、応答CR。現在のCOM番号を確認するまで送信しない。

親PC USBが引き続き検出されているため、外部電源投入前に親USBを外すよう案内する。Host USB-A→7355 USB-Bの固定接続、ATE用RS232C変換器の接続を整え、外部電源はOFFを維持した上で受信待受を準備する。今回COM6/COM22を開く操作、reset、ATE/NF55G/7355への送信、通電操作は行っていない。

[接続準備記録](Readiness_01.json)／[全体手順](../../Acceptance_Procedure_Rev0.md)
