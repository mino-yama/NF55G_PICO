# CDC転送失敗の診断候補 2026-11-22 Rev.0

## 確認事実

2026-11-22 Scheduler修正後の実機共存再試験: 新Host nonce11F71FF28CE2AC1D/READYとIDN照合成功、親は再起動せず再開。29回目READでHost A/T→E=TIMEOUT|1となり停止（2秒の明示期限、Rなし）。D1はRetry0、SD/RTC OK、終了後もログdrop0/Queue0。親PIOエラーなし、X1 frame decode error0。SD排出飢餓とは別の未確定事象として記録し自動再送しない。CDC transfer失敗をTIMEOUTと区別する候補.22.1を準備、全464回帰成功、ARMビルド/link成功・metadata/ELF wrap参照照合済み・未配置。

- [実機結果](NF_Coexist_02/result.json)、[全ATE応答](NF_Coexist_02/requests.json)、[Host原記録](NF_Coexist_02/host.raw)、[RAM snapshot](NF_Coexist_02/ram_snapshot.json)。Hostのrequest=0x1E、mode=1、期限0x7D0、A/T/E、E原文TIMEOUT|1。親の後付け補正ではなくHost自身のtimeout。
- 元のSD CSVを退避済み。filename /sd/BANK_A/20261122_161735.csv、32511 byte、SHA-256 c5f59f7714044e44f6a57e3ad03def9086d84e34dd2717b1c6f4c890e0d4f284。[CSV](NF_Coexist_02/20261122_161735.csv)。
- 固定SDK2.2.0のcdc_host.c: cdch_xfer_cbは非SUCCESS時にTU_ASSERTでreturnする。通常のRX完了処理/アプリRX callback/次のread_xferには進まない。今回その転送エラーが発生したかは未確認。
- 7355の応答生成が2秒を超えた可能性、USB transfer failureで受信が止まった可能性等を区別できていない。単にtimeoutを延長して合格とは扱わない。明示要求期限の比較は後続の診断条件として分ける。

## 候補.22.1の変更

- relay_cdc_guard.c/.hを追加し、SDK class driverのcdch_xfer_cbをlinker --wrapで観測。SDK原典は変更しない。
- mountで照合済みCDC device addressとrelay_host_tを登録し、umountで解除する。対象以外/解除後のcallbackは元の処理へ渡す。
- 対象CDCの非SUCCESS transferはendpoint方向によりUSB_RX_XFER/USB_TX_XFERとしてrelay_host_failへ通知。現在要求があれば既存E=理由|ambiguousを返し、fault保持する。USB TX開始前0、開始後1。元の非SUCCESS callbackへ入らず再試行・fault解除・機器設定・測定の再実行をしない。
- SUCCESS時は元のSDK処理へ渡す。フレーム種別・payload上限・CRC/session/request契約は変更しない。error理由の識別を追加する。
- Host版はmeter-host-relay-20261122.1。親は既存FW prefix照合のまま、今回の診断のための親変更は不要。
- この候補は診断と早期エラー通知であり、今回の根本原因を修正済みとは扱わない。旧callback/同一USB address再利用の一般的な転送世代保証や自動復旧を追加したものではない。

## 検証・配置前条件

実C guardをnativeへ組み込み、成功/別deviceエラーの委譲、unmount解除後の委譲、送信前RX失敗のAMBIGUOUS=0、送信後RX/TX失敗のAMBIGUOUS=1、fault保持/後続拒否を検証。全Host Unit/Mockは464件成功、14.708秒。

- [guardリンク試験](Transfer_Guard_Unit.log)
- [全回帰](Transfer_Guard_All_Unit.log)
- [ARMビルド](Transfer_Guard_Build.log)

ARM link成功。UF2 metadataは.22.1 / RP2350 ARM Secure / GP0/1 UART / GP12/13 USB / SDK2.2.0。ELFのCDC driver table 0x1000964C内のcallback pointerが0x10001B81（__wrap_cdch_xfer_cbのThumb pointer）であることを確認。候補UF2 94720 byte、SHA-256 6d2bc8071472e2d63c5f1a2f10931cfcccdd09b5903679064d8bf25292efaed3。[固定候補manifest](Transfer_Guard_Candidate/manifest.json)、[ELF table](Transfer_Guard_Table_Verification.log)。次に対象Hostの全Flash退避・verify・配置・再起動・H/IDN照合へ進む。既存のHost単独給電BOOTSEL書込み手順を使用する。未配置段階で実機反映済みとはしない。

## 現在状態と残事項

親は通信停止後のREPL、Logger inactive/drop0/Queue0、外部リンクfault保持。Host書込み準備として対象UID・通信idleを照合後、外部PIO SM4/5停止・GP12/13入力化を実施済み（NF55G UARTは変更なし）。Host単独USB-C給電/BOOTSEL準備の回答待ち。7355の一時TRIG delayは前工程で0秒へ復元済み。追加のREAD/設定/NF55G送信なし。

USB-CDC-SD-01は修正版の観測範囲でdrop0だが、50回共存は未完了。長期負荷/同期SD Timing/QR共存/量産自動復旧/測定Cache接続と共にOpen継続。実測・推測・未確認を区別し、Issueは独断でCloseしない。

## 配置結果（後続追記）

ユーザーがHost単独USB-C/BOOTSEL準備完了を回答後、serial BFCF2EDB84B0B37F・現行.21.1・BOOTSELを照合。全Flash2,097,152 byteをsave -a -v退避・verify（SHA 5d429adf838c62d68c8e9f2182db553e5237cb0958da53b7220472d3ef342dbe）。候補.22.1をload -vしverify成功、配置後版・同個体をinfo照合。rebootを行わずBOOTSELで保持した。[配置manifest](Transfer_Guard_Deployment_01/manifest.json)、[操作ログ](Transfer_Guard_Deployment_01/operations.json)、[全Flash退避](Transfer_Guard_Deployment_01/host_flash_before.bin)。現在はユーザーによる無給電での配線復元・Host通常起動の回答待ち。親の外部PIOは停止・GP12/13入力、Logger inactive、REPL停止。

## 配線復元後の起動確認（後続追記）

ユーザーが配線復元・Host通常起動完了を回答。親RAM診断を起動し、親nonce AEBFF8CD13A17FFEでHを120回送信したがhは未受信、FrameReader decode error0で終了。機器Q/READ/設定は送っていない。[診断原記録](Transfer_Guard_Deployment_01/runtime_hello.log)。この結果だけでHost FW停止や配線不良を断定しない。

Host TXのCOM22受動採取はPCプロセス起動のOSアクセス拒否で開始できず、Host送信線の無出力を実測した記録ではない。実行経路をnative cmdへ切り替え、完了したPC側mpremote診断だけを終了してCOM6を解放した。親RAM runtimeは同じnonceのまま維持、機器要求を出さず待機。BOOT用ボタンを離してCDC HostのRSTを1回押す操作を依頼し、回答待ち。次回は親を再起動せずH/IDNを一回照合し、新版.22.1・新Host nonce・READYの成立後にだけ共存試験へ進む。起動確認不成立なら追加測定をしない。

## RST後・配線確認後の照合（後続追記）

ユーザーのHost RST完了後、親を再起動せずATE IDN入口を一度実行。H応答なし、ATEはTIMEOUT/AMBIGUOUS=0、同時COM22受動採取0 byte、機器Q送信を確認できず停止。[結果](transfer_guard_retest_idn/result.json)。ユーザーは親GP12→HostGP1、HostGP0→親GP13、GND共通、COM22 RX→HostGP0の4項目を確認済みと回答。

親の既存app/nonceを維持するRAM H診断を開始（新しいpublic復旧APIやfault解除ではない）。ユーザーが7355 USB-B抜線/Host RST完了を回答後、新Host nonce351A9A9718F8D296、版.22.1、READYを3回受信。Pico decoder error0・PIO errorなし。[観測記録](Transfer_Guard_Deployment_01/rst_after_usb_isolation_observation.json)。新版の実行開始は確認できたが、USB-B抜線の申告とREADYが食い違うため、現在の7355本体USB-B端子が空かを確認中。追加IDN/測定/設定は送っていない。診断終了後は親REPL停止、両COM解放。
