# CHANGELOG

2026-11-21 USB HOSTリセット検討: NF55G Pico治具内に[検討資料Rev.0](USB_Host_Reset_Study_20261121/Reset_Study_Rev0.md)を新規保存。QR/CDCの手動RESET・電源再投入・ソフトRESET候補を整理し、CDCの親/Host双方の状態初期化と旧機器応答排除を未確定課題としてUSB-HOST-RESET-01へ記録。既存方針/コード/配線/Flashは変更せず、実機試験未実施。

2026-11-20 ユーザー方針更新: RUNパッド施工は難しいため外部RESET配線/駆動回路は進めず、手動RESET/電源再投入をデバッグで選ぶ。GP14/22は汎用予備。初回起動前から記録し、異常→正常データを交互に送る受入を計画。形式不正後の受付継続と、timeout/切断等の規定fault保持を分けて判定する。今回は計画のみ、実機注入/コード変更なし。 [計画](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Error_Normal_Alternation_Plan_Rev0/Plan_and_Reset_Decision_Rev0.md)／[現行GPIO Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev1.md)。

2026-11-20 工数/GPIO並行計画: 測定原文取得/ATE返却は実機済み。残る数値・単位/Cache/正式ATE入口とAD実装は仕様回答後コード/Mock1〜2実働日、基本実機確認含2〜3実働日（概算12〜24時間、待ち/全量産受入は別）。親GPIOは既存予約のQR GP8/9と実装済み測定器GP12/13を配線基準として維持。現行測定器PIOはSM4/5で旧案の順序に注意。RESETは必須/制御方式未確定、GP14/22を親側予備候補として確保しHost RUN結線は回路確認後。今回コード/Flash/実配線変更なし。 [工数](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Effort_Estimate_Rev0.md)／[配線基準](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/GPIO_and_AD_Plan_20261120_Rev0/Parent_GPIO_Wiring_Baseline_Rev0.md)。

2026-11-20 ユーザー補足による解釈訂正: 「試験者設定のレンジ」はATE側のコマンドで決定/設定する意味。前面手動設定を前提にせず、ATEが固定レンジ値またはAUTO条件を指定→Queryで設定確認→測定要求を送る。Pico/Hostは本文を中継し、指定値の独自置換/自動最適化を行わない。次の安定性試験もこの順序で実施する計画。今回は記録訂正のみ、実機送信/コード/Flash変更なし。 [現行方針Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Next_Steps_After_ATE_Range_Decision_Rev1.md)。

2026-11-20 ユーザー決定: 最適レンジは試験者が設定し、レンジ追加調査はここまでとする。中継は明示コマンド/原文を維持し自動最適化/独自補正しない。レンジ読戻し差の記録は保持し中継継続のブロッカーにしない。次は固定入力/試験者レンジでの安定性→timeout/切断/清浄復帰→ATE/NF55G/SD共存受入。その後、正式API等を確認してADC測定Cache/ATE確認後別指令ADへ接続する。今回は説明/記録のみ。 [方針・次工程](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Next_Steps_After_Operator_Range_Decision_Rev0.md)。

2026-11-20 Codex直接送受信: ユーザー固定入力/COM7解放後、AUTO単発-2.91185V、続けてRANG20指定-2.9118V、RANG200指定-2.912V、AUTO-2.91186Vを取得。全機器エラー0、各READ一回/再送なし、最終AUTO ON/COM7解放済み。CONFは20指定で199.9999V、200指定で1099.999V、AUTO測定後19.99999Vを原文保持し、選択境界の理由は未解決でIssue Open維持。 [測定比較](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Codex_Fixed_Range_Comparison_01/Result_Rev0.md)。

2026-11-20 入力再接続依頼後の200V状態READ?は正常15byteの-002.9119E+00（-2.9119V）、機器エラー0。前回非ゼロ-2.91180Vとの差の大きさ0.10mV。今回の新前面値/CONFは未提示、基準精度/合否は未判定。次は同入力でAUTOの設定/読戻し/単発測定を確認する。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/User_200V_Measurement_02/Result_Rev0.md)。

2026-11-20 200V読出し0Vの入力条件をユーザー確認: 「変わっている、現在無負荷」。前回-2.91180Vとは異なる入力条件の試行として分け、同一入力のレンジ比較は未実施と補足。無負荷の具体的結線は未確定で0Vの正当性や故障を断定しない。 [補足](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/User_200V_Measurement_01/Input_Condition_Clarification_Rev0.md)。

2026-11-20 ユーザーの200Vレンジ状態READ?は正常15byteの+000.0000E+00（0V）、機器エラー0。前回-2.91180Vと数値が異なるため、現在の前面値/入力・配線維持を確認中。レンジ変更や故障を原因と断定せず原文保持。Codex追加送信/コード変更なし。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/User_200V_Measurement_01/Result_Rev0.md)。

2026-11-20 UP一回の表示対応確認: 押下前AUTO0/CONF19.99999V、ユーザーの押下時表示200V、押下後AUTO0/CONF199.9999V。今回の一時表示は変更後レンジと一致。過去RANG20直後の約200V読戻しの理由は別途未解明でIssue Open維持。現在固定200V相当、次は同じ低電圧入力で単発読出しを比較。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Panel_Range_Interpretation_01/UP_Once_Result_Rev0.md)。

2026-11-20 前面キー操作なしの基準Query: AUTO?=0、CONF?はVOLT +1.999999E+01,+1.000000E-06（正常36byte）。現在の機器読戻しは固定20Vレンジ相当。以前のCONF約200Vとは取得時点/キー操作が異なり、過去SCPI動作の原因や一時表示の意味は未確定。次はUP一回の前後を比較。 [基準記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Panel_Range_Interpretation_01/No_Key_Baseline_Rev0.md)。

2026-11-20 前面レンジ確認の前提を補足: ユーザーはレンジボタン押下時の表示が変更前後のどちらか不明と回答。取説4-3/4-19でUP/DOWNは設定変更そのものと確認。過去の前面20V報告は保持するが「現在レンジ確定」との扱いは保留し、前面読取り未確認へ訂正。正常CONF約200Vの観測は保持。USB-CDC-RANGE-01はCloseせず確認前提を更新。まずキー操作なしのAUTO?/CONF?を記録する。 [補足記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Panel_Range_Interpretation_01/Clarification_Rev0.md)。

2026-11-20 ユーザー単発測定: READ?の15byte原文-02.91180E+00+CRLFを取得、-2.91180V、機器エラー0。前面もマイナスと回答し極性一致。校正/製品合否は未判定、前面20V/CONF約200V相違はOpen維持。次は同じ約2.9V入力で200Vレンジの前面/原文/再測定を確認する手順を作成。Codexの実機送信/コード変更なし。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/User_Single_Measurement_01/Result_Rev0.md)。

2026-11-20 ユーザーの測定準備ログで、16進03送信直後のOPC?にERR:FRAME。ATE受信コードの制御byte拒否/行終端まで拒否/実行前エラー応答と一致し、その行は外部機器へ送られない。後続OPC?=1、機器エラー0。READ?は未実施。設定再送せずTRIG:COUN?の確認後に単発測定へ進む手順を提示。コード/Flash変更なし。 [記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/User_Trigger_Setup_01/Result_Rev0.md)。

2026-11-20 .3のユーザー固定20V確認: AUTO OFF/RANG20の後、AUTO?=0、CONF?は正常36byteのVOLT +1.999999E+02,+1.000000E-05、SYST:ERR?=0。ユーザーは前面20Vを確認。受信書式は正常だが前面/読戻し相違は継続しUSB-CDC-RANGE-01をOpen維持。FIFO不具合だけを原因にしない。次の測定用V/COM入力値を確認中、Codexは測定未送信。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/User_Fixed_20V_Check_01/Result_Rev0.md)。

2026-11-20 .3実機で設定Query5種×12周（60件、機器応答総1035byte）と終了エラーQueryを成功。全周で原文/書式/長さ一致、CONFは正常なVOLT +1.999999E+01,+1.000000E-06、AUTO=1、エラー0。先行の応答崩れは今回再現せず、受信健全性を確認。固定20V切替/前面一致/測定は未実施でレンジIssue等はOpen維持。COM7解放済み。 [結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/CONF_FIFO_Validation_01/Result_Rev0.md)。

2026-11-20 CDC FIFO修正版.3をBFCF2EDB84B0B37Fへ配置完了。旧.2全Flash2MiB退避/hash照合、新UF2照合、Flash verify、書込み後個体/版/BOOTSEL照合成功。rebootなし、親ソフト変更なし。次は通常接続で設定Query12周の受信健全性を確認する。レンジ/測定は未実施、Issue Open維持。 [配置結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Host_Deployment_03/Result_Rev0.md)。

2026-11-20 CDC FIFO修正版.3のARM build/link、UF2版/hash照合完了。全453件成功。TX/RX FIFO256整合、endpoint64維持、SDK原本変更なし。実機はまだ.2で、全Flash退避後に.3配置する準備。測定前に累積Queryの受信健全性を確認する。 [ビルド結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Build_Result_Rev0.md)。

2026-11-20 USB-RELAY-CDC-BUF-01（Open）: 提示CONF?が36byteの不正文字列に復号。固定SDK CDCのrx配列はTX macro確保64byte/初期化RX深さ256byteという不一致を確認し、実FIFOで隣接領域書換えを再現。Host側TX/RX256整合+ビルド時guardへ修正、新FW.3をビルド中。回帰3件追加し全453件成功。提示崩れの実機因果/20V問題は未確定でCloseしない。 [修正記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_CDC_Buffer_Fix_01/Result_Rev0.md)。

2026-11-20 ユーザー操作用の7355レンジ切替/単発測定/任意コマンド送信手順を別ファイル作成。原典§6.8.4で設定後Query必須と各書式を照合し、EXT_SEND/EXT_QUERYの逐次操作へ展開。20V前面/CONF相違はOpen維持して確認点を明記。実機への設定/測定送信なし、コード/Flash変更なし。 [操作手順](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/Host_UART_Sync_Fix_01/Serial_Monitor_Range_Measurement_Rev0.md)。

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

2026-11-20 中継実機試行1は治具ATE識別で停止。COM5/57600 8N1で*IDN?を1回送信し10秒待機したが受信0byte。EXT_QUERY/7355への送信は未実行、自動再送なし。ATE側接続をユーザー確認済み。コード/Flash変更なし、USB-RELAY-ATE-01をOpen追加し親起動の切分けへ進む。 [試行結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Runtime_01/ATE_Capture_01/Result_Rev0.md)。

2026-11-20 親配置完了: COM6/unique_id 69f7d45962cfdfadの既存26ファイルを退避・SHA照合後、配置対象30ファイルを実機SHA照合（追加/更新8）。実機RAM検証と配置後import成功。通常起動せずREPL停止、PIO4/5はinactive。Host/親の配置は完了したが、配線と実機中継受入は未実施。[親配置結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Parent_Deployment_01/Result_Rev0.md)。以下の親未配置記述は配置前の状態として保持。

2026-11-20 後続配置: Host BFCF2EDB84B0B37Fへmeter-host-relay-20261120.1を書込み、Flash verifyと書込み後版照合に成功。旧.5全Flash退避・照合済み。BOOTSELのままrebootせず、親Picoは未配置・実機中継未試験。[Host配置結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Hardware_Deployment_Rev0/Host_Deployment_01/Result_Rev0.md)。以下のHost未配置記述は配置前の状態として保持。

2026-11-20 親/Host中継リンクを実装。ExternalInstrumentLink/PIO UART、本文保持parser、FixtureAppの非同期ATE応答を追加。HostにX1 codec/要求engine/CDC adapterの独立UF2を追加し、旧診断/電圧試験/QRを保持。全446件成功（追加32件）、ARM build/link、公式PIO assembler、未配置パッケージhashを検証。ソースの有効化flagはFalse、配置用コピーのみTrue。実機操作なし。 [リンク実装記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Result_Rev0.md)。

2026-11-20 ユーザー承認により中継通信契約をRev.1として確定。承認前原案を保持し、ATE/UART/上限/CRC契約をMaster/関連Open Issuesへ反映。external_instrument_contract.pyへ承認値・本文保持パーサー・CRC/長さ検証・原文HEX応答を追加、13テストを追加。本番ATE入口・Host C・GPIO/実機書込みは変更していない。 [確定仕様 Rev.1](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Interface_Spec_Rev1.md)。

2026-11-20 外部測定器中継コア第1段階: external_instrument_relay.pyと19テストを追加。内部要求相関、原文保持、送受信完了の分離、総期限/遅着・切断・取消・旧接続の拒否を実装。全Host Unit/Mock 401件成功。正式ATE/UART/Host実機中継は未接続。開発用通信契約の具体案を作成し、Open事項は確定/Closeしない。 [実装記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Result_Rev0.md)。

2026-11-20 中継開発の優先指定: ユーザー指示によりレンジ切替検証を後回しにし、中継完成後にシリアルモニターからユーザーがコマンド/応答・前面を確認する方針を記録。USB-CDC-RANGE-01はOpen継続。正式中継API/親子UARTの未確定契約を承認済みとは扱わず、コード/実機変更なし。 [要求記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Serial_Monitor_Relay_Requirements_20261120_Rev0.md)。

2026-11-20 .5実機試行1: COM22の120秒採取で.5起動・CDC・IDNを確認。RANG 20後error=0、CONF約200Vと前面報告20Vの相違を再現し、レンジゲートでREAD前停止。原文/hash/Query別応答を保存。追加コード変更なし。 [実機結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Handoff_20261120_Rev0/Runtime_v5_run01/Result_Rev0.md)。

## 2026-11-20 CDC電圧評価FW.5配置

- ユーザーの接続分離・BOOTSEL準備完了を受け、対象BFCF2EDB84B0B37Fの現行.3全Flash 2MiBを退避・照合OK。その後.5 UF2のhashを照合してload -v、Flash verify OK。実機infoで.5/同chipid/BOOTSELを確認。
- 再起動・測定は未実施。コード変更なし、ソフト回帰は直前382件成功を継承。[配置記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Handoff_20261120_Rev0/Deployment_v5/Result_Rev0.md)。

## 2026-11-20 CDC Host引継ぎ・READ前応答検証の補強

- raw #07～09とmanifestを照合し、CDC/IDN成立、測定未取得、.3配置記録/.4未配置を整理。ユーザー回答「20Vレンジで電源OFF」とCONF約200Vの相違をUSB-CDC-RANGE-01としてOpen追加。
- 評価FW.5で設定数値/CONF検証を共用Cへ分離。有限10進数、完成CONF機能・full-scale・正の分解能を照合し、不正数値・NUL・部分/複数行を拒否。既存19～21Vゲートを維持し、SCPI指令・親/ATE/NF55G仕様は変更しない。
- 実Cの7テストを追加、全Host Unit/Mock 382件成功。両FWのARM build/link、UF2版.5/GPIO/SDK metadata、6成果物hash照合も成功。変更前のソース・全6ビルド成果物、raw証跡を案件内へ保持。新FWの実機配置・測定は未実施。[詳細](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Handoff_20261120_Rev0/Result_Rev0.md)。
## 2026-11-20 外部測定器Host診断FW配置

- USB-A Host診断UF2を対象serial BFCF2EDB84B0B37Fへpicotool v2.2.0-a4で配置し、Flash verify OK。全Flash退避済み。
- 書込み時はPC USB-Cのみ接続し、外部電源・USB-A機器・QR・診断UART adapterは外した。通常起動後COMが出ないのはFWのUSB Device/CDC無効化による想定動作。診断UART受信、Host起動、CDC/IDN実機試験は未実施。

## 2026-11-20 診断UART受信試験

- SH-U05A COM22はPnP状態OK。115200/8N1、flow controlなし、DTR/RTS OFF、TXなしで30秒採取を4回実施。最初の2回はGP0端子位置の誤認が後から判明し、3回目も0 byte。4回目は124 byteを受信し、FW版/Chip IDと`USB_HOST_READY rhport=1 dplus=12 dminus=13`を確認。rawは`temp/meter_host_com22_capture_20261120_04.raw`、SHA-256は`8e44cfb8024be10b107bd31c384781ed2b7266cbd0f03a141fa976d21a731ed3`。
- FW起動、診断UART受信、PIO USB Host初期化を確認。7355未接続のためCDC mount/IDN/測定は未試験。電源保護条件とR13施工状態を確認するまではUSB-Bを接続しない。

## 2026-11-20 7355固定接続USB Host試行

- ユーザー申告の準備確認後、7355をUSB-A Hostへ固定接続しPC USB-Cを切り離して外部電源を投入。COM22の30秒UART採取は124 byte、SHA-256 `3c06c23cecb91cf7c58cb4e9ceac961dd9e1a95c50cb8c000e85477cc52f715a`。
- FW bannerと`USB_HOST_READY rhport=1 dplus=12 dminus=13`は受信したが、`USB_MOUNT`/`CDC_MOUNT`/IDNイベントなし。CDC列挙受入は未達。次の通電前に電源OFFでケーブル経路と7355側USB interface設定を確認する。

## 2026-11-20 7355 CDC/IDN通信確認

- USB-A–USB-Bケーブル経路と7355 BUS=CDCを確認後、外部電源で固定接続試験を実施。対象VID/PID `1334:0309`のUSB/CDC mount、9600/8N1、DTR/RTS ON、`*IDN?`一回送信、CRLF終端の32 byte応答を確認。
- 実測IDN `ADC Corp.,7355,246410099,  A02`。以前の`246410072 / A01`は別個体の参照値であり、今回の差はユーザー確認済みで想定内。前面LANG=SCPIと既知低電圧入力を確認後、測定試験へ進む。
- raw `temp/meter_host_com22_capture_20261120_07.raw`、436 byte、SHA-256 `cac1ab22e6655a323671938428ce66037773c6bd3cc140867f9c394445f5222b`。

## 2026-11-20 単発DCV測定用FW準備
## 2026-11-19 外部測定器用USB HOSTの基板・端子構成を確定

- 追加RP2350-USB-A向け診断用CDC ACM Host FW `meter-host-diag-20261119.1`を独立プロジェクトとして作成。GPIO12/13 PIO Host、VID/PID確認、9600/8N1・DTR/RTS設定完了待ち、`*IDN?`一回、raw responseのGP0診断出力を実装。親Pico/ATE/NF55G制御や測定設定は含めない。
- SDK 2.2.0／ARM Secure build-link成功。UF2 hash等をbuild manifestへ記録。Host/Mock既存回帰375件成功。新Hostへの書込み・実機列挙・CDC/測定は未実施し、QR用FWと配布物は変更していない。
- ユーザーよりRP2350-USB-AのR13撤去完了との報告を受領。施工前後写真、はんだ状態、周辺部品、再給電後の電気確認は未確認。再給電・Host試験完了とは扱わない。
- BOOTSEL serial BFCF2EDB84B0B37Fからpicotool v2.2.0-a4で全Flash 2MiBを読み取り退避し、`save -a -v`照合OK。SHA-256と対象情報を個体別manifestへ記録。消去・書込みなし。
- ユーザー承認によりUSB-A Host側R13撤去を次の物理作業対象とした。電源を全て切り離して現物位置を照合し、R13のみ処置する条件を記録。撤去作業そのものは未実施。
- ユーザー報告で基板5V-GND／3V3-GNDとも電圧に異常なし。具体的な数値・測定条件は未提示であり、無負荷電圧、給電容量・保護やUSB Host動作の受入とは区別。
- 通信ケーブル交換後、WindowsがRP2350系USB CDC（2E8A:0009、Pico、Board CDC、COM25）をPnP状態OKで認識。BOOTSEL・Flash操作・書込みは未実施。
- RESET/RUN操作後もCOM25の通常USB CDC状態を維持し、BOOTSEL VID:PID 2E8A:000FとRP2ボリュームは未検出。BOOTを保持したRUN/RESET操作後に再確認する。Flash操作なし。
- BOOT保持付きRESET/RUN後、VID:PID 2E8A:000FのRP2350 Boot、PnP状態OK、E: RP2350/FAT約134MBを検出。INFO_UF2はBootloader v1.1、Model RP2350、Board-ID RP2350。Flash退避・消去・書込みは未実施。
- 初回PC列挙ではUSB VID 2E8A/RP2350、COMポート、BOOTSELボリュームを検出せず、USB列挙エラーもなし。物理接続申告とWindows認識を区別して受入記録へ追加。書込み・Flash操作なし。
- ユーザー報告によりWaveshare RP2350-USB-Aを入手し、回路確認済み、現在PCとUSB-C接続中の進捗を記録。USB列挙、個体識別、Flash退避・書込み、Host受入は未確認。
- 外部測定器用HostをWaveshare RP2350-USB-A（WAVESHARE-30274）とし、USB-Cを開発側、USB-Aを機器側として外部測定器のUSB-Bへ接続する構成を記録。ケーブルはユーザー準備、給電は外部電源。
- ユーザー指示により、給電源はQR用と同じ多摩電子工業DC5V/2.4A（既存記録上の申告値）を共用する方針。複合負荷での容量・分岐保護は未確認のため段階試験対象とし、開発USB-CのPC給電と外部電源の同時直結は共通VBUS/VSYSネットのため行わない。
- Pico 2からQR用RP2350-USB-Cと外部測定器用RP2350-USB-Aを使い分ける役割分担についてユーザー了承を記録。
- QR用RP2350-USB-Cとの2 Host構成を最新接続仕様、Software Module Interface、USB-INT-01、Host準備資料へ反映。ピン対応、ケーブル結線、外部電源の電気的保護・容量と実機動作は未確認のまま。文書のみ更新、コード/FW/配線/実機操作は変更していない。

## 2026-11-19 外部測定器の機種非依存名称と中継経路を明確化

- 機能上の名称を「外部測定器」とし、7355/DMMは今回使用する具体的な実機として区別。ATEがコマンド本文・測定手順を指定し、親Picoが対象Host/adapterへ中継して応答をATEへ返す役割分担を現行方針へ反映。
- 接続仕様、ADC校正開発方針、外部測定要求、ATE指定ASCII中継計画を更新。既存コード、ATE API、通信フレーム、Host FW、配線・機器動作は変更していない。文書変更のみのためHost/Mock試験は未実施。

## 2026-11-19 USB HOST中継配線の引継ぎ

- Pico 2／Expander／中継基板／QR用と外部測定器用USB HOSTのユーザー指定構成を記録。初版の「RP2350-USB-C USB HOST ×2」は本日後続指示で更新。
- 中継基板をUSB HOSTとPico間の接続位置を示す目印・ハード設計/デバッグの説明補助と明記し、今後のUSB CDC開発および開発済みQR機能のPico側ポート接続説明に使う方針を追記。既存設計方針は変更しない。
- 秋月電子117585、ADA-5200（スイッチサイエンス8588、PiCowbell Proto）、はんだ付け配線、RESET信号の存在を記録。過去会話のC-17585は誤りとして訂正。
- `docs/USB_HOST_Interconnect_Spec.md`を追加し、README、Codex引継ぎ、ソフトウェア境界、Open Issues、引継ぎ台帳へ反映。
- 未確認ピン・配線位置・RESET接続をUSB-INT-01としてOpen管理。既存OI-17はADC校正の課題として維持し、USB CDC保守通信とも分離。
- 文書のみの更新。Host/Mock 375件成功。GPIO割当、通信方式、FW、USB HOSTドライバ、実配線・実機動作は変更・検証していない。

## 2026-11-19 50A/50mVシャントの換算を親Picoへ実装

- ユーザー回答でシャント50A/50mV（1mΩ）、取得mV、換算担当Picoが確定。電流2系統はmVの数値をそのままAにする。BATT_VはVを維持。
- `calibration_measurement.py`でmV保持と`get_calibration(token)`を追加。原文/元単位を保持し、換算候補をコピーで返す。誤単位を拒否し、浮動小数点演算・丸め・自動測定・AD送信を行わない。
- `test_calibration_measurement.py`に換算・単位・精度・失効・Mock無送信の6件を追加し、関連仕様とCAL-EXT-02の回答済み範囲を更新。正式ATE/Host接続・AD表現・実機検証は残る。[詳細](ADC_Calibration_Development_20261119.md)。
- Host Unit/Mockの全375件成功（9.164秒）。追加後ログは別名保存し、前回ログを保持した。

## 2026-11-19 ADC校正治具の開発継続と測定Cache基盤

- ユーザー指示により新製品FWへの追従変更保留とADC治具開発継続を区別。必須対象3系統×2点、12VOUT_I固定係数の扱い、OI-17/OI-19とNF54G資料の区別を記録。
- OI-17の12VOUT_I固定値は製品FWの設計思想によるもので、試験手順書の検査項目に明記されていないとユーザー確認。IssueはOpenで追跡するが、治具開発のブロッカーではない。製品FW/AD/AR仕様は変更しない。
- `calibration_measurement.py`と`FixtureApp.measurements`を追加。試行/取得/対象/点の照合、再取得前の破棄、遅着/重複拒否、TEST_START/再START/TEST_END成立との連動、原文/数値文字列の保持とコピー保護を実装。
- 単体/Mock統合テスト15件を追加。正式ATEコマンド/親子UART/CDC/換算/AD送信は未追加、実機配置・製品FW/GitHub Issuesの変更なし。未回答IssueはCloseしない。[実装範囲と検証ログ](ADC_Calibration_Development_20261119.md)。
- Host Unit/Mockを含む全369件成功（7.521秒）。今回変更した追跡ファイルのdiff空白チェック成功。

## 2026-11-16 7355コマンドはATE指定ASCIIを中継する方針へ整理

- ユーザー方針によりDMMのSCPI・設定/測定順序をATE担当、親を要求相関/中継/Cache、HostをCDC送受信とする分担を明記。任意ASCII応答と校正用の明示測定Cacheを区別し、取得→ATE確認→別書込み・完了/TEST_ENDで破棄を維持する。
- CDC成立後の設定/測定、親経由中継、異常/復帰、QR共存、校正/読戻しのデバッグ工程を追加。正式中継API・数値変換等は未確定、IS状態は変更なし。文書のみ、コード/FW/実機操作・Host/Mockなし。[分担とデバッグ計画](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/DMM_ATE_ASCII_Control_Debug_Plan_20261116_Rev0.md)。

## 2026-11-16 RP2350-USB-A端子位置とUART監視配線を図面化

- メーカー回路図P1とピン配置図を照合し、部品面・裏面の全18端子番号/GPIO位置、GP0/GP1/GND/5V/3V3、監視用TX→RX配線と後工程の親接続案をA4横3枚のPDF/SVG/PNGへ整理。試作完了後にはんだ付けするユーザー予定を注記。
- 18端子の一意性、文字/参照先/原典hashと3ページ描画を確認。図面生成scriptと記録のみ、IS状態・FW/実配線は変更せず、Host/Mock・実機試験なし。[図面一覧](drawings/RP2350_USB_A_Pinout_20261116_Rev0/README.md)。

## 2026-11-16 CDC Host単体仕様とUART監視手順を整理

- PC成功条件をPIO Hostで再現する初回範囲を、専用FW/列挙/CDC設定/IDN、その後に電圧/レンジ確認の順として整理。追加HostのGP0診断TX→3.3V adapter RXD/GND、115200/8N1案、外部5VとPC書込みモードを分離する配線条件を記録。
- 新CDC FWは未作成で、QR版を流用して動作確認済みとはしない。R13状態とadapter型番はユーザー確認中。今回は仕様書のみ、コード/FW変更・ビルド/Host/Mock/実機操作なし。[単体確認仕様](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/CDC_Host_Single_Acceptance_20261116_Rev0.md)。

## 2026-11-16 親PicoのPIO UART2系統のGPIO空き確認

- src/・旧診断script・Rev.4 GPIO表・RS232/RTC回路図・SD EAGLEネットを照合。QR用GP8 TX/GP9 RXを維持し、7355用はGP12 TX/GP13 RXの割付案を作成。PIO1 SM0～3を候補にし、GPIO/物理pin対応と原典・hash証跡を保存。
- GP10旧診断、GP6/7 RTC選択、GP15 card-detect等を考慮。資料上の競合なしと現物未確認を分離し、USB-SUB-05はOpen維持。文書/証跡のみ、ソース/設定/FW/配線変更なし、Host/Mock・実機試験未実行。[割付と確認結果](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Parent_PIO_UART_Pin_Check_20261116/Pin_Assignment_Rev0.md)。

## 2026-11-16 RP2350-USB-Aの7355 CDC Host資料と改造手順を調査

- 指定SKU10275についてメーカー回路図・Wiki・デモZIP・R13位置/ピン画像・設計資料・TinyUSB説明の原典9件を新規保存。hash台帳、展開物、固定SDK/PIO関連11ファイルの照合コピー、回路図描画を作成。販売ページはWeb確認済み、HTML保存は429で未完了と記録。
- R13撤去をHost専用化の基本案とし、R10 NC/R11・R12維持、USB-A側CC変更不要、VSYS直結電源の扱い、追加pull-down評価、CDC Host専用FWと単体受入順序を具体化。USB-SUB-05と基板選定/モジュール資料に関連付け、個体版・電気条件・FW適合はOpen維持。
- 収集scriptの構文・原典hash/形式/リンクを確認。既存FW/量産コード/配線変更・機器操作なし、Host/Mock・ARMビルド・実機試験は未実行。[調査と手順](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/RP2350_USB_A_20261116/Assessment_Rev0.md)。

## 2026-11-14 QRと校正の書込み後読戻しフロー案

- 書込み完了で取得Cacheを破棄した後、ATEが明示Refreshと個別Queryで期待値照合する手順を整理。SSはINFO_REFRESH、ADは計画上AR_REFRESH。AR未実装・形式と反映時期のOpenを明示し、校正後の外部測定確認は保存値確認と分けた。
- 照合期待値はATE保持の設計案。文書のみ更新、コード/FW/配線変更なし、Host/Mock・実機試験未実行。[確認フロー案](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Post_Write_Verification_Flow_Rev0.md)。

## 2026-11-14 QRとDMMの取得Cacheは書込み完了またはTEST_ENDで破棄

- ユーザー指定で書込み完了時の使用Cache破棄、TEST_END時の全取得Cache破棄を確定。未完了要求の失効・遅着での復活禁止・再利用には再取得/ATE確認を要件化し、成否不明時INVALIDの既存Hard Ruleと整合。履歴ログは保持する。
- 取得値書込み要件、ATE/Cache Master、Open Issues、試験要件、工程案を更新。正式API・完了単位等は未確定。文書のみ、コード/FW/配線変更・Host/Mock・実機試験なし。

## 2026-11-14 DMMとQRは取得CacheをATE確認後に別指令で書込み

- ユーザー回答で取得→Cache・ATE返却→ATE確認→別の明示書込み指令でCache値を付加する順序を確定。数値直接指定方式は維持。書込み時の再取得禁止、確認した値と書込み値の同一性、INVALID/不一致時の無送信を要件とし、ATE/Cache Master・関連要件・工程・試験要件・Open Issuesへ反映した。
- 正式API/取得識別・Cache寿命/書込み後状態・変換規則等は未確定。今回は文書変更のみ、コード/FW変更・Host/Mock・実機試験なし。[確定要件](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Acquired_Value_Write_Requirement_Rev0.md)。

## 2026-11-14 校正とQRの取得値付加書込みの到達要件を追記

- ユーザー指示により、数値直接指定と別にDMM取得値を校正書込みへ付加する方式、QR読取値をNF55G書込みへ使う方式を到達機能として記録。関連要件・工程案・Open Issuesを更新。
- 従来のATE数値再指定契約との差を明示し、取得と明示書込みの実行境界は確認中。正式API・SS変換/保留解除は未確定。文書のみ更新、コード/FW変更・Host/Mock・実機試験なし。[要件追記](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Acquired_Value_Write_Requirement_Rev0.md)。

## 2026-11-14 7355通信後のQRと測定機能の開発工程案

- 単体測定→2経路の資源/通信契約→双方向リンク→QRのATE連携→7355測定のATE連携→補正フロー→総合試験の順序と完了条件を整理。QRの既得固定接続実績を使い、要求相関を重点工程とした。SS保留、測定取得と補正書込みの分離を維持する。
- 工程案のみ追加。コード／FW／配線変更・実機操作なし、Host／Mock未実行。未回答API・残Issueは確定/Closeしない。[開発工程案](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Development_Steps_After_CDC_Rev0.md)。

## 2026-11-14 7355 USB CDC設定保存とIDN後の電圧・レンジ試験を準備

- PC成功条件（9600/8N1・DTR/RTS両ON・CRLF・識別情報）を集約。保存済みメーカー説明書からSCPIのDC/AC選択、固定/AUTOレンジ、READ?、トリガ条件を確認し、IDN→DC20V単発→200V→AUTOの逐次手順を作成。設定後にQuery応答を受けるUSB制約を反映した。
- 前面BUS/LANGは未確認と明記。ADCのMD?は資料上RS-232/LAN専用のためCDCへ流用しない。コード／FW／配線・原典変更なし。文書・原典照合のみ、Host／Mock・実機測定は未実行。[設定・即試験手順](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/CDC_Settings_Voltage_Quick_Test_Rev0.md)。

## 2026-11-14 追加基板RP2350-USB-Aと7355 USB-B接続を確定

- ユーザーの型番明示を反映し、追加基板USB-A→USB A–Bケーブル→7355 USB-Bを確定。選定記録・基板分離方針・USB-SUB-05を更新し、直前の接続形態確認待ちを解消。既存QR基板の記録・構成は維持する。
- 文書のみ更新。回路・FW適合と親側2リンクは未受入、IssueはOpenを維持。コード／FW／配線変更・実機操作なし、Host／Mockは再実行しない。[選定記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Board_USB_A_Selection_Rev0.md)。

## 2026-11-14 7355用追加HostはQRと同じ基板・USB-Aを指定

- ユーザー指定の基板・端子方針を別記録へ保存し、基板分離方針とUSB-SUB-05へ最新追記。既存QR記録はRP2350-USB-Cのため、USB-Aの接続形態は確認中とし、型番変更や変換器採用を推定しない。
- 文書のみ変更。コード／FW／配線変更・購入・実機操作なし。Host／Mockは再実行せず、IssueはOpenを維持。[選定記録](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Board_USB_A_Selection_Rev0.md)。

## 2026-11-14 ユーザー指定でAlt方式デコードを再採用

- 英語設定の切分けを終了し、Alt方式で続行するユーザー指示を受領。全設定初期化は行わず、qr-uart-20261114.2の保存snapshotから作業C・解析器・テスト／fixtureを復元。11ファイルhash一致、Host／Mock346件成功（9.433秒、skipなし）。
- 実機は.1のため.2再配置とkind12の35文字確認は次工程。正式親子UART・ATE／Cache／SSは未統合、その他Open事項は維持。[再開記録](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/ALT_Decode_Resume_20261114/Resume_Result_Rev0.md)。

## 2026-11-14 QR側の英語設定に合わせAlt処理を撤回・原文取得版へ復元

- ユーザーの設定変更・再試験指示で受信停止。Alt専用C・nativeテスト・fixtureを履歴へ退避し、作業FW／解析器をqr-uart-20261114.1の1024件HID原文取得版へ復元、5ファイルhash一致を確認。
- 復元後Host／Mock326件成功（5.854秒）。旧配布物・旧Alt実機データは保持。実機Flashは.2のままで、.1書戻しと英語設定の再採取は次工程。[復元結果](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/English_Keyboard_Retest_20261114/Restoration_Result_Rev0.md)。

## 2026-11-14 HOST基板内でQR35文字を復元する診断版を準備

- qr_alt_decoder.c／hを追加し、実機VID／PID・記述子に限定したAlt＋5桁数字の復元を実装。完成35文字＋Enterでkind12、異常はkind13。部分データは公開せず、切断初期化・暫定timeout・Enter境界の復帰を管理する。
- 同じCコードのnative実行で両向き実機HID再生等16件、ログ解析追加4件、全Host／Mock346件成功（skipなし）。ARMビルド80ステップ成功、qr-uart-20261114.2のUF2と50ファイルを保存、旧132ファイルのhash一致。
- 正式親子UART・ATE／Cache／Logger／SS、7355・2 Hostは変更しない。新FWの実機配置・基板内復元の実受信は次工程。[仕様・検証・配布](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/Decoder_FW_20261114/Result_Rev0.md)。

## 2026-11-14 Type_C2 QRプラグ両向きで既知35文字一致

- 反転向きBでも393レコード／HID388件、35文字と期待HID全列が一致。向きA／BのHID全388件も一致、Enter1回・解放まで確認。
- 両向き各1回・RST後のPC側照合として記録。FW内デコーダ・連続読取・電源投入起動・保護・7355／2 Hostを未受入として保持。[実機評価総括](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/Result_Rev0.md)。追加のFW・ソース変更なし。

## 2026-11-14 QR既知35文字の単発取得・オフライン完全一致

- qr-uart-20261114.1を対象照合・旧Flash退避・書込みverifyして実機再試験。393レコード／HID388件で既知35文字の完全一致、期待HID全列との一致、Enter1回と解放まで確認。
- これはPC側の既知データ1件の照合。FW内文字列デコーダ・正式親子UART・全ハード受入は未実装／未完。先頭NULと電源投入起動差、両向き・繰返し・負荷・保護・7355・2 Hostを残す。
- [実機原文・結果](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/run05_scan_35chars_1024_rst/Result_Rev0.md)。ソース追加変更なし、直前のHost／Mock326件成功を維持。

## 2026-11-14 QR実機HIDの診断ログ容量を1024件へ拡張

- 35文字QRの1読取で旧256件ログが満杯になり、完全一致を未判定として記録。実機のAlt＋テンキー列を含む原文を保持し、機器設定は変更しない。
- UART版をqr-uart-20261114.1／1024件へ分離。旧RAM版と旧配布物は維持、UARTの76byte形式とHost処理は変更しない。解析上限は既知新版だけ1024、旧版・未知版は256、満杯拒否を維持。
- 新規4テスト・Host／Mock326件成功（5.612秒）。新FWのビルド・UF2検証と配布保存が成功、旧88ファイルのhash一致を確認。実機未配置。[仕様・検証](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/UART_FW_1024_20261114/Specification_Rev0.md)。

## 2026-11-14 USB SubMCU起動UARTの先頭NULを警告付きで診断解析

- 2回の起動rawで先頭00＋正規2レコードを確認。既定の厳密拒否は維持し、明示オプションで先頭1byteだけを分離、元hash・警告・非合格情報を保存する。途中破損・連番欠落・複数ノイズの受理は追加しない。
- 新規7テスト、Host／Mock全322件成功（6.967秒）。FW・原文・旧配布物は変更しない。QR・外部給電起動・電気保護の受入は未完了。USB-SUB-04はOpenとして記録。
- [仕様・検証結果](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/Boot_UART_20261114/Startup_UART_Handling_Rev1_20261114.md)。

## 2026-11-14 実ATEでの未受信問題の解決記録

- ユーザーが実ATE・実NF55Gの総合テストを実施し、前日のATE未受信は終端コードの相違が原因、CR（0x0D）統一で解決と報告。Real_Hardware_Test_LogとATE-TX-01へ記録した。
- 未受信原因調査の完了と、送信証跡・初回ASCII異常・応答遅延の残課題を区別。関連CSV原本は変更せず、コード・設定・実機配置変更なし。文書のみの更新のためHost／Mockは再実行していない。

## 2026-11-13 OI-13のRTCピン割当て確認

- ユーザーが現行RTCピン割当てに競合がないことを確認。I2C0 SDA=GP20／SCL=GP21の実装・仕様・2026-11-10実機受入記録と照合し、OI-13をResolvedへ更新した。
- HW-01のSD基板GP4／GP5分離とDEV-RTC-01の保持課題は別件として維持。文書のみ更新し、コード変更・実機操作なし。Host／Mockは再実行していない。

2026-11-13以前のコミット済み記録は[変更前の履歴](history/CHANGELOG_Before_20261113.md)に保存。現在の記録と併せて参照する。

## 2026-11-13 入替えPico COM6／69f7d45962cfdfadを最新化

- ユーザー指定の元ATE用個体をID照合し、旧26ファイル退避・hash確認後に現行一式を配置。ate_server.py／ate_uart.py／config.py／src main.py／repl_sink.pyの5件が更新。26 Pythonのhash一致・実機compile成功、Host／Mock315件成功。
- 2秒timeout条件の初回実機は13/15。TEST_END直後に遅着を観測したため、10秒待ちで再確認し15/15成功。LOG_DROP_COUNT?=0は3201.859ms、SD／自己診断OK・drop0・REPL実出力確認・NF55G送信0byte。通常main.py再起動後7件成功。57600／8N1・CR・REPL ONで通常待受中。
- 終了直後3.20秒遅延と起動後初回914msは原因未確定で残件。ATE／PIA5100／GPIB実経路は未確認。[個体別配置記録・退避先](Pico_Swap_69f7d459_Update_20261113_Rev0.txt)。


## 2026-11-13 最新FW再配置・全件一致確認

- ユーザー依頼でCOM14／Pico ID `2d35a1e11ac125e3`の旧27ファイルを退避・hash照合後、現行src25 Python＋root main.pyの配置処理を実施。全26件が既に最新版と一致しておりUp to date、内容差分なし。再照合・実機compileも全件成功。
- Host／Mock315件成功、通常main.py再起動後のPC直結7件成功。57600／8N1・応答CR・REPL ONで通常待受中。初回ASCII異常・ATE／GPIB経路は未解決のまま。[確認記録](Pico_Latest_Update_20261113_Rev0.txt)。


## 2026-11-13 初回IDN ASCII異常の追加確認・PC設定復元

- クレジット追加後の再試験で、Host先行7F／FFは初回ERR:ASCII→次回正常を再現。実機RAMでUART受信前段を4条件・8件観測したが全件正常、不正byteなし。初期化直後要求は約1.04～1.05秒後に応答し、起動待ちを確認したがASCII異常の原因とは断定しない。
- 意図しないPC側config欠落をユーザー承認でCR／REPL ONへ復元。旧固定OFFテストもON／OFF直接検証へ復元しHost／Mock315件成功。実機FWファイルは変更せず、通常起動後7件成功、57600／8N1・CR・REPL ONで待受中。
- 実機の初回ASCII異常は今回未再現、原因未確定。物理電源再投入・普段のPCソフトでの再現時rawが残件。[追加確認記録](Startup_First_IDN_ASCII_20261113_Rev1.txt)。


## 2026-11-13 REPLミラー既定OFFを開発Picoへ転送

- COM14／Pico ID `2d35a1e11ac125e3`へ`src/config.py`のみ配置。PC／Pico SHA-256一致、`REPL_LOG_ENABLED=False`と`ATE_BAUDRATE=57600`をPico上で読戻し確認。
- ATE側baud設定が未確認のためMain再起動は保留。COM19の旧115200bps `*IDN?`は無応答で、新57600bpsのATE通信確認とは扱わない。相手側57600bps設定後に再起動・ATE応答確認が必要。[実機記録](Real_Hardware_Test_Log.md)

## 2026-11-13 REPLログミラーの既定OFF

- `src/config.py`の`REPL_LOG_ENABLED`を既定Falseに設定。Falseではsink生成・poll・REPL出力を省略する。Thonnyで確認するときだけTrueへ変更し、config.py配置後に再起動する。
- OFF既定値とsink factoryをテストで確認。Host/Mock全310件成功。REPL出力ON時のUSB stdout write実機待ち時間と57600bpsでのTimingは未測定。通常Timing/HILはOFFを使う。

## 2026-11-13 ATE UART baudrateを57600bpsへ変更

- ATE UART0（GP0/GP1）のbaudrateを設定値`ATE_BAUDRATE=57600`へ変更。ATE側の8N1・CRLF、NF55G UART1の38400bps／8E1設定は変更しない。
- UART初期化テストで57600bps／8N1・GP0/GP1を確認。Host/Mock 309件成功。ATE側装置設定との一致およびPico実機配置・loopback/HILは未確認のため、両端を57600bpsへ合わせる前に単独配備しない。

## 2026-11-13 旧デバッグPico 2を現行FWへ更新・ATE再接続後の確認

- COM14／Pico ID `2d35a1e11ac125e3`を照合し、ユーザー指定により旧FWバックアップなしで現行`src/`一式と`firmware/main.py`を配置。PC／Pico hash一致、MicroPython上のsrc 25 modules compile成功。Main起動。
- COM19再接続後、IDN／IDLE／SD／Self Check正常。ローカルLogger試験T000001でRTC_CHECK、IDN、COMM_STATUSを記録し、REPLミラー出力とTEST_END保存診断OK・drop0を確認。NF55G本体は未接続で製品Transactionなし。
- TEST_END直後のPICO_SELF_CHECK?は742.86ms、待受復帰後3回は57～59ms。遅延原因は未確定。NF55G接続時HIL／TimingとSD CSV独立読戻しは残件。[実機テストログ](Real_Hardware_Test_Log.md)

## 2026-11-13 開発Pico 2を現行MicroPython FWへ更新

- ユーザー指定により旧FWバックアップなしで書換え。COM14のPico固有ID `2d35a1e11ac125e3`を照合し、現行`src/`一式と`firmware/main.py`を配置。主要ファイルhash一致、MicroPython上でsrc Python 25本のcompile成功。
- mpremoteからMainを起動。COM19の`*IDN?`は起動前後とも無応答だったため、ATE疎通・起動後診断・Logger HILは未完了。製品指令は送信していない。結果と全配置hashは[実機テストログ](Real_Hardware_Test_Log.md)。

## 2026-11-13 REPL/debugミラーのPico 2実機確認

- 対象Pico ID `69f7d45962cfdfad`へ既存ファイルを退避後、変更3ファイルを配置し、Pico／PC SHA-256一致とMicroPython compileを確認。
- mpremote監視ではTEST_START→RTC_CHECK?→COMM_STATUS?→TEST_ENDのCSV行を表示し、終了時TEST_LOGGER／TEST_LOG_DROP／SD／drop count正常を確認。続いてユーザーがThonnyでCOM6を開き、`MPY: soft reboot`後のMain起動、T000010のTEST_START／`*IDN?` REQUESTと結果表示を実機確認。
- NF55G Refresh／Control／FUは未送信。ThonnyでのT000010終了診断、NF55G Transaction中のTiming、SDファイルの独立読戻しは未確認。Thonny／mpremoteのCOM6同時オープンは禁止し、soft rebootは試験停止・再起動を伴う。

## 2026-11-13 TEST_START有無のATEローカル処理時間比較

- COM19でTEST_STARTなし／ありを各6回、150ms間隔で比較。RTC_CHECK?、COMM_STATUS?、SD_STATUS?は全件正常。通常Query中央値は約8～28ms、TEST_START／TEST_ENDは約214／208ms。試験時LoggerとREPL mirrorを有効にしても今回のローカルQueryで大幅な定常遅延は観測されなかった（RTC_CHECK?最大75.84ms）。
- 今回NF55G本体は未接続。TEST_STARTなしのSTATUS_REFRESHは1回ACK_TIMEOUT（418.41ms、cmd retry=1／rsp retry=0）となり、再試行・後続NF55G Refreshは停止。この結果は未接続時の観測で製品通信試験ではない。NF55G接続時HILを残件とする。最終IDLE／SD／Self Check／drop0を確認。[実機記録](Real_Hardware_Test_Log.md)。

## 2026-11-13 ATE応答の物理配送とACK_TIMEOUTログレビュー

- 提供CSVをコードと照合し、ATE/TX/RESULTは応答生成イベントでUART送信完了を示さないことを確認。過去のCOM19応答実受信記録も反映し、ATE側応答timeoutがPico処理時間より短い可能性を原因未確定の仮説としてATE-TX-01へ追記。timeout値／遅着受信とATE raw RX、Pico UART送信状態の突合が必要。
- T000053のERP_SET ACK_TIMEOUT後にSE応答frameが遅れて現れるため、設定適用・現状態は未確定。再送・追加Controlを避ける方針を記録。T000053の誤った14桁CLOCK_SYNCと、後続T000054／55の修正済み12桁CLOCK_SYNCを区別。Code／Test変更なし。

## 2026-11-13 COM19 *IDN?応答時間の単発確認

- COM19直結で`*IDN?`を1回送信し、応答を約219msで完全受信。受信待ち15秒の範囲内でCRLF完結を確認した。これはPC直結のシリアル応答測定で、実ATEアプリ／GPIB経路のtimeout検証ではない。ATE-TX-01はOpen継続。

## 2026-11-13 COM19 baudrate比較再試験

- 同一`*IDN?`を57600／115200bpsで各1回送信。57600は3秒無応答、115200は`ERR:ASCII`を約264msで受信し、IDN成功なし。baud/framing/経路不一致の可能性はあるが原因確定せず。ATE-TX-01 Open継続、製品コマンド送信なし。[実機テストログ](Real_Hardware_Test_Log.md)。

## 2026-11-13 ATE→PIA5100受信経路の切り分け継続

- ユーザー観測としてNF55G側UART1波形、RB01G経由、PC serialは正常、ATE→PIA5100→Pico経路のみ未受信との情報を記録。これらをATE UART0の経路試験と混同しない。
- ATE UART0は57600bps／8N1へ変更済みだがMain再起動後の実速度、PIA5100／ATE側通信設定、GPIB timeoutは未確認。ATE-TX-01をOpen維持し、ローカル`*IDN?`による区間別観測を次段階とする。NF55Gコマンド送信なし。

## 2026-11-13 SDログのREPL/debugミラー

- `ReplDebugSink`を追加し、通常治具起動時にSDへ書き込めたログ行を同じCSV形式でMicroPythonの`sys.stdout`へベストエフォート出力する。USB書込可能poll、4096byte有界Queue、1巡32文字上限を設け、通信busy中は出力しない。満杯・未接続・切断時はREPLコピーだけを破棄する。
- Loggerに任意sinkを追加し、SD保存後の行だけを複製。既存のSD／ATE drop countと製品通信契約は維持した。
- Host/Mock 307件成功。MicroPython実機のstdout poll性、Thonny接続時の中断影響、ATE/NF55G同時動作Timingは未確認。Thonny/REPLへ入る操作が動作中アプリを中断し得るため、実機HILで別途確認する。

## 2026-11-11 D1～D5各10回の実機受信時間測定

- D1／D2／D3／D5は現行T2・通常ATE経路で各10回正常取得。D4は製品用T2を変えず、再送なし・Cache非採用のRAM観測で完全応答10回を取得し、各3区間の平均・最大・T2余裕を集計した。
- ACK後平均はD1=14.0、D2=22.0、D3=18.6、D4=116.0、D5=58.9ms。D4は全10回100ms超過、最大133ms。製品FW／Pico処理の寄与は未確定、D4-TIM-01はOpen継続。待ち時間設定を独断変更しない。
- 2本のCSV・102フレームBCC・SD／PC SHA-256と別計算一致、ログ破棄0、通常待受復帰・COM解放済み。[平均表・各回・原本・方式](Spec_Review_20261111/D1_D5_Timing_20261111_112941/Timing_Result_Rev0.md)。製品用ソース変更・配置なし。

## 2026-11-11 D0 T2 300msのPico配置・実機確認

- 既存開発機COM6の25ファイルを退避・比較後、config.pyのみ配置しPC／Pico SHA-256一致。実行中のD0契約が300ms／327文字であることも確認した。
- COM20からS1.13・PS_ON=1／BATT_ON=0のD0正常系10回を実施。全件OK、ACK後完全応答180～182ms、Transaction194～195ms、再送0。CSV22229byte・201データ行の14列／全24フレームBCC／SD-PC hash一致、破棄0、自己診断正常を確認した。
- 通常待受復帰・COM6／COM20解放済み。開始時のATE無応答原因、実機異常系・量産全条件は未確認。OI-02はOpen継続、追加の製品ソース修正なし。[結果・証跡](Spec_Review_20261111/Hardware_D0_T2_300ms_Result_20261111.md)。

## 2026-11-11 D0 T2をr2の300msへ変更

- ユーザーの先行反映指示によりsrc/config.pyのT2_D0_MSを600から300へ変更。AGENTS.mdにD0だけのr2部分採用を明記し、README／ATE／Protocol／Test仕様、実装計画、HIL手順とOI-02を同期した。r2全体への基準切替は行わない。
- 既存D0送信契約テストを更新し、ACK後299／300ms受理、最終試行301ms期限超過、EB介在でも期限非延長の3件を追加。再送上限1、ambiguous／Cache失効、Query無送信を確認した。
- 関連29件、全Host／Mock287件成功（4.797秒）。[変更・検証記録](Spec_Review_20261111/D0_T2_300ms_Implementation_20261111.md)と実行ログを保存。Pico配置・実機試験は未実施。OI-02は実機Timing確認を残してOpen、OI-01／03と他Issueの状態は維持。

## 2026-11-11 RW11通信r2と購入仕様2d5の事前確認

- [改訂仕様影響確認Rev.0](Spec_Review_20261111/Review_Rev0.md)を新規作成。通信r1→r2の全ページ抽出比較と購入仕様の関連本文・表・注記を、現行治具と既存OIへ照合した。原典のhash／ページ数と通信差分を同じ案件フォルダへ保存。
- D0 T2=300ms統一、D4／D5説明長の修正、D3表記、SOC／累積量等を整理。D4文書間不一致、警告設定、QR容量／REV、補正条件、消去・監視・計数条件をSPEC-R2-01～09としてOpen Issuesへ追加。既存OIはCloseせず、回答候補と未解決を区別。
- 現行Host／Mock284件成功（2.721秒）。仕様基準、ソース、テストコード、原典、Pico配置・製品状態は変更していない。r2採用・設計回答後に必要なCode／Test／Docs同時更新を行う。

## 2026-11-11 再START対応の完了整理・懸念事項継続

- 修正・Host／Mock284件・Pico配置・実機正常系3試行・SD／PC hash照合・tempへの再回収を完了として整理。tempの回収コピーはGit管理外とし、案件フォルダ内の正本CSV・解析・配置台帳を保持する。
- QR実入力／新USB遅延応答、実SD異常系、量産Timing、START再送識別は継続調査。SS開発は保留、TEST-SESSION-01はOpenを維持。[完了範囲と残事項](Test_Interruption_20261111/Implementation_20261111.md)。

## 2026-11-11 再START修正版のPico配置・実機デバッグ

- 事前提示手順でCOM6旧25ファイルを退避し、対象4ファイルの配置・PC／Pico hash一致を確認。Host／Mock284件成功。
- SC→D0→Query→10秒→再STARTと3試行を実機確認。再STARTはOK（163.3／200.2ms）、旧DATA QueryはINVALID、3本のCSVに試行分離。全CSVのSD／PC hash・14列、SC／D0全8フレームのBCCと再送0を確認。
- 最終保存診断OK・破棄0・通信IDLE、通常待受復帰・COM解放済み。今回追加の製品ソース修正なし。SS保留、QR／異常系／量産Timing全般は未確認。TEST-SESSION-01はOpen継続。[実機結果](Test_Interruption_20261111/Hardware_Deployment_Result_20261111.md)。

## 2026-11-11 TEST_START再受付：前試行保存と新試行開始

- 試験中の再TEST_STARTを旧試行の排出・flush・close・命名→新試行開始へ変更。通信busy／保存延期／CONT競合はBUSYで新試行を作らない。旧Queueは新ファイルへ流さない。
- 全試験CSVへT000001等の試行IDを付加。同一秒でも分離し、両BANKの既存最大番号から継続採番する。旧／新名を容量集計・循環対象とし、同名ファイルは上書きしない。
- 新試行のQR受信・S/Nと全製品Cacheを失効。自動Refresh／SSは追加しない。完了保存診断と最新8件RAM履歴を保持。SD異常時はCSV保証をせず異常・破棄を記録し、再START中の再mountは行わない。
- Host／Mock284件成功。新規11件と既存ファイル名期待値更新。Code／Test／ATE・Cache・Logger・Interface・Test仕様を同時更新。修正版の実機配置・Timing確認は未実施。SS開発保留、TEST-SESSION-01はOpen継続。[実装記録](Test_Interruption_20261111/Implementation_20261111.md)。

## 2026-11-10 RP2350-USB-C初回受入準備・USBポート割当て固定

- RP2350-USB-C回路図のコネクタ参照名でType_C1（ネイティブUSB）をADCMT 7355、Type_C2（GPIO13/12・PIO-USB）をBCR-TC2D1BKへ固定割当て。機器の入替えをせず、USBハブを標準構成から除外。
- 回路・CC/VBUS・電源の受入前確認、QR／7355個別USB試験、両ポート同時Host動作、Pico 2とのUART疎通準備をRP2350_USB_C_First_Acceptance_20261110.mdへ整理。治具接続図Rev.3を生成し、Rev.2以前は履歴として保持。
- 検証: Rev.3 PDF全3ページを描画・目視確認。文書リンク、PDF/SVG/PNG生成、git diff --check、文書診断を確認。通信コード・テストコード変更、実機受入、USB列挙、7355通信、基板改造は未実施。USB-SUB-01／HW-01はOpen継続。

## 2026-11-10 RTC電源切断・再投入後の保持確認

- ユーザーの電源切断・再投入後、時刻を再設定せず09:59:58→10:00:01 JSTの3秒進行を確認。初期日時への戻りなし、PC日本時間との差5秒以内、control=0x1C／status=0x08／OSF=0。RTC・SD・自己診断正常、drop0、通信IDLE。
- [RTC受入記録](RTC_Acceptance_Recheck_20261110.md)へ結果・証跡を追記。今回1回の切断・再投入では保持成立。実際の電源断時間・電池電圧・長時間保持は未測定。DEV-RTC-01は人間確認前のためOpen継続。コード変更・NF55G送信なし、COM解放済み。

## 2026-11-10 RTC向き修正後の受入再確認（通電機能OK）

- ユーザーが接続向き間違いを申告。修正後のCOM6機でI2C 0x68認識、RTC_SET_20261110_095635成功、6回読出しで10秒進行を確認。control=0x1C、status=0x88→0x08、EOSC=0、OSF=0。SD・自己診断正常、drop0、通信IDLE。
- [RTC_Acceptance_Recheck_20261110.md](RTC_Acceptance_Recheck_20261110.md)へ通電中の合格範囲と証跡を保存。電池保持はユーザーに通常電源の30秒切断・再投入を依頼中。保持・電池電圧・潜在損傷は未確認、DEV-RTC-01はOpen継続。
- コード変更・配置・NF55G送信なし。保守確認後は通常起動へ戻しCOM解放。Host／Mock再実行なし。

## 2026-11-10 RTC電池取付け後の時刻設定確認（通信未成立）

- ユーザーのTime Set・読戻し指示でCOM6開発機を確認。RTC_DATETIME?はERR:NO_RTC、RTC_SET_20261110_095229はEIO。I2C0 GP20/GP21スキャンは検出0件。設定・読戻し・秒進行は未完了。
- [RTC_Battery_Recheck_20261110.md](RTC_Battery_Recheck_20261110.md)へ証跡と未確認事項を記録。再装着・給電・接触等の原因は未確定。通常起動へ戻しCOM解放、NF55G送信・コード変更なし。DEV-RTC-01はOpen継続。

## 2026-11-10 LIFE_SET通常値1点・読戻し・元値復元

- ユーザーがSampleクリア許容、バッテリ／負荷未接続を回答。COM6／COM20、NF55G S1.13／号機000832でLIFE_SET_123の12.3％設定後、LIFE_SET_RAW=00000000で元の0.0％へ復元。新規D0 RAWは000→07B→000。
- SL2回はOK、正常応答DATA0文字、各46ms、cmd/rsp retry0、ambiguous=False、BCC一致。各SL後のDATA無効化、明示D0での読戻しとSTATUS／INFO維持を確認。
- 元のOFF期間RAWはSLで変更され、寿命元値復元後も元に戻らないことを実測。CSV9220byte／91行14列はSD/PC SHA-256一致。終了時自己診断正常、SD OK、drop0、通信IDLE。待受復帰とCOM解放済み。
- 詳細は[実機結果](Life_Set_Hardware_Test_20261110.md)。製品コード追加変更なし、Host／Mockは直前273件成功。範囲外・不正RAW、保守識別値、外部動作・保持は未検証。OI-08はOpen継続。

## 2026-11-10 LIFE_SET再開・配置と元値退避（SL未送信）

- ユーザーがSL先行とSampleのデータクリア許容を回答。COM6へSL差分3ファイルを退避・配置し、24ソースの実機compile／SHA-256一致を確認。Host／Mock273件成功（2.496秒）。
- COM20でFW S1.13／製造号機000832、積算寿命RAW000＝0.0％とOFF期間／D0原文を退避。CSVは256byte分割回収・SD/PC SHA-256一致。最終自己診断正常、SD OK、drop0、通信IDLE。
- 物理バッテリ・負荷状態の確認回答待ち。SL未送信、通常値書込み・読戻し・復元は未確認。[Life_Set_Hardware_Test_20261110.md](Life_Set_Hardware_Test_20261110.md)へ証跡を記録。範囲外試験なし、OI-08 Open継続。

## 2026-11-10 作業中断・次回コマンドデバッグ引継ぎ

- 会議のため本日の開発・デバッグを一旦終了するユーザー指示を記録。Next_Command_Debug_Handoff_20261110.mdへ再開確認、専用Sample準備後のLIFE_SET候補、バッテリ条件整備後のBC、保留項目と証跡保存を整理。
- 実機接続・送信・配置・コード変更・追加テストなし。過去の機器状態を現在状態と断定せず、実施済み／未確認を区別。Issue状態は変更しない。

## 2026-11-10 共通ベースを示す治具図面Rev.2・SVG編集説明

- Pico-Quad-Expanderの枠内へPico 2／RTC／SD／RS232C 2CHの4基板を配置し、共通ベースであることを明確化。HOSTは枠外の追加機器として表示。GPIO割付・既存仕様は変更しない。
- docs/drawings/NF55G_Fixture_20261110_Rev2へPDF／SVG／PNGと編集方法READMEを保存。Rev.0／Rev.1は保持。SVGの文字・図形・線は個別編集可能、線の自動追従や生成スクリプトとの自動同期はないことを説明。
- PDFの表示・文字収まり、SVG構文を確認。通信コード変更・実機操作・Host／Mock再実行なし。加工・結線の未確定事項は継続。

## 2026-11-10 Pico-Quad-Expander接続を図面Rev.1へ反映

- ユーザー補足により、RTC／SD／RS232C各基板はPico-Quad-Expander経由の接続と明記。全体図のPico周囲にExpanderを表示し、GPIO共有、既存ヘッダー接続、追加HOST用UART引出し案を反映。READMEのハード構成も補足。
- docs/drawings/NF55G_Fixture_20261110_Rev1へPDF／SVG／PNGと説明を保存し、Rev.0は保持。スロット位置・向き・積層順・追加引出し位置は推測しない。既存GPIOとSD GP4/GP5分離条件は継続。
- 全3枚のレンダリングを確認。通信コード・実機配線変更なし、Host／Mock再実行なし。USB-SUB-01／HW-01はOpen継続。

## 2026-11-10 治具接続・GPIO割付図 Rev.0（追加発注説明用）

- docs/drawings/NF55G_Fixture_20261110_Rev0へA4横3枚のPDF、編集用SVG、PNGプレビューと資料READMEを作成。生成スクリプトはscripts/build_fixture_connection_drawing.py。
- 全体接続、Pico物理ピン付きGPIO、追加／改造範囲を整理。RTC／SD／RS232 2CH、ATE–PIA5100、NF55G、追加HOST–USBハブ–QR／7355を記載。現行と候補を線種・色で分離。
- 再発注時のADA-5703 GP4/GP5分離、追加UART引出し、USBホストCC／VBUS確認と給電・固定を説明。コネクタ撤去やUSB直付けの要否は未確定。端子番号・加工位置を推測しない説明図とし、製造用結線図は後続。
- PDF全3枚のPNG目視、文字抽出・GPIOと公式pinoutの照合を実施。通信コード変更なし。実機改造・接続・配置なし。HW-01／USB-SUB-01はOpen継続。

## 2026-11-10 QR／DMM共通USB下位マイコン・UART連携の開発準備

- 添付の過去会話で指定されたWaveshare RP2350-USB-Cと、今回指定の治具Pico 2との双方向UARTを要求として記録。11/09のUSB-A候補案は履歴として保持し、基板固有の改造条件を転用しない。
- USB_Host_SubMCU_Integration_Plan_20261110.mdを新規作成。BCR-TC2D1BK／7355の役割、既存UART0／1使用中という制約、PIO RX＋TX案、内部コマンド・データと要求相関、シャント換算、電源・部品・段階試験を整理。
- QR／外部測定要求、従来変更案、Interface、Test仕様へ参照を追加。USB-SUB-01をOpen追加し、正式API・配線・給電・CDC実適合・Timing等は未確定として管理。既存IssueはCloseしない。
- 検証: python -m unittest discover -s tests -v、Host Unit／Mock NF55G全273件成功（5.750秒）。資料整理のみでコード・テストコード・原典資料の変更なし。新基板ビルド、USB／UART実機検証、Pico配置は未実施。ハード入手後に開発・デバッグへ進む。

## 2026-11-10 ATE要求のCR／LF／CRLF終端対応

- ユーザー指定により全3終端を受理し、定期CRを含む空行は無応答で無視する。CR待ちを廃止し、後続正常コマンドのERR:FRAMEと空CRによるidle処理阻害を解消。応答はCRLFを維持。
- 分割到着テストを新仕様へ更新し、D0一回実行・空行・異常復帰・Queue上限の回帰テストを追加。実機結果はATE_Line_Ending_Fix_20261110.mdへ記録する。

## 2026-11-10 項目別PARAM実変更・復元の実機結果照合

- 前日実行した通常10項目の変更・読戻し・復元が完了していることを確認し、SD原本を分割回収。SP20件、D5 21件、BCC82フレームと各復元後のD5全100文字一致を検証。ATE最短間隔101.0453ms、ログ破棄0。
- 現在のINFO全26項目も元値と一致。Parameter_Item_Hardware_Test_20261110.mdとATE_Command_Masterへ実機範囲・未確認条件を追記。製品コード・配置変更なし。実動作とRTC保持は別途確認。

## 2026-11-09 CSV回収時の欠落再現・ATE速度条件確認

- LOGGER-CSV-01を再確認し、SD原本は正常、一括REPL HEX回収時のPCコピー欠落と判明。PARAM旧コピー96 byte、ERP旧コピー32 byte不足。再現3回とも欠落。256 byte分割回収＋SD/PC SHA-256照合へ試験用回収方法を変更し、旧コピーと正常版を別保存。製品Logger実装は変更していない。
- ATEはユーザー指定の0.1秒に1コマンド程度を条件とする。実測最短101.0623msの117コマンドでログ破棄0、CSV全239行14列、SD/PCハッシュ一致。CSV_Log_Recovery_Recheck_20261109.mdへ証跡と前報の訂正を記載。IssueはOpen継続。

## 2026-11-09 開発機・実装済みATEコマンド実機デバッグ

- COM6／COM20でD0/D1/D5、EL/OL全ブロック、ERP4組合せ、CLOCK_SYNC後D2、PARAM_SETと項目別PARAM同値書戻しを実機確認。ERPは元の0/0へ復元。ローカル拒否時のNF送信なしをCSVで確認。
- 無間隔339応答でログ391件破棄、項目別SPの送信RAW CSV行1件に列欠けを観測し、LOGGER-BURST-01／LOGGER-CSV-01をOpen追加。外部動作・量産Timingや未実施の副作用コマンドを正常扱いしない。詳細はDevelopment_Unit_Command_Debug_20261109.md。コード・配置変更なし。

## 2026-11-09 開発用COM6機 RTC・SD受入確認

- 固有ID69f7d45962cfdfadを照合。RTC設定・読戻し・進行、SD初期化・記録・再マウント・電源切入後の保持を確認。配置25ファイルは13:18の配置時点と全件一致し、今回はソース再配置・UF2更新なし。
- 約124GBのSDはexFAT署名によりVFS_MOUNTでMOUNT_ERR。ユーザーの全データ消去許可後にFAT32初期化し正常認識。64マーカー・全73データ行のCSVを保存・回収し、再マウントと2回の電源切入後もSHA-256一致、drop0。
- RTCは日本時間設定・発振条件EOSC=0を確認したが、約30秒電源断後に2回とも初期日時へ戻りOSF再セット。DEV-RTC-01をOpenで追加し、総合受入は保留。電池・VBAT等の実測は未実施で原因は未確定。
- 詳細はDevelopment_Unit_Acceptance_20261109.md。実装変更なし、Host / Mock再実行なし。UART送信ガード下のRTC・ログ確認はNF55G送信試行0。製品PASS / FAIL判定なし。

## 2026-11-09 ATE設計者向けコマンド一覧 Rev.1

- Rev.0-draftのMarkdown / Wordを変更せず保持し、日付付きのATE_Command_List_for_Test_Program_Rev1_20261109.md / .docxを新規作成。既存一覧の構成・表現を基本維持し、実装有無欄は実装済みのみ「※」、未実装は空欄とした。
- PARAM_SET、CLOCK_SYNCの10進日時指定とASCII HEX変換、実応答形式、最終Self Check・SD復帰条件、試験指示書§7.1～7.5の使用例と注意事項、略語、実機確認範囲・量産制約を追加。正式ATE入口と診断スクリプト、Host検証と実機成立を区別した。
- CLEAR_DATAの消去範囲対応をATE-CLEAR-01、SSの「それ以降は0000」の領域対応をOI-23の追加確認として記録。仕様・製品通信コード・Issue状態は変更しない。
- Word生成スクリプトへ入力 / 出力パス指定、版数連動フッター、実装有無欄の幅、表見出しの繰返し・行分割抑止を追加。
- 検証: Host Unit Test / Mock NF55G Test全210件成功。実装印144件と共通Command Coreの定義を照合。WordでPDF出力し全27ページの画像を目視確認、表見出しだけの改ページを抑止。元Markdown / WordのSHA-256一致で未変更を確認。Pico配置・実機操作なし。

## 2026-11-09 試験ログ・QR S/N命名・最終Self Check

- ATE要求と実行結果を既存NF55G RAW／transactionログへ追加。TEST_START後のQR末尾6桁をRAM連携し、終了時にS/N＋開始日時へ変更。未取得・不正時は日時名を維持し、命名衝突は既存ログを上書きしない。
- TEST_START／TEST_ENDはSD異常でも試験受付・終了のOKを返し、装置異常は最終Self Checkへ分離。TEST_LOGGER／TEST_LOG_DROPを保持し、終了後の復帰で直前試験の保存異常を消さない。
- Logger／ATE／Interface／Runtime／QR要件／Test仕様とOpen Issuesの確定済み部分を追記。IssueはCloseしない。Host／Mock全195件合格。Pico配置、新QR物理入力、実カードのrename・抜き差し・Timingは未実施。

## 2026-11-09 SD抜き差し・試験終了後復帰

- SDログ開始失敗時も試験期間を保持し、試験中・連続記録中のSD_REINITをERR:BUSYで拒否。SD異常は保持し、再挿入だけで記録を再開しない。
- TEST_END／LOG_CONT_STOP後、ATE応答・待ち要求とNF55G通信を優先し、待機時に1回だけ再認識。電源投入時の既存FATマウント、フォーマット禁止、SD異常でも通信継続を維持。
- 未保存Queueの持越しを防ぎ、破棄件数を計上。SD異常時の既存ATE応答形式は維持。Logger／ATE／Runtime／Test仕様を更新。
- Host／Mock全189件合格。Pico配置・実カード抜き差し・冷間起動・Timing検証は未実施。既存CMD0不具合とOpen Issuesは未解決。

## 2026-11-09 CH9350によるQR・測定器制御の変更意向

- 提示画像2点を原本コピー保存し、QRリーダーをBCR-TC2D1BKと記録。メーカー公式のUSB HID／Type-C／動作時230mAを確認し、QR要件と共通化案に反映。Type-C下流接続・給電・HID形式・7355との共存は未検証。コード変更・実機試験なし。
- 最新指摘によりQRとDMMをWaveshare側へ共通化する方針へ修正。RP2350-USB-A＋USBハブでHID／CDCを扱う案、機器識別・同時接続・片側切断等の確認項目を変更要求に反映。直前のQR用CH9350を残す案は経緯として扱う。資料上の対応と実機未検証を区別し、コード・試験結果は変更していない。
- 7355用追加マイコンをWaveshare製とするユーザー指定を記録。RP2350-USB-Aを第一候補に、CDCホスト用C/C++実装、R13等の現物照合、単体通信から治具連携へ進む開発案を追記。型番確定・実装・基板改造・実機試験は未実施。
- 追加回答により測定器をADCMT 7355、接続をUSBと確定。保存済み取扱説明書§6.4でUSBTMC／CDCを確認し、HID用CH9350では対応しないとの資料上の判断、別USBホスト構成案と残確認事項を追記。従来外部測定要求に変更案への参照を追加。構成採用・実装・実機試験は未実施。
- CH9350でQR読取とマルチメーター制御の両方を行う意向を別文書に記録。HID用途と測定器USB制御の互換性は未確認としてCH9350-06を追加。
- 要求記録のみ。コード・正式接続仕様は変更せず、Host／Mock／実機試験は未実施。

## 2026-11-07 D3/D4 Refresh Host実装

- `D3_REFRESH`と`D4_MAINT_READ`を共通Parser/Dispatcherへ接続し、仕様既定のNF CMD、T2、応答長でDecode後に各CacheをVALID化。
- D3/D4成功時とambiguous failure時にDATA Cacheを無効化する契約を統合テストで確認。Decode失敗時も対象CacheをINVALIDのまま維持。
- Host/Mock全183件成功。ATE個別Query名は未定義のため追加せず、Pico配置・実機HILは未実施。

## 2026-11-07 NF55 RAWのASCII表示

- NF55送受信RAWの `raw_ascii` をRAM Queueの書出し時に生成。印字可能文字を表示し、制御文字・非ASCIIを `\xHH`、バックスラッシュを `\\` として保持する。`raw_hex`や過去CSVは変更しない。
- 書込み前に通信busyを再確認。Host/Mock全176件合格。Picoへ配置し、MicroPythonでSC・ACK等の表示変換を確認。通信中を含む実機タイミングと新しいNF55 RAWのSD書込みは未検証。

## 2026-11-07 RTC基準SC実機確認

- 変更済み4モジュールを退避・配置し、PicoとのSHA-256一致を確認。RTC `20261107_153531` をSCで送信し、直後のD0日時も同値。後続RTCとの差は-1秒（逐次取得）。
- SC/D1/D0の保存RAWはBCC一致、再試行0回。停電後や長時間の保持は未確認。D2-PS-01とOI-03はOpenのまま。

## 2026-11-07 SC Host実装とTIME変換修正

- `CLOCK_SYNC`に明示10進日時を渡し、SC DATA各欄をASCII HEXに変換。正常応答DATA長0、不正入力の送信拒否、成功・成否不明時のDATA/STATUS無効化を追加。
- D0/D4のTIMEをASCII HEX数値から10進日時へ変換。既存の日時Mockデータも原典形式に修正。
- 実機D0の時刻欄 `1A0B03100730` を観測。修正前表示は `201A0B03_100730`、修正後のオフライン解釈は `20261103_160748`。SC送信・配置・保持確認・D2実機試験は未実施。
- Host/Mock全173件合格。SC単体の実機応答や時刻保持はまだ確認していない。
- OI-03とD2-PS-01は未解決。SCの時刻差はAC OFF時間計算へ影響し得るため、試験時刻は担当者が決定する。

## 2026-11-04 補正方式の選択要件

- ①コマンド＋数値による直接書込み、②測定値取得・ATE判定後の別の数値付き書込み、の両方式を利用可能とする要件を追加要求仕様・開発計画に明記。
- ①は7355読取りの事前実行を不要とし、②は取得時に自動書込みしない。両方式の検証予定を追記。書込みコマンド名称の共通化／分離は詳細設計で決定する。
- 既定の開発順序を維持。文書のみ更新し、Code／Test変更・Host／Mock・実機試験は未実施。

## 2026-11-04 追加機能の開発順序

- ユーザー指示により「現在の実機確認 → QRコード読取り → 7355連携による外部測定値取得・補正機能追加」をImplementation Plan、README、追加要求仕様に反映。
- 7355の通信仕様・アドレス設定の詳細化、実装・試験を後続ステップとして記録。資料はreference/ADCMT_7355_20261104に保存済み。既存Phaseの並び・Issueの状態は維持。
- 計画文書のみ更新。Code／Test変更なし。Host／Mock・実機試験は未実施。

## 2026-11-04 外部測定値による補正の追加要求

- 7355の通信仕様・アドレス設定を仕様化対象へ追加。設定項目、未確定値、受入確認項目を追加要求文書に記載し、CAL-EXT-03で管理。メーカー製品ページでGPIB+01／ADC・SCPI対応を確認。マニュアル本文・実機設定は未確認。

- 7.3の3対象・各2点の設定目安と、既存の数値指定方式に追加する外部実測値取込み要求を別文書へ記録。
- ユーザー指定のUART0／PIA5100／GPIB／7355接続、外部シャント抵抗・製品電圧の測定、ATE側の測定対象制御を記録。
- 追記確認: ①DISCHG_I／充電、②BATT_CHG／放電はユーザー確認済み。取得値をATEへ返して判定後、別の数値付き書込み指令でNF55Gへ書き込む。取得による自動書込みは行わない。
- 未確定の転送手順、補正点対応、換算・正式コマンド等をCAL-EXT-01/02で継続管理。既存AD/AR IssueはCloseしない。検証予定に取得だけでは書き込まないことと書込み指定値の使用を追加。
- 要求整理のみ。正式コマンド・Code／Testの機能追加は詳細確定待ち。Host／Mock・実機試験は未実施。

## 2026-10-14 RP2350-USB-A QR入力サンプル調査

- Waveshare公式デモZIPとTHLN33固定コミットの主要8ファイルをreference/RP2350_USB_A_research_20261014へ原典コピーとして保存。SHA-256を記録。
- HIDからASCIIへの変換、USB CDCとUARTの出力先、THLN33の13byteフレームとAZERTY配列をソース確認。既存QRの35文字＋LFへの変更案を調査資料へ整理。
- 基板抵抗に関する実装者の報告、依存版、実レポート形式と量産安定性をRP2350-QR-01/02としてOpen Issuesへ追記。今回基板の改造要否は未確定。
- 検証はソース比較、保存ファイルのハッシュ照合、文書差分チェック。実装変更なし。ビルド・Host/Mock再実行・実機試験は未実施。

## 2026-11-07 D2_REFRESH Host実装

- `D2_REFRESH`（NF CMD D2、T2=100ms、DATA 30文字）を共通Dispatcherへ追加し、OFF_PERIODをD2 Cacheへ保存。
- D2 Protocol SUCCESS時にDATA Cacheを無効化し、ambiguous failure時もD2/DATAを安全側で無効化。D2専用ATE Query名は未定義のため追加せず。
- 成功Decode、T2/長さ、Cache invalidation、Decode失敗、ambiguous timeoutを含む全Host/Mock 164件が合格。Pico未配置・実機D2 HIL未実施。

## 2026-11-07 DATA_REFRESH (D0) Host実装

- `DATA_REFRESH`をNF CMD D0、T2=600ms暫定、応答DATA 327文字で実装。全DATA QueryはCacheのみ参照し、自動Refreshしない。
- D0内STATUS/Manufacturing/ParameterをDATA以外のCacheへ昇格しない。TIMEのASCII HEX検証を追加し、Decode不完全時にDATAをVALIDにしない。
- OI-03は未解決のまま維持。D0 ACK後のCHARGE_END挙動をPico側で補正しない。D0実機HILは未実施。
- 全Host/Mock 164件合格後、D0 integration/decoder focused 34件合格。Pico配置および実機D0通信は未実施。

## 2026-09-28 実機デバッグ前のコード説明コメント

- `src/`の24 Pythonファイルと`firmware/main.py`、`firmware/sd_startup_probe.py`に日本語の概要コメントを追加。各モジュールの役割と、ATE受信から通信・Decode・Cache更新・ログ保存までの流れを説明。
- 主要処理には、FU拒否、再送の分離、EB処理、Refresh開始時のINVALID、Queryの自動Refresh禁止、通信中のRAM記録、QR単独試作の境界を追記。
- コメント追加前後で全26ファイルのASTとコメント・空行以外のトークンの一致を確認。仕様・実行ロジックの変更なし。
- 検証: `.venv\Scripts\python.exe -B -m unittest discover -s tests` — Host/Mock 161件成功。
- Picoへの配置・実機通信は未実施。既存の未コミット変更を保持し、Open Issuesは変更・Closeしていない。

## HOST TX0比較ログ: 前機器Usage残留の調査

- L-46Xはキーボード経由でもReport解析ログが出ない一方、keyboard登録とD2点灯を確認。公開FWの取得エラー無視・Usage残留を原因候補として調査記録とOpen Issuesへ追加。実機原因は未確定。

## HOST TX0診断受信の追加

- GP10/PIO0 SM1/230400bps専用診断スクリプトを追加。既存PIO受信のpin/baud/SM/bufferを引数化しQR用既定値を維持。
- 大容量リングのwrap/overflowと不正サイズ拒否のHost試験を追加。実機ログ取得結果は別途記録。

## QR認識切分け - L-46X単体再接続では回復せず

- キーボードなしの通常起動後、L-46Xのみ抜き差ししてもD2消灯のままとユーザー確認。調査書・手順・実機ログ・OI-23へ反映。
- キーボード先行認識条件との差を優先調査。特定FW不具合の断定・設定変更・コード変更は行わない。


## QR認識切分け - D2消灯後のL-46X再認識を確認

- キーボード取り外しでD2消灯、L-46X接続で再点灯をユーザー確認。調査書・手順・実機ログ・OI-23へ追記。
- 前機器の表示残留という説明を除外。電源投入直後との差の根本原因は未確定。コード変更なし。


## QR認識切分け - キーボード経由の回復条件

- キーボード接続後にL-46Xへ差し替えるとD2が点灯するとのユーザー報告を記録。調査書・試験手順・実機ログ・OI-23を更新。
- 取り外し中のD2消灯とリーダによる実データ再受信は未確認。履歴依存の候補として扱い、根本原因の断定や恒久対策化は行わない。コード変更なし。


## L-46X通常起動時の認識継続調査

- 通常起動でもD2消灯と確認。メーカー公開FWの認識条件と未確定事項をL46X_USB_Recognition_Investigation.mdへ記録。実機FW一致・根本原因は未確定。設定/コード変更なし。


## QR切分け追報 - L-46X長押し起動操作の確認

- ユーザーの「強制初期化」は電源投入時トリガ10秒以上長押しと確認し、試験手順・実機ログ・OI-23へ記録。設定への影響は原典未確認として保持。コード変更なし。


## QR切分け追報 - 電源再投入後のD2消灯再発

- 電源切/入でD2消灯、QRリーダ初期化とのユーザー報告を試験手順・実機ログ・OI-23へ記録。先の受信成功と起動再現性を区別。
- 初期化内容/操作順と起動後USB接続の比較は未確認。コード変更なし。


## QR再試験 - 35文字受信・分割・Cache・REPL表示成功

- COM14でQR_TEST READYを確認。US250A-CGXE-009491-10101A2623000001とLF（36byte）を受信し、6項目と先頭ゼロ保持を確認。
- QR手順・試験仕様・実機ログ・OI-23を更新。コード変更なし。SS/CSVは対象外。認識改善要因は未特定のためIssueはCloseしない。


## QR切分け実測 - キーボードABC+EnterをPicoで受信

- COM14でABC+LFの4byteを確認し、期待どおりQR_LENGTHとなった。ホストTX1→GP9 PIO受信とLF終端検出の動作を実測。
- 試験手順・実機ログ・試験仕様・OI-23に記録。L-46Xによる実QR受信は未確認。コード変更なし。


## QR切分け追報 - USBキーボード認識成功

- 通常USBキーボード接続時はD2点灯とユーザー確認。L-46X接続時との差を試験手順・実機ログ・OI-23へ記録。UART/Pico受信成功とは区別する。コード変更なし。


## QR切分け追報 - 給電確認とLED識別訂正

- HOST 5V/VBUS両端子への給電OKをユーザー確認として記録。
- LED取り違えの可能性から、以前のD2点灯・ホストHID認識済み判断を撤回し、確認待ちへ訂正。QR試験手順・実機ログ・OI-23を更新。コード変更なし。


## 2026-09-26 - HID認識確認とQR受信診断追加

- PCでのHID入力とホストD2点灯をユーザー確認。Picoの直近timeout時Cacheは原文0文字。
- 試験専用の受信byte数/先頭64byte/総受信数の表示を追加し、タイミング外入力と無受信・終端不足を切り分ける。Host159件合格、Pico上の応答Mock試験合格。


## 2026-09-26 - QR試験ATE応答のMicroPython互換性修正

- COM10送信後、応答バッファのbytearray部分削除がMicroPythonでTypeErrorとなり試験が停止。スライス再代入へ修正してPicoへ再配置。
- Host/Mock159件合格。Pico上で試験runをMockポートに接続し、2byteずつの分割応答がIDLE+CRLFとして完了することを確認（ATE_PARTIAL_TX_PICO_OK）。実QR受信は未確認。


## 2026-09-26 - QRホストへのVBUS/5V給電接続を記録

- ユーザー報告のPico VBUS→HOST VBUSおよび5V両端子の給電接続完了を、試験手順・OI-23・実機ログに反映。
- 電源実測とQR読取結果は未確認。コード変更なし。


## 2026-09-26 - QRテスト機OPTICON L-46Xを記録

- QR要件・試験手順・OI-23・実機ログにテスト機型番とCOM10=ATE/COM14=REPLを記録。
- USB HID設定・Enter付加と実読取は未確認。文書のみの更新でコード変更なし。


## 2026-09-26 - 接続済みQR用PIO受信を追加

- GP9 RX/GP8 idle HighのPIO受信adapterと専用start()を追加。ATE UART0と共存し、NF55G UART1は変更しない。
- Host/Mock159件合格。COM14へ試験専用3ファイルを追加し、PIO初期化とGP9/GP8 High、受信エラーなしを確認。確認後停止。
- main.py/既存srcは変更なし。手順・Interface/Test/Open Issues・実機ログを更新。光学QR読取とATE指示の実測は待機中。


## 2026-09-26 - QR用GPIO候補調査

- 既存コードとRTC/RS232/SD資料を照合し、TX=GP8（物理11番）・RX=GP9（物理12番）・GND=物理13番を候補としてQR試験手順に記録。実配線確認は未実施。
- UART1の別ピンであるためNF55G用UART1と独立使用できないこと、共存時はPIO UART実装が必要であることを明記。今回コード変更・GPIO初期化・実機試験なし。


## 2026-09-26 - QR単独受信試作

- ATE開始後の35文字受信、6項目固定位置分割、一時RAM Cache、REPL表示の独立試作を追加。英数字とハイフンを許可。
- QR取得はSS連携と分離し、正式Cache名/SS変換/本番統合は保留。LF/CRLF・10秒timeout・100ms入力無通信確認は試験設定。
- 保存済みマニュアル/図面を確認し、手順・関連仕様・OI-23・Host試験を更新。実機はCOM未検出、配線/リーダ設定待ち。
- Host/Mock: 156件合格（QR新規9件）。Python構文検査・git diff --check合格。実機配備・HID読取・REPL表示の実測は未実施。


## 2026-09-18 - QR製品REVと通信仕様の差異を確認事項として保持

- ユーザーがQR製品REV3桁とUNIT_REV4バイトの差異を認識し、確認事項として残すよう指定。OI-23とQR要件に通信仕様r1 p.22 §8.5.3の根拠を追記。
- ラベルと通信仕様の整合、格納・変換方法は未確定。補完処理やCode変更、IssueのCloseは行わない。


## 2026-09-18 - QR REVは製品REV

- ユーザー指定によりQR REVを製品REV（UNIT_REV対応）と明記し、FW_REVISIONとは区別。QR要件・ATE仕様・OI-23・試験仕様を更新。
- QR3桁からUNIT_REV4桁への格納規則は未確定。Code変更なし。


## 2026-09-18 - FW_REVISIONは仕様書との照合のみ

- FW_REVISIONがFW書き込み仕様書のREVSIONと一致することを確認する要件をQR要件・ATE仕様・試験仕様・OI-23に記録。SS書込み対象外を維持。
- 比較元仕様書・期待値・比較規則・照合担当は未確定。今回は要件記録のみで、Code変更や実機照合は行っていない。


## 2026-09-18 - 生産情報のSS書込み範囲確認

- 生産LOT・生産年月・S/N情報の書込み範囲をUNIT_REV～BBU_SRLの9項目としてユーザー確認を記録。QR要件、ATE仕様、OI-23、試験仕様を更新。
- 各項目への割当て、QRの製造年/製造週と生産年月の関係、REV変換は未確定のまま。Code変更なし。


## 2026-09-18 - SET_SERIAL書込み対象の記録

- ユーザー提示画像を保存し、SS対象9項目と画面SRL/既存SERIALの名称対応をQR要件・ATE仕様に記録。
- QR REV3桁と既存UNIT_REV4桁の変換、LOT/SERIAL対応、ADU/BBU取得元をOI-23に明記。FW_REVISIONはGET表示のみ。試験仕様と資料一覧を更新。
- 詳細未確定のためCode変更なし。


## 2026-09-18 - QR読取CacheとSSの紐付け方針

- ユーザー指定により、QR読取値の書込みコマンドをNF55G SSとし、保存Cache名と詳細フィールド紐付けは後日決定する方針を記録。
- QR要件、ATE/Cache/Test仕様、OI-23を更新。自動書込み禁止を維持し、Code変更・Cache追加・SS連携実装は行っていない。


## 2026-09-18 - QRフィールド6項目の桁数指定

- 製造年2桁、製造週2桁、製造号機6桁を追加。品名8桁・品目コード14桁・REV3桁と合わせた項目合計は35桁。
- QR要件、OI-23、試験仕様を更新。文字種・範囲・配置順・区切りは未確定で、受信全長や切出し位置は推測しない。Code変更なし。


## 2026-09-18 - QRフィールド3項目の桁数指定

- 品名8桁、品目コード14桁、レビジョン（REV）3桁をQR要件に記録し、OI-23と試験仕様を更新。
- その他の桁数、文字種、配置順・区切り等は未確定。部分仕様の記録のみで、Code変更・QR機能実装はなし。


## 2026-09-18 - ATE主導QR工程の詳細要件

- QR読取、原文取得、解析・妥当性検証、解析値取得、変換・明示書込み、必要時の明示読出し・照合を工程分離する要件とコマンド案を記録。
- QR原文・解析値・書込み結果のCSV記録、ATEへの異常コード返却を追加。自動書込み禁止とATEによる製品PASS/FAIL判定を維持。
- QR要件、ATE/Cache/Logger/Test仕様、OI-23を更新。名称・形式・ハード制御・照合担当は未確定。Codeと実行テストの追加は詳細確定後とし、今回も機能未実装。


## 2026-09-18 - 製品銘板図の保存

- 訂正されたDesktopのパスからNF55802-G_01.pdfをrequired_for_developmentへ保存し、SHA-256一致を確認。
- 参照資料一覧、QR要件、OI-23の未保存状態を更新。本文解析・Code変更なし。詳細仕様とOI-14/OI-23は未確定のまま。過去の未保存記録は当時の履歴として保持。


## 2026-09-18 - QR読取経路とCache利用要件の部分確定

- ATEのPico専用読取開始後、QRリーダと「かんたんUSBホスト HIDキーボード用」を介してPicoへ取り込みCacheする要件を記録。
- Cacheを後続のNF55G書込みとログファイル名に利用する。自動書込みは行わない。
- ATE/Cache/Logger仕様、将来の受入試験観点、OI-14/OI-23、参照資料一覧を更新。詳細仕様未確定のためCodeと実行テストの追加は保留し、機能を未実装と明記。
- USBホストマニュアルは保存済み。銘板図は指定元パスに存在せず未保存・未読。以前の記録は当時の状態として保持。


## 2026-09-18 - QR label read/write feature discussion recorded (no implementation)

- Recorded a new discussion: reading product label QR (revision/year/week/serial) and writing parsed values into NF55G, driven step-by-step by explicit ATE commands (proposed: `QR_SCAN`/`QR_GET`/`QR_PARSE`/`QR_DATA`/existing NF55G WRITE-READ/`QR_VERIFY`), with a proposed Pico-side `QR_RAW`/`REV`/`YEAR`/`WEEK`/`SERIAL`/`VALID`/`TIMESTAMP` cache.
- Product nameplate drawing `NF55802-G_01.pdf` was shared as future reference for the QR format but has not been added to `reference/`, and no textual field layout was provided.
- No code, command, or cache was implemented. Added `docs/Open_Issues.md` OI-23 to track all unconfirmed items (QR field layout, command/cache names, reader interface, and Pico 2 vs Pico 2 W hardware choice for a possible BLE HID Host reader).

## 2026-09-16 - Pico 2 hardware communication test

- Recorded the COM14 HIL results for microSD, DS3231 RTC, and two-channel RS232C in `docs/Real_Hardware_Test_Log.md`.
- SD passed after one retry and RTC passed; RS232C UART initialization passed but both loopback receive checks returned zero bytes. No NF55G command/control was transmitted.

## 2026-09-16 - RS232C loopback retest after wiring correction

- Re-ran the COM14 RS232C HIL after correcting the loopback wiring. CH0 and CH1 both passed 256-byte exact loopback and 100-frame stress with zero crosstalk.
- No NF55G command/control was transmitted.

## 2026-09-16 - Base board selection update

- Replaced the hardware baseline base board identification with SeeedStudio 103030397 (GPIO EXPANDER QUAD RASPBERRY PI PICO).
- Kept the existing UART, RTC, and microSD GPIO assignments unchanged; electrical and mechanical verification of the new base board remains a hardware follow-up.

## 2026-09-10 - Runtime clock, EB, ATE, and real SD integration

- Integrated shared Pico-compatible monotonic clock, bounded EB processing without Cache promotion/deadline resets, transaction exclusion, UART exception results, and protocol-level FU blocking.
- Added operator-confirmed CRLF ATE transport and cooperative scheduler, partial reply handling, RAM protocol traces, and transaction summaries.
- Added FAT CSV sink and HIL-derived SPI SD driver with CSD capacity, bounded waits, RTC filenames, owned bank rotation, deferred flush, and failure/reinit handling. Fixed host CSV CRLF corruption and deferred-flush recovery found by tests.
- Added 31 runtime Host/Mock tests; all 136 tests passed. Added `Runtime_Integration.md` and deployment entry-point candidate; updated related specifications. No Pico deployment or real NF55G communication was performed. Physical SD/firmware timing validation and Open Issues remain pending.

## 2026-09-10 - D1/D5 Refresh and Cache Query paths

- Added explicit D1/D5 read definitions and STATUS/INFO query allowlists; wired parser and FixtureApp to shared dispatcher handlers. Flags return 0/1, parameter values decimal, and manufacturing text preserves leading zeros.
- Refresh invalidates its target before communication and validates only after complete decode; invalid queries never transmit. Added HWE minimum invalidation and ambiguous UART OSError reporting with unavailable timing/retry metadata represented as None.
- Added 14 Host/Mock integration tests covering all 63 queries, failure/retry paths, invalidation, no-auto-refresh, and FU blocking. All 105 tests passed; no Pico deployment or NF55G transmission.
- Updated ATE/interface/test documentation and HIL readiness. Pico clock, EB, scheduler, real SD logger integration, and existing Open Issues remain pending.

## 2026-09-10 - Real NF55G HIL preparation

- Added `docs/NF55G_HIL_Preparation.md` with entry-gate status, wiring/firmware records, ordered firmware preparation, and an initial D1/D5 procedure for use only after the existing gates are met.
- Audited the current skeleton: missing Refresh/Query dispatch, production scheduler, Pico clock integration, EB handling, transaction re-entry/exception protection, and physical SD/RTC logger integration. Confirmed unsupported Refresh/Query responses in a host-only check; 91 passing tests do not cover these missing paths.
- Separated D0's open side-effect question, BC/control actions, AR/FD issues, and all FU prohibition from the initial read sequence. No NF55G transmission, firmware placement, specification relaxation, or Open Issue closure.
- Recorded operator confirmation of PC–Pico connection and loopback removal; FW revision remains undecided and product connection/power state is unconfirmed. Host/Mock regression: 91 tests passed; diff check passed.

## 2026-09-10 - SD initialization repeat check

- Three sequential SD mount probes and a 160-record basic I/O run passed under normal permissions on COM14; all exited 0. Logger readback: 161 lines, 160 writes, 5 flushes, 1 close, 0 drops; clean reinit OK.
- Recorded result payloads in the hardware log. No CMD0 recurrence was observed, but cold-start initialization and the original cause remain unverified. No runtime changes or Open Issue closures.

## 2026-09-10 - UART two-channel loopback verification

- Re-ran `pico_uart_hil.py --port COM14 --bytes 256 --frames 100` under normal permissions; exit 0. Both UARTs passed 256-byte exact loopback with zero crosstalk and 100 frames / 3500 bytes per channel.
- Recorded the command, raw result payload, operator-reported wiring, and limits in `docs/Real_Hardware_Test_Log.md`. A previous run's session was lost and is not used as evidence.
- No runtime/firmware changes, NF55G protocol commands, or Open Issue closures. Final-firmware HIL and the earlier SD initialization anomaly remain pending.

## 2026-09-09 - RTC/SD rerun port access

- Recorded initial COM14 access denial under both normal and elevated execution, then successful RTC scan/read after the operator released the port. User reports both RS232 channels shorted for loopback.
- Recorded an initial SD `CMD0 failed: 31`, followed by a successful mount-only probe and complete 160-record SD basic retry (161 lines, 160 writes, 5 flushes, 1 close, 0 drops, clean reinit OK). The initial SD anomaly remains unexplained; no firmware changes or Open Issue closures.
- Operator later clarified that the SD card was removed/reinserted between failure and recovery. Updated the hardware log: contact quality is a candidate, but reinsertion-related card-state changes are not ruled out.

## 2026-09-09 - Pico identity and deployment inventory

- Added `scripts/pico_inventory.py` for read-only MicroPython identity/filesystem inspection through `mpremote connect COM14 resume run`, with no automatic soft reset or peripheral initialization.
- Verified Pico 2 / RP2350, MicroPython v1.28.0, and a root containing only `/sd`; no root boot/main files or fixture source deployment were observed. SD contents and frozen modules were outside the inspection scope.
- Recorded raw output and the user's confirmation of current ADA-5703 GP4/GP5 physical disconnection in `docs/Real_Hardware_Test_Log.md`. HW-01 remains open for final inspection traceability; no NF55G commands were sent.

## 2026-09-09 - Windows development environment setup

- Added workspace VS Code settings for the local Python environment, unittest discovery, and cmd.exe terminals; added process tasks for Host/Mock tests and dependency checks. Store PowerShell still requires elevated execution in the observed tool environment; OS permissions were not changed.
- Created a local ignored `.venv` and added `requirements-dev.txt` for HIL, Word generation, and MicroPython tooling.
- Added `docs/Development_Environment.md` with cmd.exe setup commands and the current installation limitation; linked it from README.
- Initial restricted installation failed because pip ignored its package index. A subsequent user-authorized elevated installation succeeded into the local `.venv`; direct dependencies are pinned to pyserial 3.5, python-docx 1.2.0, and mpremote 1.29.0.
- Validation under normal permissions: all 91 Host/Mock tests passed, `pip check` found no conflicts, RTC/SD/UART HIL and mpremote help commands succeeded, and COM14 was enumerated. `git diff --check` passed. No hardware commands, protocol changes, or Open Issue closures were performed.

## 2026-09-07 - r1 development baseline adoption

- Adopted `reference/RW11用電源通信仕様書r1.pdf` (GVT-284454-001-00, first edition 2026/9/4) as the current baseline at user request; local SHA256 matches the existing impact review.
- Updated AGENTS.md to Rev.1, startup/handoff guidance, reference index, current Master/plan baseline references, and active issue guidance. D6 originals and historical review/test records remain available.
- Documented PS_OFF-only OFF_PERIOD updates and the corresponding real-NF55G checks. Existing ordinary wire formats and runtime code require no change from this revision; no product behavior is emulated in Pico.
- FU remains disabled, unresolved issues remain open, and the inspection discussion document remains a discussion rather than an adopted specification.
- Validation: Host Unit/Mock suite (`python -m unittest discover -s tests`) passed all 91 tests; `git diff --check` passed. Real NF55G r1 behavior remains unverified.

## 2026-09-07 - D6 to r1 specification review

- Added `docs/RW11_D6_to_R1_Impact_Review_20260907.md` with full 43-page text/image comparison, change list, implementation impact, and remaining verification.
- Added OI-22 for r1 BOOT update recovery wording/procedure confirmation; FU remains prohibited and existing issues remain open.
- No runtime, test, original-source, or baseline-rule changes. Existing host/mock suite: 91 tests passed. Real NF55G r1 behavior remains unverified.

## Rev.0 - 2026-09-01
Initial Codex handoff baseline.

Included:
- ATE command architecture
- explicit Refresh + Cache
- Data Decode master
- Cache invalidation/post-check rules
- Pico software module boundaries
- Protocol state machine
- Command Retry / Response Retry separation
- ambiguous transaction policy
- Mock NF55G and host test plan
- Logger/SD formal specification
- FU hard prohibition
- ATE priority rule
- USB CDC detailed implementation deferred
- Fixed implementation phase order in `docs/Implementation_Plan.md`
- Defined development vs production source versioning policy

Initial implementation start:
- Added `src/config.py` constants for frame bytes, timing, retry, cache names, and invalidation policy.
- Added `src/models.py` lightweight shared model classes.
- Added `src/frame.py` for NF55G frame build/parse and BCC calculation.
- Added `src/nf55_decode.py` pure decoders for D0/D1/D2/D3/D4/D5/BC/EB/EL/OL/AR/FD.
- Added `src/cache_manager.py` for power-on invalid cache state, validate/invalidate, refresh failure, and control ambiguous/success invalidation.
- Added initial host `unittest` coverage for frame/BCC, cache, and decode basics.
- Expanded decoder unit tests to cover D0/D1/D2/D3/D4/D5/BC/AR/EL/OL/FD normal lengths, wrong lengths, key numeric conversions, status bit decode, FD raw preservation, and EL/OL START_NO mismatch.
- Added comprehensive D0 Golden Data assertions covering TIME, REALTIME, OFF, LIFE_CALC, LIFE_DIAG, ACCUMULATED, MFG raw/decode, PARAM raw/decode, and STATUS raw/decode.
- Added host-side Mock NF55G with `FakeClock`, `MockUART`, `ResponseFactory`, and scenario steps for ACK, NAK33, ACK_TIMEOUT, RESP_TIMEOUT, BCC NG, PME, SQE, and HWE.
- Added `src/nf55_protocol.py` transaction state machine covering WAIT_ACK, WAIT_RESPONSE, VALIDATE_RESPONSE, COMMAND_RETRY, RESPONSE_RETRY, SUCCESS, and FAILED paths with host unit tests.
- Added control command/cache integration for CHARGE_ON, CHARGE_OFF, BACKUP_ENABLE, OUTPUT_RESTART, PARAM_SET, and related control commands, with tests for success invalidation, parser rejection, PME/SQE no-invalidation, HWE/ambiguous invalidation, and no automatic post-refresh.
- Added Logger/SD core with RAM queue, host memory SD sink, TEST_START/TEST_END, LOG_CONT_START/LOG_CONT_STOP, SD_STATUS?, SD_USAGE?, LOG_DROP_COUNT?, SD_REINIT, forced drain on TEST_END, drop counting, and no write/flush while protocol busy.
- Recorded separate SD real-hardware debug checklist for Mount, CSV creation, Write, Flush, Close, continuous logging, card removal, write error, and reinitialization.
- Added Pico-side RTC command support for RTC_DATE?, RTC_TIME?, RTC_DATETIME?, RTC_SET_YYYYMMDD_HHMMSS, and RTC_CHECK? using a DS3231 abstraction, explicitly separate from NF55G SC/CLOCK_SYNC.
- Added Pico/MicroPython `DS3231I2CDevice` access for I2C0 GP20/GP21, including BCD datetime read/write and OSF clear, with host fake-I2C tests.
- Added and consolidated AD/AR Open Issue review notes, including interim FW analysis, into OI-16 through OI-21 plus OI-04/OI-05 refinements for production FW/design confirmation.
- Added HW-01 for the ADA-5703 PiCowbell GP4/GP5 physical conflict with Pico-2CH-RS232 NF55G UART1, and noted that disabling PiCowbell RTC in software is not sufficient.
- Added a first-step real-hardware debug notice and T8 pre-check requiring ADA-5703 GP4/GP5 physical isolation before final fixture UART/SD debug.
- Recorded that 2026-09-04 Pico 2 SD/RTC real-hardware tests were performed with ADA-5703 GP4/GP5 physically isolated; HW-01 remains open for final fixture isolation/inspection traceability.
- Added `docs/Desktop_to_VSC_Migration_Plan.md` to define the Desktop Codex to VSC+Codex scope boundary, migration gate, current status, VSC start checklist, and required real-hardware records.
- Added `docs/Desktop_to_VSC_Migration_Plan.md` to `HANDOFF_MANIFEST.txt`.
- Added `reference/NF55G_VSC_Codex_Migration_Guide.md` as a supporting reference for ChatGPT -> Desktop Codex -> VSC+Codex staged migration, maintained until VSC+Codex handoff and retained as a record afterward.
- Added the VSC+Codex migration guide to `HANDOFF_MANIFEST.txt` as a supporting reference file and clarified generated migration/support notes in `reference/README_REFERENCE.md`.
- Added `scripts/pico_sd_hil.py` as a repeatable Pico 2 MicroPython SD HIL runner for SD mount, CSV write/readback, current logger queue-path verification, and clean SD reinitialization checks.
- Recorded 2026-09-07 Pico 2 SD logger queue-path verification in `docs/Real_Hardware_Test_Log.md`; host `tests.test_logger_sd` passed and Pico 2 SD queue/readback completed with 160 records, 5 flushes, 1 close, and 0 drops.
- Extended `scripts/pico_sd_hil.py` with configurable queue/load record count and an interactive card removal/reinsert mount probe; recorded a 2000-record Pico 2 SD logger load pass with 0 drops.
- Recorded Pico 2 microSD physical removal detection and post-reinsert remount/write/readback recovery; forced write-error injection remains pending.
- Recorded an inconclusive forced write-error attempt: physical removal after opening a MicroPython file did not surface a logger-visible write/flush error after either 1-record or 256-record attempts, so a lower-level fault-injection procedure is still required.
- Recorded final post-fault-attempt SD remount/write/readback recovery on Pico 2, confirming the card returned to normal operation after reinsertion.
- Re-ran Pico 2 SD removal/reinsert checks after the prior physical-removal timing was found uncertain; baseline write/readback, removed-card mount failure, post-reinsert remount, and post-reinsert logger write/readback all passed.
- Added `scripts/pico_uart_hil.py` for Pico 2 MicroPython RS232C 2ch loopback HIL checks and recorded CH0/CH1 init, 256-byte loopback, no-crosstalk, and 100-frame stress PASS results; 512-byte single-write behavior is recorded as a HIL buffering limit observation.
- Added host-testable Pico hardware/transport layer skeletons (`ate_uart.py`, `nf55_uart.py`, `diagnostic.py`, `command_parser.py`, `main.py`) plus tests for local routing, diagnostics, `FW_UPDATE` prohibition, and no-control behavior before NF55G connection.
- Added `scripts/pico_rtc_hil.py` and recorded a pre-NF55G readiness check: host tests passed, RTC/SD/UART HIL checks passed on Pico 2, and remaining work is gated on final fixture isolation evidence, final firmware path, and real NF55G availability.
- Revised Desktop-to-VSC migration and test plans for the 2026-09-07 boundary: Desktop Codex completed host/mock plus Pico 2 RTC/SD/UART REPL HIL; VSC+Codex takes over final firmware placement/build/flash, final-firmware reruns, low-level SD write-error fault injection, and Real NF55G HIL.


## 2026-09-10: Integrated Pico deployment

Deployed 23 Python files with matching SHA-256; real RTC/SD smoke, 64-row CSV readback after remount, RAM ATE CRLF/FU rejection, and scheduler run/stop passed. NF55G disconnected; observed NF55G TX zero. Device left in REPL; cold boot and physical ATE/NF55G tests pending.

Evidence and limitations: [Pico deployment](Pico_Deployment_20260910.md). Reproducible finite check: `scripts/pico_runtime_smoke.py`.


## 2026-09-10: SD startup diagnostics

Added RAM-only first-startup SD stage/error snapshot; no automatic retry, added delay or ATE format change. Soft-boot mount passed; cold-power failure cause remains unconfirmed. Host/Mock: 138 tests passed. See [investigation](SD_Startup_Investigation.md).


## 2026-09-10: Controlled SD cold-start comparison prepared

Added opt-in startup delay / CS-before-SPI settings (normal defaults unchanged) and temporary `firmware/sd_startup_probe.py`. Pico /main.py now selects DELAY_ONLY: 500 ms wait, original CS order, one CMD0 attempt. Cold-power result pending; normal entry point must be restored after investigation. Host/Mock: 139 tests passed. See [experiment matrix](SD_Startup_Investigation.md).


## 2026-09-10: DELAY_ONLY cold start failed; CS_ONLY selected

500 ms added wait with original CS/SPI order still returned CMD0 failed: 31, CARD_INIT, elapsed 625 ms. First-boot evidence captured before reset/reinit. Switched temporary Pico entry to CS_ONLY (0 ms added wait; GP17 High before SPI creation). CS_ONLY cold-power result pending. See [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: CS_ONLY cold start failed; combined condition selected

CS High before SPI creation with no added wait returned CMD0 failed: 31, CARD_INIT, elapsed 126 ms. Captured before reset/reinit. Temporary Pico entry now selects DELAY_AND_CS (500 ms wait, then CS High, then SPI creation). Combined cold-power result pending. No runtime logic change or Host test rerun for this case selection. See [SD investigation](SD_Startup_Investigation.md).


## 2026-09-10: SD startup comparison completed without improvement

DELAY_AND_CS cold start: CMD0 failed: 31, CARD_INIT, elapsed 627 ms; captured before reset/reinit. Baseline, delay-only, CS-only and combined cases all exhibited the same CMD0 failure. Tested 500 ms wait and CS-before-SPI are not established fixes. Restored normal firmware/main.py to Pico /main.py, retaining diagnostic support. Root cause remains open. No Host tests rerun for hardware measurement and entry restoration; last suite 139 passed.


## 2026-09-10: Chat CMD0 diagnostic handoff validated

Corrected pre-mount diagnostic contamination: preserve first baseline mount failure, then probe only an unmounted CMD0 failure, without auto-remount. Bounded repeated-CMD0 method; actual regression tests replace synthetic assertions. Host/Mock 143 passed; Pico warm CMD0 10/10 idle responses, SD remount and existing 65-line CSV readback passed. Temporary diagnostic boot deployed for cold-power evidence; root cause unresolved. See [handoff validation](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: Verification-method handoff

Updated verify_sd_diagnostics.py to execute diagnostic regressions; aligned instructions to current 400 kHz baseline. Added simulated SPI constructor/command coverage for idle clocks, exact CMD0 frame, error preservation and timeout. Diagnostic 5 passed; full Host/Mock 144 passed. No Pico/runtime changes; see [verification handoff](SD_CMD0_Chat_Handoff_Validation.md).


## 2026-09-10: CMD0_NO_PRE_FF hardware comparison prepared

Temporary Pico /main.py selects CMD0_NO_PRE_FF: only CMD0's CS-Low pre-command
FF byte is omitted. Other commands retain it. Initialization remains 400 kHz,
mode 0, 16 FF bytes with CS High, zero added wait and original CS/SPI ordering.
The driver default CMD0_PRE_DUMMY=True preserves normal behavior; only the
diagnostic entry overrides it. Startup snapshot includes cmd0_pre_dummy=False.
Post-failure probing still preserves the initial result; its CMD0 commands also
use this setting. No automatic remount or production workaround was added.

Host/Mock: 144 passed, with first-CMD0 byte sequence and failure/timeout checks
covering both pre-FF settings. Pico warm runtime smoke passed: RTC advancing,
64 CSV rows at /sd/BANK_A/20260910_114306.csv, zero drops, remount/readback,
RAM ATE CRLF and FU rejection, run/stop and zero observed NF55G TX bytes.
Evidence: temp/pico_no_ff_runtime_smoke.log and temp/pico_no_ff_warm_boot.log.
Cold-power result pending operator power-cycle; no claim of root-cause repair.
Earlier statements that this comparison was unimplemented are historical.


## 2026-09-10: RETRY_ONLY comparison prepared

Temporary diagnostic entry retains the SDCard object whose constructor failed,
via ObservedSDCard, and records the original mount error before follow-up.
PROBE_MODE=RETRY_ONLY issues one CMD0 on that same object/SPI: no SPI constructor
or init, no additional 128-clock train and no explicit retry delay. Ordinary
cmd() CS transitions and post-response FF clocks remain; "no extra clocks" does
not mean zero clocks between commands. SPI is deinitialized only after the probe.
CASE remains CMD0_NO_PRE_FF to keep the preceding trial's command bytes unchanged.
The baseline of this comparison is that preceding trial, not the original driver.

If first mount succeeds or no retained object exists, probing is skipped. No
automatic remount follows a failure. First evidence is not overwritten by a
successful follow-up. All additional probing is diagnostic, not production retry.

Host/Mock: 146 passed. New checks enforce retained-object reuse, exactly one
attempt, zero requested delay and no fallback reconstruction when object missing.
Pico warm test injected a software CMD0 error after a real 0x01 reply, confirmed
constructor-failure object retention, then obtained 0x01 from one same-SPI retry.
SD remount and existing 65-line CSV readback passed. This injected failure is NOT
a reproduced cold-power failure and does not establish a fix.
Evidence: temp/pico_cmd0_retry_only_warm_injection.log; reproducible script:
scripts/pico_cmd0_retry_only_smoke.py. Warm boot evidence:
temp/pico_retry_only_warm_boot.log.

Pico /main.py and /sd_cmd0_probe.py contain the updated diagnostic module.
The next operator power-cycle must be captured before host reset/reinit; inspect
startup_sd_diagnostic and REPL global diagnostic_report, including probe_mode,
mode, attempts and results. Cold result pending; root cause remains unresolved.


## 2026-09-10: CLOCKS_ONLY comparison prepared

PROBE_MODE=CLOCKS_ONLY retains the failed card/SPI, drives CS High and writes
16 FF bytes (128 clocks), then sends one CMD0 with zero explicit delay. No SPI
constructor/init occurs before that retry; deinit is cleanup after the result.
CASE remains CMD0_NO_PRE_FF, matching RETRY_ONLY. Report includes mode, attempts,
delay_ms and extra_idle_bytes=16. First failure is retained without automatic remount.

Host/Mock: 147 passed. New test verifies CS High during all 16 writes, same SPI,
no reconstruction factory, then exactly one retry and cleanup. The warm Pico
smoke uses injected failure; cold-power evidence still requires a physical cycle.
Evidence paths: temp/pico_clocks_only_warm_injection.log and
temp/pico_clocks_only_warm_boot.log. No permanent workaround has been selected.


## 2026-09-10: Pico CLOCKS_ONLY verification record

Recorded COM14 preserved startup evidence (initial CMD0=31; follow-up=0x7F)
in Real_Hardware_Test_Log.md and SD_Startup_Investigation.md. This was a re-read,
not a new physical cold-start trial. Host/Mock 147 passed; firmware unchanged;
root cause remains open.


## 2026-09-10: CLOCKS_ONLY physical power-cycle evidence

Recorded operator-confirmed power-cycle trial at 15:20 JST: initial CMD0=31,
retained-SPI follow-up after 128 clocks=0x7F, SD unmounted. Failure reproduced;
root cause remains open. Evidence and device REPL state recorded in hardware
log and SD investigation. No firmware changes; last Host/Mock run 147 passed.


## 2026-09-10: Deploy chat SD changes; Phase 1 passed

Deployed and byte-verified 24 files on Pico 2, with prior Python files backed up.
Host/Mock 147 passed; basic CMD0 at measured 100 kHz returned 0x01.
Phase 2 cold power cycle, Phase 3 five CASE cold trials and optional Phase 4
physical measurement remain pending. See Real_Hardware_Test_Log.md.


## 2026-09-10: Phase 2 cold mount succeeded; Phase 3 BASELINE ready

100 kHz / PULL_UP cold boot returned mounted=True, READY, OK, elapsed_ms=305.
Additional CMD0 probe skipped for mounted filesystem. Recorded first evidence;
deployed and byte-verified BASELINE variant for next physical power cycle.
No root-cause conclusion or Open Issue closure. See hardware test log.


## 2026-09-10: Phase 3 BASELINE cold mount passed

BASELINE cold boot: mounted=True, READY, OK, 304 ms. Initial evidence recorded;
follow-up CMD0 skipped. DELAY_ONLY entry deployed and byte-verified for trial 2/5.
No application source changes or Open Issue closure. See hardware test log.


## 2026-09-10: Phase 3 DELAY_ONLY cold mount passed

DELAY_ONLY cold boot: mounted=True, READY, OK, 806 ms including 500 ms wait.
Initial evidence recorded; follow-up CMD0 skipped. CS_ONLY entry deployed and
byte-verified for trial 3/5. No source change or Open Issue closure.


## 2026-09-10: Phase 3 CS_ONLY cold mount passed

CS_ONLY cold boot: mounted=True, READY, OK, 307 ms. Initial evidence recorded;
follow-up CMD0 skipped. DELAY_AND_CS entry deployed and byte-verified for trial
4/5. No application source change or Open Issue closure.


## 2026-09-10: Phase 3 DELAY_AND_CS cold mount passed

DELAY_AND_CS cold boot: mounted=True, READY, OK, 810 ms including 500 ms wait.
Initial evidence recorded; follow-up CMD0 skipped. CMD0_NO_PRE_FF entry deployed
and byte-verified for trial 5/5. No source change or Open Issue closure.


## 2026-09-10: Five-CASE cold-boot series completed

Final CMD0_NO_PRE_FF trial mounted successfully in 305 ms. All five CASEs
returned OK/READY with 100 kHz initialization and MISO PULL_UP. Recorded
evidence-backed comparison; no unique optimum or root cause established.
Optional physical MISO measurement remains unperformed. Diagnostic entry
retained; Pico at REPL with ATE loop stopped. Last Host/Mock: 147 passed.


## 2026-09-10: Restore normal baseline per user decision

Restored and byte-verified firmware/main.py as Pico /main.py; retained SD
100 kHz initialization and MISO PULL_UP, with no wait, original CS order,
and CMD0 pre-FF enabled. Normal warm mount check passed (333 ms), Host/Mock
147 passed. Left normal firmware running. Requested task complete; optional
voltage measurement unperformed, clock-only root cause not established.


## 2026-11-13 REPLミラー既定OFFを開発Picoへ転送

- COM14／Pico ID `2d35a1e11ac125e3`へ`src/config.py`のみ配置。PC／Pico SHA-256一致、`REPL_LOG_ENABLED=False`と`ATE_BAUDRATE=57600`をPico上で読戻し確認。
- ATE側baud設定が未確認のためMain再起動は保留。COM19の旧115200bps `*IDN?`は無応答で、新57600bpsのATE通信確認とは扱わない。相手側57600bps設定後に再起動・ATE応答確認が必要。[実機記録](Real_Hardware_Test_Log.md)

## 2026-11-14 固定接続・連続読取候補FWの準備

ユーザー指示によりホットプラグ試験を今回の目標から外し、固定接続での電源投入～連続読取を対象にする。qr-fixed-20261114.1を独立Continuousビルドで追加。起動3秒待ち候補・段階記録・1秒heartbeatと64件の再利用FIFOを追加し、HID原文全件送信を止めて完成文字列／異常／状態を継続送信する。旧.1/.2配布と旧有限RAM/UARTモードは保持。parser・native Cテストを更新。実機未書込み・起動問題の解決は未確認。[診断仕様](USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/ALT_Decode_Resume_20261114/Fixed_FW_20261114/Specification_Rev0.md)。

## 2026-11-14 固定接続候補FWの配置

qr-fixed-20261114.1を追加基板A06FEA01012EC137へ配置。現Flash2MB退避・load -v・独立verify・配置後版／chipid照合・reboot成功。Host／Mock354件成功。外部給電・QR固定接続の自動起動／継続読取は未検証であり、電源ON認識問題を解決済みとはしない。

## 2026-11-14 固定接続cold-start第1回と20読取

qr-fixed-20261114.1／A06FEA01012EC137。電源ONのみ・RSTなしでHID mount3606ms、A/B交互20件を全件35文字一致で取得。main/frame進行、drop0、途中再起動・decodeエラーなし。先頭NULは継続。cold-start複数回・10分以上稼働は未確認。原因確定・全体受入・Open Issue Closeとはしない。

## 2026-11-14 固定接続の限定動作確認完了

qr-fixed-20261114.1／A06FEA01012EC137。電源ONからRSTなしのQR自動認識3試行中3成功、各HID mount3606ms。第1回A/B交互20読取は全件35文字一致、drop0、decodeエラー・途中再起動なし。先頭NULは継続。10分以上はエージェント追加の試験であり待ち時間への指摘を受け今回は省略、長時間成功とは扱わない。今回の固定接続の基本動作確認であり、正式ATE連携・7355／2 Host・量産保護等の受入／Open Issue Closeとは区別。


## 2026-11-14 QR／7355 Host基板の分離を採用

ユーザー指示により7355用Host基板を追加し、QR用と親Picoへの接続経路を分離する方針へ変更。既存QR基板Type_C1の改造・CC切替案と写真依頼は取り下げ、旧案は履歴として保持。構成方針書、既存計画の最新注記、親インターフェース設計条件・段階試験計画を更新しUSB-SUB-05を追加。USB-SUB-03は旧構成課題としてOpen維持。コード／FW・基板の変更、購入操作・追加実機試験なし。[現行方針](USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Split_Host_Architecture_Rev0.md)。

## 2026-11-18 S1.15_r1 新旧FW静的レビュー
- ユーザー指定S1.13/S1.15_r1をreference/FW_Review_S1.15_r1_20261118へ全件保管。既存ファイル削除なし。全172ファイルの原本/コピーSHA-256一致。
- docs/S1.15_r1へOI照合、機能差分、全ファイル一覧・テキスト差分・試験ログを追加。
- Open_IssuesへAR表現の確認事実とS115-01〜04を追記。既存IssueはCloseしない。
- Host Unit / Mock NF55G: python -m unittest discover -s tests -v、354件成功。NF55G再ビルド・実機試験は未実施。Picoコード/仕様変更なし。

### S1.15_r1 治具側影響の追加確認（2026-11-18）
- docs/S1.15_r1/Fixture_Impact_20261118.mdを追加。現行デコード・コマンド入口と照合し、直ちに必要なPico修正は未特定。D0取得順序、SC応答時間、新FW版照合、ATE期待値、AD/AR正式実装の前提を整理。
- 現行関数の直接確認5項目成功。Picoコード変更なし。新FW実機・ATEコードは未検証。

### 2026-11-18 S1.15_r1検証の工程割当て
- docs/S1.15_r1/Verification_Schedule_20261118.mdにV01〜09の工程・担当区分・前提・完了証跡を登録。現行Development_StepsとImplementation_Planへ参照追記。
- Fixture_Impactの確認事項を段階1/4/5/6へ配置。日程は工程順で管理し、製品FW設計回答と治具検証を分担。計画文書のみのためテスト再実行なし。
