#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"

eeprom_data_t g_eeprom_data = {0};
eeprom_data_t g_write_eeprom_data = {0}; // EEPROM書込みデータ

uint16_t    gu16_c_timing1ms = 0;
uint16_t    gu16_c_timing1s  = 0;
volatile uint16_t  gu16_f_timing    = 0;
volatile uint16_t  gu16_f_timing_1sec = 0;
volatile uint32_t  gu32_SysTickCount = 0;

#ifdef _DEBUG_ON_
uint8_t     INPUT_DEBUG[7] = {0};
#endif

uint16_t    gu16_CheckADC0 = 0;
uint16_t    gu16_CheckADC1 = 0;

uint16_t    gu16_ADC_cnt_4  = 0;
uint16_t    gu16_ADC_cnt_10 = 0;  /* S1.14 128F対策 */
uint16_t    gu16_ADC_cnt_50 = 0;
uint16_t    gu16_ADC0_Result[7][50] = {0};
uint16_t    gu16_ADC1_Result[7][50] = {0};
uint16_t    gu16_ADC0_Sens[7] = {0};
uint16_t    gu16_ADC1_Sens[7] = {0};
uint16_t    gu16_ADC0_5_10[10] = {0};  /* S1.14 128F対策 */

uint8_t  gu8_f_batt_not_con=2;
uint16_t gu16_c_batt_not_con=0;

uint16_t gu16_c_batt_con=0;

struct _Filter pi_ps_on        = { 0, 0, TIMER_10ms,   TIMER_10ms,  0, _TRG_NONE_ };
struct _Filter pi_burst_on     = { 0, 0, TIMER_2ms,   TIMER_2ms,  0, _TRG_NONE_ };
struct _Filter pi_dischg12_ovp = { 0, 0, TIMER_6ms,   TIMER_6ms,  0, _TRG_NONE_ };
struct _Filter pi_pfc_fail_in  = { 0, 0, TIMER_300ms, TIMER_300ms,  0, _TRG_NONE_ };

//struct _Filter pi_ac_on_no_isr = { 0, 0, TIMER_8ms,   0,          0, _TRG_NONE_ };
struct _Filter pi_ac_on_level  = { 0, 0, TIMER_3ms,   TIMER_8ms,  0, _TRG_NONE_ };
struct _Filter pi_aft_ac_on_level  = { 0, 0, TIMER_3ms,   TIMER_8ms,  0, _TRG_NONE_ };

///追加filter///////////////////////////////////////////////

struct _Filter pi_low_v          = {0,0,(TIMER_300ms-TIMER_4ms),   TIMER_10ms, 0, _TRG_NONE_};//
struct _Filter pi_high_i_of       = {0,0,TIMER_250ms,   TIMER_250ms, 0, _TRG_NONE_};
struct _Filter pi_high_i_of_h       = {0,0,TIMER_250ms, TIMER_250ms, 0, _TRG_NONE_};

struct _Filter pi_high_i_on       = {0,0,TIMER_10ms,   TIMER_10ms, 0, _TRG_NONE_};
struct _Filter pi_high_i_on_50ms   = {0,0,TIMER_1ms,   TIMER_1ms, 0, _TRG_NONE_};
struct _Filter pi_high_i_on_10ms   = {0,0,TIMER_1ms,   TIMER_1ms, 0, _TRG_NONE_};  /* S1.14 128F */

struct _Filter pi_high_v         = {0,0,TIMER_2ms,   TIMER_2ms, 0, _TRG_NONE_};
struct _Filter pi_high_i_dis_6   = {0,0,TIMER_1ms, TIMER_1ms, 0, _TRG_NONE_};
             //
struct _Filter pi_high_i_cha     = {0,0,TIMER_1ms,   TIMER_1ms, 0, _TRG_NONE_};
struct _Filter pi_high_v_cha_6   = {0,0,TIMER_4ms,   TIMER_4ms, 0, _TRG_NONE_};

struct _Filter pi_low_v_shortage  = {0,0,TIMER_250ms,   TIMER_250ms, 0, _TRG_NONE_}; //
struct _Filter pi_low_v_shortage_5a = {0,0,TIMER_250ms,   TIMER_250ms, 0, _TRG_NONE_};
struct _Filter pi_bbu_sw_short   = {0,0,(TIMER_300ms-TIMER_4ms),   (TIMER_300ms-TIMER_4ms), 0, _TRG_NONE_};  //
struct _Filter pi_bbu_sw_open    = {0,0,(TIMER_300ms-TIMER_4ms),   (TIMER_300ms-TIMER_4ms), 0, _TRG_NONE_};  //
struct _Filter pi_fan_fail_adu   = {0,0,(TIMER_300ms-TIMER_4ms),   (TIMER_300ms-TIMER_4ms), 0, _TRG_NONE_};                 //
struct _Filter pi_fan_fail_bbu   = {0,0,(TIMER_300ms-TIMER_4ms),   (TIMER_300ms-TIMER_4ms), 0, _TRG_NONE_};
struct _Filter pi_fail_bbu       = {0,0,(TIMER_300ms-TIMER_4ms),   (TIMER_300ms-TIMER_4ms), 0, _TRG_NONE_};
struct _Filter pi_temp_fail_adu  = {0,0,(TIMER_50ms-TIMER_4ms),   (TIMER_50ms-TIMER_4ms), 0, _TRG_NONE_};    //
struct _Filter pi_temp_fail_bbu  = {0,0,(TIMER_50ms-TIMER_4ms),   (TIMER_50ms-TIMER_4ms), 0, _TRG_NONE_};
struct _Filter pi_batt_temp_aft   = {0,0,(TIMER_300ms-TIMER_4ms),  (TIMER_300ms-TIMER_4ms), 0, _TRG_NONE_};   //
struct _Filter pi_batt_temp_bef   = {0,0,(TIMER_300ms-TIMER_4ms),  (TIMER_300ms-TIMER_4ms), 0, _TRG_NONE_};
struct _Filter pi_batt_break     = {0,0,TIMER_250ms,   TIMER_250ms, 0, _TRG_NONE_};  //
struct _Filter pi_batt_break_chg = {0,0,TIMER_250ms,   TIMER_250ms, 0, _TRG_NONE_};
struct _Filter pi_batt_not       = {0,0,TIMER_1ms,   TIMER_1ms, 0, _TRG_NONE_};
struct _Filter pi_latch_fail     = {0,0,(TIMER_50ms-TIMER_4ms),   (TIMER_50ms-TIMER_4ms), 0, _TRG_NONE_};
struct _Filter pi_batt_low_6     = {0,0,TIMER_250ms,   TIMER_250ms, 0, _TRG_NONE_};

struct _Filter pi_batt_high_6    = {0,0,TIMER_250ms,   TIMER_250ms, 0, _TRG_NONE_};  //

struct _Filter pi_fan_low_protection   = { 0, 0, TIMER_30s,  TIMER_10ms, 0, _TRG_NONE_ };
struct _Filter pi_fan_high_protection  = { 0, 0, TIMER_30s,  TIMER_10ms, 0, _TRG_NONE_ };
struct _Filter pi_fan_stop_protection  = { 0, 0, TIMER_10s,  TIMER_10ms, 0, _TRG_NONE_ };

///////////////////////////////
uint8_t     gu8_f_over_v = 0;
uint8_t     gu8_f_over_i_on = 0;
uint8_t     gu8_f_over_chg=0;
uint8_t     gu8_f_sw_short=0;
uint8_t     gu8_f_pfc_err=0;
uint8_t     gu8_f_tmp_fail_adu=0;
uint8_t     gu8_f_tmp_fail_bbu=0;
uint8_t     gu8_f_tmp_wng_batt=0;

////////////////////////////////////////////////////////////
struct _Filter pi_burst_i_over   = {0,0,(TIMER_300ms+TIMER_50ms),   (TIMER_300ms+TIMER_50ms), 0, _TRG_NONE_};
struct _Filter pi_burst_i_good    = {0,0,(TIMER_300ms+TIMER_50ms),   TIMER_10ms, 0, _TRG_NONE_};
struct _Filter pi_batt_con       ={0,0,TIMER_300ms,   TIMER_300ms, _NOT_ , _TRG_NONE_};

uint16_t    gu16_c_proc_delay = 0;
uint8_t     gu8_f_proc_start = 0;

uint8_t     gu8_f_ps_on = _OFF_;
uint8_t     gu8_f_burst_on = _OFF_;
uint8_t     gu8_f_dischg12_ovp = _OFF_;
uint8_t     gu8_f_pfc_fail_in = _OFF_;

uint8_t     gu8_batt_connect = _BATT_NOT_CONNECT_;

uint16_t    gu16_d_fan_rpm = 0;
uint16_t    gu16_d_fan_rpm_old = 0;
uint8_t     gu8_f_odrRPM = 0;

///追加分///////////////////////////////////////////////
uint8_t     gu8_f_low_v         = _OFF_;
uint8_t     gu8_f_high_i_of      = _OFF_;
uint8_t     gu8_f_high_i_of_h    = _OFF_;
uint8_t     gu8_f_high_i_on      = _OFF_;
uint8_t     gu8_f_high_i_on_50ms = _OFF_;
uint8_t     gu8_f_high_i_on_10ms = _OFF_;  /* S1.14 128F対策 */
uint8_t     gu8_f_high_v        = _OFF_;
uint8_t     gu8_f_high_i_dis_6  = _OFF_;
uint8_t     gu8_f_high_i_cha    = _OFF_;
uint8_t     gu8_f_high_v_cha_6  = _OFF_;
uint8_t     gu8_f_low_v_shortage  = _OFF_;
uint8_t     gu8_f_low_v_shortage_5a = _OFF_;
uint8_t     gu8_f_bbu_sw_short  = _OFF_;
uint8_t     gu8_f_bbu_sw_open   = _OFF_;
uint8_t     gu8_f_fan_fail_adu    = _OFF_;
uint8_t     gu8_f_fan_fail_bbu    = _OFF_;
uint8_t     gu8_f_fail_bbu        = _OFF_;
uint8_t     gu8_f_temp_fail_adu   = _OFF_;
uint8_t     gu8_f_temp_fail_bbu   = _OFF_;
uint8_t     gu8batt_temp_st       = _OFF_;
uint8_t     gu8_f_batt_temp_aft =   _OFF_;
uint8_t     gu8_f_batt_temp_bef =   _OFF_;
uint8_t     gu8_f_batt_break      = _OFF_;
uint8_t     gu8_f_batt_break_chg  = _OFF_;
uint16_t    gu16_batt_break_chg_timer=0;
uint8_t     gu8_f_batt_not        = _OFF_;
uint8_t     gu8_f_latch_fail      = _OFF_;
uint8_t     gu8_f_batt_low_6      = _OFF_;
uint8_t     gu8_f_batt_high_6     = _OFF_;

uint8_t     gu8_f_stop_cha= _OFF_;        //充電停止フラグ
uint8_t     gu8_f_susp_cha= TEMP_SUPPRES_0;//充電中断フラグ 温度抑止用
uint8_t     gu8_f_not_batt= _OFF_;        //バッテリ未接続時フラグ

uint32_t    gu32_c_opencheck_time=0;
uint8_t     gu8_f_opencheck=0;

uint8_t     gu8_f_ac_off_detected=0;

/////////////////////////////////////////////////////
uint8_t     gu8_f_skip_reason=0;

uint8_t     gu_f_burst_i_over=_OFF_;
uint8_t     gu_f_burst_i_good=_OFF_;
int16_t     gi16_ad_llc_temp = 0;
int16_t     gi16_ad_bbu_temp = 0;
int16_t     gi16_ad_batt1_temp = 0;
int16_t     gi16_ad_battery_temp = 0;

uint8_t     gu8_f_batt_connect = _UNKNOWN_CONNECT_;
uint8_t     gu8_f_batt_connect_trg = _TRG_NONE_;

uint32_t    gu32_c_ac_on_period = 0;
uint32_t    gu32_c_ac_off_period = 0;
uint8_t     gu8_f_ac_on = _OFF_;
uint8_t     gu8_f_ac_on_1ms = _OFF_;
uint8_t     gu8_f_aft_ac_on= _OFF_;

uint16_t    gu16_c_ac_on_flt = 0;
uint8_t     gu8_f_ac_on_trg = _TRG_NONE_;

uint8_t     gu8_f_ac_interrupt_1s = _OFF_;
uint8_t     gu8_f_ac_70v_ac_interrupt= _OFF_;
uint8_t     gu8_f_ac_under_70v = _OFF_;
uint32_t    gu32_c_ac_interrupt_protection = 0;

uint8_t     gu8_f_rtc_1sec = 0;
DL_RTC_Calendar gs_RTCCalendar;

uint8_t     gu8_f_ps_on_out = _OUT_NOT_;
uint32_t    gu32_c_ps_on_out_delay = 0;
uint8_t     gu8_f_burst_out = _OUT_NOT_;
uint32_t    gu32_c_burst_out_delay = 0;
uint8_t     gu8_f_12v_en_out = _OUT_NOT_;
uint32_t    gu32_c_12v_en_out_delay = 0;
uint8_t     gu8_f_batt_en_out = _OUT_NOT_;
uint32_t    gu32_c_batt_en_out_delay = 0;
uint8_t     gu8_f_chgv_114v_out = _OUT_NOT_;
uint32_t    gu32_c_chgv_114v_out_delay = 0;
uint8_t     gu8_f_dischg12v_en_out = _OUT_NOT_;
uint32_t    gu32_c_dischg12v_en_out_delay = 0;
uint8_t     gu8_f_batchg_en_out = _OUT_NOT_;
uint32_t    gu32_c_batchg_en_out_delay = 0;
uint8_t     gu8_f_vcc_12v_en_out = _OUT_NOT_;
uint32_t    gu32_c_vcc_12v_en_out_delay = 0;
uint8_t     gu8_f_test_out = _OUT_NOT_;
uint32_t    gu32_c_test_out_delay = 0;

uint8_t     gu8_f_backup_active = 0;
uint8_t     gu8_f_charge_output = 0;
uint8_t     gu8_f_dischg_term = 0;
uint8_t     gu8_c_dischg_term = 0;
uint8_t     gu8_backup_enable_cmd = 0;
uint8_t     gu8_backup_off_cmd = 0;
uint8_t     gu8_f_susp_dischg = 0;
uint8_t     gu8_f_stop_dischg = 0;

uint8_t     gu8_f_stop_condition=0;
uint8_t     gu8_f_first_check = _ON_;
uint8_t     gu8_f_initial_skip = _OFF_;

uint8_t     gu8_f_charging_active = 0;
uint8_t     gu8_f_charge_on_cmd = 0;    // 受け取ったコマンド
uint8_t     gu8_f_charge_on = 0;    // データ
uint8_t     gu8_f_charge_off_cmd = 0;    // 受け取ったコマンド
uint8_t     gu8_f_charge_off = 0;    // データ
uint8_t     gu8_f_full_charge = 0;
uint32_t    gu32_c_minus_dv_disable = 0;                    // 充電開始後、-ΔV検出を行わない期間カウンタ
uint8_t     gu8_f_charge_inhibited = 0;    // 充電禁止中フラグ(0:充電可能 1:充電禁止中)
uint8_t     gu8_f_main_chg_now = 0;     // 主充電中フラグ
uint8_t     gu8_f_suppr_chg_now = 0;      //温度抑止中フラグ
uint8_t     gu8_f_charge_cmd_mode = 0;      // 今回の充電が強制充電コマンドによるものであることを通知するフラグ

uint8_t     gu8_f_dcir_check_doing = 0;    // DCIR測定中フラグ
life_diag_data_response_t gs_life_diag_data_response = {0}; // 寿命診断データ(BCコマンドレスポンス用)
uint8_t     gu8_f_dcir_proc_init = 0;
uint8_t     gu8_f_dcir_request = 0;     // DCIRリクエストフラグ(0:リクエストなし 1:リクエストあり)
uint8_t     gu8_f_dcir_complete = 0;    // DCIR完了フラグ(0:未完了 1:完了)

int8_t      gi8_d_soc_wh = 0;     // SOC(Wh)
int8_t      gi8_d_soc_mah = 0;    // SOC(mAh)

uint8_t     gu8_f_ac_link = 0;
uint8_t     gu8_f_ac_link_restarting = 0;
uint8_t     gu8_f_output_restart = 0;
uint32_t    gu32_c_ac_link_timer = 0;

uint8_t     gu8_f_full_charge_dcir = 0; // 満充電(DCIR用)
uint32_t    gu32_c_dcir_timer  = 0;     // DCIR用タイマ
uint8_t     gu8_f_dischg_under_1s = 0;  // 放電1秒未満
uint8_t     gu8_f_dischg_up_1s = 0;     // 放電1秒以上

uint8_t     gu8_f_converter_pwm = _OUT_NOT_;
uint32_t    gu32_c_converter_pwm_delay = 0;
uint8_t     gu8_f_fan_pwm = _OUT_NOT_;
uint32_t    gu32_c_fan_pwm_delay = 0;

float       gf_dischg_i_coeff  = 0.0;
float       gf_batt_v_coeff    = 0.0;
float       gf_acdc12v_v_coeff = 0.0;
float       gf_batt_chg_coeff  = 0.0;
float       gf_12vout_i_coeff  = 0.0;
float       gf_12vout_v_coeff  = 0.0;

/* S1.14 123F対策 補正の計算式を修正 */
float       gf_dischg_i_coeff_ad2  = 0.0;
float       gf_dischg_i_coeff_po2  = 0.0;
float       gf_batt_v_coeff_ad2   = 0.0;
float       gf_batt_v_coeff_po2   = 0.0;
float       gf_acdc12v_v_coeff_ad2 = 0.0;
float       gf_acdc12v_v_coeff_po2 = 0.0;
float       gf_batt_chg_coeff_ad2  = 0.0;
float       gf_batt_chg_coeff_po2  = 0.0;
float       gf_12vout_v_coeff_ad2  = 0.0;
float       gf_12vout_v_coeff_po2  = 0.0;

uint16_t    gu16_ad_dischg_i  = 0;
uint16_t    gu16_ad_batt_v    = 0;
uint16_t    gu16_ad_acdc12v_v = 0;
uint16_t    gu16_ad_batt_chg  = 0;
uint16_t    gu16_val_12vout_i  = 0;    /* S1.14 128F対策 */
uint16_t    gu16_val_12vout_i_50 = 0;  /* S1.14 128F対策 */
uint16_t    gu16_val_12vout_i_10 = 0;  /* S1.14 128F対策 */

uint16_t    gu16_ad_12vout_v  = 0;

uint8_t     gu8_uart_main_receivedata[UART_RCV_MAIN_NUM];
uint8_t     gu8_uart_main_rcv_wpt = 0;
uint8_t     gu8_uart_main_rcv_rpt = 0;

uint8_t     gu8_rcv_main_stage = 0;
uint32_t    gu32_rcv_all_timer = 0;
uint8_t     gu8_rx_proc_stage  = 0;

uint8_t     gu8_d_uart_sendbuf[UART_REQ_NUM][SENDBUF_SIZE];
uint8_t     gu8_d_uart_recvbuf[UART_RCV_NUM][RECVBUF_SIZE];
uint8_t     gu8_d_uart_rcv_count[UART_RCV_NUM];
uint8_t     gu8_d_uart_rcv_wpt = 0;
uint8_t     gu8_d_uart_rcv_rpt = 0;
uint8_t     gu8_d_uart_datalen = 0;
uint8_t     gu8_d_uart_rcv_num = 0;
uint16_t    gu16_c_tx = 0;
uint8_t     gu8_d_uart_snd_wpt = 0;
uint8_t     gu8_d_uart_snd_rpt = 0;
uint16_t    gu16_tx_send_req[UART_REQ_NUM][2] = {0};
uint8_t     gu8_d_sendbuf[SENDBUF_SIZE];
uint8_t     gu8_d_recvbuf[RECVBUF_SIZE];
uint8_t     gu8_f_cmd_id_no[UART_RCV_NUM];
uint8_t     gu8_f_ack_nak_rcv = 0;
uint8_t     gu8_f_evt_ack_nak_rcv = 0;
uint8_t     gu8_f_nak_sndreq = 0;
uint8_t     gu8_proc_stage = 0;
uint8_t     gu8_pos = 0;
uint8_t     gu8_f_multi_command = 0;
uint8_t     gu8_f_command_proc = 0;       // 受信コマンド処理中フラグ
uint8_t     gu8_d_clock_data[6] = {0};

uint8_t     gu8_b_err_log[47]={0};      //エラーログフラグ


uint8_t     gu8_f_cmd_sc_recv = 0;        // 時刻設定(SET CLOCK)受信フラグ
uint32_t    gu32_c_cmd_sc_evt_delay = 0;   // 時刻設定(SET CLOCK)受信後 イベントDelayタイマ
uint8_t     gu8_f_cmd_d1_recv = 0;        // 状態情報(GET DATA1)受信フラグ
uint8_t     gu8_f_event_lost = _EVENT_LOST_OK_;

uint8_t     gu8_f_ac_interrupt_check = 0;
uint8_t     gu8_f_ac_interrupt_detect = 0;
uint32_t    gu32_ac_interrupt_timer = 0;

set_parameter_t gs_set_parameter_tmp; // SET PARAMETERの値の一時保存
set_parameter_t gs_set_parameter;     // SET PARAMETERの値

enum I2cControllerStatus gI2cControllerStatus;
uint8_t     gTxPacket[20];
uint8_t     gRxPacket[16];
uint32_t    gTxLen, gTxCount;
uint32_t    gRxLen, gRxCount;
uint16_t    eeprom_write_req[I2C_REQ_NUM][4] = {0};
uint16_t    eeprom_req_cnt = 0;
uint8_t     eeprom_req_busy = 0;
uint8_t     eeprom_req_write_idx = 0;
uint8_t     eeprom_req_read_idx = 0;
uint8_t     gu8_f_eeprom_check_error = 0;

realtime_data_t    gs_realtime_data = {0};    // リアルタイムデータ
life_calc_data_t gs_life_calc_data = {0}; // 寿命計算データ
life_diag_data_t gs_life_diag_data = {0}; // 寿命診断データ


status_info_t gs_status_info ={0}; // 状態情報
event_data_t  gs_event_data  ={0}; // イベントデータ
event_data_t  gs_event_data_new ={0}; // イベントデータ
event_data_t  gs_event_data_old ={0}; // イベントデータ
event_data_t  gs_event_data_change  ={0}; // イベントデータ

realtime_data_t    realtime_data = {0};    // リアルタイムデータ
life_calc_data_t life_calc_data = {0}; // 寿命計算データ
life_diag_data_t life_diag_data = {0}; // 寿命診断データ

// 保護
uint8_t     gu8_alm_type_12v_err = 0;
uint8_t     gu8_alm_type_dischg_err = 0;
uint8_t     gu8_alm_type_chg_err = 0;
uint8_t     gu8_alm_type_temp_err = 0;
uint8_t     gu8_alm_type_pfc_err = 0;
uint8_t     gu8_alm_type_batt_err = 0;
uint8_t     gu8_alm_type_fan_err = 0;
uint8_t     gu8_f_backup_active_alm = 0;
uint8_t     gu8_f_12v_oc_off = 0;
uint8_t     gu8_f_12v_oc_off_h = 0;
uint32_t    gu32_c_fan_fail_timer = 0;
uint32_t    gu32_c_fan_fail_stop_timer = 0;
uint8_t     gu8_f_fan_fail_stop = 0;
uint8_t     gu8_f_fan_fail_check = 0;

uint8_t     gu8_f_batt_err_startup_exist = 0;
uint8_t     gu8_f_wdt_err=0;
uint32_t    gu32_c_low_v_shortage = 0;

uint16_t    gu16_ad_12vout_i_now_ad=0;
uint16_t    gu16_ad_12vout_v_now_ad=0;
uint16_t    gu16_ad_chgout_v_now_ad=0;

// FAN制御用(PWM)
uint8_t     gu8_fan_output_stg = 0;     // FAN出力処理ステージ
uint16_t    gu16_fan_pwm_freq = 0;      // FAN周波数
uint16_t    gu16_fan_now_pwm_duty = 0;  // FAN_Duty現在設定値(変更前設定値)
uint16_t    gu16_fan_new_pwm_duty = 0;  // FAN_Duty新設定値

uint32_t    gu32_PWM_FREQ = 0;
uint32_t    gu32_PWM_DUTY = 0;
float       gf_pwm_target_bias = 0.0;   // FAN出力変更時の小刻み差分
float       gf_pwm_bias_add_duty = 0.0; // FAN出力変更時の小刻み差分を足している途中のDuty(0.1倍対応のためfloat)
uint8_t     f_gu8_pwm_target_updwn = 0; // FAN出力変更時のDuty比Up/Down記憶フラグ
uint16_t    c_gu16_pwm_upd_period = 0;  // FAN出力変更時の小刻み変更の周期カウンタ
uint16_t    c_gu16_pwm_upd_comp = 0;    // FAN出力変更時の小刻み変更の完了チェック用カウンタ]
#ifdef _DEBUG_ON_
uint8_t     gu8_his_flg = 0;
#endif
int16_t     gi16_ctl_target_temp = 0;   // FAN_温度制御_対象選択用
int16_t     gi16_pre_temp = 0;          // FAN_温度制御_前回温度
uint8_t     f_gu8_fan_temp_updwn = 0;   // FAN_温度制御_前回からの温度変化の向き
uint16_t    gu16_fan_odr_duty = 0;      // FAN_指令Duty比(%)
uint16_t    gu16_fan_odr_rpm = 0;       // FAN_指令rpm
uint16_t    gu16_fan_correction_duty = 0;    // FAN_補正込みDuty比(%)
uint16_t    c_gu16_fan_temp_ctl = 0;    // FAN_温度制御_インターバル用カウンタ
uint16_t    c_gu16_duty_set = 0;        // FAN出力処理ステージ_インターバル用カウンタ
uint8_t     f_gu8_fan_duty_change = 0;  // FAN出力Duty変更ありフラグ

uint8_t     f_gu8_fan_speed_def = 0;    // FAN_デフォルト回転モード
uint8_t     f_gu8_fan_speed = 0;        // FAN_現在の回転モード(温度制御用)
uint8_t     f_gu8_fan_ctl_mode = 0;     // FAN制御_デフォルト回転モードor温度制御モード

uint32_t    gu32_b_fanrpm[256] = {0};
uint16_t    gu16_p_fanrpm = 0;

uint8_t     gu8_f_wng_fan_low = 0;      // FAN回転低下警告通知フラグ
uint8_t     gu8_f_wng_fan_high = 0;     // FAN回転上昇警告通知フラグ
uint8_t     gu8_f_wng_fan_low_protection = 0; // FAN回転低下警告通知フラグ(保護)
uint8_t     gu8_f_wng_fan_high_protection = 0;// FAN回転上昇警告通知フラグ(保護)
uint8_t     gu8_f_wng_fan_stop_protection = 0;// FAN回転停止警告通知フラグ(保護)
uint8_t     gu8_f_fan_fail = 0;         // FAN異常通知フラグ

// 積算データ
uint8_t gu8_f_backup_start_sek = 0;       // バックアップ開始通知フラグ(積算データ用:バックアップ回数)
uint8_t gu8_f_sl_cmd_rcv_sek = 0;         // SLコマンド受信通知フラグ(積算データ用:バッテリ劣化度)
uint8_t gu8_f_dischg_start_sek = 0;       // 放電開始通知フラグ(積算データ用:バッテリ総放電回数)
uint8_t gu8_f_full_chg_sek = 0;           // 満充電検出通知フラグ(積算データ用:バッテリ総充電回数)
uint8_t gu8_f_soc_calc_finish_sek = 0;    // SOC計算終了通知フラグ(積算データ用:バッテリ総放電量/バッテリ総充電量(1:充電中 2:放電中))
float gf_dischg_mah_val_sek = 0.0;        // バッテリ放電量
float gf_chg_mah_val_sek = 0.0;           // バッテリ充電量

uint32_t gu32_c_adu_temp_sek = 0;        // 電源内部積算温度タイマー(1h)
uint32_t gu32_c_adu_action_time = 0;     // 電源稼働時間タイマー(1h)
uint32_t gu32_c_bat_connect_time = 0;    // バッテリ接続時間タイマー(1h)
uint32_t gu32_c_bat_temp_ave_sek = 0;    // バッテリ積算温度/平均温度タイマー(1h)
uint8_t gu8_c_batt_temp_reference_ok = 0;    // バッテリ温度フィルター処理が終了するまで待機するためのタイマー(4ms)
 // サブタイマー群
uint16_t gu16_c_bat_temp_calc = 0;    // バッテリ温度平均算出用タイマー(1m)
 // データ群
//uint16_t gu16_bat_temp_1h_sum = 0;           // バッテリ温度算出用合計値(※最大で、1minごと合計60データとして変数型を想定)
int16_t gi16_bat_temp_1h_sum = 0;           /* S1.14 150F対策 */
uint8_t gu8_c_bat_temp_1h_sum_sample = 0;    // バッテリ温度算出用合計値_サンプル数
 // フラグ群
uint8_t gu8_f_ac_70v_ac_interrupt_on_trg = 0;    // AC70V瞬断ONトリガ
uint8_t gu8_f_bef_ac_70v_ac_interrupt = 0;       // 前周期のAC70V瞬断の有無(0:なし 1:あり)

 // クリアデータ
uint8_t gu8_f_power_category_clear = 0;    // 電源カテゴリデータ(積算データ)クリアフラグ
uint8_t gu8_f_batt_cate_clear = 0;      // バッテリカテゴリデータ(積算データ)クリアフラグ
uint8_t gu8_f_cd_cmd_rcv = 0;           // CDコマンド受信フラグ(バッテリ異常解除通知用)
// 充電制御向けクリアデータフラグ
uint8_t gu8_f_charge_ok_clear = 0;      // CHARGE_OK クリアコマンド(充電開始用)

uint8_t gu8_f_batt_life_over_threshold = 0;    // DCIR寿命診断_閾値越えフラグ(閾値以下:0 閾値より上：1)

// バッテリ電圧値補正機能
uint8_t gu8_cmd_ad_type = 0;            // 補正対象種類(1:dischg_i 2:batt_v 3:acdc12v_v 4:batt_chg 5:_12vout_v)
uint8_t gu8_cmd_ad_position = 0;              // 補正位置指定(1:A? 2:B?)
float gf_cmd_ad_val = 0.0;                // ユーザー登録値(電圧,電流)
uint16_t gu16_cmd_ad_set_ad_val = 0;    // E2P登録AD値記憶用
float gf_cmd_ad_after_correction_slope = 0.0;    // 補正後の傾き
float gf_cmd_ad_calculated_value = 0.0;      // AD値-->算出値

// OFF期間データ(otd:off time data)
uint8_t gu8_f_otd_old_set_clk_cmd = 0;          // SET_CLOCKコマンド前回値
uint8_t gu8_f_otd_ac_off_time_en = 0;           // AC_OFF合計時間Enableフラグ
time_t gt_otd_ac_off_occurrence = 0;                // AC_OFF直前時間（を1900年からの秒数に変換した値）
time_t gt_otd_ac_on_time = 0;                   // AC_ON発生時間（を1900年からの秒数に変換した値）
int16_t gi16_otd_ps_off_bat_temp_ave = 0;       // PS_OFF中のバッテリ平均温度算出用SUM値保存変数(uint16_tで足りるだろう(32768/6/10=546.13℃)) ※/10は単位変換:0.1℃-->1℃
int16_t gi16_otd_chg_bat_temp_ave = 0;          // 充電中のバッテリ平均温度算出用SUM値保存変数(uint16_tで足りるだろう(32768/6/10=546.13℃)) ※/10は単位変換:0.1℃-->1℃
uint8_t gu8_f_otd_chg_soc_calc_fin = 0;         // OFF期間データ用、充電量SOC計算完了フラグ
float gf_otd_chg_soc_now = 0.0;                 // OFF期間データ用、充電量保存変数(mAh)
float gf_otd_chg_soc_total = 0.0;               // OFF期間データ用、トータル充電量(mAh)
uint8_t gu8_f_otd_batt_deg_set = 0;             // OFF期間データ用、バッテリ劣化度更新フラグ
uint16_t gu16_c_otd_ps_off_bat_temp_ave = 0;    // PS_OFF中のバッテリ平均温度算出用SUM値サンプリング周期カウンタ(max1分:60000)
uint16_t gu16_c_otd_chg_bat_temp_ave = 0;       // 充電中のバッテリ平均温度算出用SUM値サンプリング周期カウンタ(max1分:60000)

// 寿命計算データ(jcd:jyumyo calc data)
uint8_t gu8_f_jcd_chg_soc_calc_fin = 0;    // 寿命計算データ用充電量計算完了フラグ
float gf_jcd_ttl_chg_soc = 0;              // 寿命計算データ用総充電量保存変数
float gf_jcd_chg_soc_now = 0;              // 寿命計算データ用今回充電量保存変数

// GET DATA2
uint8_t gu8_f_off_time_data_clear_en = 0;    // OFF期間データクリア有効フラグ


uint32_t gu32_c_soc_timer_1s = 0;
uint32_t gu32_c_soc_timer_1h = 0;
uint8_t  gu8_flag_old = 0;
uint8_t  gu8_status_old = 0;
uint8_t  gu8_eeprom_write_stage = 0;;
uint8_t  gu8_eeprom_read_all_stage = 0;
uint8_t  gu8_eeprom_all_backup = 0;
uint8_t  gu8_f_wng_fan_low_old = 0;
uint8_t  gu8_f_wng_fan_high_old = 0;
uint8_t  gu8_f_wng_fan_stop_old = 0;
uint8_t  gu8_alm_type_batt_err_old = 0;
uint8_t  gu8_f_batt_connect_old = _BATT_NOT_CONNECT_;
uint8_t  gu8_f_ac_on_old = _OFF_;
uint16_t gu16_c_ac_on = 0;
uint16_t gu16_c_aft_ac_on = 0;

uint32_t gu32_c_fan_prm_old = 0;
uint32_t gu32_c_ac_on_old = 0;
uint8_t  gu8_f_rpm = 0;   /* 初回の割込み発生を記憶 */
uint16_t    gu16_c_sta_rpm = 0;
uint8_t     gu8_now_spd = 0;
uint8_t     gu8_new_spd = 0;

uint16_t    gu16_now_rpm = 0;
uint16_t    gu16_now_per = 0;

uint16_t    gu16_new_rpm = 0;
uint16_t    gu16_new_dty = 0;
uint16_t    gu16_new_per = 0;

uint16_t    gu16_max_rpm_5 = 0;
uint16_t    gu16_min_rpm_5 = 0;
uint16_t    gu16_max_rpm_1 = 0;
uint16_t    gu16_min_rpm_1 = 0;

float       gf_max_per = 0;
float       gf_min_per = 0;
float       gf_adj_per = 0;

uint8_t gu8_f_charging_active_old = 0;
uint8_t gu8_f_backup_active_old = 0;
uint8_t gu8_f_fan_spd_backup = 0;
uint8_t gu8_f_fail_adu_bbu = 0;
uint8_t gu8_f_on = 0;
uint16_t gu16_c_fan = 0;

uint8_t gu8_ac_link_stage = 0;

uint8_t gu8_f_response = CMD_NORMAL;

uint8_t gu8_cmd_sp_proc_stage = 0;
uint8_t gu8_cmd_rp_proc_stage = 0;
uint8_t gu8_cmd_se_proc_stage = 0;
uint8_t gu8_cmd_ss_proc_stage = 0;
uint8_t gu8_cmd_sl_proc_stage = 0;
uint8_t gu8_cmd_bc_proc_stage = 0;
uint8_t gu8_cmd_ad_proc_stage = 0;
uint8_t gu8_cmd_sc_proc_stage = 0;

uint8_t gu8_ack_stage = 0;
uint8_t gu8_nak_stage = 0;
uint8_t gu8_tx_send_stage = 0;
uint8_t gu8_evt_proc_stage = 0;

uint8_t gu8_f_envt_first = 1;  // 最初の1回   注意！！

uint8_t gu8_burst_stage = 0;
uint8_t gu8_dischg_ps_on_stage = 0;
uint8_t gu8_dischg_ps_off_stage = 0;
uint8_t gu8_f_ps_on_old = _OFF_;
uint8_t gu8_f_ps_on_backup_old = _DISABLE_;

uint8_t gu8_end_dischg_stage=0;

uint8_t gu8_f_user_select = 0;
uint32_t gu32_c_event_wait = 0;

uint32_t gu32_c_eeprom_timer = 0;

uint8_t gu8_f_before_shutdown=0;

uint8_t gu8_prev_ac_link=_DISABLE_ ;

uint32_t gu32_reset_cause=0;

uint8_t gu8_f_ini_ps_on = 2;

/*******************************/
/* Boot <-> User受け渡しデータ */
/*******************************/
__attribute__((section(".fixed_ram"))) __attribute__((used))
data_info_common_t data_info_common;
