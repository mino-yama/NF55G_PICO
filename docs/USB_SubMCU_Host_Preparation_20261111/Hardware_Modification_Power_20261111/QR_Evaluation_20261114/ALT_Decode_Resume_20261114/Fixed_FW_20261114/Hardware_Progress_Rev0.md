# 固定接続候補FW 実機進捗 Rev.0

2026-11-14。qr-fixed-20261114.1／A06FEA01012EC137。

- Flash配置・独立verify完了。
- cold-start第1回: RSTなし自動認識成功（HID mount3606ms）。
- 同一起動20読取: A→B各10件・全件35文字一致、7760 HID報告処理、drop0、再起動・decodeエラーなし。
- cold-start第2／3回、10分以上稼働は未確認。
- 先頭NUL・電気保護・正式親子UART／ATE・7355／2 Host等の既存課題は維持。

[第1回の証跡](cold01/Result_Rev0.md)／[実機検証計画](Hardware_Test_Plan_Rev0.md)
