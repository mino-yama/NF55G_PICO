# L-46X接続時のD2消灯：ソース解析（2026-10-02）

## 結論
主原因候補は「L-46XのHID Report Descriptor取得・解析が成立せず、Keyboard Usageが設定されない」こと。キーボード先行接続による回復は、前機器のUsage情報が残る処理で説明できる。公開ソース上のエラー無視・情報未初期化は確認できたが、実機FW同一性とReport転送の失敗理由は未確定。D2点灯のみを正常な初期化の証明にしない。

## 対象と出所
- ユーザー提供CH559sdccUSBHost-master.zip。原本は変更せず、直下のC/H/READMEだけreference/local_hardware_reference_20260904/required_for_development/CH559_analysis_20261002へ抽出。
- 比較対象は以前取得したq61org/CH559_EasyUSBHostのmain。比較用コピーを同フォルダeasyusb_comparisonへ保全。コミット未記録のため、実機版や現在の最新版とは断定しない。ZIPと各保存ファイルのSHA256はmanifest.json。
- 2026-09-26の実機TX0ログはdocs/L46X_USB_Recognition_Investigation.mdとReal_Hardware_Test_Log.mdを参照。本日は新たな実機試験をしていない。

## 確認したソース上の事実
### 添付ZIPと基板用コードの相違
添付main.c:15はLED=P1.6、21はUART0=1000000bps。基板用比較ソースmain.c:139はP3.1をLowにする検出出力、501以降はg_numKbds>0の変化で出力を更新する。実機は230400bpsでCALLBACK付きログを出している。従って添付ZIP単独のLED処理をかんたんUSBホストのD2へ直接当てはめられない。添付バイナリへの置換も行わない。

### 共通のHID取得エラー無視
添付USBHost.c:718～747はSET_IDLE後にGET_DESCRIPTOR(REPORT)を実行。取得エラー時は737～738でreturnし、parseHIDDeviceReportへ進まない。呼出元877は戻り値を評価しない。
比較版udev_hid.c:130～159も同様。236～241のhiddevice_init_endpointは戻り値を無視して0を返す。SET_IDLEの結果も両版で継続可否に使っていない。

### D2登録条件と前機器情報の残留
比較版main.c:188以降はiface.usage == Usage_KEYBOARDだけを確認してg_numKbdsを増やす。USBHost.c:690以降のinterface再設定ではinterface/class/subclass/endpoint等を更新する一方、usageの初期化がない。切断処理795付近もconnectedの解除とcallbackで、usageをクリアしない。udev_hid.c:64～67でReport解析時にusageを設定するため、Report取得が失敗すると以前のusageを保持する経路がある。
これは新機器として再登録する際の内部情報残留であり、D2が単に消えず残っているという説明とは異なる。

### Report要求長
両版ともReport長をHID descriptorの宣言値から取得せず、512byteを要求する。比較版USBHost.c:316～331では残量が0またはshort packetになるまで読む。これ自体だけで不適合や原因とは断定できない。実Report長、受信パケット列、結果コードを確認する必要がある。例えば実長がEP0最大64byteの整数倍で、終端の0byte応答が得られなければ追加IN待ちになる可能性があるが、L-46Xの実長や当該挙動は未観測。

## 実測との照合
|条件|Report解析ログ|Keyboard登録ログ|D2|
|---|---|---|---|
|L-46X直接再接続|観測なし|観測なし|消灯|
|Dell KB216接続|Usage Keyboardと解析内容あり|1 keyboard(s)|点灯|
|Dell取り外し後L-46X|観測なし|1 keyboard(s)|点灯|

L-46XのVID/PIDは065a/a001、EP0最大64byte、HID Class3/Subclass1/Protocol1。機器名・configuration・interface取得までは両条件とも進んでいる。Report要求からattachまで約293～294ms。キーボード経由の状態ではQR読取に対応するKeyEvtも取得済み。
ログ不在だけでReport処理の未実施とは断定しない。ソースで示された失敗時の分岐と、前機器に依存する登録結果を合わせるとUsage残留が有力な説明となる。約294msだけでタイムアウトとも断定できない。

## 未確認事項と次の確証
1. 実機に書かれたFWの版・ソースとの一致。
2. SET_IDLEとGET_DESCRIPTOR(REPORT)それぞれの戻り値、受信長、最終受信パケット長、失敗したSETUP/DATA/STATUS段階。
3. HID descriptorのReport宣言長と実際のバイト列。512byte要求との差。
4. 接続直前/直後のiface.usageとReport取得後の値。

メーカーへの確認または実機と一致するFWへの診断追加では、上記をログ化する。先にReport転送の失敗原因を確定し、SET_IDLE拒否、GET_REPORT_DESCRIPTOR失敗、正常だが空/非対応Reportなどを分ける。

## 修正方針候補（未適用）
- 機器スロット再利用前にinterface情報を初期化し、取得失敗を呼出元まで伝える。
- 今回の機器で取得・検証できた情報だけを登録に使う。
- HID descriptorのReport長を保存し、バッファ上限と合わせて適切な長さを要求する。
- Report解析の境界チェックと、対応する入力形式の確認を行う。
Usage初期化だけではL-46Xの取得失敗を直せず、キーボード経由の偶然の回復もなくなる可能性がある。Protocol1を見て強制登録するだけの対策は、未確認のReport形式を処理するため採用しない。

## 検証範囲
ソース静的解析と既存実機ログ比較を実施。ZIP内のexe/bat/バイナリは実行せず、FW書込み・製品通信・Picoコード変更なし。Host Unit/Mock試験はコード無変更のため再実行なし。修正時は制御転送失敗、空Report、正常Keyboard、切断/別機器再接続、長さ境界の試験と、両接続順での実機検証を行う。未確定事項は既存OI-23の継続調査でありCloseしない。
