#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"

const cmd_tbl_t CMD_TBL[VAILD_CMD_ID_NUM] =
{
    // CMD,DATA長
    {'S','P',50},  // 0   各種閾値設定用 (SET PARAMETER)
    {'R','P', 0},  // 1   各種閾値初期値設定 (RESET PARAMETER)
    {'S','E', 4},  // 2   ERP 設定 (SET ERP)
    {'S','C',12},  // 3   時刻設定 (SET CLOCK)
    {'S','S',50},  // 4   製造情報設定 (SET SERIAL)
    {'S','L', 8},  // 5   寿命計算結果記憶 (SET LIFE)
    {'B','C', 1},  // 6   寿命診断実行 (BATT CHECK)
    {'C','N', 1},  // 7   強制充電 (CHARGE ON)
    {'C','F', 1},  // 8   強制充電停止 (CHARGE OFF)
    {'B','E', 0},  // 9   バックアップ許可 (BACKUP ENABLE)
    {'B','F', 0},  // 10  バックアップ停止 (BACKUP OFF)
    {'O','R', 0},  // 11  復電リスタート制御 (OUTPUT RESTART)
    {'D','0', 0},  // 12  全データ取得 (GET DATA0)
    {'D','1', 0},  // 13  状態情報 (GET DATA1)
    {'D','2', 0},  // 14  起動時寿命計算用 (GET DATA2)
    {'D','3', 0},  // 15  通常寿命計算用 (GET DATA3)
    {'D','4', 0},  // 16  保守情報取得 (GET DATA4)
    {'D','5', 0},  // 17  REV/号機・設定確認 (GET DATA5)
    {'E','L', 2},  // 18  エラーログ取得 (ERROR LOG)
    {'O','L', 2},  // 19  ON/OFF ログ取得 (OPERATE LOG)
    {'C','D', 1},  // 20  データクリア (CLEAR DATA)
    {'C','L', 0},  // 21  ログ全クリア (CLEAR LOG)
    {'F','U', 0},  // 22  FW アップデート (FW UPDATE)
    {'F','D', 6},  // 23  FW データ取得 (FW DATA)
    {'A','D',10},  // 24  バッテリ電圧補正機能 (ADJUST)
    {'A','R', 0}   // 25  バッテリ電圧補正機能_読み出し用 (ADJUST READ)
};

const uint8_t ERROR_RESPONSE_TBL[][ERR_RES_NUM] =
{
    { STX, 0x00, 0x00, 'X', 'X', 'X', ETX, 0x00, 0x00 },  // 0:
    { STX, 0x00, 0x00, 'C', 'M', 'E', ETX, 0x00, 0x00 },  // 1:コマンドエラー(CME)レスポンス
    { STX, 0x00, 0x00, 'P', 'M', 'E', ETX, 0x00, 0x00 },  // 2:パラメータエラー(PME)レスポンス
    { STX, 0x00, 0x00, 'S', 'Q', 'E', ETX, 0x00, 0x00 },  // 3:シーケンスエラー(SQE)レスポンス
    { STX, 0x00, 0x00, 'H', 'W', 'E', ETX, 0x00, 0x00 },  // 4:HW破損エラー(HWE)レスポンス
    { STX, 0x00, 0x00, 'M', 'C', 'M', ETX, 0x00, 0x00 },  // 5:多重コマンド受信(MCM)レスポンス
    { STX, 0x00, 0x00, 'F', 'U', 'E', ETX, 0x00, 0x00 }   // 6:FWアップデートエラー(FUE)レスポンス
};

const uint8_t MONTH_END_TBL[13] = {31,31,28,31,30,31,30,31,31,30,31,30,31};

const set_parameter_t SET_PRAMETER_DEF_TBL =
{
    .ps_on_backup = _ENABLE_,    // 有効        停電時のバックアップ動作設定
    .ac_link      = _DISABLE_,   // 無効        停電後の復電検出におけるリスタート動作設定
    .auto_charge  = _ENABLE_LV2_,// 有効レベル2 自動充電方式の設定
    .event        = _DISABLE_,   // 無効        イベント送信設定
    .max_backup_time = 0,        // 無制限      最大バックアップ時間設定(分)
    .min_backup_time = 15,       // 15秒        最小バックアップ時間設定(秒)
    .restart_time    = 15,       // 15秒        AC_LINKが有効およびOUTPUT RESTARTコマンドを受信時のリスタート実行時に出力をオフする時間
    .batt_low_thf    = 50,       // 50%         バッテリ充電量低下(BATT_LOW)閾値  0:初期値
    .batt_cap_mah    = 4900,     // 4900mAh     バッテリ容量(mAh単位)             0:初期値
    .batt_cap_wh     = 36,       // 36Wh        バッテリ容量(Wh単位)              0:初期値
    .dummy1 = 0,
    .chg_ir_thd      = 0,        // 0(判定しない) 充電DCIRの判定閾値
    .batt_wng_thd    = 65,       // 65℃        バッテリ充電抑止温度閾値          0:初期値
    .batt_alm_thd    = 80,       // 80℃        バッテリ温度異常閾値              0:初期値
    .adu_temp_thd    = 85,       // 85℃        AC/DC部の温度警告(ADU_TEMP_WNG)の検出閾値   0:初期値
    .bbu_temp_thd    = 85,       // 85℃        BACKUP部の温度警告(BBU_TEMP_WNG)の検出閾値  0:初期値
    .fan_wng_thd     = 615       // 615rpm      FANの回転停止警告(FAN_WMG)の検出閾値        0:初期値
};

const uint8_t FFFF_TBL[]   = "FFFF";
const uint8_t FFFFFF_TBL[] = "FFFFFF";

