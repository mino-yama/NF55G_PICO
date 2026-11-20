# 外部測定器USB Host CDC 引継ぎ・開発継続 Rev.0

2026-11-20 最新実機結果: .5のUSB/CDC/IDNは成立。レンジ設定後error=0、CONF約200Vと前面報告20Vの相違を再現。CONF_RANGE_NOT_20VでREAD前停止し測定値未取得。[試行1結果](Runtime_v5_run01/Result_Rev0.md)。以下の未実行記述は試行前の記録として保持。

2026-11-20 後続更新: 評価FW.5を対象BFCF2EDB84B0B37Fへ配置、Flash verify OK。書込み後infoで.5と同個体を確認。BOOTSELのままでrebootせず、測定は未実施。[配置結果](Deployment_v5/Result_Rev0.md)。以下の未配置記述は配置前の状態として保持。

日付: 2026-11-20 JST。同一USB Host SubMCU案件を継続。以下を最新状態とする。過去の0 byte/CDC未成立の記録は当時の状態として保持。

## 確認できた事実

- 対象Host: RP2350-USB-A、USB serial BFCF2EDB84B0B37F。QR用基板とは別。
- 起動/診断UART: raw #04以降でFW版・Chip ID・USB_HOST_READYを受信。
- [raw #07](meter_host_com22_capture_20261120_07.raw): VID/PID=1334:0309、CDC mount、9600/8N1、DTR/RTS、IDN一回とCRLF32 byteを確認。測定器IDはADC Corp.,7355,246410099,  A02。過去PC直結の246410072/A01とは別個体。
- [raw #08](meter_host_com22_capture_20261120_08.raw): 測定FW.1は引用符付きVOLT:DCを誤拒否しREAD前停止。
- [raw #09](meter_host_com22_capture_20261120_09.raw): 測定FW.2は00001を誤拒否しREAD前停止。CONFは約200 Vを示す。
- 測定FW.3: manifestに配置・Flash verify OKの記録あり。実行ログなし。現在Flash内容は今回読出し確認していない。
- 測定FW.4: 未配置の記録。変更前manifestと6ビルド成果物のhashを照合し、[変更前退避](before_changes/build_manifest.json)に保持。
- ユーザー回答: 引継ぎ時「20Vレンジで電源OFF」。PC USB-Cの現在接続状態までは回答から確定しない。
- 既存raw #08/#09にREAD送信なし。単発測定の取得・精度確認は未完了。

証跡は元のtempファイルを変更せずコピーし、[Evidence Manifest](Evidence_Manifest.json)でサイズ・SHA-256を記録した。記録がないことだけで未実施と断定せず、上記は保存された証跡の範囲である。

## 推測・未確認事項

raw #09でRANG 20の後のCONF応答は、VOLT +1.999999E+02,+1.000000E-05。数値は約200 Vで、ユーザー報告の前面20 Vと相違する。同一時点での対応、nominal値とfull-scale境界の扱い、機器の応答仕様は未確認。原因は断定しない。メーカー英文説明書6-46/PDF140のレンジ指令表をテキスト・保存済みページ画像で照合したが、この相違を解消する記述は今回確認していない。

[USB-CDC-RANGE-01](../../../Open_Issues.md)をOpen追加。200 V応答を20 Vへ読み替えず、レンジコマンドを独自変更しない。正式親子UART/ATE中継、外部測定Cacheとの接続、AD/AR、共用電源の電気受入も残る。IssueはCloseしない。

## 今回の変更

- [scpi_response_validation.c](../../../../firmware/usb_submcu_external_meter_host/scpi_response_validation.c)と対応ヘッダを追加。設定数値/CONF解析をmain.cから分離し、実FWとHostテストで同じC処理を使用する。
- NaNは旧.4の「19未満または21超なら拒否」という比較を通る余地があるため、有限10進数の文法・変換成否を先に照合する。NaN/Inf、16進数、埋込みNUL、不完全指数、オーバー/アンダーフローを拒否する。
- CONFはCRLFまで完成した1行全体、機能VOLT、数値full-scale、正の有限分解能を照合する。余分な行/フィールド、片側引用符、未完成応答を拒否。既存.4の19～21 Vゲートは変更せず、量産の精度許容差へ昇格しない。
- main.cの呼出しを接続し、日本語コメントを追加。CMakeの測定用評価版をmeter-host-voltage-test-20261120.5へ更新。コマンド列、GPIO、通信条件は変更しない。
- [追加テスト](../../../../tests/test_external_meter_scpi_validation.py)7件で実Cをnativeコンパイルし、実測00001/約200Vと不正・部分応答、19～21 V境界を検証する。
- FW README/build manifest、受入仕様、電圧手順、Test Specification、Open Issues、CHANGELOGを更新。既存の他作業差分・原典・QR FW・NF55G向けソースは変更しない。

## 検証

- .venv/Scripts/python.exe -B -m unittest discover -s tests -v: **382件成功、10.344秒**。追加7件を含む。[全Host/Mockログ](Host_Mock_20261120_Rev0.log)。
- ARM build/linkはIDN用/電圧評価用とも成功（アプリは-Wall -Wextra -Werror）。picotoolのUF2ファイル読取りで版.5、GP0診断TX、GP12/13 USB-A、SDK2.2.0を確認。[ビルドログ](Build_20261120_Rev0.log)／[UF2 metadata](UF2_Info_20261120_Rev0.log)。
- .5 UF2: 117760 bytes、SHA-256=5156ce1fb1556cdba723a0b3021f57fa14ed803776435c0b7de15bc84876b860。全6成果物の最新hashは[build manifest](../../../../firmware/usb_submcu_external_meter_host/build_manifest.json)へ更新。変更前.4を退避済み。新UF2は未配置。
- 今回変更した追跡文書のgit diff --checkは成功。追加/変更C・ヘッダ・テストにも末尾空白なし。全体チェックは既存の別ファイルSplit_Host_Architecture_Rev0.md:5～6の末尾空白を指摘し、今回変更せず保持。
- 実機書込み・通電・測定、NF55G制御は今回実行していない。Host/Mock成功をCDC実機受入や精度合格に読み替えない。

## 次の実機工程

1. 外部電源OFFを維持し、7355のUSBケーブルと診断UARTをHostから外す。外部5VはスイッチOFFだけでなくHostから切り離す。PC USB-Cと外部5Vは共通電源ネットのため同時直結しない。
2. 書込みモードはPC USB-Cだけを接続し、BOOTを押したままRUN/RESETを押して離し、その後BOOTを離す。対象serial BFCF2EDB84B0B37FのBOOTSEL認識を確認する。
3. 最新build manifestの.5 UF2 hash・対象を照合して配置し、Flash verifyと版を記録する。今回のソフト開発ではここを未実施とする。旧.3を外部測定器接続状態で試験起動せず、.5へ置換してから次へ進む。
4. 書込み後PC USB-Cを外し、無給電でGP0 TX→SH-U05A RXDとGNDを接続。変換器TXD/3V3/5V0はHostへ接続しない。USB-A→7355 USB-Bを固定接続。BUS=CDC、LANG=SCPI、既知約0.2 VのV/COM入力と現在の前面設定を確認する。
5. COM22の現在の割当てを照合し、115200/8N1・送信なしのUART採取を先に開始。新規raw名で120秒採取し、待受開始後に外部電源を一度投入する。受信待受と電源操作は別々に合図して行う。
6. .5 banner→USB/CDC mount→制御転送→SCPI設定を確認。CONFが再び約200 VならCONF_RANGE_NOT_20VでREAD前停止するのが期待動作。前面レンジとrawを同一試行として保存し、原因確認へ戻る。19～21 Vで他の照合も通った場合だけREAD一回まで進む。精度合格や製品PASSとはしない。

この評価FWは7355の設定を変更し、元の設定へ自動復元しない。開始時設定を保持し、必要な復元は記録と読戻しで確認する。単発20 V評価が成立してから200 V/AUTO、単体成立後に親子UART/ATEへ進む。
