# REVピリオド対応FW 準備結果 Rev.0

2026-11-23。実原文`US250A-CGXE-009491-101A1.2601000001`に対応するQR用HOST修正版を準備した。

- 版：`qr-fixed-20261123.1`
- SDK：2.2.0、RP2350 ARM Secure、Release。既存ビルド手順で81工程完了、終了0。独自Cソースは-Wall/-Wextra/-Werror。
- 最終Host Unit／Mock：516件成功、skipなし、35.051秒。
- UF2：84,480byte、SHA-256 `cadff2460cc7b1be3ca8c8882c4b120569178371d3092c1182c66eb01bae2b3e`。
- 旧配布物を保持し、新配布先へUF2／BIN／ELF、ソース、UF2 info、hash manifestを保存。
- 実機配置は未実施。現在の基板は旧FW。修正後実読取りは未確認。

[配布manifest](../../firmware/usb_submcu_host_probe/releases/qr-fixed-20261123.1/manifest.json)／[UF2情報](../../firmware/usb_submcu_host_probe/releases/qr-fixed-20261123.1/UF2_Info.txt)／[ビルドログ](Revision_Period_ARM_Build_Rev0.log)／[最終回帰](Revision_Period_Final_Host_Mock_Rev0.log)／[新版サンプル](Samples_Rev1/normal_samples.txt)。

## 次の実機操作

既存QR固定接続FWの書込み手順を継承。QR用HOSTの外部5VをOFF・切離し、スキャナーとGP0信号線を外し、PC Type_C1のみをBOOTSEL接続する。外部5VとPC USBの同時給電はしない。親Picoと測定器HOSTは操作しない。個体A06FEA01012EC137を照合、現Flash全体を新規保存・hash記録してから新版load -v／独立verify。PCを外した後、無給電で元の固定接続へ戻し、受信待受後に給電・原文一致を再確認する。

手順根拠：[QR既存書込み・固定接続計画](../USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/ALT_Decode_Resume_20261114/Fixed_FW_20261114/Hardware_Test_Plan_Rev0.md)。BOOTSEL接続への切替えはユーザー操作待ち。NF55G送信・SS書込みなし。
