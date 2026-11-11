# UART版FW準備・検証 結果 Rev.0

日付: 2026-11-11／工程②「UART版FW」

**qr-uart-20261111.1をビルド・検証し配布用に保存。実機書込み・UART波形／ログ受信・QR動作は未実施。**

## 配布物

- [UART版UF2](../../../firmware/usb_submcu_host_probe/releases/qr-uart-20261111.1/usb_submcu_qr_uart_probe.uf2): **79360byte**、SHA-256 **31da5f6f743fe6447fa03c56d223ccd6f12ecb074a8cc92374867e1cee754a70**。
- [配布manifest](../../../firmware/usb_submcu_host_probe/releases/qr-uart-20261111.1/manifest.json): UF2／ELF／bin、当該ソース、メーカー原文・互換派生、ビルド・解析・受信スクリプトとログ検査テストのhashを記録。
- 名称usb_submcu_qr_uart_probe、版qr-uart-20261111.1。RP2350 ARM Secure、SDK2.2.0、2MB専用ボード設定。運用対象は追加基板A06FEA01012EC137。個体IDをコード固定する版ではなく、実機で返る個体IDを照合する。

## 変更内容と理由

- CMakeLists.txt: UART版とRAM版の版名を分離。PROBE_FW_VERSIONをbootレコードとバイナリ情報で共通化した。
- main.c: GP0 UART0 TXを115200／8N1・HWフローなしで設定。GP1のUART割当てや受信処理はしない。GP0とType_C2 GP12／13をメタデータに記録。
- 起動時はUSB初期化前に版・個体IDを出し、Host configure/initのfalse経路でも診断出力を排出する。通常Hostループの送信はFIFO空き確認と1呼出し最大16byteを維持。
- build_usb_submcu_host_probe.ps1: -DiagnosticTxはbuild_uart_gp0を使い、RAM版buildと分離。旧配布物は変更しない。
- フレームABI・記録件数・原文取得という役割は[UART仕様](Specification_Rev0.md)を参照。正式な治具UARTプロトコル・QR判定・DMM・2 Host対応は追加していない。

## 検証結果

| 検証 | 結果 | 証跡 |
|---|---|---|
| ARMビルド・リンク・UF2生成 | 終了0、86ステップ。アプリ2ソースは-Wall／-Wextra／-Werror | [Build.txt](Build.txt) |
| Host／Mock・ログ解析回帰 | 全301件成功、9.173秒 | [Host_Mock.txt](Host_Mock.txt) |
| UF2全ブロック | 512byte境界、155ブロックのmagic確認 | manifest |
| 配布物の識別 | UART版の名称・版、ARM Secure、SDK2.2.0、GP0 TX・GP12／13が一致 | [UF2解析](UF2_Info.txt) |
| ELFシンボル・ABI | uart_init／uart_set_format／pump_uart／PIO Hostあり、g_probe=19476byte。UART read／native USB Device初期化シンボルなし | [シンボル](ELF_Symbols.txt) |
| mainのARMコード | uart_initの115200、8N1設定・GPIO0割当て、USB開始前のログ排出をソースと照合 | [逆アセンブル](Main_Disassembly.txt) |
| 旧RAM版と原典 | 旧配布43ファイル・上流原文14ファイルのhash一致 | [保全確認](Preservation_Check.json) |

Host／MockはPC側Pythonの回帰試験であり、UART出力の実機受入を代替しない。SH-U05A単体の112件ループバック結果も、このFWの起動・波形・USB Timingを実証したものではない。

## 次の工程③と未確認

1. USBを抜いてSH-U05AのTXD–RXD短絡を外す。UARTモード選択ジャンパは維持。除去済みとの確認はまだない。
2. 実機直前に[治具図Rev.4](../../drawings/NF55G_Fixture_20261111_Rev4/README.md)を使い、R13／CC抵抗の改造と電源枝の保護・極性確認を案内する。抵抗サイズ・現物照合も残る。
3. 改造後の電源確認が済んでから、対象個体を照合してUART版を書込み・verifyする。今回その操作は行っていない。
4. [配線・設定手順](../SH_U05A_Debug_Setup_Rev1.md)に従い、追加基板GP0→SH-U05A RXDとGNDのみ接続。3V3／5V0／TXDは追加基板へ接続しない。
5. 外部給電時はPC Type_C1を外し、起動前からUART受信を開始。版qr-uart-20261111.1と実個体IDを確認後、QR列挙・HID原文を取得する。

今回の操作はPC上のビルド・ファイル解析・Host／Mockのみ。COM22・COM21・親Pico・追加基板・QR／7355・NF55G／ATEへは接続・送信・reset・書込みしていない。USB-SUB-01／02／03はOpenのまま。回路改造・UART実受信・QR35文字一致・7355・2 Host・正式親子UARTの受入は今後。
