# HOST復旧作業・両方向診断 Rev.0

2026-11-28。HOST復旧を優先するユーザー指示で、固定基板・コネクタを変更せず追加診断した。現時点で通常のHOST情報応答は復旧していない。R3校正取得・400セット耐久は未開始。

## 両方向の追加診断

元の全Flash退避を保持し、UART単体診断版`meter-host-relay-uartdiag-20261128.2`を一時配置・独立verifyした。7355 USBと外部5Vを外したPC USB単独給電で実施。native USB COM25は既知HOST `BFCF2EDB84B0B37F`を識別した。

- 親からの通常HOST_INFO要求141バイトを親PIOの送信側で記録したが、HOST自身のUART受信数はrx=1から増えなかった。
- native USBの明示自己診断で、HOST内部の応答生成とUART書込み235バイトを計数。これは診断用sessionへの応答であり、通常ATE経路の成功とは扱わない。
- 監視開始直後の自己診断送信に同期し直した[2回目の採取](uart_diagnostic_v2/capture_02/capture_result.json)でも、親UART受信0バイト。親GP13の1 ms周期読取りは変化0・最終high。再実行時は同じ診断要求の再使用によりHOSTのUART書込みが235→342へ増えた。これらは内部の書込み計数であり、端子から出た電気信号を直接検証した値ではない。
- HOST GPIOの入力変化計数は観測中に増加しなかった。診断で入力化した端子はGPIO2～29（電源関連候補23／24／25を除く）、GPIO1は既存UART RXを維持。GPIO0はUART TXを維持。未使用端子の設定は一時診断だけで、通常FWへ残していない。負のサンプリング結果だけで全信号の不在や断線箇所を断定しない。

候補・ソース・ビルド・配置結果は`uart_diagnostic_v2/`に保存。初回ビルドはPC側240秒期限を超えた後に生成が完了し、増分ビルドの正常終了で完成を確認した。最終UF2 SHA-256は`5701979a2b22aa01d6af8b563cb1d8472aca9bb81d03ed3e319df72ae5fe23c9`。

## 低速出力確認の扱い

親GP12をUARTではなく一時的なSIO出力へ切り替えた低速試験では、設定直後の読戻しがhighのままと記録された。これは低レベルを出せない証拠として採用しない。続く[出力レジスタ・読戻し確認](uart_diagnostic_v2/pin_drive_check.log)では、20 ms待機後に以下を確認した。

| 状態 | GPIO機能 | 出力値 | 読戻し |
|---|---|---|---|
| 開始前 | PIO1（CTRL=7） | high | 1 |
| 診断出力low | SIO（CTRL=5） | SIO OUT bit12=0、OE bit12=1 | 0 |
| 診断出力high | SIO（CTRL=5） | SIO OUT bit12=1、OE bit12=1 | 1 |
| 終了後 | 元のPIO1（CTRL=7） | high | 1 |

従って、設定直後と待機後の観測差はあるが、GPIO出力不良を確定しない。最初の低速採取はPC側の常駐再開待ちが25秒でtimeoutとなり、HOST採取結果の保存まで到達しなかった。親側finallyでCTRL=7・TX activeへ戻った記録は残り、追加の直接API確認でも復元を確認した。

## 復元と現在の状態

一時診断終了後、元の全2 MiBへ復元し、独立verify・.25.2版読戻し・通常起動を確認。[復元結果](uart_diagnostic_v2/restore_recovery_end/result.json)。診断版は残していない。

復元後の[通常情報照会](ate_recovery_post_v2.json)はHOST_INFO timeout（1,000 ms）、治具IDN正常、IDLE／SD OK／drop0。親は試行停止・busy=Falseだが、中継fault=Trueが残っていた。保存済みソース・配置設定は変更していない。次の無給電導通確認のため、追加の操作を止めている。導通確認後の通常給電・親再起動でRAM faultを再確認する。

原因は未確定。設定・既知FWの再書込みだけでは復旧していないため、全給電停止時の①親GP12―HOST GP1、②HOST GP0―親GP13、③共通GNDの実導通測定を依頼した。基板・コネクタが従来どおりという申告と測定事実は区別し、断線・HOST故障・GPIO故障を独断で確定しない。

製品指令・校正書込み・R3測定は実行していない。診断結果を400セット受入へ加算しない。
