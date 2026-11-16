# 固定接続候補FW 実機進捗 Rev.1

2026-11-14。qr-fixed-20261114.1／A06FEA01012EC137。

|確認|結果|証跡|
|---|---|---|
|cold-start第1回|RSTなしで認識3606ms、A/B交互20件全一致、drop0|[第1回](cold01/Result_Rev0.md)|
|cold-start第2回|RSTなしで認識3606ms、A1件35文字一致、drop0|[第2回](cold02/Result_Rev0.md)|
|cold-start第3回|未実施|—|
|10分以上の継続稼働と読取|未実施|—|

現時点の電源投入2試行中2成功。先頭NUL1 byteは継続。原因特定・全体受入・量産保証・Open Issue Closeは行わない。正式親子UART／ATE・7355／2 Host・量産給電保護等は残課題。
Rev.0は当時の記録として保持する。
