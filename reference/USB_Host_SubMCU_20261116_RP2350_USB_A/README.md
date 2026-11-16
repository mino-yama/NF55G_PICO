# RP2350-USB-A DMM Host原典資料台帳

保存日: 2026-11-16 JST。同一NF55G試験治具USB Host案件。対象: Switch Science SKU10275/WAVESHARE-30274。原典ファイルは編集せず、解析・回路図描画は[調査結果フォルダ](../../docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/RP2350_USB_A_20261116/Assessment_Rev0.md)に分離した。

|原典|公開URL|保存物|
|---|---|---|
|メーカー回路図|https://files.waveshare.com/wiki/RP2350-USB-A/RP2350-USB-A.pdf|[PDF](RP2350-USB-A.pdf)|
|メーカーWiki|https://www.waveshare.com/wiki/RP2350-USB-A|[HTML](Waveshare_Wiki.html)|
|メーカーサンプル|https://files.waveshare.com/wiki/RP2350-USB-A/RP2350-USB-A.zip|[ZIP](RP2350-USB-A.zip)、Official_Demo/に36エントリを展開|
|R13位置写真|https://www.waveshare.com/w/upload/c/ca/RP2350-USB-A-R13.png|[PNG](Waveshare_R13_Location.png)|
|ピン配置図|https://www.waveshare.com/w/upload/6/64/680px-RP2350-USB-A-details-6.jpg|[JPG](Waveshare_Pinout.jpg)|
|RP2350設計資料|https://files.waveshare.com/wiki/common/Hardware-design-with-rp2350.pdf|[PDF](Hardware-design-with-rp2350.pdf)|
|Pico C SDK資料|https://files.waveshare.com/wiki/common/Raspberry-pi-pico-2-c-sdk.pdf|[PDF](Raspberry-pi-pico-2-c-sdk.pdf)|
|TinyUSB CDC|https://docs.tinyusb.org/en/latest/reference/class/cdc.html|[HTML](TinyUSB_CDC.html)|
|TinyUSB Host例|https://docs.tinyusb.org/en/latest/examples/host/cdc_msc_hid.html|[HTML](TinyUSB_Host_CDC_Example.html)|

ダウンロードURL、最終URL、HTTP結果、サイズ・SHA-256は[主要5件の成功記録と販売ページ429](download_manifest_retry.json)、[図・設計資料4件](download_manifest_retry_02.json)を参照。初回sandbox内ネットワーク接続失敗は[初回記録](download_manifest.json)として保持。元データの置換・失敗の削除は行っていない。

販売ページ https://www.switch-science.com/products/10275 はWebツールで内容を確認したが、HTML保存はHTTP429で未完了。公式の主要資料は取得できている。販売ページをローカル保存済みとはしない。

SDK/PIOの抜粋はLocal_Fixed_SDK/、Local_Fixed_PIO/へコピーし、ライセンスを併置。[元パス・コピーhash台帳](local_source_manifest.json)。SDK2.2.0と現行QR vendorからの11ファイルで、SDK/依存全体のコピーではない。最新版ドキュメントと固定版のAPIは区別する。

公式ZIP SHA-256: `e709329b4ec4735ba1895578edac8fd0fba1f575656df213b55e6997fda1dec5`。10月14日保存版と同一。原典のlibrary.propertiesは0.5.2、WikiのDemo表示は0.5.3のため表記差を保持する。既存QRのFW/個体の動作実績をこのUSB-A新個体の実績へ転用しない。
