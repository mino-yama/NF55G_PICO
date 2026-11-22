# 7355 電池入力・CDC復帰と逐次読出し 結果 Rev.0

2026-11-21。ユーザー申告で、昨日と同じ7355実機の入力へDC 9～10 Vの電池を接続。今回は逐次測定に使用する前の通信経路確認を実施した。入力電圧・極性・接続状態は本試行で独立測定していない。

## 確認結果

- Windowsの利用可能シリアルポート一覧はCOM7のみ。COM7はPnP上で状態OKのElecom USB-Serial Converter（056E:5004）。診断UARTのCOM22は利用可能一覧に現れず、Hostの受動ログは取得できなかった。
- COM7を57600/8N1、フロー制御なし、DTR/RTS OFFで開き、未読ATE応答がないことを確認。
- 治具識別Queryは `NF55G_PICO_FIXTURE,Rev.0` を返した。
- 7355向けの最初の `EXT_QUERY 2000 *IDN?` は `ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`。続けて送った機能、連続測定、AUTO、CONF、トリガ、サンプル数、遅延、機器エラーの各読み出しQueryも同じエラーで拒否された。
- このため7355の現在状態は取得できず、7355応答やSCPIコマンドがHostまで届いた証拠もない。`READ?`は送信していない。

## 2026-11-21 電源投入順/USB-B後接続の比較

- 比較前Queryで7355 IDN、DCV、連続OFF、AUTO ON、CONF約20 V、IMM/Trigger/Sample各1、delay 0、機器エラー0を確認。状態rawは[temp/meter_ate_power_order_precheck_20261121_01.raw](../../../temp/meter_ate_power_order_precheck_20261121_01.raw)、399 byte、SHA-256 `C830164DEE554F9A9CD21BFD03D11DB11712C40817372AE8E23BA7E41C8C`。
- 比較A: USB-Bを接続したまま7355をOFF。Host→親Picoの順に既設RESET/RUNで起動し、7355を最後にON。HELLOは`meter-host-relay-20261120.3|READY`、IDN QueryのA/T/R完了と7355 IDN 32 byteを確認。Host raw [meter_host_com22_power_order_test_20261121_01.raw](../../../temp/meter_host_com22_power_order_test_20261121_01.raw) 464 byte, SHA-256 `FB2398ECB4DE8DD00BEA9FDFC01940CD94DC3FACA302F996F072397FCE8F8567`; ATE raw [meter_ate_com7_power_order_test_20261121_01.raw](../../../temp/meter_ate_com7_power_order_test_20261121_01.raw) 78 byte, SHA-256 `2E98EA7BC17B13017DE8FDBFD4498971C7743876B1B39F8789F3807AF05E2269`。
- 比較B: 7355をUSB-B未接続でONにし、Host/親Picoを起動。起動後にUSB-Bを接続し、同じIDN Queryを一回送信。HELLOは`READY`、IDN A/T/Rと32 byte応答に成功。Host raw [meter_host_com22_hotplug_parent_20261121_01.raw](../../../temp/meter_host_com22_hotplug_parent_20261121_01.raw) 464 byte, SHA-256 `024CB67D4DC6B258A0B05472725EB74B3EA85C1B47D731AAEB926164757E770E`; ATE raw [meter_ate_com7_hotplug_parent_20261121_01.raw](../../../temp/meter_ate_com7_hotplug_parent_20261121_01.raw) 78 byte, SHA-256 `2E98EA7BC17B13017DE8FDBFD4498971C7743876B1B39F8789F3807AF05E2269`。
- 比較Bの後もDCV/連続OFF/AUTO ON/CONF約20 V/IMM/Trigger・Sample各1/delay 0/機器エラー0を維持。設定rawは[temp/meter_ate_hotplug_state_20261121_01.raw](../../../temp/meter_ate_hotplug_state_20261121_01.raw)、321 byte、SHA-256 `1CDE3915BB9E94A6DF9B2043DC236A97320C293950CFD66D3C300346ECE497B0`。9～10 V入力のREAD一回は`+09.62247E+00`、後続エラーは`+0,"No error"`。raw [meter_ate_hotplug_read_20261121_01.raw](../../../temp/meter_ate_hotplug_read_20261121_01.raw)、88 byte、SHA-256 `BFD929D149340C67AD2BF35CA2837F6B95DEB82E801A7034677D023B45B7A51A`。
- 比較Aの追加反復#2もREADY/IDN A/T/R成功。Host raw [meter_host_com22_power_order_repeat_20261121_02.raw](../../../temp/meter_host_com22_power_order_repeat_20261121_02.raw)、464 byte、SHA-256 `C7E54F166E59583DF1D85E01B29915C9C3E0F854AED8CB4027E727914DD49ABF`; ATE raw [meter_ate_com7_power_order_repeat_20261121_02.raw](../../../temp/meter_ate_com7_power_order_repeat_20261121_02.raw)、78 byte、SHA-256 `2E98EA7BC17B13017DE8FDBFD4498971C7743876B1B39F8789F3807AF05E2269`。
- 比較Aの追加反復#3もREADY/IDN A/T/R成功。Host raw [meter_host_com22_power_order_repeat_20261121_03.raw](../../../temp/meter_host_com22_power_order_repeat_20261121_03.raw)、464 byte、SHA-256 `E0D9E9C6A6DE1D8F6E390D7206DCD800EAFBF132B2C6A45B53EAD97AA26A860E`; ATE raw [meter_ate_com7_power_order_repeat_20261121_03.raw](../../../temp/meter_ate_com7_power_order_repeat_20261121_03.raw)、78 byte、SHA-256 `2E98EA7BC17B13017DE8FDBFD4498971C7743876B1B39F8789F3807AF05E2269`。
- 電源最後投入Aは3回連続成功、新規USB-B後接続Bは1回成功。今回の試行ではいずれも起動順起因の不安定さを再現しなかった。量産受入に必要な反復数/長期/負荷条件は未確定・未実施。

## 原因の切り分けと当面の対処

- 現行FWの[CDC unmount処理](../../../firmware/usb_submcu_external_meter_host/relay_main.c)は`tuh_cdc_umount_cb()`から`relay_host_device_ready(&host, false)`を呼ぶ。[Host状態管理](../../../firmware/usb_submcu_external_meter_host/relay_host.c)は、既に通常要求を受理して`high_watermark != 0`なら未処理要求がなくても`relay_host_fail("DISCONNECTED")`し、Host faultをラッチする。再mount後も`service_configuration()`は`host.fault`中にCDC line coding/接続を進めず、READYへ自己復帰しない。次のHELLOはFAULTを返し、親も`RECOVERY_REQUIRED`をラッチする。実機切断後のHELLO FAULTと、その次の拒否、および[Host/Mock回帰テスト](../../../tests/test_external_instrument_link.py)がこの経路と整合する。
- 切断直後の最初のIDN応答は物理切断後の新しい応答と証明できず、遅延CDCデータの可能性が残る。鮮度未確認応答を測定値として使わない。
- 暫定運用: 通信中に7355 USB-Bを抜かず、7355を電源断する場合も同じHost session中に行わない。必要な場合は、通信を停止し、7355電源OFF、接続構成を固定、Hostを先にRESET/RUN、親Picoを後にRESET/RUN、7355をONの順で起動する。HELLOがREADYであることと、読取専用IDN/状態Queryを新規取得してからREADへ進む。切断/電源断後に自動復帰や直前要求の再送はしない。この手順は今回の比較A/Bで各一回成功した範囲の対処であり、自動化機能ではない。
- WDT/親指令/Host状態クリアの実装はユーザー方針どおり保留。通信後unmountの回帰テスト`test_disconnect_after_query_latches_host_fault_until_reset`を追加し、全Host/Mock 454件成功。

通常READおよび電源順A/Bは成功。一方、切断直後応答の鮮度と全電源/負荷条件は未検証。最終比較B後のリンクはIDN/READ成功状態。`USB-RELAY-LINK-01`と`USB-CDC-RANGE-01`はOpenのまま。

## 2026-11-21 Hotplug FW candidate

- Relay FW `meter-host-relay-20261121.1`へ初期対策を実装: idle CDC unmountはHost faultを立てずreadyをfalseにし、remount後はCDC line coding/DTR/RTSを再設定してREADYへ戻す。未接続中Qは`LINK_NOT_READY|0`を返してUSBへ送らず、親はfaultを解除状態のまま次の明示要求を受付可能。USB TX開始後のunmountは`DISCONNECTED|1`でfault保持・再送なし。
- 回帰3件: idle unmount/remount後の同一session要求、切断中要求の非ambiguous拒否と再接続後の新要求、送信開始後の切断のambiguous停止を追加。全Host/Mock 456件成功。
- Pico SDK 2.2.0でIDN/電圧/Relayの全targetをARM build/link。picotool metadataでRP2350 ARM Secure/board/SDK/version/pinを確認。candidate UF2は94,720 byte、SHA-256 `2C7314B9ED42F00ACD6EAF32684854FF13EEBE4101B4F8E6ACB3506C6F4E014B`。ELF SHA-256 `79ECDEB0C8989AE21A325F92E6B26CF96D8E6ECD9C6059D3CA167D6557403ED0`、BIN SHA-256 `E949D8088EB1C3278271AD3348C8D1AC0A0256EAA51EDCFA30A7662A60E0B7DD`。
- candidateはbuild済み・未配置。対象HostのFlash backup/verifyとcandidate deployment、USB-B idle/処理中切断、遅延CDC応答、繰返しhotplug、ATE/NF55G/SD共存負荷は未実施。現行実機は旧Relay FWのままなので、実機では引き続き通信中の抜線/7355電源断を避け、切断があった場合はHost→親を手動復帰してREADY/IDN確認後に測定する。ここでは量産hotplug受入完了としない。
## COM22追加デバッグ

- その後COM22がPnP状態OKで利用可能になった。現行`relay_main.c`ではGP0/GP1をX1親子通信に使用し、周期heartbeatや平文診断ログは出さない。よってHost待機中の30秒受動採取が0 byteだったことは、単独では故障根拠にならない。
- COM22を先に受動オープンし、COM7から読取専用`EXT_QUERY 2000 *IDN?`を一回送信。ATE応答は`ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`、同時刻のHost GP0 TX採取は0 byteだった。ATE応答rawは[temp/meter_ate_com7_capture_20261121_02.raw](../../../temp/meter_ate_com7_capture_20261121_02.raw)、40 byte、SHA-256 `CE0C62DA0E0B1463792BB2575C5DA71803003556447DE1885B94D52A62AB6609`。Host TX rawは[temp/meter_host_com22_capture_20261121_03.raw](../../../temp/meter_host_com22_capture_20261121_03.raw)、0 byte、SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`。
- 現行[親リンク](../../../src/external_instrument_link.py)の`start()`はfault保持中ならHELLO/Qを送る前に`RECOVERY_REQUIRED`を返す。今回の応答とHost TX 0 byteは親側fault gateによる拒否と整合する。最初にfaultを立てた原因がHost応答、過去の通信失敗、他の経路のどれかは未特定。
- 最初の同時採取は収集コマンドの終端設定漏れでATEのCR応答を読み取れず、read-only ID Queryの応答を保存できなかった。測定/設定コマンドではない。修正後の上記Queryでも再送・設定変更・`READ?`は行っていない。

## 変更・停止条件

機器設定変更、`EXT_SEND`、測定、再送、電源操作、Host/親Picoの再起動は行っていない。NF55G向けコマンドも送っていない。ユーザー指示どおりHost内状態クリア/WDT/親からのRESETは案のまま保留し、今回の結果から実装しない。

現行[親リンク](../../../src/external_instrument_link.py)では、親側fault保持中の要求は `RECOVERY_REQUIRED` として拒否される。また初回HELLOでHostがFAULTを返した場合も親側でfaultを保持する。今回のATE応答だけでは、既に親faultが保持されていたのか、HostのFAULTを受けて親がfault化したのかを区別できない。COM22のHost診断がないため原因未確定とする。

## Fault分析と復帰結果

親側faultが保持されている間は外部要求がHostへ送られないこと、既設RESET/RUNによるHost→親Picoの手動復帰でRelay READYへ戻ることを確認した。faultを立てた元の原因を識別する既存ATE API/管理入口は確認できておらず、WDT/ソフトRESET機能も未実装のまま。

## 2026-11-21 手動復帰と逐次READ

- ATE/NF55G通信がアイドルとのユーザー確認後、7355/電池/外部給電は維持したまま、外部Hostの既設RESET/RUN、次に親Picoの既設RESET/RUNを手動操作した。Host reset機能/WDT/ソフトRESETは追加していない。
- COM22を受動監視してCOM7から読取専用`EXT_QUERY 2000 *IDN?`を一回送信。X1のH/A/T/Rフレームを確認し、Host `BFCF2EDB84B0B37F`、版`meter-host-relay-20261120.3`、状態`READY`を確認。7355 IDNは`ADC Corp.,7355,246410099,  A02`、原応答32 byte。復帰後のATE rawは[temp/meter_ate_com7_capture_20261121_04.raw](../../../temp/meter_ate_com7_capture_20261121_04.raw)、78 byte、SHA-256 `2E98EA7BC17B13017DE8FDBFD4498971C7743876B1B39F8789F3807AF05E2269`。Host X1 rawは[temp/meter_host_com22_capture_20261121_05.raw](../../../temp/meter_host_com22_capture_20261121_05.raw)、464 byte、SHA-256 `7E60819AF925F6371E6B48C2F6CCA5D43AE1883DC7F0B78D2664998FC0E8CD7A`。
- 設定変更なしの状態Query結果: `SENS:FUNC?`=`"VOLT:DC"`、`INIT:CONT?`=0、`RANG:AUTO?`=1、`CONF?`=`"VOLT +1.999999E+01,+1.000000E-06"`、trigger source=IMM、trigger count=00001、sample count=00001、delay=+0.0000E+00。先行状態Queryとrawは[temp/meter_ate_7355_state_20261121_01.raw](../../../temp/meter_ate_7355_state_20261121_01.raw)、321 byte、SHA-256 `1CDE3915BB9E94A6DF9B2043DC236A97320C293950CFD66D3C300346ECE497B0`。
- 上記のユーザー申告9～10 V電池入力で、`:READ?`を合計10回、各応答後に`:SYST:ERR?`を1回ずつ取得。READ原文は`+09.62330E+00`, `+09.62331E+00`, `+09.62331E+00`, `+09.62323E+00`, `+09.62323E+00`, `+09.62324E+00`, `+09.62322E+00`, `+09.62324E+00`, `+09.62325E+00`, `+09.62324E+00`。全応答15 byte、CRLF終端、機器エラー10回すべて`+0,"No error"`。
- READ 1～3/エラー応答rawは[temp/meter_ate_battery_reads_20261121_01.raw](../../../temp/meter_ate_battery_reads_20261121_01.raw)、264 byte、SHA-256 `D8DC84F7ED901C696776B4F3B631396B63FC312F3345872E8586849D29CBDCA5`。READ 4～10/エラー応答rawは[temp/meter_ate_battery_reads_20261121_02.raw](../../../temp/meter_ate_battery_reads_20261121_02.raw)、616 byte、SHA-256 `2FB38ECC50C284810B9B3B44837F5B90EC8647378109C1F362B875C54611FC19`。
- 10回の最小/最大は9.62322/9.62331 V、平均9.623257 V、レンジ幅0.00009 V（90 µV）。これは同条件での生データのばらつきであり、基準源精度、測定精度、合否、製品PASSは判定しない。コマンド再送・設定書込み・NF55Gコマンドなし。
- 10回終了後の状態QueryでもDCV、連続OFF、AUTO ON、CONF=`VOLT +1.999999E+01,+1.000000E-06`、機器エラー0を再確認。rawは[temp/meter_ate_7355_final_state_20261121_01.raw](../../../temp/meter_ate_7355_final_state_20261121_01.raw)、SHA-256 `F10DDC24B811B6DEA0655087A3D3FE1B814B91E338E914E23AF784797168EB43`。

## 2026-11-21 USB-B切断比較

- ユーザーは7355背面USB-Bが物理的に空で、他のUSBデータ経路もないと確認。Windows PnPにも7355の直接COMは現れず、利用中のCOMはATE COM7とSH-U05A COM22。
- USB-B切断中に読取専用`EXT_QUERY 2000 *IDN?`を2回、別要求として実施。1回目はX1 request `00000024`のA/T/Rを受信し、ATEへIDN 32 byteを返した。2回目はrequest `00000025`に対しHostが`E: RECOVERY_REQUIRED|0`を返し、ATEも`ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`となった。
- 1回目のIDNデータが切断後に新規取得されたのか、CDC経路に残っていたデータなのかは証明できない。したがって切断中のIDN応答は新鮮な測定器応答として採用しない。2回目の拒否からHost faultが保持されたことを確認した。USB切断検出と遅延応答境界の受入は未完了。
- 切断中は`READ?`を送っていない。設定変更・自動再送・電源操作なし。Host/親リンクは再びfault状態のため、ケーブル再接続後にHost→親Picoの順で手動復帰し、fresh IDNとREAD一回を確認するまで次の測定を行わない。
- 1回目raw: [Host X1](../../../temp/meter_host_com22_disconnect_20261121_01.raw) 289 byte, SHA-256 `4A04EFDCFE34EBEC4C4B83DDABB33EE8F02FFB16C002327F2E1B7211E5E1EE4A`; [ATE](../../../temp/meter_ate_com7_disconnect_20261121_01.raw) 78 byte, SHA-256 `2E98EA7BC17B13017DE8FDBFD4498971C7743876B1B39F8789F3807AF05E2269`。
- 2回目raw: [Host X1](../../../temp/meter_host_com22_disconnect_20261121_02.raw) 113 byte, SHA-256 `6879A7BDBBCAA3F8BF0106D2DDE1479F2689978AD306BDC33E1892CDC5E8BE44`; [ATE](../../../temp/meter_ate_com7_disconnect_20261121_02.raw) 40 byte, SHA-256 `CE0C62DA0E0B1463792BB2575C5DA71803003556447DE1885B94D52A62AB6609`。

## USB-B再接続後の復帰再試行

- ユーザーはUSB-B再接続後にHost→親Picoの順で手動復帰したと回答。続く読取専用IDN Queryも`ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`となり、Host GP0 TXは0 byte。したがってCOM7側で使われる親リンクのfault gateは解消していない。リセット対象個体/ボタン操作/実際の親ソフト再起動をこちらからは独立確認できていないため、原因を断定しない。
- この応答後は外部機器Query/READを追加していない。再試行raw: [Host X1](../../../temp/meter_host_com22_recovery_after_disconnect_20261121_01.raw) 0 byte, SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`; [ATE](../../../temp/meter_ate_com7_recovery_after_disconnect_20261121_01.raw) 40 byte, SHA-256 `CE0C62DA0E0B1463792BB2575C5DA71803003556447DE1885B94D52A62AB6609`。

切断後の最初の復帰再試行時点では親fault gateが残っていた（上記時点の履歴）。続くHost→親Picoの再起動と電源順A/B比較後は、HELLO READY・IDN・READ成功を再確認した。現時点の起動順は安定しているが、使用中unmountの回復境界/最初の遅延応答鮮度は未解決。`USB-RELAY-LINK-01`と`USB-CDC-RANGE-01`はOpenのまま。