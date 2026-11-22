# Host通信経路・キャッシュリセット 検討 Rev.2

日付: 2026-11-21。NF55G Pico治具案件。

## ユーザー訂正による目的の確定

目的は7355本体やQRリーダー本体のリセットではなく、通信経路上の問題に備えたHostマイコン内のキャッシュ/バッファ/通信管理状態のリセットである。今後のデバッグでエラー情報を取得し、復旧できない場合の手段を用意する。

RUN配線を引き出せず量産ユーザーのボタン操作にも依存できないという制約、Host監視/WDT/親Picoからのリセット指令/Host受付入口を検討する要件は維持する。機器側へのRESET/SCPI初期化、機器の電源再投入を本機能へ含めない。

Rev.0/Rev.1で機器本体の復旧まで広げた記述は今回の目的を表さない。本Rev.2を目的・対象範囲の現行記録とする。Host内状態クリアとHost再起動のどちらを採用するかは、効果と停止条件をデバッグで比較して決める。

## 対象状態と現行実装の確認事実

「キャッシュ」は以下の通信保持状態を指す。Host内の通信バッファと、親Picoの製品/測定Cache、CPUハードウェアキャッシュは区別する。CPUキャッシュ保守操作を本件の解決策として想定しない。

| 対象 | 現行ソースにある状態 | リセット時の設計対象 |
|---|---|---|
| CDC Host要求管理 | request、command/response配列、長さ、pending、tx_started/tx_done/response_done、期限、fault | 前要求を終了・失効させ、次要求に持ち越さない |
| CDC Host UART | フレーム途中、drop、前byte、ハードウェアFIFO、送信outboxと送出位置 | 途中フレーム/旧応答を破棄し、新しい境界へ同期 |
| CDC Host USB | TinyUSB送受信FIFO、実行中転送、callback、usb_inflight/offset、設定処理epoch等 | 所有中の転送と状態の整合を保って初期化する |
| CDC Hostリンク | bound、session、request high_watermark | 世代を更新し、古い要求を再採用しない |
| QR Host | decoderの途中文字/桁/キー/修飾キー/active/discarding、stream FIFO、UART出力途中 | 部分QRと旧出力を破棄し、次の読取り境界へ同期 |
| 親Picoの対象リンク | パーサー、送受信Queue、pending、fault、session、対象取得との対応 | Hostのクリアに合わせて対象経路を再確立 |

根拠はrelay_host.h/relay_main.c、qr_alt_decoder.h、probe_stream.h、external_instrument_link.py。現行CDCに状態クリア専用APIはなく、faultは保持される。QRは現行UART送信専用で、管理受信口の追加が必要。

## 復旧手段の候補

| 手段 | 対象と使い分け | 留意点 |
|---|---|---|
| 通信状態クリア指令 | Hostが動作中で、滞留バッファやfault/途中要求を整理したい場合 | main/IRQ/callback/転送所有権を整合させてから初期化する |
| 親指令によるHost再起動 | 通信状態の部分初期化で復旧しない、または一括再初期化が適切な場合 | Host MCUだけを再起動。機器本体へのRESET指令は送らない |
| Host内蔵WDT | mainや必要な処理が停止して親指令を受け付けられない場合 | 機器応答timeoutやQR無入力とは分けて監視する |

状態クリアはRAMのmemsetやfault=falseだけでは成立しない。USB転送中のbuffer/offsetだけを消すと遅いcallbackが新しい状態を更新したり、旧コマンドの残りが送信されたりするため、先に処理を停止/隔離する。固定PIO USBドライバの停止・キャンセル・再開の成立範囲を調べ、保証できない範囲はHost再起動案と比較する。通常業務のfault保持仕様を無断で解除しない。

## 親指令とHost受付入口の案

管理操作として状態照会、診断snapshot、通信状態クリア、Host再起動を分ける。正式名称/フレーム種別/ATE外部公開は未確定。

- 通常の7355向け本文/QRデータと別の管理要求として振り分け、機器へ転送しない。
- FAULT/USB未接続/通常要求中でも管理受付を巡回する。main停止時はWDTで補完する。
- CRC/長さ/対象Host/管理世代/要求IDを照合し、不正・旧要求・重複でクリア/再起動しない。通常sessionが成立しないFAULT時にも使える管理照合を設計する。
- 親は対象経路だけを停止・復帰させ、他方のHost、ATE/NF55G通信、既存GPIO割付を維持する。
- QRの親→Host UART線は現物確認が必要。RUN配線は追加しないが、UART受信線がなければ指令受付は成立しない。

## 状態クリアの処理順序案

1. 親が対象系統の新規要求を止め、直前エラー・要求ID・送信開始/完了・受信長・Queue/dropを保存する。
2. Hostは管理要求を照合し、新規通常送信を止める。進行中要求は中断として記録し、送信後の成否不明は維持する。関連取得Cacheを親でINVALIDとする。
3. USB転送/IRQ/callbackの所有を整理し、旧世代処理を隔離する。状態クリア後に古いcallbackが到着しても新状態を変更させない。
4. 対象のUART/USB保持データ、途中要求/途中QR、送信Queueを整理する。診断snapshotと累積エラー履歴はクリア対象から分離して保存する。
5. 新しい通信世代へ切り替える。Host再起動時は新boot IDを使い、再起動しない状態クリアでも別のリンク世代を更新する。親側も旧要求/旧応答を失効させる。
6. 管理応答で「クリア受理」「Host内クリア完了」「通信再開可能」を区別する。Host再起動の場合は新boot ID確認で再起動を判定する。

バッファを消しただけで旧データの境界が確定したとは扱わない。USBから遅れて届く旧7355応答や途中QRの後半が新要求へ混入する可能性は、通信経路の受入項目として残す。これを理由に機器RESET/SCPI初期化を本機能へ追加しない。境界を確認できない条件は復旧未完了として返し、直前コマンドを自動再送しない。

## 動作監視・WDT・記録

Hostはmain/USB/UART処理の進捗、USB状態、FAULT、boot/リンク世代、最終要求と送信段階を報告する案とする。親はHeartbeat停止と機器応答timeoutを分ける。WDTは必要な処理の進捗を条件に更新し、単に通信faultだから更新を止める設計にはしない。タイマーIRQで無条件に更新してmain停止を隠さない。

診断は親のRAM Queueへ保持し、NF55G通信中にSD write/flushを行わない。クリア前snapshotが取れないハングでは、取得済み周期報告と再起動要因を残す。詳細が得られなければ不明として記録する。WDT期限・発火条件・保持領域・再起動上限は未確定。

## デバッグ・受入案

- バッファ滞留、UART途中フレーム、応答組立途中、送信outbox残留、fault保持、USB転送中、QR途中読取りを個別に再現する。
- 量産要件（2026-11-21ユーザー指定、FW実装はCDCデバッグ完了後）: 7355 USB-Bの接続/切断復帰を操作者の手動RESETに依存させない。idle/要求中のunmount、7355電源後投入、Host起動後USB-B接続、連続抜差しを別条件で受入する。現在要求のambiguous処理、旧CDCデータ/遅延callback隔離、CDC再設定、Host/親session世代切替、再接続後のREADY条件を定義し、自動再送せずATE/NF55G/SD/他Host Timingを阻害しないことを確認する。機器本体RESET/SCPI初期化は対象外。実装方式と測定再開条件は[USB-RELAY-HOTPLUG-01](../Open_Issues.md)でOpen管理する。
- 同じ条件で状態クリアとHost再起動の効果を比較する。クリア後は旧要求の残り送信、古いcallback反映、旧応答/QR後半混入、重複実行がないことを確認する。
- FAULT/USB未接続中の管理受付、不正/重複/旧世代指令の拒否、管理応答欠落を確認する。
- main停止を注入してWDT復帰を確認し、正常な待機/機器応答待ちで誤発火しないことを確認する。
- 機器向けRESET/SCPI初期化等が送信されないこと、対象外Host/ATE/NF55G/SD処理へ影響しないことを確認する。

## 今回の変更と残事項

目的の訂正と検討資料/索引の更新のみ。コード/Flash/配線変更、状態クリア、Host再起動、実機送信、Host Unit/Mock試験は行っていない。文書リンクと差分形式を確認する。

USB-HOST-RESET-01およびUSB-RELAY-HOTPLUG-01はOpen継続。量産時のUSB-B接続/切断を操作者の手動RESET/RUNに依存させないFW対応をCDCデバッグ完了後に実装する要件を記録した。停止/転送所有権整理、旧応答排除、session世代切替と再接続後のREADY条件は未確定。WDT条件/期限と実機の反復/負荷受入も未完了。Host状態リセットの対象は確定したが各方式/設計値は未確定。

## 参照

- [CDC状態](../../firmware/usb_submcu_external_meter_host/relay_host.h) / [CDC I/O](../../firmware/usb_submcu_external_meter_host/relay_main.c)
- [QR decoder](../../firmware/usb_submcu_host_probe/qr_alt_decoder.h) / [QR stream](../../firmware/usb_submcu_host_probe/probe_stream.h)
- [親リンク](../../src/external_instrument_link.py)
- [Rev.1](Host_Supervision_and_Software_Reset_Rev1.md)（監視/管理入口の参考。目的は本Rev.2を優先）
