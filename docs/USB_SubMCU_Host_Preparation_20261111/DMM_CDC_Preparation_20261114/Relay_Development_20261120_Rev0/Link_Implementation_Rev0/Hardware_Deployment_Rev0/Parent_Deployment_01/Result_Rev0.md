# 親Pico 中継コード配置結果 Rev.0

2026-11-20 JST。ユーザーがHostを外し、外部5V/親子信号を切り離した親Picoだけを通常USB接続したと報告した後に実施。

## 確認結果

- 実機USB/unique_id: 69f7d45962cfdfad、COM6、MicroPython v1.27.0（2025-12-09）。
- 既存26ファイルを退避し、各SHA-256を実機計算値と照合成功。/sdは走査・変更していない。
- PIO SM4/5はinactive、CRC-32標準入力123456789の値3421780262、os.urandom(8)を実機で確認。
- 配置前に新parser/codec/親adapterをRAM上で実行し、擬似I/OのHELLO→Q→T/R→HEX応答が成立。実機asm_pioでTX4/RX12命令に組立て成功。GPIO/UARTインスタンスは生成していない。
- 配置用Parentの30ファイルを照合。5ファイル追加・3ファイル更新の計8ファイルだけを書込み、同一22ファイルは保持した。依存moduleを先に配置し、src/main.pyを最後に切り替えた。
- 旧src/mock_nf55g.pyは配置対象外で、削除/変更していない。新calibration_measurement.pyは新main.pyの依存RAM基盤として配置したもので、AD/AR機能の実装/実行を意味しない。
- 全30ファイルを実機SHA-256で照合し、raw REPLでsoft resetして旧moduleキャッシュを消去後、新しいsrc.main等をimport検証した。PARENT_DEPLOYMENT_IMPORT_OK、EXTERNAL_ENABLED=True、PIO4_ACTIVE=False、PIO5_ACTIVE=Falseを確認。
- 通常main.pyは起動せず、終了時はfriendly REPLで停止。親子UART、ATE疎通、実USB CDC中継、NF55G通信/書込み、レンジ/測定は今回実行していない。

## 退避時の一時エラー

最初の退避はWindowsのパス長制限でsrc/command_dispatcher.pyのPC側保存に失敗した。実機は未変更。長いパス対応の再開scriptへ切り替え、先行5ファイルも再照合して保持し、全26ファイルの退避を完了した。初回失敗manifestも履歴として保持する。

## 証跡

[完了した退避manifest](Backup_Manifest_02.json)／[初回退避manifest](Backup_Manifest.json)／[実機API確認](Runtime_API_Precheck.log)／[配置前RAM検証](RAM_Validation.json)／[配置manifest](Deployment_Manifest.json)／[配置後import](Post_Deployment_Import.log)

配置scriptはbackup・package・実機変更の事前照合、依存順配置、書込み後hash、失敗時rollbackを備える。rollbackは今回不要だった。通常起動せずに検証するraw soft reset以外の追加reset操作は行っていない。ソフト回帰は配置直前の全446件成功を継承し、今回は再実行していない。

## 次の無給電結線

親のPC USBを外し、両基板の外部5V/USBを外した無給電状態で端子表示を照合する。承認済みのネット接続は親GP12 TX→Host GP1 RX、Host GP0 TX→親GP13 RX、GND共通。Host GP12/13はUSB-A用なので親の同番号と接続しない。Expander CN/中継基板の具体的な物理端子やRESET位置は推測しない。外部電源はまだOFFで、結線確認後にATE側監視を準備する。

[全体の実機受入手順](../../Acceptance_Procedure_Rev0.md)。現物配線/電源/IRQ負荷・実機縦通しは未受入で、関連Open IssuesはCloseしない。
