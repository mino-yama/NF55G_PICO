# NF55G治具 接続・GPIO・Type_C2改造図 Rev.4

日付: 2026-11-11
状態: **改造箇所・手順を図面化済み。基板は未施工。実機確認の直前に改造を案内する。**

ユーザー指示「実機確認前に指示」「治具回路図に改造個所と手順を明記」を反映した新しい図面版。Rev.3以前とメーカー原典は上書きしていない。今回の作成を改造実施・電気受入・量産承認として扱わない。

## 印刷用・編集用

- [印刷用PDF：A4横5枚](NF55G_Fixture_Connection_GPIO_Rev4_20261111.pdf)
- SVG: [1 全体接続](NF55G_Fixture_Rev4_sheet1.svg)、[2 GPIO](NF55G_Fixture_Rev4_sheet2.svg)、[3 追加範囲](NF55G_Fixture_Rev4_sheet3.svg)、[4 改造回路・位置](NF55G_Fixture_Rev4_sheet4.svg)、[5 作業手順・記録欄](NF55G_Fixture_Rev4_sheet5.svg)
- プレビュー: [1](preview_sheet1.png)／[2](preview_sheet2.png)／[3](preview_sheet3.png)／[4](preview_sheet4.png)／[5](preview_sheet5.png)
- [専用生成スクリプト](../../../scripts/build_fixture_connection_drawing_rev4.py)。既存Rev.3の生成スクリプトは維持。
- [旧Rev.3](../NF55G_Fixture_20261110_Rev3/README.md)

## 追記した内容

4枚目にはD+=GPIO12／R12、D−=GPIO13／R11の正しい接続を示し、R13（D+プルアップ）とR18／R19（CCのSink側）の撤去、R20／R21（CC Source側）への各56kΩ・1%実装、R11／R12とType_C1側R5／R6を維持することを明記。メーカーUSB-C専用FAQの赤丸位置写真を原形のまま掲載し、部品サイズ・現物の位置照合を施工条件とした。

5枚目には、Host FWと試験準備→実機直前の案内→無給電→変更前写真→R13撤去→CC変更→外観確認→電源のみ確認→QR専用試験の順序と記録欄を追加した。測定できないDB_N／DN1の微細端子プロービングは要求しない。現行dev-20261111.1はUSB単体確認用でHostを起動しないため、そのままQR試験には使わない。

給電は、デバッグ時PC→Type_C1、機器使用時は外部5Vアダプタ→Expander分岐→追加基板5V／GND。追加側最大1Aはユーザー申告であり、保護・負荷時動作の実測ではない。PCとExpanderを同時給電しない。切替え・機器配線は電源OFFで行う。Type_C1=7355／Type_C2=QRの固定割当て、既存ATE／NF55G／RTC／SD、下位UART未確定の扱いを維持する。

## 検証

PDF全5ページを描画・目視確認。4枚目の注記間隔を調整して再描画。ページ数・用紙寸法・文字領域・必要情報・SVG XMLを[検証記録](verification.json)で確認。各ページの抽出テキストも保存。Host Unit／Mock NF55Gは[287件成功、6.399秒](Host_Mock_20261111.txt)。今回の変更対象は図面・文書・図面生成スクリプトで、通信FW変更・機器操作・はんだ作業は未実施。

生成環境: Python 3.12、PyMuPDF、Windows MS Gothic、Pillow 11.3.0（メーカーWebPを画素の加工なしでPNGへ形式変換し、PDFとSVGへ埋込み）。依存情報と出力hashはmanifest.jsonを参照。

## 残確認

部品サイズ・実装箇所の最終照合、Expander取出し端子・保護・実負荷・逆流、QR Host FW・機能時ログ経路、二系統Host・治具UART・Timingは未確認。USB-SUB-01／02、HW-01を独断でCloseしない。汎用Type-C Sourceや製造用全結線の完成図と誤認しない。

根拠: [Host回路条件Rev.0](../../USB_Host_SubMCU_Host_Circuit_Conditions_Rev0_20261111.md)／[一次資料・メーカー写真台帳](../../../reference/USB_Host_SubMCU_Host_Conditions_20261111/manifest.json)。
