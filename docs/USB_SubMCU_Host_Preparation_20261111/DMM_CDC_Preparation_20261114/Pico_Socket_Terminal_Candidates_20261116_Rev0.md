# Pico 2用ソケットとはんだ付け基板とネジ端子台の候補

2026-11-16 JST。親Pico 2の追加PIO UARTを引き出す用途の候補調査。製品を選定・購入・配線変更した記録ではない。

## 候補

|用途|候補と公式ページ|構成と寸法|今回の適用判断|
|---|---|---|---|
|Picoとほぼ同寸ではんだ付け|[Adafruit PiCowbell Proto #5200](https://www.adafruit.com/product/5200)|52.0×20.4×4.7mm。20pin×2のヘッダーを別途選択してはんだ付け。各ピンに追加の引出し穴、中央に13列の4穴連結パターン|省スペース第一候補。適切なメスソケットを付け、親GP8/9、GP12/13、GNDを引き出す案|
|ソケット実装済み＋ネジ端子台|[Adafruit Terminal PiCowbell #5907](https://www.adafruit.com/product/5907)|20pin×2のソケット実装済み。40pinを1対1でネジ端子へ引出し、はんだ用の複製穴と中央試作領域あり|両方の要望を満たす製品。Picoより幅が増えるため積層・端子操作スペースを確認|
|はんだ作業領域を広くする|[Adafruit Proto Under Plate #5905](https://www.adafruit.com/product/5905)|52.0×38.2×5.6mm。ヘッダー別途取付け、追加配線用パッドあり|配線を基板上に整理したい場合。Pico同幅ではない|
|手持ち基板にソケット追加|[秋月 FH-1x20-3.2CO / 117585](https://akizukidenshi.com/catalog/g/g117585/)、[FH-1x20-6.1CO / 117584](https://akizukidenshi.com/catalog/g/g117584/)|Pico用20P左右セット、2.54mm、リード長3.2/6.1mm。基板は別途必要|信号名付き。ユニバーサル基板で自作する場合の国内調達候補|

製品の同寸/ヘッダー位置をもとにPico 2の40pin端子への機械的適用を検討する。Pico用の製品名だけで、現在のExpander/積層構成で無加工装着できるとは確定しない。

## 現治具での使い方の案

今回の既存Pico-Quad-Expanderを維持し、接続可能な位置の40pinから信号を取り出すなら、#5200に接続方向に合う20pin×2のソケットを装着し、複製パッドからUART線をはんだ付けする案が小さい。空きスロットの有無・実装面・メス/オス・高さ・端子へのアクセスは現物で照合する。

Pico 2単体を差し込んでネジ止め配線を行うなら#5907が分かりやすい。ただしメーカーはソケット実装済みのためshort/stacking headerへ交換できない構成と説明している。既存Expanderへの中継挿入を無加工で保証せず、用途に合う接続面を確認する。ヘッダー未実装版#5904はメーカーでNo longer stockedの表示なので、これを入手前提としない。

積層が必要な場合の別売候補は[Adafruit Pico Stacking Headers #5582](https://www.adafruit.com/product/5582)。通常のメスソケット、長リードソケット、上下中継用スタッキングヘッダーは役割が違い、リードが長いだけで下側も挿抜用になるとは扱わない。

ネジ端子台を使う場合も、全40pin分が必須ではない。#5200等の引出しを使い、外付け3極端子台をQR用TX/RX/GNDと7355用TX/RX/GNDの2組にする自作案もある。端子台そのものの寸法・線径・実装位置は今回未選定。

## ピンと注意点

- 親PIO UART候補はQRがGP8 TX/GP9 RX、7355がGP12 TX/GP13 RX。基板は引出し専用として扱い、既存ATE/NF55G/SD/RTC割付は変えない。
- PiCowbellのSTEMMA QTはGP4/GP5へ接続される。今回のNF55G UART1と共用しないため、そこへI2C機器を接続しない。製品説明ではI2C pull-up自体は未実装。
- #5200等の中央試作穴には4穴連結等の既存パターンがあり、全穴独立のユニバーサル基板ではない。はんだ前にパターンを確認する。
- Pico端子配列の候補であり、RP2350-USB-A/USB-C基板用のソケットではない。Host基板は別形状である。

## 確認範囲

メーカー/販売者ページと[Terminal PiCowbellの公式pinout](https://learn.adafruit.com/adafruit-terminal-picowbell-for-pico/pinouts)、[公式組立構成](https://learn.adafruit.com/adafruit-terminal-picowbell-for-pico/overview)を確認。寸法・ヘッダーの有無・配線パッドの説明を比較した。注文時の価格/在庫/配送条件は別途確認する。

原典・FW・実配線は変更していない。実機寸法測定・装着試験なし。今回の成果は候補メモのみで、コード試験を必要とする変更はない。
