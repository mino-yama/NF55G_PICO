# QR修正版 書込み・読取り試験結果 Rev.0

2026-11-23。今回の限定目標である、QR用HOST修正版の書込みと、親GP9経由の実原文受信・分解を確認した。

## 確認できた事実

|項目|結果|
|---|---|
|対象|QR用RP2350-USB-C、ID A06FEA01012EC137|
|配置FW|qr-fixed-20261123.1、SDK2.2.0 ARM Secure|
|書込み|旧Flash2MB退避・独立verify、新UF2 load -v／独立verify／版照合成功|
|起動|Run_07でboot seq0・同一個体ID・新版FWの一致、phase1～4を確認|
|USB|RST後3606msでHID mount、63byte descriptor、VID/PID E851:1001|
|QR原文|`US250A-CGXE-009491-101A1.2601000001`を5件受信、全件が期待原文35文字と完全一致|
|分解|型式US250A-C／品目GXE-009491-101／REV A1.／YY26／WW01／号機000001|
|通信品質|85レコードseq0～84連続、解析エラー0、UART faultなし、全heartbeat drop0、最後のtexts=5／reports=1940／flags=13|
|回収|120.008秒、13,090byte。親計算とPCの長さ／SHA一致|
|終了時|親QR SM0／測定器SM4/5停止、GP9/12/13入力化。QR HOSTは新FWの固定接続運転状態|
|回帰|全Host Unit／Mock 516件成功、35.051秒|

Run_07 raw SHA-256：`f04faf8031dc557447004f7a2da62f37b40d4fc43070a15217c6226494f3d0ff`。

## 途中結果と限界

配線復帰後のRun_05／06は受信0byteだった。配線確認とQR用HOST RSTの依頼後、Run_07で起動からの受信と5件一致に成功。0byteだった原因は未特定で、電源投入だけで常に認識することやRST不要を保証しない。今回の新FWの実績はRST後の読取りである。

同一原文の5件受信は確認したが、読取りトリガーとの一対一対応や重複抑止の正式仕様は未確定。正常サンプル10種類すべての実機読取りを行ったとは扱わない。

受信・文字復元の限定確認であり、正式ATE Cache／SS連携、製品PASS判定、量産受入ではない。診断JSONのhardware_acceptance=falseはこの区別のため維持。NF55G／SSへの送信なし。製造年週を銘板DATEの月へ変換せず、REVの3→4文字変換も確定しない。

## 証跡

- [書込みと全Flash退避の記録](Deployment_Result_20261123_Rev0.md)
- [Run_07解析・5件原文・6項目](Run_07/result.json)
- [受信原文](Run_07/qr_host.raw)
- [親採取ログ](Run_07/parent.log)
- [最終回帰ログ](Revision_Period_Final_Host_Mock_Rev0.log)
- [修正仕様](Revision_Period_Spec_20261123_Rev0.md)
- [実原文を基にした正常サンプル10件](Samples_Rev1/normal_samples.txt)
