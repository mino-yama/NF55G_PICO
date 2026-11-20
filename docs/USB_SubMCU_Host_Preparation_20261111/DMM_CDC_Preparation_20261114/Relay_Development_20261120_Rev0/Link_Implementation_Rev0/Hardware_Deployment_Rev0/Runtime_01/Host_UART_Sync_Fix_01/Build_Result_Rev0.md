# Host同期修正版 ビルド完了 Rev.0

2026-11-20。FW meter-host-relay-20261120.2、ARM build/link成功、固定SDK2.2.0、-Wall/-Wextra/-Werror。picotool info -aで新FW版・RP2350 ARM Secure・Host GP0/1とUSB GP12/13を照合。全Host Unit/Mock NF55G 450件成功（追加4件、全78分割境界を含む）、失敗/エラー/skipなし。

配置用UF2: docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/meter_host_relay_20261120_2.uf2

94720byte、SHA-256 cb3fc420088b72eae1bab80fad5ddb09c75f0bd8a79889aefddb08f42a869def。旧.1 UF2も元の既知hash 2f6faee45dbbad016fe8470128e7cce9cb1c6e05980d053d4d83880b24a3906c と一致し保持。親ソフト変更なし。現在の実機Hostはまだ.1で、今回修正版は未書込み・実機未受入。

次は外部電源OFF、Hostの外部5V/親信号/GND/監視UART/USB-Aを切離し、HostをBOOTSELでPC USB-Cへ単独接続する。個体照合・現行Flash全退避・UF2照合後に.2を書込みFlash verify。以降は電源投入前から受信を監視し、USB-Bなしでh/NOT_READY→親LINK_NOT_READY、USB-B接続後に識別中継を確認。IssueはOpen維持。

[build/hash manifest](Build_Manifest_Rev0.json)／[UF2 metadata](UF2_Info_Rev0.log)／[450件結果](After_Fix_Host_Mock.log)／[ビルドログ](Build_Rev0.log)／[修正詳細](Result_Rev0.md)／[配置受入手順](Deployment_Acceptance_Rev0.md)。
