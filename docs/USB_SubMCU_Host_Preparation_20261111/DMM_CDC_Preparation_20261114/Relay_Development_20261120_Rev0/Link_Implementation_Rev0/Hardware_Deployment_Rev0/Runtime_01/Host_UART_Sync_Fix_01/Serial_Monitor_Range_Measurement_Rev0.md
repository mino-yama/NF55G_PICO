# 7355 レンジ切替・単発測定・任意コマンド送信手順 Rev.0

2026-11-20。親Pico→Host .2→7355の識別中継成功後、ユーザーがシリアルモニターで設定/測定を確認する手順。Codexから実機へ以下の設定/測定は送信していない。既存Quick Startは上書きしない。

## 送信条件と応答

COM7 ELECOM、57600bps/8N1、flow controlなし、終端CR。USB-A→7355 USB-B接続、外部給電。Host PC USB-Cは外したまま。7355 BUS=CDC/LANG=SCPIを前提とする。

**コード枠も1行ずつ送信し、その応答が完了してから次の行を送る。一括貼付け・連続送信はしない。** EXT_SENDは機器から応答のない設定用、EXT_QUERYは応答を受け取る指令用。?記号による自動判別はない。

EXT_SEND <期限ms> <機器コマンド本文> → OK:EXT_TX（全送信完了）。これは機器の設定受理やレンジ一致を保証しない。設定後は必ず次のQueryを実行し、応答を受ける。メーカー§6.8.4（冊子6-42/PDF136ページ）のUSB通信条件に従う。設定からQueryへ20ms以上空ける運用は既存初回手順の暫定値で、手動送信では一呼吸置く。SCPI CDCのメーカー保証値として20msを断定しない。

EXT_QUERY <期限ms> <機器コマンド本文> → OK:EXT_RX:<長さ>:<原文HEX>。CRLFもHEXに含む。文字列/カンマ/引用符/数値表現は変換せず返す。期限1〜10000ms、本文/応答192byteまで。通常Queryは2000ms、測定/完了確認は10000msを例にする。タイムアウト後は自動/盲目的に再送せずログを保存する。fault解除の代わりに再送しない。

初回測定は既知の20V未満の低い直流電圧をV/COMへ接続する。レンジ切替のために高電圧を印加する必要はない。電流端子は用いない。前面レンジ/入力値/測定応答を記録する。

## 1. 識別と開始前エラー

~~~text
EXT_QUERY 2000 *IDN?
EXT_QUERY 2000 :SYST:ERR?
~~~

SYST:ERR?はエラーキューを読み進めるため原文を保存する。開始前の既存エラーと後から発生したエラーを分ける。初回は新たな非ゼロエラーを確認した時点で設定/測定を進めず報告する。無条件の*CLSや*RSTで履歴/設定を消さない。

## 2. DC電圧・20V固定へ切替

各設定の後のQuery応答を待つ。以下も一行ずつ。

~~~text
EXT_SEND 2000 :INIT:CONT OFF
EXT_QUERY 2000 :INIT:CONT?
EXT_SEND 2000 :ABOR
EXT_QUERY 10000 *OPC?
EXT_SEND 2000 :SENS:FUNC "VOLT:DC"
EXT_QUERY 2000 :SENS:FUNC?
EXT_SEND 2000 :SENS:VOLT:DC:RANG:AUTO OFF
EXT_QUERY 2000 :SENS:VOLT:DC:RANG:AUTO?
EXT_SEND 2000 :SENS:VOLT:DC:RANG 20
EXT_QUERY 2000 :CONF?
EXT_QUERY 2000 :SYST:ERR?
~~~

復号後の期待: INIT:CONT?=0、OPC?=1、FUNC?はVOLT:DC（引用符付きもあり得る）、AUTO?=0。CONF?の機能/レンジ/分解能原文、前面レンジ、SYST:ERR?の原文を記録する。

**USB-CDC-RANGE-01は未解決。過去には前面20Vに対してCONF?が約200V（1.999999E+02）を返した。今回も相違があれば、そのまま原文と前面表示を記録し、20Vに一致したと扱わず測定段階へ進む前に共有する。** この手順のRANG 20はメーカー書式と既存確認手順の指定値で、今回の機器で20V切替成功を保証する記述ではない。19.999等への置換や独自換算で相違を吸収しない。

## 3. 単発測定の準備と1回読出し

前段の機能/レンジと入力条件を確認してから実行。設定ごとに*OPC?で完了確認する。

~~~text
EXT_SEND 2000 :TRIG:SOUR IMM
EXT_QUERY 10000 *OPC?
EXT_SEND 2000 :TRIG:COUN 1
EXT_QUERY 10000 *OPC?
EXT_SEND 2000 :SAMP:COUN 1
EXT_QUERY 10000 *OPC?
EXT_SEND 2000 :TRIG:DEL 0
EXT_QUERY 10000 *OPC?
EXT_QUERY 2000 :TRIG:SOUR?
EXT_QUERY 2000 :SYST:ERR?
EXT_QUERY 10000 :READ?
EXT_QUERY 2000 :SYST:ERR?
~~~

OPC?は復号1、TRIG:SOUR?はIMMを確認。測定前に非ゼロエラーがあればREAD?へ進まない。READ?はトリガ系を初期化して測定データを返す（冊子6-43/PDF137ページ）。FETC?は既存データの読出しであり新規測定の代用にしない。MEAS?はDCV等の設定を変えるため、レンジ切替確認では使わない。

応答はHEXから原文を復号して前面値/既知入力と比較する。ヘッダや指数表現を保持し、OLやエラーを通常の測定値として採用しない。正確度や製品PASSを通信成功だけで判定しない。再度1回測定する場合は前回の応答が完全に終了していることを確認後、READ?を明示送信する。失敗時の自動再測定ではない。

## 4. 200Vレンジへ切替

同じ低電圧入力のままレンジだけを変える。

~~~text
EXT_SEND 2000 :SENS:VOLT:DC:RANG 200
EXT_QUERY 2000 :CONF?
EXT_QUERY 2000 :SYST:ERR?
~~~

前面200VとCONF?、エラーなしを確認後に限り、次を送る。

~~~text
EXT_QUERY 10000 :READ?
EXT_QUERY 2000 :SYST:ERR?
~~~

20Vへ戻すときは手順2のRANG 20→CONF?→SYST:ERR?を実行し、前面と読戻しの相違に同じ扱いを適用する。低いレンジ0.2/2等は今回は例示せず、入力条件を確認してから別途決める。

## 5. オートレンジへ切替

~~~text
EXT_SEND 2000 :SENS:VOLT:DC:RANG:AUTO ON
EXT_QUERY 2000 :SENS:VOLT:DC:RANG:AUTO?
EXT_QUERY 2000 :SYST:ERR?
~~~

復号1と前面AUTO、エラーなしを確認後、単発測定する。

~~~text
EXT_QUERY 10000 :READ?
EXT_QUERY 2000 :CONF?
EXT_QUERY 2000 :SYST:ERR?
~~~

終了時はDCV/AUTO/連続OFF/IMM/トリガ回数1/サンプル1/遅延0を残す。元設定へ自動復元は行わない。必要なら開始前の値を記録し、終了後ユーザーが設定と読戻しで復帰する。

## 任意の機器コマンド

上記と同じ外枠で機器コマンド本文を置き換える。機器から応答のある指令はEXT_QUERY、応答のない指令はEXT_SENDを指定。EXT_SEND設定後に読戻しQueryまたは*OPC?、必要に応じSYST:ERR?を明示して応答を受ける。セミコロン結合や連続設定で確認を省略しない。

例: EXT_QUERY 2000 :CONF? は7355の設定確認。治具自身の*IDN?とEXT_QUERY 2000 *IDN?は宛先が異なる。Host/親が任意のSCPI設定を補ったり応答を測定Cache/AD/ARへ自動格納したりはしない。

## 根拠と実施状況

原典: reference/ADCMT_7355_20261104/7355-ope-fow-00000200a00-j.pdf、§6.8.4、冊子6-42〜6-46（PDF136〜140ページ）。設定後Query必須、FUNC/CONF/READ/INIT/ABOR/TRIG/SAMP/RANG書式を照合。Query引数の省略が表記上曖昧なSAMP:COUN?やTRIG:DEL?を必須確認にせず、設定後は共通*OPC?を使った。

既存のCDC_Settings_Voltage_Quick_Test_Rev0.mdと過去実測結果を参照。IDN中継は実機確認済み。以下のレンジ/測定手順は今回作成したユーザー操作用で、Codexによる実行済み結果ではない。USB-CDC-RANGE-01はOpenのまま。コード/Flash変更なし。
