# 測定器HOST通常RST 引継ぎ・追加デバッグ Rev.0

後続のユーザー指示による[7355通信再開確認](CDC_Resume_01/Result_Rev0.md): 同じ親runtime／RST後HOST nonceのままREADYと明示IDN一回成功。以下のNOT_READY／通信再開未確認は本RST試験時点の履歴として保持する。

2026-11-23。NF55G Pico試験治具案件。親管理コード／HOST .23.2配置と、実ATE経由の通常RST一回・新nonce照合まで完了。USB状態はNOT_READYで、7355通信再開は未確認。以下は開始時点から最終結果までの工程記録。

## 最終結果

- 固定SDK2.2.0／ARM GCC14.3.0／-Wall -Wextra -Werrorで.23.2の別build成功。[ARMログ](arm_build_v2.log)。UF2 100864 byte／SHA-256 `77ccbbb88f220131b4a319fd2b7edd2c639482d4f6879c6b29f2854a74859f69`。ELF 1035920 byte／`38ab438223657ce0c62ddbee79309a54a52468ab8a650db5b2bbdf4da9c4a3ec`。[固定manifest・source hash](package_manifest_v2.json)。.23.1候補と元Flashは保持。
- ARM mainの実呼出は`relay_host_take_reset`→条件分岐→`watchdog_reboot(0,0,10)`。[逆アセンブル](arm_main_v2.dis)。既存CDC guardとRAM受信wrapper `0x20000120`のリンクも維持。
- .23.2を同一HOSTへload -v／独立verifyし、picotoolで通常起動。実ATE COM7から下表3要求のみ送信し、HOST TXをCOM22で受動取得。[結果JSON](hil_result.json)、[親RAM診断](hil_parent.log)、[HOST raw](hil_host.raw)。

| 要求 | 実機結果 |
|---|---|
| HOST_INFO? METER | BFCF2EDB84B0B37F／.23.2／旧nonce D90F7FE8E7DFF8D5／NOT_READY |
| HOST_RESET METER | RESET_ACCEPTED／同じ個体・旧nonce |
| HOST_INFO? METER | RESET_DONE／旧nonce→CBFA8C2C4F42C7BA／NOT_READY |

通常RSTは1回のみで再送なし。試験中の親nonce `f2caeb2e46c95f01`不変、Cache metadata不変、NF55G送信試行0、親frame error0、Logger停止を確認。NF送信は試験専用RAM guardで禁止して計数した。実配置のparser／main／link／contractと実ATE／PIO／HOST UARTを使用し、親の18秒有限RAM試験が終了後にPIO4/5停止・GP12/13入力化した。HOSTはBOOTSELではなく.23.2通常FWで起動中。

NOT_READY状態からの管理RST成立という限定結果。7355へのIDN／READ／設定送信なし。USB READY、正常機器通信、既存親FAULTを保持した実機RST、遅着応答境界、長期／複合負荷は未確認。次は現物のUSB接続・計器の稼働条件を確認し、READY成立後に別のCDC試験へ進む。USB-HOST-RESET-01等はOpen維持。

## 開始時点の確認事実（履歴）

- ユーザー貼付けのChat引継ぎはcommit `37c6431`の実装記録と一致。Chat本文の直接閲覧は行っていない。
- 修正前Host Unit／Mock NF55G全472件成功（19.632秒）。[ログ](host_mock_tests.log)。
- RST候補UF2の再計算SHA-256は`9C32948FA4DF986AC53E377925535608B60F5D2B870FFB7EAF31C0A2C53C6427`。親Pythonのみ修正し、HOST C／UF2は変更なし。今回ARM再ビルドなし。
- ユーザーは接続について「全て接続済み」と回答。給電内訳は追加確認が必要。
- OS列挙でCOM6／2E8A:0005／SER 69F7D45962CFDFAD、COM7／056E:5004、COM22／1A86:5523を検出。
- COM6を自動resetなしの`mpremote resume run`で調査し、親実機ID `69f7d45962cfdfad`、MicroPython 1.27.0を確認。親はREPL停止状態。[配置一覧・hash](parent_inventory.log)。HOST送信・Flash変更なし。
- 実配置linkは10012 byte／SHA-256 `18defb0a1a55f2b88a8bc9baecc9429dd5e7380201f19cba73f46f4462c41fe2`。mainは15522 byte／`cbb7c94e70cf330c11af056a5f7ff7e05a31e11fc7228494450ce468a580a120`。新RST版未配置。
- `picotool info -a`でBOOTSEL機器なし。測定器HOSTの電源OFFや未接続を証明するものではない。

## 再現・修正

1. RST受理後、新boot確認INFOの前でも通常要求を開始できた。確認待ち中は`RECOVERY_REQUIRED`で拒否する。
2. INFOの新nonceを通常sessionとして登録していたが、HOSTはH/hで通常sessionをbindする。そのためRST_DONE後のQが無視された。INFOでは通常sessionを未確立とし、次の明示要求でH/h照合後にQを送る。

native C HOST＋Python親の追加試験で2件失敗を確認。[修正前51件中2件失敗](rst_before_fix.log)。既存親fault保持の追加試験も実施。実機USB受信0 byte問題の原因とは確定しない。

変更: `src/external_instrument_link.py`、`tests/test_external_instrument_link.py`。管理要求から機器コマンドを自動送信しない。試験のIDNはPCの模擬機器への明示要求。

## 検証結果

`.venv/Scripts/python.exe -B -m unittest discover -s tests -v`

全475件成功（21.055秒）。[修正後ログ](host_mock_after_fix.log)。native C／親連携は追加3件を含む51件。新boot未確認時のQ拒否、RST_DONE後H/h経由の明示IDN成功、既存親fault保持を確認。

## 開始時点の未確認・次工程（履歴）

給電条件を確認後、親実sourceと全Flashを退避・照合し、親mainの現物差分を保持して管理版を配置する。初回HOST導入には従来の手動BOOTSELが必要。ACK→同一個体／新nonce、親起動世代維持を実機検証する。USB READY／7355応答・旧応答境界は別項目。USB-HOST-RESET-01等はOpen継続。

今回、NF55G／7355へのコマンド送信、実機RST、Flash書込みは未実施。

後続確認: ユーザーから測定器HOSTはPC USB-C単独給電・外部5V切離しと回答。親srcを`parent_before/src`へ退避。実mainと候補との差は管理要求受付の追加のみ、configは実機の`EXTERNAL_INSTRUMENT_ENABLED=True`を保持する。親測定器UARTのPIO SM4/5を停止・GP12/13を入力化し、両SM inactiveを確認。[停止記録](parent_pio_stopped.log)。測定器HOSTの手動BOOTSEL接続を依頼中。

## 配置工程の進捗（後続追記）

ユーザーが測定器HOSTをBOOTSELへ接続。実個体BFCF2EDB84B0B37F／旧.22.2を照合し、全Flash2MBをsave -a -vで退避。SHA-256 `c862a1843476ec23cab85633e6ad371a26b43d15bd1537b70375cfd28b37aa09`。[退避記録](host_flash_backup.json)。.23.1をload -v／独立verifyし、起動せずBOOTSEL保持。

親COM6が一時OS一覧から消失し、配置前probeで停止した。親未書込みの段階。ユーザーが親の通常USB接続へ戻した後、実ID／全30source hashを再照合。全Flash4MBをsave -a -vで退避し、SHA-256 `526793b72abb3b51044dd7b5421004d16bfc74d7e166848e51291ce17fba904b`。[退避記録](parent_flash_backup.json)。親4ファイルを一時名で配置・実機compile／hash検証後renameし、configほか26sourceを保持。通常再起動後も全source hashと管理APIを照合し、PIO4/5停止・GP12/13入力化。[再起動後照合](parent_post_reboot_verify.log)。全操作出力は[操作台帳](deployment_operations.jsonl)。

## HOST再起動期限の追加修正

実機RST前のソース確認で、mainがreset due中に`watchdog_reboot(0,0,10)`を毎巡回呼ぶ経路を確認。固定SDKのwatchdog.cでは同APIがwatchdogを無効化して期限を再設定する。短い巡回で期限を延長し続ける懸念を特定した。旧.23.1を実機起動して再現した結果とは区別する。

`relay_host_take_reset`を追加し、ACK後の再起動要求を一度だけ消費、due／BUSYは再起動まで保持。relay_host.c/.h、relay_main.cの日本語コメントとCMake版を.23.2へ更新。追加native試験でACK前0回／ACK後1000巡回1回を確認。全Host Unit／Mock476件成功（19.505秒）。[最終回帰ログ](host_mock_final.log)。native C／親連携は52件。ARM／実機確認を継続する。
