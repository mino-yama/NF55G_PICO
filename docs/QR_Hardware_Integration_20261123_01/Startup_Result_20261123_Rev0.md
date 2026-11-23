# QR起動・列挙切り分け Rev.0

2026-11-23。ユーザーがスキャナー接続先をQR用HOSTのType_C2（制御側と反対の遠い端子）と確認し、読取り音ありと申告。親GP9で180秒の受動採取を開始してから、QR用HOSTだけのRSTと読取りを依頼し、実施回答を受けた。

## 実測結果

Run_03は180.041秒・28,798byteを採取。親RAM計算SHA-256とPC回収が一致：`912b387d5c64fd691aa6ccb46845061dfece2fb94364bc84ece745201ddf77dc`。受信faultなし、終端断片なし。採取終了時はQR SM0／測定器SM4/5停止、GP9/12/13入力化。NF55G送信なし、FW書込みなし。

採取中に意図したRSTを含むため、単一起動前提の`result.json`は連番再開をCAPTURE_ERRORSとして記録した。原文を保持し、`inspect_startup.py`でboot seq=0の明示境界だけを分割して再解析した。通常の連番欠落を無視する処理にはしていない。

|区間|観測|
|---|---|
|RST前|29件のheartbeat。drop=0、最終reports=1940、texts=0、flags=13。今回の採取開始時点ではQRプロファイル有効。前回Run_02終了後から今回開始前までの認識経緯は未採取であり、RSTだけで改善したとは断定しない。|
|RST後|158件、seq=0から連続。boot=`qr-fixed-20261114.1`、board_id=`A06FEA01012EC137`で期待値と一致。phase1～4を観測、起動3606msでHID mount、63byte descriptorとVID/PID E851:1001を記録。最終drop=0／reports=388／texts=0／flags=13。|
|文字復元|起動58102ms、seq64の`qr_decode_error`、値07。ソースの`QR_ALT_CHARACTER`（許可外文字）に対応。完成QR原文kind12は0件。|

個体／版の文字列は一致しているが、現在の`identity_verified`はエラーなし条件も含むためfalse。エラーを取り除いて受入済み扱いしない。

## 判断・次段階

USB列挙とHID入力の受信を確認。35文字原文・6項目分解の実機成功は未確認。現FWは英数字・ハイフン35文字のAlt数値入力復元に限定しており、許可外の値が何だったかはcontinuous版のログに記録されていない。読んだQR原文／種類の確認待ち。原文を得る前に文字制約やデコーダを緩和しない。正式ATE／Cache／SS連携と既存Open Issueは継続。

## 診断変更・検証

採取時間を30～180秒で指定できるようにし、実行プログラムをrun別に保存。boot境界別の解析を追加。明示bootのみ分割し、区間内の連番欠落を引き続き拒否するテストを追加。QR関連14件成功、全Host Unit／Mock **512件成功（11.981秒）**。

- [採取原文](Run_03/qr_host.raw)
- [起動世代別の解析](Run_03/startup_segments.json)
- [親採取ログ](Run_03/parent.log)
- [全体回帰ログ](Startup_Host_Mock_Rev0.log)
