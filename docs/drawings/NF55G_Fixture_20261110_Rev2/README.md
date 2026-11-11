# NF55G試験治具 接続・GPIO割付図 Rev.2

2026-11-10更新。Pico-Quad-ExpanderがPico 2／RTC／SD／RS232C 2CHの4基板の共通ベースとなるよう、全体図の配置を修正した。4基板をExpanderの枠内、追加HOST・USB機器を枠外に表示する。実スロット位置・寸法・積層順を示す配置図ではない。GPIO・通信条件・加工要否の確定度はRev.1から変更していない。

## ファイル

- [印刷用PDF・A4横3枚](NF55G_Fixture_Connection_GPIO_Rev2_20261110.pdf)
- 編集用SVG: [1 全体接続図](NF55G_Fixture_Rev2_sheet1.svg)、[2 GPIO表](NF55G_Fixture_Rev2_sheet2.svg)、[3 追加・改造範囲](NF55G_Fixture_Rev2_sheet3.svg)
- [全体図プレビュー](preview_sheet1.png)
- [生成スクリプト](../../../scripts/build_fixture_connection_drawing.py)
- 過去版: [Rev.1と適用範囲](../NF55G_Fixture_20261110_Rev1/README.md)。Rev.0／Rev.1の成果物は保持。

## SVGの編集方法

SVGはラスタ画像ではなく、文字・四角形・線を保持した編集可能な形式。InkscapeやAdobe IllustratorなどのSVG編集ソフトで開き、個別の要素を選択して文字・位置・色・配線を修正できる。図形の移動に線が自動追従するCAD接続機能は付いていないため、線の端点も合わせて調整する。

文字はパス化しておらず編集できる。MS Gothicを指定し、代替としてNoto Sans CJK JPなどを指定している。フォント環境が異なると文字幅が変わるため、保存・PDF書出し後に表示を確認する。

ブラウザーやVS Codeのプレビューは閲覧用途。テキストエディターでSVGソースも変更できるが、図形配置はSVG編集ソフトが扱いやすい。SVGからPDFへ書き出せる。手編集後のSVGは別名・別版で保存し、生成スクリプトの再実行で同じ版の出力を上書きしないようにする。スクリプトとSVGの変更は自動同期しない。

## 検証・残事項

PDF全3ページをPNGへ変換して表示確認、SVG XMLとPDF文字のページ内収まりを確認。通信プログラム変更・実機操作なし。HOST側UARTピン、USB給電・改造要否、コネクタ端子番号、引出し位置は未確定。HW-01／USB-SUB-01をOpen維持。製造用加工確定図ではない。
