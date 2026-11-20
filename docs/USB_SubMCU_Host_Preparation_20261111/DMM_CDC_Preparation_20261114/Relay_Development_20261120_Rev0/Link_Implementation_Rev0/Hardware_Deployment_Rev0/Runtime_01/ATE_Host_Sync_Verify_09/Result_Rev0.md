# Host同期修正版 起動照合 試行9 結果 Rev.0

2026-11-20。FW .2配置後、ユーザーが外部給電/親信号/監視を復帰し電源OFFで完了。COM22/Host GP1とCOM7を先に待受開始し、電源ON通知後に治具IDとEXT_QUERYを各1回実施。USB-B未接続。

## 確認事実

治具ID NF55G_PICO_FIXTURE,Rev.0+CR成功。EXT_QUERY 2000 *IDN?への応答はERR:EXT_LINK_NOT_READY:AMBIGUOUS=0+CR。親実装上、正しいsession/基板ID/FW prefixを持つh/NOT_READYを受理した場合の応答で、タイムアウトではない。親Host起動照合が成立した。

Host GP1の受動採取は76byte。先頭00 1byteに続く75byteのH（session=13E65D6186A73B400000000000000000）を確認。余分なデータとHの間にCRLFなし。原文decoderの一行FRAME_FORMATは先頭00を含むためであり、.2は@から同期してHを処理できた。入力線にはHのみでQなし、7355への機器コマンド未送出。捕捉例外なし。COM7/22解放済み。自動再送/レンジ/READ/NF55G/Flash変更なし。

## 検証範囲と残事項

起動時データを含む実機親経由照合が修正後成功し、修正前の同条件TIMEOUTから改善を確認。USB-Bなしという期待条件でNOT_READYを正常に返したもので、USB識別中継受入の完了とはしない。次は電源/配線を維持し、電源ONの7355へUSB-Bだけ接続して同じ親経由IDNを1回実行する。失敗時自動再送なし。Host fault解除や再bindは行わない。前回NOT_READYでは親fault/Host session bindを確定していないため、新要求のHでREADY照合する通常処理を使う。IssueはOpen維持。

[ATE結果](Capture_Result.json)／[Host入力線採取](Host_RX_Capture.json)／[原文](host_rx.raw)。
