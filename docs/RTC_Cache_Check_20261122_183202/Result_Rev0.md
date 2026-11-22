# RTC・Cache確認 2026-11-22 Rev.0

## 結果と確認範囲

RTC読取りとSTATUS Cacheの実機確認は成功。通信異常・不完全Decode・Control後の無効化は、PCの既存Unit/Mock試験72件ですべて成功した。設定変更を伴うControlや意図的な通信障害は実機に実行していない。量産の総合受入や全Cacheの実機検証完了とはしない。

## 実機で確認できた事実

親unique_id 69f7d45962cfdfad、COM6保守、COM7 ATE/57600 8N1、COM22受動監視を使用。親はリセットせず、既存RAMアプリのservice_onceを32秒間処理した。cache_manager / command_dispatcher / rtc_driver / nf55_commandの4モジュールは実機とPCソースのサイズ・SHA256が一致。

### RTC

- ATEのRTC_DATE?、RTC_TIME?、RTC_DATETIME?、RTC_CHECK?が有効な日付・時刻・OKを返した。
- RTC_DATETIME?を6回読取り、20261122_183204から183209へ5秒進行。PC単調時計の対応区間は5.062秒。
- DS3231 Statusは前後とも0x09。OSF（発振停止フラグ、bit7）は前後とも0。RTC_CHECK?だけではOSFを確認しない実装のため、read_statusでも別途照合した。
- 各秒のPC受信時刻との表示差は約1.02～1.08秒遅れ。RTC表示の1秒分解能、PC時刻の正確性と通信時間を含む観測値であり、これだけでRTC精度・ドリフトを判定しない。
- RTC_SETやNF55G CLOCK_SYNCは送っていない。時刻・Statusレジスタの書込みなし。

### STATUS Cache

- 試験開始時にSTATUSのみRAM上で明示INVALID化。既存の保持値を使わず、37個の個別ATE QueryがすべてERR:CACHE_INVALIDを返した。
- 明示STATUS_REFRESHを1回実施。実機D1通信は成功し、処理時間23 ms、Command Retry=0、Response Retry=0、ambiguous=False。
- 通信呼出し直前にSTATUSがINVALIDであることをRAMの観測proxyで確認。proxyはD1一回以外を許可しない。実通信は既存Protocolを使用し、観測後にdispatcher.protocolを元へ戻した。
- Refresh後のSTATUSはVALID、source_cmd=D1。37個のQueryを2巡（74照会）し、保存された各フィールドと応答が一致。
- 111個の個別Query（無効時37＋有効時74）によるProtocol.transact追加呼出しは0。全試験中の呼出しは明示D1一回のみ。
- 有効時の個別Queryで値・updated_ms・source_cmdが変化しないことを確認。他のCacheはメタデータ・データとも前後一致。
- これはキャッシュの取得・参照契約の確認であり、D1各フラグの製品合否判定ではない。実際の読取り内容はdevice_snapshot.jsonに保存。

## PC上で確認した異常系（実機故障の発生試験ではない）

既存のtests.test_rtc_driver、tests.test_read_cache_integration、tests.test_control_cache_integration、tests.test_frame_cache_decodeを実行。72件、0.043秒、すべてOK。

- RTC未接続、日時の書式・暦の不正、DS3231レジスタ・OSF処理。
- Refresh開始時の無効化、通信タイムアウト・UART例外・HWE・Decode不良時のINVALID維持。
- 不完全DecodeをVALIDへ昇格しないこと、Refresh失敗後に古い値を復活させないこと。
- Control成功／実行成否不明時の関連Cache無効化、明確な拒否時の保持、Control応答からSTATUSへ転用しないこと。
- Queryが自動Refresh・NF55G送信を起こさないこと。

## 終了時状態

親runtime停止、NF55G IDLE、Logger停止、drop=0、Queue=0。ATE待ち要求0・送信残り0・ATE例外なし。既存SDログはSHA前後一致。CDC fault・親nonce・外部PIO SM4/5停止を維持。COMポート解放。STATUSのみ今回の実機D1成功結果としてVALID。外部測定器への要求・FW書込みなし。

## 未確認事項

RTCの長期精度・電源断中のバックアップ保持・日付境界の実機通過、STATUS以外のCacheの今回の実機Refresh、実機の設定変更／意図的通信異常を伴う無効化、QR／DMM取得Cacheの統合受入は未実施。QRは11月23日の取付け後に試験予定、CDC診断版.22.3も同日の予定を維持。

## 証跡

- [集計](result.json)
- [実機スナップショット](device_snapshot.json)
- [ATE要求・応答・PC時刻](requests.json)
- [ATE原文](ate.raw)
- [実機RAM実行コード](device_check.py)
- [PC実行スクリプト](run_check.py)
- [実機処理出力](device_stdout.raw)
- [Unit/Mock 72件全出力](Host_RTC_Cache_Unit.log)
