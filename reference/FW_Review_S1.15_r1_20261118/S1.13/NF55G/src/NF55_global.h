#ifndef _NF55_GLOBAL_H_
#define _NF55_GLOBAL_H_

#include "NF55_eeprom.h"
#include "NF55_tbl.h"

extern eeprom_data_t g_eeprom_data;
extern eeprom_data_t g_write_eeprom_data; // EEPROM書込みデータ

struct _Filter
{
    uint32_t ON; /* ON  認識カウンタ     */
    uint32_t OF; /* OFF 認識カウンタ     */
    uint32_t ON_time; /* ON  認識時間         */
    uint32_t OF_time; /* OFF 認識時間         */
    uint8_t sts;
    uint8_t trg;
};

extern uint16_t     gu16_c_timing1ms;
extern uint16_t     gu16_c_timing1s;
extern volatile uint16_t  gu16_f_timing;
extern volatile uint16_t  gu16_f_timing_1sec;
extern volatile uint32_t  gu32_SysTickCount;

#ifdef _DEBUG_ON_
extern uint8_t    INPUT_DEBUG[7];
#define I_PS_ON_IN       INPUT_DEBUG[0]   // PA28  PS_ON_IN
#define I_BURST_IN       INPUT_DEBUG[1]   // PA31  BURST_IN
#define I_DISCHG12V_OVP  INPUT_DEBUG[2]   // PA2   DISCHG12V_OVP
#define I_AC_ON_IN       INPUT_DEBUG[3]   // PB3   AC_ON_IN
#define I_PFC_FAIL_IN    INPUT_DEBUG[4]   // PA9   PFC_FAIL_IN
//#define I_FAN_PRM        INPUT_DEBUG[5]   // PB14  FAN_PRM
#define I_FAN_PRM        (DL_GPIO_readPins(GPIO_GRP_B_PORT, GPIO_GRP_B_PB14_INPUT_PIN )!=0)  // PB14  FAN_PRM
#define I_TEST_IN        INPUT_DEBUG[6]   // PA18  TEST_IN
#endif

extern uint16_t     gu16_CheckADC0;
extern uint16_t     gu16_CheckADC1;

extern uint16_t     gu16_ADC_cnt_4;
extern uint16_t     gu16_ADC_cnt_50;
extern uint16_t     gu16_ADC0_Result[7][50];
extern uint16_t     gu16_ADC1_Result[7][50];
extern uint16_t     gu16_ADC0_Sens[7];
extern uint16_t     gu16_ADC1_Sens[7];

extern uint8_t  gu8_f_batt_not_con;
extern uint16_t gu16_c_batt_not_con;
extern uint16_t gu16_c_batt_con;
extern struct _Filter pi_ps_on;
extern struct _Filter pi_burst_on;
extern struct _Filter pi_dischg12_ovp;
extern struct _Filter pi_pfc_fail_in;

//extern struct _Filter pi_ac_on_no_isr;
extern struct _Filter pi_ac_on_level;
extern struct _Filter pi_aft_ac_on_level;
///追加filter///////////////////////////////////////////////
extern struct _Filter pi_low_v;
extern struct _Filter pi_high_i_of;
extern struct _Filter pi_high_i_of_h;
extern struct _Filter pi_high_i_on ;
extern struct _Filter pi_high_i_on_50ms;
extern struct _Filter pi_high_v ;
extern struct _Filter pi_high_i_dis_6 ;
extern struct _Filter pi_high_i_cha;
extern struct _Filter pi_high_v_cha_6 ;
extern struct _Filter pi_low_v_shortage;
extern struct _Filter pi_low_v_shortage_5a;
extern struct _Filter pi_bbu_sw_short;
extern struct _Filter pi_bbu_sw_open;
extern struct _Filter pi_fan_fail_adu;
extern struct _Filter pi_fan_fail_bbu ;
extern struct _Filter pi_fail_bbu;
extern struct _Filter pi_temp_fail_adu;
extern struct _Filter pi_temp_fail_bbu ;
extern struct _Filter pi_batt_temp_aft;
extern struct _Filter pi_batt_temp_bef;
extern struct _Filter pi_batt_break;
extern struct _Filter pi_batt_break_chg;
extern struct _Filter pi_batt_not ;
extern struct _Filter pi_latch_fail;
extern struct _Filter pi_batt_low_6 ;
extern struct _Filter pi_batt_high_6 ;
/////////////////////////////////////////////////////////////////
extern struct _Filter pi_burst_i_over;
extern struct _Filter pi_burst_i_good;
extern struct _Filter pi_batt_con;

extern struct _Filter pi_fan_low_protection;
extern struct _Filter pi_fan_high_protection;
extern struct _Filter pi_fan_stop_protection;

extern uint8_t     gu8_f_over_v;
extern uint8_t     gu8_f_over_i_on;
extern uint8_t     gu8_f_over_chg;
extern uint8_t     gu8_f_sw_short;
extern uint8_t     gu8_f_pfc_err;
extern uint8_t     gu8_f_tmp_fail_adu;
extern uint8_t     gu8_f_tmp_fail_bbu;
extern uint8_t     gu8_f_tmp_wng_batt;

extern uint16_t    gu16_c_proc_delay;
extern uint8_t     gu8_f_proc_start;

extern uint8_t     gu8_f_ps_on;
extern uint8_t     gu8_f_burst_on;
extern uint8_t     gu8_f_dischg12_ovp;
extern uint8_t     gu8_f_pfc_fail_in;

extern uint8_t     gu8_batt_connect;

extern uint16_t    gu16_d_fan_rpm;
extern uint16_t    gu16_d_fan_rpm_old;
extern uint8_t     gu8_f_odrRPM;

/////////追加分/////////////////////////////////////////
extern uint8_t     gu8_f_low_v;           //項番1-2:不足電圧 2-1
extern uint8_t     gu8_f_high_i_of;        //項番4:過電流保護 2-10
extern uint8_t     gu8_f_high_i_of_h;        //項番4:過電流保護 2-10  (H)
extern uint8_t     gu8_f_high_i_on;        //項番3:過電流保護 2-8
extern uint8_t     gu8_f_high_i_on_50ms;
extern uint8_t     gu8_f_high_v;          //項番8:過電流保護 2-7
extern uint8_t     gu8_f_high_i_dis_6;    //項番10:過電流保護 2-15  BATT6直
extern uint8_t     gu8_f_high_i_cha;      //項番12:過電流保護 2-13
extern uint8_t     gu8_f_high_v_cha_6;    //項番13:過電圧保護 2-11  BATT6直
extern uint8_t     gu8_f_low_v_shortage;    //項番15:不足保護 2-14
extern uint8_t     gu8_f_low_v_shortage_5a;//項番15:不足保護 2-14
extern uint8_t     gu8_f_bbu_sw_short;    //項番16:出力スイッチ故障(ショート) 2-9
extern uint8_t     gu8_f_bbu_sw_open;     //項番17:出力スイッチ故障(オープン) 2-9
extern uint8_t     gu8_f_fan_fail_adu;    //項番18:ADU 温度異常保護(警告) 1-1
extern uint8_t     gu8_f_fan_fail_bbu;    //項番19:BBU 温度異常保護(警告) 1-2
extern uint8_t     gu8_f_fail_bbu;
extern uint8_t     gu8_f_temp_fail_adu;   //項番20:ADU 温度異常保護 1-3
extern uint8_t     gu8_f_temp_fail_bbu;   //項番21:BBU 温度異常保護 1-4
extern uint8_t     gu8_f_batt_temp_aft;   //項番30:バッテリ温度抑止(充電中) 22.3.1 項番2
extern uint8_t     gu8_f_batt_temp_bef;
extern uint8_t     gu8_f_batt_break;      //項番31:バッテリ保護素子破損 22.3.1 項番3
extern uint8_t     gu8_f_batt_break_chg;
extern uint16_t    gu16_batt_break_chg_timer;
extern uint8_t     gu8_f_batt_not;        //項番32:バッテリ未接続 22.3.1 項番4
extern uint8_t     gu8_f_latch_fail;      //項番33:バッテリ温度異常 22.3.2 項番1
extern uint8_t     gu8_f_batt_low_6;      //項番34:バッテリ低電圧 22.3.2 項番2  BATT6直

extern uint8_t     gu8_f_batt_high_6;     //項番36:バッテリ高電圧 22.3.2 項番3  BATT6直


extern uint8_t     gu8_f_stop_cha;        //充電停止フラグ
extern uint8_t     gu8_f_susp_cha;        //充電中断フラグ
extern uint8_t     gu8_f_not_batt;        //バッテリ未接続時フラグ

extern uint32_t    gu32_c_opencheck_time;
extern uint8_t     gu8_f_opencheck;

extern uint8_t     gu8_f_ac_off_detected;
/////////////////////////////////////////////////
extern uint8_t     gu8_f_skip_reason;
extern uint8_t     gu_f_burst_i_over;
extern uint8_t     gu_f_burst_i_good;

extern int16_t     gi16_ad_llc_temp;
extern int16_t     gi16_ad_bbu_temp;
extern int16_t     gi16_ad_batt1_temp;
extern int16_t     gi16_ad_batt2_temp;
extern int16_t     gi16_ad_battery_temp;

extern uint8_t     gu8_f_batt_connect;
extern uint8_t     gu8_f_batt_connect_trg;

extern uint32_t    gu32_c_ac_on_period;
extern uint32_t    gu32_c_ac_off_period;
extern uint8_t     gu8_f_ac_on;
extern uint8_t     gu8_f_ac_on_1ms;
extern uint8_t     gu8_f_aft_ac_on;

extern uint16_t    gu16_c_ac_on_flt;
extern uint8_t     gu8_f_ac_on_trg;

extern uint8_t     gu8_f_ac_interrupt_1s;
extern uint8_t     gu8_f_ac_70v_ac_interrupt;
extern uint8_t     gu8_f_ac_under_70v;
extern uint32_t    gu32_c_ac_interrupt_protection;

extern uint8_t     gu8_f_rtc_1sec;
extern DL_RTC_Calendar gs_RTCCalendar;

extern uint8_t     gu8_f_ps_on_out;
extern uint32_t    gu32_c_ps_on_out_delay;
extern uint8_t     gu8_f_burst_out;
extern uint32_t    gu32_c_burst_out_delay;
extern uint8_t     gu8_f_12v_en_out;
extern uint32_t    gu32_c_12v_en_out_delay;
extern uint8_t     gu8_f_batt_en_out;
extern uint32_t    gu32_c_batt_en_out_delay;
extern uint8_t     gu8_f_chgv_114v_out;
extern uint32_t    gu32_c_chgv_114v_out_delay;
extern uint8_t     gu8_f_dischg12v_en_out;
extern uint32_t    gu32_c_dischg12v_en_out_delay;
extern uint8_t     gu8_f_batchg_en_out;
extern uint32_t    gu32_c_batchg_en_out_delay;
extern uint8_t     gu8_f_vcc_12v_en_out;
extern uint32_t    gu32_c_vcc_12v_en_out_delay;
extern uint8_t     gu8_f_test_out;
extern uint32_t    gu32_c_test_out_delay;

extern uint8_t      gu8_f_converter_pwm;
extern uint32_t     gu32_c_converter_pwm_delay;
extern uint8_t      gu8_f_fan_pwm;
extern uint32_t     gu32_c_fan_pwm_delay;

extern float        gf_dischg_i_coeff;
extern float        gf_batt_v_coeff;
extern float        gf_acdc12v_v_coeff;
extern float        gf_batt_chg_coeff;
extern float        gf_12vout_i_coeff;
extern float        gf_12vout_v_coeff;
extern uint16_t     gu16_dischg_i;
extern uint16_t     gu16_batt_v;
extern uint16_t     gu16_acdc12v_v;
extern uint16_t     gu16_batt_chg;
extern uint16_t     gu16_12vout_i;
extern uint16_t     gu16_12vout_v;

extern uint8_t      gu8_alm_type_12v_err;
extern uint8_t      gu8_alm_type_dischg_err;
extern uint8_t      gu8_alm_type_chg_err;
extern uint8_t      gu8_alm_type_temp_err;
extern uint8_t      gu8_alm_type_pfc_err;
extern uint8_t      gu8_alm_type_batt_err;
extern uint8_t      gu8_alm_type_fan_err;
extern uint8_t      gu8_f_backup_active_alm;
extern uint8_t      gu8_f_12v_oc_off;
extern uint8_t      gu8_f_12v_oc_off_h;
extern uint32_t     gu32_c_fan_fail_timer;
extern uint32_t     gu32_c_fan_fail_stop_timer;
extern uint8_t      gu8_f_fan_fail_stop;
extern uint8_t      gu8_f_fan_fail_check;

extern uint8_t      gu8_f_batt_err_startup_exist;
extern uint8_t     gu8_f_wdt_err;
extern uint32_t    gu32_c_low_v_shortage;

extern uint16_t    gu16_ad_12vout_i_now_ad;
extern uint16_t    gu16_ad_12vout_v_now_ad;
extern uint16_t    gu16_ad_chgout_v_now_ad;

// FAN制御用(PWM)
extern uint8_t     gu8_fan_output_stg;
extern uint16_t    gu16_fan_pwm_freq;
extern uint16_t    gu16_fan_now_pwm_duty;
extern uint16_t    gu16_fan_new_pwm_duty;
extern uint32_t    gu32_PWM_FREQ;
extern uint32_t    gu32_PWM_DUTY;
extern float       gf_pwm_target_bias;
extern float       gf_pwm_bias_add_duty;
extern uint8_t     f_gu8_pwm_target_updwn;
extern uint16_t    c_gu16_pwm_upd_period;
extern uint16_t    c_gu16_pwm_upd_comp;
#ifdef _DEBUG_ON_
extern uint8_t     gu8_his_flg;
#endif
extern int16_t     gi16_ctl_target_temp;
extern int16_t     gi16_pre_temp;
extern uint8_t     f_gu8_fan_temp_updwn;
extern uint16_t    gu16_fan_odr_duty;
extern uint16_t    gu16_fan_odr_rpm;
extern uint16_t    gu16_fan_correction_dutyy;
extern uint16_t    c_gu16_fan_temp_ctl;
extern uint16_t    c_gu16_duty_set;
extern uint8_t     f_gu8_fan_duty_change;

extern uint8_t     f_gu8_fan_speed_def;
extern uint8_t     f_gu8_fan_speed;
extern uint8_t     f_gu8_fan_ctl_mode;

extern uint32_t    gu32_b_fanrpm[256];
extern uint16_t    gu16_p_fanrpm;

extern uint8_t     gu8_f_wng_fan_low;
extern uint8_t     gu8_f_wng_fan_high;
extern uint8_t     gu8_f_wng_fan_low_protection;
extern uint8_t     gu8_f_wng_fan_high_protection;
extern uint8_t     gu8_f_wng_fan_stop_protection;
extern uint8_t     gu8_f_fan_fail;

extern char gu8_s_debug_fan_sirei_num;

extern uint8_t     gu8_f_backup_active;
extern uint8_t     gu8_f_charge_output;
extern uint8_t     gu8_f_dischg_term;
extern uint8_t     gu8_c_dischg_term;
extern uint8_t     gu8_backup_enable_cmd;
extern uint8_t     gu8_backup_off_cmd;
extern uint8_t     gu8_f_susp_dischg;
extern uint8_t     gu8_f_stop_dischg;

extern uint8_t     gu8_f_stop_condition;
extern uint8_t     gu8_f_first_check;
extern uint8_t     gu8_f_initial_skip;

extern uint8_t     gu8_f_charging_active;
extern uint8_t     gu8_f_charge_on_cmd;    // 受け取ったコマンド
extern uint8_t     gu8_f_charge_on;    // データ
extern uint8_t     gu8_f_charge_off_cmd;    // 受け取ったコマンド
extern uint8_t     gu8_f_charge_off;
extern uint8_t     gu8_f_full_charge;
extern uint32_t    gu32_c_minus_dv_disable;                    // 充電開始後、-ΔV検出を行わない期間カウンタ
extern uint8_t     gu8_f_charge_inhibited;
extern uint8_t     gu8_f_main_chg_now;

extern uint8_t     gu8_f_dcir_check_doing;
typedef struct {    // 寿命診断データ(BCコマンド返信用)
    uint8_t  batt_check_mode_res;     // バッテリ測定モード
    uint16_t batt_voltage1_res;       // バッテリ測定電圧1
    uint16_t batt_voltage2_res;       // バッテリ測定電圧2
    uint16_t batt_current1_res;       // バッテリ測定電流1
    uint16_t batt_current2_res;       // バッテリ測定電流2
    int8_t   batt_ir_temp_res;        // バッテリ測定温度
    int8_t   batt_ir_soc_mah_res;     // バッテリ測定SOC(mAh)
    uint16_t batt_ir_res;             // バッテリのDCIR
} life_diag_data_response_t;
extern life_diag_data_response_t gs_life_diag_data_response; // 寿命診断データ
extern uint8_t gu8_f_dcir_proc_init;
extern uint8_t     gu8_f_dcir_request;
extern uint8_t     gu8_f_dcir_complete;

extern int8_t      gi8_d_soc_wh;     // SOC(mAh)
extern int8_t      gi8_d_soc_mah;    // SOC(Wh)

extern uint8_t     gu8_f_ac_link;
extern uint8_t     gu8_f_ac_link_restarting;
extern uint8_t     gu8_f_output_restart;
extern uint32_t    gu32_c_ac_link_timer;

extern uint8_t     gu8_f_full_charge_dcir;
extern uint32_t    gu32_c_dcir_timer;
extern uint8_t     gu8_f_dischg_under_1s;
extern uint8_t     gu8_f_dischg_up_1s;

extern uint8_t     gu8_f_converter_pwm;
extern uint32_t    gu32_c_converter_pwm_delay;
extern uint8_t     gu8_f_fan_pwm;
extern uint32_t    gu32_c_fan_pwm_delay;

extern float       gf_dischg_i_coeff;
extern float       gf_batt_v_coeff;
extern float       gf_acdc12v_v_coeff;
extern float       gf_batt_chg_coeff;
extern float       gf_12vout_i_coeff;
extern float       gf_12vout_v_coeff;
extern uint16_t    gu16_ad_dischg_i;
extern uint16_t    gu16_ad_batt_v;
extern uint16_t    gu16_ad_acdc12v_v;
extern uint16_t    gu16_ad_batt_chg;
extern uint16_t    gu16_ad_12vout_i;
extern uint16_t    gu16_ad_12vout_v;

extern uint8_t     gu8_uart_main_receivedata[UART_RCV_MAIN_NUM];
extern uint8_t     gu8_uart_main_rcv_wpt;
extern uint8_t     gu8_uart_main_rcv_rpt;

extern uint8_t     gu8_rcv_main_stage;
extern uint32_t    gu32_rcv_all_timer;
extern uint8_t     gu8_rx_proc_stage;

extern uint8_t     gu8_d_uart_sendbuf[UART_REQ_NUM][SENDBUF_SIZE];
extern uint8_t     gu8_d_uart_recvbuf[UART_RCV_NUM][RECVBUF_SIZE];
extern uint8_t     gu8_d_uart_rcv_count[UART_RCV_NUM];
extern uint8_t     gu8_d_uart_rcv_wpt;
extern uint8_t     gu8_d_uart_rcv_rpt;
extern uint8_t     gu8_d_uart_datalen;
extern uint8_t     gu8_d_uart_rcv_num;
extern uint16_t    gu16_c_tx;
extern uint8_t     gu8_d_uart_snd_wpt;
extern uint8_t     gu8_d_uart_snd_rpt;
extern uint16_t    gu16_tx_send_req[UART_REQ_NUM][2];
extern uint8_t     gu8_d_sendbuf[SENDBUF_SIZE];
extern uint8_t     gu8_d_recvbuf[RECVBUF_SIZE];
extern uint8_t     gu8_f_cmd_id_no[UART_RCV_NUM];
extern uint8_t     gu8_f_ack_nak_rcv;
extern uint8_t     gu8_f_evt_ack_nak_rcv;
extern uint8_t     gu8_f_nak_sndreq;
extern uint8_t     gu8_proc_stage;
extern uint8_t     gu8_pos;
extern uint8_t     gu8_f_multi_command;
extern uint8_t     gu8_f_command_proc;
extern uint8_t     gu8_d_clock_data[6];

extern uint8_t     gu8_f_cmd_sc_recv;
extern uint32_t    gu32_c_cmd_sc_evt_delay;
extern uint8_t     gu8_f_cmd_d1_recv;
extern uint8_t     gu8_f_event_lost;

extern uint8_t     gu8_f_ac_interrupt_check;
extern uint8_t     gu8_f_ac_interrupt_detect;
extern uint32_t    gu32_ac_interrupt_timer;

extern set_parameter_t gs_set_parameter_tmp;
extern set_parameter_t gs_set_parameter;

extern uint8_t gu8_f_backup_start_sek;
extern uint8_t gu8_f_sl_cmd_rcv_sek;
extern uint8_t gu8_f_dischg_start_sek;
extern uint8_t gu8_f_full_chg_sek;
extern uint8_t gu8_f_soc_calc_finish_sek;
extern uint8_t gu8_f_soc_calc_finish_sek;
extern float gf_dischg_mah_val_sek;
extern float gf_chg_mah_val_sek;
extern uint32_t gu32_c_adu_temp_sek;
extern uint32_t gu32_c_adu_action_time;
extern uint32_t gu32_c_bat_connect_time;
extern uint32_t gu32_c_bat_temp_ave_sek;
extern uint8_t gu8_c_batt_temp_reference_ok;
extern uint16_t gu16_c_bat_temp_calc;
extern uint16_t gu16_bat_temp_1h_sum;
extern uint8_t gu8_c_bat_temp_1h_sum_sample;
extern uint8_t gu8_f_ac_70v_ac_interrupt_on_trg;
extern uint8_t gu8_f_bef_ac_70v_ac_interrupt;

extern uint8_t gu8_f_power_category_clear;
extern uint8_t gu8_f_batt_cate_clear;
extern uint8_t gu8_f_cd_cmd_rcv;

extern uint8_t gu8_f_charge_ok_clear;

extern uint8_t gu8_f_batt_life_over_threshold;

extern uint8_t gu8_cmd_ad_type;
extern uint8_t gu8_cmd_ad_position;
extern float gf_cmd_ad_val;
extern uint16_t gu16_cmd_ad_set_ad_val;
extern float gf_cmd_ad_after_correction_slope;
extern float gf_cmd_ad_calculated_value;

extern uint8_t gu8_f_otd_old_set_clk_cmd;
extern uint8_t gu8_f_otd_ac_off_time_en;
extern time_t gt_otd_ac_off_occurrence;
extern time_t gt_otd_ac_on_time;
extern int16_t gi16_otd_ps_off_bat_temp_ave;
extern int16_t gi16_otd_chg_bat_temp_ave;
extern uint8_t gu8_f_otd_chg_soc_calc_fin;
extern float gf_otd_chg_soc_now;
extern float gf_otd_chg_soc_total;
extern uint8_t gu8_f_otd_batt_deg_set;
extern uint16_t gu16_c_otd_ps_off_bat_temp_ave;
extern uint16_t gu16_c_otd_chg_bat_temp_ave;

extern uint8_t gu8_f_jcd_chg_soc_calc_fin;
extern float gf_jcd_ttl_chg_soc;
extern float gf_jcd_chg_soc_now;

extern uint8_t gu8_f_off_time_data_clear_en;

extern uint32_t gu32_c_soc_timer_1s;
extern uint32_t gu32_c_soc_timer_1h;
extern uint8_t  gu8_flag_old;
extern uint8_t  gu8_status_old;
extern uint8_t  gu8_eeprom_write_stage;
extern uint8_t  gu8_eeprom_read_all_stage;
extern uint8_t  gu8_eeprom_all_backup;
extern uint8_t  gu8_f_wng_fan_low_old;
extern uint8_t  gu8_f_wng_fan_high_old;
extern uint8_t  gu8_f_wng_fan_stop_old;
extern uint8_t  gu8_alm_type_batt_err_old;
extern uint8_t  gu8_f_batt_connect_old;
extern uint8_t  gu8_f_ac_on_old;
extern uint16_t gu16_c_ac_on;
extern uint16_t gu16_c_aft_ac_on;

extern uint32_t gu32_c_fan_prm_old;
extern uint32_t gu32_c_ac_on_old;
extern uint8_t  gu8_f_rpm;
extern uint16_t    gu16_c_sta_rpm;
extern uint8_t     gu8_now_spd;
extern uint8_t     gu8_new_spd;

extern uint16_t    gu16_now_rpm;
extern uint16_t    gu16_now_per;

extern uint16_t    gu16_new_rpm;
extern uint16_t    gu16_new_dty;
extern uint16_t    gu16_new_per;

extern uint16_t    gu16_max_rpm_5;
extern uint16_t    gu16_min_rpm_5;
extern uint16_t    gu16_max_rpm_1;
extern uint16_t    gu16_min_rpm_1;

extern float       gf_max_per;
extern float       gf_min_per;

extern float       gf_adj_per;

extern uint8_t gu8_f_charging_active_old;
extern uint8_t gu8_f_backup_active_old;
extern uint8_t gu8_f_fan_spd_backup;
extern uint8_t gu8_f_fail_adu_bbu;
extern uint8_t gu8_f_on;
extern uint16_t gu16_c_fan;

extern uint8_t gu8_ac_link_stage;

extern uint8_t gu8_f_response;

extern uint8_t gu8_cmd_sp_proc_stage;
extern uint8_t gu8_cmd_rp_proc_stage;
extern uint8_t gu8_cmd_se_proc_stage;
extern uint8_t gu8_cmd_ss_proc_stage;
extern uint8_t gu8_cmd_sl_proc_stage;
extern uint8_t gu8_cmd_bc_proc_stage;
extern uint8_t gu8_cmd_ad_proc_stage;

extern uint8_t gu8_ack_stage;
extern uint8_t gu8_nak_stage;
extern uint8_t gu8_tx_send_stage;
extern uint8_t gu8_evt_proc_stage;

extern uint8_t gu8_f_envt_first;

extern uint8_t gu8_burst_stage;
extern uint8_t gu8_dischg_ps_on_stage;
extern uint8_t gu8_dischg_ps_off_stage;
extern uint8_t gu8_f_ps_on_old;
extern uint8_t gu8_f_ps_on_backup_old;

extern uint8_t gu8_end_dischg_stage;

extern uint8_t gu8_f_user_select;
extern uint32_t gu32_c_event_wait;

extern uint32_t  gu32_c_eeprom_timer;

extern uint8_t gu8_f_before_shutdown;

extern uint8_t gu8_prev_ac_link;
///////////////////////////////
enum I2cControllerStatus {
    I2C_STATUS_IDLE = 0,
    I2C_STATUS_TX_STARTED,
    I2C_STATUS_TX_INPROGRESS,
    I2C_STATUS_TX_COMPLETE,
    I2C_STATUS_RX_STARTED,
    I2C_STATUS_RX_INPROGRESS,
    I2C_STATUS_RX_COMPLETE,
    I2C_STATUS_ERROR,
};

extern enum I2cControllerStatus gI2cControllerStatus;
extern uint8_t     gTxPacket[20];
extern uint8_t     gRxPacket[16];
extern uint32_t    gTxLen, gTxCount;
extern uint32_t    gRxLen, gRxCount;
extern uint16_t    eeprom_write_req[I2C_REQ_NUM][4];
extern uint16_t    eeprom_req_cnt;
extern uint8_t     eeprom_req_busy;
extern uint8_t     eeprom_req_write_idx;
extern uint8_t     eeprom_req_read_idx;
extern uint8_t     gu8_f_eeprom_check_error;


extern uint8_t     gu8_b_err_log[47];
////////////////////////////////////////////////////////////////////////
// 13.4.1 リアルタイムデータ
////////////////////////////////////////////////////////////////////////
typedef struct {
    uint16_t _12v_voltage;      // 12V出力電圧値
    uint16_t _12v_current;      // 12V出力電流値
    uint16_t batt_voltage;      // バッテリ電圧
    uint16_t charge_voltage;    // バッテリ充電電圧
    uint16_t batt_chg_current;  // バッテリ充電電流
    uint16_t batt_current;      // バッテリ放電電流
    int8_t   batt_soc_wh;       // バッテリSOC(Wh)
    int8_t   batt_soc_mah;      // バッテリSOC(mAh)
    int8_t   batt_temp;         // バッテリ温度
    int8_t   adu_temp;          // AC/DC部内部温度
    int8_t   bbu_temp;          // BACKUP部内部温度
    uint16_t fan_rotation;      // FAN回転数
    uint8_t  fan_level;         // FAN回転数レベル
} realtime_data_t;

extern realtime_data_t gs_realtime_data; // リアルタイムデータ

////////////////////////////////////////////////////////////////////////
// 13.6.1 寿命計算データ
////////////////////////////////////////////////////////////////////////
typedef struct {
    uint8_t  charge_data;      // バッテリ充電量データ
    uint8_t  charge_end;       // バッテリ充電完了
    uint8_t  batt_charge;      // バッテリ充電量
    int8_t   batt_temp;        // バッテリ温度
    uint16_t batt_deg;         // バッテリ劣化度
} life_calc_data_t;

extern life_calc_data_t gs_life_calc_data; // 寿命計算データ

////////////////////////////////////////////////////////////////////////
// 13.7.2 寿命診断データ
////////////////////////////////////////////////////////////////////////
typedef struct {
    uint8_t  batt_check_mode;     // バッテリ測定モード
    uint16_t batt_voltage1;       // バッテリ測定電圧1
    uint16_t batt_voltage2;       // バッテリ測定電圧2
    uint16_t batt_current1;       // バッテリ測定電流1
    uint16_t batt_current2;       // バッテリ測定電流2
    int8_t   batt_ir_temp;        // バッテリ測定温度
    int8_t   batt_ir_soc_mah;     // バッテリ測定SOC(mAh)
    uint16_t batt_ir;             // バッテリのDCIR
} life_diag_data_t;

extern life_diag_data_t gs_life_diag_data; // 寿命診断データ

////////////////////////////////////////////////////////////////////////
// 10.4.4 状態情報
////////////////////////////////////////////////////////////////////////
/*****************/
/* SIGNAL_STATUS */
/*****************/
struct signal_status_bit_t {
  uint8_t  burst_on :1; // BURST信号オン
  uint8_t  ps_on    :1; // PS_ON信号オン
  uint8_t  dummy    :6;
};
union signal_status_u {
    uint8_t all;
    struct signal_status_bit_t bit;
};
/*********************/
/* COMMAND_STATUS(1) */
/*********************/
struct command_status1_bit_t {
  uint8_t  backup_ready  :1; // バックアップ可能状態
  uint8_t  restart_ready :1; // RESTART待ち状態
  uint8_t  ps_off_charge :1; // PS_OFF_CHARGE有効
  uint8_t  burst         :1; // BURST有効
  uint8_t  dummy         :4;
};
union command_status1_u {
    uint8_t all;
    struct command_status1_bit_t bit;
};
/*********************/
/* COMMAND_STATUS(2) */
/*********************/
struct command_status2_bit_t {
  uint8_t  charge_on    :1; // CHARGE ONコマンド実行中
  uint8_t  charge_off   :1; // CHARGE OFFコマンド実行中
  uint8_t  batt_check   :1; // BATT CHECKコマンド実行中
  uint8_t  charge_ready :1; // 充電待ち受け状態
  uint8_t  dummy        :4;
};
union command_status2_u {
    uint8_t all;
    struct command_status2_bit_t bit;
};
/*****************/
/* BACKUP_STATUS */
/*****************/
struct backup_status_bit_t {
  uint8_t  batt_low    :1; // バッテリ容量低下
  uint8_t  batt_on     :1; // バックアップ中
  uint8_t  dummy       :6;
};
union backup_status_u {
    uint8_t all;
    struct backup_status_bit_t bit;
};
/******************/
/* CHARGE_STATUS */
/******************/
struct charge_status_bit_t {
  uint8_t  charge_on    :1; // 充電中
  uint8_t  charge_ok    :1; // 充電完了
  uint8_t  s_charge_on  :1; // 補充電中
  uint8_t  dummy        :5;
};
union charge_status_u {
    uint8_t all;
    struct charge_status_bit_t bit;
};
/***************/
/* ADU_WARNING */
/***************/
struct adu_warning_bit_t {
  uint8_t  dummy1       :1;
  uint8_t  adu_temp_wng :1; // ADU部温度警告検出時
  uint8_t  fan_wng      :1; // ファン回転数低下検出時
  uint8_t  dummy2       :5;
};
union adu_warning_u {
    uint8_t all;
    struct adu_warning_bit_t bit;
};
/**************/
/* ADU_ALM(1) */
/**************/
struct adu_alm1_bit_t {
  uint8_t  fan_fail       :1; // ファン破損検出時
  uint8_t  pfc_ov         :1; // PFC過電圧検出時
  uint8_t  _12v_oc_off_h  :1;//   8/20追加
  uint8_t  dummy          :5;
};
union adu_alm1_u {
    uint8_t all;
    struct adu_alm1_bit_t bit;
};
/***************/
/* BBU_WARNING */
/***************/
struct bbu_warning_bit_t {
  uint8_t  bbu_temp_wng :1; // BBU温度警告検出時
  uint8_t  dummy        :7;
};
union bbu_warning_u {
    uint8_t all;
    struct bbu_warning_bit_t bit;
};
/***********/
/* BBU_ALM */
/***********/
struct bbu_alm_bit_t {
  uint8_t  chg_oc   :1; // 充電回路過電流検出時
  uint8_t  chg_ov   :1; // 充電回路過電圧検出時
  uint8_t  chg_lv   :1; // 充電回路不足電圧検出時
  uint8_t  bbu_fail :1; // BBU破損検出時
  uint8_t  dummy    :4;
};
union bbu_alm_u {
    uint8_t all;
    struct bbu_alm_bit_t bit;
};
/****************/
/* BATT_WARNING */
/****************/
struct batt_warning_bit_t {
  uint8_t  batt_temp_wng :1; // バッテリ温度警告検出時
  uint8_t  dummy         :7;
};
union batt_warning_u {
    uint8_t all;
    struct batt_warning_bit_t bit;
};
/*************/
/* BATT_ALM1 */
/*************/
struct batt_alm1_bit_t {
  uint8_t  batt_ov       :1; // バッテリ過電圧時検出時
  uint8_t  batt_lv       :1; // バッテリ電圧低下時検出時
  uint8_t  batt_temp_alm :1; // バッテリ温度異常検出時
  uint8_t  dummy         :5;
};
union batt_alm1_u {
    uint8_t all;
    struct batt_alm1_bit_t bit;
};
/*************/
/* BATT_ALM2 */
/*************/
struct batt_alm2_bit_t {
  uint8_t  batt_dcn    :1; // バッテリ未接続検出時
  uint8_t  batt_p_fail :1; // バッテリ保護回路破損検出時
  uint8_t  batt_mcn    :1; // バッテリ誤接続検出時
  uint8_t  batt_life   :1; // バッテリ寿命検出時
  uint8_t  dummy       :4;
};
union batt_alm2_u {
    uint8_t all;
    struct batt_alm2_bit_t bit;
};
/**************/
/* ADU_ALM(2) */
/**************/
struct adu_alm2_bit_t {
  uint8_t  _12v_oc_off :1; // 12V PS_OFF過電流検出時
  uint8_t  _12v_oc     :1; // 12V過電流検出時
  uint8_t  _12v_lv     :1; // 12V不足電圧検出時
  uint8_t  _12v_ov     :1; // 12V過電圧検出時
  uint8_t  dummy       :4;
};
union adu_alm2_u {
    uint8_t all;
    struct adu_alm2_bit_t bit;
};

typedef struct {
    union signal_status_u   signal_status;
    union command_status1_u command_status1;
    union command_status2_u command_status2;
    union backup_status_u   backup_status;
    union charge_status_u   charge_status;
    union adu_warning_u     adu_warning;
    union adu_alm1_u        adu_alm1;
    union bbu_warning_u     bbu_warning;
    union bbu_alm_u         bbu_alm;
    union batt_warning_u    batt_warning;
    union batt_alm1_u       batt_alm1;
    union batt_alm2_u       batt_alm2;
    union adu_alm2_u        adu_alm2;
    uint8_t                 reserve[2];
} status_info_t;

extern status_info_t gs_status_info;

////////////////////////////////////////////////////////////////////////
// 6.3.2 イベントデータ
////////////////////////////////////////////////////////////////////////
/*****************/
/* BACKUP_STATUS */
/*****************/
struct e_backup_status_bit_t {
  uint8_t  batt_low :1; // バッテリ容量低下検出時
  uint8_t  batt_on  :1; // バックアップ開始時
  uint8_t  dummy    :6;
};
union e_backup_status_u {
    uint8_t all;
    struct e_backup_status_bit_t bit;
};
/*****************/
/* CHARGE_STATUS */
/*****************/
struct e_charge_status_bit_t {
  uint8_t  charge_on :1; // 充電開始時
  uint8_t  charge_ok :1; // 充電完了時
  uint8_t  dummy     :6;
};
union e_charge_status_u {
    uint8_t all;
    struct e_charge_status_bit_t bit;
};
/***************/
/* ADU_WARNING */
/***************/
struct e_adu_warning_bit_t {
  uint8_t  adu_life_wng :1; // 電源寿命警告検出時
  uint8_t  adu_temp_wng :1; // 電源温度警告検出時
  uint8_t  fan_wng      :1; // ファン回転数低下警告検出時
  uint8_t  dummy        :5;
};
union e_adu_warning_u {
    uint8_t all;
    struct e_adu_warning_bit_t bit;
};
/***********/
/* ADU_ALM */
/***********/
struct e_adu_alm_bit_t {
  uint8_t  fan_fail       :1; // ファン破損検出時
  uint8_t  pfc_ov         :1; // PFC過電圧検出時
  uint8_t  _12v_oc_off_h  :1;//   8/20追加
  uint8_t  dummy          :5;
};
union e_adu_alm_u {
    uint8_t all;
    struct e_adu_alm_bit_t bit;
};
/***************/
/* BBU_WARNING */
/***************/
struct e_bbu_warning_bit_t {
  uint8_t  bbu_temp_wng :1; // BBU温度警告検出時
  uint8_t  dummy        :7;
};
union e_bbu_warning_u {
    uint8_t all;
    struct e_bbu_warning_bit_t bit;
};
/***********/
/* BBU_ALM */
/***********/
struct e_bbu_alm_bit_t {
  uint8_t  chg_oc   :1; // 充電回路過電流検出時
  uint8_t  chg_ov   :1; // 充電回路過電圧検出時
  uint8_t  chg_lv   :1; // 充電回路不足電圧検出時
  uint8_t  bbu_fail :1; // BBU破損検出時
  uint8_t  dummy    :4;
};
union e_bbu_alm_u {
    uint8_t all;
    struct e_bbu_alm_bit_t bit;
};
/****************/
/* BATT_WARNING */
/****************/
struct e_batt_warning_bit_t {
  uint8_t  batt_temp_wng :1; // バッテリ温度抑止時
  uint8_t  dummy         :7;
};
union e_batt_warning_u {
    uint8_t all;
    struct e_batt_warning_bit_t bit;
};
/*************/
/* BATT_ALM1 */
/*************/
struct e_batt_alm1_bit_t {
  uint8_t  batt_ov       :1; // バッテリ過電圧検出時
  uint8_t  batt_lv       :1; // バッテリ電圧低下検出時
  uint8_t  batt_temp_alm :1; // バッテリ温度異常検出時
  uint8_t  dummy         :5;
};
union e_batt_alm1_u {
    uint8_t all;
    struct e_batt_alm1_bit_t bit;
};
/*************/
/* BATT_ALM2 */
/*************/
struct e_batt_alm2_bit_t {
  uint8_t  batt_dcn      :1; // バッテリ未接続検出時
  uint8_t  batt_p_fail   :1; // バッテリ保護回路破損検出時
  uint8_t  batt_mcn      :1; // バッテリ誤接続検出時
  uint8_t  batt_life     :1; // バッテリ寿命検出時
  uint8_t  dummy         :4;
};
union e_batt_alm2_u {
    uint8_t all;
    struct e_batt_alm2_bit_t bit;
};

typedef struct {
    union e_backup_status_u   backup_status;
    union e_charge_status_u   charge_status;
    union e_adu_warning_u     adu_warning;
    union e_adu_alm_u         adu_alm;
    union e_bbu_warning_u     bbu_warning;
    union e_bbu_alm_u         bbu_alm;
    union e_batt_warning_u    batt_warning;
    union e_batt_alm1_u       batt_alm1;
    union e_batt_alm2_u       batt_alm2;
    uint8_t                   reserve;
} event_data_t;

extern event_data_t gs_event_data;
extern event_data_t gs_event_data_new;
extern event_data_t gs_event_data_old;
extern event_data_t gs_event_data_change;

extern uint32_t gu32_reset_cause;
extern uint8_t gu8_f_ini_ps_on;
/*******************************/
/* Boot <-> User受け渡しデータ */
/*******************************/
typedef struct {
    uint8_t  gu8_f_start_status;   /* 起動状態フラグ */
    uint8_t  gu8_f_fw_update_mode; /* FW Update mode フラグ */
    uint32_t data[10];
} data_info_common_t;
extern data_info_common_t data_info_common;

#endif /* _NF55_GLOBAL_H_ */
