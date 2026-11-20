# 通信契約Rev.1 ユーザー承認・コード反映記録

2026-11-20後続更新: 親ATE入口/PIO adapterと独立Host中継FWをコードで結合し、全446件成功・ARMビルド成功。[最新の実装/未配置範囲](Link_Implementation_Rev0/Result_Rev0.md)。以下の未接続記述は当時の実装段階。

2026-11-20 JST。ユーザーの「了解。確定して下さい」により[開発用通信契約Rev.1](Interface_Spec_Rev1.md)を確定した。承認前[原案Rev.0](Interface_Proposal_Rev0.md)を保持。

## 確定した内容

- ATE入口: EXT_QUERY / EXT_SEND、明示timeout 1～10000ms、本文/応答192 byte。既存ATE 57600/8N1・応答終端設定を維持。
- 親子UART: 115200/8N1、親PIO1 GP12 TX/GP13 RX、Host GP0 TX/GP1 RX。
- @X1フレーム: 起動session32HEX、request8HEX、kind/mode、timeout8HEX、payload長4HEX、最大192 byteのHEX本文、CRC-32/IEEE、CRLF、最大512 byte。
- 原文応答: OK:EXT_RX:<byte数>:<HEX>、送信完了OK:EXT_TX、エラーERR:EXT_<理由>:AMBIGUOUS=0/1。
- 自動IDN/レンジ設定/測定/Query追加/再送を中継FWへ持ち込まず、任意応答を校正Cacheへ自動格納しない。

## 今回の変更と理由

[external_instrument_contract.py](../../../../src/external_instrument_contract.py)に承認済み定数、モニター要求parser、親子フレームencode/decodeとCRC/長さ検証、ATE用原文HEX応答/エラー書式を追加した。本文へ既存parserのstripを適用せず、先頭/末尾空白・引用符・カンマ・大小文字を保持する。コードと仕様を同期するための独立モジュールであり、実機I/Oや自動送信はない。

[test_external_instrument_contract.py](../../../../tests/test_external_instrument_contract.py)に13件追加。独立したCRC計算との照合、CRC破損、CRCが正しくても不正header/長さの拒否、全192 byteのpayload往復、timeout/本文境界、CR/LF/CRLF、原文HEX応答、エラー文字列注入拒否を確認した。

ATE_Command_Master/Software_Module_Interface/Test_Specification/Implementation_Plan/Open_Issues/CHANGELOGと既存モニター要求記録へ承認を反映した。未承認候補という過去の記録は履歴として保持し、現行Rev.1を優先する。

## 検証結果

- 個別13件成功。
- .venv/Scripts/python.exe -B -m unittest discover -s tests -v: **全414件成功、5.508秒**。既存Host Unit/Mock NF55Gを含む。[全件ログ](Host_Mock_Contract_Rev1.log)。
- 更新したMaster/関連文書のgit diff --check成功。追加ファイルの末尾空白・記録リンクも確認。
- 今回はGPIO非依存Pythonモジュールと文書の更新。Host Cを変更しておらずARM rebuild・実機Flash・配線/通電・機器への送信は行っていない。

## 実装状態と残事項

モニターパ－サーとフレームcodecはまだ量産parser/FixtureApp・PIO adapter・Host C FWに接続していない。現行配置FWからEXT_QUERY/EXT_SENDを使える状態ではなく、モニター縦通しは未完成。CRC codecはフレーム構文を検証し、kind別のsession照合・要求順序・実機状態は将来adapterが検証する。

原案で別途照合としたHELLO payloadのFW版/基板ID表現・nonce乱数API、親PIOのSM/命令メモリ/IRQ/負荷、現物端子/RESET・配線、復帰時の旧データ排除、target MicroPythonでの実行・UART/CDC縦通しが残る。仕様採用のみを理由にUSB-SUB-01/05・USB-INT-01をCloseしない。レンジ相違の検証は保留を維持する。
