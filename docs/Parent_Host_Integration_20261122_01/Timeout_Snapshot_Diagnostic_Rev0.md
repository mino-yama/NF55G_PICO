# CDC TIMEOUT受信状態の診断 2026-11-22 Rev.0

## 現在の停止点

Host実機はmeter-host-relay-20261122.1 / BFCF2EDB84B0B37F。TIMEOUT後のfaultを保持。親は書込み準備のためruntime停止・外部PIO SM4/5停止・外部端子入力化、外部fault保持・Logger停止/drop0/Queue0・NF55G IDLE。親nonce AEBFF8CD13A17FFE、最後のHost nonce4453B52BC1280AE0。COM6/7/22は解放済み。新しい機器要求は出していない。

候補.22.2はnative全465件成功、ARMビルド成功、ELFのCDC callback wrapperとsnapshot文字列・UF2 metadata/SHA照合済み、未配置。主目的は受信途中状態の観測であり、根本原因の修正済みとは扱わない。

## 実機結果

- 新Host .22.1起動後のIDN一致と50回共存成功。[結果](NF_Coexist_03/result.json)、[SD照合](NF_Coexist_03/File_Export/verification.json)。CSV55,879 byte/853行、D1 50件、NF RAW200件、drop0、Queue0、外部faultなし。Host A/T/Rは各50、単一session。
- 500回への拡張・期限2000ms: 116回成功後117回目でTIMEOUT。Host request168、A=PC観測100.016秒、T=100.454秒、E=102.016秒、E原文TIMEOUT|1。Rなし。D1 Retry0、SD/RTC正常、drop0。[結果](NF_Coexist_04_Long/result.json)、[Host時刻](NF_Coexist_04_Long/host_frames.json)、[CSV照合](NF_Coexist_04_Long/File_Export/verification.json)。CSV130,367 byte/1992行、D1 117件、NF RAW468件。
- Host RST後、新nonce4453B52BC1280AE0・READY3回を確認。親再起動なし。新Host bootへQ未送信の段階で、新Host nonce変更/READY/親要求なし/Logger停止をassertしたRAMアダプタ再初期化を行った。[保守試験helper](rebind_after_new_host_nonce.py)。量産APIや自動fault解除の実装ではない。
- [設定原文](Read_Deadline_State_01/result.json): IDN ADC Corp.,7355,246410099, A02、INIT:CONT=0、TRIG:SOUR=IMM、TRIG:COUN=00001、SAMP:COUN=00001、TRIG:DEL=+0.0000E+00、SENS:FUNC=VOLT:DC、SYST:ERR=+0,No error。設定書込みなし。エラーqueueは1回読んだ原文を保存し、自動clearしていない。
- 期限10000msの別試験: 72回成功後73回目でTIMEOUT、USB転送失敗の通知なし。2秒期限だけを延ばせば解消する現象ではない。[結果](NF_Coexist_05_10s/result.json)、[Host時刻](NF_Coexist_05_10s/host_frames.json)、[CSV照合](NF_Coexist_05_10s/File_Export/verification.json)。CSV81,877 byte/1244行、D1 73件、NF RAW292件、drop0、Queue0。すべて自動再送なし、異常で停止。
- PCでのHost frame受信時刻はUSB-UARTのbuffering/coalescingを含む。T/RのPC時刻差0はMCUイベント同時や機器応答0msを示さない。[制限込みの集計](NF_Coexist_03/timing_summary.json)。

## .22.2の診断追加

HostのTIMEOUT理由を TIMEOUT_RX<n>_T<t>_C<c>_X<tail> として記録する。n=保持RX byte数、t=USB全送信完了、c=CRLF応答完成、tail=保持RX末尾最大4byteのHEX（受信なしはNONE）。例: TIMEOUT_RX0_T1_C0_XNONE。既存Eの理由|ambiguous枠を使用し、frame種別/上限/CRC/session/requestは変えない。

部分応答を完成RやVALID Cacheへ昇格させない。fault保持・再送禁止・実行成否不明は維持する。親期限が先に切れる場合はATEには従来TIMEOUTが返り、Hostの詳細Eがstaleとして破棄される場合があるため、COM22原記録も判定に使う。

実C試験では無受信、部分2byte、CR終端のみ、応答完成済みだがTX callback未完了の4条件を区別し、ambiguous/fault保持を検証。全465件成功、12.694秒。[試験summary](Timeout_Snapshot_Unit_Summary.json)。前段の464件は[全出力](Transfer_Guard_All_Unit.log)を保存済み。今回の465件全出力はファイルへredirectしていないためsummaryのみを保存した。

## 上流調査（未適用・本件原因と未同定）

原典の一括更新はしていない。以下は公式upstreamでの別条件の報告であり、今回の原因の証明ではない。

- [PR207](https://github.com/sekigon-gonnoc/Pico-PIO-USB/pull/207): CRC16 routineのRAM配置修正が2026-07-14にmergeされた。報告の再現条件はflashアクセスを制約する環境でのmulti-packet OUTであり、そのまま本構成へ当てはめない。
- [PR210](https://github.com/sekigon-gonnoc/Pico-PIO-USB/pull/210): 受信loopの絶対期限と切詰めpacketのACK抑止を提案。閲覧時Open。本件でそのloop停止やmemory破壊を確認したものではない。
- [PR211](https://github.com/sekigon-gonnoc/Pico-PIO-USB/pull/211): RP2350構成で1bit framingずれと受信停止を報告し、CRCを検証する修復案を提案。閲覧時Open、maintainerは受信経路自体の改善を希望とコメント。本件のCRC/framingずれは未観測。

## 次工程

ARM build/link/UF2 metadata・snapshot動作を確認して候補を固定し、親通信停止・PIO入力化、Host単独BOOTSEL、現行全Flash退避/verify、候補配置/verify、配線/給電復元、H/IDN、同条件再現へ進む。実機から保持RX長/末尾が取得できるまで、無応答・途中受信・受信待ち停止のいずれかを推測で確定しない。

量産自動復旧/監視/WDT/管理API・旧機器応答境界・QR共存・測定Cache接続の未確定/未受入はOpen継続。機器RESET/SCPI初期化・NF55G設定書込み・FUは本工程へ追加していない。

## .22.2 候補固定

UF2 95,232 byte、SHA256 `ebbb7f99e09524a7cd89cb5ac7fb44c70d1be931358b8141a2135c888410c847`。[候補manifest](Timeout_Snapshot_Candidate/manifest.json)、[ARM build](Timeout_Snapshot_Build_Native.log)。親RUNNING=False、SM4=False、SM5=False、Logger=Falseを実機照合後、Host単独BOOTSEL準備を依頼。実機版はまだ.22.1であり、候補を実機検証済みとは扱わない。

## .22.2 候補固定

UF2 95,232 byte、SHA256 `ebbb7f99e09524a7cd89cb5ac7fb44c70d1be931358b8141a2135c888410c847`。[候補manifest](Timeout_Snapshot_Candidate/manifest.json)、[ARM build](Timeout_Snapshot_Build_Native.log)。親RUNNING=False、SM4=False、SM5=False、Logger=Falseを実機照合後、Host単独BOOTSEL準備を依頼。実機版はまだ.22.1であり、候補を実機検証済みとは扱わない。

## .22.2 書込み完了

対象serialと旧版.22.1を照合し、全Flash 2MBをsave/verify後に候補UF2をload/verify。metadataは.22.2一致。現在BOOTSELで通常配線復元待ち、実行時検証は未実施。[書込み記録](Timeout_Snapshot_Deployment_01/manifest.json)。旧Flash SHA256 `a2fdc8874880b58220241a30306da9fb9490479aec648be3d89fb718fb0bdc22`。

## .22.2 実機初回結果

通常配線復元後のH 30回は応答0、親frame error0。Host RST後はnonce `E47063DECF50313F`、.22.2/READYを3回照合、PIO errorなし。親nonceは同じ。親RAMの外部linkだけを再構築し、SD/NF55G/Logger appを維持した。最初の明示IDNはA/T/E、E=`TIMEOUT_RX0_T1_C0_XNONE|1`、Rなし。ATEはローカル期限で先にTIMEOUT/AMBIGUOUS=1。機器に同一bootで再送していない。[IDN記録](timeout_snapshot_confirmed_idn/result.json)、[生Host出力](timeout_snapshot_confirmed_idn/host.raw)。Logger停止/drop0/Queue0、既存CSVは81,877 byte/1,244行でSHA一致。新たなREAD連続試験は未開始。原因は未確定。次は下位USB INのNAK/受信PIDとendpoint状態を観測し、受信未投入と転送待ちを区別する。
