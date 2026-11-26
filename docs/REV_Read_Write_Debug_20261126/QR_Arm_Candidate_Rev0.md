# 旧QR遅着対策の双方向診断版

2026-11-26、OI-23。前回は親PicoがAの到着と破棄を観測してからBの受付を開いた。今回の診断版では、AのHID読取が途中の時点で親が受付を要求し、QR用HOST側でAを完成まで処理して破棄したことを確認する。量産FWへの採用は検証後に判断する。 [前回実機結果](QR_Prearm_Boundary_Rev0.md)

## 実装

- QR用HOSTの診断ビルド `PROBE_QR_ARM=ON` でUART0のGP1/RXを使用する。親はGP8から115200 bps・8N1で `A`＋24桁の16進受付ID＋LFを送る。戻りの診断レコードは従来の76バイト枠を使う。種別16が同じ受付IDと旧QRの破棄フラグ、種別17が同じ受付IDと35文字のQR原文を返す。
- QR用HOSTは処理中の旧読取および異常後の破棄状態が終了し、Enter後のキー解放を受けてから受付応答を出す。次のQRを1件だけ公開する。切断・期限で受付を失効させ、応答後のデコーダ異常でも受付を解除する。親の診断は受付IDと応答後のレコード連番を確認し、Bの原文とSS候補を照合する。
- 診断は親のCOM6保守経路で一時実行する。既存のQR/SSコマンドの量産フローに組み込む前に、親GP8→QR用HOST GP1/RX、QR用HOST GP0/TX→親GP9、共通GNDを実機で照合する。診断からのSS送信は0件。

## 検証

- Host Unit／Mock NF55Gは551件成功。Cの実コードで、Aの最初のHID報告後、読取途中、Enter直前と直後に受付要求を入れ、旧Aが公開されず、受付確認後のBを1件だけ公開することを確認した。不正長・不正文字の要求、同一IDの再投入、期限の周回、受付取消も確認した。 [全回帰ログ](qr_arm_candidate_01/host_mock.log)
- `qr-arm-diag-20261126.1` のSDK 2.2.0 ARMビルドが完了。初回のビルドは時間切れとなり、生成済みの同じNinjaビルドから再開してリンクとUF2生成が成功した。picotoolでRP2350 ARM Secure、GP0/TX・GP1/RXと版を確認した。 [診断UF2](qr_arm_candidate_02/usb_submcu_host_probe.uf2) · [版とSHA-256](qr_arm_candidate_02/manifest.json) · [UF2情報](qr_arm_candidate_02/uf2_info.log) · [ビルド再開ログ](qr_arm_candidate_02/build_resume.log)
- RP2350実機では、まずAを単独表示して読む。親がHID進行中に受付要求を出し、QR用HOSTの受付応答に破棄フラグ1が含まれることを確認した後に、Bを単独表示して読む。Bの原文35文字・SS候補50文字・ログ欠落0を確認し、診断後はQR用HOSTの既存FWに復帰する。
- スキャナー内部でトリガー済みでも最初のHID報告がQR用HOSTに到着していない場合を識別できるかは未確認。実機試験ではBの操作を受付応答後に行う。

## 実機の準備状況

- 親GP8（物理11番）→QR用HOST GP1/RXを接続し、導通ありとユーザー実測。親の物理12番および13番への持続する導通なし。既存のQR用HOST GP0/TX→親GP9では、定期通知を3件連続受信。双方向のUART動作は実機試験で確認する。 [配線点検](QR_Return_Wiring_Check_Rev0.md)
- 書込み対象の過去記録はQR用HOST `A06FEA01012EC137`。実施時はBOOTSELで対象ID・現FWを照合し、全Flashを退避してから診断UF2を検証付きで書き込む。既存版 `qr-fixed-20261123.1` は復帰用として用意済み。今回の読み取り専用照会では親Picoの通信IDLE、SD OK、ログ欠落0、測定器HOST READYを確認した。 [既存版の書込み記録](../QR_Hardware_Integration_20261123_01/Deployment_Result_20261123_Rev0.md)

| 親PicoのGPIO | 親の物理ピン | 信号経路 |
|---|---:|---|
| GP8 | 11 | 親TX → QR用HOST GP1/RX（今回の追加対象） |
| GP9 | 12 | QR用HOST GP0/TX → 親RX |
| GP11 | 15 | QR・測定器用の割当なし |
| GP12 | 16 | 親TX → 測定器用HOST GP1/RX |
| GP13 | 17 | 測定器用HOST GP0/TX → 親RX |

親Picoの物理13番／18番をそれぞれQR用／測定器用の共通GNDに使える。UARTは3.3 V TTL。HOST側の端子は基板のGP0/TX・GP1/RX表示で照合する。 [既存の配線基準](../USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev1.md)

## 診断版の実機書込み

2026-11-26、PC単独給電のBOOTSELで `A06FEA01012EC137` を照合。旧版 `qr-fixed-20261123.1` の全Flash 2 MiBを退避して独立照合し、診断版 `qr-arm-diag-20261126.1` の書込みと独立照合を完了した。書込み直後のBOOTSEL情報で同じ個体ID・診断版を確認した。 [旧版情報](qr_arm_flash_20261126_133524_554951/before.log) · [退避データのSHA-256](qr_arm_flash_20261126_133524_554951/backup.sha256) · [書込み後の情報](qr_arm_flash_20261126_133524_554951/after.log)

T000985では親PicoのIDLEとSD OKを確認した後、QR用HOSTの定期通知が6秒以内に届かず、Aをスキャンする合図の前に試験を終了した。続く3秒の受動採取でもQR UARTの受信は0バイト。`TEST_END` はOK、親のログ欠落0。実機の固定配線と給電の復帰を確認して再試験する。 [初回実機ログ](run_20261126_QR_Arm_HIL_01/qr_arm_candidate_wire.log) · [受動採取ログ](run_20261126_QR_Arm_HIL_01/health_wire.log)

固定配線復帰後、T000986で定期通知とスキャナー認識を確認。AのHID受信中に受付IDを送ったが、同じIDの応答を8秒以内に受信できなかった。次の切り分けで親の送信フレーム先頭にLFを付け、GP8の出力を親自身の別PIOで受け直したところ送信原文と一致した。続いてアイドル中のQR用HOSTが同じIDの種別16を返したため、追加のGP8→GP1/RXを含む双方向UART通信が実機で成立した。最初の応答欠落とLFの因果関係は未確認。 [A受信中の試行](run_20261126_QR_Arm_HIL_02/qr_arm_candidate_wire.log) · [双方向UARTの照合ログ](run_20261126_QR_Arm_Link_01/qr_arm_candidate_wire.log)

## 旧QRの破棄とBの実機照合

- 1回目の再試行では、定期通知でAのHID途中状態を時間内に観測できず終了した。 [再試行ログ](run_20261126_QR_Arm_HIL_03/qr_arm_candidate_wire.log)
- T000989ではAのみをスキャンし、HID受信中の通知（連番313）を受けて受付要求を送った。QR用HOSTは連番314で同じ受付ID `EAEE30F6E19396DC00000001` と破棄フラグ1を返した。HID途中の通知から応答まで、HOSTの記録時刻差は734 ms。
- 応答後にスキャンしたBは、同じ受付IDで連番332に到着した。連番に欠落はなく、原文35文字 `US250A-CGXE-009491-101A032601000002` とSS候補50文字が期待値に一致した。SS送信0件、`TEST_END` OK、ログ欠落0件。試行終了後は親PicoのIDLEとSD OKを確認。測定器HOSTの既知の照会タイムアウトも再確認した。 [成功ログ](run_20261126_QR_Arm_HIL_04/qr_arm_candidate_wire.log)
- 量産ATEへの統合、最初のHID報告が遅れるケース、連続試験での再現性は未確認。OI-23を継続する。

## 元FWへの復元

2026-11-26 13:49 JST、退避した全Flash 2 MiBとSHA-256を確認し、同じQR用HOST `A06FEA01012EC137` に復元。独立照合はOK。復元後のBOOTSEL情報で `qr-fixed-20261123.1` を確認した。 [復元照合ログ](qr_arm_flash_20261126_134909_758150/restore_verify.log) · [復元後の情報](qr_arm_flash_20261126_134909_758150/restore_after.log)

固定配線の復帰後、親Picoの通常処理は通信IDLE、SD OK、ログ欠落0。QR UARTの3秒採取と親受信部を再初期化した後の8秒採取はいずれも0バイトで、QR用HOSTの起動とスキャナー認識は追加確認が必要。 [受動採取](qr_arm_flash_20261126_134909_758150/restored_health_wire.log) · [受信部再初期化後の採取](qr_arm_flash_20261126_134909_758150/restored_health_rebind_wire.log)

その後、固定配線を維持してQR用HOSTのRSTを1回操作。起動連番0の版 `qr-fixed-20261123.1` と連番1の個体ID `A06FEA01012EC137` を受信した。起動後4.575〜6.575秒にスキャナー認識あり・欠落0の定期通知を3件連続で受信。親Picoの通常処理再開後もIDLE、SD OK、ログ欠落0。測定器HOST照会は引き続き `ERR:HOST_TIMEOUT`。RSTを押さずに復帰しなかった原因は未確認。 [復元後の起動原文](qr_arm_flash_20261126_134909_758150/restored_boot_wire.log)
