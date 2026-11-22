# Host→親Pico 遠隔再起動確認 2026-11-21 Rev.0

ユーザーが順次再起動とリモートデバッグ検証を指示。

## 実施結果

- Host BFCF2EDB84B0B37Fは直前の[BOOTSEL復帰作業](Host_Bootsel_Recovery_20261121_Rev0.md)でpicotoolの通常起動指令に成功した。READY/実行中FW版は未確認。
- 通常起動後に`picotool reboot -f --ser BFCF2EDB84B0B37F`を試行したが、対象デバイスにアクセスできず、今回の再起動は不成立。ビルド設定はUSB stdio無効であり、通常起動後のUSB経由強制再起動を利用可能とはしない。
- 親PicoのUSB保守ポートは未検出。PCにはATE COM7と監視COM22のみ。USB列挙を45秒監視し、その後も再確認したが親ポートは現れなかった。
- picotoolの読取照会でもアクセス可能なBOOTSELデバイスはなかった。
- 現行ATE parser/dispatcherには親再起動指令がなく、親再起動は未実施。ATE UARTへREPL制御文字を送信していない。
- ユーザーは親保守USBを接続する意向を回答。接続検出・親固有ID照合・再起動・新HELLO/READY/7355 IDNの確認が残る。

## 検証上の結論

BOOTSEL中のHost通常起動は遠隔実施できた。一方、現在の構成でHost/親の両方を常時遠隔再起動できることは確認できていない。Host管理指令/WDTの新規実装は既存保留方針を維持。親USB接続待ちで、順次再起動とCDC復帰の受入は未完了。

コード、Flash、仕様の変更なし。測定・機器設定・NF55Gコマンドなし。Host/Mockテスト再実行なし。関連IssueはOpen継続。
