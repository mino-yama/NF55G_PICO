# RTC電池取付け後の時刻設定・再確認（2026-11-10）

ユーザー申告: RTCを取り外してリセットされた後、電池を取り付けた。現在時刻の設定・読戻しを依頼。電池装着後のバックアップ保持・RTCの起動を確認済みとは扱わない。

## 確認できた事実

- 対象Pico: COM6、unique_id `69f7d45962cfdfad`。ATE入口はCOM20、115200/8N1。開始時のIDNはNF55G_PICO_FIXTURE,Rev.0、通信IDLE。
- 2026-11-10 09:52:28 JST以降、RTC_DATETIME?は`ERR:NO_RTC`。
- PCの日本時間から`RTC_SET_20261110_095229`を送信したが、`ERR:[Errno 5] EIO`。正常設定応答は得られず、設定・読戻し・秒進行の確認は未完了。
- Pico ID照合後、I2C0、SDA=GP20、SCL=GP21、100kHzでスキャン。検出アドレスは空配列`[]`で、DS3231の0x68は検出されなかった。確認時のSDA/SCL読取レベルはともにHigh。
- スキャン後はsoft rebootで通常起動へ戻しCOM6を解放。ATEの確認接続COM20も解放。NF55GへのSC／CLOCK_SYNCや製品コマンドは送信していない。プログラム配置・配線変更・基板改造は行っていない。

## 未確認事項と次の確認

現在RTCがPico-Quad-Expanderへ再装着済みか、基板の向き・挿入位置、VCC／GND／SDA／SCLの接続、電圧実測は未確認。電源・接触・配線・基板故障のどれかを断定しない。電池の取付けだけでPicoとのI2C通信成立を確認したとは扱わない。

ユーザーにRTCの再装着・通常電源供給の状態を確認し、接続確認後に0x68検出→現在JST設定→即時読戻し→数秒後の進行確認の順で再試験する。電源断保持は別途確認し、DEV-RTC-01を独断でCloseしない。

証跡: [ATE要求・応答](../temp/rtc_battery_recheck_20261110_095228/rtc_set_readback.json)、[I2Cスキャン結果](../temp/rtc_battery_recheck_20261110_095228/i2c_scan.stdout.txt)、[スキャンstderr](../temp/rtc_battery_recheck_20261110_095228/i2c_scan.stderr.txt)。
