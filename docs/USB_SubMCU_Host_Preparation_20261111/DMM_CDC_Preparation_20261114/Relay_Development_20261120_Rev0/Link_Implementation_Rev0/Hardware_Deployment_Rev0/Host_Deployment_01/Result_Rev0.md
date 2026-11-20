# Host中継FW 配置結果 Rev.0

2026-11-20 JST。ユーザーの指定準備完了を受け、対象Hostへ中継FWを配置。

- 書込み前: chipid 0xbfcf2edb84b0b37f、RP2350 A4、2048K、BOOTSEL、旧版meter-host-voltage-test-20261120.5。
- ビルドUF2と配置用コピーのSHA-256がともに 2f6faee45dbbad016fe8470128e7cce9cb1c6e05980d053d4d83880b24a3906c と一致。
- 現行.5全Flash 2,097,152 byteを別名退避し、save -a -vのFlash照合OK。SHA-256: 86a61f8d704c330705980cfa44cefde638de38d43bebe303c1e5feb1192ecd7d。
- 対象serial指定のload -vで中継FWを書込み、Flash verify OK。
- 書込み後infoでmeter-host-relay-20261120.1、同chipid、BOOTSELを確認。rebootは行っていない。
- 親Picoのファイル変更・中継通信・7355への送信は未実施。親配置後に実機縦通しを確認する。

## 証跡

[書込み前info](before_info.log)／[旧.5退避・照合](backup_verify.log)／[書込み照合](load_verify.log)／[書込み後info](after_info.log)／[配置manifest](Deployment_Manifest.json)

## 次の作業

HostのPC USB-Cを外して無給電にする。外部5Vと親子信号線を切り離した親PicoだけをPC USBへ通常接続し、現在のポート・実ID・既存ファイルを確認する。親はBOOTSELへ入れず、MicroPythonの既存ファイルを退避してから配置する。

コード変更なし。今回の検証は個体/metadata確認、全Flash退避・照合、UF2照合・書込み・Flash verify。ソフト回帰は直前446件成功を継承し、再実行していない。
