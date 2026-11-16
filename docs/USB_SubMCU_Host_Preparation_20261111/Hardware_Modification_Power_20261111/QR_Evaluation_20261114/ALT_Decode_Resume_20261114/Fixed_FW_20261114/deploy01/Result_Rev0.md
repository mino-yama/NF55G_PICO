# 固定接続候補FW 配置結果 Rev.0

2026-11-14。ユーザーのBOOTSEL準備完了を受けて実施。外部5V・QR・UARTを外しPC Type_C1のみ接続する手順。

対象chipid A06FEA01012EC137、RP2350 A4、ARM Secure、Flash2MB。配置前版qr-uart-20261114.2を確認。
Flash全2MBをbefore.binへ退避。SHA-256=e46ab98d8ec514665a6ae8b69b52c6e46f19b6de50eed293f62bed7c1e1ad997。
新UF2=84480byte、SHA-256=da331d3f14725f666191c2cda6ce180a3c44bf3b53a1d41e657e6284fa304424。
load -v成功、独立verify成功、配置後infoでqr-fixed-20261114.1と同一chipidを確認、reboot終了0。

書込み・Flash照合は完了。外部給電・QR固定接続でのcold-startと連続読取はまだ未実施。USB native CDCは無効のため、通常起動で新COMが出ることを期待しない。起動確認はGP0診断UARTで行う。
ビルド時manifestのflashed=falseは配布固定時点の情報であり、実機配置履歴はこの記録を参照する。

[退避原文](before.bin)／[退避ログ](backup.txt)／[配置前情報](info_before.txt)／[書込み](load.txt)／[独立verify](verify.txt)／[配置後情報](info_after.txt)／[配置状態](status.json)／[reboot結果](reboot_status.json)
