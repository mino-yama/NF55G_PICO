#ifndef _NF55_EEPROM_H_
#define _NF55_EEPROM_H_

/**********************************************
 *   EEPROM配置仕様
 *   NF55G(RW11)_EEPROM_MAP_20260409_new.xlsx
 **********************************************/

// SET PARAMETER
typedef struct {
    uint8_t  ps_on_backup;      // 停電時のバックアップ動作設定
    uint8_t  ac_link;           // 停電後の復電検出におけるリスタート動作設定
    uint8_t  auto_charge;       // 自動充電方式の設定
    uint8_t  event;             // イベント送信設定
    uint8_t  max_backup_time;   // 最大バックアップ時間設定(分)
    uint8_t  min_backup_time;   // 最小バックアップ時間設定(秒)
    uint8_t  restart_time;      // AC_LINKが有効およびOUTPUT RESTARTコマンドを受信時のリスタート実行時に出力をオフする時間
    uint8_t  batt_low_thf;      // バッテリ充電量低下(BATT_LOW)閾値
    uint16_t batt_cap_mah;      // バッテリ容量(mAh単位)
    uint8_t  batt_cap_wh;       // バッテリ容量(Wh単位)
    uint8_t  dummy1;
    uint16_t chg_ir_thd;        // 充電DCIRの判定閾値
    uint8_t  batt_wng_thd;      // バッテリ充電抑止温度閾値
    uint8_t  batt_alm_thd;      // バッテリ温度異常閾値
    uint8_t  adu_temp_thd;      // AC/DC部の温度警告(ADU_TEMP_WNG)の検出閾値
    uint8_t  bbu_temp_thd;      // BACKUP部の温度警告(BBU_TEMP_WNG)の検出閾値
    uint16_t fan_wng_thd;       // FANの回転停止警告(FAN_WMG)の検出閾値
} set_parameter_t;

// SET ERP
typedef struct {
    uint8_t  burst;             // バースト動作制御
    uint8_t  ps_off_charge;     // PS_OFF時の充電制御
} set_erp_t;

// SET SERIAL
typedef struct {
    uint8_t  fw_rev[6];       // FW REVISION
    uint8_t  unit_rev[4];     // ユニットレビジョン
    uint8_t  unit_lot[4];     // ユニット製造ロット
    uint8_t  unit_serial[6];  // ユニット製造号機
    uint8_t  adu_rev[4];      // AC/DC レビジョン
    uint8_t  adu_lot[4];      // AC/DC製造ロット
    uint8_t  adu_serial[6];   // AC/DC製造号機
    uint8_t  bbu_rev[4];      // BACKUP部レビジョン
    uint8_t  bbu_lot[4];      // BACKUP部製造ロット
    uint8_t  bbu_serial[6];   // BACKUP部製造号機     48byte
} set_serial_t;

// SET LIFE
typedef struct {
    uint16_t batt_deg;        // 寿命計算結果
} set_life_t;

// OFF期間データ
typedef struct {
    uint16_t ac_off_hour;         // AC_OFF合計時間[H]
    uint16_t ps_off_hour;         // バッテリのPS_OFF合計時間[H]
    int8_t   ave_off_temp;        // PS_OFF中のバッテリの平均温度
    uint8_t  dummy1;
    uint16_t off_charge_hour;     // バッテリ充電合計時間[H]
    int8_t   ave_charge_temp;     // 充電中のバッテリの平均温度
    uint8_t  dummy2;
    uint16_t off_charge;          // バッテリ総充電量
    uint16_t batt_deg;            // バッテリ劣化度
    // SUB
    uint32_t ac_off_hour_sub;
    uint32_t ps_off_hour_sub;
    uint32_t off_charge_hour_sub;
} off_period_data_t;

// バッテリ容量
typedef struct {
    float    wh;                  // バッテリ容量現在値(Wh)
    float    mah;                 // バッテリ容量現在値(mAh)
} batt_cap_t;

// 積算データ
typedef struct {
    int32_t total_adu_temp;         // 電源内部積算温度
    // SUB
    uint32_t total_adu_hour_sub;
    //
    uint16_t total_adu_hour;        // 電源稼働時間
    uint16_t ac_fail_count;         // 瞬断回数(70V以下)
    uint16_t ac_log_count;          // 瞬断回数(90V以下)
    uint16_t total_backup_count;    // バックアップ回数
    uint16_t batt_deg;              // バッテリ劣化度
    uint16_t total_batt_hour;       // バッテリ接続時間
    uint16_t batt_discharge_count;  // バッテリ総放電回数
    uint16_t batt_charge_count;     // バッテリ総充電回数
    float    batt_ttl_discharge;    // バッテリ総放電量
    float    batt_ttl_charge;       // バッテリ総充電量
    int32_t total_batt_temp;        // バッテリ積算温度
    int8_t   batt_temp_ave;         // バッテリ平均温度
    int8_t   batt_temp_max;         // バッテリ最高温度
    int8_t   batt_temp_min;         // バッテリ最低温度
    uint8_t  dummy1;
    // SUB
    uint32_t total_batt_hour_sub;
    uint32_t batt_temp_sample_count; // バッテリ温度平均算出用サンプル数
} cumulative_data_t;

// ERROR LOG
typedef struct {
    uint8_t  error_log_count;         // ERROR LOG数
    uint8_t  error_log_writepointer;  // ERROR LOG書込ポインタ
} error_log_index_t;

typedef struct {
    uint8_t  year;    // 発生年
    uint8_t  month;   // 発生月
    uint8_t  day;     // 発生日
    uint8_t  hour;    // 発生時
    uint8_t  id;      // ID
} error_log_data_t;

// OPERATE LOG
typedef struct {
    uint8_t  operate_log_count;         // OPERATE LOG数
    uint8_t  operate_log_writepointer;  // OPERATE LOG書込ポインタ
} operate_log_index_t;

typedef struct {
    uint8_t  year;    // 発生年
    uint8_t  month;   // 発生月
    uint8_t  day;     // 発生日
    uint8_t  hour;    // 発生時
    uint8_t  id;      // ID(ON/FFログ)
} operate_log_data_t;

// SET CLOCK
typedef struct {
    uint64_t time;    // 時刻(time_t)
} set_clock_t;

// 補正データ
typedef struct {
    float    point1;  // 補正1位置
    uint16_t ad1;     // 補正1AD値
    uint16_t dummy1;
    float    point2;  // 補正2位置
    uint16_t ad2;     // 補正2AD値
    uint16_t dummy2;
} correct_t;

// EEPROMデータ
//#pragma pack(push,1)
typedef struct {
    set_parameter_t     set_parameter; // 0(20)  SET PARAMETER
    uint8_t             dummy1[12];

    set_erp_t           set_erp;       // 32(2)  SET ERP
    uint8_t             dummy2[14];

    set_serial_t        set_serial;    // 48(48)  SET SERIAL

    batt_cap_t          batt_cap;      // 96(8)   バッテリ容量現在値
    uint8_t             dummy10[8];

    off_period_data_t   off_period_data; // 112(28)  OFF期間データ
    uint8_t             dummy4[4];

    set_clock_t         set_clock;      // 144(8) 時刻データ
    uint8_t             dummy9[8];

    cumulative_data_t      cumulative_data;    // 160(48)  積算データ
    //uint8_t             dummy5[4];

    error_log_index_t   error_log_index;  // 208(2)
    uint8_t             dummy6[14];       // 210

    error_log_data_t    error_log_data[32]; // 224(160)

    operate_log_index_t operate_log_index;  // 384(2)
    uint8_t             dummy7[14];         // 386

    operate_log_data_t  operate_log_data[64]; // 400(320)

    set_life_t          set_life;      // 720(2)  SET LIFE
    uint8_t             dummy3[14];

    uint8_t             dummy8[16]; // 736

    correct_t           dischg_i;  // 752(16)

    correct_t           batt_v;    // 768(16)

    correct_t           acdc12v_v; // 784(16)

    correct_t           batt_chg;  // 800(16)

    correct_t           _12vout_v; // 816(16)

    uint8_t             batt_err;     // 832
    uint8_t             ps_on_sts;    // 833
    uint8_t             dummy13[14];  // 834

    uint8_t             dummy14[8];   // 848
    uint32_t            crc32;        // 856
    uint32_t            pin_code;     // 860
} eeprom_data_t;
//#pragma pack(pop)

#define EEPROM_SP_POS        0       // SET PARAMETER
#define EEPROM_SE_POS        32      // SET ERP
#define EEPROM_SS_POS        48      // SET SERIAL
#define EEPROM_BATT_POS      96      // バッテリ容量現在値(SOC)
#define EEPROM_OFF_DATA_POS  112     // OFF期間データ
#define EEPROM_SC_POS        144     // 時刻データ
#define EEPROM_SEKISAN_POS   160     // 積算データ
#define EEPROM_ERR_IDX_POS   208     // ERROR LOG INDEX
#define EEPROM_ERR_DATA_POS  224     // ERROR LOG DATA
#define EEPROM_OPE_IDX_POS   384     // OPERATE LOG INDEX
#define EEPROM_OPE_DATA_POS  400     // OPERATE LOG DATA
#define EEPROM_SL_POS        720     // SET LIFE
#define EEPROM_DISCHG_I_POS  752     // DISCHG_I 調整
#define EEPROM_BATT_V_POS    768     // BATT_V 調整
#define EEPROM_ACDC12V_V_POS 784     // ACDC12V_V 調整
#define EEPROM_BATT_CHG_POS  800     // BATT_CHG 調整
#define EEPROM_12VOUT_V_POS  816     // 12VOUT_V 調整
#define EEPROM_BATT_ERR_POS  832     // バッテリ異常
#define EEPROM_PS_ON_STS_POS 833     // PS_ON状態
#define EEPROM_CRC_POS       856     // CRC
#define EEPROM_PINCODE_POS   860     // PINCODE

#define EEPROM_VALID_DATA    834    // EEPROM有効データ数(CRC計算範囲)
#define EEPROM_ALL_DATA      864    // EEPROM全データ数

#define ERROR_LOG_COUNT      32     // ERROR LOG数
#define OPERATE_LOG_COUNT    64     // OPERATE LOG数

// SET PARAMETER
#define SP_PS_ON_BACKUP    gs_set_parameter.ps_on_backup      // 停電時のバックアップ動作設定
#define SP_AC_LINK         gs_set_parameter.ac_link           // 停電後の復電検出におけるリスタート動作設定
#define SP_AUTO_CHARGE     gs_set_parameter.auto_charge       // 自動充電方式の設定
#define SP_EVENT           gs_set_parameter.event             // イベント送信設定
#define SP_MAX_BACKUP_TIME gs_set_parameter.max_backup_time   // 最大バックアップ時間設定(分)
#define SP_MIN_BACKUP_TIME gs_set_parameter.min_backup_time   // 最小バックアップ時間設定(秒)
#define SP_RESTART_TIME    gs_set_parameter.restart_time      // AC_LINKが有効およびOUTPUT RESTARTコマンドを受信時のリスタート実行時に出力をオフする時間
#define SP_BATT_LOW_THD    gs_set_parameter.batt_low_thf      // バッテリ充電量低下(BATT_LOW)閾値
#define SP_BATT_CAP_MAH    gs_set_parameter.batt_cap_mah      // バッテリ容量(mAh単位)
#define SP_BATT_CAP_WH     gs_set_parameter.batt_cap_wh       // バッテリ容量(Wh単位)
#define SP_CHG_IR_THD      gs_set_parameter.chg_ir_thd        // 充電DCIRの判定閾値
#define SP_BATT_WNG_THD    gs_set_parameter.batt_wng_thd      // バッテリ充電抑止温度閾値
#define SP_BATT_ALM_THD    gs_set_parameter.batt_alm_thd      // バッテリ温度異常閾値
#define SP_ADU_TEMP_THD    gs_set_parameter.adu_temp_thd      // AC/DC部の温度警告(ADU_TEMP_WNG)の検出閾値
#define SP_BBU_TEMP_THD    gs_set_parameter.bbu_temp_thd      // BACKUP部の温度警告(BBU_TEMP_WNG)の検出閾値
#define SP_FAN_WNG_THD     gs_set_parameter.fan_wng_thd       // FANの回転停止警告(FAN_WMG)の検出閾値

// SET ERP
#define SE_BURST           g_eeprom_data.set_erp.burst                    // バースト動作制御
#define SE_PS_OFF_CHARGE   g_eeprom_data.set_erp.ps_off_charge            // PS_OFF時の充電制御
// SET SERIAL
#define SS_FW_REV      g_eeprom_data.set_serial.fw_rev       // FW REVISION
#define SS_UNIT_REV    g_eeprom_data.set_serial.unit_rev     // ユニットレビジョン
#define SS_UNIT_LOT    g_eeprom_data.set_serial.unit_lot     // ユニット製造ロット
#define SS_UNIT_SERIAL g_eeprom_data.set_serial.unit_serial  // ユニット製造号機
#define SS_ADU_REV     g_eeprom_data.set_serial.adu_rev      // AC/DC レビジョン
#define SS_ADU_LOT     g_eeprom_data.set_serial.adu_lot      // AC/DC製造ロット
#define SS_ADU_SERIAL  g_eeprom_data.set_serial.adu_serial   // AC/DC製造号機
#define SS_BBU_REV     g_eeprom_data.set_serial.bbu_rev      // BACKUP部レビジョン
#define SS_BBU_LOT     g_eeprom_data.set_serial.bbu_lot      // BACKUP部製造ロット
#define SS_BBU_SERIAL  g_eeprom_data.set_serial.bbu_serial   // BACKUP部製造号機
// SET LIFE
#define SL_BATT_DEG    g_eeprom_data.set_life.batt_deg       // 寿命計算結果
// OFF期間データ
#define OFF_AC_OFF_HOUR     g_eeprom_data.off_period_data.ac_off_hour     // AC_OFF合計時間[H]
#define OFF_PS_HOUR         g_eeprom_data.off_period_data.ps_off_hour     // バッテリのPS_OFF合計時間[H]
#define OFF_AVE_OFF_TEMP    g_eeprom_data.off_period_data.ave_off_temp    // PS_OFF中のバッテリの平均温度
#define OFF_OFF_CHARGE_HOUR g_eeprom_data.off_period_data.off_charge_hour // バッテリ充電合計時間[H]
#define OFF_AVE_CHARGE_TEMP g_eeprom_data.off_period_data.ave_charge_temp // 充電中のバッテリの平均温度
#define OFF_OFF_CHARGE      g_eeprom_data.off_period_data.off_charge      // バッテリ総充電量
#define OFF_BATT_DEG        g_eeprom_data.off_period_data.batt_deg        // バッテリ劣化度
// 積算データ
#define SEK_TOTAL_ADU_TEMP  g_eeprom_data.cumulative_data.total_adu_temp            // 電源内部積算温度
#define SEK_TOTAL_ADU_HOUR  g_eeprom_data.cumulative_data.total_adu_hour            // 電源稼働時間
#define SEK_AC_FAIL_COUNT   g_eeprom_data.cumulative_data.ac_fail_count             // 瞬断回数(70V以下)
#define SEK_AC_LOW_COUNT    g_eeprom_data.cumulative_data.ac_log_count              // 瞬断回数(90V以下)
#define SEK_TOTAL_BACKUP_COUNT g_eeprom_data.cumulative_data.total_backup_count     // バックアップ回数
#define SEK_BATT_DEG        g_eeprom_data.cumulative_data.batt_deg                  // バッテリ劣化度
#define SEK_TOTAL_BATT_HOUR g_eeprom_data.cumulative_data.total_batt_hour           // バッテリ接続時間
#define SEK_BATT_DISCHARGE_COUNT g_eeprom_data.cumulative_data.batt_discharge_count // バッテリ総放電回数
#define SEK_BATT_CHARGE_COUNT    g_eeprom_data.cumulative_data.batt_charge_count    // バッテリ総充電回数
#define SEK_BATT_TTL_DISCHARGE   g_eeprom_data.cumulative_data.batt_ttl_discharge   // バッテリ総放電量
#define SEK_BATT_TTL_CHARGE      g_eeprom_data.cumulative_data.batt_ttl_charge      // バッテリ総充電量
#define SEK_TOTAL_BATT_TEMP g_eeprom_data.cumulative_data.total_batt_temp           // バッテリ積算温度
#define SEK_BATT_TEMP_AVE   g_eeprom_data.cumulative_data.batt_temp_ave             // バッテリ平均温度
#define SEK_BATT_TEMP_MAX   g_eeprom_data.cumulative_data.batt_temp_max             // バッテリ最高温度
#define SEK_BATT_TEMP_MIN   g_eeprom_data.cumulative_data.batt_temp_min             // バッテリ最低温度

#endif /* _NF55_EEPROM_H_ */
