# QR接続案内の訂正 Rev.0

2026-11-23。ユーザー申告：スキャナーはQR用HOSTのUSB-Cへ接続、QR用HOST GP0から親Pico GP9へ接続。

直前のUSB-A接続確認の案内は、測定器用RP2350-USB-Aとの取り違えであり撤回する。QR用はRP2350-USB-C。既存設計とFWはスキャナー用Type_C2（D+=GP12／D−=GP13）のPIO USB Hostを使用する。Type_C1のネイティブUSBはこのQR FWで初期化しない。UARTはGP0 TX→親GP9 RX、115200/8N1、共通GND。

根拠：`firmware/usb_submcu_host_probe/main.c`のピン宣言・cfg.pin_dp=12／tuh_init(1)、および[既存準備資料](../USB_SubMCU_Host_Preparation_20261111/Preparation_Rev0.md)。現行FWの現在の実個体照合は未完了。

[実測記録](Hardware_Result_20261123_Rev0.md)のUSB-A確認待ちという記述は本訂正で置き換える。2回の採取でheartbeatが正常、qr_enabled=false、HID report／QR文字列が0件だった観測事実は変わらない。Type_C2への接続と照明／ビープを確認中。USB-Cという申告だけで誤配線や給電不良を断定しない。
