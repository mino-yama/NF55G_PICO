# RP2350-USB-Aで7355のCDC Hostを作るための資料と改造手順

調査日: 2026-11-16 JST。対象はユーザー指定の[Switch Science SKU 10275 / WAVESHARE-30274](https://www.switch-science.com/products/10275)、Waveshare RP2350-USB-A。QR用RP2350-USB-Cとは別個体を使い、USB-Aから7355背面USB-Bへ接続する同一案件の継続。

## 結論

**CDC Hostとして使う構成は成立する見込みがあるが、出荷状態のまま完成品として使えるとは判断しない。公開回路と同じR13実装の個体なら、R13撤去によるHost専用化を基本案とし、CDC Host FWを別途作成する。**

メーカーFAQがR13撤去を明記しているのは、Hostのホットプラグ、およびLow-Speedキーボード/マウスの無応答に関する条件。7355はFull-Speed機器であり、今回の固定接続CDCで「R13ありでは絶対に動かない」と実証した資料ではない。一方、回路図ではHost側D+が1.5kΩで3V3へ引かれているため、Host専用基板からこのプルアップを除く方針が妥当と判断する。現物の版・実装と一致することを確認してから施工する。

|項目|今回の判断|根拠・適用範囲|
|---|---|---|
|R13 1.5kΩ|実装あり・公開回路と一致なら撤去する基本案|公式FAQと回路図。USB-A側D+のDevice用プルアップ|
|R10 NC/1.5kΩ|未実装のまま維持。現物実装は照合|回路図ではD−側の選択プルアップ。Hostへ追加しない|
|R11/R12 各27Ω|維持|USB-A D−/D+の直列抵抗。撤去対象ではない|
|QR基板で行ったCC抵抗の変更|USB-A側では不要|USB-AコネクタにCC端子はない。USB-C側R5/R6は書込み/Device用として維持|
|D+/D−外付け15kΩプルダウン|今回一律必須とは確定しない。電気条件・採用FWを評価して判断|公開回路に外付けはなく、既存PIO実装はGPIO内蔵pull-downを有効化。内蔵pull-downだけでUSB規格適合を保証するものではない|
|給電/保護|接続方法の具体化が必要|USB-A VBUS、Type-C VBUS、5V端子が同一VSYS。原典上専用Host電源スイッチ/過電流/逆流防止素子は見当たらない|
|CDC Host FW|必須|メーカーHID→Device CDCデモは7355 CDC Host用FWではない|

## 集めた資料

原典とダウンロード履歴は[資料フォルダと台帳](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/README.md)へ保存した。既存QR基板の回路図・旧調査資料・7355マニュアルは変更していない。

|資料|用途・確認範囲|
|---|---|
|[メーカー回路図 PDF](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/RP2350-USB-A.pdf)|1ページ。USB-A/Type-C/電源/GPIOのネットを抽出と画像で確認|
|[メーカーWiki HTML](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/Waveshare_Wiki.html)|FAQのR13処置、C/C++デモ、依存版、書込み方法|
|[メーカーのR13位置写真](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/Waveshare_R13_Location.png)|赤丸・矢印の原画像を保存。今回個体の部品位置は現物照合する|
|[ピン配置図](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/Waveshare_Pinout.jpg)|端子の5V/GND/3V3、UART候補、GPIO16のRGB使用を確認|
|[メーカーDemo ZIP](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/RP2350-USB-A.zip)|展開物も保存。HID Host→Device CDCの構成とPIOピンを読解。実行・書込みはしていない|
|[RP2350ハードウェア設計資料](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/Hardware-design-with-rp2350.pdf)|公式Wikiが案内するRaspberry Pi資料。必要節を今後参照するため保存。全頁レビューではない|
|[Pico C/C++ SDK資料](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/Raspberry-pi-pico-2-c-sdk.pdf)|同上。FW開発の参照用として保存|
|[TinyUSB CDC公式説明](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/TinyUSB_CDC.html)と[Host例](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/TinyUSB_Host_CDC_Example.html)|CDC Host・制御線・line coding・送受信の説明。最新版の機能を固定版へ無条件適用しない|
|[固定SDK/PIOソースの台帳](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/local_source_manifest.json)|現在案件のSDK2.2.0とQR側vendorからCDC Host/HCD/PIOの関連11ファイルを別途コピーしhash照合。依存一式を再配布したものではない|

販売ページはWeb閲覧でSKU/商品コード/回路図リンクを確認。ファイルとしての取得はHTTP429で失敗したため、販売ページHTMLを保存済みとはしない。メーカーWiki等の主要資料は別途取得成功し、失敗も台帳に残した。

## 原典回路で確認した事実

### USB信号と端子

USB-A J1のDATA+はDB_P→R12 27Ω→GPIO12、DATA−はDB_N→R11 27Ω→GPIO13。R13 1.5kΩはGPIO12側から3V3へ接続。R10はGPIO13側から3V3へのNC/1.5kΩ選択部品。

![公式回路図のUSB-A部分を拡大した図](USB_A_Circuit_Detail.png)

Type_C1の信号はRP2350のネイティブUSBへ接続。R5/R6各5.1kΩはCCからGNDへ接続される。**7355をUSB-Aへ接続する今回構成では、Type-CをHost化するCC施工は行わない。** メーカーFAQのR13撤去後にDeviceとして使えなくなる対象はPIO側USB-Aであり、ネイティブType-CのBOOT/書込み経路とは分ける。

USB-AはPIO Host側roothub1を使う構成がサンプルにある。pin_dp=12、D−=13、DPDMを前提候補とし、USB-A実機FWで照合する。ネイティブUSB Host/roothub0を使った旧Type_C1向け検討は今回のUSB-A用設定に流用しない。

### 電源

回路図ではUSB-A J1 VBUS、Type_C1 VBUS、P1の18番VSYSが同じネット。P1 17番がGND、16番が3V3で、ピン配置図の電源表示は5V/GND/3V3である。VSYSを3.3Vで給電してもUSB-Aへ必要な5Vは生成されない。**今回のUSB Host評価は適切な5V系から給電し、3V3端子へ5Vを入れない。**

USB-Cと外部5Vを同時に直結すると給電源同士が接続される。PC書込み時は外部電源を切り離し、通常評価ではPC Type-Cを切り離して外部5Vを使用する運用を基本案とする。同時PCデバッグが必要なら電源分離/逆流防止を別途設計する。

U1の500mA LDOは3V3生成用であり、USB-A VBUSが500mAに制限/保護される意味ではない。7355がAC自己給電でもUSB端子のVBUS検出・電流・逆給電は実機で確認する。以前のQR単体評価での保護条件に関するユーザー指定を、未確認の新基板へ自動転用しない。

### メーカーFAQと版の扱い

メーカーFAQはHostでのホットプラグ・Low-Speed無応答にR13撤去を案内し、撤去後のPIOポートDevice利用不可も記載している。固定接続の今回評価でホットプラグ受入を必須へ追加しない。

FAQにはRP2350 A4との回答があるが、保存した公式R13位置写真のチップ表記はA2である。写真は位置の参考とし、今回個体のシリコン版や改良済み実装を写真/FAQだけで確定しない。

## FWで必要な変更と使える材料

公式`host_hid_to_device_cdc`は**USB-AでHIDを受け、ネイティブType-CのCDC DeviceからPCへ出す**サンプル。`CFG_TUD_CDC=1`はPC側Deviceの設定であり、7355を制御する`CFG_TUH_CDC`とは異なる。公開サンプルのHost設定はHIDを有効にしており、7355へのCDC Host送受信は実装されていない。

必要な開発は次のとおり。

1. RP2350-USB-A専用のC/C++ CDC Host FWをQR版とは別のproject/成果物として用意。固定SDK2.2.0を出発点に、PIO driver/HCD APIの整合を確認する。GPIO12/13はUSB専用、GPIO16はRGB使用としてUART割当てから除外する。
2. PIO USBを初期化しHost taskを継続実行。メーカー例は120MHzを使用しており、既存PIO実装に合うクロックを固定する。商品の最大CPU150MHzという記載だけでPIO USBを150MHz動作へ変更しない。
3. `CFG_TUH_CDC=1`でCDC ACMを有効化。7355のVID:PID=1334:0309、CDC通信/データinterface、endpointと記述子全体を実機取得して識別する。
4. 固定版の`CFG_TUH_CDC_LINE_CONTROL_ON_ENUM=0x03`または対応する制御APIでDTR/RTS両ON、line codingを9600/8N1へ設定。USB制御転送の完了を確認してからコマンド送信へ進む。PCのCOM24番号はHost MCUでは使用しない。
5. `tuh_cdc_write`/flush/read等で部分送受信・CRLF終端・timeout・切断・遅着を管理。USB処理をUART出力待ちで止めず、RAM Queueで診断を出す。
6. 初回はIDN原文照合、その後は[保存済み7355電圧試験手順](../CDC_Settings_Voltage_Quick_Test_Rev0.md)へ進む。7355本体のBUS=CDC/LANG=SCPIは前面確認が必要。ADC形式で取得を代用しない。
7. 親Picoとの独立双方向UARTは単体CDC成立後に正式契約へ接続。GP0 TX/GP1 RXは出力図上の候補だが、baudrate・正式pin/APIは未確定。ATE UART0/NF55G UART1は維持する。

メーカーWikiはDemo0.5.3/SDK2.1.0を記載する一方、取得ZIPの`library.properties`は0.5.2表記。ZIP SHA-256は10月14日保存版と一致した。版名を推定で揃えず、実際のソース・依存版・hashで管理する。

WikiにあるHCDの`return`削除は今回の採用手順にしない。現固定SDKのHCDはframe番号/abortの戻り値を返す実装で、QR側vendorに対応関数が存在することを確認した。ただしCDC HostとしてのARMビルド・動作確認は今回未実施。既存QR FW/依存原典を改変して新基板へ書き込まない。

## 改造と初回評価の実施順

以下は具体化した施工・受入手順案で、今回の作業で施工や機器操作を行った記録ではない。

|段階|実施内容|確認・保存するもの|
|---|---|---|
|A0 個体確認|型番・基板版・チップ表記、R13/R10実装と公式位置図を照合|今回個体の識別と施工前写真。版が違う場合は部品を推定して撤去しない|
|A1 初回書込み経路確認|外部5Vと7355を外し、Type-CからPCへ接続。対応手段で識別・元Flash退避を行う|識別/Flash退避/使用ツール。既存QR個体を対象にしない|
|A2 無給電施工|PC/外部電源/7355/給電し得るUART adapterを全て外し、R13だけを撤去（実装確認できた場合）。R10はNC維持、R11/R12は残す|施工前後の写真、取り外し部品、パッド剥離/半田ブリッジなし。R13パッドを短絡しない|
|A3 給電単独確認|供給元を1つに限定。外部5VとGND/極性/枝の保護条件を確認し、機器未接続で5V/3V3と異常発熱・resetを点検|測定点と電圧・電源経路。外部5VとPC VBUSを同時直結しない|
|A4 CDC用FW配置|外部給電を外してPC書込みモードへ。対象専用の検証済みFWを配置し版・内容照合|版・個体・hash・verify。現時点では対象FW未作成|
|A5 固定接続で起動|全て無給電でUSB-A–Bケーブルを7355へ接続。PC Type-Cを外し、診断受信を準備して外部5Vで起動|mount/USB速度/descriptor、DTR/RTS・line coding完了、起動差と電圧|
|A6 IDN→単発測定|`*IDN?`+CRLFの識別後、既知低電圧で20V/200V/AUTO・READ?を逐次試験|識別応答・設定/測定原文・前面表示・エラー/timeout。NF55Gへは書き込まない|
|A7 親との接続|2基板の独立UART・要求/試行相関を実装し結合試験|取得→Cache→ATE確認→別書込み、書込み完了/TEST_ENDで破棄。通信Timing・遅着除外|

R13の正しい位置は[メーカー写真](../../../../reference/USB_Host_SubMCU_20261116_RP2350_USB_A/Waveshare_R13_Location.png)を参照する。メーカーFAQのHost専用化案を具体化したものであり、現物のR13が未実装ならその撤去作業は不要。外付け15kΩを追加する場合はD+/D−の各GND側への条件と位置を別途確定し、R13パッドへそのまま置換しない（R13の反対端は3V3）。

## 未確認事項と残Issue

- 今回個体の入手/基板版/R13実装/改造状態、シリコン版。
- 7355のFull-Speed CDCでの起動・列挙・制御転送・連続応答。PC直結の成功は新Hostの受入ではない。
- 給電容量/突入/枝保護/USB側負荷/逆給電、実装の電気条件。外付けプルダウン追加の要否と規格適合。
- 新Host FWの版固定・ビルド・配置、独立双方向UARTと親PIO資源・正式API。
- 校正AD/AR・QR/SSの未確定変換と反映時期は従来Issueを維持。今回の基板選定で解決扱いにしない。

USB-SUB-05に今回の基板資料・施工案を関連付け、USB-SUB-02等の給電/保護課題を維持する。旧1基板2 HostのUSB-SUB-03は今回構成の必須条件に戻さない。

## 今回の変更と検証

原典9件（Wiki/回路図/ZIP/CDC説明2件/位置図2件/設計資料2件）を取得し、全件のサイズ・SHA-256を記録。ZIP36エントリを確認・展開し、過去のメーカーZIPとhash一致。関連ローカルソース11件はコピー元とhash一致。回路図を描画してUSB-A・電源・ピンを画像確認、メーカー位置写真/ピン配置も目視確認した。販売ページは閲覧確認のみ、HTML取得は429として台帳に残す。

収集用scriptはPython構文確認、資料manifest/hash/PDF・ZIP形式/参照リンクを検査。FW/量産コード/実配線を変更しておらず、Host Unit/Mock NF55G・ARMビルド・実機試験は今回実行していない。施工済み・CDC Host完成とは報告しない。
