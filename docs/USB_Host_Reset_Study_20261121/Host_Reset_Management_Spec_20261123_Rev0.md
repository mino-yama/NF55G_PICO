# 測定器HOST管理・通常RST仕様 Rev.0

記録日: 2026-11-23。対象は測定器用RP2350-USB-A HOSTのみ。現状: .23.2のARM build・配置・実ATE経由の通常RST一回／新nonce照合成功。USBはNOT_READYで機器通信再開未確認。全476回帰成功。詳細は[追加デバッグ・実機記録](Debug_20261123_01/Result_Rev0.md)。以下の.23.1ビルド／未確認記述は初版時点の履歴として保持。

## ATE入口

| ATE要求 | 動作 | 応答 |
|---|---|---|
| `HOST_INFO? METER` | 管理照会を一回送信し、対象ID・FW・起動nonce・状態を確認 | `OK:HOST_INFO:<ID>:<FW>:<NONCE>:<STATE>` |
| `HOST_RESET METER` | freshな情報照会後、対象HOSTの通常FW再起動を一回だけ要求 | ACK受信後 `OK:HOST_RESET_ACCEPTED:<ID>:<旧NONCE>` |
| `HOST_INFO? METER` (RST後) | 新しい起動nonceを別要求で確認 | `OK:HOST_RESET_DONE:<ID>:<旧NONCE>:<新NONCE>:<STATE>` |

管理要求はATE parserの独立カテゴリで処理し、`EXT_QUERY`/`EXT_SEND`やNF55G dispatcherへ渡さない。`METER`以外は未対応。`HOST_RESET`はBUSY時に拒否する。HOSTがFAULTまたはUSB未接続でも、UART処理が動作していれば情報照会と通常RST受付は可能。通常QがHOST内で進行中ならRSTは拒否する。

## X1管理wire

- 追加kind: `I` info request、`i` info response、`S` reset request、`K` reset accepted。既存`H/h/Q/A/T/R/E`の意味は変更しない。
- `I`: sessionは親nonce + 8 byte zero、request IDは単調増加、payloadは`<16文字HOST ID>|<16桁challenge>`。challengeは照会request IDと親時刻から作る大文字16桁hex。
- `i`: 要求ID・親nonceを反映し、session下位にHOST起動nonceを返す。payloadは`<ID>|<FW>|<READY/NOT_READY/BUSY/FAULT>|<challenge>`。
- `S`: `i`で照合した同一ID/親nonce/HOST nonceとchallengeを使う。RST request IDは直前のinfo request ID + 1に限る。challenge有効時間は2,000ms。期限・nonce・ID・要求IDの不一致、重複は実行しない。
- `K`: `RESET_ACCEPTED`。送信キュー投入だけでは再起動せず、ACK全byteをUARTへ出し終えて`uart_is_busy`が解除された後にのみ通常再起動を許可する。ACK期限は1,000ms。期限超過時は未送出ACKを捨て、再起動しない。
- 親はRST実行を自動再送しない。`S`送出後ACKが得られない場合は`ERR:HOST_RESULT_UNKNOWN`、親fault保持、session破棄とする。HOST_INFOによる新nonce確認まで通常リンク復帰を推定しない。

HOSTは`watchdog_reboot(0, 0, 10)`で通常起動へ戻す。BOOTSEL移行、親全体の再起動、NF55G/7355へのRESET/SCPI送信、WDT常時監視は対象外。

2026-11-23実装補正: `relay_host_take_reset`でACK送出後の再起動要求を一度だけ消費する。reset due／BUSYは再起動まで保持する。SDKの`watchdog_reboot`はwatchdogを無効化して期限を再設定するため、10ms期限をmainの毎巡回で設定し直さない。1000巡回で実行1回のnative試験を追加し、全476件成功。HOST版を`meter-host-relay-20261123.2`へ更新し、.23.1を比較用に保持。

2026-11-23実装補正: `relay_host_take_reset`でACK送出後の再起動要求を一度だけ消費する。reset due／BUSYは再起動まで保持する。SDKの`watchdog_reboot`はwatchdogを無効化して期限を再設定するため、10ms期限をmainの毎巡回で設定し直さない。1000巡回で実行1回のnative試験を追加し、全476件成功。HOST版を`meter-host-relay-20261123.2`へ更新し、.23.1を比較用に保持。

## 復帰境界

2026-11-23追加デバッグ: RST受理後は新boot確認INFO成立まで通常要求を`RECOVERY_REQUIRED`で拒否する。管理INFOは通常sessionをbindしないため、RST_DONEでは通常sessionを確立せず、次の明示要求でH/h照合後にQを送る。既存親faultは保持。追加3件を含め全475件成功、実機未配置。[検証記録](Debug_20261123_01/Result_Rev0.md)。

RST受理と再起動確認は別操作。HOST_INFOで同一個体・新nonceを確認しても、USB READYや7355応答境界の成立を意味しない。既存の親fault/ambiguousとCache INVALIDは解除しない。既存親faultがある場合は新nonce照合後も保持する。7355の遅着応答境界は未確定であり、RSTだけで測定再開/PASSとしない。

## 検証範囲

native C Host + Python親adapterの正常照会、FAULT照会、challenge/ID/nonce照合、BUSY、要求ID飛越し、重複、ACK送出期限、ACK欠落後のRESULT_UNKNOWNをHost Unit/Mockで検証する。NF55G/7355へのコマンド送信は0件。SDK 2.2.0 ARM buildと実機HOSTでのACK線上送出・通常再起動・新nonceは未確認。BOOTSEL/QR HOST/量産復旧は別Issue。

## ARM build記録

- 2026-11-23、固定Pico SDK 2.2.0 / ARM GCC 14.3.0 / RP2350 ARM Secureで`usb_submcu_external_meter_relay`を別build先`tmp/host_reset_build_20261123`へbuild。既存`firmware/usb_submcu_external_meter_host/build`と診断.22.3基準は変更なし。
- UF2: 100,864 byte、SHA-256 `9C32948FA4DF986AC53E377925535608B60F5D2B870FFB7EAF31C0A2C53C6427`。
- ELF: 1,035,644 byte、SHA-256 `397EB84DFE123C3851CE6777594BDB8ED9068F1F495C045DC55D690DF081F0DD`。
- picotool metadata: `meter-host-relay-20261123.1`、board `waveshare_rp2350_usb_a_host_eval`、SDK 2.2.0、image type ARM Secure。build成功は実機受入や配置許可を意味しない。
