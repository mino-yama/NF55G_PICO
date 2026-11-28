# 交換用USB HOST CDC基板のFW配置結果 Rev.0

完了後追記：ユーザーがTX/RX逆接を修正した後に通信復旧。新HOST .25.2を継続し、R3・入力40 mVで校正用取得5件、400／400セット、実SD CSV400件とPC実ファイルSHA一致、回収後の通常待機まで確認した。[最終受入結果](../Final_R3_Acceptance_Rev0.md)。以下の無応答記載は修正前等の履歴。

最新実測：ユーザー回答で電源3.3 V／5.0 V正常。親GP12の低／高各30秒のデジタル読戻し0→1に対し、HOST GP1―GNDは両区間3.28 Vだった。親低レベルへ追従しておらず、信号2経路とGNDの無給電抵抗測定を依頼中。断線箇所や原因は未確定。[受信端実測](Rx_Level_Comparison_Rev0.md)。

継続調査：親PIOを一時停止し、同じGP12/13のハードウェアUARTで正しい情報要求を送ったが受信0。ATE・PIOを元へ戻し、ATE正常応答と通常INFO timeoutを確認。PIOだけが原因とは絞れず、通常外部給電の電圧実測を依頼中。[UART比較結果](UART_Comparison_Rev0.md)。

2026-11-28。交換用HOSTへ検証済み最新通常FW `meter-host-relay-20261125.2`の書込み・独立verify・版読戻しを完了した。一時診断版は使用していない。通常接続でのHOST情報応答は未復旧。

| 項目 | 結果 |
|---|---|
| 新個体ID | `73AD3A60D10514E9`、RP2350 A4、Flash 2 MiB |
| 交換前の搭載プログラム | `usb_device`、2026-05-13ビルド |
| 書込みFW | `meter-host-relay-20261125.2` |
| UF2 SHA-256 | `088e6e2a11b2ea333e9de66af34dfe2558ab5d2c7a9ffbc6368110329d7035e4` |
| 新基板の元Flash退避 | 全2 MiB、独立verify・SHA保存済み |
| 配置照合 | load -v、独立verify、.25.2版読戻し成功 |
| 親設定 | EXTERNAL_HOST_CHIPIDだけを旧`BFCF2EDB84B0B37F`から新IDへ変更 |
| 親配置照合 | 旧設定退避・事前compile・37件SHA一致、通常再起動後の37件一致を確認 |
| 親実行中ID | 新ID `73AD3A60D10514E9`と一致、fault=False、試行停止・busy=False |

[元Flash退避情報](backup.json)、[HOST配置結果](flash_result.json)、[版読戻し](host_after.log)、[親の実行中設定](parent_runtime_check.json)、[親37件SHA](parent_after_hashes.json)を保存した。親のQR双方向受付・RTC・校正等は保持し、親保存済み設定の変更は個体ID1項目だけ。ソース既定configの旧IDは実機への配置内容とは区別する。

## 通常接続での通信確認

ユーザーから交換用HOSTを通常構成へ接続済みとの回答を受け、PC→COM7 ATE入口→親Pico→新HOSTの情報照会を実行。治具IDN正常、IDLE／SD OK／drop0だが、`HOST_INFO? METER`は`ERR:HOST_TIMEOUT`だった。[通常ATE記録](verify_02/normal_ate.json)／[通信確認結果](verify_02/verification.json)。7355 IDN照会・R3設定・校正取得・400セットはこの確認では実行していない。

初回の確認は補助診断COM23が外れていたため、HOST情報照会前に停止した（このフォルダ直下の`verification.json`）。補助ポートを任意扱いへ修正し、別フォルダ`verify_02`でATE本経路の情報照会を実行した。COM23未接続をHOST無応答の根拠にしていない。

新個体への設定反映漏れは、再起動後の実行中IDと37件SHAで除外した。交換・FW配置完了と通常通信の復旧は分けて扱う。旧基板と交換基板の双方で情報無応答が観測されたが、原因・故障箇所は未確定。R3受入を成功として扱わず、OIはOpen継続。

新規配置・確認スクリプトは`scripts/replace_meter_host_20261128.py`、`verify_replacement_meter_20261128.py`、`check_replacement_parent_20261128.py`。関連の実機検証・compile・読戻しを実施し、製品コードは変更していない。Host／Mock596件の先行実績は、この交換後の通信成立の代用にはしない。
