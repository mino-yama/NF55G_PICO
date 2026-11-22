# Codex引継ぎ実行結果 2026-11-22 Rev.0

## 確認できた事実

- 引継ぎ元: [Codex引継ぎ 2026-11-22](../Handoff_To_Codex_20261122_ParentPico_Source_NotSynced.md)。同一NF55G Pico案件の継続作業。
- 親Pico COM6 / unique_id 69f7d45962cfdfad。配置前ソースは9848 byte、SHA-256 2e554efe0db0899472eb307a942a70815aacc50727b895055586d740e4f9399b。過去取得ソースと実機hashが一致。
- 候補10012 byteとの差分はtake_reply内の非ambiguous LINK_NOT_READY時にsession/host_info/faultを解除する4行だけ。
- 親全Flash 4194304 byteをsave -a -vで退避・照合。SHA-256 d905304c294c93a6cb67bdffdad893a33c4cab56e4a9849b0647cc6a66b31f83。
- 親はexternal_instrument_link.pyのみを更新。配置前に一時ファイルのhash/compileを確認してrenameし、実機SHAを照合。ハード再起動後もUID・10012 byte・SHA-256 18defb0a1a55f2b88a8bc9baecc9429dd5e7380201f19cba73f46f4462c41fe2が一致。
- 実機configはEXTERNAL_INSTRUMENT_ENABLED=True、対象Host BFCF2EDB84B0B37F。既存configや他ソースを更新していない。
- Hostは配置前からmeter-host-relay-20261121.1 / chipid 0xbfcf2edb84b0b37f / BOOTSELと実機照会。引継ぎの「未配置」は現状と異なる。過去配置時期・工程はこの記録だけでは確定しない。
- Host全Flash 2097152 byteをsave -a -vで退避・照合。SHA-256 5d429adf838c62d68c8e9f2182db553e5237cb0958da53b7220472d3ef342dbe。今回、固定した候補UF2をload -vしてverify成功、配置後版/個体を再照合し通常起動。
- Host UF2 SHA-256 2c7314b9ed42f00acd6eaf32684854ff13eebe4101b4f8e6acb3506c6f4e014bは引継ぎ記載値と一致。
- 親の通常起動後、2026-11-22 15:33:40 JSTにEXT_QUERY 2000 *IDN?を一度送信。Host hは.21.1 / READY、新session内でA/T/Rを取得。ATEはOK:EXT_RX:32:41444320436F72702E2C373335352C3234363431303039392C20204130320D0A。原文はADC Corp.,7355,246410099,  A02 + CRLF。
- Host Unit / Mock NF55G: .venv/Scripts/python.exe -B -m unittest discover -s tests、456件、22.965秒、OK。今回ソース実装の追加変更なし。
- USB-B idle抜差し試験を1回実施。測定READ・レンジ/設定変更・NF55Gコマンド送信なし。両基板の現行Flashを新規ファイルとして保存し、原典・既存成果物を保持。

## 現在の停止点と未確認事項

ユーザーから7355 USB-B抜線完了を受領。15:34:44 JST、切断中のIDN要求を1回だけ実行し、ATEはERR:EXT_LINK_NOT_READY:AMBIGUOUS=0、Hostは同一起動session・要求2のE=LINK_NOT_READY|0を返した。A/T/Rは観測なし。ユーザーから再接続完了を受領。15:35:20 JST、親/Host/7355のRESETを追加せずIDNを1回送信し成功。初回と同じsession ACBA1904AE567F3CB2F13F9BB5D183BEのh=READY、要求3のA/T/Rを照合。idle切断→未送信拒否→再接続→明示IDNの統合試験は1回成功。COM6/7/22は解放済み。

切断中はHost側の未送信拒否を確認した。USB線のパケットを直接採取した証明ではない。再接続後IDNまで成功確認し、追加の切断・測定・設定変更は送らず終了。

idle切断/再接続は上記の1回のみ成功。送信中切断、旧応答排除、親Cache INVALID連携、長期反復・複合負荷・ATE/NF55G/SD共存は未受入。USB-RELAY-HOTPLUG-01等のOpen IssueをCloseしない。IDN成立やProtocol SUCCESSを製品PASS・測定精度の保証とは扱わない。

## 実行中の一時エラー

Windowsでプロセス起動時アクセス拒否が発生し、一時停止した。その後、既に開始した実機照合が完了し、新規プロセス起動も復旧した。権限審査の拒否通知ではなく、プロセス生成のOSエラー。

machine.bootloader()/machine.reset()ではUSB再列挙に伴いmpremoteがSerialExceptionで終了した。後続の個体指定picotool照会・再起動後実機hash照合で遷移成立を確認している。

## 証跡と変更ファイル

- [固定パッケージmanifest](manifest.json)、[全操作ログ](operations.json)
- [親配置前](parent_before.json)、[親配置後](parent_after.json)、[親再起動後](parent_after_reboot.json)
- [親全Flash退避](backup/parent_flash_before.bin)、[退避manifest](parent_flash_backup.json)
- [Host全Flash退避](backup/host_flash_before.bin)、[退避manifest](host_flash_backup.json)
- [Host配置前info](host_before_info.txt)、[配置後info](host_after_info.txt)
- [再接続IDN結果](reconnected_idn/result.json)、[Host原記録](reconnected_idn/host.raw)、[操作者確認](operator_observations.json)
- [切断中IDN結果](disconnected_idn/result.json)、[Host原記録](disconnected_idn/host.raw)
- [初回IDN結果](startup_idn/result.json)、[Host原記録](startup_idn/host.raw)、[ATE原記録](startup_idn/ate.raw)
- [親退避・配置script](parent_deploy.py)、[Host退避・配置script](host_deploy.py)、[一回限りの実機確認script](live_check.py)

配置用コピー・退避・ログは本フォルダ内。workspaceのsrcおよびfirmware Cソースは今回変更していない。索引としてCHANGELOG / Open_Issues / Test_Specification / build_manifestを更新。
