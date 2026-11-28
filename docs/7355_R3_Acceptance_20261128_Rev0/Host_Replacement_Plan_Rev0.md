# 交換用HOSTの通常FW配置手順 Rev.0

実施後追記：新個体73AD3A60D10514E9へ配置・独立verify、親の新ID反映・再起動後37件SHA一致まで完了。通常構成の情報照会はtimeout継続。[配置・通信確認結果](host_replacement_01/Result.md)。以下の未接続記載は準備時点の履歴。

2026-11-28。ユーザーがUSB HOST CDCマイコンを新しい基板へ交換し、最新FW配置を指示した。同じ復旧案件として、このフォルダの`host_replacement_01/`へ結果を保存する。

使用する通常FWは現行ソースのrelayターゲットと一致する`meter-host-relay-20261125.2`。検証済みUF2は`candidate_20261125_105200_326526/usb_submcu_external_meter_relay.uf2`、SHA-256は`088e6e2a11b2ea333e9de66af34dfe2558ab5d2c7a9ffbc6368110329d7035e4`。一時診断版は使用しない。

1. 交換用HOSTをPC USB単独給電のBOOTSELで接続。親・QR・旧HOSTの既知IDを除外し、新個体ID、RP2350、Flash 2 MiBを確認する。
2. 交換基板の現在Flash全2 MiBを退避・独立verifyし、SHAを保存する。
3. 通常FWをload -v、独立verify、版読戻しし、接続復帰まではBOOTSELを維持する。失敗時は新基板から退避したFlashへ復元・verifyする。
4. 親の確認済み37件SHAを照合し、configのEXTERNAL_HOST_CHIPIDだけを新個体IDへ変更。QR双方向・RTC・校正等は保持する。旧設定退避、事前compile、原子的配置、37件読戻し一致後に親を通常再起動する。
5. ユーザーがHOST書込み用PC USBを外して元の固定接続・外部給電・7355 USBへ戻す。PC USBと外部5Vは同時給電しない。
6. 指定のPC→ATE入口→Pico→HOST→7355経路でHOST_INFOと7355 IDN、通信／SD／dropを確認する。書込みverifyと通常通信の復旧は別々に判定する。

初期確認ではBOOTSEL機器は未列挙。接続待ちであり、交換基板への書込みや親のID変更はまだ行っていない。スクリプトは`scripts/replace_meter_host_20261128.py`。配置完了後に個体ID・ハッシュ・通信結果を別の結果ファイルへ記録する。
