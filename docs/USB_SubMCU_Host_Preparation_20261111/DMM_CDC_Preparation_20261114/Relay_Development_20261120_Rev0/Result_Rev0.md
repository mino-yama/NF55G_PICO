# 外部測定器中継コア 第1段階 実装記録 Rev.0

2026-11-20後続更新: 親ATE入口/PIO adapterと独立Host中継FWをコードで結合し、全446件成功・ARMビルド成功。[最新の実装/未配置範囲](Link_Implementation_Rev0/Result_Rev0.md)。以下の未接続記述は当時の実装段階。

2026-11-20後続更新: ユーザー承認により[通信契約Rev.1](Interface_Spec_Rev1.md)を確定し、契約module/13テストを追加、全414件成功。[承認・コード反映記録](Contract_Approval_Rev1.md)。以下の人間確認待ち記述は承認前の状態。

2026-11-20 JST。同一USB Host SubMCU案件。ユーザーの「中継部分はじめて」を受け、未確定の正式通信契約に依存しない要求管理部分を実装した。レンジ切替/CONF相違の検証は保留を維持する。

## 今回の到達点

[src/external_instrument_relay.py](../../../../src/external_instrument_relay.py)にExternalInstrumentRelayを追加。GPIO・UART・USBやATE書式に依存せず、adapterからの送信/受信イベントを受けてRAM内で一要求を管理する。既存FixtureApp・parser・量産scheduler・Host C FWへはまだ接続していない。したがってシリアルモニターから外部測定器への縦通しは未完成。

- clockとコマンド/応答上限をconstructorへ注入。deadlineと応答有無、終端をbeginへ明示する。数値・pin・baudrate・CRC・正式コマンド名を先行固定しない。
- beginは内部tokenを返す。tokenは起動接続世代/連番の内部照合用で、正式UARTフレームではない。requestはコピーを返す。ASCII本文は空白・引用符・カンマ・大文字小文字・末尾空白を保持し、CR/LF/NULや非ASCII本文を拒否する。機器別送信終端の付加はadapter担当。
- mark_tx_startedを送信開始前に通知し、mark_tx_completeはadapterが全送信完了を確認した場合だけ通知する。部分送信はfailを通知し、再送しない。TX_COMPLETEは機器の設定受理や実行成功を意味しない。
- receiveは分割応答を上限内で結合し、指定終端を含む原文bytesを返す。受信完了がTX callbackより先でも両方揃うまで成功にしない。本文の数値解釈・レンジ判定をしないため、CONF約200Vも中継原文として保持できる。
- 1要求1結果枠。未完了要求や未回収結果がある間は次要求をBUSYで拒否。応答超過時は保持済みprefixと失敗状態を返し、上限を超えて蓄積しない。
- 総期限はbegin受付時から。期限ちょうどの応答も遅着として拒否。送信開始後のtimeout/取消/切断/部分送信はambiguous=Trueとし、リンク再確立を要求する。送信前の失敗はambiguous=Falseだが、古いadapter作業を排除するまでは再受付しない。
- 古いtokenや接続世代の完了/失敗は新要求へ適用しない。複数行や完了後の追加データを未回収成功へ混入させず異常にする。
- establish_linkはadapterが旧CDC/UART断片・未完了送信を排除した清浄な接続を検証した後の内部入口。単なるquiet時間や最新tokenの後付けでは清浄性を保証しない。これは将来adapterの実装・受入責任であり、本コアだけで実機遅着を排除できたとは扱わない。

NF55G送信・FU・製品Cache・測定Cache・Logger/SD・製品PASS/FAILへの副作用はない。正式ATEエラー表・Cache契約も変更していない。

## 変更ファイルと理由

- 新規src/external_instrument_relay.py: 書式に依存しない要求相関/期限/原文保持の基盤。
- 新規tests/test_external_instrument_relay.py: 19テスト。実測IDN全分割境界、引用符/空白保持、200V CONF原文、応答有無、送受信callback逆転、期限境界、部分送信、切断/取消/再確立、旧token、複数行、上限を検証。
- Software_Module_Interface/Test_Specification/ATE_Command_Master/Implementation_Plan/Open_Issues/CHANGELOG: 内部到達点と未接続範囲を追記。
- [開発用通信契約案](Interface_Proposal_Rev0.md): 次工程のATE指令・UART候補・フレーム案を人間確認用に具体化。未承認案であり今回の実装値ではない。

## 試験結果

個別19件成功。全体は .venv/Scripts/python.exe -B -m unittest discover -s tests -v で **401件成功、5.327秒**（既存Host Unit/Mock NF55Gを含む）。[全件ログ](Host_Mock_Rev0.log)。Pythonのみの追加でHost C FWを変更していないためARM rebuildは行っていない。実機への配置・配線変更・通電・計測器コマンド送信も今回行っていない。

## 次工程と残事項

正式ATE/親子UARTの未確定値を推測しないというAGENTS.md Hard Rules 3/25とUART_Contract_Draftの人間確認条件を維持する。上記通信契約案を確認してから、ASCII中継入口、親PIO adapter、Hostの双方向受付/CDC中継、scheduler連携、実機縦通しを実装する。USB-SUB-01/05、USB-INT-01、USB-CDC-RANGE-01はOpenのまま。校正Cacheへの数値採用・AD/AR連携は別段階。
