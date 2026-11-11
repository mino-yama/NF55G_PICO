# USB_HOST_SubMCU 接続対象の確認結果

日付: 2026-11-10
状態: 既存治具を識別済み。追加RP2350-USB-CのPC接続待ち。

## 確認できた事実

- ユーザー指定の最新資料はUSB_Host_SubMCU_Integration_Plan_20261110.md。再読した内容はRev.0で、構成とUSB固定割当ては確定要求、UARTピン・フレーム・依存版等は設計案／未確定という記載だった。
- ユーザーが当初指定したCOM6について確認した後、実物の接続先は「既存の治具Pico 2だった」と訂正回答を受けた。COM6を追加RP2350-USB-Cの受入実績として扱わない。
- COM6をDTR=False／RTS=Falseで開き、4秒間の送信なし受信確認を実施。受信0byte、エラーなし。[機械記録](USB_Host_SubMCU_COM6_Passive_20261110.json)。
- mpremote connect COM6 resume runによるRAM内識別と既存pico_inventory.pyの読み取りを実施。MicroPython 1.27.0、RPI_PICO2、RP2350、unique ID 69f7d45962cfdfad、150MHzを確認。
- /main.pyはsrc.main.main()を呼び出す既存治具の起動入口。SHA-256: b0b2a60bdabebe7f7f576039755b6e135be3731f9a2470d991b95ca540a21b93。
- /srcにはate_server.py、ate_uart.py、nf55_protocol.py、nf55_uart.py、rtc_driver.py、sd_card.py等が存在。/src/main.pyのSHA-256: 344516de307fae8e7fe60ab556b19e28a4c4c3a06ddfd4e0c1f211c2fe0a76fc。
- REPL識別により実行中アプリを一時停止した。soft reset、自動再起動、GPIO／周辺初期化、FW配置、機器ファイル書換えは実施していない。通常運転へ戻す際は試験非実施状態で電源を入れ直すよう案内した。

## 実施結果と残事項

既存Host／Mockの273件成功は[事前確認記録](USB_Host_SubMCU_Acceptance_Precheck_20261110.md)を参照。今回追加したローカル確認スクリプトは、送信なし受信確認とRAM内識別の2本で、いずれも実行終了コード0。最初のインライン識別コマンドはホストの引用符解釈エラーで未実行となり、ファイル方式で修正した。

追加基板のFW・USB・UART・電源受入は未実施。既存治具の情報から追加基板の動作を推定しない。USB-SUB-01ほかOpen IssueはCloseしていない。

## 次の物理操作と再開順

1. 追加のWaveshare RP2350-USB-CをType_C1からデータ対応USBケーブルでPCへ接続する。Type_C2、7355、治具UARTは外して初回識別する。
2. 接続完了連絡後にCOM／USB識別を再列挙し、追加基板を特定する。COM6やRPI_PICO2の表示だけで追加基板と断定しない。
3. 基板版・ポート位置・CC／VBUS構成を回路図と現物で照合して記録する。未確認の改造やUSB機器接続は進めない。
4. 既存ファームがあれば識別・保全した後、基板適合と依存版を確認して単体受入用FWを準備する。
5. QR単体、7355単体、同時接続、UART連携の順で、確定済みの条件と実機電源受入を満たす範囲まで進める。未確定の内部プロトコルは独断で固定しない。

## 追加ファイル

- 本記録とCOM6受信JSON: 事実と対象訂正を記録するため。
- scripts/usb_submcu_passive_acceptance_20261110.py: COM6の送信なし受信記録。
- scripts/usb_submcu_identity_20261110.py: 周辺初期化・ファイル書換えなしのRAM内識別。

元資料、通信実装、既存成果物は変更していない。本記録は前回の事前記録を上書きせず、後続記録として保存した。
