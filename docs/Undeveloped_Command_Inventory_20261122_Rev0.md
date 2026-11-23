# 未開発コマンド一覧・優先順位検討 Rev.0

確認日: 2026-11-22。案件: NF55G Pico試験治具。目的: 開発優先順位の検討。下記順位は提案であり、ユーザー決定ではない。

後続決定（2026-11-22）: ユーザーが提示手順を採用。採用した開発順と23日の固定配線化は[決定記録](Development_Order_and_Fixed_Wiring_Decision_20261122.md)を参照。本文の「提案/未決定」は一覧提示時点の状態を残したもの。

## 確認方法と状態

ATE_Command_Master、現行command_parser/nf55_command/command_dispatcher/main、QR試作、ADC基盤、HOST管理提案と直近記録を照合した。現行parserをPC上で呼び出し、HOST管理・QR・AR・AD・SERIALの代表名がUNKNOWN、EXT_QUERY/EXT_SENDがEXTERNAL、FW_UPDATEがFORBIDDENとなることを確認した。NF55G/実機へは送信していない。ソース実装状態と実機配置・受入状態は別に扱う。

以下で「未定」は正式名未定の機能を示す。「候補」は提案/試作名であり、その名称で動作する正式コマンドではない。機能を分けて列挙しているため、行数は確定コマンド数ではない。

## 未開発・正式統合未完了の一覧

| ID | コマンド/機能 | 現状 | 主な依存・確認事項 | 優先案 |
|---|---|---|---|---|
| H1 | `HOST_INFO? METER`（候補） | 新管理照会は未実装。既存X1 HELLOとは別 | 個体/FW/boot世代/FAULT/対応能力のfreshな照合、管理wire | 1 |
| H2 | `HOST_RESET METER`（候補） | 通常RST未実装。23日の実装予定 | H1、FAULT中受付、対象だけ再起動、新nonce、旧要求排除 | 1 |
| A1 | ADC測定取得（未定） | 測定Cache基盤あり。ATE取得からCacheへの接続未実装 | 対象3系統・A/B・試行/取得ID、応答単位/完成判定/overrange | 2 |
| A2 | ADC測定Cache照会（未定） | 内部get/get_calibrationあり。ATE入口未実装 | A1、原文/数値/単位/識別、照会で再測定しない | 2 |
| A3 | `AD_<TYPE>_<POINT>_<VALUE>` | 数値直接指定のATE入口・送信builder未実装 | TYPE/Point対応、VALUE8/極性/丸め/範囲、応答/T2 | 2 |
| A4 | 測定Cache指定AD書込み（未定） | Cache破棄基盤あり。ATE入口/AD接続未実装 | A1～A3、ATE確認後の明示書込み、成功/成否不明で使用値失効 | 2 |
| A5 | `AR_REFRESH` | decoderあり。読出しATE入口/Cache更新未実装 | 正式AR形式/T2、実機製品FW、小数情報の欠落 | 2 |
| A6 | `AR_<対象>_P<1/2>_<ADC/REF>?` | AR個別Queryは登録0件 | A5、REFの表現/単位。Masterは5系統×2点×2値=20入口相当 | 2/後続 |
| A7 | AD個別照合（未定、応答3種確定） | AR発行/直前書込み値保持/比較/ログの一連処理未実装 | A3～A5、小数を失わない比較手段。同一試行/対象/点 | 2 |
| Q1 | `QR_SCAN`（試作名） | 単独試作あり。現HOSTから正式ATE受付/Cacheへの統合未完了 | 試行/要求境界、期限、残留/遅着排除、現HOSTリンク | 3 |
| Q2 | `QR_STATUS?` / `QR_CANCEL`（試作名） | 単独試作あり。正式ATE入口未登録 | Q1、期限/取消/遅着と状態応答の正式化 | 3 |
| Q3 | `QR_GET` / `QR_DATA`（試作名） | 原文/6項目返却の単独試作あり。正式ATE入口未登録 | Q1、実データ、Cache識別、有効/無効、保持値のみ照会 | 3 |
| Q4 | `QR_PARSE`（候補） | 独立コマンド未実装。試作は受信後に自動分割済み | 独立工程にするか要検討。別コマンド追加が必須とは未決定 | 3・採否検討 |
| S1 | `SERIAL_<ITEM>_<VALUE>`（SS） | 数値/文字列直接指定のATE入口・SS builder未実装 | UNIT/ADU/BBU各REV/LOT/SERIALの9項目、50文字配置/予約/部分更新 | 3 |
| S2 | QR Cache指定SS書込み/書込み先指定（未定） | 正式Cache→SS接続未実装 | Q3/S1、REV3→4、年/週→LOT、号機→SERIAL、ADU/BBU取得元 | 3 |
| S3 | `QR_VERIFY`等の書込み個別照合（候補） | 未実装。採用する操作契約は要検討 | S1/S2、明示読戻し/対象相関。INFO_REFRESHと既存Queryは利用可能 | 3・採否検討 |
| H3 | `HOST_BOOTSEL METER`（候補） | 未実装、実装日は未指定 | H1、給電維持PCデータ接続、移行後UART停止とPC個体照合 | 4 |
| H4 | QR HOSTのINFO/RESET/BOOTSEL（名称未定） | QR用管理経路の拡張未実装 | QR RX実結線/双方向管理、測定器HOST版とは別受入 | 4 |
| R1 | D2/D3/D4専用Cache Query（未定） | Refresh実装済み、専用Query名/返却契約未定義 | 必要な取得項目と用途を選定。DATA Queryを流用しない | 5・必要性検討 |

A6の20入口相当はDISCHG_I/BATT_V/ACDC12V_V/BATT_CHG/12VOUT_V。校正必須はDISCHG_I/BATT_CHG/BATT_Vの3系統なので、まずその12入口相当を対象にし、残る8入口は必要性を検討する提案。残る2系統の校正書込み開発を追加要求と解釈しない。

AD個別照合の確定応答は`OK:AD_VERIFY`、`ERR:AD_VERIFY_MISMATCH`、`ERR:AD_VERIFY_TIMEOUT`。コマンド名/引数と照合不能等の追加応答は未確定。小数の実機切分けは[専用試験計画](ADC_Decimal_Hardware_Test_Plan_20261122_Rev0.md)に従う。

## 未開発一覧から除外するもの

| 区分 | 対象 | 理由/残事項 |
|---|---|---|
| 実装済み・現在デバッグ中 | `EXT_QUERY` / `EXT_SEND` | ATE→親→測定器HOST中継は実装・実機実績あり。CDC受信停止/復帰・共存受入は継続。ソース既定無効と実機評価構成を区別 |
| 実装済み | D0/D1/D5、D2/D3/D4 Refresh、EL/OL RefreshとQuery、FD_READ/FD_DATA? | ARを除く読出しは実装あり。FDの表記差等、実機条件/受入の未解決を未開発に数えない |
| 実装済み | DATA/STATUS/INFO/BC Query、充電/出力制御、ERP4組合せ、BC開始/停止、CLEAR、CLOCK_SYNC、LIFE_SET、PARAM_SET/RESET・通常10項目 | コードあり。全条件の実機受入完了を意味しない |
| 実装済み | RTC、TEST_START/END、連続ログ、SD照会/再初期化、診断5入口 | 今回の新規開発候補ではない |
| 意図的に拒否 | `FW_UPDATE` / FU | `ERR:FU_DISABLED`。開発対象へ入れない |
| 意図的に拒否 | 保護設定5項目の`PARAM_<ITEM>_<VALUE>` | PARAMETER_PROTECTEDを実装済み。拒否解除を未開発と数えない |
| 意味確認待ち・拒否実装済み | `PARAM_CHG_IR_THD_<VALUE>` | PARAMETER_UNCONFIRMED。採用はPARAM-IR-01の回答後。通常項目へ独断追加しない |
| 別機能/採否未定 | 常時WDT・量産自動復旧、USB保守コンソール | 特定の未実装ATEコマンドではない。必要なら別案件内の開発項目として優先度を検討 |

## 優先順位のたたき台

1. **現在の先行デバッグを支えるHOST INFO/通常RST（H1/H2）**。既存の23日予定を維持。CDC受信の原因切分けも継続する。
2. **ADC一連機能（A1～A7）**。準備/独立開発は並行し、統合は先行デバッグ後。小数問題はA3/A5/A7を跨ぐため、書込み・AR観測経路が準備できた段階で実機切分けを先に行い、照合方式の確定へつなげる。仕様回答待ちで独立開発まで止めない。
3. **QR正式ATE連携→SS書込み→明示照合（Q/S系）**。直近ユーザー指定のADC後という順序を維持。QRの取付け後単独試験は前倒しで既存計画どおり可能。
4. **保守作業の省力化（H3/H4）**。給電/接続条件と必要性に応じて繰上げを検討する。
5. **D2/D3/D4専用照会（R1）と必須校正外のAR照会**。量産ATEで必要な項目から採否を決める。

優先順位を決める主な分岐は「HOST BOOTSELをADCより先にするか」「ADCは取得/Cacheと書込み/照合を段階リリースするか」「QR_PARSEやQR_VERIFYを独立コマンドにするか」。今回順位は確定せず、コード実装・仕様の採否・実機操作は行っていない。

## 根拠・確認結果

- [ATE Master](ATE_Command_Master.md)、[ADC記録](ADC_Calibration_Development_20261119.md)、[QR要件](QR_Reader_Requirements.md)、[HOST管理提案](USB_Host_Reset_Study_20261121/Development_Reset_Bootsel_Command_Proposal_20261122_Rev0.md)、[ADC/QR統合計画](ADC_QR_Integration_Plan_20261122_Rev0.md)。文書中の古い「未実装」は後続実装と照合した。
- `src/command_parser.py`、`src/nf55_command.py`、`src/command_dispatcher.py`、`src/main.py`、`src/qr_reader.py`、`src/calibration_measurement.py`を確認。
- `.venv/Scripts/python.exe -B -c ...`による分類確認: 上記代表名はUNKNOWN、EXT2入口はEXTERNAL、FW_UPDATEはFORBIDDEN。AR Query登録0件。Refresh辞書18件（FDは動的解決）、Cache Query307件。
- 今回は一覧作成と分類確認のみ。Host Unit/Mock全件再実行、build、実機送信は未実施。未実装名を送って実機の状態を変える確認は行っていない。
