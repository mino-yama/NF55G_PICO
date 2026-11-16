# 7355 Type_C1 Host接続条件・切替回路案 Rev.0

**2026-11-14 方針変更により本書の既存QR基板Type_C1改造・CC切替案は採用しない。施工・写真依頼は不要。本書は当時の検討履歴として保持。** [2基板・2経路の現行方針](Split_Host_Architecture_Rev0.md)。


2026-11-14。同一USB Host SubMCU案件の継続。回路検討案であり施工指示・施工承認・Host実機受入の記録ではない。

## 確認できた事実

ユーザー回答: 7355接続はUSB-C－USB-B直結。追加RP2350のType_C1側R5／R6は未改造。PC直結では7355のCDC識別QueryがDTR／RTS両ONで3回成功した。[実機原文・結果](PC_Connection_Rev0/Result_Rev0.md)。

原典回路図ではType_C1のCC1→R5 5.1kΩ→GND、CC2→R6 5.1kΩ→GND。VBUSはVSYS直結。Type_C2のR18／R19／R20／R21と異なり、Type_C1にSource用予備抵抗パッドがあることは原典から確認できない。[原典確認画像](PC_Connection_Rev0/Schematic_Review.png)。Type_C1のD線はRP2350 native USB、Type_C2はGP12／13のPIO USB。

USB-IF Type-C Release 2.0 §3.5.4はC－USB2.0 Standard-BケーブルのCプラグCCにRdを規定する。これは規格上の構成であり、手元ケーブルの内部抵抗を測定した結果ではない。ケーブルにHost用Rpが入っているとは扱わない。

## 回路として必要な区別

R5／R6をGND側へ接続したまま56kΩに換えてもRpにならない。Source用RpはCCから5V側へ接続する。Device用RdとSource用Rpを同時に常設する回路にはしない。

Type_C1をHost専用のRpへ変えると、PCのUSB-C Sourceとの通常の接続検出条件も変わる。従来どおりBOOTSEL USB書込みができると保証しない。従来書込み経路を保つため、単純なHost専用化を先に施工しない。

未改造RdのままではUSB2.0データ通信自体が絶対にできない、という結論でもない。この基板はVBUS常時直結で、CCを監視してUSB Hostを起動する回路は原典にない。native Host FWによる固定ケーブル限定試験で列挙する可能性と、Type-C Sourceとして適正なCC・VBUS制御を備えることは区別する。現仕様資料が求めるHost回路条件を、通信する可能性だけで満たしたと扱わない。

## 切替回路の具体案（未承認・未施工）

書込みとHost評価でCC終端を切り替える案。R5／R6周囲の実装位置・CC側パッドを現物へ照合し、配線可能性を確認してから施工図へ進む。次の接続は論理回路であり、写真の左右にパッド位置を推定してはならない。

|信号|PC書込み／Device状態|7355 Host評価状態|
|---|---|---|
|Type_C1 CC1|5.1kΩでGNDへ|56kΩ・1%で外部給電5V系統へ|
|Type_C1 CC2|別の5.1kΩでGNDへ|別の56kΩ・1%で外部給電5V系統へ|
|CC切替|両CCを同時に切替。候補は2極2投の先切り後接続スイッチ|RpとRdが同時につながらない構成|
|Type_C1相手|PCだけ、7355は外す|7355だけ、PCは外す|
|給電|PCから。外部5Vの供給経路を物理的に外す|既指定の外部5V。PCへつながる給電経路を外す|
|Type_C2|初回FW書込み／7355単体試験ではQRを外す|2 Hostの段階までQRを戻さない|

切替・配線・機器交換は無給電で行う。この案はCC終端を選択するだけで、VBUS接続検出連動スイッチ・放電・逆流防止・過電流保護を実装するものではない。量産Type-C Sourceの完成案ではなく固定機器の限定評価用候補。56kΩはDefault USB Power用候補で、1.5A／3A供給を広告しない。スイッチや抵抗の現物準備済みとは扱わない。

R5／R6の撤去と切替回路追加を採用するか、CCを分離できる外付け評価基板で本体を保持するかは未決定。通常のC変換アダプターを挟むだけで、基板上RdがSource回路へ変わるとは扱わない。

## 次の実作業と完了条件

1. Type_C1・R5／R6の現物位置が見える写真を原典へ照合する。微細CC端子への測定を要求しない。
2. 書込み経路を維持する施工図・部品・切替状態を具体化して人間確認。既存資料の「未照合の改造はしない」に従い、この時点では部品を動かさない。
3. 7355単体native Host用FWをQR版と別成果物として作成・ビルド・Host／Mock試験。固定SDK2.2.0、roothub0、CDC ACM、DTR／RTS両ON、PC実績の9600/8N1、GP0診断TXのみ、識別Queryに限定。親Pico／NF55Gを接続せず、QR版配布と配置前Flashを保持する。正式な内部UART契約を確定しない。
4. 回路とFWの準備後に、対象個体照合・Flash退避・書込み／verifyを行う。無給電でPCを外し7355固定接続・外部給電へ切替え、UART待受を先行する。Host列挙・制御線設定結果・送受信原文を取得し、PC実績の識別応答と照合する。ここまでの実作業は未実施。

## 未確認・変更範囲

写真によるR5／R6の位置／パッド対応、CC切替の施工可否、ケーブル型番・内部構成、7355 BUS／LANG前面値、Type_C1 native Host実機動作、2 Host、VBUS逆流／保護は未確認。USB-SUB-01／02／03／04をCloseしない。

今回は回答記録・原典照合・切替回路案の作成のみ。元資料・コード・FW・基板を変更せず、機器へ追加送信／COM openなし。Host Unit／Mock NF55Gはコード変更がないため再実行なし。

## 根拠

- 原典: reference/USB_Host_SubMCU_20261110/RP2350-USB-C_schematic.pdf、1ページ。元ファイルは変更しない。
- [USB-IF Type-C Release 2.0](https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf) §3.5.4、2026-11-14確認。ケーブル規定の根拠であり、現物ケーブルの検査結果ではない。
- [Microchip CC／Rp・Rd解説](https://developerhelp.microchip.com/xwiki/bin/view/applications/usb/typec-features/cc-vconn-signals/)。案件内保存原典: reference/USB_Host_SubMCU_Host_Conditions_20261111/Microchip_CC.html。
- [既存Host回路条件](../../USB_Host_SubMCU_Host_Circuit_Conditions_Rev0_20261111.md)。Type_C1の改造条件を確定していない旨、PC／外部5V切離し、固定評価と量産Source受入の区別を継承。

旧Integration Planの表にあるR5／R6「VSYS側」の記載は、2026-11-11に訂正済みの対象であり、その表記を配線根拠にしない。本書と原典のGND接続を使用する。
