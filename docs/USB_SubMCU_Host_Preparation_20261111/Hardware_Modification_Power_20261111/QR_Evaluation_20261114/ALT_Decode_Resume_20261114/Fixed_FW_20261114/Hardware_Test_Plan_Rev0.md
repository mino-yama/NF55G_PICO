# 固定接続候補FW 実機検証計画 Rev.0

2026-11-14。未実施の計画。対象qr-fixed-20261114.1。

## 書込み

外部電源OFF、外部5V線・QR・UARTを基板から外す。PC Type_C1だけ接続してBOOTSELへ。picotoolでA06FEA01012EC137を照合し、現Flash2MB退避・hash保存、新UF2 hash照合、load -vと独立verify、配置版infoを記録する。既存親Picoは操作しない。PC Type_C1と外部5Vを同時接続しない。

## 固定接続cold-start

書込み後にPC Type_C1を外し、外部電源OFFでQR Type_C2・外部5V・GP0→SH-U05A RXD/GNDを戻す。受信を開始してから電源ON。RST/BOOTは押さない。
bootと個体ID、phase1～4、HID mount／descriptor／mount、heartbeatを確認する。3秒待ちが入るので初期化完了時刻も記録。失敗時はUART原文を保存し、heartbeatのmain回数・frame数・DP/DMの値から停止／未認識を切り分ける。3秒待ちで改善しただけなら原因特定とはしない。
cold-startを少なくとも3回（各OFFで10秒以上待つ）確認する。各試行は別ファイルへ保存。再現回数・失敗も省略しない。

## 継続読取

認識後、検証済みQR A/Bを交互に20回、1回ずつ完了を確認し1秒以上あけて読む。完成件数20・順番A/B各10・原文35byte・重複/断片混入なし・drop0・main/frame進行を照合する。さらに10分以上の連続稼働中に追加の異なるQRを読み、停止やFIFO欠落がないことを確認する。速度・最大時間の無制限保証とはしない。
旧原文送信換算で20読取は1024件を大きく超える入力HIDを含む。新モードは原文を省略するため、取得レコード数だけを旧入力報告数と同一視しない。新モードはレコード総数1024超もHost parserで検証する。

## 未解決事項

先頭NUL、電源ON認識、初期化段階、drop、遅延して届く読取の取り扱いを記録。正式ATE/Cache/SSへの連携、7355／2 Host、量産給電保護のCloseはしない。ホットプラグ成功は今回の目標に含めない。
