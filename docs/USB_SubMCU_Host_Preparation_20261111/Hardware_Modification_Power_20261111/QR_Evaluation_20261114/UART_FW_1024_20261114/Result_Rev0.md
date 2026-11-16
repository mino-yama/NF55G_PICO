# UART 1024件版 ビルド・配布準備結果 Rev.0

日付: 2026-11-14／qr-uart-20261114.1

## 結果

- ARMビルド・リンク成功（79ステップ、終了0）。アプリの-Wall／-Wextra／-Werrorを維持。
- Host／Mock326件成功（5.612秒）。容量に関する新規4テストを含む。
- picotoolファイル情報で版・ARM Secure・SDK2.2.0・Diagnostic RAM capacity 1024 records・GP0 TX／115200 8N1・GP12 D+／GP13 D−を確認。
- ELF g_probe=0x13014=77844byte。ELF sizeのbss=86392byte、text=43360byte。
- UF2=79360byte、SHA-256=0ce5168e546f25431e51922fb6fd0728a38697efb65937b9532da9f9aece1b81。
- UF2全155ブロックのmagicを確認。ARM Secure familyブロック154件の連番／件数・payload256byteと補助ブロック1件を分けて検査。ファイル全体で一律の連番という初期の検査仮定を修正し、配布バイナリ自体は変更していない。
- 新配布44ファイルをhash台帳へ保存。旧UART版45ファイル・旧RAM版43ファイルは各manifestのbytes／SHA-256一致を確認。

## 配布・証跡

[UF2](../../../../../firmware/usb_submcu_host_probe/releases/qr-uart-20261114.1/usb_submcu_qr_uart_probe.uf2)／[manifest](../../../../../firmware/usb_submcu_host_probe/releases/qr-uart-20261114.1/manifest.json)。

[仕様](Specification_Rev0.md)／[ビルド](Build.txt)／[Host／Mock](Host_Mock.txt)／[UF2情報](UF2_Info.txt)／[RAMサイズ](ELF_Size.txt)／[シンボル](ELF_Symbols.txt)／[旧版保持](Preservation_Check.json)／[新配布検証](Release_Verification.json)。

## 実機配置前の手順

外部電源OFF、追加基板から外部5V線・QR・7355・UART2線を外す。PC Type_C1だけを接続し、BOOTを押したままRSTを押して離し、BOOTを離す。書込み待機になったらchipid A06FEA01012EC137と配布hashを再照合し、現在Flashの退避、load -v、独立verify、配置後版確認の順で進める。

今回はビルドと配布準備まで。新FWの実機書込み・新容量でのQR読取はまだ行っていない。旧256件ログの上限到達は不合格のまま保存し、35文字一致とはしない。GPIO・Host処理・機器設定・正式治具UART仕様は変更していない。
