# USB SubMCUの次工程・手戻りを抑える順序 Rev.0

**2026-11-14 最新方針：Host基板をQR用／7355用に分離し、親Picoへ独立した2経路で接続する。以下の1基板・2 Hostを先に成立させる順序は旧案。** [新しい構成と順序](Split_Host_Architecture_Rev0.md)。


2026-11-14。同一USB Host SubMCU案件の継続。ユーザーの「CDC側か、QRを上流Picoへ渡すコマンドか。手戻りの無い手順で」に対する調査・工程判断。

## 判断

先に7355のUSB CDC Host適合と、固定2ポートの同時Host構成を確認する。親Pico受渡しはQR/DMM共通の内部リンクとして境界案を今から整理し、物理リンク・正式コマンド実装の固定はUSB構成成立後とする。PC向けUSB CDC保守コンソールは今回の7355 CDCとは別で、追加実装しない。
手戻りを無条件にゼロにできるとは約束せず、未成立の構成を先に検証して大きな作り直しを避ける。

## 確認できた事実

- QR側はqr-fixed-20261114.1で電源ONからRST不要の3試行成功、連続20読取35文字一致。旧原文版と新配布・Flash退避を保持。
- 現QR FWはCFG_TUH_RPI_PIO_USB=1／CFG_TUH_CDC=0／CFG_TUD_ENABLED=0。Type_C2のPIO Host単体であり、Type_C1のDMM Hostは実装済みではない。
- 固定SDK2.2.0内TinyUSBのusbh.cは単一_usbh_controller、HCDはPIO/ネイティブを構成で選ぶ。単純なtuh_init(0),tuh_init(1)の併記を2 Host成立としない。USB-SUB-03を維持。
- 7355英文メーカー説明書§6.1（印刷6-1／PDF95）はBUSをMENU→8 I/F→BUSで選択し、USBとCDCを別選択肢として記載。使用IFは同時利用不可、設定は不揮発保持。
- §6.4（印刷6-10／PDF104）はUSB Full-Speed、Type-B、TMC/CDC、ASCII指令・応答を記載。ただし実機のBUS・FW・VID/PID・CDCインターフェースは未確認。
- PCポート基準取得ではSH-U05A COM22だけを識別。これだけで7355が物理的に未接続とは断定しない。
- 親PicoはATE UART0=57600/8N1、NF55G UART1=38400/8E1。古い計画のATE115200表記は現在のconfigと異なる。既存2 UARTを転用しない。GP8/GP9の旧PIO RX試作は双方向リンクではない。

## 実施順と各段階の完了条件

|順序|作業|完了の確認|
|---|---|---|
|1 実機のCDC識別|7355をPCへ直接接続し、現在BUS/FWを記録、CDC設定・COM/VID/PID/インターフェースを採取。初期化・校正・設定全消去はしない|メーカーのCDCクラスと実機記述子の一致、使用設定を記録|
|2 DMM Host単体|Type_C1のHost給電/CC条件を再確認後、QR版と別プロジェクト/配布でネイティブUSB Host CDCを検証。公式コマンド体系/終端を確認し識別問合せ・既知条件の1読出しまで|実機の送受信原文、USBクラス適合、応答と前面表示。測定値からNF55G書込みを行わない|
|3 固定2 Host構成|QRのPIO側とDMMネイティブ側の管理を独立させる候補を固定依存版で検証。USB-SUB-03の成立方式を明示|両機器同時認識、DMM待機中もQR読取、非blocking・欠落数確認。ライブラリ/配線の変更が必要なら先に設計提示|
|4 共通内部UART|親PicoのPIO RX/TX資源と下位GPIOを確認し、版/起動識別・要求ID・CRC/境界・取消・再起動時の扱いを確定|両端Hostテストで分割/連結/破損/遅延/再起動を検証、正式案をレビュー後に物理疎通|
|5 QR縦通し|同じ共通リンクで親の受付開始→下位ARM→35文字→親の現試行へ採用。初回はSS/正式Cacheへの結合を切離す|未受付・取消後・旧試行・旧起動・既読重複を採用しない。既存FixtureApp.accept_qrを要求相関なしに直結しない|
|6 DMM縦通しと併用|同じリンクへDMM取得を追加。ATE/NF55G/Loggerと併用|取得とATE判定・明示書込みを分離。Queryから自動取得せず、既存Timingを侵害しない|

## QR受渡しで先に明確化すべき点

診断版は読取を連続通知するが、正式運用ではATEの明示読取開始と現試行に対応させる必要がある。RST前に読んだQRが認識後に届いた可能性もあるため、「その時受け取った35文字」を無条件で今の製品へ採用しない。
QR_ARM/QR_CANCEL等は既存準備資料の仮称。下位ではUSB/Alt復元、親では6項目分割・試行相関・ログS/Nを担当する案を維持。DMM用の共通枠だけ予約し、未確定コマンド値・単位/レンジ等を推測で固定しない。

## 今回進めた作業と次の操作

原典の該当ページを抽出・画像確認し、現在の設定・依存版・親側受入口を照合。上記順序と共通リンク境界の案を別紙に保存。コード/FW/実機設定の変更や書込みなし。
次の実作業は7355のPC直結による識別。7355を追加RP2350のType_C1へまだ接続しない。現在のBUS設定を記録してからCDCへ設定し、USB Type-BをPCへデータケーブルで直接接続する。PCからの指令送信は正確なコマンド体系/終端の確認後。親Picoの環境は変更しない。

## 根拠

[原典と固定ソースhash](Source_Check_Rev0.json)／[PCポート基準](PC_Port_Baseline_Rev0.json)／[内部リンク境界案](UART_Contract_Draft_Rev0.md)
原典: ../../../reference/ADCMT_7355_20261104/7355-ope--foa-00000201a00-e.pdf、印刷6-1/6-10/6-11。
参照: ../../USB_Host_SubMCU_Integration_Plan_20261110.md、../../Software_Module_Interface.md、../../Open_Issues.md USB-SUB-01/03。
TinyUSB公式のCDC Host説明は https://docs.tinyusb.org/en/latest/reference/class/host.html 、Host→CDC Device例 https://docs.tinyusb.org/en/latest/examples/dual/host_hid_to_device_cdc.html 。後者はHost+Deviceであり2 Hostの証拠ではない。最新版説明の機能を固定SDKに無条件転用しない。
