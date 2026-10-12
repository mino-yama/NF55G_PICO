# L-46X USB認識の調査

## 実測とユーザー報告
- 通常USBキーボード: D2点灯、ABC+LFのPico受信成功。
- L-46X: 一度35文字+LFをPicoで受信成功。その後電源再投入でD2消灯。
- 電源投入時トリガ10秒以上長押しは強制起動。メーカー作成第5版p.22によれば、この状態では読取データをホストへ出力しない。
- 今回、通常起動でもD2が点灯しないとのユーザー報告。PCへの一時直結は現在不可。

## 公開FWで確認したこと
参照: https://github.com/q61org/CH559_EasyUSBHost （取得時main、実機FWとの同一性は未確認）。取得コピーはtmp/qr_usb_research。
- udev_hid.cのgetHIDDeviceReportはSET_IDLEとReport Descriptor取得を行う。parseHIDDeviceReportが最初のUsageを保持する。
- main.cのusbAttachCallbackはUsage_KEYBOARDを満たすinterfaceをキーボードとして登録する。g_numKbds > 0でP3.1の検出出力を有効にする。
- 従ってD2消灯だけでは、USB列挙失敗とHID descriptor取得/解釈失敗を区別できない。PCでExcelに入力できることも、この簡易ホストでの初期化成功までは保証しない。
- Boot protocol限定という原因はこのコードからは確定できない。UART速度9600やEnter変更で認識を直せるという根拠もない。
- 過去に同じ経路で受信成功しているため、固定的な非対応と決めず、起動順/電源立上り/初期化の再現性を比較する。

## 次の比較試験
リーダのトリガを押さず、ホスト単独で起動後にリーダUSBを接続する。D2を確認し、接続済み一括電源投入の場合と比較する。設定変更やFW書換えは行わない。
改善しない場合はPC接続可能になった時点でVID/PID・interface/HID descriptorを取得するか、実機ホストFWを確認した上でメーカーの初期化診断ログの取得方法を検討する。原因は未確定。

強制起動の出典（メーカー作成資料の販売店掲載版）:
https://www.j-itecs.co.jp/wp/wp-content/uploads/2020/11/6dfa8720842f8ee09b40c16ba5909b4c.pdf

## キーボード経由での認識回復（ユーザー報告）
キーボードを接続した後、キーボードを外してQRリーダに差し替えるとD2が点灯する。
これはキーボード認識を先行させた接続履歴に依存する回復条件の候補。ホスト内の状態、経過時間、USBリーダへの給電再投入等が同時に変わるため、ホストFWの不具合や特定の初期化不足と断定しない。
キーボードを外した後にD2が消灯し、L-46X接続後に再点灯するかは未確認。D2の前機器表示残りと、新機器認識を区別する。通常起動のL-46Xで再度35文字+LF受信できれば、実データ通信の回復も確認できる。
キーボード経由の操作は切分け手順であり、量産の起動手順や恒久対策には採用しない。根本原因と電源再投入後の再現性はOpenのまま。

## D2消灯・再点灯の確認（ユーザー追報）
キーボードを抜くとD2が一度消灯し、L-46Xを挿すと再点灯することをユーザーが確認。
前機器の認識表示が残っただけという説明は当該操作について除外できる。キーボード認識後のホストではL-46Xへの差し替えで新たな認識表示が成立する。
電源投入直後との違いがホスト内部状態、USB初期化タイミング、給電立上りのどれかは未確定。今回の認識回復状態での実データ再受信はまだ別途確認が必要。

## L-46X単体の抜き差しでは回復しない（ユーザー確認）
提案した比較手順（キーボードなしで通常電源投入→L-46Xだけを抜き差し）について、ユーザーがD2点灯しないと報告。
観測の整理: L-46X直接起動=認識表示なし、L-46X単体再接続=認識表示なし、キーボード認識→取り外しでD2消灯→L-46X接続=D2再点灯。
単なるL-46Xの再接続だけでは回復しない。キーボードを認識させる操作に関連したホスト状態/初期化経路を優先調査する。ただし試行回数、待ち時間、電源波形を揃えた反復比較は未実施であり、特定FW不具合と断定しない。
次の確証はホストのUSB初期化ログを失敗条件と成功条件で比較すること。公開FWと実機FWの同一性、診断出力の有効性と端子を確認してから取得方法を決める。診断のためのFW書換えや追加配線は未実施。

## HOST TX0診断受信（2026-09-26）
ユーザーがHOST TX0→Pico GP10（物理14番）の追加接続を完了。GND共通、TX1→GP9、RX1←GP8は維持。
scripts/pico_usb_host_debug.pyは専用診断としてPIO0/SM1で230400bps/8N1を受信し、16384byteリングからCOM14へ時刻差と生バイトreprを出力する。公開FWのUART0設定が根拠で、実機FWの診断有効性は未確認。受信異常/overflowはLOSSとして明示し、不完全なログと扱う。既存QR受信の既定値は変更なし。
本診断中は量産runtime/QR試験を停止し、ATEコマンドは処理しない。SS/FU送信、SD書込み、HOST設定変更はしない。Picoの電源を維持してL-46X抜き差し→キーボード認識→取り外し→L-46X接続を記録する。Picoごと電源断すると診断も停止するので再起動が必要。自動起動は変更しない。
参照資料としてローカルのL-46X第6版PDFの存在を確認。以前の第5版に基づく説明は第6版での照合待ち。

2026-09-26 HOST TX0診断: Host/Mock全161件合格、git diff --check合格（既存ファイルの改行警告のみ）。COM14への転送は接続不可で未完了。serial.tools.list_portsではCOM10のみ列挙、COM14は認識されていない。診断受信開始・230400bps実受信・ログ比較は未実施。Pico USB再接続後に転送から再開する。

2026-09-26 再接続後: COM14（USB VID:PID=2E8A:0005）を確認。qr_pio_rx.pyとpico_usb_host_debug.pyをPicoへ転送し、HOST_DEBUG READY GP10 physical14 230400 8N1 PIO0/SM1を実機で確認。診断受信待機を開始。開始時点ではHOST_TX0の受信出力なし。HOST実機の診断出力有効性とUSB認識失敗原因は未確認。専用診断中はATE QR_SCANを処理しない。

## 2026-09-26 TX0実測: L-46X再接続でD2消灯
GP10/230400bpsで実際の診断出力を取得。ユーザーは再接続後D2消灯と報告。
以下はCOM14の分割受信を連結した抜粋（受信開始から約84秒）。HOST_DEBUG LOSS表示なし。ただしUART全バイトの完全性は独立検証していない。
```text
Device at root hub 1 connected
initializing device at root hub port 1
Device class 0
Max packet size 64
VID/PID: 065a/a001
SetAddress: 16
Manufacturer String: Opticon
Model String: Opticon USB Barcode Reader
config total length: 0x0022
Configuration value: 1
Interface count: 1
Interface descriptor found
Interface 0
  Class 3
  Sub Class 1
  Interface Protocol 1
  Alternate Setting 0
  Endpoint Count 1
HID descriptor found
HID at Interface 0
  USB 1.11
  Country code 0x00
  TypeX 0x22
Endpoint descriptor found
Requesting report from interface 0
CALLBACK: dev[0] @16, is_attach=1
```
機器情報・HID interface取得までは進行。Report要求後にUsage等の解析出力およびkeyboard connected出力が観測されない。取得済み公開udev_hid.cはReport転送エラー時に解析前returnするためReport取得/解析段階を優先調査。ただし実機FW同一性・転送結果コード・受信長は不明で、エラー原因は断定しない。
次はPico/HOSTを通電したままキーボード接続→D2確認→取り外し→L-46X接続の比較ログを取得する。QR/SS試験は行わない。

## 2026-09-26 キーボード経由の比較ログ
ユーザー操作: L-46Xを外す→キーボードD2点灯→外す→L-46X再接続でD2点灯。COM14 TX0診断にも対応する接続/切断を確認（LOSS表示なし）。
- 約221秒: Dell KB216 Wired Keyboard、VID/PID 413c/2113、EP0最大8byte、interface 2個。Report要求後にUsage Keyboardとreport解析内容が出力され、CALLBACK: 1 keyboard(s) now connected。
- 約228秒: disconnect, 0 keyboard(s) now connected。
- 約232秒: Opticon USB Barcode Reader、065a/a001、EP0最大64byte、interface 1個。Requesting report from interface 0から約294ms後にattach callback。Usage/Report解析ログは今回もないがCALLBACK: 1 keyboard(s) now connectedが出力された。
- 先のD2消灯時もReport要求→attachが約293msで、解析ログなし。違いはkeyboard登録の有無。
取得済み公開コードとの照合: udev_hid.cのhiddevice_init_endpointはgetHIDDeviceReportの戻り値を無視する。Report取得エラーは解析前return。USBHost.cの確認した切断/再登録経路はiface usageをクリアしておらず、main.cの登録判定はiface.usage == Usage_KEYBOARD。従って前のキーボードのUsageが残り、Report取得が正常化しなくても登録される仮説が今回の差を説明する。実機FW同一性・実際のReport転送結果/長さ未確認のため原因確定ではない。
従前の「単なるD2表示残留ではない」は維持するが、新規登録の根拠に前機器の内部情報が残留する可能性は別問題として追加。D2点灯を完全なHID初期化成功とは扱わない。
次に専用診断を継続したままQRを1回読み、TX0のKeyEvt等を確認する。これはキー入力経路の診断であり、QR Cache/35文字受信の再試験ではない。HOST設定/FWは変更しない。

## 2026-09-26 QR読取時のTX0キーイベント確認
ユーザーがキーボード経由でD2点灯したL-46XでQRを1回読取。COM14で受信開始後473064～473158msに@16 KeyEvtのDown/Upを連続観測。冒頭D02,D18,U02/U18、続いてD02,D16等、末尾D1e,U1e,D28,U28。HOST_DEBUG LOSS表示なし。
これにより現在の接続状態ではL-46Xの読取に対応した入力をHOSTがキーイベントへ変換していることを確認。D2表示だけの確認から進展した。ただし今回の診断はTX0のみで、TX1の35文字本文・QR Cache・ATE応答は監視していない。今回の結果をQR受信試験全体の合格や電源再投入後の認識改善とは扱わない。
Report解析ログが無いのにキーボード経由で登録/入力処理できるという観測は、前機器Usage残留の仮説と整合するが、実機FW一致とReport取得失敗理由は未確定。恒久対策は未実施。診断受信は継続中。
