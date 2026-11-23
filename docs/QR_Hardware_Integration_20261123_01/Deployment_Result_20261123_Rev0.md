# QR修正版 実機書込み結果 Rev.0

2026-11-23。ユーザーの「書込みテスト進めて」指示と、QR用HOSTをPC単独給電でBOOTSEL接続済みとの回答後に実施。

## 書込み・照合済み

対象ID `A06FEA01012EC137`／RP2350／Flash 2048K／BOOTSELを照合。旧版`qr-fixed-20261114.1`の全Flash 2,097,152byteを退避し、save -a -vに加えて独立verifyを実施。SHA-256 `214d4db5a5af3d3e21dd0f735666bfceca3707bb3d73f43f3ae935313a7c4faa`。

配布manifestの50ファイルを全hash照合後、UF2 84,480byte／SHA-256 `cadff2460cc7b1be3ca8c8882c4b120569178371d3092c1182c66eb01bae2b3e`を対象ID指定でload -v。さらに独立verify成功。書込み後infoでも同一IDと新版`qr-fixed-20261123.1`を確認。終了コードは全工程0。書込み後はBOOTSELを保持し、親／測定器HOSTへFW変更なし。

- [書込み結果JSON](Deployment_01/result.json)
- [全Flash退避](Deployment_01/before_flash_2MB.bin)
- [退避hash](Deployment_01/backup_hash.txt)
- [load -v](Deployment_01/load_verified.log)
- [独立verify](Deployment_01/independent_verify.log)
- [書込み後info](Deployment_01/after_info.log)

## 読取り試験の準備

Run_04は親で64KiB採取バッファの再確保時にMemoryErrorとなり、待受開始前に停止。受信ドライバ構築後の確保だったため、その診断PIOを明示close・GP9入力化して復旧した。失敗ログは[Run_04](Run_04/parent.log)に保持。

前回のRAM原文はPCにhash照合済みで保存されているため、親のqr_rawを解放。採取バッファを再利用し、PIO構築前にバッファ確保するよう診断プログラムを変更。後処理後SM0=false、空きRAM 274,576byte、保持採取バッファ65,536byteを確認。

Run_05は180秒・期待原文`US250A-CGXE-009491-101A1.2601000001`を指定して開始し、QR_CAPTURE_READYを確認後、ユーザーへ無給電での固定配線復帰・給電・2～3回読取りを依頼。修正後実読取りの結果は採取終了後に別記する。書込み成功だけでQR読取り成功としない。

## 配線復帰後の経過

ユーザーから固定配線復帰・同原文読取りの完了回答を受領。Run_05は180.001秒、受信0byte、faultなし。配線復帰の実時刻との関係を確定できないため、復帰申告後にRun_06（60秒）を新規採取し、再読取りの回答も得たが、こちらも0byte／faultなしだった。

Run_05／06とも空データのSHAが一致しただけであり、QR成功・HOST停止・配線不良の証明にはしない。heartbeatもないため、QR文字復元より前のHOST→親UART経路・HOST起動の確認が必要。Run_07（120秒）を開始し、GP0→親GP9／共通GNDの復帰確認とQR用HOSTだけのRST、同原文1回の読取りを依頼。

新FWのビルド定義はPROBE_CONTINUOUS=1／PROBE_UART_TX_PIN=0／版qr-fixed-20261123.1を再確認済み。実機起動確認とは区別する。

- [Run_05結果](Run_05/result.json)
- [Run_06結果](Run_06/result.json)
