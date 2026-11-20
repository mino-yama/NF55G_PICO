# 中継の開発用通信契約 提案 Rev.0（承認済み原案）

**2026-11-20承認済み。現行は[ユーザー確定仕様 Rev.1](Interface_Spec_Rev1.md)。以下は承認前の原案を保存した履歴であり、未承認という記述は当時の状態を示す。**

2026-11-20 JST。実装済みの内部コアとは区別し、以下は人間確認用の提案。正式仕様の確定、GPIO実装、実機配線・配置はまだ行わない。既存AGENTS.mdのOpen Issue推測禁止とUART契約案の確認条件に従う。

## 1. シリアルモニター/ATE入口の案

接続は既存ATE UART0（親GP0 TX/GP1 RX、57600/8N1）を維持。RS232経由の既存接続を用い、TTL UARTへRS232信号を直結しない。NF55G UART1は転用しない。

|操作|入力例|意味|
|---|---|---|
|Query|EXT_QUERY 2000 *IDN?|外部測定器へ本文とCRLFを一回送信し、CRLFまで待つ。期限は要求受付から2000ms|
|応答なし設定|EXT_SEND 2000 :SENS:VOLT:DC:RANG 20|同じ中継先へ一回送信。機器の設定受理/実行完了を推定しない|

上記の2000は入力例で、固定既定値にはしない。timeoutは1～10000msの明示指定、SCPI本文上限192 byte、応答上限192 byteを開発用候補とする。送信側のコマンド終端は親の既存CR/LF/CRLFを受理するが、本文には含めずHost adapterがCRLFを一度だけ付加する。外側の指令名とtimeoutの後の本文を無変形で保持し、空白・引用符・カンマ・大文字小文字を変更しない。現在のparserのstrip処理を本文に適用しないように入口を分ける。?記号から応答有無を推測しない。

Query応答案: OK:EXT_RX:<10進byte数>:<原文の大文字HEX>。CRLFもHEXへ含める。これによりIDNのカンマや空白を既存ATE応答から区別する。応答なし設定の全送信完了はOK:EXT_TX。失敗はERR:EXT_<内部理由>:AMBIGUOUS=0/1を候補とする。正式エラー名称は本案承認時に確定する。返却は既存ATE応答終端設定に従う。

## 2. 親子UARTの開発用候補

- 115200/8N1。親: PIO1のTX=GP12/RX=GP13、Host: TX=GP0/RX=GP1、GND共通。親TX→Host RX、Host TX→親RX。これらは別MCUのGPIOで、Host GP12/13のUSB-Aと混同しない。親のPIO1の2SM利用、命令メモリ・IRQ・負荷は実装/実機検証前に照合する。QRの独立経路候補GP8/9は転用しない。
- Host GP0の現行診断文字列を同じ正式応答線へ混在させない。中継FWでは診断の平文出力・自動IDN・固定測定シーケンスを無効にする。必要な診断は別工程とする。
- 物理pin番号・Expander/中継基板の接続位置・RESET結線は未確認のため本案で確定しない。既存のPin_Assignment記録と現物照合が必要。

## 3. 親子フレーム候補

ASCIIで @X1,<session>,<request>,<kind>,<mode>,<timeout>,<length>,<payload_hex>,<crc> とCRLF。sessionは親起動nonce16HEX+Host起動nonce16HEX、requestは8HEX、modeは0（送信のみ）/1（Query）、timeoutは8HEX ms、lengthはpayload原文長4HEX、crcは8HEX。payloadは最大192 byte（HEX384文字）を候補とする。CRC-32/IEEE（binascii.crc32相当）を@からpayload_hex直後のカンマまでのASCIIへ計算する。512 byte以内のフレーム上限とし、過長/不正CRCは実行せず破棄する。

kind候補: H=接続照合要求、h=照合応答、Q=要求、A=受付、T=機器への全送信完了、R=完成応答、E=要求失敗。接続照合では片側nonce未確定部分は0を用い、照合後に両起動nonceが一致した要求だけを受理する。起動nonceの生成方法は実装時にSDK/MicroPythonの乱数APIを照合する。接続照合payloadのFW版/基板ID表現は実装前の詳細レビューで揃える。

要求は一件ずつ。親はATE応答と要求相関を管理し、HostはCDCへの本文送信とCRLF応答完成を管理する。AとTとRを区別し、Tは製品や機器の動作成功を意味しない。timeout/部分送信/切断時は自動再送しない。状態復帰は接続境界と旧データ排除をadapterが実証してから明示する。単なるquiet時間や新tokenの付与だけで遅着排除済みと扱わない。

## 4. 初回受入の範囲

識別Query一件、任意設定一件、応答の文字列保持、timeout/切断/遅着拒否、ATE/NF55G優先を確認する。レンジ値の一致や測定精度を中継受入の条件にしない。レンジの検証はユーザーが中継完成後に行う。任意応答を測定Cacheへ自動格納せず、AD/ARへ接続しない。

## 5. 今回の実装との区別

src/external_instrument_relay.pyはGPIO/通信書式に依存しない内部APIのみ。上記ATE名・pin・baudrate・上限・CRC・nonceは現時点でコードへ固定していない。親/Hostの実通信、ATE入口、本番schedulerは未接続であり、モニターからの縦通しはまだできない。
