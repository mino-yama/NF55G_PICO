# CDC FIFO修正版 ビルド完了 Rev.0

2026-11-20。meter-host-relay-20261120.3のARM build/link成功。picotool info -aでFW版・RP2350 ARM Secure・SDK2.2.0・GP0/1とUSB GP12/13を確認。全453件成功、失敗/エラー/skipなし。

配置用UF2はdocs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/meter_host_relay_20261120_3.uf2、94720byte、SHA-256 529f12081432aea98189c4aeb3cc7a96fa28deb13d49b7a2f175cc9c75336ab5。旧.2のUF2と設定headerは別名保存。固定SDK/vendorソースは変更せず、HostのTX/RX FIFOを256で整合させ、endpoint64は維持した。起動時UART同期修正は保持。

まだ実機Hostは.2で新.3は未配置。次はシリアルモニターを閉じ、外部電源OFF、Host外部給電線/親信号/GND/監視UART/USB-Aを切り離してBOOTSEL単独PC USB-C接続。個体/旧版/状態を照合し、現行.2全Flash2MiB退避・照合後に新UF2をload -vで配置する。

配置後は親経由に戻して設定変更・READなしのQueryを12周実行する準備済み。CONFの正しい書式と原文の保持を確認し、レンジ20Vと前面の相違は別途確認する。提示CONFの崩れとの実機因果とレンジ問題は未確定でIssueはOpen。

[build/hash manifest](Build_Manifest_Rev0.json)／[453件テスト](After_Fix_Host_Mock.log)／[ARM build](Build_Rev0.log)／[UF2 metadata](UF2_Info_Rev0.log)／[修正詳細](Result_Rev0.md)／[累積Query準備](CONF_FIFO_Validation_01/Preparation_Rev0.md)。
