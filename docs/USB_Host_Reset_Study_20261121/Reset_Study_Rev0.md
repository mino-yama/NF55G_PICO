# NF55G Pico治具 USB HOSTリセット方法の検討 Rev.0

日付: 2026-11-21

対象: QR用RP2350-USB-C、外部測定器7355用RP2350-USB-A、および親Picoとの通信復帰。
ユーザー指定によりNF55G Pico治具案件内に保存する。設計検討であり、リセット方式の採用確定や実機検証結果ではない。

## 確認できた事実

- 既存方針はRUNパッド施工・外部RESET駆動回路を進めず、手動RESET/電源再投入をデバッグで比較するもの。親GP14/22は汎用予備のまま維持する。
- QR現行ソースはUART送信のみで、親からのリセット指令の受信処理はない。ContinuousビルドにはUSB開始前の3秒待ちがあるが、起動改善効果は実機未確認。
- CDC Hostの`relay_host_fail()`はfaultを保持する。タイムアウト、要求後の切断等で停止し、再接続やHELLOだけでfaultを解除しない。再起動時にHost nonceを生成する。
- 親`ExternalInstrumentLink`も異常後のfault/sessionを保持する。通常入口に復帰専用APIはない。Hostだけ再起動しても親のfaultや旧sessionは解消しない。逆に親だけを再起動すると、既存Hostは新しい親nonceをPARENT_RESTARTとしてfaultにする場合がある。
- 固定TinyUSBのPIO Hostドライバには`hcd_deinit()`の実装が見当たらず、共通側のweak stubはfalseを返す。API名の存在だけでUSB停止・再初期化が成立するとは判断できない。
- 既存回路資料ではHostのVBUS/VSYSが共通であり、MCUのRESETをUSB給電のOFFと同一視できない。QR/CDC Hostは外部電源を共用する方針で、共通電源を切ると両系統へ影響する。

ソース確認は現在の作業ツリーを対象とする。各実機の書込済み版と一致するかは試験前に識別する。

## 方法の比較・提案

| 方法 | 復帰対象・制限 | 現時点の扱い |
|---|---|---|
| 基板RESETボタン | Host MCUを再起動する。接続機器の電源断、機器内部の測定取消し、親リンク復帰を保証しない | 最初に比較する候補 |
| Host枝の電源OFF/ON | 対象枝を再起動する。QR電源も同時に切れるかは実配線次第。7355本体は別電源/別状態として扱う | RESETで復帰しない条件と比較。枝の分離・逆給電を事前確認 |
| 共通外部電源OFF/ON | 両Hostへ影響する。親PicoやQRへの影響範囲も実配線次第 | 全体起動試験として個別復帰とは区別 |
| UART指令→watchdog再起動 | RUN配線なしで実装できる候補。UART処理自体が停止した故障への対策は別途必要 | 未実装。指令契約、実行条件、親側の再接続を設計してから判断 |
| 自動watchdog | Host停止検出と再起動の候補。測定成否不明・旧応答問題は別に残る | 未実装。タイムアウトごとの自動再起動/再送は採用しない |
| USBスタックのみ再初期化 | PIO/IRQ/転送/FIFO/列挙状態を含む停止と再開の成立確認が必要 | 現段階で標準復帰手順にしない |

提案は手動RESETを第一候補、電源再投入を比較対象とする。採用決定ではない。RP2350のRUN/watchdogリセット機構は公式資料で確認できるが、接続機器までの清浄復帰は本構成で受入が必要。

## QR側の比較試験案

1. 電源投入前からログを採取し、Host版・個体ID、列挙、最初のQRと連続読取りを記録する。
2. 認識しない条件や途中切断を分けて記録し、HostのみRESETした場合を確認する。
3. 別試行でQR給電も切れる電源再投入と比較する。実際に給電が切れた範囲と再起動状態を記録する。
4. 部分QRの破棄、旧データ混入、欠落/重複、再読取り、UART欠落カウンタを確認する。QRを読まない時間だけで故障と判断しない。

## CDC側の復帰試験案

1. 新規要求を止め、要求原文・送信状態・エラー・時刻を記録する。送信後の成否不明を保持し、自動再送しない。
2. 測定器の未完了動作と旧応答を解消する方法を、メーカー手順と実機で確立する。Host RESET、USB抜き差し、DTR変更、FIFO破棄だけで解消したとは扱わない。
3. 現行実装ではHostと親リンクの両方の初期化が必要。親Pico全体の再起動はATE/NF55G通信へ影響するため、保守停止中に実施する比較候補とし、通常運転中に自動実行しない。片側の起動途中に要求を送らず、HostのUSB初期化完了後に新sessionで接続する。
4. 清浄状態を確認後、明示的な識別/設定Queryで新しい応答を確認する。レンジ等はATE指示値で再確認し、独自補正しない。測定・設定の再実行は成否不明の扱いを解決してから行う。
5. 旧session/遅延応答が新要求の結果として採用されないこと、正常要求一件に一応答、復帰時間、他系統への影響を確認する。

初期化専用APIによる親リンクだけの復帰は将来案であり、現行機能として操作手順に含めない。旧データ排除の待ち時間・判定条件は未確定で、数値を推定しない。

## 未確認事項・残Issue

- 手動RESETで解消できる故障の範囲、電源再投入が必要な条件、復帰時間と再現性。
- 個別枝の電源遮断可否、USB/UARTからの逆給電、共通電源操作の影響範囲。
- 7355の未完了処理・旧応答を解消する正式手順と、その完了判定。
- 親Pico全体を再起動せず、対象リンクだけを清浄復帰させるAPI/ATE契約の必要性。
- ソフトRESET指令、自動watchdog、USB再初期化方式の採否。

関連IssueはCloseしない。今回の変更は検討資料と索引への記録のみ。コード/配線/Flash/実機電源操作を変更していない。Host Unit/Mockおよび実機試験は未実施。

## 根拠

- [従来RESET方針・異常/正常交互試験](../USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Error_Normal_Alternation_Plan_Rev0/Plan_and_Reset_Decision_Rev0.md)
- [USB HOST接続仕様](../USB_HOST_Interconnect_Spec.md)
- [QR現行ソース](../../firmware/usb_submcu_host_probe/main.c)
- [CDC Host状態管理](../../firmware/usb_submcu_external_meter_host/relay_host.c) / [CDC制御](../../firmware/usb_submcu_external_meter_host/relay_main.c)
- [親リンク](../../src/external_instrument_link.py)
- [固定PIO Hostドライバ](../../tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src/portable/raspberrypi/pio_usb/hcd_pio_usb.c) / [TinyUSB共通処理](../../tools/usb_submcu/pico-sdk-2.2.0/lib/tinyusb/src/host/usbh.c)
- [RP2350公式データシート](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-2-rp2350-datasheet.pdf?disposition=inline) §12.9 watchdog / chip-level reset
- [Waveshare RP2350-USB-A公式Wiki](https://www.waveshare.com/wiki/RP2350-USB-A)
