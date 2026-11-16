# 原文取得版への実機書戻し結果 Rev.0

日付: 2026-11-14／対象chipid A06FEA01012EC137

- BOOTSELで対象照合、書戻し前はqr-uart-20261114.2。
- 現Flash全2,097,152byteを退避しsave -a -v照合成功。
- qr-uart-20261114.1の配布UF2 SHA-256=0ce5168e546f25431e51922fb6fd0728a38697efb65937b9532da9f9aece1b81を再確認。
- load -vと独立verifyが終了0。配置後の版はqr-uart-20261114.1、1024件、GP0診断TX／115200 8N1、GP12 D+／GP13 D−、個体一致。
- 対象指定reboot成功。Alt専用復元を含まない原文取得FWへ実機も復元した。新QR設定での起動・列挙・文字列照合は次の採取で確認する。

## 次の手順

追加基板のPC Type_C1を抜き、外部電源OFFで外部5V／GND、GP0→SH-U05A RXDとGND、Type_C2 QRを戻す。SH-U05AのみPC接続、PC Type_C1と7355は未接続。受信READY後に外部電源投入、起動と列挙を確認して同じ35文字QRを1回読む。QR設定はユーザーが英語キーボードへ変更済みとの申告。Alt版実績は新設定の結果へ転用しない。

[配置前情報](before_info.txt)／[全Flash退避](backup_verify.txt)／[load verify](load_verify.txt)／[独立照合](independent_verify.txt)／[配置後情報](after_info.txt)／[reboot](reboot_status.json)。

退避Flash SHA-256: E46AB98D8EC514665A6AE8B69B52C6E46F19B6DE50EED293F62BED7C1E1AD997

旧配布・旧試験原文・Alt試作は履歴として保持。今回コード変更・Host／Mock再実行なし。直前の復元後Host／Mock326件成功を維持。USB-SUBの設計回答・Open状態は変更しない。
