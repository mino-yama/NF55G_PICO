# 親Pico稼働状態のまま7355接続再確認 2026-11-21 Rev.0

ユーザー指示に従い、親PicoのFW変更・再起動を行わず現状の接続で確認。

## 確認事実

- COM7/57600/8N1、応答終端CR。`*IDN?`→`NF55G_PICO_FIXTURE,Rev.0`、`COMM_STATUS?`→`OK:state=IDLE`。親のATE処理が稼働していることを確認。
- `EXT_QUERY 2000 *IDN?`一回→`ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`、応答約16ms。7355のIDNは取得できなかった。
- 同時のCOM22/115200/8N1受動監視は0 byte。COM22へ送信なし。両ポートはclose済み。
- 再起動、FW変更、READ、設定変更、NF55G向け指令なし。

[ATE原記録](../../../temp/usb_cdc_resume_20261121/live_parent_check_151528/result.json)、[Host受動採取](../../../temp/usb_cdc_resume_20261121/live_parent_check_151528/host.raw)。

## 解釈・未確認事項

親が稼働していることと外部測定器リンクが要求を受け付けることは別。今回の即時拒否とHost無受信は、先行タイムアウトによる親側リンクfault保持のソース経路と整合する。`COMM_STATUS?`はNF55G通信側の診断であり、7355リンクREADYを示さない。

7355まで識別要求が届いた証拠はなく、物理接続良否、7355スリープ、Host READYは今回判定できない。ソフトRESET/WDTや管理指令を追加していない。関連IssueはOpen継続。コード・仕様変更なしの実機通信確認のためHost/Mock再実行なし。
