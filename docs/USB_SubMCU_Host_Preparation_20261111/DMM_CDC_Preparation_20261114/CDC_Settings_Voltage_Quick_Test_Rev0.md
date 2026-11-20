# 7355 USB CDC設定・電圧測定初回手順 Rev.0

2026-11-20 最新実機結果: .5のUSB/CDC/IDNは成立。レンジ設定後error=0、CONF約200Vと前面報告20Vの相違を再現。CONF_RANGE_NOT_20VでREAD前停止し測定値未取得。[試行1結果](Handoff_20261120_Rev0/Runtime_v5_run01/Result_Rev0.md)。以下の未実行記述は試行前の記録として保持。

2026-11-20 後続更新: 評価FW.5を対象BFCF2EDB84B0B37Fへ配置、Flash verify OK。書込み後infoで.5と同個体を確認。BOOTSELのままでrebootせず、測定は未実施。[配置結果](Handoff_20261120_Rev0/Deployment_v5/Result_Rev0.md)。以下の未配置記述は配置前の状態として保持。

## 2026-11-20 CDC Host引継ぎ・応答検証補強（最新）

USB/CDC/IDNはraw #07で確認済み。測定FW.1/.2はREAD前停止、.3は配置記録あり・実行記録なし。今回ユーザー回答は「20Vレンジで電源OFF」。CONF読戻し約200Vとの相違は未解決として追跡する。

評価版.5では、設定数値とCONF読戻し検証を実FW共用Cモジュールへ分離し、NaN/Inf・非10進表記・埋込みNUL・部分/複数行・不正な分解能を拒否する。既存.4の19～21Vゲートを維持し、レンジ指定コマンドや量産基準を変更しない。実Cの7テストを追加。全Host Unit/Mock 382件成功。実機再配置・測定は未実施。版別成果物・試験ログ・再開手順は[引継ぎ記録](Handoff_20261120_Rev0/Result_Rev0.md)を参照する。


2026-11-14作成、2026-11-20追記。同一USB Host SubMCU案件。CDC Host/IDN実機通信は確認済み。測定FW.3は配置済みだが未実行、.4は`:CONF?`の20Vレンジ確認ゲートを追加したbuild候補。

## 1. USB CDC設定と確認済み実績

|項目|使用条件・状態|
|---|---|
|新しい接続構成|RP2350-USB-AのUSB-A → USB A–Bケーブル → 7355背面USB-B。CDC Host/IDN通信成立を2026-11-20確認|
|7355本体のIF選択|ユーザー確認でBUS=CDC|
|今回準備するコマンド体系|ユーザー確認でLANG=SCPI|
|CDC line codingの再現条件|9600 baud、8 data bits、parity None、1 stop bit（8N1）。PCで成功した値でありUSB実転送速度の意味ではない|
|CDC制御線|DTR=ON、RTS=ON。PC実績の再現条件。全個体共通の必須仕様とまでは断定しない|
|フロー制御|新HostではDTR／RTSを明示ONとして保持する。UARTのRTS/CTS配線や自動フロー制御とは別|
|送信終端|ASCIIコマンド＋CRLF（0D 0A）。IDNは7byte `2A 49 44 4E 3F 0D 0A`|
|確認済み応答終端|IDNはCRLF。その他の応答終端は初回原文で確認する|
|出力データ|CDCはASCIIを使用。メーカー資料でREAL64はUSB CDC対象外|
|VID:PID|1334:0309（16進）、USB REV_0100|
|Windows識別|usbser、COM24（当時の割当て、固定仕様ではない）、Class_02/SubClass_02/Prot_01|
|IDN成功原文（PC直結の別個体）|`ADC Corp.,7355,246410072,  A01\r\n`。今回の個体IDではない|
|IDN成功原文（USB Host実測）|`ADC Corp.,7355,246410099,  A02\r\n`。ユーザー確認により別個体差は想定内|
|実測USB serial|今回のIDN応答からは未確認|
|PC再現実績|両制御線ONで初回＋COM再開2回の計3回IDN成功|

元の実測記録: [PC直結結果](PC_Connection_Rev0/Result_Rev0.md)、[制御線比較と再開記録](PC_Connection_Rev0/Repeat_And_RTS_Check/Results.json)。この実績をRP2350-USB-AのHost受入へ転用しない。旧記録のType_C1 native Host案は現構成のFW指定に使わず、USB-A側の回路・PIO Host設定を別途照合する。

## 2. コマンド早見表（SCPI）

各行はCRLFを付けて単独送信する。下記はメーカーリファレンスの短縮形。`*IDN?`以外は今回の測定用FWで送信予定、実機応答は未確認。

|目的|コマンド|確認方法|
|---|---|---|
|識別|`*IDN?`|上記識別応答|
|直流電圧選択|`:SENS:FUNC "VOLT:DC"`|`:SENS:FUNC?`で`VOLT:DC`|
|交流電圧選択|`:SENS:FUNC "VOLT:AC"`|`:SENS:FUNC?`で`VOLT:AC`|
|DC固定レンジ指定|`:SENS:VOLT:DC:RANG 20`|`:CONF?`の機能・レンジと前面表示を確認|
|DCオートOFF|`:SENS:VOLT:DC:RANG:AUTO OFF`|`:SENS:VOLT:DC:RANG:AUTO?` → `0`|
|DCオートON|`:SENS:VOLT:DC:RANG:AUTO ON`|`:SENS:VOLT:DC:RANG:AUTO?` → `1`|
|設定条件確認|`:CONF?`|機能・レンジ・分解能を原文記録|
|新規測定して読出し|`:READ?`|測定応答。トリガ源IMMを用意する|
|取得済み値の読出し|`:FETC?`|新しい測定の開始と混同しない。初回の主経路にはしない|
|設定完了確認|`*OPC?`|`1`。製品PASSや測定確度の合格を意味しない|
|エラー確認|`:SYST:ERR?`|コードと文字列を保存。読出しでキューが進むため履歴を残す|

DCレンジ指定値（V）: `0.2`＝200mV、`2`＝2000mV、`20`＝20V、`200`＝200V、`1000`＝1000V。
ACは`VOLT:AC`へ置換し、最上位レンジは`700`。初回はDCで確認し、ACの試験入力条件・前面比較は別途決める。

固定レンジ設定とAUTO OFFの両方を明示し、読出しで確認する。レンジ照合は`:CONF?`を使う。リファレンスの`:RANGe? {MAXimum|MINimum}`は現在レンジの問合せとしての引数省略可否が表記上明確でないため、初回手順の必須コマンドにしない。

## 3. IDN直後の実施順（DC、単発測定）

前提: BUS=CDC、LANG=SCPIを前面で確認。初回は入力が20Vレンジ内に収まる既知の直流電圧とし、入力値とV/COM接続、前面表示を記録する。20V以上を想定する場合は最初から適切なレンジへ変更する。レンジ切替の確認のために高電圧を印加する必要はない。

メーカー§6.8.4はUSBで設定コマンドを連続させず、設定後にQueryを送って応答を受けるよう指示している。以下は「設定 → Query → 応答完了」を1組として逐次処理する。Queryの前に20ms以上空ける運用を初回の暫定値とする（20msの明記はADCコマンド章§6.8.3にあり、SCPI CDC固有の保証値とは扱わない）。

|順序|送信（設定がある場合は設定の後にQuery）|期待・記録|
|---|---|---|
|1|`*IDN?`|機種・S/N一致。応答完了後に次へ|
|2|`:SYST:ERR?`|開始前のエラー原文を保存。既存エラーは今回の指令のせいと断定しない|
|3|`:INIT:CONT OFF` → `:INIT:CONT?`|`0`。連続モードを止める|
|4|`:ABOR` → `*OPC?`|`1`。測定系をIDLEへ|
|5|`:SENS:FUNC "VOLT:DC"` → `:SENS:FUNC?`|DCV選択|
|6|`:SENS:VOLT:DC:RANG:AUTO OFF` → `:SENS:VOLT:DC:RANG:AUTO?`|`0`|
|7|`:SENS:VOLT:DC:RANG 20` → `:CONF?`|DCV・20Vレンジと前面表示を確認|
|8|`:TRIG:SOUR IMM` → `:TRIG:SOUR?`|`IMM`。他のトリガ源ではREAD?がErr-214になり得る|
|9|`:TRIG:COUN 1` → `:TRIG:COUN?`|1|
|10|`:SAMP:COUN 1` → `:SAMP:COUN?`|1|
|11|`:TRIG:DEL 0` → `:TRIG:DEL?`|0秒。以前の待ち時間設定を引き継がない|
|12|`:SYST:ERR?`|新規エラーがあれば測定へ進まず原文保存して切分け|
|13|`:READ?`|1測定応答を保存し、前面値・既知入力と照合|
|14|`:SENS:VOLT:DC:RANG 200` → `:CONF?`|同じ低電圧入力で200Vレンジへの切替を確認|
|15|`:READ?`|再測定。レンジにより桁・分解能は変わる|
|16|`:SENS:VOLT:DC:RANG:AUTO ON` → `:SENS:VOLT:DC:RANG:AUTO?`|`1`、前面AUTO表示確認|
|17|`:READ?`|AUTOで再測定|
|18|`:SYST:ERR?`|終了時のエラーを記録|

この手順は終了時DCV/AUTO/連続OFF/IMM/単発数1/遅延0を残す。試験前設定への自動復元は行わず、必要なら開始時の値をQueryで保存して終了後に設定・読戻しする。

Queryは応答の行境界まで受信してから次へ進む。暫定の評価用timeoutは通常Query 2秒、測定・OPC 10秒とし、メーカー保証時間や量産Timingへ昇格しない。timeout、受信断片、予期しない非同期データ、機種不一致では中断し、自動で設定・測定を再送しない。タイムアウト後の遅着が次Queryへ混入しないよう区別する。原文を残す前の入力buffer消去はしない。

測定応答はヘッダ付きの場合があるため、最初から裸の浮動小数と仮定しない。桁数・ヘッダ・指数・CRLFを保存する。OLはメーカー資料上約±9.99999E+37または±9.999999E+37で、通常の電圧値として採用しない。NULL・スケーリング等の計算状態も未確認のため、通信成功だけで入力電圧との一致や校正合格を判定しない。

## 4. LANGがADCだった場合の参考

ADC形式ではDCV=`F1`、ACV=`F2`、AUTO=`R0`、200mV=`R3`、2000mV=`R4`、20V=`R5`、200V=`R6`、DC1000V/AC700V=`R7`。設定読戻しは`F?`と`R?`。SCPIと混在送信しない。

`MD?`は保存済み取扱説明書の表でRS-232/LAN専用とされ、`IRO?`もUSB CDC対象外。したがってADCのCDC測定読出しをこれらで代用しない。今回の即試験経路はSCPIを前提とし、LANG=ADCのまま使う場合のCDC読出し経路はメーカーサンプル等で追加確認する。34401モードも今回の手順対象外。

## 2026-11-20 単発DC電圧評価プロファイル

別ターゲット`meter-host-voltage-test-20261120.4`を追加。既存のIDN専用UF2は維持する。測定版はCDC mount後、IDN確認、開始時`:SYST:ERR?`、連続OFF/ABOR/DCV/20V固定/AUTO OFFを逐次設定し、レンジ設定直後に`:SYST:ERR?`、続いて`:CONF?`を行う。`:CONF?`応答の先頭full-scale値が19～21Vの範囲外、応答形式不明、timeout、overflow、既知の設定Query不一致、SCPI error codeが0以外ならREAD前に停止する。合格時だけIMM/trigger count 1/sample count 1/delay 0を逐次設定し、`:SYST:ERR?`確認後に`READ?`を一回だけ実行、最後にerror queryを行う。自動再送なし。`:CONF?`と`:READ?`はraw保存、測定精度・製品合否は自動判定しない。版.1は引用符付き`"VOLT:DC"`を拒否、版.2は数値`00001`を文字列不一致で拒否、版.3は数値比較を実装したが未実行。版.4は実測`:CONF?`が約200Vを示すように見えたことを受けてREAD前レンジゲートを追加した。

この試験は7355の設定状態を変更し、以前の状態へ自動復元しない。終了時はDCV、固定20V、AUTO OFF、連続OFF、IMM、trigger/sample count 1、delay 0となる。ユーザーは事前設定を記録済みと回答。既知入力は「約0.2V、無負荷」で、配置前にV/COMへ接続済みとの確認を受領。LANG=SCPI、BUS=CDCも確認済み。入力源の校正状態と実電圧は別途記録し、通信応答を精度合格や製品PASSと扱わない。

測定版`.1`と`.2`は対象chipid `0xbfcf2edb84b0b37f`へ配置しFlash verify OK。raw #08/#09で`:READ?`前に停止。raw #09の`:CONF?`応答は`"VOLT +1.999999E+02,+1.000000E-05"`。これは約200Vに見え、指定した20Vと異なるため前面表示で確認する。版`.3`は配置済みだが未実行、外部電源を入れない。20V読戻しゲート付き版`.4`はbuild/hash検証済み、未配置。配置前に停止時の現在レンジと7355前面表示を確認する。artifact/版/hashはbuild manifestを参照。

## 根拠と未確認事項

- 保存済みメーカー英文説明書: `reference/ADCMT_7355_20261104/7355-ope--foa-00000201a00-e.pdf`。印刷6-1/PDF95（BUS）、6-10/PDF104（USB）、6-20/PDF114（LANG）、6-26/PDF120（測定数値・OL）、6-29～32/PDF123～126（ADC形式）、6-42～46/PDF136～140（USBの順序制約・機能・測定・トリガ・レンジ）、6-52～54/PDF146～148（ASCII・IDN・OPC）、8-24/PDF210（Err-214）。重要な表はPDF136/137/140を描画して確認。
- 和文説明書 `reference/ADCMT_7355_20261104/7355-ope-fow-00000200a00-j.pdf` の6-46/PDF140でもレンジ記法を照合。
- メーカー公開窓口: https://www.adcmt.com/download/ope_current 、サンプル案内: https://www.adcmt.com/download/sampleprogram 。コマンドの直接根拠は保存済みメーカー説明書。FW A01に対する全SCPI機能の実機適合は未確認。
- 未確認: 前面BUS/LANG、既知入力・前面測定値、上記測定コマンドの応答、Host側記述子・endpoint、RP2350-USB-A給電・PIO Host FW、親子UART連携。USB-SUB-05等はOpenのまま。

2026-11-20に測定用FWプロファイル、CMakeターゲット、README、build manifestと本手順を更新。IDN専用UF2は維持し、両プロファイルをARM build/link、picotool metadata、artifact hashで確認。Host/Mock回帰375件は成功。測定用FW`.1`/`.2`は設定Query比較でREAD前に停止。修正版`.3`を配置・verify済みだが測定再試験は未完了。実測精度評価は未実施。既存のNF55G向けコード、配線、原典資料は変更せず、NF55Gへの書込み・製品PASS/FAIL判定は行わない。
