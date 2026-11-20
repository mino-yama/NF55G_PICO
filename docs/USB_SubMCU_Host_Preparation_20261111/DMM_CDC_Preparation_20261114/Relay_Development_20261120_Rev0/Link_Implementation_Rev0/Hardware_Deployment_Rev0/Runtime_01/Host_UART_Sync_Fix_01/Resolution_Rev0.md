# Hostデバッグ 解決記録 Rev.0

2026-11-20。起動時の00byteが正常な親HフレームにCRLFなしで先行し、旧Hostが一行77byteとして破棄することを実原文/C engineで再現。Hostのみ@先頭同期を実装し、CRC/長さ/session/重複拒否/故障保持を維持した。親ソフトや機器レンジ仕様は変更していない。

4回帰追加、全Host Unit/Mock NF55G450件成功、ARM build/link成功。FW.2を対象BFCF2EDB84B0B37Fへ旧全Flash退避後に配置しFlash verify/版照合成功。実機試行9で起動00byte付きでも親照合/NOT_READY成功、試行10で親経由7355識別32byteを原文どおり返却。原因となる受信処理の不具合について修正効果を確認した。

残受入: USB接続済み冷起動・設定送信・切断/遅着/復帰・NF55G/ATE優先・PIO実負荷/SD timing等。起動00byteの電気的起源は未特定、IssueはOpen維持。レンジ問題はユーザー指示どおり保留。

[修正詳細とテスト](Result_Rev0.md)／[配置結果](Host_Deployment_02/Result_Rev0.md)／[親経由実機識別](../ATE_Host_IDN_10/Result_Rev0.md)／[シリアルモニター手順](Serial_Monitor_Quick_Start_Rev0.md)。
