# USB_HOST_SubMCU 接続・受入テスト 事前確認記録

日付: 2026-11-10
状態: 事前確認済み。確定仕様の所在・対象実機の識別待ち。実機受入合格ではない。

## 確認できた事実

- 現在の案件フォルダを継続使用。元資料・既存成果物・通信コードは変更していない。
- 確認資料: [開発準備Rev.0](USB_Host_SubMCU_Integration_Plan_20261110.md)、[初回受入チェックリスト](RP2350_USB_C_First_Acceptance_20261110.md)、[接続図Rev.3](drawings/NF55G_Fixture_20261110_Rev3/README.md)、[原典台帳](../reference/USB_Host_SubMCU_20261110/README.md)。
- 固定割当てはType_C1=ADCMT 7355、Type_C2=BCR-TC2D1BK。USBハブは使用しない。
- 上記資料では下位UART GPIO、正式baud・フレーム・CRC・要求ID規則、依存ライブラリ版は未確定と記載。今回確定した仕様との同一性は未確認。
- リポジトリ内のファイル名検索では、USB_HOST_SubMCU専用の確定仕様・新規ファームプロジェクトは特定できなかった。資料や実装の不存在・未実施を意味しない。

| Port | VID:PID | serial | 表示 |
|---|---|---|---|
| COM6 | 2E8A:0005 | 69F7D45962CFDFAD | USBシリアルデバイス |
| COM20 | 056E:5004 | 空欄 | Elecom USB-Serial Converter |

COM番号・VID/PIDだけでは治具Pico／下位RP2350を同定できない。ポートは開いていない。REPL割込み・soft reset・UART送信・FW配置は未実施。

## 実行した試験

- コマンド: .venv/Scripts/python.exe -B -m unittest discover -s tests -v
- 結果: **273件成功、9.013秒、終了コード0**。Host Unit／Mock NF55Gの回帰確認。
- COM列挙: .venv/Scripts/python.exe -m serial.tools.list_ports -v、終了コード0、2ポート。
- 通常シェル起動がアクセス拒否となったため、実行環境の昇格機能で上記を実行した。
- 下位MCUのUSB・UART・電源・実測値・共存Timingの検証は未実施。回帰結果から実機受入成功は判断しない。

## 接続・受入の実施順

| 順 | 作業 | 次へ進むための証跡 | 今回の状態 |
|---|---|---|---|
| 1 | 確定仕様の版・ファイル、対応FWと依存版を照合 | 仕様パス・版、UART両端GPIO、baud、フレーム／CRC、FW識別 | 保存先確認中 |
| 2 | 基板版・Type_C1/Type_C2を現物照合。CC・VBUS・保護・逆給電を確認 | 基板写真、回路との対応、電圧・電流測定値 | 未確認 |
| 3 | 書込み対象を同定。Type_C1の7355を外し、Type_C2も空で単体書込み・起動確認 | 対象基板の識別、書込み物のhash、版情報・起動ログ | 未実施 |
| 4 | Type_C2だけにQR。35文字・大小文字・先頭ゼロ・ハイフン・suffixを照合 | descriptor、HID原文、期待値と受信値 | 未実施 |
| 5 | Type_C1だけに7355。FW／BUS／USB classと確定した取得手順を確認 | descriptor、設定、送受信原文、前面表示との比較 | 未実施 |
| 6 | 固定割当てで両機器同時動作・片側切断／復帰 | 機器別ログ、欠落／重複、再起動・旧値不採用 | 未実施 |
| 7 | 確定したUARTピンで接続。3.3V・共通GND・TX/RX交差確認後、疎通と異常系 | 両端trace、分割／連結／CRC／timeout／取消／遅延応答／再起動 | 確定仕様照合待ち |
| 8 | ATE・NF55G・Logger併用のTiming確認 | T1/T2、応答時間、再送・drop、CSV完全性 | 未実施 |

既存資料でPico GP8 TX／GP9 RXはPIO候補であり、下位GPIOを推定して接続しない。ATE UART0 GP0/GP1とNF55G UART1 GP4/GP5は維持する。通信中のSD write/flush禁止、NF55G Transaction 1件、FU禁止を維持する。取得だけで補正を書き込まない。

## 未確認事項・再開条件

ユーザーへ今回固めた最新仕様の保存先とRP2350-USB-Cの接続状態を確認中。仕様・対象識別後に上記1から照合し、電源受入を満たした段階まで順に実施する。USB-SUB-01ほか既存Open Issueは変更・Closeしていない。実装変更時はCode／Test／Docs／CHANGELOGを同時更新する。

## 後続結果（2026-11-10、通信用ケーブルへの変更後）

追加基板をBOOT時E: RP2350／2E8A:000F、通常起動時COM21／2E8A:0009として認識した。USB serialはA06FEA01012EC137で一致。ファーム名・版、電源・USBホスト・UART受入は未確認。COM6はユーザー訂正により既存治具である。最新の実測結果と残項目は[初回接続受入結果](USB_Host_SubMCU_First_Connection_Acceptance_20261110.md)を参照。

## 実機CC実装の照合（2026-11-10）

写真・申告でType_C2のCC1／CC2とも0=Sink位置に実装、1=Source位置は未実装。QR用Sourceの電気受入は未完了。Type_C1 CC接続の資料不一致も検出しUSB-SUB-02へ記録した。詳細・次の受入条件は[CC実装照合](USB_Host_SubMCU_CC_Inspection_20261110.md)を参照。

## Type_C2無負荷VBUS実測（2026-11-10）

ユーザーからVBUS=5V、抵抗変更なし、LED消灯との回答を受領。電圧は実測として記録し、Source設定・電流供給能力・保護の合格とは区別する。CCは両方Sink設定のまま。[詳細記録](USB_Host_SubMCU_CC_Inspection_20261110.md)。

## 確認用UF2の配置・USB単体受入（2026-11-11）

追加基板A06FEA01012EC137（COM21）の元Flash全2MBを退避・実機照合し、USB CDCのみの確認FW dev-20261111.1を書込み・verify成功。USB実機123チェックを再起動前後各1回成功、Host／Mock287件成功。通常起動待受でCOMハンドル解放。QR・7355・UART・電気条件の受入は未実施。最新のUF2・ソース・バックアップ・検証結果は[今回の受入記録](USB_SubMCU_FW_Acceptance_20261111/Result.md)を参照。

## Type_C2のHost条件具体化（2026-11-11）

メーカーUSB-C専用FAQのプルアップ撤去位置を確認。D+=GPIO12／R12、D−=GPIO13／R11へ先の説明を訂正。R13撤去、CCのR18／R19未実装化・R20／R21各56kΩの変更案を[Host回路条件Rev.0](USB_Host_SubMCU_Host_Circuit_Conditions_Rev0_20261111.md)へ具体化。デバッグPC給電／QR・DMM時は外部アダプタのExpander分岐5V・1Aというユーザー指定を反映し、同時直結給電を避ける。部品変更と保護・負荷時電気受入、Host FWは未実施。USB-SUB-01／02はOpen。

## 改造案内のタイミングと図面（2026-11-11）

改造は今行わず、実機確認の直前に案内するというユーザー指示を記録。[治具図Rev.4（5枚）](drawings/NF55G_Fixture_20261111_Rev4/README.md)を追加し、4枚目に部品変更・位置、5枚目に施工順・電源切替え・受入記録欄を明記。基板と配布FWは変更していない。
