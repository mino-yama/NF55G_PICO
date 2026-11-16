# UART診断FW 1024件版 仕様 Rev.0

日付: 2026-11-14／版: qr-uart-20261114.1

## 変更理由

35 ASCII文字の試験QRで、実機はAlt＋テンキー数字列を含むHID入力を返し、旧版256件のRAMログが上限到達した。文字列全体の取得には容量が不足したため、診断用UART版だけを1024件へ増やす。機器側の出力設定や親Picoの仕様は変更しない。

## 仕様

- CMakeのUART有効時だけPROBE_RECORD_CAPACITY=1024、版qr-uart-20261114.1。通常RAM版は256件・従来版名を維持。
- 76byteレコード・20byteヘッダの並びは維持。UART版g_probeは77844byte、通常版は19476byte。満杯では上書きせず破棄数を加算。
- UF2メタデータにDiagnostic RAM capacity: 1024 recordsを追加。版は起動レコードとも同じ。
- GP0 TX／115200・8N1、Type_C2 GP12 D+／GP13 D−、PIO／DMA／クロック・Host処理・最大16byteずつのUART排出は変更しない。
- scripts/usb_submcu_probe_log.pyはboot版が既知のqr-uart-20261114.1の場合だけUART上限を1024にする。旧版・未知版の上限は256。RAM解析は従来の固定256件ABIのまま。
- capacity到達・連番欠落・途中破損・記述子不完全を引き続き拒否。head NULは既存の明示オプションのみ。hardware_acceptance=false／qr_text_verified=false／tail_completeness=not_provenを維持。

## 検証

容量境界1023／1024、既知新版400件受理、旧版・未知版255／256境界、400件内の連番欠落拒否を4テストで確認。全Host／Mock326件成功（5.612秒）、Host_Mock.txt参照。ARMビルド・RAM配置・UF2メタデータ・配布hashはビルド完了後のResult_Rev0.mdへ記録する。

新FWの実機書込み・新容量でのQR再読取はまだ実施していない。旧版の実機結果と混同しない。
