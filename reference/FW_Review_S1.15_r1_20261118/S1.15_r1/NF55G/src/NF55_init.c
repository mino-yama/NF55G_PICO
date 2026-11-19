#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"

void SystemInit(void);
void userInit(void);
void make_set_parameter_value(void);
void rtc_calendar_set( void );
void batt_err_alm_redisplay(void);

extern void converter_pwm_stop(void);
extern void set_info_evt_errlog( uint8_t flag, uint8_t status );

static const DL_TimerG_TimerConfig gTIMER_G12TimerConfig = {
    .period     = 0xFFFFFFFFL,                        // TIMG12 32bit
    .timerMode  = DL_TIMER_TIMER_MODE_PERIODIC,
    .startTimer = DL_TIMER_START,
};

/*******************************************************************************
 * Function Name: SystemInit()
 * Description  : HW期化処理
 * Arguments    : SysConfig設定以外で初期化したいもの
 * Return Value : None
 *******************************************************************************/
void SystemInit(void)
{
    NVIC_EnableIRQ(ADC12_0_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_1_INST_INT_IRQN);

    NVIC_EnableIRQ(GPIO_GRP_B_INT_IRQN);

    NVIC_EnableIRQ(I2C_0_INST_INT_IRQN);

    NVIC_EnableIRQ(RTC_INT_IRQn);

    NVIC_ClearPendingIRQ(UART_0_INST_INT_IRQN);
    NVIC_EnableIRQ(UART_0_INST_INT_IRQN);

    // TIMG12はここでStart
    DL_TimerA_initTimerMode(TIMER_G12_INST,
        (DL_TimerG_TimerConfig *) &gTIMER_G12TimerConfig);

    __enable_irq();
}
/*******************************************************************************
 * Function Name: userInit()
 * Description  : 初期化処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void userInit(void)
{
    memcpy( SS_FW_REV, FW_REVISION, 6 );     // 製造データ FW REVISIONセット

    // DAC_OUT(PA15)
    DL_DAC12_output12(DAC0, 0);

    /* Start RTC clock */
    DL_RTC_enableClockControl(RTC);

    rtc_calendar_set();           // RTC 時刻セット

    // SYNC_0/120/240 PWM Stop
    converter_pwm_stop();

    //****************************
    // EEPROM内容から復元する情報
    //****************************
    make_set_parameter_value();      // SET PARAMETERデータ

    if( gs_set_parameter.ps_on_backup == _ENABLE_ )   // PS_ON_BACKUP設定?
    {
        set_info_evt_errlog( FLAG_BACKUP_READY, _SET_);   // 状態情報 BACKUP_READY セット
    }
    else
    {
        set_info_evt_errlog( FLAG_BACKUP_READY, _RESET_); // 状態情報 BACKUP_READY リセット
    }

    if( SE_BURST == _ENABLE_ )          // Burst設定
    {
        set_info_evt_errlog( FLAG_BURST, _SET_);       // 状態情報 BURST有効
    }
    else
    {
        set_info_evt_errlog( FLAG_BURST, _RESET_);     // 状態情報 BURST無効
    }

    if( SE_PS_OFF_CHARGE == _ENABLE_ )  // PS_OFF_CHARGE設定
    {
        set_info_evt_errlog( FLAG_PS_OFF_CHARGE, _SET_);       // 状態情報 PS_OFF_CHARGE有効
    }
    else
    {
        set_info_evt_errlog( FLAG_PS_OFF_CHARGE, _RESET_);     // 状態情報 PS_OFF_CHARGE無効
    }

    /* S1.14 123F対策 補正の計算式を修正 */
#if 0
    gf_dischg_i_coeff  = ((g_eeprom_data.dischg_i.point1 - g_eeprom_data.dischg_i.point2) /
                                (g_eeprom_data.dischg_i.ad1 - g_eeprom_data.dischg_i.ad2))*1000;     // DISCHG_I AD(1)値係数(mA単位)
    gf_batt_v_coeff    = ((g_eeprom_data.batt_v.point1 - g_eeprom_data.batt_v.point2) /
                                (g_eeprom_data.batt_v.ad1 - g_eeprom_data.batt_v.ad2))*1000;         // BATT_V AD(1)値係数(mV単位)
    gf_acdc12v_v_coeff = ((g_eeprom_data.acdc12v_v.point1 - g_eeprom_data.acdc12v_v.point2) /
                                (g_eeprom_data.acdc12v_v.ad1 - g_eeprom_data.acdc12v_v.ad2))*1000;   // AC/DC12V_V AD(1)値係数(mV単位)
    gf_batt_chg_coeff  = ((g_eeprom_data.batt_chg.point1 - g_eeprom_data.batt_chg.point2) /
                                (g_eeprom_data.batt_chg.ad1 - g_eeprom_data.batt_chg.ad2))*1000;     // BATT_CHG AD(1)値係数(mA単位)
    gf_12vout_i_coeff  = 33000.0f/ UINT12_MAX_VALUE;                                                             // 12VOUT_I AD(1)値係数(mA単位) 3.3V=4095
    gf_12vout_v_coeff  = ((g_eeprom_data._12vout_v.point1 - g_eeprom_data._12vout_v.point2) /
                                (g_eeprom_data._12vout_v.ad1 - g_eeprom_data._12vout_v.ad2))*1000;   // 12VOUT_V AD(1)値係数(mV単位)
#endif

    /* DISCHG_Iの傾き、Point2のAD値、Point2の電流値 */
    gf_dischg_i_coeff     = (g_eeprom_data.dischg_i.point1 - g_eeprom_data.dischg_i.point2) / (g_eeprom_data.dischg_i.ad1 - g_eeprom_data.dischg_i.ad2);
    gf_dischg_i_coeff_ad2 =  g_eeprom_data.dischg_i.ad2;
    gf_dischg_i_coeff_po2 =  g_eeprom_data.dischg_i.point2;

    /* BATT_Vの傾き、Point2のAD値、Point2の電圧値 */
    gf_batt_v_coeff     = (g_eeprom_data.batt_v.point1 - g_eeprom_data.batt_v.point2) / (g_eeprom_data.batt_v.ad1 - g_eeprom_data.batt_v.ad2);
    gf_batt_v_coeff_ad2 =  g_eeprom_data.batt_v.ad2;
    gf_batt_v_coeff_po2 =  g_eeprom_data.batt_v.point2;

    /* acdc12V_vの傾き、Point2のAD値、Point2の電圧値 */
    gf_acdc12v_v_coeff     = (g_eeprom_data.acdc12v_v.point1 - g_eeprom_data.acdc12v_v.point2) / (g_eeprom_data.acdc12v_v.ad1 - g_eeprom_data.acdc12v_v.ad2);
    gf_acdc12v_v_coeff_ad2 = g_eeprom_data.acdc12v_v.ad2;
    gf_acdc12v_v_coeff_po2 = g_eeprom_data.acdc12v_v.point2;

    /* batt_chgの傾き、Point2のAD値、Point2の電流値 */
    gf_batt_chg_coeff     = (g_eeprom_data.batt_chg.point1 - g_eeprom_data.batt_chg.point2) / (g_eeprom_data.batt_chg.ad1 - g_eeprom_data.batt_chg.ad2);
    gf_batt_chg_coeff_ad2 = g_eeprom_data.batt_chg.ad2;
    gf_batt_chg_coeff_po2 = g_eeprom_data.batt_chg.point2;

	/* (ここは変更無し) 12VOUT_I AD(1)値係数(mA単位) 3.3V=4095 */
    gf_12vout_i_coeff  = 33000.0f/ UINT12_MAX_VALUE;

    /* 12vout_vの傾き、Point2のAD値、Point2の電圧値 */
    gf_12vout_v_coeff     = (g_eeprom_data._12vout_v.point1 - g_eeprom_data._12vout_v.point2) / (g_eeprom_data._12vout_v.ad1 - g_eeprom_data._12vout_v.ad2);
    gf_12vout_v_coeff_ad2 = g_eeprom_data._12vout_v.ad2;
    gf_12vout_v_coeff_po2 = g_eeprom_data._12vout_v.point2;

    // SOC(%)の計算
    gi8_d_soc_mah = (int8_t)((g_eeprom_data.batt_cap.mah * 100) / (float)SP_BATT_CAP_MAH);    // SOC(mAh)%  SP_BATT_CAP_MAH = 4900
    if( gi8_d_soc_mah >= SOC_80 )  // SOC 80%以上?
    {
        set_info_evt_errlog( FLAG_CHARGE_OK, _SET_ );      // 満充電(充電完了)イベント セット
    }
    else
    {
        set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );    // 満充電(充電完了)イベント セット
    }

    /* S1.14 121F対策 */
    gf_jcd_ttl_chg_soc = g_eeprom_data.batt_cap.chgsoc;

    batt_err_alm_redisplay(); // バッテリ異常時の状態復元

    gf_otd_chg_soc_total =g_eeprom_data.off_period_data.off_charge * 49.0f;
    /* 出力系初期値 */
#if 1   // SysConfigの初期値を同じ(/12V_EN以外)
    gu8_f_ps_on_out        = _OUT_OFF_;        // PS_ON OFF
    gu32_c_ps_on_out_delay = 0;
    gu8_f_burst_out        = _OUT_OFF_;        // BURST_ON OFF
    gu32_c_burst_out_delay = 0;
    gu8_f_12v_en_out        = _OUT_ON_;        // /12V_EN ON
    gu32_c_12v_en_out_delay = 0;
    gu8_f_batt_en_out        = _OUT_OFF_;      // BATT_EN OFF
    gu32_c_batt_en_out_delay = 0;
    gu8_f_chgv_114v_out        = _OUT_OFF_;    // CHRGV_11.4V OFF
    gu32_c_chgv_114v_out_delay = 0;
    gu8_f_dischg12v_en_out        = _OUT_OFF_; // DISCHG12V_EN OFF
    gu32_c_dischg12v_en_out_delay = 0;
    gu8_f_batchg_en_out        = _OUT_OFF_;    // /BATCHG_EN OFF
    gu32_c_batchg_en_out_delay = 0;
    gu8_f_vcc_12v_en_out        = _OUT_OFF_;   // VCC_12V_EN OFF
    gu32_c_vcc_12v_en_out_delay = 0;
    gu8_f_test_out        = _OUT_OFF_;         // TEST_OUT OFF
    gu32_c_test_out_delay = 0;
#endif

    gu8_f_converter_pwm        = _OUT_NOT_;    // Converter PWM OFF
    gu32_c_converter_pwm_delay = 0;
    gu8_f_fan_pwm        = _OUT_NOT_;          // FAN PWM OFF
    gu32_c_fan_pwm_delay = 0;

    gu16_c_proc_delay = TIMER_100ms; // 処理開始遅延カウンタ
    gu8_f_proc_start = 0;            // 処理開始フラグOFF

    /* OFF期間データ */
    if( g_eeprom_data.set_clock.time != 0x69560D60L )    // ROM初期化後以外を参照する
    {
        gt_otd_ac_off_occurrence= *(time_t*)&g_eeprom_data.set_clock.time;
    }
    else
    {
        gt_otd_ac_off_occurrence = 0;
    }
    gu8_f_otd_batt_deg_set = _ON_;    // バッテリ劣化度_更新
}

/*******************************************************************************
 * Function Name: make_set_parameter_value()
 * Description  : SET PARAMETERデータ作成処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void make_set_parameter_value(void)
{
    gs_set_parameter = g_eeprom_data.set_parameter;

    if( gs_set_parameter.batt_low_thf == 0 )      // バッテリ充電量低下(BATT_LOW)閾値 = 0?
    {
        gs_set_parameter.batt_low_thf = SET_PRAMETER_DEF_TBL.batt_low_thf;    // 初期値(50)
    }

    if( gs_set_parameter.batt_cap_mah == 0 )      // バッテリ容量(mAh単位) = 0?
    {
        gs_set_parameter.batt_cap_mah = SET_PRAMETER_DEF_TBL.batt_cap_mah;    // 初期値(4900)
    }

    if( gs_set_parameter.batt_cap_wh == 0 )       // バッテリ容量(Wh単位) = 0?
    {
        gs_set_parameter.batt_cap_wh = SET_PRAMETER_DEF_TBL.batt_cap_wh;      // 初期値(36)
    }
    //if( gs_set_parameter.chg_ir_thd == 0 )        // 充電DCIRの判定閾値 = 0?
    //{
    //    gs_set_parameter.chg_ir_thd = SET_PRAMETER_DEF_TBL.chg_ir_thd;       // 初期値(0)
    //}

    if( gs_set_parameter.batt_wng_thd == 0 )      // バッテリ充電抑止温度閾値 = 0?
    {
        gs_set_parameter.batt_wng_thd = SET_PRAMETER_DEF_TBL.batt_wng_thd;   // 初期値(65)
    }

    if( gs_set_parameter.batt_alm_thd == 0 )      // バッテリ温度異常閾値 = 0?
    {
        gs_set_parameter.batt_alm_thd = SET_PRAMETER_DEF_TBL.batt_alm_thd;   // 初期値(80)
    }

    if( gs_set_parameter.adu_temp_thd == 0 )      // AC/DC部の温度警告(ADU_TEMP_WNG)の検出閾値 = 0?
    {
        gs_set_parameter.adu_temp_thd = SET_PRAMETER_DEF_TBL.adu_temp_thd;   // 初期値(85)
    }

    if( gs_set_parameter.bbu_temp_thd == 0 )      // BACKUP部の温度警告(BBU_TEMP_WNG)の検出閾値 = 0?
    {
        gs_set_parameter.bbu_temp_thd = SET_PRAMETER_DEF_TBL.bbu_temp_thd;   // 初期値(90)
    }

    if( gs_set_parameter.fan_wng_thd == 0 )       // FANの回転停止警告(FAN_WMG)の検出閾値 = 0?
    {
        gs_set_parameter.fan_wng_thd = SET_PRAMETER_DEF_TBL.fan_wng_thd;     // 初期値(615)
    }
}

/*******************************************************************************
 * Function Name: rtc_calendar_set()
 * Description  : RTC 時刻セット処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void rtc_calendar_set( void )
{
    time_t tt;
    struct tm *tm_lt;
    DL_RTC_Calendar RTCCalendarConfig;

    tt = *(time_t*)&g_eeprom_data.set_clock.time;

    tm_lt = localtime(&tt);

    RTCCalendarConfig.year  = tm_lt->tm_year+1900;
    RTCCalendarConfig.month = tm_lt->tm_mon+1;
    RTCCalendarConfig.dayOfMonth = tm_lt->tm_mday;
    RTCCalendarConfig.hours = tm_lt->tm_hour;
    RTCCalendarConfig.minutes = tm_lt->tm_min;
    RTCCalendarConfig.seconds = tm_lt->tm_sec;

    /* Set RTC Calendar */
    DL_RTC_initCalendar(RTC, RTCCalendarConfig, DL_RTC_FORMAT_BINARY);

    gs_RTCCalendar = RTCCalendarConfig;
}

/*******************************************************************************
 * Function Name: batt_err_alm_status()
 * Description  : バッテリ異常時の状態復元
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void batt_err_alm_redisplay(void)
{
    gu8_alm_type_batt_err = g_eeprom_data.batt_err;   // [バッテリ異常](ラッチ系)情報

    if( gu8_alm_type_batt_err != 0 ) // 異常あり?
    {
        if( (gu8_alm_type_batt_err & BIT0) != 0 )
        {
            set_info_evt_errlog( FLAG_BATT_TEMP_ALM, _SET_ );  // BATT_TEMP_ALM  (4)
        }

        if( (gu8_alm_type_batt_err & BIT1) != 0 )
        {
            set_info_evt_errlog( FLAG_BATT_LV, _SET_ );  // BATT_LV  (2)
        }

        if( (gu8_alm_type_batt_err & BIT2) != 0 )
        {
            set_info_evt_errlog( FLAG_BATT_OV, _SET_ );  // BATT_OV  (2)
        }

        if( (gu8_alm_type_batt_err & BIT3) == 0 )
        {
            gu8_f_batt_err_startup_exist = 1; // バッテリ異常有りフラグ
        }

        /*** 放電停止 ***/
        gu8_f_stop_dischg =  _ON_;   //放電停止フラグON

        /*** 充電停止 ***/
        gu8_f_stop_cha= _ON_;        //充電停止フラグ
    }
}
