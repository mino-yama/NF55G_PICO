# USB IN下位層の観測 2026-11-22 Rev.0

## 確認済み

.22.2は対象Hostへ全Flash退避・書込み照合済み。通常配線復元後のH 30回は応答なし、RST後は新nonce `E47063DECF50313F`でREADYを3回照合できた。最初のIDN要求は `TIMEOUT_RX0_T1_C0_XNONE|1`。これは中継engineがUSB送信完了を観測し、受信byteを受け取っていないことを示す。計測器がコマンドを実行したか、USB線上にデータを返したかは確定しない。[前段記録](Timeout_Snapshot_Diagnostic_Rev0.md)。faultを保持し、自動再送しない。

## .22.3の追加観測

原典SDK/vendorは変更せず、GNU linker wrapでPIO USB受信関数の戻り後に観測する。ACK等の時間制約区間の内部は変更しない。診断wrapperはRAM配置。対象CDCのbulk IN endpointが転送中の場合だけ、明示Q送信開始以降の呼出数・NAK PID数・非負戻り値数を集計する。転送開始/abort/再投入、DATA toggle変更、fault解除は行わない。

TIMEOUT Eの理由へ以下を追記する。通常R、他のE、ambiguous=0、payload上限に収まらない場合は追記しない。session/request/期限/ambiguousは保持し、X1 CRCは追記後のpayloadで再計算する。

| 項目 | 意味 |
|---|---|
| I | 対象bulk IN受信関数の呼出回数 |
| N | 最後の受信buffer PIDがNAKだった回数 |
| D | 下位受信関数が非負値を返した回数 |
| S/P | 最後の受信buffer先頭byte/PID（HEX） |
| EP | 対象bulk IN endpoint address（HEX、0なら未特定） |
| H | endpointのhas_transfer |
| K | endpointの期待DATA toggle |
| L | endpointのactual_len/total_len |

受信関数の戻り値やbufferは、その関数が返した範囲の観測に限る。ロジックアナライザの線上記録と同等とは扱わない。I=0の場合も原因を一つへ断定しない。D>0かつengine RX0ならPID/転送完成条件等を追加照合する。

wrapper呼出と集計には追加のCPU時間がある。受信関数内部は同一でも、タイミングに全く影響しないとは扱わず、診断版で再現しなくなっただけでは根本修正の証明にしない。

## 検証と実機状態

候補準備中。実機は.22.2のfaultを保持、親runtime稼働、Logger停止/drop0/Queue0、NF55G IDLE。機器の設定変更なし。原典資料とvendor sourceは変更なし。量産完成・原因確定とは扱わない。

## 候補固定・実機書込み準備

全467 Host/Mock試験成功（19.094秒）、ARM -Wall/-Wextra/-Werror build成功。ELFのCDC tableはguard wrapperを参照し、bulk INの実呼出はRAM `0x20000120`の受信wrapperへ接続している。UF2 96,256 byte、SHA256 `7a817134cffdf124197c68d958cfe9b5a96a98dbe308c8d5dd5a63e121e98ef2`。[候補manifest](USB_Lower_Diagnostic_Candidate/manifest.json)、[ARM build](USB_Lower_Diagnostic_Build_Retry.log)、[回帰試験](USB_Lower_Diagnostic_All_Unit.log)。親停止・SM4/5停止・外部端子入力化を実行/照合済み。Host単独BOOTSEL準備を依頼中、まだ.22.3は未配置。最初の制限付きビルドはNinja起動後に進行せず、確認済みの当該親子プロセスだけを停止して既設ツールチェーン権限で再実行した。最初のELF検証は最適化後関数名の照合方法を修正し、実symbolのdisassemblyで呼出先を確認した。FW source変更や実機再試行による対処ではない。
