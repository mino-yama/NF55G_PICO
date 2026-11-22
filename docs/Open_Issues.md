# Open Issues

2026-11-22 23日作業計画: 既存改善/診断と通常RSTの重複箇所を照合。今回の文書調査でコード変更なし、固定.22.3 UF2/全12ソースhash一致。将来RST実装はmain/engine/親link等を共有するため別版で統合・回帰検証する。23日は測定器HOST RST実装、USB IN診断、山田のQR取付け後単独確認、成立後の共存試験を計画。ハードは山田担当、BOOTSEL実装日/AD-AR/WDTは別途。[項目・手順・開発案件](Debug_Development_Plan_20261123_Rev0.md)。

2026-11-22 USB bulk INソース追跡（原因未確定・Open継続）: 固定SDK/vendorの受信投入→PIO IN→完了event→CDC FIFO→engineを確認。NAK継続/PID不一致は失敗eventなしで待機、FIFO空で受信投入失敗時はappに再投入契機なし、完了event未到達と期限前FIFO未回収でもengine RX0となり得る経路を整理。実発生の証明ではなく、.22.3の計数と追加観測で切分けが必要。コード/原典/FW/実機変更・試験実行なし。[調査Rev.0](Parent_Host_Integration_20261122_01/USB_Bulk_IN_Source_Trace_20261122_Rev0.md)。

2026-11-22 USB-HOST-RESET-01 分担・予定更新（Open継続）: 給電維持・信号切断・外部操作のハードは山田が検討。コマンドによるHOST通常RSTは2026-11-23に実装予定。ハード検討を通常RST実装の開始条件にせず、BOOTSEL実装日は未指定。今回は記録のみ、コード/Flash/実機操作なし。[分担・予定](USB_Host_Reset_Study_20261121/Development_Reset_Task_Decision_20261122_Rev0.md)。

2026-11-22 USB-HOST-RESET-01 開発用コマンド検討（Open継続）: ユーザー指定によりRST/BOOT外部端子操作なし・HOSTがハングしない前提で、既存UART経由のINFO/通常RESET/BOOTSELを検討。まず双方向UART実装済みの測定器HOSTを対象とし、FAULT中も使える管理入口、対象/boot世代照合、通常再起動後の親リンク再確立を提案。BOOTSEL中はUART受付不可で、外部給電OFF→PC給電へ切替えるとモードを失うため、給電維持PCデータ接続は回路/実機確認事項。QR RX実配線、wire/応答/期限は未確定。常時WDT/自動復旧は今回の範囲外。コード/Flash/実機操作なし。[開発用提案Rev.0](USB_Host_Reset_Study_20261121/Development_Reset_Bootsel_Command_Proposal_20261122_Rev0.md)。

2026-11-22 CDC下位診断: 実機.22.2の初回IDNがTIMEOUT_RX0_T1_C0_XNONE|1となった。自動再送なし・fault保持。候補.22.3は受信関数の戻り後に対象bulk INのNAK/PID/転送状態を観測し、TIMEOUT Eだけへ追記する。vendor原典・転送制御・fault規則は変更しない。Host/Mock全467件成功（19.094秒）、ARMビルド確認中・実機未配置。[記録](Parent_Host_Integration_20261122_01/USB_Lower_Diagnostic_Rev0.md)。


2026-11-22 CDC期限比較: .22.1で50回共存成功（CSV853行/D1 50件/drop0/SHA一致）。500回の2秒期限試験は116成功後117回目TIMEOUT、10秒期限試験も72成功後73回目TIMEOUT。両条件でD1 Retry0・SD/RTC OK・drop0、USB_RX_XFER/TX_XFER通知なし。DMMは連続OFF/IMM/trigger1/sample1/delay0/DCV/error0を読取り確認済み。TIMEOUT受信長/TX完成/応答完成/末尾を記録する候補.22.2を準備、全465回帰成功、ARM build進行中・未配置。[最新診断](Parent_Host_Integration_20261122_01/Timeout_Snapshot_Diagnostic_Rev0.md)。

2026-11-22 AD個別照合要求（Open）: 対象とPoint 1/2を明示し、同一試行の直前正常書込み値をAR読戻し値と照合、結果と両値を試験ログに残す。ATEへの指定応答は`OK:AD_VERIFY`、`ERR:AD_VERIFY_MISMATCH`、`ERR:AD_VERIFY_TIMEOUT`。電源再投入後の保持は別検証。現行正本のAD書込み・AR読出しATE入口は未実装。レビュー対象S1.13/S1.15_r1のARはfloat型pointを整数変換してREF8を出力し小数部分を失うため、全値の一致を保証できない。正式AR形式・小数を保持する読戻し手段・使用製品FW、AD/ARの正式通信契約とAR T2、未書込み/対象不一致/通信異常時の応答を設計確認する。OI-04/12/16/18/19/20/21はCloseしない。[詳細](ADC_Calibration_Development_20261119.md)。

2026-11-22 Scheduler修正後の実機共存再試験: 新Host nonce11F71FF28CE2AC1D/READYとIDN照合成功、親は再起動せず再開。29回目READでHost A/T→E=TIMEOUT|1となり停止（2秒の明示期限、Rなし）。D1はRetry0、SD/RTC OK、終了後もログdrop0/Queue0。親PIOエラーなし、X1 frame decode error0。SD排出飢餓とは別の未確定事象として記録し自動再送しない。CDC transfer失敗をTIMEOUTと区別する候補.22.1を準備、全464回帰・ARM/link・UF2/ELF照合成功、対象Hostへ退避/verify配置済み（通常配線復元・実機検証待ち）。 [記録](Parent_Host_Integration_20261122_01/Transfer_Error_Diagnostic_Rev0.md)。

## USB-CDC-SD-01: 連続ATE burst時のLogger排出飢餓（Open、2026-11-22）

2026-11-22 CDC/NF55G/SD共存修正: 実機でREAD+D1+ローカル照会の連続burst時にSDログdrop（21回目6件、終了後8件）を検出。最終ATE応答後の無条件returnにより次巡回までSDを延期し、次burstが先着するとLoggerが飢餓になる経路を回帰試験で再現（修正前drop688）。最終応答送出後は同じ巡回の既存has_work/通信busy判定へ進め、ATE待ち/未送出/受信中は優先、NF55G/外部通信中のSD禁止は維持。追加2件を含むHost Unit/Mock全461件成功（9.859秒）。修正版の実機配置・共存再試験を進行中。[受入記録](Parent_Host_Integration_20261122_01/Acceptance_Status_Rev1.md)。
実機同条件でdrop 0を再確認し、同期SD I/OによるATE応答時間の許容上限・長期/複合負荷の受入を残す。Codex判断でCloseしない。

2026-11-22 CDC受入継続: 可変長応答1000回・途中応答切断/遅着拒否・不正/正常ATE交互の回帰3件を追加、Host Unit/Mock全459件成功（17.130秒）。実機は親PIO停止を確認して接続解除/起動を実施したが、Host hがFAULTかつ旧boot nonceのままで起動成立未確認。RESET対象を確認するまで追加要求を停止。実機反復・送信中切断・旧応答境界等は未完了、Issue Open。[受入状況](Parent_Host_Integration_20261122_01/Acceptance_Status_Rev0.md)。

2026-11-22 引継ぎ実行: 親69f7d45962cfdfadの旧9848 byteを実機hash照合し、親全Flash 4 MB/Host全Flash 2 MBを退避・verify。親candidate 10012 byteを配置・再起動後SHA照合、Host BFCF2EDB84B0B37Fへ`.21.1`をload -vし通常起動。初回IDN成功後、idle USB-B抜線中は`LINK_NOT_READY|0`で拒否し、再接続後はRESETせず同じHost起動sessionでREADY/IDN成功（1回）。Host/Mock全456件成功。送信中切断・旧応答排除・Cache INVALID連携・長期/複合負荷は未受入、Issue Open継続。[実行結果](Parent_Host_Integration_20261122_01/Result_Rev0.md)。以下の未配置記述は各記録時点の履歴。

## USB-RELAY-HOTPLUG-01: 量産時の7355 USB-B接続/切断復帰（Open、2026-11-21）

ユーザー要件: 量産ではUSB-Bの接続/切断を操作者が安定して行える保証がないため、CDCデバッグ完了後にFWを修正し、接続/切断後の復帰を手動RESETに依存させない。機器本体へのRESET/SCPI初期化は対象外。WDT/親RESETの方式も本Issueで先行確定しない。

現行確認: 新規起動からの「7355最後に電源ON」は3/3回READY/IDN成功。「7355 ON後にHost/親起動、その後USB-B接続」は1/1回READY/IDN/READ成功。通信後のunmountはfault latch原因。candidate `.21.1`はidle disconnect後に同一sessionでremount/CDC再設定、切断中要求は`LINK_NOT_READY|0`で未送信拒否、送信開始後disconnectは`DISCONNECTED|1`でfault保持とした。Host/Mock 456件、全3 firmware targetのARM build/link、UF2 metadata確認済み。candidateはbuild/manifest記録済みだが対象Hostへ未配置。切断後Cache INVALIDの親連携、実機応答freshness/遅延データ、反復/負荷受入は未確認。根拠とrawは[実機比較記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Battery_Read_Precheck_20261121.md)。

残実装・受入要件: candidate `.21.1`を対象Hostへ安全に配置し、電源/USB-B hotplug実機でidle disconnect、CDC再列挙と9600/8N1・DTR/RTS再設定、要求前切断、送信中切断、遅延/残留応答、連続抜差し、7355電源断/投入を検証する。送信開始後の切断では親側の関連取得CacheをINVALIDにする統合確認が残り、自動再送は禁止。旧7355応答を新要求に採用しない境界を確認できない場合はRECOVERY_REQUIRED等で停止する。READ再開条件はREADY/新IDN・必要状態照合とする。ATE順序、他Host/NF55G/SD Timingと復帰不能時のATE通知も受入対象。実機合格・長期/複合負荷前のためIssue Open。

初期FW対策はcandidate `.21.1`として実装・Host/Mock・ARM build済み、対象個体へ未配置。切断中/切断直後の測定を許可せず、Flash退避/配置後に実機で復帰境界を確認する。本IssueはOpen。

2026-11-21 USB-HOST-RESET-01 目的訂正（Open継続）: ユーザーは7355/QR本体のRESETを求めておらず、通信経路上の問題とHostマイコンのキャッシュ/通信保持状態のリセットが目的と明示。状態クリアとHost再起動/WDTを分けて比較する案へ訂正。機器向けRESET/SCPI初期化は本件に含めない。方式/クリア範囲/転送停止/世代境界等は未確定。[現行Rev.2](USB_Host_Reset_Study_20261121/Host_Communication_State_Reset_Rev2.md)。コード/Flash/実機操作なし。

2026-11-21 USB-HOST-RESET-01 要件具体化（Open継続）: 量産でボタン操作は困難、構造上RUN配線を引き出せないとのユーザー説明により、検討主軸をHost監視/WDT/親UART管理指令/FAULT中も動くHost管理入口へ変更。手動RESETはデバッグ比較用。親対象リンクの再確立、7355旧応答排除、QRのRX配線・読取り境界も必要。期限/フレーム/保持領域/再起動上限等は未確定。コード/Flash/実機操作なし。[設計検討Rev.1](USB_Host_Reset_Study_20261121/Host_Supervision_and_Software_Reset_Rev1.md)。

2026-11-21 USB-HOST-RESET-01（Open）: NF55G Pico治具案件内でQR/CDC Hostのリセット方法を検討。手動RESETを第一候補、電源再投入を比較対象とする提案で採用未確定。CDCは親/Host双方のfault・session初期化と7355の旧応答/未完了処理解消が必要で、片側RESETのみを復帰完了としない。RUN外部配線を進めない既存方針は維持。ソフトRESET/自動watchdog/USB再初期化は未実装・採否未確定。コード/Flash/実機操作なし、関連IssueはCloseしない。[検討資料Rev.0](USB_Host_Reset_Study_20261121/Reset_Study_Rev0.md)。

2026-11-20 ユーザー方針更新: RUNパッド施工は難しいため外部RESET配線/駆動回路は進めず、手動RESET/電源再投入をデバッグで選ぶ。GP14/22は汎用予備。初回起動前から記録し、異常→正常データを交互に送る受入を計画。形式不正後の受付継続と、timeout/切断等の規定fault保持を分けて判定する。今回は計画のみ、実機注入/コード変更なし。 [計画](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Error_Normal_Alternation_Plan_Rev0/Plan_and_Reset_Decision_Rev0.md)／[現行GPIO Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev1.md)。

2026-11-20 工数/GPIO並行計画: 測定原文取得/ATE返却は実機済み。残る数値・単位/Cache/正式ATE入口とAD実装は仕様回答後コード/Mock1〜2実働日、基本実機確認含2〜3実働日（概算12〜24時間、待ち/全量産受入は別）。親GPIOは既存予約のQR GP8/9と実装済み測定器GP12/13を配線基準として維持。現行測定器PIOはSM4/5で旧案の順序に注意。RESETは必須/制御方式未確定、GP14/22を親側予備候補として確保しHost RUN結線は回路確認後。今回コード/Flash/実配線変更なし。 [工数](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Effort_Estimate_Rev0.md)／[配線基準](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev0.md)。

2026-11-20 ユーザー補足による解釈訂正: 「試験者設定のレンジ」はATE側のコマンドで決定/設定する意味。前面手動設定を前提にせず、ATEが固定レンジ値またはAUTO条件を指定→Queryで設定確認→測定要求を送る。Pico/Hostは本文を中継し、指定値の独自置換/自動最適化を行わない。次の安定性試験もこの順序で実施する計画。今回は記録訂正のみ、実機送信/コード/Flash変更なし。 [現行方針Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Next_Steps_After_ATE_Range_Decision_Rev1.md)。

2026-11-20 ユーザー決定: 最適レンジは試験者が設定し、レンジ追加調査はここまでとする。中継は明示コマンド/原文を維持し自動最適化/独自補正しない。レンジ読戻し差の記録は保持し中継継続のブロッカーにしない。次は固定入力/試験者レンジでの安定性→timeout/切断/清浄復帰→ATE/NF55G/SD共存受入。その後、正式API等を確認してADC測定Cache/ATE確認後別指令ADへ接続する。今回は説明/記録のみ。 [方針・次工程](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Next_Steps_After_Operator_Range_Decision_Rev0.md)。

2026-11-20 Codex直接送受信: ユーザー固定入力/COM7解放後、AUTO単発-2.91185V、続けてRANG20指定-2.9118V、RANG200指定-2.912V、AUTO-2.91186Vを取得。全機器エラー0、各READ一回/再送なし、最終AUTO ON/COM7解放済み。CONFは20指定で199.9999V、200指定で1099.999V、AUTO測定後19.99999Vを原文保持し、選択境界の理由は未解決でIssue Open維持。 [測定比較](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Codex_Fixed_Range_Comparison_01/Result_Rev0.md)。

2026-11-20 UP一回の表示対応確認: 押下前AUTO0/CONF19.99999V、ユーザーの押下時表示200V、押下後AUTO0/CONF199.9999V。今回の一時表示は変更後レンジと一致。過去RANG20直後の約200V読戻しの理由は別途未解明でIssue Open維持。現在固定200V相当、次は同じ低電圧入力で単発読出しを比較。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Panel_Range_Interpretation_01/UP_Once_Result_Rev0.md)。

2026-11-20 前面キー操作なしの基準Query: AUTO?=0、CONF?はVOLT +1.999999E+01,+1.000000E-06（正常36byte）。現在の機器読戻しは固定20Vレンジ相当。以前のCONF約200Vとは取得時点/キー操作が異なり、過去SCPI動作の原因や一時表示の意味は未確定。次はUP一回の前後を比較。 [基準記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Panel_Range_Interpretation_01/No_Key_Baseline_Rev0.md)。

2026-11-20 前面レンジ確認の前提を補足: ユーザーはレンジボタン押下時の表示が変更前後のどちらか不明と回答。取説4-3/4-19でUP/DOWNは設定変更そのものと確認。過去の前面20V報告は保持するが「現在レンジ確定」との扱いは保留し、前面読取り未確認へ訂正。正常CONF約200Vの観測は保持。USB-CDC-RANGE-01はCloseせず確認前提を更新。まずキー操作なしのAUTO?/CONF?を記録する。 [補足記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Panel_Range_Interpretation_01/Clarification_Rev0.md)。

2026-11-20 ユーザー単発測定: READ?の15byte原文-02.91180E+00+CRLFを取得、-2.91180V、機器エラー0。前面もマイナスと回答し極性一致。校正/製品合否は未判定、前面20V/CONF約200V相違はOpen維持。次は同じ約2.9V入力で200Vレンジの前面/原文/再測定を確認する手順を作成。Codexの実機送信/コード変更なし。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/User_Single_Measurement_01/Result_Rev0.md)。

2026-11-20 .3のユーザー固定20V確認: AUTO OFF/RANG20の後、AUTO?=0、CONF?は正常36byteのVOLT +1.999999E+02,+1.000000E-05、SYST:ERR?=0。ユーザーは前面20Vを確認。受信書式は正常だが前面/読戻し相違は継続しUSB-CDC-RANGE-01をOpen維持。FIFO不具合だけを原因にしない。次の測定用V/COM入力値を確認中、Codexは測定未送信。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/User_Fixed_20V_Check_01/Result_Rev0.md)。

2026-11-20 .3実機で設定Query5種×12周（60件、機器応答総1035byte）と終了エラーQueryを成功。全周で原文/書式/長さ一致、CONFは正常なVOLT +1.999999E+01,+1.000000E-06、AUTO=1、エラー0。先行の応答崩れは今回再現せず、受信健全性を確認。固定20V切替/前面一致/測定は未実施でレンジIssue等はOpen維持。COM7解放済み。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/CONF_FIFO_Validation_01/Result_Rev0.md)。

2026-11-20 CDC FIFO修正版.3をBFCF2EDB84B0B37Fへ配置完了。旧.2全Flash2MiB退避/hash照合、新UF2照合、Flash verify、書込み後個体/版/BOOTSEL照合成功。rebootなし、親ソフト変更なし。次は通常接続で設定Query12周の受信健全性を確認する。レンジ/測定は未実施、Issue Open維持。 [配置結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Host_Deployment_03/Result_Rev0.md)。

2026-11-20 CDC FIFO修正版.3のARM build/link、UF2版/hash照合完了。全453件成功。TX/RX FIFO256整合、endpoint64維持、SDK原本変更なし。実機はまだ.2で、全Flash退避後に.3配置する準備。測定前に累積Queryの受信健全性を確認する。 [ビルド結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Build_Result_Rev0.md)。

2026-11-20 USB-RELAY-CDC-BUF-01（Open）: 提示CONF?が36byteの不正文字列に復号。固定SDK CDCのrx配列はTX macro確保64byte/初期化RX深さ256byteという不一致を確認し、実FIFOで隣接領域書換えを再現。Host側TX/RX256整合+ビルド時guardへ修正、新FW.3をビルド中。回帰3件追加し全453件成功。提示崩れの実機因果/20V問題は未確定でCloseしない。 [修正記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Result_Rev0.md)。

2026-11-20 .2実機試行10で親経由7355識別中継成功。ATEへOK:EXT_RX:32:HEXを返しADC Corp.,7355,246410099,  A02+CRLFを原文保持。Host入力線にHとQ一件を正常捕捉、再送/レンジ/READなし。試行9の起動00byte付き照合成功と合わせ同期修正の効果を確認。全受入/Issue Closeとはせず切断復帰/実負荷等は残る。シリアルモニターCOM7/57600 8N1を解放済み。 [解決記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/Resolution_Rev0.md)。

2026-11-20 修正版.2実機試行9: 電源投入前からのHost GP1監視で00+正常Hの76byteを確認。同条件でも親経由のh照合成立を示すEXT_LINK_NOT_READY/AMBIGUOUS=0を取得し、旧TIMEOUTから改善。USB-B未接続で機器Qなし。識別中継/負荷等は未確認のためIssueはOpen。次は同じ通電でUSB-Bだけ接続し識別確認。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Host_Sync_Verify_09/Result_Rev0.md)。

2026-11-20 Host同期修正版.2をBFCF2EDB84B0B37Fへ配置完了。旧.1全Flash2MiB退避・照合、新UF2 hash照合、load -vのFlash verify、書込み後ID/版/BOOTSEL照合成功。rebootなし、通常起動/親経由受入は次試験待ち。親ソフト変更なし、450件成功を継承。 [配置結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/Host_Deployment_02/Result_Rev0.md)。

2026-11-20 Host同期修正版.2のARM build/linkとUF2 metadata/hash照合完了。全450件成功。旧.1 UF2/sourceを保持し、新.2を別名配置用保存。実機はまだ.1で未書込み、次は個体照合/全Flash退避後に配置・実機再試験。 [ビルド結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/Build_Result_Rev0.md)。

2026-11-20 起動時UART不具合を実原文で再現し修正: Host GP1で00 00+正常H（計77byte）を取得。旧Cは一行として破棄しhなし。Host受信を@先頭から同期させ、CRC/長さ/session/重複/故障保持/再送禁止を維持。回帰4件を追加して全450件成功。FW .2をビルド中、実機未配置。電気的起源と実機因果の最終確認は残りIssueはOpen。 [修正記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/Result_Rev0.md)。

2026-11-20 外部給電・PC UART直結でHost h/NOT_READY成功。試行7の親H原文75byteをPC UARTからそのまま送る比較でもh成功。原文書式は受理可能。親直結時の起動データ/信号条件等は未確認で、次は電源投入前からHost GP1を監視する準備。起動時データで最初のHが同じ不正行として破棄される可能性は仮説のみ。コード/Flash変更なし、Issue Open維持。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_External_Replay_01/Result_Rev0.md)。

2026-11-20 Host実電圧のユーザー回答は5.0V/3.2V。測定精度/波形は未確認で電源異常や原因を断定しない。次は外部給電・USB-B未接続を維持し親信号を切離してPC UARTからH一回を送り、送信元を比較する準備。 [実測報告](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Host_NoUSB_07/Power_Measurement_Rev0.md)／[次試験](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_External_UART_01/Preparation_Rev0.md)。

2026-11-20 試行7: 外部給電でUSB-B未接続の冷起動でも、親経由はTIMEOUT/AMBIGUOUS=0。Host GP1監視でCRC正常H 75byteを確認。USB起動順序だけで原因を確定しない。次はHost基板の実5V/3V3電圧をユーザーへ依頼中。今回はHost TXを直接監視していない。コード/Flash変更・再送なし、Issue Open維持。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Host_NoUSB_07/Result_Rev0.md)。

2026-11-20 試行6: Host GP1受信線で親Hフレーム75byteを捕捉、CRC/形式正常。親からのH送信は監視点で確認。治具ID正常だが中継はTIMEOUT/AMBIGUOUS=0。Host内部UART受理/実電圧/起動時USB接続順序等は未確認。次は外部給電でUSB-Bなし冷起動を比較し、原因を決めず切り分ける。コード/Flash変更なし、Issue Open維持。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Host_Input_Capture_06/Result_Rev0.md)。

2026-11-20 ユーザー回答: Host側の外部5V/GND線も接続済み。端子実電圧は未測定で電源正常を断定しない。次は監視RXDをHost GP1へ移し、親TXのH要求到達を受動採取する準備。電源再投入で前試行fault/sessionを持越さず実行する。 [次試験準備](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Host_Input_Capture_06/Preparation_Rev0.md)。

2026-11-20 試行5: 親経由で治具IDは成功、EXT_QUERYは2015ms後TIMEOUT/AMBIGUOUS=0。並行したCOM22 RX専用Host TX監視は0byte・捕捉例外なし。直前Host単体USB-C給電では識別成功。外部給電復帰と親Hの到達等は未確認のため、Host側外部5V/GND線の接続をユーザー確認中。自動再送/Flash変更なし、Issue Open維持。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Host_Capture_05/Result_Rev0.md)。

2026-11-20 Host単体識別成功: USB-Bなし冷起動から接続後、h=READY、基板ID/FW版一致。Q(*IDN?、2000ms)にA/T/Rを確認し7355の32byte識別原文を取得。レンジ/READ/再送/Flash変更なし。親経由は未成立のまま、次は親復帰とHost TX受動採取を準備。IssueはOpen維持。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_Direct_IDN_02/Result_Rev0.md)。

2026-11-20 Host冷起動比較: USB-BなしでHostとUART変換器を無給電にして再接続後、H/h応答が回復。基板ID/FW版一致、NOT_READY、16ms。USB切断だけでは回復しなかった先行試験と区別。原因未確定、次は同じ給電/UARTでUSB-B接続の変化を比較する。機器コマンド/Flash変更なし、Issue Open維持。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_Cold_Boot_01/Result_Rev0.md)。

2026-11-20 USB-B切離し比較: Hostの電源/UART維持でHを1回送信し3000ms待機したが受信0byte。診断JSONのFRAME_ENDINGは空受信をdecodeした結果で、実機不正フレームの観測ではない。機器コマンドなし。次はUSB-B未接続でHost/変換器を無給電にして冷起動比較。原因未確定、Issue Open維持。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_USB_Disconnected_01/Result_Rev0.md)。

2026-11-20 Host単体デバッグ: COM22からHを1回送ったが3秒応答なし、受信0byte。Q/SCPI未送信。先行のUSB-B未接続時にはH応答があったため、HostのUSB-C給電/UART配線を維持して7355 USB-Bだけ外す比較診断を準備。USB起因とは未断定、FW変更・自動再送なし。USB-RELAY-LINK-01はOpen。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_Direct_IDN_01/Result_Rev0.md)。

2026-11-20 再試験4: COM7/57600 8N1で治具ID応答成功。EXT_QUERY 2000 *IDN?はERR:EXT_TIMEOUT:AMBIGUOUS=0、7355識別は未取得。自動再送/レンジ/READ/追加デバッグ/Flash変更なし、COM7解放済み。USB-B接続復帰後も中継TIMEOUTが返り、停止箇所・原因は未確定。Issue Open継続。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Capture_04/Result_Rev0.md)。

2026-11-20 接続復帰後試験3: ELECOMはCOM7（056E:5004）へ変化。COM5では送信前停止し、COM7で治具*IDN?を1回送ったが10秒応答0byte。EXT_QUERYは未送信、自動再送・Flash変更なし。親の外部給電復帰とATE接続を確認する段階。IssueはOpen継続。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Capture_03/Result_Rev0.md)。

2026-11-20 親単体診断: 実機IDを照合しFactory/SD/中継PIO初期化成功。PIO RXを同じGP12へ一時割当てた内部送受信で75byte完全一致・UARTエラーなし。元GP13入力/親Host配線/Host状態は未確認でUSB-RELAY-LINK-01はOpen維持。本番コード/Flash変更・機器Queryなし。終了時は親friendly REPL停止。 [診断結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Startup_Investigation_01/Result_Rev0.md)。

2026-11-20 再試験2: COM5/57600 8N1で治具ID NF55G_PICO_FIXTURE,Rev.0 の応答を確認。EXT_QUERY 2000 *IDN?は2016ms後にERR:EXT_TIMEOUT:AMBIGUOUS=0。7355識別は未取得、自動再送・電源/コード変更・レンジ切替/READなし。停止箇所は未確定でUSB-RELAY-LINK-01をOpen追加。ATE無応答Issueは今回再現せず、原因未確定のままOpen維持。 [再試験結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Capture_02/Result_Rev0.md)。

## USB-RELAY-LINK-01: 中継識別要求のTIMEOUT（Open、2026-11-20）
2026-11-21 最新反復結果: USB-B接続/7355 OFF状態からHost→親Picoを起動し、7355を最後にONする比較Aは3回連続でHost READY/IDN A/T/R成功。7355先行ON後のUSB-B接続比較Bは1回、READも1回成功。今回の起動順失敗は未再現だが、利用中unmountのfault latch/遅延応答鮮度と量産反復受入は未解決でIssue Open。[反復証跡](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Battery_Read_Precheck_20261121.md)。


確認事実: ATEの治具ID応答成功後、外部識別要求はTIMEOUT/AMBIGUOUS=0。推測: HELLO未成立またはHostのUSB送信開始前TIMEOUT等。未確認: 親/Host間の実フレーム、PIO実初期化、Host通常起動・USB状態。原因を決めず親単体診断へ進む。実機中継受入未成立。

2026-11-21 追加: COM22受動監視中の読取専用ID Queryは`ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`、Host GP0 TX 0 byteで親fault gateによる拒否と切り分け。通信idle確認後、Host→親Picoの順に既設RESET/RUNを手動操作し、Host `.3`/READYと7355 IDNを確認。DCV/AUTO ON/CONF約20 V・エラー0でREADを10回取得、値9.62322～9.62331 V、各機器エラー0。設定書込みなし。fault初発原因、精度・製品PASS、前面/CONFのレンジ相違は未解決のため本Issueおよび`USB-CDC-RANGE-01`はOpen継続。WDT/管理RESET機能は未実装。[逐次読出し結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Battery_Read_Precheck_20261121.md)。

切断比較追記: USB-Bが空とのユーザー確認後も1回目のIDN応答がA/T/Rで返ったが鮮度は未証明。次要求はHost `RECOVERY_REQUIRED|0`で拒否され、現在のHost/親リンクはfault状態。USB unmount時の遅延応答境界は未受入、切断中READなし。物理接続確認後に手動復帰し、fresh IDNを確認するまで測定を再開しない。[切断比較raw](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Battery_Read_Precheck_20261121.md)。

再接続後追記: ユーザーのHost→親Pico手動復帰完了回答後も、COM7のIDN Queryは`ERR:EXT_RECOVERY_REQUIRED:AMBIGUOUS=0`、COM22 Host TXは0 byte。親fault gateが残ったため測定を中止した。意図した親個体のリセット成立は未確認。対象Pico/RESET操作を特定するまで追加Query/READをしない。[再試行raw](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Battery_Read_Precheck_20261121.md)。

2026-11-21 後続結果: Host→親Picoの再起動後、電源順比較A (USB-B固定、7355を最後にON) とB (7355 ON後にUSB-B接続) は各1回READY/IDN成功。Bでは設定状態を維持しREAD `+09.62247E+00`, SYST:ERR=0。よって電源ON順や新規USB-B接続だけでは不安定さを再現しなかった。unmount faultは`relay_host_device_ready(false)`→high_watermark判定→Host fault latch、remountしてもconfigure抑止というソース経路と実機HELLO FAULTが一致。回帰テスト追加、Host/Mock 454件成功。暫定運用は通信session中のUSB-B抜線/7355電源断を避け、必要時Host→親再起動後にREADY/IDN確認。最初の切断後IDNの鮮度・遅着応答境界は未確定でIssue Open。[根拠・比較結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Battery_Read_Precheck_20261121.md)。

2026-11-21 反復数訂正: 上記の当初記録後、比較Aを2回追加し、USB-B固定・7355最後投入で3/3回READY/IDN成功。比較Bは1/1回IDN成功、READも1回成功した。初回1回ずつの記述は当時の結果として保持し、現時点の集計はA=3/3、B=1/1。少数試行であり量産受入完了ではない。[追加raw](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Battery_Read_Precheck_20261121.md)。

## USB-RELAY-ATE-01: 配置後の治具ATE ID応答なし（Open、2026-11-20）

COM5のELECOM（056E:5004）、57600/8N1から治具自身の*IDN?+CRを一回write（戻り値6）したが、10,093msで受信0byte。治具ID未確認のためEXT_QUERYは未送信。ユーザーはATE側UART0/GP0/GP1への接続を確認済み。親の起動・RS232信号・給電状態のいずれも未確認で、原因を断定しない。配置前/後のRAM・import成功は実ハード初期化/通常起動の成功を意味しない。次は親単独USBで起動ログ/Factory初期化を診断し、57600を根拠なく変更しない。 [試行結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Capture_01/Result_Rev0.md)。

2026-11-20 USB-SUB-01/05進捗: 親adapter/ATE入口と独立Host中継FWを実装し、全446件成功・ARM build/link成功。HELLO payloadのchipid|FW|状態、os.urandom/固定SDK get_rand_64を実装詳細として照合し、PIO TX4+RX12=16命令を公式assemblerで確認。これらのコード作成・Host検証は完了。一方、実機ファイル配置/Flash・実UART/USB・PIO IRQ/負荷・電源/端子/RESET・旧機器応答を含む実復帰は未確認。故障は保持し自動再送しない。USB-SUB-01/05・USB-INT-01はOpenを維持。レンジ相違は保留。 [リンク実装記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Result_Rev0.md)。

2026-11-20 USB-SUB-01/05の回答済み仕様: ユーザーが開発用通信契約Rev.1を承認。ATEのEXT_QUERY/EXT_SEND、timeout1～10000ms、本文/応答192byte、親子115200/8N1・親GP12/13/HostGP0/1、session/request/CRC-32と512byte上限のフレームを採用。これらを未承認候補とは扱わない。一方、HELLO payloadのFW版/ID表現、nonce用API、復帰時の旧データ排除、PIO資源/現物配線/RESET/負荷・実機受入は残るためIssueはOpen維持。レンジ相違検証は保留。 [確定仕様 Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Interface_Spec_Rev1.md)。

2026-11-20 USB-SUB-01/05進捗: 外部測定器の書式非依存中継コアを実装し全401件成功。ATE名/応答形式・親子UART pin/baudrate/フレーム/CRC/起動相関等は未承認案のまま。adapterの清浄接続保証、現物配線とPIO資源/実機負荷は未検証。既存IssueはOpenを維持する。 [実装記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Result_Rev0.md)。

2026-11-20 .5実機再現: 同一試行でユーザーは前面20Vを報告。RANG 20直後のSYST:ERR?は+0,"No error"、CONFは再び約200Vを返し、.5はCONF_RANGE_NOT_20VでREAD前停止。原因は未確定でUSB-CDC-RANGE-01をOpen維持。 [実機結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Handoff_20261120_Rev0/Runtime_v5_run01/Result_Rev0.md)。

## USB-CDC-RANGE-01: 7355前面レンジとCONF読戻しの相違（Open、2026-11-20）

確認事実: raw #09で`:SENS:VOLT:DC:RANG 20`の後、`:CONF?`が`"VOLT +1.999999E+02,+1.000000E-05"`を返した。ユーザーは引継ぎ時に前面20Vレンジ・電源OFFと回答。応答数値は約200Vであり前面20Vと一致しない。推測: nominal値とfull-scale境界、機器応答仕様等の可能性は未検証で、原因としない。未確認: 同一試行時点の前面/読戻し対応、レンジコマンドの実機挙動、メーカーの説明。独自換算や200V応答の20V扱いは行わない。評価FW.5でも19～21V以外はREAD前停止を維持する。設計/機器仕様の確認を要し、Codex判断でCloseしない。[引継ぎ記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Handoff_20261120_Rev0/Result_Rev0.md)。

2026-11-19 CAL-EXT-02の追加回答: シャント抵抗は50A/50mV（1mΩ）、取得単位mV、Aへの換算担当はPicoで確定。I[A]=U[mV]を内部校正候補取得へ実装した。元測定Cacheを保持し、誤単位では候補を拒否する。正式API・実応答の単位正規化・AD表現/極性・A/B点対応等の未回答部分と実機検証は継続し、IssueはCloseしない。[記録](ADC_Calibration_Development_20261119.md)。

2026-11-19ユーザー決定と実装進捗: 必須校正はDISCHG_I/BATT_CHG/BATT_Vの3系統×2点。OI-17は設計指示7.3との不整合とせず、12VOUT_Iの追加校正は要求しない。ただし関連機能の確認完了/Issue Closeではない。OI-19の保存後反映・再投入要否は実機確認待ち。ADC治具機能の開発は継続可となり、取得Cacheの内部基盤・試行境界の失効を実装。CAL-EXT-02等の正式API、A/BとP1/P2対応、シャント換算、AD/AR契約の未回答部分は継続する。製品FW/GitHub Issuesは変更しない。[確定事項・未確認事項・今回の境界](ADC_Calibration_Development_20261119.md)。
2026-11-19 OI-17の開発影響判定: NF55G製品FWの12VOUT_I固定値は試験手順書に検査項目として明記されておらず、ユーザー確認によりFWの設計思想によるものと判明。OI-17として追跡を継続するが、治具開発のブロッカーではない。IssueはCloseせず、製品FWやAD/AR動作を変更しない。

2026-11-14 取得値Cache書込み（詳細設計Open）: DMM/QR読取り→Cache・ATE返却→ATE確認→別指令でCache値書込み、数値直接指定方式の維持、書込み完了時の使用Cache破棄、TEST_END時の全取得Cache破棄はユーザー確定。TEST_END後の遅着では復活させず、成否不明時もHard Rule 15に従いINVALID。正式API/取得識別・Cache名/追加期限・完了単位/明示拒否時処理・単位換算・QR/SS変換と保留解除時期は未確定。実装・受入未完了のため関連IssueはCloseしない。[確定要件](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Acquired_Value_Write_Requirement_Rev0.md)。

## 2026-11-11 D1～D5各10回の受信時間比較（D4-TIM-01、Open継続）

S1.13・PS_ON=1／BATT_ON=0、COM6／COM20でD1／D2／D3／D5を各10回測定。ACK後完全応答の平均／最大はD1=14.0／15ms、D2=22.0／23ms、D3=18.6／34ms、D5=58.9／74msで、現行T2内。通常40回は再送0・Protocol OK。D2準備のSC1回は母数から除外。

D4は再送なし・Cache非採用のRAM観測で10回の完全応答を取得。CSV時刻の平均116.0ms・最大133ms、全回100ms超過（最小113ms）。1000msの測定窓は製品用T2への採用ではなく、現行D4=100ms、ソース、量産不使用方針を維持する。D4の通常Transaction10回成功とは扱わない。線上送出時刻・Pico受信負荷の寄与と最終仕様を確認し、D4-TIM-01はCloseしない。

両CSVのSD／PC SHA-256、全102フレームBCC、全14列、標本数と平均の独立再検算が一致。ログ破棄0、通常待受復帰・COM解放済み。[結果・各回データ・方式の区別](Spec_Review_20261111/D1_D5_Timing_20261111_112941/Timing_Result_Rev0.md)。D2-PS-01、OI-01／03、他FW・動作状態・長時間・実機異常系は未解決。

## 2026-11-11 D0 T2の300ms採用（OI-02、Open継続）

同日実機追記: 開発機COM6／unique_id=69f7d45962cfdfadへconfig.pyだけを配置しhash一致、読込済みT2=300msを確認。製品S1.13・PS_ON=1／BATT_ON=0でD0を10回取得し、ACK後完全応答180～182ms、再送0、DATA327文字・BCC一致。CSVのSD／PC hash一致・破棄0、通常待受復帰・COM解放済み。下記の実機配置未確認は追記前の状態。長時間・異常系・EB競合・量産全条件を未確認としてOpen継続。[実機結果](Spec_Review_20261111/Hardware_D0_T2_300ms_Result_20261111.md)。

- ユーザーが通信r2事前確認版p.17／28のD0 T2=300msの先行反映を指示。今回D0だけを採用し、T1や他のr2変更は従来どおり管理する。
- src/config.py、D0送信契約、関連Master・テストを300msへ同期。下記の600ms暫定・変更候補は本指示前の履歴。
- OI-02の一覧／個別説明の値の不一致はr2で統一され、採用値も300msへ変更。本改訂後の実機配置・応答最長時間・量産Timingは未確認のため、Issueは独断でCloseしない。OI-01、OI-03と他Issueの状態は変更しない。
- [変更・検証記録](Spec_Review_20261111/D0_T2_300ms_Implementation_20261111.md)を参照。

## 2026-11-11 RW11改訂仕様の事前確認（Open継続）

対象は通信r2事前確認（2026/10/19）と購入仕様2d5（同日）。現行r1基準・実装は変更せず、以下を設計確認対象として追加する。[影響確認Rev.0](Spec_Review_20261111/Review_Rev0.md)の第3～6節に原典ページ、確認事実、見立て、質問を記載。購入旧版との厳密差分は未実施。既存IssueをCloseしない。

既存OIへの追加根拠: OI-02は通信r2 p.17／28と購入p.42がD0 T2=300msで一致し、文書上の不一致解消候補。PARAM-IR-01は購入p.36が0=検出停止と明記するが、通信r2 p.19の初期値／停止併記は残る。ERP-CONDITION-01は購入p.14～15でGRP=101の信号非依存・SE制御・負荷／時間条件を具体化。OI-23は購入p.46で35文字・6項目が裏付けられるが、容量・REV／LOT変換・SS対応は未確定。OI-07は購入p.25～26で500mA以下の取得エラーと測定条件を具体化。OI-22は通信r2 p.37でUSER書換え前後の説明が整理された。いずれも適用FW・設計承認・必要な実機確認前の回答候補として扱う。

READ-FD-01は通信r2 p.38でもFD見出しと46h 30hの不一致が残る。OL応答見出しはp.34でOLへ修正されたため、OLの表記改善とFD未解決を分ける。D2-PS-01、BE-ACCEPT-01、D4-TIM-01、AD／AR関連OIは未解決。SS開発保留・FU禁止・Picoで製品判定しない方針を維持する。

| 新規ID | 確認事実と設計確認事項 | 状態 |
|---|---|---|
| SPEC-R2-01 | D4長: 通信r2 p.27／32～33は積算70・合計212、購入p.42は積算100・合計242。正式長／順序・適用FWと訂正対象を確認。治具は212を維持し自動吸収しない。D4-TIM-01とは別問題 | Open |
| SPEC-R2-02 | 警告設定: BBUは通信r2 p.19が85℃／60～95℃、購入p.34設定表が90℃／60～100℃。購入同頁のADU／BBU保護表と設定表で解除温度も不一致。FAN無効化65534rpm対254℃、D1 ADU_TEMP_WNG非送信とEB／保護表の適用範囲を確認。保護設定拒否は維持 | Open |
| SPEC-R2-03 | QR容量: 購入p.46のVersion1／21セル／Mと35文字は両立しない。DENSO WAVE公式表でVersion1／Mは数字34桁・英数字20文字。版／内容の訂正、印字・余白・実Sampleを確認。35文字受信を短縮しない。OI-23関連 | Open |
| SPEC-R2-04 | REV／SS: 購入p.5はQR欄が―、A09以降の通信末尾ピリオド指定とA01.～A06.の表が併存。p.46はQR REV3桁。通信r2 p.22のUNIT_REV4文字への変換、ADU／BBUの0応答とREV管理説明、LOT・年週・予約・FW_REV非更新を含むSS対応を確認。末尾文字・ゼロを推測補完しない。OI-23関連 | Open |
| SPEC-R2-05 | 補正: 購入p.26本文のPS_OFF／7.8Vと三社方法のPS_ON／5V・10Vが不一致。充電電流点が0.5V／1.85V表記、放電点は空欄。既存ユーザー指定条件との対応、単位・P1/P2・正式AD／AR通信を確認。CAL-EXT-01、OI-04／05／12／16～21関連 | Open |
| SPEC-R2-06 | OFF消去: 通信r2 p.39・購入p.38はD2後SLでクリア、通信r2 p.32はBATT1,2_DEG除外と途中AC_OFF／PS_OFF例外、p.23はGET DATA後と記載。消去の許可元・対象・タイミングと例外を確認。時刻差によるAC_OFF計算の扱いも確認。OI-08関連 | Open |
| SPEC-R2-07 | 多重／監視図: 通信r2 p.7は先行処理継続・最終ACK正常受信で終結、p.11図はレスポンス②／ACK①、p.14装置側図はコマンドACK後T1始動。応答ID・順序、T2との関係、ACK欠落・遅延再送・EB競合を確認。装置側T1は未確定、OI-01／11とD4-TIM-01関連 | Open |
| SPEC-R2-08 | CF／解除／Cache: 購入p.21のCFによるAUTO_CHARGE無効とクリア後復元について、D5が保存値／実効値のどちらを返すか、解除がCF DATA0／CDのどちらか確認。購入p.36～37のバッテリラッチ解除の条件付き再起動と一覧×の関係、CD各DATAの範囲も確認。現行CFのINFO維持・SL後D2等の維持を変更すべきかはCache契約と併せて確認し、独断変更しない | Open |
| SPEC-R2-09 | 計数／観測: 購入p.11の停電85V以下（設計75～83V）とp.38／通信r2 p.41のAC_FAIL_COUNT 70V以下の対応、短時間瞬断時の放電と通知の区別を確認。通信r2 p.29のBURST_ON=状態とp.30の入力信号・実動作非依存の関係も確認。ERP-CONDITION-01関連 | Open |

検証: 現行Host／Mock284件成功。r2適合・製品実動作を保証する試験ではない。ソース／テストコード／実機配置変更なし。

## TEST-SESSION-01: 試験中断とTEST_START再受信時のデータ分離（Open、2026-11-11）

2026-11-11完了整理: 再START修正・Pico配置・正常系3試行・ログ回収は完了。懸念事項は継続調査とし、QR実入力／新USB要求相関、実SD異常系、量産Timing全般、START再送識別を残す。SSは保留。temp再回収3本もSD原本hash一致。詳細と完了範囲は[実装記録](Test_Interruption_20261111/Implementation_20261111.md)を参照。IssueはCloseしない。

2026-11-11修正版実機確認: 事前提示手順に従いCOM6へ4ファイル配置、旧25ファイル退避、配置hash一致。COM20でSC→D0→Query→10秒→再STARTと3試行を実施し、再START両方OK、旧DATA失効、独立CSV3本・SD／PC hash一致、保存診断正常・破棄0を確認した。再STARTのPC往復163.3／200.2ms。通常待受へ復帰・COM解放済み。[詳細](Test_Interruption_20261111/Hardware_Deployment_Result_20261111.md)。下記の実機未配置記述は過去時点。QR／SS・新USB要求相関・実機保存異常系・量産Timing全般は未確認で、IssueはOpenを維持する。

2026-11-11修正開始指示後: 再STARTの前試行保存→新試行開始をソースに実装。試行ID付きCSV、旧Queue・QR／S/N非継承、全製品Cache失効、保存延期時BUSY、前試行の保存診断と最新8件RAM履歴、既存BANKからの採番・容量管理を更新。Host／Mock284件成功。修正版の実機配置・Timing確認は未実施。SS開発は保留し、正式SS／新USB経路の要求相関は未実装。[実装記録](Test_Interruption_20261111/Implementation_20261111.md)。以下の未実装・着手待ち記述は変更前の履歴。残項目確認前のためOpen継続。

2026-11-11実機観測: ユーザー指定のTEST_START→SC→DATA_REFRESH→データ取得→10秒待機→再TEST_STARTをCOM20で実施。SC／D0成功、再STARTはERR:BUSY、通信IDLEで、同じCSVに記録された。TEST_END後の保存診断OK・破棄0、回収CSVのSD／PC hash一致。QR／SS未実施、src／tests／firmware変更・配置なし。[結果と証跡](Test_Interruption_20261111/Hardware_Start_Repeat_Result_20261111.md)。SS開発は保留し、本結果を基に開発着手のユーザー判断を待つ。IssueはOpen継続。

- ユーザー要求: 自律Refresh／PS_ON?／疎通確認で中断を推定せず、TEST_STARTの繰返しとTEST_ENDを基にQR／シリアルとTEST Logを保全する。まず混在調査と方針検討を行い、ソースへ即時反映しない。
- 確認事実: 現行の二重TEST_STARTはERR:BUSYで前回分を閉じない。Hostで、その後の操作続行と別QR受理により1本のログへ2試行分が入り、後のS/Nで命名されることを再現。QR受信途中にTEST_END→次STARTとし、旧QR完了が新試験へ採用される経路も再現。製品Cacheは試験境界で失効しない。QR→SS連携は未実装であり、製品への誤書込みを実証したものではない。
- 採用基本方針（2026-11-11ユーザー指定）: 受付済みTEST_STARTごとに独立した試行IDを付け、1試行1CSVとすることを最重要要件とする。1回目、2回目、3回目を同じファイルへ追記しない。前回分を終了指示未受信として保全し、QRの履歴保持と書込み利用資格を分ける。製品PASS/FAILや中断理由は推定しない。詳細設計・実装は未実施。
- 要求対象外（同日ユーザー指定）: 試験中は複数回のAC_OFFがあるため、製品電源瞬断の検出を要求しない。AC_OFFを試行分割の根拠にしない。Pico電源断時の途中データ消失は許容し、保持・復旧を要求しない。ただし通常動作での試行混在と既存CSVの追記・上書きは許容しない。
- QR／SS追加確定（同日ユーザー指定）: 製品交換を識別できないためQRは次試行へ引き継がない。同一製品の再試験もQRを再取得し、ATEの明示指示で再度SSを実行する。新試行の書込みシリアルが空ならエラーを返してSSをNF55Gへ送信しない。前回値や既定値で補完しない。前試行のQR履歴は前試行に保存する。正式エラーコード・空の具体的判定・SSフィールド対応は未確定でOI-23と関連する。
- 残確認事項: START再送の識別方法、最終中断後に次指示がない場合、切替え受付／保存完了応答、ID生成・命名衝突、保存診断履歴、製品Cache失効の具体化、SS空シリアルの判定・エラー詳細。方針採用だけでIssueをCloseせず、QR正式Pico連携の組込み前に修正する推奨時期と未実装状態を維持する。
- [案件調査と方針案Rev.0](Test_Interruption_20261111/Investigation_and_Policy_Rev0.md)。Host／Mock273件成功。実機未検証、src／tests／firmware変更・配置なし。OI-14／OI-23／USB-SUB-01と関連し、独断でCloseしない。

## USB-INT-01: USB HOST中継基板のピン番号・配線位置（Open、2026-11-19）

2026-11-19最新構成指定: QR用HostはWaveshare RP2350-USB-C、外部測定器用HostはWaveshare RP2350-USB-A（商品コードWAVESHARE-30274）。外部測定器用Hostは開発側にUSB-C、機器側にUSB-Aを使い、外部測定器のUSB-Bへユーザー準備ケーブルで接続する。給電はQR用と同じ外部電源を共用する。既存記録上の電源は多摩電子工業DC5V/2.4Aという申告値で、正確な型番、実電流制限値、分岐保護は未確認。

2026-11-19 ユーザー了承: Pico 2からQR用RP2350-USB-Cと外部測定器用RP2350-USB-Aを使い分ける役割分担を確認した。ピン番号・配線位置や電源条件の未確認事項は引き続き本Issueで管理する。

Pico 2 ⇔ Expander ⇔ 中継基板の部品は秋月電子117585（Pico用20Pピンソケット、リード長3.2mm、左右セット）およびADA-5200（スイッチサイエンス8588、PiCowbell Proto）。Expander CNからピンソケットを介してADA-5200へ接続し、ADA-5200から各Host基板へはんだ付け配線する。RESET信号の存在も指定された。

中継基板はUSB HOSTとPico間の接続位置・配線を明確にする目印で、ハード設計・デバッグ時の説明を補助する。今後開発するUSB CDCと、開発済みQR機能のPico側ポート接続の説明に使用する。既存の設計方針を変更せず、USB CDC自体の実装や開発状態もこの追記では変更しない。

具体的なExpander CN番号・ピン番号、ADA-5200と各Host基板の端子対応・配線位置、ユーザー準備ケーブルの型式・結線、共用外部電源によるQR＋Host＋外部測定器の同時負荷時電流・電圧・配線容量・分岐保護、RESETの接続先・配線位置・制御条件は未確認。回路図／配線表または記録付き実機確認で特定するまで推測で補わない。現物作業の未実施を資料欠落だけから断定しない。

この追記は物理的な配線中継の引継ぎに限定し、既存GPIO割当、通信制御方式、FW、USB HOSTドライバ、RESET制御を変更・追加しない。USB CDC保守通信（OI-15）およびUSB-SUB-01～04とは区別し、OI-17（AD/AR target mapping）を変更しない。詳細は[接続仕様](USB_HOST_Interconnect_Spec.md)。USB-INT-01はOpenを維持する。

| ID | Item | Closure Evidence Required |
|---|---|---|
| USB-INT-01 | USB HOST interconnect pins and wiring locations, including RESET | Confirmed schematic/wiring table or documented physical wiring verification identifying Expander CN, 117585, ADA-5200, QR RP2350-USB-C Host, external-instrument RP2350-USB-A (WAVESHARE-30274) Host, USB-A-to-instrument-USB-B cable, external power, and RESET. |

## USB-SUB-01: QR／7355共通USB下位マイコンと双方向UART（Open、2026-11-10）

2026-11-10図面追記: [追加発注用の接続・GPIO説明図Rev.0](drawings/NF55G_Fixture_20261110_Rev0/README.md)を作成。USBコネクタ撤去／直付け・基板改造の要否は未確定。HOST回路・CC／VBUS、信号引出し、下位GPIO、電源容量・保護、機構固定を現物確認後に確定する。再発注時にはHW-01のSD基板GP4/GP5分離処置・検査も引き継ぐ。今回の説明図を加工確定図としない。

2026-11-10資料収集: Waveshare公式RP2350-USB-C回路図・ピン配置図・RP2350資料、およびSanwa Supply BCR-TC2D1BK取扱説明書を取得し、[資料台帳](../reference/USB_Host_SubMCU_20261110/README.md)に原本、取得元、SHA-256を記録。7355の日本語／英語取扱説明書等と製品銘板図は既存資料を確認した。回路図と実機基板版の一致、USB・給電・ハブ構成、実機のFW／BUS設定・動作、試験用QR等は未確認のため、本IssueはOpenを維持する。

2026-11-10 USBポート割当て固定: 回路図コネクタ名で`Type_C1`をADCMT 7355（ネイティブUSB）、`Type_C2`をBCR-TC2D1BK（PIO-USB）へ割り当て、機器の入替えを行わない。USBハブは標準構成から外す。[治具接続図Rev.3](drawings/NF55G_Fixture_20261110_Rev3/README.md)に回路名付き配線を反映。受入前電源確認、各機器の単体列挙、同時Host動作、UART疎通準備を[初回受入チェックリスト](RP2350_USB_C_First_Acceptance_20261110.md)に記録。Type_C2 CC抵抗の現物設定、両USB Host同時動作、7355の実機USB class／FW／BUSと通信、給電・保護、実基板版との照合は未実施。

- 確定した要求: 今回添付の過去会話で指定されたWaveshare RP2350-USB-Cを使用し、BCR-TC2D1BKと7355のUSB処理を集約。治具Pico 2とUARTでコマンド・データを双方向共有する。ハードが揃ってから開発・デバッグを進める。
- 従来候補RP2350-USB-A／CH9350は履歴。USB-A向けR13等をUSB-Cへ適用しない。CH9350-06の型番未指定という記述は旧時点の状態であり、実機成立の未確認部分は引き続きOpen。
- 未確定: USBポート／ハブ・給電・CC条件、7355 CDC実適合・取得手順、下位UARTピン、治具PIO TX／RX資源、通信速度・フレーム・CRC・要求相関・timeout・再送・再起動、正式ATE API／Cache／CSV、シャント換算担当と測定条件。
- 既存UART0はATE、UART1はNF55G。GP8／GP9でUART1を再初期化せず、PIO双方向UARTを検討する。既存QR用PIO RX／GP8 High固定だけでは指令を送れない。
- [開発準備資料](USB_Host_SubMCU_Integration_Plan_20261110.md)に役割、データ項目、工程、ハード確認・段階試験を整理。詳細設計時に未確定部分を人間確認する。コード変更・新基板ビルド・実機検証・配置は未実施。CAL-EXT-01、OI-14／OI-23と補正関連Issueも独断でCloseしない。

## ATE-EOL-01: CR単独受信の残留と後続コマンドへの影響（Open、2026-11-10）

2026-11-10方針確定: ユーザーが「要求はCR／LF／CRLFをすべて受理、定期CR単独は無視」と指定。旧CRLF限定方針を変更し、空行を無応答で破棄する受信処理へ修正した。応答はCRLFを維持。以下の未確定記述・旧実機結果は修正前の履歴。修正後の検証・配置は[対応記録](ATE_Line_Ending_Fix_20261110.md)を参照。人間確認前のためOpenを維持する。

- ユーザー指定確認項目: INFOのCR／LF／CRLF終端、コマンドなしCR定期送信の無視可否と後続正常コマンドへの影響。
- ホスト確認事実: CR単独は空コマンドとして実行されないが受信状態に残り、後続の正常CRLFコマンド1件がERR:FRAMEとなる。空CRLFは無視される。INFO単体は未登録でERR:UNKNOWN_CMD。
- 未確認・未確定: COM20実機での定期CR送信、SD処理への実際の影響、CRLF限定仕様とCR単独無視要求の扱い。実装変更・実機配置なし。独断でCloseしない。
- 詳細: [ATE終端文字・CR単独の確認](ATE_Line_Ending_Check_20261110.md)。

ATE-EOL-01追記（2026-11-10、Open継続）: COM20実機でD0入口DATA_REFRESHのCR／LF／CRLFを確認。CR／LF単独とCR単独10回定期送信後は、後続DATA_REFRESHが1回ERR:FRAME、次はOK。CRLF・空CRLF後・分割CRLFは正常。最短送信間隔113.966ms、終了時通信IDLE／SD・自己診断OK、破棄0。上記の定期CR実機確認は実施済みとなるが、SD滞留の実測と処置方針は未確定。コード変更なし。[実機結果と処置案](ATE_D0_Line_Ending_Hardware_Test_20261110.md)。

## ATE-TX-01: ATE応答のUART送信・受信確認とログ表現（Open、2026-11-13）

2026-11-14ユーザー確認（未受信問題は解決）: 本日、実ATEと実NF55Gの組合せで総合テストを実施し、前日発生したATEへ値が返らない問題は終端コードの相違が原因と判明。終端をCR（0x0D）へ統一して解決したとの報告を受領した。以下の原因未確定・timeout仮説は確認前の履歴であり、今回の未受信原因として扱わない。関連CSVは`F:/BANK_A/20261114_092525_T000019.csv`。本記録はユーザーによる実機確認に基づき、CSV単独で物理終端やATE受信を証明したものではない。ATE-TX-01のうち未受信原因調査は完了とし、ログの論理RESULTと物理送信証跡の区別、初回ASCII異常、TEST_END後の応答遅延・遅着対応は別の残課題としてOpenを維持する。総合テスト全項目の合否・長時間条件は本報告だけでは確定しない。

- 確認事実: `FixtureApp.execute_ate_line`は応答文字列を生成した後、ATEログへ`direction='TX', event='RESULT'`として記録し、その後`ATEServer.reply`／`flush_reply`へ渡す。したがってCSVの`ATE/TX/RESULT`はCommand Coreの論理結果で、UART.writeの実行・受理量・全byte送信完了・ATE側受信を証明しない。ATEServerは短いwriteの残りを保持するが、受理byte数・残量・送信完了・write例外の証跡をLoggerへ残していない。`ATE/RX/REQUEST`も行組立後の論理要求であり、全受信byteの物理RAW記録とは別。
- 過去の実機事実: COM19で`*IDN?`→`NF55G_PICO_FIXTURE,Rev.0`やATE Query応答を実際に受信した記録がある（`Development_Unit_Command_Debug_20261109.md`、本Real_Hardware_Test_Log内の2026-11-13確認）。したがってPico→ATE経路は少なくとも当該試験時には応答していた。今回の未受信を直ちに恒久的な配線／UART送信故障とは扱わない。ただし過去成功は今回の接続状態を保証しない。
- 追加ユーザー観測（2026-11-13）: NF55G側UART1ではオシロスコープで波形を確認。過去に作成したRB01G経由は問題なし、PC serial通信も問題なしとの申告。ATE向けUART0（GP0/GP1）とPIA5100／GPIB経路の受信確認とは別経路のため、これらの成功だけではATE経路成立を証明しない。調査対象をPico UART0 TX→RS232変換／配線→PIA5100→GPIB→ATEの各区間へ絞るが、故障箇所は未確定。
- Baudrate切替状態: 現行PCソースとPico上`/src/config.py`の`ATE_BAUDRATE=57600`は一致確認済み。ただしconfig転送後にMainを57600bps設定で再起動した実測確認は未記録。起動中に初期化済みUART0はconfig.pyのファイル更新だけでは速度変更されない。Main再起動前にATE側装置・PIA5100経路のbaud／format設定を照合する。
- 2026-11-13再確認: COM19をPCから直接115200bps／8N1で開き、`*IDN?\r\n`を1回送信。受信前残byteなし、`NF55G_PICO_FIXTURE,Rev.0\r\n`を送信後約219msで完全受信した。これはPC→COM19→Picoの直接シリアル経路の単発値であり、実ATEアプリ、GPIB転送、ATE側response timeout／遅着時処理の測定ではない。過去のCOM19正常応答記録と併せ、ATE側timeout仮説を継続確認するが原因確定とはしない。
- 2026-11-13 baud比較: 同一COM19直結・`*IDN?\r\n`を各速度1回、先行RXをclearして比較。57600bpsでは3秒間responseなし。続く115200bpsでは約264ms後に`ERR:ASCII\r\n`を受信し、IDN応答ではなかった。非ASCII応答はbaud／UART framingまたは経路不整合と整合するが、どの要求に対応するbyteか一回比較だけでは確定できない。両速度ともIDN成功とは扱わず、再送・製品コマンドは行っていない。
- ATE timeout仮説: Picoはコマンド処理完了後に応答を生成・送信するため、NF55G TransactionやTEST_ENDのSD flush等がATE側応答timeoutを超えれば、ATEアプリが結果待ちを打ち切る可能性がある。NF55G T1/T2、最大1回のCommand Retry、ATE各コマンドの処理時間・SD処理時間を含めたATE timeout設定は本Issueでは未確認。ATEがtimeout後に受信を継続するか、遅着行を次要求の応答として誤対応しないかも確認が必要。これは現時点の仮説であり原因確定ではない。
- ユーザー観測: 2026-11-13提供CSVではPico側に`ATE/TX/RESULT`がある一方、ATE側で結果を受信できていないとの報告。CSVだけでは実送信・ATE受信・ATE timeoutのどの段階か確定できない。ATE側の実timeout値、送信時刻・timeout時刻・受信raw bytes／CRLF有無と、同一要求のPico側UART処理時刻を突合する。
- T000053所見: `ERP_SET_1_0`／`ERP_SET_0_0`の一部は`ERR:ACK_TIMEOUT`、cmd_retry=1、rsp_retry=0、ambiguous=True。各再試行付近またはTransaction終了後にSE応答らしいNF55G RX frameが記録される。遅延フレームの帰属先と製品への適用有無は確定不能で、設定状態は不明として扱う。状態を明示読戻しで確認するまでSET再送や追加Controlを行わない。
- Clock Sync訂正: T000053の`CLOCK_SYNC 20261109120000`は14桁のため、ATE parserが12桁形式エラーとして無送信拒否した。その後のT000054／T000055では修正入力`CLOCK_SYNC 261109120000`（12桁）が記録され、SC transactionはOK。旧不正入力と修正後結果を混同しない。
- 次の確認: まずATE timeout設定と問題が起きたコマンド名・timeout値を確認し、`*IDN?`等ローカル応答とNF55G Transactionを区別して、ATE送信時刻・timeout時刻・遅着応答の有無を記録する。同時にPico側の要求受付時刻、応答生成時刻、UART.write return値・残byte数・flush完了を採取する。必要ならRS-232側の独立モニターでTX/RXを観測する。UART driver受理はATE受信確認の代替としない。計測自身がTimingを阻害しないことも検証する。
- `ATE,TX,RESULT`を物理送信完了と扱わない。Logger field／eventの名称変更や送信計測実装は、Code／Test／Docs／CHANGELOGを揃えて別途対応する。ATE未受信原因、短write／無受理／線路／相手機器のどこかを断定せず、IssueはOpenを維持する。
- 追加確認方針（2026-11-13）: NF55G UART1のオシロ波形、RB01G経由の正常、PC serial正常というユーザー観測はATE UART0経路の合格根拠に転用しない。ATE baud変更後の実行中UART速度（config.py更新だけでは切替わらずMain再起動が必要）、PIA5100 RS232設定とGPIB側のATE timeoutを確認する。安全なローカル`*IDN?`を1件用い、Pico UART0 TX端、RS232／PIA5100区間、ATE側GPIB受信結果を段階的に照合する。NF55G制御は送らない。

- 初回ASCII追記（2026-11-13、Open継続）: ユーザー確認はPC直結・再起動直後。Host先行7F／FFで初回ASCII異常を再現したが、実機RAM受信観測4条件8件は全件正常、混入なし。UART生成後の起動処理約1秒待ちは別途観測。原因未確定のままとし、実際の再現時raw／PCソフト手順・物理起動条件の照合を残す。[追加確認](Startup_First_IDN_ASCII_20261113_Rev1.txt)。

- 入替え個体追記（2026-11-13、Open継続）: COM6／ID69f7d45962cfdfadを現行一式へ更新し、PC直結の通常起動7件は正常。ただしTEST_END後のLOG_DROP_COUNT?に3201.859msを観測。初回2秒待ちではtimeoutし次要求で遅着0を拾った。10秒待ちで15件成功したが遅延は解消しておらず、ATE timeout・遅着対応・後処理Timingを残件とする。初回IDN914.070msは別観測で原因未確定。[配置・Timing記録](Pico_Swap_69f7d459_Update_20261113_Rev0.txt)。

## LOGGER-BURST-01: ATE連続要求時の試験ログ破棄（2026-11-09、Open）

- 追加条件・実測: ユーザー指定のATE速度は0.1秒に1コマンド程度、これ以上の速度は使わない。101ms以上（実測最短101.0623ms）の117コマンドでは破棄0、239行すべて14列、SD/PC SHA-256一致。以後の実機試験条件へ反映する。無間隔時の391件破棄を撤回するものではなく、長時間・異なる構成は未確認。[再確認記録](CSV_Log_Recovery_Recheck_20261109.md)。

- 開発機COM6／ATE COM20の実機試験で339件の応答をほぼ無間隔に取得したところ、通信自体はD0/D1/D5/EL/OL成功、再送0だったが、TEST_END後のTEST_LOG_DROP=391でSelf Check NG。Logger Queue上限256件、ATE優先のservice_once経路を確認。75ms間隔のCache Query106件では当該試験の破棄0・Self Check OK。
- 量産ATEの要求間隔、記録件数、許容drop数とRAM Queue／SD排出の設計条件を確認する。間隔を空けた結果だけで無間隔の大量要求を許容済みとしない。詳細は[開発機コマンド実機デバッグ](Development_Unit_Command_Debug_20261109.md)。

## LOGGER-CSV-01: PC回収時の欠落による項目別SPのCSV列欠け（2026-11-09、Open）

- `PARAM_EVENT_ENABLE_0`の同値SPは正常応答し、INFOの全26項目とD5の100文字全体は前後一致。SD CSVの当該SP送信RAW行だけ`raw_hex`欄が空で列位置が欠けていた。ログ破棄0。ほかの取得可能なSP/D5フレームはBCC一致。
- 上記は旧PCコピーの観測。再確認でSD原本12657 byteに対し旧コピー12561 byte（96 byte不足）と判明。原本は全201行14列で、分割回収・SD/PC SHA-256一致後は項目別SP送信原文とBCCも正常。SD保存時の列欠けとした見立てを訂正する。一括HEX回収は3回とも32～64 byte欠落が再現。試験用回収を256 byte分割＋長さ・全体SHA-256照合へ変更した。USB/出力/受信の内部欠落箇所は未確定で、独断でCloseしない。[再確認記録](CSV_Log_Recovery_Recheck_20261109.md)。

## DEV-RTC-01: 開発用COM6機のRTC電源断保持（2026-11-09、Open）

2026-11-10保持再確認追記: ユーザーの電源切断・再投入連絡後、RTC_SETなしで09:59:58→10:00:01 JSTの3秒進行、初期日時への戻りなし、PC日本時間との差5秒以内を確認。status=0x08／OSF=0、control=0x1C／EOSC=0。今回1回の電源切断後の保持は成立。実際の電源断時間・電池／VBAT電圧・長時間保持は未測定で、過去不成立の原因は断定しない。人間確認前のためOpenを維持。[受入結果・証跡](RTC_Acceptance_Recheck_20261110.md)。以下の保持確認待ちは試験前の履歴。

2026-11-10向き修正後の受入: ユーザーが誤方向接続を申告。修正後I2C 0x68検出、09:56:35 JST設定・読戻し、10秒進行、OSF=0を確認。通電中の機能は正常。電池保持は通常電源の30秒切断・再投入を依頼中で未確認、Open継続。電池電圧・潜在損傷の有無は未測定。[受入再確認](RTC_Acceptance_Recheck_20261110.md)。

2026-11-10電池取付け後の再確認: ユーザーがRTC取外し・リセット・電池取付けを申告。時刻設定を試みたがRTC_DATETIME?=ERR:NO_RTC、RTC_SET=EIO、I2C0 GP20/GP21の検出アドレスは空配列。再装着・給電・接触等は未確認で原因を断定しない。時刻設定・読戻し・電源断保持とも未完了。Open継続。[再確認記録](RTC_Battery_Recheck_20261110.md)。

- 追加確認17:12 JST: RTC_SETで20261109_171043を設定・読戻し後、ユーザーが30秒電源断。3回目も20000101_000056→000057、status=0x88、check=True。再設定せず読取り、保持不成立を確認。原因未確定・Open継続。証跡: temp/dev_acceptance_20261109_run01/cold_run03.json。

- 対象はunique_id=69f7d45962cfdfadの開発機。COM14機のRTC保持実績と混同しない。
- 確認事実: 新規装着後にI2C0の0x68を認識し、PC日本時間設定・読戻し・秒進行は正常。時刻設定後、ユーザーが約30秒の電源断・再接続を実施した2回ともRTCが20000101へ戻りstatus=0x88（OSF再セット）。再設定時のcontrol=0x1C、EOSC=0を確認。設定後status=0x08、2.1秒進行も正常だった。
- ユーザーから「新しいRTCなので設定が必要」と回答があり再設定したが、2回目も保持不成立。設定不足・電池不良・基板故障等を断定しない。電池の装着・絶縁・向き・接触・電圧、VBAT給電経路の現物確認・実測が必要。
- RTC_CHECK / Self CheckのRTC=OKはアクセス・日時検証であり保持合格を意味しない。今回は既存ドライバを変更せず、独断でCloseしない。詳細・証跡は[開発機受入記録](Development_Unit_Acceptance_20261109.md)。

## ATEコマンド一覧 Rev.1照合時の確認事項（2026-11-09）

- ATE-CLEAR-01（Open）: ユーザー提示の試験指示書§7.5はCLEAR_DATA / CLEAR_LOGを指定する。現行ATEにはCLEAR_ALL / CLEAR_POWER / CLEAR_BATT / CLEAR_LOGがあり、CLEAR_DATA同名コマンドはない。CLEAR_DATAの消去対象と既存CD DATA0 / 1 / 2との対応、量産での実施条件を確認する。CLEAR_ALLの別名と推測せず、Picoへの自動対応・新規コマンド追加は行わない。
- OI-23追加確認（Open継続）: 同指示書§7.1の「UNIT_REV～BBU_SRLまで、それ以降は0000」を要求として保持する。「それ以降」の対象画面項目・通信領域・桁数との対応は未確認。一律ゼロ埋めするSSデータを推測生成しない。9項目のSS書込み対象とFW_REVISION照合の既定方針は変更しない。
- 今回はATE設計者向け一覧への記録であり、通信仕様・実装を変更せず、既存IssueもCloseしない。詳細はATE_Command_List_for_Test_Program_Rev1_20261109.md第14.2 / 14.6節を参照する。

## BE-ACCEPT-01: 非バックアップ状態でのBE受付（2026-11-09、Open）

- 確認事実: r1 p.17はBEの受付をPS_OFF=不可、バックアップ中=可と記載。今回D1でPS_ON=1／BATT_ON=0を確認後、10:29:53 JSTにBACKUP_ENABLEを1回送信したところ、SQEでなく正常応答DATA15文字・OK（26ms、再送0、BCC一致）だった。前後のD1全フィールドは一致し、BACKUP_READY=1を維持。バッテリ未接続はユーザー報告。元PARAMはPS_ON_BACKUP=1。
- ユーザー観測: 出力変化・瞬断・再起動なし。電圧数値・波形は未提示。
- 未確認: 受付条件とPS_ON／BATT_ONの対応、r1 p.23の待機状態説明およびp.43の装置動作例との解釈、今回FWと最終仕様との整合。設計担当者の回答が必要。今回だけで製品FW不具合とは断定しない。
- 方針: PicoでOKをSQEへ置換せず、実応答を保持する。BF・OR・停電操作を追加して辻褄を合わせない。バックアップ中のBE正常動作・実放電は未確認。詳細は[実機記録](Real_Hardware_Test_Log.md)、[証跡](../temp/hil_backup_enable_20261109_run01/result_summary.json)。

Revision: Rev.0
Codex must NOT close these by inference.

## D4受信Timingの実機確認 2026-11-09

2026-11-09ユーザー指定: 副作用があるためD4は量産では使用しない。以下のTiming問題はCloseせず、保守時の課題として保持し、CLEAR試験を優先する。

- D4-TIM-01（Open）: D4_MAINT_READを2セッションで確認し、両方ACK_TIMEOUT、command retry 1、response retry 0、ambiguous=True。D4／DATA CacheはINVALID。T2=100msは変更していない。
- 確認事実: ACKはTXの6／7ms後。再確認ではACKから約102ms後、218byteフレームの170byteを部分RAWに記録。直後のCommand RetryのACK待ちでは0x20を観測し、最終ACK_TIMEOUT。後続の完全D4フレームはDATA212文字・BCC一致。elapsed114／115ms。
- 推測: T2内に応答処理が完了せず、再送時に前応答と競合している可能性。送出開始／完了、UART残量、Pico CPU負荷の寄与は未確認。FW違反と断定しない。
- 要確認: r1のT2定義と最終FW Timing、線上のACK／応答時刻、Pico受信バックログと処理負荷。Pico上のPython Mock再生もRESP_TIMEOUTだが、Mock負荷があり実UARTの証拠ではない。
- T2延長・遅延D4のCache昇格・ACK仕様変更はしない。設計確認後に再試験する。実測はtemp/hil_20261109_run01/events.jsonl。独断でCloseしない。

## 2026-11-09 試験ログ・自己診断の追加要求への対応

- OI-14／OI-23の一部要求をユーザー確認: ログ用S/NはTEST_START後に読むQR末尾6桁、命名はS/N＋開始日時、未取得時は日時維持。共通コアのRAM連携と終了時リネームを実装。両IssueはCloseしない。
- 未完了: 新USBホスト／物理受信ループ／正式QR ATEコマンドの接続、実カードでの命名・抜き差し・close・復帰・Timing検証。QRとSSの対応は今回確定していない。
- TEST_ENDの装置Self Checkを追加。SD異常でも試験受付を継続し、製品判定と装置診断を分離。既存CMD0不具合は未解決のまま。

## D2とPS_ON受付条件の確認 2026-11-07

- D2-PS-01（Open）: r1 p.18 §7.2(2)はPS_ON時にシーケンス／パラメータエラーを返さないと記す一方、p.17 §7.1注1はPS_ON後SET CLOCK処理完了までD2を受け付けないと記し、p.32 §10.6.1はSET CLOCK受信前にシーケンスエラーを返すと明記する。総則とD2個別条件の適用関係、SC未完了時の実FW応答を設計確認する。Pico側でSC自動送信や受付条件の補完を追加せず、独断でCloseしない。詳細: [D2とPS_ONの影響確認](D2_PS_ON_Review_20261107.md)。今回実機試験は未実施。
- 2026-11-09開発機追記: PS_ON=1。SC前のD2は2回ともBCC一致のSQE、現在時刻でCLOCK_SYNC（SC）成功後のD2はOK・DATA30文字、再送0。SC未完了条件との整合があるが、SC前の製品内部状態は未観測であり単独原因とは断定しない。原典p.18総則とp.17/p.32個別条件の整合確認は継続する。[実機記録](Development_Unit_Command_Debug_20261109.md)。

## 外部測定値による補正の追加要求 2026-11-04

- CAL-EXT-03（Open）: ユーザー指示により7355の通信仕様・アドレス設定を仕様化対象へ追加。採用GPIBアドレス、設定／保持／照合方法、ADC／SCPI選択、正確なコマンド、終端／EOI、応答表現、測定・timeout設定、異常復帰を確定する。メーカー製品ページではGPIBが+01オプション、ADC／SCPI対応と確認したが、実機搭載・マニュアル本文は未確認。値を推測で設定しない。GPIB制御経路はCAL-EXT-01と併せて確認。

- CAL-EXT-01（Open）: ユーザー指定はPico 2 UART0↔PIA5100↔GPIBのATE接続と、7355による外部シャント抵抗／製品電圧の測定。測定対象はATEが制御する。GPIB制御権、PIA5100のモード、7355読出し手順、ATE指令と測定応答の識別・中継方法は未確認。接続構成だけでPicoからの直接読出し可能と断定しない。
- CAL-EXT-02（Open）: 2026-11-04ユーザー確認により①DISCHG_I／充電、②BATT_CHG／放電は記載どおりで確定。取得と書込みは別コマンドとし、読取値を一旦ATEへ返して判定した後、ATEが改めて書込みコマンド＋数値を送る。取得による自動書込みは行わない。残事項はA/BとP1/P2対応、シャント換算の担当・符号・丸め、返却値の形式・単位、測定の鮮度、正式コマンド／応答／失敗時動作。既存AD/ARのOI-04/OI-05/OI-16～OI-21はOpenを維持する。
- 詳細: [追加要求記録](Calibration_External_Measurement_Requirements_20261104.md)。要求整理のみ。実装・機器仕様確認・実機試験は未実施。

## RP2350-USB-A QR入力経路の調査 2026-10-14

- RP2350-QR-01（Open）: THLN33のHID→ASCII/UART公開実装とWaveshare公式HID→ASCII/USB CDCデモを取得・ソース確認。THLN33は13byteバイナリ出力・AZERTY有効のため既存35文字＋LF受信とは互換でない。文字列UART出力への変更、リーダ配列・レポート形式、依存版の整合を確認する。ビルド・実機試験は未実施。
- RP2350-QR-02（Open）: 実装者からR13除去とD+/D-各15kΩプルダウン追加の報告あり。今回基板の版・回路・実装との一致は未確認。改造要否を推測で確定しない。電源容量・再接続・電源再投入の安定性も評価する。
- 詳細: [RP2350-USB-Aサンプル調査](RP2350_USB_A_HID_UART_Research_20261014.md)。OI-14/OI-23およびCH9350評価課題はOpenを維持する。

## 既存の未確定事項

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
過去のAD/ARレビューにあるD6参照は当時の比較記録として保持する。r1への基準切替は既存Issueの解決・Closeを意味しない。

| ID | Issue | Rev.0 implementation |
|---|---|---|
| OI-01 | Pico-side T1 final value | 200 ms provisional |
| OI-02 | r1のD0 T2一覧300ms／個別600msはr2で300msへ統一 | 2026-11-11ユーザー指定により300ms採用・配置済み。S1.13正常系10回はACK後180～182ms・再送0。異常系・長時間・量産全条件は未確認、Open継続。 |
| OI-03 | Current FW may clear CHARGE_END after D0 ACK | retain existing non-destructive D0 policy; confirm r1/final FW interpretation |
| OI-04 | AR REF/value8 final wire format and ATE return policy | Fixture draft keeps REF as raw8/open; interim FW appears to use IEEE754 float raw HEX. Decide raw/decode/both before final ATE release. |
| OI-05 | AD runtime coefficient immediate reflection vs reboot | Interim FW writes EEPROM and computes response-local slope, but runtime coefficient globals may not update immediately. No automatic reboot; confirm final behavior. |
| OI-06 | BC=0 STOP current FW behavior | implement spec; confirm final FW |
| OI-07 | BC MODE=13 response details | expose received data; confirm |
| OI-08 | SL out-of-range PME behavior | 2026-11-09: 正式LIFE_SET／RAW入口を実装、範囲外も無補正送信。PMEと読戻しはSample準備後に実機確認。量産使用未確定、Open継続。詳細は下記SL記録。 |
| OI-09 | OR request while restart already active | current FW SQE; confirm |
| OI-10 | FD out-of-range address | current FW FF fill; confirm formal behavior |
| OI-11 | EB timing while command transaction active | keep original deadline; HIL confirm |
| OI-12 | AR T2 final value | confirm before final release |
| OI-13（Resolved、2026-11-13） | RTC HAT revision pin mapping | ユーザー確認により現行I2C0 SDA=GP20／SCL=GP21で問題なく、ピン競合なしとして解決。実装・Software_Module_Interfaceと一致し、2026-11-10実機で0x68検出・日時設定／読戻し・秒進行を確認済み（RTC_Acceptance_Recheck_20261110.md）。HW-01のSD基板GP4／GP5分離、およびDEV-RTC-01の保持確認とは別件。 |
| OI-14 | QR Cacheからのログファイル名生成 | 2026-09-18ユーザー指定によりQR読取Cacheをログファイル名に利用する。採用フィールド、命名形式、使用不可文字、重複時処理、未読時処理、TEST_STARTとの順序は未確定。OI-23参照。Openを維持する。 |
| OI-15 | Detailed USB CDC/PySide6 protocol | deferred phase |
| OI-16 | AD request/response wire format mismatch | Fixture draft defines AD as 10-char DATA control/set command; interim FW request is `TYPE1+POINT1+VALUE8` and success response is `TYPE1+POINT1+ADC6+CALC8`. Confirm r1/production FW/design expectation. |
| OI-17 | AD/AR target mapping and 12VOUT_I coverage | User confirmed on 2026-11-19 that the product FW fixed value reflects FW design intent and is not listed as an inspection item in the test procedure. Keep OI-17 open for traceability, but it does not block fixture development. Do not infer new AD/AR behavior or change product FW. |
| OI-18 | AD POINT/VALUE validation and rejection policy mismatch | Fixture docs leave POINT/VALUE validation open; interim FW uses POINT `1/2`, clamps out-of-range VALUE, and may not explicitly reject unsupported TYPE/POINT. Define final PME/SQE/clamp behavior. |
| OI-19 | AD persistence/write timing and EEPROM error behavior | Interim FW stores `correct_t` to EEPROM and returns after write check; final commit timing, busy behavior, retention, write-cycle limits, and HWE behavior need confirmation. |
| OI-20 | AR response length/order final confirmation | Fixture draft and interim FW both indicate 140 DATA chars: five targets x two points x `(ADC6 + REF/value8)`. Verify final production FW order/length before fixing ATE query behavior. |
| OI-21 | AD calibration preconditions and HIL acceptance criteria | Fixture docs assign PASS/FAIL to ATE and external measurement; interim FW has no visible AD-specific state checks. Define allowed state/load/output/charger interlocks and measurement correlation criteria. |
| OI-22 | r1 BOOT update interruption recovery wording and procedure | r1 p.37 section 12.5.2 removes D6 automatic recovery within 1 second and requires BOOT retry writing, but the introduction still describes differing automatic-recovery availability and (1) duplicates USER wording in (2). Design must confirm the supported recovery sequence and applicable FW. FU remains prohibited in the Pico fixture; this does not block ordinary communication development. See `RW11_D6_to_R1_Impact_Review_20260907.md`. |
| HW-01 | ADA-5703 GP4/GP5 and Pico-2CH-RS232 UART1 pin conflict | Adafruit ADA-5703 PiCowbell PCF8523 RTC/I2C circuitry is physically connected to GP4=SDA and GP5=SCL, while Waveshare Pico-2CH-RS232 fixes NF55G UART1 to GP4=TX and GP5=RX. 2026-09-04 real-hardware SD/RTC tests were performed with ADA-5703 GP4/GP5 physically isolated. Keep open until the final fixture physical cut/isolation method and inspection record are formally documented. |
| OI-23 | QR読取・Cache・NF55G書込み連携 | 2026-09-18ユーザー指定: 製品銘板図 NF55802-G_01.pdf のQRをリーダで読み、かんたんUSBホスト HIDキーボード用を介してPicoへ取り込む。ATEの読取開始コマンド後に読み取り、Pico側にCacheする。読取開始はPico専用コマンド。後続のATE指示によるNF55Gファームウェアのコマンドでの書込み、およびログファイル名にCacheを利用する。読取による自動書込みは行わない。詳細は QR_Reader_Requirements.md。銘板PDFとUSBホストマニュアルはreference/local_hardware_reference_20260904/required_for_development/に保存済み。2026-09-26に銘板図とUSBホストの受信関連仕様を確認。資料入手のみで本IssueをCloseしない。桁数は品名8桁・品目コード14桁・REV3桁・製造年2桁・製造週2桁・製造号機6桁（項目合計35桁）をユーザー指定として記録。2026-09-26: ユーザーが6項目の配置順と区切りなし35文字、英数字とハイフン許可を指定。単独QR受信・分割・一時Cache・REPL試作を先行し、SS連携は別工程とする。未確定: 許容範囲、年の解釈、正式ATEコマンド/応答/timeout、Cache名と寿命、USBホスト〜Picoの接続/ピン/電気条件、SSへの各フィールド対応、ログ命名規則。書込みコマンドはSSに確定し、保存Cache名は後日ユーザーが決定して紐付けを具体化する。生産LOT・生産年月・S/N情報の書込み範囲はUNIT_REV～BBU_SRLとユーザー確認。QRの製造年/製造週と「生産年月」の関係および各項目への割当ては未確定で、週から月を推測しない。提示SET_SERIAL画面のSS対象はUNIT/ADU/BBUそれぞれのREV・LOT・SERIALの9項目（画面SRLは既存SERIALに対応）。FW_REVISIONはFW書き込み仕様書のREVSIONと一致するかの照合のみで、SS対象外。比較元仕様書のファイル/版/期待値、比較規則、照合担当は未確定。QR REVは製品REVとしてUNIT_REVに対応し、FW_REVISIONとは別項目。QRの製品REV3桁と通信仕様r1 p.22 §8.5.3のUNIT_REV4バイトとの差異はユーザー認識済み。ラベルと通信仕様の整合および3桁から4バイトへの格納・変換方法を確認事項として継続管理する（末尾文字・空白等を推測補完しない）。年/週からLOTへの対応、号機からSERIALへの対応、ADU/BBU値の取得元は要確認。表示された末尾ピリオドやゼロ値を自動補完・既定値として採用しない。ユーザー提示の工程案はQR_SCAN/QR_GET/QR_PARSE/QR_DATA/既存WRITE/必要時READ/QR_VERIFYまたはATE照合。分解・桁数/文字種/範囲検証・書込み変換・CSVへの原文/解析値/書込み結果記録・ATEへの異常コード返却を要件として追記。名称は案。照合担当、リーダ開始指示方式、変換規則、エラーコード表、CSV列/試行識別も未確定。Picoでの一致照合を採用しても製品PASS/FAILはATEが判定する。従来のBLE案は今回の採用経路ではない。Openを維持。今回のユーザー許可によりQR単独試作のみ先行し、正式Cache/SS連携は保留。2026-09-26ユーザーがGP9←TX1/GP8→RX1/GND接続完了を報告。COM14でPIO初期化成功。テスト機はユーザー指定OPTICON L-46X。COM10=ATE、COM14=REPL。Pico VBUSからHOST VBUSと5V両方への給電接続完了をユーザー確認。HOST 5V/VBUS給電はユーザー確認OK（数値未提示）。D1/D2取り違えの可能性により以前のホストHID認識済み判断は撤回、現在D1点灯/D2消灯の報告。ATE開始受付は確認済みだがQR受信0byteでtimeout。通常USBキーボード接続ではD2点灯をユーザー確認。ABC+EnterについてPico実測4byte（ABC+LF）、QR_LENGTHを確認し、キーボード→ホスト→GP9受信経路の動作を確認。後続再試験で35文字+LF受信、6項目分割、RAM Cache READYとREPL表示まで成功。実測原文はUS250A-CGXE-009491-10101A2623000001。その後ユーザーが電源切/入でD2消灯再発、QRリーダ初期化を報告。初期化操作は電源投入時のトリガ10秒以上長押しとユーザー確認。メーカー作成第5版p.22 §3.1.4で強制起動中はホストへ読取データを出力しないことを確認。通常起動と区別する。保存設定への影響の詳細と認識再発の根本原因は未確定。電源操作対象/順序と、通常起動後USB挿入との比較は未確認。その後、キーボード接続→取り外し→L-46X接続でD2点灯するとユーザー報告。キーボード取り外し時のD2消灯とL-46X接続時の再点灯をユーザー確認済み。前機器の表示残留とは区別できた。L-46X単体の抜き差しではD2が点灯しないこともユーザー確認。キーボード認識を先行させる条件との差を優先調査する。今回状態での実データ再受信と、電源投入直後との差の原因は継続調査。認識改善の要因・給電品質・安定性は未確定。正式Cache/SS連携等を含む本IssueはOpenを維持する。手順はQR_Receive_Test.md。 |

## AD/AR consolidated review notes

Reviewed documents:
- `AGENTS.md`
- `README.md`
- `docs/ATE_Command_Master.md`
- `docs/ATE_Command_List_for_Test_Program.md`
- `docs/Data_Decode_Master.md`
- `docs/Cache_Master.md`
- `docs/Protocol_State_Machine.md`
- `docs/Software_Module_Interface.md`
- `docs/Test_Specification.md`
- `docs/Implementation_Plan.md`
- `docs/Program_State_Transition_Diagram.md`
- `docs/Real_Hardware_Test_Log.md`
- `docs/CHANGELOG.md`
- `reference/RW11用電源通信仕様書d6.pdf`
- `reference/NF55G_試験治具仕様書_Rev0_正本.docx`
- `reference/NF55G_試験治具仕様書_添付資料_CN24通信ハーネス結線表.docx`
- `reference/NF54191-G_S1.docx`
- `reference/開発手順(ChatGPT→Codex引き渡し).docx`

Interim FW source checked:
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_define.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_tbl.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_serial.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_global.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_global.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_input.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_init.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_eeprom.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_eeprom.c`

Consolidation map:
- OI-16 merges former OI-16, OI-20, and OI-29. The issue is one wire-format mismatch: fixture draft command/response expectation vs interim FW implementation.
- OI-17 merges former OI-17, OI-24, and OI-32. The fixed-value behavior for `12VOUT_I` is user-confirmed as product FW design intent and is not a fixture-development blocker; retain the issue as an open mapping record.
- OI-18 merges former OI-18, OI-19, OI-27, and OI-28. The issue is one validation-policy question: accepted POINT/VALUE range and error/clamp behavior.
- OI-19 keeps former OI-21. Persistence/write behavior is separate from protocol field layout.
- OI-20 keeps the AR order/length part of former OI-24. REF representation and ATE return policy are tracked in OI-04 to avoid duplication.
- OI-21 merges former OI-22 and OI-26. Calibration preconditions and HIL acceptance belong together because both must be confirmed with production FW and design.
- OI-05 absorbs former OI-23 and OI-31. The issue is one reflection-timing question: EEPROM update vs runtime coefficient update vs reboot.

Detailed AD/AR differences:
- AD request/response format: `ATE_Command_Master.md` and `ATE_Command_List_for_Test_Program.md` define ATE command `AD_<TYPE>_<POINT>_<VALUE>` mapped to NF CMD `AD` with 10-char DATA, while interim FW parses DATA as `TYPE1 + POINT1 + VALUE8`. Current fixture docs treat AD as a control/set command, but interim FW returns success DATA `TYPE1 + POINT1 + ADC6 + CALC8`. Final production FW/D6-design expectation is not yet confirmed.
- AD VALUE/AR REF numeric representation: fixture docs intentionally keep AR `REF8` raw/open and do not finalize AD VALUE encoding. Interim FW uses `aschex_to_float()` and `float_to_aschex()`, which indicates IEEE754 float bit pattern encoded as 8 ASCII HEX chars. Endianness, ATE decoded display, and raw preservation policy must be decided.
- AD target mapping: fixture decoder and interim FW both indicate five calibration targets: `DISCHG_I`, `BATT_V`, `ACDC12V_V`, `BATT_CHG`, and `12VOUT_V`. `12VOUT_I` has a fixed product-FW coefficient rather than an AD/AR EEPROM record. The user confirmed this reflects FW design intent and is not listed as a test-procedure inspection item. Keep OI-17 open for traceability, but do not block fixture development or add calibration behavior by inference.
- AD POINT/range handling: fixture docs leave POINT and VALUE validation as open design items. Interim FW maps POINT `1` to `point1/ad1` and POINT `2` to `point2/ad2`; unsupported TYPE/POINT may fall through without explicit PME/SQE, and out-of-range VALUE is clamped rather than rejected. Production FW must define whether invalid input is rejected, clamped, or treated as sequence/parameter error.
- AD persistence and reflection timing: interim FW writes calibration records to EEPROM and checks write completion, but successful AD appears to calculate response-local values without visibly updating runtime measurement coefficient globals such as `gf_batt_v_coeff`. This differs from an ATE expectation that immediate `AR_REFRESH` or subsequent measurements reflect AD. Confirm whether reboot, re-init, delay, or explicit refresh path is required.
- AR response shape: `Data_Decode_Master.md` defines AR as 140 DATA chars: five systems x two points x `(ADC6 + REF8)`. Interim FW matches 140 DATA chars and full frame length 146, ordered `DISCHG_I`, `BATT_V`, `ACDC12V_V`, `BATT_CHG`, `12VOUT_V`. This agreement still needs final production FW confirmation before the ATE query behavior is fixed.

Implementation cautions for AD/AR:
- Do not translate between tentative FW behavior and r1/design intent inside Pico. If interim FW behavior differs, expose it as an Open Issue and confirm with production FW/design.
- Keep AD implementation provisional until OI-16 through OI-21 and OI-04/OI-05 are answered. Parser strictness should follow the confirmed final format, not Codex inference.
- AD success or ambiguous failure must invalidate `DATA` and `AR`. ATE individual Query must not auto-refresh; ATE must explicitly run `AR_REFRESH` after AD.
- Do not update `AR` cache from AD response data unless final FW explicitly defines AD response as AR-equivalent.
- Do not update `STATUS` or `INFO` cache from AD/AR side effects, response status, D0 embedded status, or EB events.
- Treat AD `OK` as protocol success only. Calibration correctness, product behavior, and measurement PASS/FAIL remain ATE/design responsibility.
- For HIL, log raw AD frame DATA, AD result, retry counts, ambiguous flag, elapsed time, AR raw response, decoded ADC values, REF raw values, and external measurement values.
- Before final release, test each AR system, P1/P2, nominal/min/max/out-of-range AD values, malformed AD fields, power-cycle retention, immediate AR after AD, delayed AR after AD, and reboot-required behavior if applicable.

## 2026-09-26 キーボード経由の比較ログ
ユーザー操作: L-46Xを外す→キーボードD2点灯→外す→L-46X再接続でD2点灯。COM14 TX0診断にも対応する接続/切断を確認（LOSS表示なし）。
- 約221秒: Dell KB216 Wired Keyboard、VID/PID 413c/2113、EP0最大8byte、interface 2個。Report要求後にUsage Keyboardとreport解析内容が出力され、CALLBACK: 1 keyboard(s) now connected。
- 約228秒: disconnect, 0 keyboard(s) now connected。
- 約232秒: Opticon USB Barcode Reader、065a/a001、EP0最大64byte、interface 1個。Requesting report from interface 0から約294ms後にattach callback。Usage/Report解析ログは今回もないがCALLBACK: 1 keyboard(s) now connectedが出力された。
- 先のD2消灯時もReport要求→attachが約293msで、解析ログなし。違いはkeyboard登録の有無。
取得済み公開コードとの照合: udev_hid.cのhiddevice_init_endpointはgetHIDDeviceReportの戻り値を無視する。Report取得エラーは解析前return。USBHost.cの確認した切断/再登録経路はiface usageをクリアしておらず、main.cの登録判定はiface.usage == Usage_KEYBOARD。従って前のキーボードのUsageが残り、Report取得が正常化しなくても登録される仮説が今回の差を説明する。実機FW同一性・実際のReport転送結果/長さ未確認のため原因確定ではない。
従前の「単なるD2表示残留ではない」は維持するが、新規登録の根拠に前機器の内部情報が残留する可能性は別問題として追加。D2点灯を完全なHID初期化成功とは扱わない。
次に専用診断を継続したままQRを1回読み、TX0のKeyEvt等を確認する。これはキー入力経路の診断であり、QR Cache/35文字受信の再試験ではない。HOST設定/FWは変更しない。

## CH9350副作業: 新HID-UART基板（2026-10-11）

- CH9350-06機器指定（2026-11-09、Open継続）: ユーザー提示画像から今回のQRリーダーをサンワサプライBCR-TC2D1BKと記録。公式仕様はUSB HID／Type-C／動作時230mA。Waveshare＋ハブ案のType-C下流データ接続、給電、HIDレポート・配列・終端、35文字受信、7355との共存を確認する。旧L-46Xの動作実績と区別する。

- CH9350-06最新方針（2026-11-09、Open継続）: ユーザー指摘によりQRと7355の両機能をWaveshare側で扱う。QR用CH9350を残す直前の案を修正。RP2350-USB-A 1枚＋USBハブでHID／CDCを共存させる案を優先検討する。TinyUSBとPico-PIO-USBのHID／CDC／Hub対応は資料確認済みだが、今回の機器・ハブ・基板版での同時動作は未検証。機器識別、バッファ、給電、切断復帰、治具との共通通信形式・Timingを確認し、型番・配線・正式APIは未確定のまま維持する。以下の追記は方針変更の経緯として保持する。

- CH9350-06追加指示（2026-11-09、Open継続）: 7355用追加マイコンはWaveshare製を使用する。型番は未指定で、RP2350-USB-Aを第一候補として提案。CDCホスト用C/C++実装、基板版・R13・VBUSの確認、7355との単体通信、治具へのUART／PIO接続とTimingが未検証。公式HID→CDCデモのCDCはPC向け出力で、測定器側CDCホスト対応の確認とは扱わない。詳細は[開発案](CH9350_QR_DMM_Plan_20261109.md)。

- CH9350-06追記（2026-11-09、Open継続）: ユーザーが測定器をADCMT 7355、接続をUSBと確定。保存済み英文取扱説明書§6.4（PDF104ページ）でUSBTMC／CDC対応を確認。CH9350はキーボード／マウスHID用のため、記載機能では7355のUSB制御に対応しないと判断。7355用のCDC／USBTMC対応USBホスト構成、実機FW・BUS設定・通信手順、既存ATE通信との共存は未確定。人間による構成確認・選定が必要であり、IssueはCloseしない。

- CH9350-06（Open、2026-11-09）: ユーザーからCH9350でQR読取とマルチメーター制御の両方を行いたいとの変更意向あり。CH9350はHID用途であり、7355等のUSB測定器制御への対応は未確認。測定器型式・USBクラス・転送方式、基板数と接続構成、従来PIA5100／GPIB経路の置換範囲を確認する。詳細は[変更要求記録](CH9350_QR_DMM_Plan_20261109.md)。対応可能とは確定せず、実装・正式仕様の切替えは未実施。

- CH9350-01（確認済み）: 2026-10-11ユーザー訂正により対象ICをCH9350と確認。状態2/3/4の11byteキーボードフレーム用デコーダと合成試験を追加した。販売基板固有仕様と実機互換性の確認は継続する。
- CH9350-02（Open）: GP4/GP5 UART1はNF55G専用として保持する。CH9350試験はGP9=PIO0/SM0受信115200bps/8N1、GP8=送信禁止High固定へ割り当てる。GP8/GP9のハードUART1機能は使わない。販売基板のTX電圧、DIP対応、電源容量、RX接続条件は未確認。既存QRのGP9/9600bps PIOの成功を新基板115200bpsの成功とみなさない。
- CH9350-03（Open）: CH9350資料p.7に下位機・状態2/3/4の単方向通信ではRXDをGNDにする条件あり。READMEのUART RX/TX接続候補との差は販売基板仕様と実動作で確認する。未知の基板端子を独断で短絡せず、モード/状態通知の応答要否も推測しない。
- CH9350-04（Open）: 評価基本設定をSEL=H/S1=H/S0=L/BAUD1=H/BAUD0=HのEVAL-CH9350-STATE2、量産候補を同論理のPROD-CH9350-STATE2として記録。販売基板DIP番号とON/OFFから各論理への対応は未確認で、現物測定後に確定する。量産候補は連続読取・再接続・電源再投入・電気評価の合格後に承認し、作業者判断で切り替えない。詳細はCH9350/docs/dip_switch_settings.md。
- CH9350-05（Open）: 評価基板固有の回路図・取扱説明書・DIP設定表は未入手。2026-10-11ユーザーから、販売ホームページ記載内容を基に基板情報をメモした旨の説明あり。DIP搭載、端子表示等はユーザー提供情報として記録し、ホームページ画面・記載日時・DIP設定表原文は未保存。ICデータシート確認事項および現物測定結果と区別し、記録がないことだけで仕様や設定を断定しない。
- 手順/結果: CH9350/docs/test_environment.md、CH9350/docs/test_results.md。OI-23および旧USBホスト調査はOpenを維持。NF55G既存プログラムとPico main.py/boot.pyは変更・配置していない。

## ERP-CONDITION-01: バースト実動作の外部条件・復元入口（Open、2026-11-09）

- 確認事実: r1 p.21のSE DATAはBURST 1文字＋PS_OFF_CHARGE 1文字＋RESERVE 2文字。低消費電力設定は1000。0000はPS_OFF充電も無効。p.30のBURST_ONはBURST信号の受信状態でバースト有無に依存しない。
- 確認事実: 実装済みATE入口はERP_SET_1_0／ERP_SET_0_0のみ。p.21の両初期値1に相当する1100や0100は未実装で、元のPS_OFF_CHARGE=1へ今回の2入口だけで復元できない。
- 未確認: 最終NF55G仕様に基づくBURST入力の論理・極性、PS_ON／PS_OFF・負荷とバースト開始／解除の条件、遷移時間、消費電力判定値、Sample条件。通信仕様から未記載条件を補完しない。
- 人間確認事項: 実機試験の信号・負荷条件と最終設定／復元方針。充電有効の比較・復元を試験範囲とする場合はERP_SET_0_1／ERP_SET_1_1入口の必要性を確認する。現段階では自動追加・実機送信せず、独断でCloseしない。
- 詳細: ATE_Command_Master.md「ERP DATA各桁と追加条件の原典照合」、Test_Specification.mdのSample試験手順。

ERP-CONDITION-01追記（2026-11-09、Open継続）: ユーザーが充電有効の2入口の追加を指示。ERP_SET_0_1／ERP_SET_1_1を実装し、全4組合せのHost／Mockを確認したため、上記「復元入口未実装」は過去時点の状態となる。現在は保存済み両設定に対応するコマンドで明示復元可能。実機の信号・負荷・充電条件、最終設定方針、Sample試験と保持は未確認であり、IssueはCloseしない。

## READ-FD-01: r1のFDフレーム表の文字コード不一致（Open、2026-11-09）

- 確認事実: r1 p.37 §12.7は本文・見出しでCMD ID=FDを指定する一方、要求／応答のバイト表は46h 30h（F0）となっている。ATE_Command_Masterと既存decode_fdはFD・64 ASCII HEXを定義する。
- 実装方針: 本文のIDとMasterに合わせFDを送信し、F0への自動切替や応答置換を行わない。FD READはHost／Mockで確認し、実機送信は設計側のID確認後とする。
- 未確認: 最終仕様／FWの正式ID、表記の訂正有無。担当者確認を要し、誤記とは断定しない。OI-10（範囲外アドレスの応答）もOpenのまま。ERPと併せた後日の実機デバッグ予定に含めるが、この確認事項を解消した扱いにはしない。

READ-FD-01関連補足: r1 p.34のOL応答もCMD ID欄見出しはCD、本文とバイト列はOL（4Fh 4Ch）となっている。実装は本文・バイト列一致のOLを採用し、CDへの応答置換はしない。原典表記の設計確認対象として記録し、訂正やIssue Closeは行わない。

## PARAM-IR-01: CHG_IR_THDの値0の意味確認（Open、2026-11-09）

- 確認事実: r1 p.19のCHG_IR_THDは範囲0～4094で、0に「電源初期値」と「検出停止」の両記載がある。初期値欄は0（判定しない）、p.20も初期値では本判定を実行しないと記載。
- 未確認: 値0が内部既定値参照なのか常時検出停止なのか、最終仕様／FWでの定義と保持・読戻しの意味。将来の内部初期値変更を含めて同一機能と断定しない。設計担当者の確認を要する。
- 方針: 項目別設定は通常10項目を先行し、CHG_IR_THDは値にかかわらずERR:PARAMETER_UNCONFIRMEDで無送信拒否。他項目の設定時にはCHG_IR_THD欄をFFF（変更なし）にする。原典を変更・補完せず、独断でCloseしない。既存50文字一括PARAM_SETは従来の契約を保持し、今回新しい値を実機へ送信しない。

2026-11-09 OI-06／OI-07追記（Open継続）: BATT_CHECK_START／STOPと8結果Queryをr1に基づき実装。STOPもBC DATA0・応答30文字・T2=6秒として検証し、空応答や暫定FWの実装差をPicoで吸収しない。MODE13は受信値をATEへ公開し、Protocol OKを診断成功へ変換しない。全256件のHost／Mock成功は最終FWのSTOP動作やMODE13詳細の設計回答・実機検証とは異なる。評価用のため、実機前にバッテリ・充放電・負荷条件とOI-06／07を担当者が確認する。今回実機送信なし、IssueはCloseしない。

## OI-08: SL範囲外・不正DATAの実機確認（2026-11-09、Open継続）

2026-11-10通常値実機追記: LIFE_SET_123でRAW07B／12.3％、RAW000書戻しで0.0％へ復元を新規D0で確認。SL正常応答DATA0文字、各46ms、再送0。Sampleクリア許容・バッテリ／負荷未接続。OFF期間欄は元に戻らない実測を記録。範囲外／不正DATA／4095は未送信であり、PME動作や量産使用の設計回答ではない。IssueはOpen継続。[実機結果](Life_Set_Hardware_Test_20261110.md)。

- 原典で確認: r1 p.23のBATT_DEGは3桁HEX、0～4095、0.1％単位。4095は保守用電源識別値。SL受信で条件によりOFF期間データがクリアされる（p.32／39）。p.41の積算BATT_DEGはSET LIFEで設定された値を返す。SL個別説明にPMEの明記はない。
- ユーザー指示: 正式コマンドとして実装、量産使用は未確定。特に制限を設けず、PMEは実機確認し、範囲外書込みと読戻しで挙動を見る。追加指示によりSampleは後日準備、今回は実装・テスト手順作成まで。
- 実装: LIFE_SET_<VALUE>とLIFE_SET_RAW=<ASCII>。業務値域・特殊値・RAWの長さ／HEXを制限しない。ATE行とNFフレーム区切りのための書式／ASCII検査のみ。0～4095は3桁HEXの全域なので、4096以上は桁数超過も伴う。数値範囲判定と不正文字／長さの判定を分けて観測する。
- 未確認: 正式FWの不正長・不正HEX・負数・上限超過に対するPME／受理／切捨て、拒否時の保存値とOFF期間データへの影響、電源再投入保持。Picoは実応答や読戻しを補正せず、Mock結果から製品FW動作を断定しない。
- Host／Mock268件成功。Picoへの追加配置・製品への送信は未実施。[実機手順](Life_Set_Hardware_Test_Procedure_20261109.md)に元値退避、DATA_REFRESH→BATT_DEG_TOTAL?、範囲外各ケースと復元を記載。OI-08をCloseしない。

## USB-SUB-02: 実機Sink設定とHost用CC／VBUS／D線構成の確認（Open、2026-11-10）

- 現物写真の裏面表は0=Sink／1=Source。ユーザー申告はCC1／CC2とも0位置実装、1位置未実装。Type_C2はSink設定で、QR用Sourceの受入未完了。写真から抵抗値・基板版は確定しない。
- 原典回路図ではType_C2のRdはR19(CC1)／R18(CC2)各5.1kΩでGND接続、Source側R21(CC1)／R20(CC2)はVSYS接続でNC。Source用の値は原典で指定されていない。5.1kΩの単純移植・短絡は指示しない。Rp値、給電能力・保護・逆流、VBUS電圧／電流、D線プルアップR13／R10の現物・Host適合を設計確認する。
- 原典では両ポートVBUSがVSYSネットへ直結。CC変更だけで逆流防止・過電流保護や両Host成立を保証しない。
- 資料不一致: 計画・初回受入・資料台帳はType_C1 CC各5.1kΩをVSYS側と記載するが、原典図はR5／R6でGND接続。原典を変更せず相違として記録。最終構成・改造範囲と資料訂正を人間確認する。Type_C1=7355／Type_C2=QRの固定要求は変更しない。
- [写真・回路図照合記録](USB_Host_SubMCU_CC_Inspection_20261110.md)。QR／7355接続、改造、電気受入、FW配置は未実施。本IssueとUSB-SUB-01はOpen継続。

USB-SUB-02追記（2026-11-10、Open継続）: ユーザーがType_C2の無負荷VBUS=5Vを実測、抵抗変更なし・LED消灯と回答。CCは従来の両Sink位置実装のまま。VBUSの5V確認だけでSource設定・供給能力・逆流／過電流保護・D線Host適合を確認済みとしない。LEDの対象とブレークアウトの部品構成は未確認。[CC照合・実測記録](USB_Host_SubMCU_CC_Inspection_20261110.md)。

USB-SUB-02追記（2026-11-11、Open継続）: ユーザーからDB_N（DN1）の実物測定は不可能、本体3V3ピンで3.3V確認との回答を受領。DB_N–3V3抵抗測定は中止し、微細端子への追加プロービングを要求しない。3.3Vは電源電圧の情報で、D線プルアップ実装・値の確認とは区別する。測定不可を根拠に部品不存在・異常や除去／改造要否を断定しない。[測定結果・制約](USB_Host_SubMCU_Power_Check_20261111.md)。

USB-SUB-01／USB-SUB-02追記（2026-11-11、Open継続）: Type_C1 USB CDCだけの隔離した確認用開発FW dev-20261111.1を追加基板A06FEA01012EC137へ配置。元FW usb_deviceの全Flash2MBを退避・実機照合後、配布UF2書込み・verify成功。COM21でUSB実機123チェックを再起動前後それぞれ成功、Host／Mock287件成功。QR／DMM用Host・治具UART・CC／D線・給電保護は未確認のままで、今回の診断コマンドは正式ATE／内部リンクとして確定しない。[受入結果・UF2・退避・manifest](USB_SubMCU_FW_Acceptance_20261111/Result.md)。

USB-SUB-02追記（2026-11-11、D線説明訂正・給電方針）: 原典の接続線とメーカーRP2350_USB_C設定を再照合。正しくはD+=GPIO12／R12／DB_P、D−=GPIO13／R11／DB_N、R13はGPIO12側のD+プルアップ。先のD−側との説明は誤りで、原典の矛盾ではない。メーカーUSB-C専用FAQにD+プルアップ撤去と位置写真があり、Host向けR13処置の根拠を確認した。CC変更案はR18／R19を外し、R20／R21を各56kΩ・1%としてDefault USB Powerを広告。部品施工は未実施・人間確認待ち。

ユーザー指定: デバッグはPC給電、QR／DMM使用時は外部5VアダプタをExpanderで分岐し、追加枝で1Aまで供給可能との申告。PCとExpander給電を同時直結せず切り替える。1A定格から過電流／逆流保護や負荷時成立を推定しない。VBUS常時直結の限定評価と、接続検出・電源スイッチを伴う最終Source設計を区別する。[具体的な回路条件・部品変更案Rev.0](USB_Host_SubMCU_Host_Circuit_Conditions_Rev0_20261111.md)。USB-SUB-01／02はOpen継続。DB_N微細測定は引き続き要求しない。

USB-SUB-02追記（2026-11-11、Open継続）: ユーザーが改造は実機確認直前に案内すること、治具回路図へ箇所・手順を明記することを指定。[治具図Rev.4](drawings/NF55G_Fixture_20261111_Rev4/README.md)の4・5枚目へ反映した。部品サイズ・現物照合、給電保護、Host FW／ログ経路を揃えた後に案内する。改造済み・電気受入済みとは扱わず、DB_N微細測定は要求しない。

## USB-SUB-03: 固定TinyUSBの単一Host管理と2 Host構成（Open、2026-11-11）

確認事実: SDK2.2.0内TinyUSB86ad6e5のusbh.cは単一_usbh_controllerを保持し、PIO／ネイティブHCDを設定で選択する。メーカー例はDevice＋HostでありHost＋Hostの証拠ではない。tuh_init(0)と(1)の連続呼出しだけで2 Host実装としない。

未確認: 独立PIOスタックとネイティブHostの共存、または複数HCD管理の実装と列挙・切断・Timing。ハードの不可能とは断定せずType_C1=7355／Type_C2=QR・ハブなしの要求を保持。[実機前準備](USB_SubMCU_Host_Preparation_20261111/Preparation_Rev0.md)。QR単体probeを別開発物として準備し、既存基板への配置・改造は未実施。USB-SUB-01／02もOpen継続。

## USB-SUB-04: 診断UART起動時の先頭NUL（Open、2026-11-14）

- 確認事実: 改造後qr-uart-20261111.1をSH-U05A COM23で電源投入・RSTの2回受信し、各309byteが一致。先頭00の後にbootとboard_idの正常な連番0／1レコードが続く。実版・個体ID一致。
- 未確認: 先頭00の発生原因、起動／reset時のTX波形、変換器・配線への依存。原因や正式UARTでの許容を推測して確定しない。
- 診断解析: 元rawを保持し既定は厳密拒否。明示--allow-startup-nul時に限り先頭NUL 1byteを警告付き分離し、正規レコードを厳密検査。元フレーム合格・QR文字列合格・hardware_acceptanceにはしない。7テスト追加、全322件成功。FW変更なし、正式親子UARTへの仕様転用なし。
- [記録・検証](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/Boot_UART_20261114/Startup_UART_Handling_Rev1_20261114.md)。USB-SUB-01／02／03はOpenを維持。

USB-SUB-02／04追記（2026-11-14、Open継続）: 改造完了の申告、PC給電5.00V／3.30V、外部給電5.01V／3.30VとUART接続時5.00V／3.3Vを記録。qr-uart-20261111.1の対象個体への書込み・verify成功。PC給電時と、同一UART配線の外部給電RST後に版・個体IDの2レコードを受信。先頭NULは再現し警告付き解析のみ。外部電源投入だけでは受信が現れずRST後に取得した差の原因は未確定。電圧・識別確認をHost／電源保護／無操作電源投入起動の合格としない。追加枝保護・QR負荷・7355・2 Hostは未受入。[比較結果](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/Boot_UART_20261114/run08_external_same_uart/Result_Rev0.md)。

USB-SUB-02追記（2026-11-14、ユーザー指定の限定QR評価）: ユーザーが追加ヒューズ施工は困難、破損責任を引き受けて続行する旨を明示。今回のQR単体評価は追加ヒューズなし、申告済み5V／2.4Aアダプタ内蔵保護で進める。これは今回の評価運用の指定であり、追加枝1A保護の確認・量産保護の受入やIssue Closeではない。PC Type_C1切離し・無給電でQR固定接続・受信先行・初回は列挙とHID記述子のみ、という条件を維持する。[評価条件](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/Conditions_Rev0.md)。

USB-SUB-02追記（2026-11-19、共用電源）: 外部測定器HostはQR用と同じ外部電源を使用する。既存記録上の多摩電子工業DC5V/2.4Aは申告定格であり、Host・外部測定器を加えた総負荷、電流制限の実作動値、枝ごとの保護・配線容量は未確認。回路・給電経路の確認後、無給電で現物部品を照合し、必要な部品処置の後に単一外部電源で段階的な複合負荷試験を行う。RP2350-USB-AのUSB-C VBUSと5V/VSYSは共通ネットなので、外部電源とPC USB-C給電の同時直結は行わない。電源分離・逆流防止を確認できた場合のみ別途試験計画を立てる。IssueはOpenを維持する。

USB-SUB-01／02追記（2026-11-14、QR列挙実機結果）: Type_C2にQR固定接続、外部給電RST後、qr-uart-20261111.1で5レコードを取得。VID=E851／PID=1001、addr1／instance0、63byte HID Report Descriptor全体、エラーレコードなし。先頭NUL警告・末尾完全性未証明は維持。QRのLED青維持・音なしとの申告。文字列・配列・suffix・35文字一致・両向き・電源投入起動・7355・2 Host・量産保護は未受入でCloseしない。[原文・結果](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/run02_rst_enumeration/Result_Rev0.md)。

USB-SUB-01追記（2026-11-14、初回35文字採取の容量不足）: QR1回読取で8byte HID reportを251件取得し、旧診断FWの全256件ログが満杯。厳密解析は拒否、35文字一致は未判定。Alt＋テンキー数字列の解釈では先頭22文字が期待原文prefixと一致したが、参考解析にとどめる。UART診断版だけ1024件・qr-uart-20261114.1へ拡張し、旧版と未知版の256件拒否条件は維持。追加4テスト、全Host／Mock326件成功。新FW実機配置と再採取は未実施。[初回結果](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/run03_scan_35chars/Result_Rev0.md)。

USB-SUB-01追記（2026-11-14、既知35文字の単発PC側照合）: 1024件版qr-uart-20261114.1で全393レコード／HID388件、連番欠落・容量到達・エラーレコードなし。Alt数字列から復元した35文字と期待原文が完全一致、期待HID全388件との別経路比較も一致、Enter1回と解放まで取得。FW内文字列デコーダと正式親子UARTは未実装。先頭NUL、UART末尾完全性、両向き・繰返し、電源投入起動、負荷・保護・7355・2 Hostは未受入でOpen継続。[単発照合結果](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/run05_scan_35chars_1024_rst/Result_Rev0.md)。

USB-SUB-01／02追記（2026-11-14、Type_C2反転向き）: ユーザーが無給電でType_C2側QRプラグを反転。RST後の既知35文字1回を取得し、向きA／Bそれぞれ393レコード／HID388件、PC側文字列完全一致、両向きHID全列一致を確認。これは両向き各1回のRST後読取実績。FW内デコーダ・正式親子UART・連続読取・電源投入起動・負荷／保護・7355／2 Hostは未受入、Openを維持。[両向き総括](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/Result_Rev0.md)。

USB-SUB-01追記（2026-11-14、基板内文字列復元の診断実装）: 実機VID/PIDと63byte HID記述子に限定し、Alt＋テンキー5桁から英数字・ハイフン35文字＋Enterを復元するCモジュールを追加。完成原文kind12、異常kind13、断片は非公開・Enterまで破棄、切断初期化、暫定inter-report5秒を実装。正式ATE／Cache／SS／親子UARTは変更しない。FWと同一Cコードをnative実行し両向き実機HID再生を含む16件、ログ解析追加4件、全Host／Mock346件成功（skipなし）。qr-uart-20261114.2はARMビルド・配布検証成功、実機配置未実施。暫定期限・プロファイル限定・1024件の有限ログを正式仕様に昇格せず、USB-SUB-01／02／03／04はOpenを維持。[診断仕様](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/Decoder_FW_20261114/Specification_Rev0.md)。

USB-SUB-01追記（2026-11-14、QR側設定変更・Alt専用処理の撤回）: ユーザーがQRはAlt設定だったと回答し、英語キーボードへ変更したためAlt処理不要、プログラム復元・再試験を指定。受信を停止し、作業中のAlt専用C／テスト／fixtureをケース内履歴へ移動、FW・解析器をqr-uart-20261114.1の原文取得版snapshotへ復元、326件Host／Mock成功。実機はこの時点で.2のまま、.1書戻しと英語設定での再採取は次工程。旧Alt設定の記録・.2配布物は履歴で保持し、英語設定の実績へ転用しない。[復元記録](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/English_Keyboard_Retest_20261114/Restoration_Result_Rev0.md)。

USB-SUB-01追記（2026-11-14、英語設定変更申告後のHID観測）: .1原文取得版へ書戻した後の再採取でも393レコード／HID388件が旧Alt設定時のpayload列と全件一致した。英語設定への変更申告と受信事実を分け、設定反映の成功や失敗原因を断定しない。Alt専用処理を再採用せず、メーカー公式USA単独設定コードを再適用して再取得する。[結果・原文・メーカー資料](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/English_Keyboard_Retest_20261114/run01_scan_35chars/Result_Rev0.md)。

USB-SUB-01追記（2026-11-14、USA再適用・電源再起動後もAlt形式）: 原文取得版.1へ書戻した状態で、英語設定変更申告後・USA単独コード再適用後・QR電源再起動申告後の各再採取はいずれも393レコード／HID388件、旧Alt payload列と一致。直接英語キー出力は未確認で原因未確定。基板側Alt処理は復元しない。次は全設定初期化（他設定も戻るためユーザー選択待ち）かPC直結切分けとし、同じ操作の単純反復はしない。[再起動後結果](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/English_Keyboard_Retest_20261114/run03_after_qr_power_restart/Result_Rev0.md)。

USB-SUB-01追記（2026-11-14、ユーザー指定でAltデコードへ方針復帰）: ユーザーが英語設定の切分けはここまでとしてAltをデコードする方法で続行と指定。全設定初期化は実行せず、.2保存snapshotからAlt対応C・解析器・テスト／fixtureを復元、対象11ファイルhash一致、Host／Mock346件成功。実機は.1のままで.2の再配置・実機kind12確認は次工程。限定診断実装と正式親子UART／Cache／SSを分け、先頭NUL・起動差・有限ログ・電気保護・7355／2 Host等はOpenを維持。[再開記録](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/ALT_Decode_Resume_20261114/Resume_Result_Rev0.md)。

### 2026-11-14 USB-SUB-01／04の固定接続評価メモ（Open維持）

QR固定接続cold-startでFW起動2件のみ、同給電のRST後は557msで認識・35文字一致。原因未確定。ユーザー指示で抜差し成立を今回の目標から外し、電源投入から連続読取へ絞る。3秒待ち＋状態診断＋継続FIFOを候補FWへ実装するが、実機未書込み・改善未確認。RST前の読取が後に届く可能性もあり、正式要求境界・古い読取の扱いは独断で確定しない。先頭NUL・量産保護・7355／2 HostもCloseしない。[候補仕様](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/ALT_Decode_Resume_20261114/Fixed_FW_20261114/Specification_Rev0.md)。


## USB-SUB-05: QR／7355の独立Host基板と親Picoの2通信経路（Open、2026-11-14）

2026-11-16親ピン空き確認: QRのGP8 TX/GP9 RXを継承、7355にGP12 TX/GP13 RXを使う案は現行ソース・RS232/RTC/SD原典で競合なし。PIO1 SM0～3（ID4～7）を予約する案。GP10旧診断・GP6/7 RTC選択配線を避けた。実ハーネス/未接続・命令メモリ/IRQ・受信負荷は未確認、配線/FW変更なし。GPIO候補の資料確認まで前進したが正式割付の実装/受入は未完了でOpen維持。[確認記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Parent_PIO_UART_Pin_Check_20261116/Pin_Assignment_Rev0.md)。

2026-11-16 RP2350-USB-A資料・施工案: ユーザー指定Switch Science SKU10275/WAVESHARE-30274のメーカー原典9件を保存。公式回路のGPIO12=D+/R12、GPIO13=D−/R11、D+から3V3へR13=1.5kΩ、R10=NC、VBUS/Type-C/5VのVSYS直結を画像確認。Host専用化は現物が同じ実装ならR13撤去を基本案とする。FAQの明記条件はホットプラグ/Low-Speed無応答で、7355 Full-Speed固定CDCの無改造不成立を実証したとはしない。USB-AのCC施工は不要。外付けpull-down、個体版・給電/保護・CDC FW/実機適合は未確認でOpen維持。[調査・具体手順](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/RP2350_USB_A_20261116/Assessment_Rev0.md)。

7355試験準備追記（2026-11-14）: [CDC設定・電圧測定即試験手順](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/CDC_Settings_Voltage_Quick_Test_Rev0.md)へPC成功条件とメーカーSCPIを記録。IDN後のDC20V→200V→AUTOを準備したが未送信。前面BUS/LANG・入力値・Host実機適合・測定応答は未確認でOpenを維持。ADC形式のMD?をUSB CDC測定読出しに流用しない。

最新追記（2026-11-14）: ユーザーが追加基板をRP2350-USB-Aと明示。基板USB-A→USB A–Bケーブル→7355 USB-Bで確定し、型番・接続形態の確認待ちは解消。既存QR基板のRP2350-USB-C／Type_C2は維持する。以下の型番・ポート未確定記述は指定前の状態として保持。個体・回路条件・FW適合・親側資源・正式リンクの受入は未完了でOpenを維持。[基板・端子選定追記](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Board_USB_A_Selection_Rev0.md)。

ユーザー確定方針: 7355用Host基板を1台追加し、既存QR Hostと親Picoへの接続経路を分ける。既存QR基板のType_C1改造・CC切替案とその写真依頼は取り下げ。親側は独立双方向UARTを2系統用意する設計方針で、ATE UART0／NF55G UART1は転用しない。

未確定: 追加基板の型番・個体・使用Hostポート・CC／VBUS・保護、親GPIO／PIO SM・命令メモリ・IRQ・buffer・受信負荷、リンクの正式フレーム／API。共通コードを用いても経路別の起動・要求・受信状態を分ける。入手・購入操作・新構成の実装／実機検証は未実施。[構成・次工程](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Split_Host_Architecture_Rev0.md)。

USB-SUB-03は1基板・2 Hostという旧構成の課題としてOpenのまま保持し、新構成の必須条件から外す。技術的に解決・Closeしたとは扱わない。USB-SUB-01／02／04も継続。

## S1.15_r1 ソース比較レビュー（2026-11-18、Open継続）

ユーザー指定のS1.13とS1.15_r1を比較。詳細と行番号根拠は [検証結果](S1.15_r1/Review_20261118.md)。原本コピー172ファイルのSHA-256一致、既存Host/Mock354件成功。実機試験・NF55G再ビルドは未実施。

- OI-03: D0 ACK後のCHARGE_ENDクリアは新版にも存続。
- OI-04: 今回の新旧ARはfloat型pointをint_to_aschex(int32_t,...)で整数HEXへ変換。過去記録のfloat raw HEX推定と区別する。過去暫定FWと今回S1.13の同一性は未確認。AD入力/応答とAR REFの表現差、小数保持・単位は要設計確認。
- OI-05/16/18/21: 通常測定の2点オフセット補正は改善したが、AD即時係数反映・AD応答式・入力検証・校正条件の懸念は残る。
- OI-06/07: BCの0/1以外PMEとDCIR中断フラグ解除等は改善。BC=0でもDCIR要求を立てる共通処理が残り、STOPの懸念は解消しない。
- OI-20: ARのDATA140文字、5系統・2点・順序はソース一致。設計回答や実機検証によるCloseではない。

| 追跡ID | 新たな確認事項 | 状態 |
|---|---|---|
| S115-01 | EEPROM CRC対象834→835byte、追加chgsoc/back_upの移行。旧EEPROM引継ぎ時のCRC不一致・起動停止可能性。書込み工程の初期化/移行手順を設計確認。 | Open・高優先 |
| S115-02 | gf_batt_v_coeffの1000倍削除に対し、input:757の充電過電圧判定は旧式のまま。閾値PRO_HIGH_V_CHG=11400との単位/オフセット整合と保護成立を設計確認。 | Open・高優先 |
| S115-03 | 実行時2点補正式とAD応答CALC式の差、およびAD後の係数反映手順。OI-05/16/21と関連。 | Open |
| S115-04 | ARの整数変換による小数情報喪失と正式REF表現。今回S1.13にも存在。OI-04と関連。 | Open |

上記は静的解析の確認事項。製品不良や実機改善を断定せず、設計回答を推測してCloseしない。治具側での吸収・仕様変更は行っていない。
