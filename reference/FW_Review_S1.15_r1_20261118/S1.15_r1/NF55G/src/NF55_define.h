#ifndef _NF55_DEFINE_H_
#define _NF55_DEFINE_H_

#include    <stdint.h>
#include    <string.h>
#include    <time.h>
#include    <ti/iqmath/include/IQmathLib.h>

/////////////////////////////////
//#define _DEBUG_ON_  // Debug
//#define _USE_IQMATH_
//#define _NO_EEPROM_
//#define _DEBUG_DATA_ON_
//#define _RELEASE_MODE_
//#define _FAN_HIS_ENABLE_
//#define _S114_DEBUG_
#define _WWDT_ON_
/////////////////////////////////

//////////////////////////////////////////
#define BOOT_START_ADDRESS   0x07000L    // Boot部の先頭アドレス */
#define BOOT_END_ADDRESS     0x0DFFBL    // Boot部の最終アドレス */
#define BOOT_CRC32_ADDRESS   0x0DFFCL    // Boot部のCRC格納アドレス */
//////////////////////////////////////////

#define FAN_DEBUG_NORMAL (0U)
#define FAN_DEBUG_LOW (1U)
#define FAN_DEBUG_HIGH (2U)
#define FAN_DEBUG_STOP (3U)
extern volatile uint8_t gu8_fan_debug_mode;
extern volatile uint8_t gu8_fan_debug_fast;

#if 0
/* boot部でDebuggerを使うときの設定 */
/* 合わせてlinker script(cmdファイル)のflashの開始アドレスを0x7000から0x0000に変更すること */
//////////////////////////////////////////
#define BOOT_START_ADDRESS   0x00000L    // Boot部の先頭アドレス */
#define BOOT_END_ADDRESS     0x06FFBL    // Boot部の最終アドレス */
#define BOOT_CRC32_ADDRESS   0x06FFCL    // Boot部のCRC格納アドレス */
//////////////////////////////////////////
#endif

//////////////////////////////////////////
#define BOOTBOOT_START_ADDRESS   0x00000L    // Bootboot部の先頭アドレス */
#define BOOTBOOT_END_ADDRESS     0x06FFFL    // Bootboot部の最終アドレス */
//////////////////////////////////////////

/////////////////////////////////
#define FW_REVISION     "S1.15 "    // FW REVISION(6char)
#define FW_VER_MAJ      0           // Release Version x.--
#define FW_VER_MIN      0           // Release Version -.xx
/////////////////////////////////


#define FW_READ_START   (0x00000000UL)
#define FW_READ_END     (0x0001FFFFUL)

#define PIN_CODE        (uint32_t)(0x4E453535L)  // NF55

#define BIT0  0x01
#define BIT1  0x02
#define BIT2  0x04
#define BIT3  0x08
#define BIT4  0x10
#define BIT5  0x20
#define BIT6  0x40
#define BIT7  0x80

/* Output */
// "H"
#define O_PS_ON_OUT_H    DL_GPIO_setPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB6_OUTPUT_PIN )        // PB6  PS_ON_OUT "H"
#define O_BURST_OUT_H    DL_GPIO_setPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB7_OUTPUT_PIN )        // PB7  BURST_OUT "H"
#define O_12V_EN_H       DL_GPIO_setPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB8_OUTPUT_PIN )        // PB8  /12V_EN "H"
#define O_BATT_EN_H      DL_GPIO_setPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB9_OUTPUT_PIN )        // PB9  BATT_EN "H"
#define O_CHGV_11_4V_H   DL_GPIO_setPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB15_OUTPUT_PIN)        // PB15 CHGV_11_4V "H"
#define O_DISCHG12V_EN_H DL_GPIO_setPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB16_OUTPUT_PIN)        // PB16 DISCHG12V_EN "H"
#define O_BATCHG_EN_H    DL_GPIO_setPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA13_OUTPUT_PIN)        // PA13 BATCHG_EN "H"
#define O_VCC_12V_EN_H   DL_GPIO_setPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA14_OUTPUT_PIN)        // PA14 VCC_12V_EN "H"
#define O_TEST_OUT_H     DL_GPIO_setPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB18_OUTPUT_PIN)        // PB18 TEST_OUT "H"

#define O_TEST_OUT_TOG   DL_GPIO_togglePins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB18_OUTPUT_PIN)     // PB18 TEST_OUT Toggle

// "L"
#define O_PS_ON_OUT_L    DL_GPIO_clearPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB6_OUTPUT_PIN )      // PB6  PS_ON_OUT "L"
#define O_BURST_OUT_L    DL_GPIO_clearPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB7_OUTPUT_PIN )      // PB7  BURST_OUT "L"
#define O_12V_EN_L       DL_GPIO_clearPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB8_OUTPUT_PIN )      // PB8  /12V_EN "L"
#define O_BATT_EN_L      DL_GPIO_clearPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB9_OUTPUT_PIN )      // PB9  BATT_EN "L"
#define O_CHGV_11_4V_L   DL_GPIO_clearPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB15_OUTPUT_PIN)      // PB15 CHGV_11_4V "L"
#define O_DISCHG12V_EN_L DL_GPIO_clearPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB16_OUTPUT_PIN)      // PB16 DISCHG12V_EN "L"
#define O_BATCHG_EN_L    DL_GPIO_clearPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA13_OUTPUT_PIN)      // PA13 BATCHG_EN "L"
#define O_VCC_12V_EN_L   DL_GPIO_clearPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA14_OUTPUT_PIN)      // PA14 VCC_12V_EN "L"
#define O_TEST_OUT_L     DL_GPIO_clearPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB18_OUTPUT_PIN)      // PB18 TEST_OUT "L"

/* Input */
#ifndef _DEBUG_ON_   // _DEBUG_ON_有効時はINPUT_DEBUG[]を使用し入力
#define I_PS_ON_IN       (DL_GPIO_readPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA28_INPUT_PIN )!=0)  // PA28  PS_ON_IN
#define I_BURST_IN       (DL_GPIO_readPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA31_INPUT_PIN )!=0)  // PA31  BURST_IN
#define I_DISCHG12V_OVP  (DL_GPIO_readPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA2_INPUT_PIN  )!=0)  // PA2   DISCHG12V_OVP
#define I_AC_ON_IN       (DL_GPIO_readPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB3_INPUT_PIN  )!=0)  // PB3   AC_ON_IN
#define I_PFC_FAIL_IN    (DL_GPIO_readPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA9_INPUT_PIN  )!=0)  // PA9   PFC_FAIL_IN
#define I_FAN_PRM        (DL_GPIO_readPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB14_INPUT_PIN )!=0)  // PB14  FAN_PRM
#define I_TEST_IN        (DL_GPIO_readPins(GPIO_GRP_A_PORT, GPIO_GRP_A_PA18_INPUT_PIN )!=0)  // PA18  TEST_IN
#endif


/* ---------------------------------------------------------------------------*/
#define     ONE_LOOP        1                           // 1ms
#define     TIMER_1ms       (uint32_t)(   1/ONE_LOOP)
#define     TIMER_2ms       (uint32_t)(   2/ONE_LOOP)
#define     TIMER_3ms       (uint32_t)(   3/ONE_LOOP)
#define     TIMER_4ms       (uint32_t)(   4/ONE_LOOP)
#define     TIMER_5ms       (uint32_t)(   5/ONE_LOOP)
#define     TIMER_6ms       (uint32_t)(   6/ONE_LOOP)
#define     TIMER_8ms       (uint32_t)(   8/ONE_LOOP)
#define     TIMER_10ms      (uint32_t)(  10/ONE_LOOP)
#define     TIMER_20ms      (uint32_t)(  20/ONE_LOOP)
#define     TIMER_30ms      (uint32_t)(  30/ONE_LOOP)
#define     TIMER_50ms      (uint32_t)(  50/ONE_LOOP)
#define     TIMER_60ms      (uint32_t)(  60/ONE_LOOP)
#define     TIMER_100ms     (uint32_t)( 100/ONE_LOOP)
#define     TIMER_150ms     (uint32_t)( 150/ONE_LOOP)
#define     TIMER_200ms     (uint32_t)( 200/ONE_LOOP)
#define     TIMER_250ms     (uint32_t)( 250/ONE_LOOP)
#define     TIMER_300ms     (uint32_t)( 300/ONE_LOOP)
#define     TIMER_350ms     (uint32_t)( 350/ONE_LOOP)
#define     TIMER_500ms     (uint32_t)( 500/ONE_LOOP)
#define     TIMER_600ms     (uint32_t)( 600/ONE_LOOP)
#define     TIMER_1000ms    (uint32_t)(1000/ONE_LOOP)  // 1sec
#define     TIMER_2000ms    (uint32_t)(2000/ONE_LOOP)  // 2sec
#define     TIMER_3000ms    (uint32_t)(3000/ONE_LOOP)  // 3sec
#define     TIMER_5000ms    (uint32_t)(5000/ONE_LOOP)  // 5sec
#define     TIMER_6000ms    (uint32_t)(6000/ONE_LOOP)  // 6sec
#define     TIMER_8000ms    (uint32_t)(8000/ONE_LOOP)  // 8sec
#define     TIMER_10s       (uint32_t)(10000/ONE_LOOP) // 10sec
#define     TIMER_15s       (uint32_t)(15000/ONE_LOOP) // 15sec
#define     TIMER_30s       (uint32_t)(30000/ONE_LOOP) // 30sec
#define     TIMER_60s       (uint32_t)(60000/ONE_LOOP) // 60sec
#define     TIMER_3min      (uint32_t)(180000/ONE_LOOP)  // 3min
#define     TIMER_5min      (uint32_t)(300000/ONE_LOOP)  // 5min
#define     TIMER_10min     (uint32_t)(600000/ONE_LOOP)  // 10min
#define     TIMER_1hour     (uint32_t)(3600000/ONE_LOOP) // 1Hour

#define     MAX_DET_TIMER  TIMER_10min  // input_filter最大値

/* ---------------------------------------------------------------------------*/
#define     _Z_         0
#define     _NZ_        1

#define     _OFF_       0
#define     _ON_        1
#define     _NOT_       2
#define     _L_         0
#define     _H_         1

#define     _OK_        0
#define     _ERROR_     1

#define     _RESET_     0
#define     _SET_       1

#define     _OUT_NOT_   0
#define     _OUT_OFF_   1
#define     _OUT_ON_    2

#define     _TRG_NONE_  0     // Trigger無
#define     _TRG_ON_    1     // Trigger=ON
#define     _TRG_OFF_   2     // Trigger=OFF

#define     _DISABLE_    0     // 無効
#define     _ENABLE_     1     // 有効
#define     _ENABLE_LV1_ 1     // 有効レベル1
#define     _ENABLE_LV2_ 2     // 有効レベル2
#define     _ENABLE_LV3_ 3     // 有効レベル3

#define     _EVENT_LOST_OK_  0  // イベントロスト正常
#define     _EVENT_LOST_NG_  1  // イベントロスト発生

#define     _CHG_MODE_FALSE_ 0
#define     _CHG_MODE_TRUE_  1

#define FW_FLASH_START  (0x00000000UL)
/* ADC */
#define ADC_AVE_VALUE_N     4   // ADC平均値数

/* バッテリ関連 */
#define BATT_NOT_CONNECT_VAL  3847 // バッテリ接続判定AD値(この値以上は未接続とする) 3.1V=3847
#define BATT_CONNECT_VAL      3598

#define _BATT_NOT_CONNECT_  0   // BATT1/BATT2未接続
#define _BATT1_CONNECT_     1   // BATT1接続
//#define _BATT2_CONNECT_     2   // BATT2接続
#define _UNKNOWN_CONNECT_   3

#define TEMP_NOT_CONNECT_VAL    BATT_NOT_CONNECT_VAL

/* 温度計算 */
#define VCC_33V      (3.3)    // VCC 3.3V
#define R_UPPER_10K  (10.0)   // R上 10KΩ
//#define R_UPPER_15K  (15.0) // R上 15KΩ
#define R_LOWER_056K (0.56)   // R下 0.56KΩ
#define T0_25C       (25.0)   // TO  25℃
#define R0_10K       (10.0)   // R0  10KΩ
#define B1_3450      (3450.0) // B   3450K
#define B2_3435      (3435.0) // B   3435K

#define BATT_TEMP_SANSHOU_CO TIMER_4ms // 起動時、バッテリ温度フィルター処理終了までの待機周期数(仮設)

/* AC検出 */
//#define AC_TIME_3_5MS (140000L) // AC ON期間(3.5ms)  3.5ms / (1/40MHz)
//#define AC_TIME_7MS   (280000L) // AC OFF期間(7ms)  7ms / (1/40MHz)
#define AC_TIME_3_5MS  (35000L) // AC ON期間(3.5ms)  3.5ms / (1/10MHz)
#define AC_TIME_7MS    (70000L) // AC OFF期間(7ms)  7ms / (1/10MHz)

// FAN制御用(PWM)
#define PWM_25KHz              (25000L)    // 25KHz
#define SMCLK_40MHz            (40000000L) // SMCLK 40MHz

#define FAN_STOP               0           // モード番号:停止
#define FAN_MIN_SPEED          2           // モード番号:最小
#define FAN_LOW_SPEED          4           // モード番号:低速
#define FAN_MID_SPEED          6           // モード番号:中速
#define FAN_HIGH_SPEED         8           // モード番号:高速
#define FAN_MAX_SPEED          10          // モード番号:最大

#define TEMP_LOW_TO_MID        70          // 低速回転-->中速回転　閾値
#define TEMP_MID_TO_HIGH       75          // 中速回転-->高速回転　閾値
#define TEMP_HIGH_TO_MAX       85          // 高速回転-->最大回転　閾値
#define TEMP_MAX_TO_HIGH       75          // 最大回転-->高速回転　閾値
#define TEMP_HIGH_TO_MID       60          // 高速回転-->中速回転　閾値
#define TEMP_MID_TO_LOW        50          // 中速回転-->低速回転　閾値

#define _TEMP_DOWN_            0           // 温度　低下
#define _TEMP_UP_              1           // 温度　上昇

#define _FAN_CTL_DEFAULT_MODE_ 0           // FAN制御：デフォルト回転モード
#define _FAN_CTL_TEMP_MODE_    1           // FAN制御：温度制御モード

#define FAN_LOW_PERCENTAGE    30          /* 低速のDutyパーセント */
#define FAN_MID_PERCENTAGE    45          /* 中速のDutyパーセント */
#define FAN_HIGH_PERCENTAGE   65          /* 高速のDutyパーセント */
#define FAN_MAX_PERCENTAGE    100         /* 最大のDutyパーセント */

#define FAN_LOW_RPM          1773         /* 低速の目標回転数 */
#define FAN_MID_RPM          2890         /* 中速の目標回転数 */
#define FAN_HIGH_PPM         4380         /* 高速の目標回転数 */
#define FAN_MAX_RPM          6150         /* 最大の目標回転数 */

#define FAN_CYCLE_COUNT     (SMCLK_40MHz / PWM_25KHz)   /* 周期のカウント値 */

/* ---------------------------------------------------------------------------*/
/* UART                                                                      */
/* ---------------------------------------------------------------------------*/
#define SENDBUF_SIZE      384
#define RECVBUF_SIZE      128

#define UART_RCV_MAIN_NUM  128   // 受信(2^nで設定)
#define UART_REQ_NUM  2     // 送信(2^nで設定)
#define UART_RCV_NUM  4     // 受信(2^nで設定)

#define STX         0x02  // STX
#define ETX         0x03  // ETX
#define ACK         0x06  // ACK
#define NAK         0x15  // NAK

#define _DONE_      1  // 完了1
#define _DONE2_     2  // 完了2
#define _CONTINUE_  0  // 継続

#define RETRY_NUM   3  // リトライ回数

/* ---------------------------------------------------------------------------*/
/* I2C                                                                        */
/* ---------------------------------------------------------------------------*/
#define I2C_SLAVE_ADR  0x50
#define I2C_REQ_NUM    16

// CMD_ID
#define VAILD_CMD_ID_NUM  26  // 有効CMD ID数

#define CMD_ID_SP  0    // 各種閾値設定用 (SET PARAMETER)
#define CMD_ID_RP  1    // 各種閾値初期値設定 (RESET PARAMETER)
#define CMD_ID_SE  2    // ERP 設定 (SET ERP)
#define CMD_ID_SC  3    // 時刻設定 (SET CLOCK)
#define CMD_ID_SS  4    // 製造情報設定 (SET SERIAL)
#define CMD_ID_SL  5    // 寿命計算結果記憶 (SET LIFE)
#define CMD_ID_BC  6    // 寿命診断実行 (BATT CHECK)
#define CMD_ID_CN  7    // 強制充電 (CHARGE ON)
#define CMD_ID_CF  8    // 強制充電停止 (CHARGE OFF)
#define CMD_ID_BE  9    // バックアップ許可 (BACKUP ENABLE)
#define CMD_ID_BF  10   // バックアップ停止 (BACKUP OFF)
#define CMD_ID_OR  11   // 復電リスタート制御 (OUTPUT RESTART)
#define CMD_ID_D0  12   // 全データ取得 (GET DATA0)
#define CMD_ID_D1  13   // 状態情報 (GET DATA1)
#define CMD_ID_D2  14   // 起動時寿命計算用 (GET DATA2)
#define CMD_ID_D3  15   // 通常寿命計算用 (GET DATA3)
#define CMD_ID_D4  16   // 保守情報取得 (GET DATA4)
#define CMD_ID_D5  17   // REV/号機・設定確認 (GET DATA5)
#define CMD_ID_EL  18   // エラーログ取得 (ERROR LOG)
#define CMD_ID_OL  19   // ON/OFF ログ取得 (OPERATE LOG)
#define CMD_ID_CD  20   // データクリア (CLEAR DATA)
#define CMD_ID_CL  21   // ログ全クリア (CLEAR LOG)
#define CMD_ID_FU  22   // FW アップデート (FW UPDATE)
#define CMD_ID_FD  23   // FW データ取得 (FW DATA)
#define CMD_ID_AD  24   // バッテリ電圧補正機能(ADJUST)
#define CMD_ID_AR  25   // バッテリ電圧補正機能_読み出し用 (ADJUST READ)
#define CMD_ID_FF  0xFF // 未定義

// NAK REASON CODE
#define NAK_PARITY   0x30 // パリティエラー
#define NAK_OVERRUN  0x31 // オーバーランエラー
#define NAK_FRAMING  0x32 // フレーミングエラー
#define NAK_BCC      0x33 // BCCエラー
#define NAK_ETX      0x35 // ETX異常
#define NAK_TIMEOUT  0x36 // タイムアウト
#define NAK_FORMAT   0x37 // フォーマットエラー(通信フォーマット異常)
#define NAK_PARAM    0x38 // パラメータエラー(ライブラリ制御命令異常)
#define NAK_PROTECT  0x39 // プロテクトエラー(書込み禁止領域アクセス)
#define NAK_ERASE    0x3A // イレースエラー(ROM異常による削除失敗)
#define NAK_VERIFY   0x3B // ベリファイエラー（ROM異常)
#define NAK_WRITE    0x3C // ライトエラー（ROM異常による書込み失敗)
#define NAK_FLOW     0x3D // フローエラー(ライブラリ制御異常)

// エラーレスポンス
#define ERR_RES_NUM  9  // エラーレスポンスデータ長

#define CMD_NORMAL   0  // 正常レスポンス
#define CMD_ERR_RES  1  // コマンドエラー(CME)レスポンス
#define PME_ERR_RES  2  // パラメータエラー(PME)レスポンス
#define SQE_ERR_RES  3  // シーケンスエラー(SQE)レスポンス
#define HWE_ERR_RES  4  // HW破損エラー(HWE)レスポンス
#define MCM_ERR_RES  5  // 多重コマンド受信(MCM)レスポンス
#define FUE_ERR_RES  6  // FWアップデートエラー(FUE)レスポンス


/* ---------------------------------------------------------------------------*/
/* 状態情報/イベント/エラーログ    操作定義                                   */
/* ---------------------------------------------------------------------------*/
#define FLAG_PS_ON          1   // PS_ON信号オン
#define FLAG_BURST_ON       2   // BURST信号オン
#define FLAG_BURST          3   // BURST有効
#define FLAG_PS_OFF_CHARGE  4   // PS_OFF_CHARGE有効
#define FLAG_RESTART_READY  5   // RESTART待ち状態
#define FLAG_BACKUP_READY   6   // バックアップ可能状態
#define FLAG_CHARGE_READY   7   // 充電待ち受け状態
#define FLAG_BATT_CHECK     8   // BATT CHECKコマンド実行中
#define FLAG_CMD_CHARGE_OFF 9   // CHARGE OFFコマンド実行中
#define FLAG_CMD_CHARGE_ON  10   // CHARGE ONコマンド実行中
#define FLAG_BATT_ON        11   // バックアップ中
#define FLAG_BATT_LOW       12   // バッテリ容量低下
#define FLAG_S_CHARGE_ON    13   // 補充電中
#define FLAG_CHARGE_OK      14   // 充電完了
#define FLAG_CHG_CHARGE_ON  15   // 充電中
                                 // ファン回転数低下検出時
#define FLAG_ADU_TEMP_WNG   16   // ADU部温度警告検出時
#define FLAG_ADU_LIFE_WNG   17   // 電源寿命警告検出時
#define FLAG_FAN_FAIL       18   // ファン破損検出時
#define FLAG_BBU_TEMP_WNG   19   // BBU温度警告検出時
#define FLAG_BBU_FAIL       20   // BBU破損検出時
#define FLAG_CHG_LV         21   // 充電回路不足電圧検出時
#define FLAG_CHG_OV         22   // 充電回路過電圧検出時
#define FLAG_CHG_OC         23   // 充電回路過電流検出時
#define FLAG_BATT_TEMP_WNG  24   // バッテリ温度警告検出時
#define FLAG_BATT_TEMP_ALM  25   // バッテリ温度異常検出時
#define FLAG_BATT_LV        26   // バッテリ電圧低下時検出時
#define FLAG_BATT_OV        27   // バッテリ過電圧時検出時
#define FLAG_BATT_LIFE      28   // バッテリ寿命検出時
#define FLAG_BATT_MCN       29   // バッテリ誤接続検出時
#define FLAG_BATT_P_FAIL    30   // バッテリ保護回路破損検出時
#define FLAG_BATT_DCN       31   // バッテリ未接続検出時
#define FLAG_12V_OV         32   // 12V過電圧検出時
#define FLAG_12V_LV         33   // 12V不足電圧検出時
#define FLAG_12V_OC         34   // 12V過電流検出時
#define FLAG_12V_OC_OFF     35   // 12V PS_OFF過電流検出時
#define FLAG_BATT_OC        36   // バッテリ放電過電流
#define FLAG_ADU_TEMP_ALM   37   // AC/DC 温度異常
#define FLAG_BBU_TEMP_ALM   38   // BACKUP 温度異常
#define FLAG_FAN_LOW        39   // ファン回転低下
#define FLAG_FAN_HIGH       40   // ファン回転上昇
#define FLAG_FAN_STOP       41   // ファン回転停止
#define FLAG_BBU_SW_ST      42   // FEW_SW ショート
#define FLAG_BBU_SW_OP      43   // FET_SW オープン
#define FLAG_PFC_OV         44   // PFC過電圧検出時
#define FLAG_12V_OC_OFF_H   45   // 12V PS_OFF過電流検出時
#define FLAG_WDT            46   //WDT
#define FLAG_COM_ALM       100   // 通信異常 （各種通信エラーに細分化可能なコードを有する）

/* ---------------------------------------------------------------------------*/
/* オペレートログ    操作定義                                   */
/* ---------------------------------------------------------------------------*/
#define OPE_AC_FAIL        1   // ACFAIL
#define OPE_MIC_POWER_ON   2   // マイコンパワーオン
#define OPE_PS_ON          3   // PS_ON
#define OPE_PS_OFF         4   // PS_OFF
#define OPE_BURST_ON       5   // BURST_ON
#define OPE_BURST_OFF      6   // BURST_OFF
#define OPE_BATT_ON        7   // BATT_ON
#define OPE_BATT_OFF       8   // BATT_OFF
#define OPE_LOWBATT_ON     9   // LOWBATT_ON
#define OPE_LOWBATT_OFF    10   //LOWBATT_OFF
#define OPE_FINAL_VOLTAGE  11   //FINAL_VOLTAGE
/* ---------------------------------------------------------------------------*/
/* 10.4.4 状態情報                                                            */
/* ---------------------------------------------------------------------------*/
#define INFO_SIGNAL_STATUS_BURST_ON         gs_status_info.signal_status.bit.burst_on        // BURST信号オン
#define INFO_SIGNAL_STATUS_PS_ON            gs_status_info.signal_status.bit.ps_on           // PS_ON信号オン
#define INFO_COMMAND_STATUS1_BACKUP_READY   gs_status_info.command_status1.bit.backup_ready  // バックアップ可能状態
#define INFO_COMMAND_STATUS1_RESTART_READY  gs_status_info.command_status1.bit.restart_ready // RESTART待ち状態
#define INFO_COMMAND_STATUS1_PS_OFF_CHARGE  gs_status_info.command_status1.bit.ps_off_charge // PS_OFF_CHARGE有効
#define INFO_COMMAND_STATUS1_BURST          gs_status_info.command_status1.bit.burst         // BURST有効
#define INFO_COMMAND_STATUS2_CHARGE_ON      gs_status_info.command_status2.bit.charge_on     // CHARGE ONコマンド実行中
#define INFO_COMMAND_STATUS2_CHARGE_OFF     gs_status_info.command_status2.bit.charge_off    // CHARGE OFFコマンド実行中
#define INFO_COMMAND_STATUS2_BATT_CHECK     gs_status_info.command_status2.bit.batt_check    // BATT CHECKコマンド実行中
#define INFO_COMMAND_STATUS2_CHARGE_READY   gs_status_info.command_status2.bit.charge_ready  // 充電待ち受け状態
#define INFO_BACKUP_STATUS_BATT_LOW         gs_status_info.backup_status.bit.batt_low        // バッテリ容量低下
#define INFO_BACKUP_STATUS_BATT_ON          gs_status_info.backup_status.bit.batt_on         // バックアップ中
#define INFO_CHARGE_STATUS_CHARGE_ON        gs_status_info.charge_status.bit.charge_on       // 充電中
#define INFO_CHARGE_STATUS_CHARGE_OK        gs_status_info.charge_status.bit.charge_ok       // 充電完了
#define INFO_CHARGE_STATUS_S_CHARGE_ON      gs_status_info.charge_status.bit.s_charge_on     // 補充電中
#define INFO_ADU_WARNING_ADU_TEMP_WNG       gs_status_info.adu_warning.bit.adu_temp_wng      // ADU部温度警告検出時
#define INFO_ADU_WARNING_FAN_WNG            gs_status_info.adu_warning.bit.fan_wng           // ファン回転数低下検出時
#define INFO_ADU_ALM1_FAN_FAIL              gs_status_info.adu_alm1.bit.fan_fail             // ファン破損検出時
#define INFO_ADU_ALM1_PFC_OV                gs_status_info.adu_alm1.bit.pfc_ov               // PFC過電圧検出時
#define INFO_ADU_ALM1_12V_OC_OFF_H          gs_status_info.adu_alm1.bit._12v_oc_off_h          // 8/20 追加
#define INFO_BBU_WARNING_BBU_TEMP_WNG       gs_status_info.bbu_warning.bit.bbu_temp_wng      // BBU温度警告検出時
#define INFO_BBU_ALM_CHG_OC                 gs_status_info.bbu_alm.bit.chg_oc                // 充電回路過電流検出時
#define INFO_BBU_ALM_CHG_OV                 gs_status_info.bbu_alm.bit.chg_ov                // 充電回路過電圧検出時
#define INFO_BBU_ALM_CHG_LV                 gs_status_info.bbu_alm.bit.chg_lv                // 充電回路不足電圧検出時
#define INFO_BBU_ALM_BBU_FAIL               gs_status_info.bbu_alm.bit.bbu_fail              // BBU破損検出時
#define INFO_BATT_WARNING_BATT_TEMP_WNG     gs_status_info.batt_warning.bit.batt_temp_wng    // バッテリ温度警告検出時
#define INFO_BATT_ALM1_BATT_OV              gs_status_info.batt_alm1.bit.batt_ov             // バッテリ過電圧時検出時
#define INFO_BATT_ALM1_BATT_LV              gs_status_info.batt_alm1.bit.batt_lv             // バッテリ電圧低下時検出時
#define INFO_BATT_ALM1_BATT_TEMP_ALM        gs_status_info.batt_alm1.bit.batt_temp_alm       // バッテリ温度異常検出時
#define INFO_BATT_ALM2_BATT_DCN             gs_status_info.batt_alm2.bit.batt_dcn            // バッテリ未接続検出時
#define INFO_BATT_ALM2_BATT_P_FAIL          gs_status_info.batt_alm2.bit.batt_p_fail         // バッテリ保護回路破損検出時
#define INFO_BATT_ALM2_BATT_MCN             gs_status_info.batt_alm2.bit.batt_mcn            // バッテリ誤接続検出時
#define INFO_BATT_ALM2_BATT_LIFE            gs_status_info.batt_alm2.bit.batt_life           // バッテリ寿命検出時
#define INFO_ADU_ALM2_12V_OC_OFF            gs_status_info.adu_alm2.bit._12v_oc_off          // 12V PS_OFF過電流検出時
#define INFO_ADU_ALM2_12V_OC                gs_status_info.adu_alm2.bit._12v_oc              // 12V過電流検出時
#define INFO_ADU_ALM2_12V_LV                gs_status_info.adu_alm2.bit._12v_lv              // 12V不足電圧検出時
#define INFO_ADU_ALM2_12V_OV                gs_status_info.adu_alm2.bit._12v_ov              // 12V過電圧検出時

/* ---------------------------------------------------------------------------*/
/* 6.3.2 イベントデータ                                                       */
/* ---------------------------------------------------------------------------*/
#define EVT_BACKUP_STATUS_BATT_LOW     gs_event_data.backup_status.bit.batt_low         // バッテリ容量低下検出時
#define EVT_BACKUP_STATUS_BATT_ON      gs_event_data.backup_status.bit.batt_on          // バックアップ開始時
#define EVT_CHARGE_STATUS_CHARGE_ON    gs_event_data.charge_status.bit.charge_on        // 充電開始時
#define EVT_CHARGE_STATUS_CHARGE_OK    gs_event_data.charge_status.bit.charge_ok        // 充電完了時
#define EVT_ADU_WARNING_ADU_LIFE_WNG   gs_event_data.adu_warning.bit.adu_life_wng       // 電源寿命警告検出時
#define EVT_ADU_WARNING_ADU_TEMP_WNG   gs_event_data.adu_warning.bit.adu_temp_wng       // 電源温度警告検出時
#define EVT_ADU_WARNING_FAN_WNG        gs_event_data.adu_warning.bit.fan_wng            // ファン回転数低下警告検出時
#define EVT_ADU_ALM_FAN_FAIL           gs_event_data.adu_alm.bit.fan_fail               // ファン破損検出時
#define EVT_ADU_ALM_12V_OC_OFF_H       gs_event_data.adu_alm.bit._12v_oc_off_h               // 8/20
#define EVT_ADU_ALM_PFC_OV             gs_event_data.adu_alm.bit.pfc_ov                 // PFC過電圧検出時
#define EVT_BBU_WARNING_BBU_TEMP_WNG   gs_event_data.bbu_warning.bit.bbu_temp_wng       // BBU温度警告検出時
#define EVT_BBU_ALM_CHG_OC             gs_event_data.bbu_alm.bit.chg_oc                 // 充電回路過電流検出時
#define EVT_BBU_ALM_CHG_OV             gs_event_data.bbu_alm.bit.chg_ov                 // 充電回路過電圧検出時
#define EVT_BBU_ALM_CHG_LV             gs_event_data.bbu_alm.bit.chg_lv                 // 充電回路不足電圧検出時
#define EVT_BBU_ALM_BBU_FAIL           gs_event_data.bbu_alm.bit.bbu_fail               // BBU破損検出時
#define EVT_BATT_WARNING_BATT_TEMP_WNG gs_event_data.batt_warning.bit.batt_temp_wng     // バッテリ温度抑止時
#define EVT_BATT_ALM1_BATT_OV          gs_event_data.batt_alm1.bit.batt_ov              // バッテリ過電圧検出時
#define EVT_BATT_ALM1_BATT_LV          gs_event_data.batt_alm1.bit.batt_lv              // バッテリ電圧低下検出時
#define EVT_BATT_ALM1_BATT_TEMP_ALM    gs_event_data.batt_alm1.bit.batt_temp_alm        // バッテリ温度異常検出時
#define EVT_BATT_ALM2_BATT_DCN         gs_event_data.batt_alm2.bit.batt_dcn             // バッテリ未接続検出時
#define EVT_BATT_ALM2_BATT_P_FAIL      gs_event_data.batt_alm2.bit.batt_p_fail          // バッテリ保護回路破損検出時
#define EVT_BATT_ALM2_BATT_MCN         gs_event_data.batt_alm2.bit.batt_mcn             // バッテリ誤接続検出時
#define EVT_BATT_ALM2_BATT_LIFE        gs_event_data.batt_alm2.bit.batt_life            // バッテリ寿命検出時

/* ---------------------------------------------------------------------------*/
/* 23.6.2 エラーログ                                                          */
/* ---------------------------------------------------------------------------*/
#define EL_BATT_TEMP_WNG 1  // 充電温度抑止
#define EL_BATT_P_FAIL   2  // 保護素子破損
#define EL_BATT_DCN      3  // 未接続
#define EL_BATT_TEMP_ALM 4  // 温度異常
#define EL_BATT_LV       5  // 低電圧
#define EL_BATT_OV       6  // 高電圧
#define EL_BATT_LIFE     7  // 寿命
#define EL_12V_OV        8  // +12V過電圧
#define EL_12V_LV        9  // +12V不足電圧
#define EL_12V_OC        10 // +12V過電流
#define EL_12V_OC_OFF    11 // +12V過電流(PS_OFF時)
#define EL_CHG_OV        12 // 充電回路過電圧
#define EL_CHG_LV        13 // 充電回路不足電圧
#define EL_CHG_OC        14 // 充電回路過電流
#define EL_BATT_OC       15 // バッテリ放電過電流
#define EL_ADU_TEMP_WNG  17 // AC/DC 温度警告
#define EL_BBU_TEMP_WNG  18 // BACKUP 温度警告
#define EL_ADU_TEMP_ALM  19 // AC/DC 温度異常
#define EL_BBU_TEMP_ALM  20 // BACKUP 温度異常
#define EL_ADU_LIFE_WNG  21 // AC/DC 寿命警告
#define EL_FAN_LOW       22 // ファン回転低下
#define EL_FAN_HIGH      23 // ファン回転上昇
#define EL_FAN_STOP      24 // ファン回転停止
#define EL_FAN_FAIL      25 // ファン回転異常
#define EL_PFC_OV        26 // PFC過電圧
#define EL_COM_ALM       27 // 通信異常
#define EL_BATT_MCN      28 // バッテリ誤接続
#define EL_BBU_FAIL      29 // BBU 破損(EEP 破損)
#define EL_BBU_SW_ST     30 // FEW_SW ショート
#define EL_BBU_SW_OP     31 // FET_SW オープン

/* ---------------------------------------------------------------------------*/
#define BATT1_4700MV    4700 // 放電終止 BATT1 4.7V(4700mV)
#define BATT2_5500MV    5500 // 放電終止 BATT1 5.5V(5500mV)

#define BATT_V_8_04V    8040 // BATT_V  8.04V(8040mV)

#define BATT_TEMP_35C   350  // バッテリ温度 35℃

#define DCIR_CHARGE_CURRENT_ERROR   500

/* ---------------------------------------------------------------------------*/
/* 保護閾値                                                                        */
/* ---------------------------------------------------------------------------*/
#define PRO_LOW_V        9800  //不足電圧
#define PRO_HIGH_I_ON    20000 //過電流保護 PS_ON
#define PRO_HIGH_I_OF    2000  //過電流保護 PS_OFF
#define PRO_HIGH_I_OF_H  5000  //過電流保護 PS_OFF(H)
/* S1.14 128F 問題点対策表に記載は無いが過電圧しきい値を13400に変更 */
//#define PRO_HIGH_V       13500 //過電圧保護(+12V出力信号)
#define PRO_HIGH_V       13400 //過電圧保護(+12V出力信号)
#define PRO_HIGH_I_DIS   58500 //過電圧保護(放電中)
#define PRO_HIGH_I_CHG   2600 //過電流保護充電
#define PRO_HIGH_V_CHG   11400 //過電圧保護充電
#define PRO_SHORTAGE1    400   //不足保護
#define PRO_SHORTAGE2    1500   //不足保護
#define PRO_BBU_SHORT    10000   //ショート
#define PRO_BBU_OPEN     10000   //オープン
#define PRO_TEMP_ADU     950   //ADU 温度異常保護
#define PRO_TEMP_BBU     950   //BBU 温度異常保護
#define PRO_PFAIL_V      10200   //素子破損
#define PRO_PFAIL_V2     4000   //素子破損
#define PRO_PFAIL_I      400    //素子破損
#define PRO_PFAIL_CHG_V  4000    //素子破損
#define PRO_PFAIL_CHG_V2  3500    //素子破損
#define PRO_BATT_LOW     6000    //バッテリ低電圧
#define PRO_BATT_HIGH    11000    //バッテリ高電圧


#define BURST_I_OVER     1200
#define BURST_I_SAFE     1000

/* 温度抑止 */
#define TEMP_SUPPRES_0   0     // 温度抑止なし
#define TEMP_SUPPRES_1   1     // 温度抑止あり
#define TEMP_SUPPRES_2   2     // 温度抑止復帰(CHARGE OFFコマンド受信)
#define TEMP_SUPPRES_3   3     // 温度抑止復帰(CHARGE ONコマンドオフ)
#define TEMP_SUPPRES_4   4     // 温度抑止復帰(自動充電無効設定)
#define TEMP_SUPPRES_5   5     // 温度抑止復帰(バッテリ異常検出)
#define TEMP_SUPPRES_6   6     // 温度抑止復帰(停電によるバックアップ移行時)

#define ADC12V_CALL_BACK     11000
#define SP_BATT_WNG_CLR_THD  41
/* SOC */
/* S1.14 121F対策 SOCは充電中は127%まで表示する。満充電検出時に100%にする */
#define SOC_127P         127   // SOC 127%
#define SOC_100P         100   // SOC 100%
#define SOC_90           90    // SOC 90%
#define SOC_80           80    // SOC 80%
#define SOC_0            0     // SOC 0%

#define INT8_MAX_VALUE             127
#define INT8_MIN_VALUE             -128
#define UINT8_MAX_VALUE            255
#define UINT8_MAX_VALUE_UNDER      254
#define UINT12_F_MAX_VALUE         4095.0
#define UINT12_MAX_VALUE           4095
#define UINT12_MAX_VALUE_UNDER     4094
#define UINT16_MAX_VALUE           65535
#define UINT16_MAX_VALUE_UNDER     65534
#define UINT24_MAX_VALUE_UNDER     16777215
#define UINT24_F__MAX_VALUE_UNDER  16777215.0
#define INT8_ACOFF_TEMP            30
///////////////
#define RAMFUNC \
    __attribute__((section(".TI.ramfunc"))) __attribute__((noinline))

#endif /*_NF55_DEFINE_H_ */
