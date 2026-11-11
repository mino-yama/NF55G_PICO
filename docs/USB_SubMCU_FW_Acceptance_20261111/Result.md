# USB SubMCU 確認用UF2のビルド・書込み・受入結果

日付: 2026-11-11
状態: **開発用確認FWを書込み・照合済み。USB単体確認は再起動前後とも成功。QR／DMM／UARTは未実装・未受入。**

## 対象と配布物

- 対象: Waveshare RP2350-USB-C、USB serial A06FEA01012EC137、COM21。Flash実機情報2048K。既存治具COM6／69F7D45962CFDFADとは別対象。
- FW識別: usb_submcu_acceptance / dev-20261111.1 / BUILD=583b3b6ba99e14bf。量産版採番の確定・承認ではなく、今回の隔離した確認用開発物の識別。
- [書込み済みUF2](../../firmware/usb_submcu_acceptance/releases/dev-20261111.1/usb_submcu_acceptance.uf2): 61,440 byte、SHA-256 a95639a6062cd69ca670741bbd34a15e3465a7f75da2bd3dd0f993281c668c37。
- [配布manifest](../../firmware/usb_submcu_acceptance/releases/dev-20261111.1/manifest.json): UF2／ELF／bin、ソース・ボード設定・HIL・ビルドスクリプトのhash、依存版を収録。source/に対象ソースのコピーも保持。
- [ソースと診断仕様](../../firmware/usb_submcu_acceptance/README.md)。今回のUSB診断コマンドは正式ATE／内部UART仕様へ追加しない。

## 旧FWの識別・バックアップ

元FWはpicotoolでusb_device、SDK 2.2.0、pico_board=pico2、ARM Secure、UART／USB stdio、ビルド日May 13 2026と読めた。名称やUSB列挙だけからQR／DMM機能の有無を断定しない。

- [元Flash全2MB](backup/original_flash_2MB.bin): 2,097,152 byte、SHA-256 1b90c7066b977f42d163b59d115742dbb56ba618f5e76862f91f2a490733b474。
- 全Flashを保存後、元基板とpicotool verifyで一致（OK、終了コード0）。USB serialを限定し、既存治具は操作していない。
- [退避台帳](backup/manifest.json)、[旧FW識別ログ](backup/original_info.txt)。退避と最初の照合には既存Arduino環境のpicotool 2.0.0を使用。以後のUF2生成・書込み等には公式2.2.0-a4を使用。

## 実装とビルド

Type_C1のUSB CDCだけを直接初期化するC++プログラムを新規作成。ID?／PING／UPTIME?／ECHOのみを処理し、不明指令を拒否する。CR／LF／CRLF、95文字上限、過長・不正ASCII行の破棄、接続切断時の部分行失効を実装した。製品PASS/FAIL、測定、補正、NF55G通信は行わない。

専用ボード設定でRP2350A／Flash 2MB／ARM Secureを指定。汎用Pico 2の4MBや既定GPIOを流用しない。UART stdio・1200bpsによるresetを無効化。USB Host・PIO・外部GPIO・LED・UART・SD・RTCを初期化しない。SDKのpicotool用USB vendor reset interfaceは復旧用に保持する。

依存版: SDK 2.2.0（a1438dff1d38bd9c65dbd693f0e5db4b9ae91779）、TinyUSB 86ad6e56c1700e85f1c5678607a762cfe3aa2f47、GCC Arm 14.3.0、CMake 3.31.6、Ninja 1.11.1.4、picotool 2.2.0-a4（公式pico-sdk-tools v2.2.0-4）。GCCは既存Arduino環境を利用し、SDK・picotoolは案件内tools/usb_submcu、CMake／Ninjaは案件内.venvへ配置。原典・既存治具実装は変更していない。

- [構成ログ](configure.txt)、[ビルドログ](build.txt): 終了コード0。アプリのコンパイルは-Wall -Wextra -Werror。
- [生成UF2の解析](uf2_info.txt): RP2350 ARM Secure、dev-20261111.1、USB stdioのみ、Fixed Pin none、範囲0x10000000〜0x10007648。
- [最終ELFのシンボル](elf_symbols.txt): uart_init／gpio_init／pio_sm_init／tuh_init／hcd_init／cyw43_arch_initに一致するシンボルなし。ソース確認と合わせて今回の初期化範囲を確認した。
- 再ビルド: scripts/build_usb_submcu_acceptance.ps1。SDK／TinyUSBは指定コミット、ツール版はmanifestを参照。ビルド日時などのメタデータを含むため、後日の再ビルドが同じバイナリhashになることまでは保証しない。

## 書込みと実機試験

picotool load -vで対象USB serialだけを指定し、上記配布UF2をロード・Flash照合（OK）。その後通常起動へ戻した。[書込み照合ログ](load_verify.txt)。

| 試験 | 結果 | 証跡 |
|---|---|---|
| Host Unit／Mock NF55G回帰 | 287件成功、7.459秒 | [実行ログ](Host_Mock_20261111.txt) |
| 書込み後USB単体 | 123チェック成功、COM21、同じFW／BUILD／個体ID | [送受信JSON](usb_hil_run01.json) |
| USB経由の再起動後 | 123チェック成功、COM21、同じFW／BUILD／個体ID | [再起動後JSON](usb_hil_after_reboot.json) |
| 実機の配置FW情報 | SDK・ボード・FW版一致 | [配置情報](deployed_info.txt) |

USB試験内容: ID一致、PINGの3種類の終端、分割CRLF、連結指令、uptime進行、大小文字・先頭ゼロ保持、95文字境界、96文字エラー、NUL混入エラーと後続復帰、FW_UPDATEを不明指令として拒否、空行無応答、連番100件のecho、部分行を残したDTR切断／再接続後の失効、余分な応答がないこと。2回とも123チェックで成功。USB serialを照合するHILスクリプトはscripts/usb_submcu_acceptance_hil.py。

再起動はpicotool info -a -fによるBOOT移行と通常起動復帰を用いた。物理的なUSB抜差し・電源断再投入は今回未実施であり、電源断保持や長時間信頼性試験とは区別する。

実機応答:

    FW=USB_SUBMCU_ACCEPTANCE;VERSION=dev-20261111.1;BUILD=583b3b6ba99e14bf;SDK=2.2.0;BOARD=RP2350_USB_C;ID=A06FEA01012EC137;USB_HOST=OFF;UART=OFF;PIO=OFF

試験終了時は通常起動で待受、HILのCOM21ハンドルは閉じた。LEDは本FWでは駆動しない。

## 復旧・使用制限

旧FWへ戻す場合は、元binのhashと対象USB serialを照合し、picotool load -v <元bin> -o 0x10000000 --ser A06FEA01012EC137 -fで全Flashを復旧する。これは復旧手順の記載であり、今回の復旧再書込みは未実施。BOOTからの復旧が必要ならType_C1でBOOT＋RUNを使用し、対象識別後にロードする。UF2を手動コピーする場合もドライブ名・INFO_UF2を照合し、既存治具と取り違えない。

CC抵抗は変更していない。DB_N（DN1）の微細端子測定は中止したまま。Type_C2のSource条件、D線プルアップ、逆流・電流制限・供給能力は未確認で、QR・7355・治具UARTは接続せず試験範囲外。USB-SUB-01／USB-SUB-02と正式内部プロトコル等の未確定事項はOpen継続。今回の単体FWをQR／DMM対応済み・量産承認済みと扱わない。

## 今回追加・更新したファイル

- firmware/usb_submcu_acceptance/: USB単体確認FW、専用ボード設定、診断仕様、ビルド依存、配布UF2／ELF／bin／ソースsnapshot／manifest。
- scripts/build_usb_submcu_acceptance.ps1、scripts/usb_submcu_acceptance_hil.py: 再ビルドと実機受入。
- .gitignore: 案件内SDK・生成中間物を除外。
- 本受入フォルダ: 元FWの退避と識別、ビルド・配置・試験証跡。
- docsのCHANGELOG／版数管理表／ソフトウェア境界／Test Specification／Open Issues／事前確認記録: 今回の開発版と隔離した受入範囲を追記。既存ATE／NF55Gの通信仕様・実装は変更していない。

公開出典: [Waveshare C/C++資料](https://docs.waveshare.com/RP2350-USB-C/C)、[SDK 2.2.0](https://github.com/raspberrypi/pico-sdk/releases/tag/2.2.0)、[公式Windowsツール](https://github.com/raspberrypi/pico-sdk-tools/releases/tag/v2.2.0-4)。
