# HID-UARTコンバーター単体TEST環境

作成日: 2026-10-11。NF55G検査治具開発の副作業。

## 現在の準備状況

元資料は [README.md](../README.md) に原本のまま複製した。
資料取得先は [reference](../reference/)、取得記録は [acquisition_index_20261011.json](../reference/acquisition_index_20261011.json)。
既存NF55G/ATE/QRプログラムとPicoのmain.py/boot.pyは変更していない。
今回のファイルはPicoへまだ転送していない。

2026-10-11、ユーザー訂正により対象ICをCH9350と確定した。
ch9350_capture.pyはimportだけではGPIOを操作しない。明示的にstart_pio()を呼ぶと、
GP9/PIO0 SM0を115200bps/8N1受信へ割り当て、GP8をHigh固定する。TX送信は行わない。
ch9350_decode.pyは状態2/3/4のキーボード11byteフレームを対象とする。
DIPの評価設定と量産候補は [dip_switch_settings.md](dip_switch_settings.md) で管理する。

評価基板固有の詳細資料は未入手である。2026-10-11、ユーザーから、販売ホームページの記載内容を基に
基板情報をメモした旨の説明を受けた。販売基板のDIP搭載、端子表示等はユーザー提供情報として扱い、
ICデータシートで確認した内容や現物測定結果と区別する。ホームページ画面とDIP設定表原文は未保存である。

## PC側の実行

NF55G_PicoフォルダでPowerShellから実行する。追加パッケージは不要。

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s CH9350/tests -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests
.\.venv\Scripts\python.exe -m mpremote --help
```

2026-10-11実行結果: CH9350共通受信ログテスト5件成功、既存Host/Mock 161件成功。
mpremoteの起動確認成功。USB認識、物理受信、115200bpsでの欠落はPCテストでは未検証。

## 生データ表示インターフェース

Picoへ `ch9350_capture.py` と既存の `src/qr_pio_rx.py` を配置する。
NF55G/ATE/SD runtimeを停止した専用試験状態で、REPLから開始する。

```python
from ch9350_capture import start_pio
result = start_pio(duration_ms=30000)
```

出力形式（合成例、実測ではない）:

```text
CAPTURE_START HEX_ONLY
RX t_ms=120 n=11 hex=57 AB 01 00 00 2C 00 00 00 00 00
CAPTURE_STOP bytes=11 reads=1 errors=0
```

t_msは収集開始からread時点までの経過時間。各バイトの到着時刻ではない。
readの分割・連結はUART受信バッファの都合で発生し、1行を1フレームと解釈しない。
Ctrl+Cまたは指定時間で停止し、受信器のclose/deinitを呼ぶ。
受信器がtake_errorを提供する場合はLOSSを明示する。errors=0だけで物理的な欠落ゼロは証明しない。
REPL表示自体の負荷もあるため、連続読取りの完全性は実データと照合する。

## 配線競合と開始条件

- 既存UART0 GP0/GP1はATE用。
- 既存UART1 GP4/GP5はNF55G専用として保持し、CH9350を接続しない。
- CH9350試験はGP9=受信、GP8=送信禁止のHigh固定、PIO0/SM0、115200bps/8N1へ固定する。
- GP8/GP9のハードUART1機能は使わないため、NF55GのUART1周辺回路を再設定しない。
- Pico GP9（物理12番）へCH9350 TX、Pico GP8（物理11番）へCH9350 RX、GNDを共通にする候補とする。
- CH9350 RXをGP8へ接続するかGNDへ固定するかは販売基板の構成確認後に決定する。現時点では短絡しない。
- GP8はHigh固定であり、CH9350へコマンドを送信しない。
- GP10には旧ホストTX0診断の接続履歴もある。新配線前に旧接続を確認する。
- CH9350 TXの実電圧、GND、5V供給能力、DIPと論理レベルの対応を確認する。
- NF55G/SD/ATEの既存runtimeを停止した専用試験で行う。今回はNF55Gへコマンドを送らない。

| CH9350基板 | Pico 2 | TESTでの扱い |
|---|---|---|
| TX | GP9 / 物理12番 | PIO0/SM0、115200bps/8N1で受信 |
| RX | GP8 / 物理11番 | High固定、送信処理なし。基板仕様確認までは接続しない |
| GND | GND / 物理13番候補 | 共通GND |
| 5V | 5V電源 | USBリーダを含む必要容量を確認して給電 |

GP4/GP5、UART1の設定、NF55G用RS232経路は変更しない。

## CH9350仕様根拠

[CH9350 V2.3英語版](../reference/CH9350DS_V2.3_EN_KamamiMirror_20261011.pdf)を参照。
公開ミラーから取得したWCH作成資料で、WCH公式ファイルとのバイト一致は未確認。

| 項目 | 記述 | 根拠 |
|---|---|---|
| USB機器を受ける側 | SEL High、下位機モード。起動/リセット時に選択 | p.4、p.7-8 |
| 状態2 | S1 High、S0 Low | p.4、p.9 §3.3 |
| UART | BAUD1/BAUD0 Highで115200、8N1 | p.4、p.7-8 |
| キーボード入力 | 状態2/3/4の57 AB 01 + 8byte、合計11byte | p.11 §4.3 |
| 状態0入力 | 0x88を含む可変長形式。状態2のデコーダとは区別 | p.10-11 §4.3 |
| その他 | 状態通知・マウス等を11byte固定として読まない | p.10-12 |
| 単方向運用 | 下位機の状態2/3/4でRXDをGNDにする条件の記述あり | p.7 §7.1(9) |

最後の項目はIC仕様であり、販売基板のRX端子を直ちにGNDへ接続する指示ではない。
基板内の抵抗・レベル変換・DIP構成を未確認のまま端子を短絡しない。
UARTの構築APIは https://docs.micropython.org/en/latest/library/machine.UART.html を参照。
[LCSC版](../reference/CH9350DS_LCSC_20261011.pdf)は中国語V2.6で、V2.3とは版を区別する。

## DIP設定

- 評価基本設定: `EVAL-CH9350-STATE2`（SEL=H、S1=H、S0=L、BAUD1=H、BAUD0=H）。
- 量産候補: `PROD-CH9350-STATE2`。評価完了までは未承認として扱う。
- 状態0は互換性切分け専用。状態2の結果や現在のデコーダと混在させない。
- 基板DIPの番号とON/OFFから論理High/Lowへの対応は未確認。現物測定前に推測設定しない。
- DIP搭載など基板固有情報は販売ホームページを基にしたユーザー提供情報。メーカー資料による確認済みとは扱わない。
- DIP変更は必ず電源OFFで行い、変更後に再投入して設定とUART出力を確認する。

詳細と現物記入欄は [DIPスイッチ設定管理](dip_switch_settings.md) を参照する。

## 次の実機試験

1. 販売基板仕様、DIP番号と論理対応、TX電圧、電源容量を実測し、DIP設定管理表へ記録する。
2. CH9350 TX→GP9、共通GNDを接続する。RX接続条件は基板確認後に決める。
3. USBキーボードで生HEXが出ることを確認する。
4. OPTICON L-46X（既存テスト機）の通常起動と実QR入力を確認する。
5. 実測フレームを保存し、実装済みデコーダの押下/解放、Shift、英数字、Enter結果と照合する。
6. 同一コード反復・100回読取り・USB再接続・電源再投入を比較する。
7. 単体試験結果を受けて統合インターフェースを検討する。製品PASS/FAILはATEの責任。

結果は [test_results.md](test_results.md) に記録する。正式Cache、SS書込み、CSVへの統合は別工程。
