# 開発用HOSTリセット・BOOTSELコマンド 検討 Rev.0

日付: 2026-11-22。案件: NF55G Pico試験治具。状態: 提案・未実装。

## 結論と今回の前提

ユーザー指定: RST/BOOTを外部操作できる端子がなく接点操作も難しい。HOSTはハングしない前提で、開発作業を容易にするコマンド操作を検討する。

既存のPC→親Pico→HOST UART経路へ開発用管理入口を追加する案を推奨する。通常再起動とFW書込み用BOOTSEL移行を別操作にする。RST/BOOTの外部配線、追加治具、定期WDT監視、自動復旧を今回の前提に含めない。明示再起動にwatchdog_rebootを利用することと、常時WDT監視の導入は別である。

本資料は2026-11-21の量産復帰・監視検討を置換せず、開発用の明示操作を先行する案。コマンド名・wire拡張・期限は提案であり、現行仕様の確定/実装完了として扱わない。

## 確認できた事実

- 測定器用HOSTはWaveshare RP2350-USB-A（WAVESHARE-30274）、QR用HOSTはRP2350-USB-C。両基板を混同しない。根拠: [接続仕様](../USB_HOST_Interconnect_Spec.md)。
- 測定器用HOSTのrelay_main.cにはUART0 GP0 TX/GP1 RX、115200/8N1の双方向処理がある。親は既存PIOのGP12 TX/GP13 RXを使う。RST/BOOT専用線なしで管理要求の経路を追加できる。
- 現行X1はH/h/Q/A/T/R/Eのみ。C/Python両方のcodecと親/子の受付処理に拡張が必要。通常Q本文をそのまま機器へ中継するため、EXT_SEND/EXT_QUERYの本文にRESETやBOOTSELを書く方法は採らない。
- 親の通常startはfault時にRECOVERY_REQUIREDで拒否する。HOST側もQをfault/ready/session条件で拒否する。管理入口を通常start/Qへ追加するだけでは、fault時やUSB未接続時に操作できない。
- HOSTは起動時にget_rand_64でnonceを生成し、H/hでchip ID/FW/状態を照合する。管理要求でも個体と起動世代を照合する材料がある。ただし既存Hは親nonce変更でPARENT_RESTART faultを起こし得るため、管理照会から既存Hを無条件に流用しない。
- 固定SDK 2.2.0にはwatchdog_rebootとreset_usb_bootがある。前者で通常起動、後者でBOOTSELへの移行を実装できる。通常リセットをRUN接点操作と全て同一とは説明しない。
- 現行中継FWではUSB stdioが無効。通常動作中のpicotoolによる移行を既存機能として利用できるとは扱わない。
- 過去にBOOTSEL状態の個体へ、対象serial指定のpicotool rebootで通常起動した記録がある。BOOTSEL中のUARTコマンド復帰とは別経路。[記録](../USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Host_Bootsel_Recovery_20261121_Rev0.md)。
- QR現行FWはUART TXのみで管理RX処理がない。実配線の親→QR HOST戻り線は未確認。測定器HOST向けの改修だけでQRにも使えるとは扱わない。

## 操作者から見たコマンド案

入口は既存ATE接続を使う開発用コマンドとする。親Pico自体、NF55G、7355本体をリセットしない。第一段階の対象は測定器用HOSTだけに限定する。

| コマンド案 | 動作 | 完了確認 |
|---|---|---|
| HOST_INFO? METER | 個体/FW/起動nonce/USB状態/FAULT/管理機能対応を取得 | 対象IDと新しい照会への相関が一致 |
| HOST_RESET METER | 対象HOSTを通常FWへ再起動 | 同一個体・FW照合と起動nonce変更。USB READYとは別に通知 |
| HOST_BOOTSEL METER | 対象HOSTをROMのUSB書込みモードへ移行 | UARTでは受理まで。PCからBOOTSEL個体を照会して完了確認 |

応答はRESET_ACCEPTED/BOOTSEL_ACCEPTED（受理）とRESET_DONE（再起動確認）を分ける。BOOTSEL_ACCEPTEDだけでPC認識済みとは返さない。BUSY、UNSUPPORTED、対象不一致、期限超過、結果不明を区別する。名称・応答文字列・期限の数値は実装仕様で確定する。

初版は要求処理中の強制中断を設けずBUSY拒否とする。NF55G/ATE処理および対象外部要求がidleの時に、明示操作で実行する。機器timeout後に要求処理が終わりFAULTを保持した状態では、HOSTが応答可能なら管理操作を受付可能にする。FAULTだから無条件でBUSYとはしない。

## 実装構成案

1. 親は通常中継と分けた管理状態機械を持つ。対象リンクだけの新規要求を停止し、freshな管理照会で対象ID・FW・boot nonce・対応能力を取得する。旧FWならUNSUPPORTEDとして停止し、自動で通常Qや別命令へ置換しない。
2. X1の外枠/CRC/長さ上限を利用する管理拡張を設け、C/Python双方で識別する。具体的kindとpayloadは実装仕様で定める。管理照会は通常session未成立・FAULT・USB未接続でも処理でき、照会だけで通常session/faultを変更しない。
3. 管理実行要求は対象ID、現在boot nonce、freshなchallenge、要求IDと操作種別に結び付ける。不正CRC、旧世代、別個体、重複要求では実行しない。受理後は追加の通常要求と管理実行要求を拒否する。
4. 再起動前の診断（FAULT、直前要求ID、TX開始/完了、RX長等）を親RAMへ保持する。NF55G通信中のSD write/flushを行わず、Flashへの毎回保存を追加しない。
5. HOSTは受付応答を優先キューへ入れ、UART送出完了を有限期限で確認してから再起動する。FIFOへの投入だけを線上送出完了としない。mainループを無期限にブロックせず、送出期限超過時の実行/中止方針を仕様化する。結果不明時に親が同じ操作を自動再送しない。
6. 通常再起動はwatchdog_reboot(0, 0, delay_ms)、BOOTSELはreset_usb_boot(0, 0)を候補とする。GPIOによる疑似スイッチ操作は不要。SDK標準経路とPIO/IRQ/USBへの影響を実機確認する。
7. 通常再起動後は親の対象リンクの旧UART受信・組立・要求・sessionを破棄し、新しい起動nonceで照合する。親Pico全体のリセットを通常手順にしない。以前の要求/設定/測定を再送しない。
8. 再起動成立と測定再開可否を分離する。未完了要求の成否不明・既存CacheのINVALID規則を維持し、Host再起動だけで有効値/成功へ変えない。旧USB応答の境界が未確認ならRECOVERY_REQUIREDを維持する。機器本体へのRESET/自動SCPI初期化は追加しない。

## BOOTSELの給電・PC接続上の制約

コマンドによるBOOTSEL移行は端子追加なしで実装できる。しかし書込みはHOSTのネイティブUSBへPCのデータ接続が必要であり、PIO-USBの機器側ポートを代用しない。

BOOTSEL中はアプリのUART管理処理が動かないので、親からHOST_RESETを送って戻すことはできない。PC接続が成立すればpicotool rebootで戻す。通常FWが有効なら、電源再投入でも通常起動へ戻る。

したがって外部電源をOFFにしてPC給電へ切り替える既存書込み手順では、直前にコマンドで入れたBOOTSEL状態を引き継げない。BOOTSEL移行指令をFlashへ永続保存する仕組みは今回追加しない。

給電を維持したままネイティブUSBデータをPCへ接続できる構成（VBUSを適切に分離した接続等）が、回路・現物で成立するかを確認する必要がある。現行資料はPC給電と外部給電の同時接続を禁止している。普通のUSBケーブルを挿す手順へ独断で変更しない。VBUS線を切れば必ず動くとも断定しない。接続検知条件・電圧・逆給電を含む確認は別に行う。

給電/USB接続が未解決でも、UARTによる通常リセット機能の開発は独立して進められる。最初の対応FW導入は現行の手動BOOTSEL書込みが必要。この機能の導入前にコマンドで初回書込みできるとは扱わない。

## 変更対象と検証計画

変更対象案: 親ATE parser/dispatcher、external_instrument_linkとcontract、HOST relay_wire/relay_host/relay_main、SDK link設定、関連Host Unit/Mock試験、ATE一覧/通信契約/Module Interface/Test Specification/CHANGELOG。現在の作業ツリーにはCDC診断等の未コミット変更があるため、それらを保持し、採用候補と実機版を固定してから実装する。

| 検証 | 確認内容 |
|---|---|
| Host Unit/Mock | 正常/FAULT/USB未接続で管理照会と操作受付、BUSY拒否、旧FW対応拒否 |
| wire/誤操作 | CRC不正/過長/旧nonce/別個体/重複/遅着/本文中RESETで誤実行せず、機器へ管理本文を送らない |
| 受付と遷移 | ACKキュー満杯/送出途中/期限超過/ACK欠落でも無限待ち・自動再送なし |
| 親リンク | 同一個体・新nonceを確認、旧応答/旧session不採用、FAULT/Cacheを無条件に解除しない |
| ARM build | 固定SDK 2.2.0で通常/BOOTSEL APIのlinkと生成物の版/hashを確認 |
| 実機RESET | 対象個体だけが再起動、親/NF55G/他HOSTを維持、起動nonce変更、USB再列挙と再開可否を別記録 |
| 実機BOOTSEL | 給電・USB接続条件を確認後、UART受付→PC個体照会→picotool通常起動を確認 |

実装順は、(1)測定器HOSTのINFO/通常RESET、(2)BOOTSEL入口と給電維持PC接続の確認、(3)必要ならQRのRX経路・FW拡張。量産の自動復旧/WDTは別工程を維持する。

## 未確認事項と今回の実施範囲

未確認: 管理wire/応答/各期限、BOOTSEL中の給電維持PC接続、QR RXの現物結線、再起動後の旧機器応答境界、実機版/候補の最終固定。USB-HOST-RESET-01はOpen継続。RST/BOOT端子操作を必要条件にはしない。

今回はソース・固定SDK・既存記録の調査と本提案の保存のみ。コード/FW/配線/Flash変更・実機コマンド送信なし。Host Unit/Mock/ARM build/実機試験は未実施。文書リンクと差分を確認する。

## ソース根拠

- [HOST main](../../firmware/usb_submcu_external_meter_host/relay_main.c)、[HOST engine](../../firmware/usb_submcu_external_meter_host/relay_host.c)、[X1 codec](../../firmware/usb_submcu_external_meter_host/relay_wire.c)
- [親リンク](../../src/external_instrument_link.py)、[承認済み中継契約](../USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Interface_Spec_Rev1.md)
- [固定SDK bootrom.h](../../tools/usb_submcu/pico-sdk-2.2.0/src/rp2_common/pico_bootrom/include/pico/bootrom.h)、[watchdog.h](../../tools/usb_submcu/pico-sdk-2.2.0/src/rp2_common/hardware_watchdog/include/hardware/watchdog.h)
- [従来のHost状態クリア検討](Host_Communication_State_Reset_Rev2.md)、[監視/再起動検討](Host_Supervision_and_Software_Reset_Rev1.md)
