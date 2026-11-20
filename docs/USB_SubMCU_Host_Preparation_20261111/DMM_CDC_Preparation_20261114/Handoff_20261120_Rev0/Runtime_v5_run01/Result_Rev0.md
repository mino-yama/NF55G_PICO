# 評価FW.5 実機試行1 結果

2026-11-20 JST。受信待受を先行してから、ユーザーが外部電源投入完了・前面20Vレンジを報告。COM22、115200/8N1、flow controlなし、DTR/RTS OFF、TXなしで120秒採取。

## 確認できた事実

- 1,756 byte受信、SHA-256: a4418463d26df602fdc01d1020f29d5c6cdd1c4bcb12da7a56523de368888bdd。起動先頭にNUL 1 byte。以降の診断行は取得できている。
- 実FW版.5、Chip ID BFCF2EDB84B0B37F、USB_HOST_READYを受信。
- USB/CDC mount VID/PID=1334:0309、line coding 9600/8N1、DTR/RTS成功。
- IDN: ADC Corp.,7355,246410099,  A02。
- 引用符付きVOLT:DC応答は受理され、AUTO OFF読戻し0も成立。
- RANG 20送信後のSYST:ERR?は +0,"No error"。
- CONF?は "VOLT +1.999999E+02,+1.000000E-05" とCRLFを返した。full-scale欄の数値は約200 V。
- ユーザーの同試行の前面報告は20Vレンジ。raw #09での相違を今回も再現。
- SCPI_FAILED step=12 reason=CONF_RANGE_NOT_20V no_retry=1で停止。READ?送信なし、測定値取得なし。

## 評価・未確認事項

READ前のゲートは意図したとおり機能した。通信成立と単発測定の受入は区別し、単発測定受入は未完了。前面20VとCONF約200Vの相違の原因は未確定。FWのレンジ読戻し条件を緩めたり、200Vを20Vとして扱ったりしない。USB-CDC-RANGE-01はOpen継続。次はメーカー説明書・サンプルのCONF/RANG仕様と今回個体の挙動を照合して、測定を伴わない切分け手順を決める。

## 証跡

[UART原文](uart.raw)／[診断行の表示用コピー](Decoded_UART.txt)／[Query別応答・hash](Capture_Result.json)

採取終了後、ユーザーへHost外部電源OFFを案内した。OFF完了は本記録作成時点で未受領。コード・配線・機器設定の追加変更、再送、追加通電は行っていない。ソフト変更がないためHost/Mockは再実行せず直前382件成功を継承する。
