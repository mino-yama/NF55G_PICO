# 中継リンク実装 第2段階 Rev.0

2026-11-20 親配置完了: COM6/unique_id 69f7d45962cfdfadの既存26ファイルを退避・SHA照合後、配置対象30ファイルを実機SHA照合（追加/更新8）。実機RAM検証と配置後import成功。通常起動せずREPL停止、PIO4/5はinactive。Host/親の配置は完了したが、配線と実機中継受入は未実施。[親配置結果](Hardware_Deployment_Rev0/Parent_Deployment_01/Result_Rev0.md)。以下の親未配置記述は配置前の状態として保持。

2026-11-20 後続配置: Host BFCF2EDB84B0B37Fへmeter-host-relay-20261120.1を書込み、Flash verifyと書込み後版照合に成功。旧.5全Flash退避・照合済み。BOOTSELのままrebootせず、親Picoは未配置・実機中継未試験。[Host配置結果](Hardware_Deployment_Rev0/Host_Deployment_01/Result_Rev0.md)。以下のHost未配置記述は配置前の状態として保持。

日付: 2026-11-20 JST。同一USB Host SubMCU案件。承認済み通信契約Rev.1に沿って、ATE受付から親adapter、Hostの実C engineまで接続した。レンジ検証は保留。

## 結果と現在の状態

- EXT_QUERY/EXT_SENDを既存ATE入口に登録し、本文の空白/引用符/カンマ/大小文字を保持する。外部機器応答をHEXで返す。
- 親は待受をblockingにせず、service_onceでATE入力→NF55G idle処理→外部中継を巡回。未完了中は次のATE要求を順番待ちにし、先行応答を追い越さない。Logger/SDのwrite/flushは通信待ち中に行わない。
- HostはGPIO0/1のX1 UART専用。自動IDN/レンジ/測定や平文ログを出さず、要求された本文にCRLFを一度だけ付けてCDCへ送る独立UF2を用意した。USB line coding/DTR/RTSの制御転送は接続処理として実施する。
- 親Pythonと実Host Cの縦通しはHost上で成功。今回追加32件を含め全446件成功。ARM build/linkも成功。
- 実機Flash/ファイル配置/配線変更/通電/計測器送信は今回未実施。ソースのEXTERNAL_INSTRUMENT_ENABLEDはFalseを保持し、既存配線へ未確認GPIOを自動で適用しない。実機確認用パッケージのコピーだけTrueにしている。

## 変更ファイルと役割

|ファイル|今回の変更・目的|
|---|---|
|src/external_instrument_link.py|CRC/長さ付き受信、HELLO照合、要求相関、非blocking送受信、期限・復帰制御|
|src/external_instrument_pio.py|PIO1 SM4 TX/SM5 RX、GP12 TX/GP13 RX、115200/8N1。FIFO空き分のみ送信、2048byte RAM受信リング|
|src/command_parser.py|外部測定器本文をstripせず専用parserで分類|
|src/main.py|外部要求を非同期受付し、応答完成後にATEへ返す。FU禁止・既存NF55G経路を維持|
|src/config.py|明示有効化flagと対象Host chipid。量産配置側の既定は無効|
|firmware/usb_submcu_external_meter_host/relay_wire.c/.h|Pythonと同一X1構文・長さ・CRC-32検証|
|同relay_host.c/.h|実USBから独立したHost engine。起動/session/request照合、二重実行拒否、応答境界、期限管理|
|同relay_main.c|実TinyUSB CDC/UARTの非blocking adapter。8枠出力Queue、USB設定完了確認、送信callback管理|
|同CMakeLists.txt/README/build_manifest.json|独立中継ターゲット追加、3成果物hash/版/試験・未配置状態を記録|
|tests/test_external_instrument_link.py|実Cをnative DLLへリンクし、FixtureAppを含む往復/異常/期限/復帰の25件|
|tests/test_external_instrument_pio.py|公式asm_pioによる組立て、PIO FIFO/IRQリングの7件|

関連ATE/Module/Test/Plan/Open Issues/CHANGELOGも同期更新する。既存QR FW、.5の電圧評価ソース、NF55Gフレーム/Retry/Cache規則、元資料は変更していない。既存6ビルド成果物のhashも保持されている。

## 接続照合・復帰の実装詳細

HELLOはH、request/mode/timeout=0、空payload、親nonce8byte+0の8byte。応答hは同じ親nonce+Host起動nonceを持ち、ASCII payloadをchipid16HEX|FW版|状態とする。状態はREADY/NOT_READY/BUSY/FAULT。親は実個体BFCF2EDB84B0B37Fとmeter-host-relay-版を確認する。HostはREADY時に親起動nonceへbindし、同一bootで別親nonceへ黙って切り替えない。Qのrequestは単調増加で、重複/逆行はUSBへ再実行しない。

親nonceはos.urandom(8)、Hostは固定SDKのget_rand_64を使用。ゼロnonceを有効接続にしない。承認時に残していたFW版/ID表現とAPI選定を、この実装と相互運用テストで具体化した。これは製品FWの設計回答を推測したものではない。

HostのA=受付、T=CDC全送信完了、R=CRLFまでの完成原文、E=理由|曖昧flag（0/1）。親はsession/request/mode/forwardしたtimeoutも照合する。CRC異常は実行/採用せず、期限切れで失敗にする。親の待ち期限はATE受付からで、送信済みUSB操作の取消成功までは保証しない。開始後timeout等は成否不明として扱う。

timeout・切断・未要求データ・親再起動等は故障状態を保持する。quiet時間だけで旧応答を排除したとは扱わず、自動再送/自動再設定/自動再測定をしない。復帰には進行中処理がなく計測器内の旧出力も排除されたことを確認し、親・Hostと計測器の状態を運用手順で揃える必要がある。Hostだけの再起動が計測器内の遅着を排除するとは保証しない。自動復帰の実機受入は未完了でありOpen追跡する。

## USB送信の実装確認

固定SDKのcdc_host.cではTX成功callbackへ転送長が渡らず、ZLPにも同callbackを使用する。次のデータ転送完了との混同を防ぐため、USB送信を最大63byteの奇数長へ分割し、各完了callbackを待って次を投入する。1～194byteの全長で正確なbyte合計と8/16/32/64のpacket sizeの倍数を避ける分割を実Cで検証した。部分write/想定外flushは失敗にし再送しない。制御転送は接続epochを照合して旧callbackを採用しない。実機USB転送・負荷Timingの確認は別途必要。

## 検証結果

- [最終Host Unit/Mock NF55Gログ](Host_Mock_Verified_Rev0.log): **446件成功、2.632秒**。追加32件を含む。
- 実CとPython codecの相互一致、全USB応答2分割境界、192byte本文、原文返却、CRC破損、期限境界/clock wrap、部分UART、二重要求、再起動、未要求/過長応答、FU禁止、TEST_START/ENDのBUSY拒否、ATE応答順序、無効時の非初期化を確認。
- [最終ARMビルドログ](Build_Verified_Rev0.log): meter-host-relay-20261120.1を固定SDK2.2.0でbuild/link成功（-Wall -Wextra -Werror）。[UF2 metadata](UF2_Info_Verified_Rev0.log)で版・RP2350 ARM Secure・GP0/1とGP12/13・SDKを確認。
- [PIO検証の出所](Validation_Provenance.json): 記録済み実機MicroPython v1.27.0と同じ公式asm_pioをHost上で実行。TX4命令+RX12命令=16命令。PIO1の32命令内に収まることを確認。hardware classはstubであり、実IRQ負荷/信号波形/実機上の実行を証明するものではない。
- 全変更追跡ファイルの空白検査と追加ファイル/リンク/hash検査を実施。既存別ファイルSplit_Host_Architectureの末尾空白は今回変更せず保持する。

公式参照: [v1.27.0 asm_pio原典](https://raw.githubusercontent.com/micropython/micropython/v1.27.0/ports/rp2/modules/rp2.py)、[StateMachine API](https://docs.micropython.org/en/v1.27.0/library/rp2.StateMachine.html)、[os.urandom](https://docs.micropython.org/en/v1.27.0/library/os.html)、[CRC-32 API](https://docs.micropython.org/en/v1.27.0/library/binascii.html)。原典の実行に使ったコピーとMIT noticeを本フォルダへ保持する。

## 実機確認用パッケージ

[配置用manifest](Deployment_Package/manifest.json)のParent/main.py+src一式とHost UF2を用意した。**未配置**。Parent/configのコピーだけEXTERNAL_INSTRUMENT_ENABLED=Trueとし、他の親設定・ソースは現作業版と同一でhashを記録した。親のruntime一式を同時配置し、新main.pyだけを旧srcへ混在させない。元src/config.pyはFalseのまま。

Host UF2は 94208 byte、SHA-256=2f6faee45dbbad016fe8470128e7cce9cb1c6e05980d053d4d83880b24a3906c。既存.5は自動電圧試験版で、中継用ではない。先に新Host UF2へ置換し、親子の接続確認後に電源を投入する。

次の実作業は[実機受入手順](Acceptance_Procedure_Rev0.md)に従う。現物端子・RESET・共用電源の電気条件、実UART波形/IRQ/Timing、USB-A経由の実中継、機器内旧応答を含む復帰は未確認。USB-SUB-01/05・USB-INT-01はOpen維持。レンジ相違USB-CDC-RANGE-01は保留し、中継の合否と分ける。
