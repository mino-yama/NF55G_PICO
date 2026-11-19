#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"

void data_proc(void);

void rtc_data_set(void);
void rtc_data_set_fu(void);
void soc_calc_proc(void);
void realtime_data_set_proc(void);
void cumulative_data_proc(void);
void off_time_data_proc(void);
void life_calc_data_proc(void);
void get_data2_proc(void);
void set_info_evt_errlog( uint8_t flag, uint8_t status );
void charge_ready_proc(void);

/* S1.12 満充電検出時のCHARGE_ON, CHARGE_OKの同時ゼロ対策 */
void full_charge_proc(void);

/*******************************************************************************
* Function Name: data_proc()
* Description  : 各種データ処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void data_proc(void)
{
	
	if(gu8_f_before_shutdown!=1)
	{
		 rtc_data_set();             // RTC時間処理

    	soc_calc_proc();            // SOC計算処理

    	realtime_data_set_proc();   // リアルタイムデータ設定処理

	}


    cumulative_data_proc();        // 積算データ処理

    if(gu8_f_before_shutdown!=1)
    {
    	off_time_data_proc();       // OFF期間データ処理

    	life_calc_data_proc();    // 寿命計算データ処理

    	get_data2_proc();           // GET_DATA2データ処理

    	charge_ready_proc();        // 充電待ち状態監視処理
			
	}
   
}
extern uint8_t eeprom_write_request( uint32_t pos, uint32_t num, uint8_t mode );

/*******************************************************************************
* Function Name: error_log_request()
* Description  : エラーログ処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void error_log_request( uint8_t almid )
{
    uint8_t wp;

    wp = g_eeprom_data.error_log_index.error_log_writepointer; // 書込みポインタ

    g_eeprom_data.error_log_data[wp].year  = gs_RTCCalendar.year-2000;  /* 2000年からの年 */
    g_eeprom_data.error_log_data[wp].month = gs_RTCCalendar.month;      /* 月(1～12) */
    g_eeprom_data.error_log_data[wp].day   = gs_RTCCalendar.dayOfMonth; /* 日(1～31) */
    g_eeprom_data.error_log_data[wp].hour  = gs_RTCCalendar.hours;      /* 時(0～23) */

    g_eeprom_data.error_log_data[wp].id    = almid;      /* ALM ID */

    eeprom_write_request( EEPROM_ERR_DATA_POS+(sizeof(error_log_data_t)*wp) , sizeof(error_log_data_t), 1 ); // EEPROM書込みリクエスト(1byte)

    g_eeprom_data.error_log_index.error_log_writepointer++;   // 書込みポインタ+1
    if( g_eeprom_data.error_log_index.error_log_writepointer >= ERROR_LOG_COUNT )
    {
        g_eeprom_data.error_log_index.error_log_writepointer = 0;
    }

    eeprom_write_request( EEPROM_ERR_IDX_POS , sizeof(error_log_index_t), 0 ); // EEPROM書込みリクエスト(page)
}


/*******************************************************************************
* Function Name: operate_log_request()
* Description  : オペレートログ処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void operate_log_request( uint8_t almid )
{
    uint8_t wp;

    wp = g_eeprom_data.operate_log_index.operate_log_writepointer; // 書込みポインタ

    g_eeprom_data.operate_log_data[wp].year  = gs_RTCCalendar.year-2000;  /* 2000年からの年 */
    g_eeprom_data.operate_log_data[wp].month = gs_RTCCalendar.month;      /* 月(1～12) */
    g_eeprom_data.operate_log_data[wp].day   = gs_RTCCalendar.dayOfMonth; /* 日(1～31) */
    g_eeprom_data.operate_log_data[wp].hour  = gs_RTCCalendar.hours;      /* 時(0～23) */

    g_eeprom_data.operate_log_data[wp].id    = almid;      /* ALM ID */

    eeprom_write_request( EEPROM_OPE_DATA_POS+(sizeof(operate_log_data_t)*wp) , sizeof(operate_log_data_t), 1 ); // EEPROM書込みリクエスト(1byte)

    g_eeprom_data.operate_log_index.operate_log_writepointer++;   // 書込みポインタ+1
    if( g_eeprom_data.operate_log_index.operate_log_writepointer >= OPERATE_LOG_COUNT )
    {
        g_eeprom_data.operate_log_index.operate_log_writepointer = 0;
    }

    eeprom_write_request( EEPROM_OPE_IDX_POS , sizeof(operate_log_index_t), 0 ); // EEPROM書込みリクエスト(page)
}


/*******************************************************************************
* Function Name: rtc_data_set()
* Description  : RTC時間処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void rtc_data_set(void)
{
    time_t tt;
    struct tm tm_data;

    if( gu8_f_rtc_1sec != 0 )
    {
        gu8_f_rtc_1sec = 0;

        gs_RTCCalendar = DL_RTC_getCalendarTime(RTC);

        tm_data.tm_year  = gs_RTCCalendar.year-1900;  /* 1900年からの年 */
        tm_data.tm_mon   = gs_RTCCalendar.month-1;     /* 月(0～11) */
        tm_data.tm_mday  = gs_RTCCalendar.dayOfMonth; /* 日(1～31) */
        tm_data.tm_hour  = gs_RTCCalendar.hours;      /* 時(0～23) */
        tm_data.tm_min   = gs_RTCCalendar.minutes;     /* 分(0～59) */
        tm_data.tm_sec   = gs_RTCCalendar.seconds;     /* 秒(0～59) */
        tm_data.tm_isdst = 0;  /* 夏時間フラグ(採用:>0,不採用:0,不明:<0)  */

        //time_t構造体に変換
        tt = mktime(&tm_data);
        *(time_t*)&g_eeprom_data.set_clock.time = tt;  // 保存
    }
}

/*******************************************************************************
* Function Name: rtc_data_set_fu()
* Description  : RTC時間処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void rtc_data_set_fu(void)
{
    time_t tt;
    struct tm tm_data;

        gs_RTCCalendar = DL_RTC_getCalendarTime(RTC);

        tm_data.tm_year  = gs_RTCCalendar.year-1900;  /* 1900年からの年 */
        tm_data.tm_mon   = gs_RTCCalendar.month-1;     /* 月(0～11) */
        tm_data.tm_mday  = gs_RTCCalendar.dayOfMonth; /* 日(1～31) */
        tm_data.tm_hour  = gs_RTCCalendar.hours;      /* 時(0～23) */
        tm_data.tm_min   = gs_RTCCalendar.minutes;     /* 分(0～59) */
        tm_data.tm_sec   = gs_RTCCalendar.seconds;     /* 秒(0～59) */
        tm_data.tm_isdst = 0;  /* 夏時間フラグ(採用:>0,不採用:0,不明:<0)  */

        //time_t構造体に変換
        gt_otd_ac_on_time = mktime(&tm_data);
       // *(time_t*)&g_eeprom_data.set_clock.time = gt_otd_ac_on_time;  // 保存
        gu8_f_cmd_sc_recv = 1;

}
/*******************************************************************************
* Function Name: soc_calc_proc()
* Description  : SOC計算処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void soc_calc_proc(void)
{
    float fd_mah;
    float fd_wh;
    //static uint32_t c_soc_timer_1s = 0;
    //static uint32_t c_soc_timer_1h = 0;
    float fd_dischage;
    float fd_leak = 0.024f;               // 電源内部漏れ電流(24uA=0.024mA)

    int16_t mah_soc;
    int16_t wh_soc;

    if( gu8_f_proc_start == 0 )  // 処理開始前?
    {
        return;
    }

    if( ++gu32_c_soc_timer_1s >= TIMER_1000ms ) // 1秒
    {
        gu32_c_soc_timer_1s = 0;

        if( gu8_f_charging_active != 0 )    // 充電中
        {
            fd_mah = (float)gu16_ad_batt_chg / 3600;                                           // mAh  (BATT_CHG/3600)
            fd_wh  = ((float)gu16_ad_batt_chg / 1000) * ((float)gu16_ad_batt_v / 1000) / 3600; // Wh   (BATT_CHG×BATT_V/3600)
            g_eeprom_data.batt_cap.mah += fd_mah;   // SOC(mAh) 加算
            g_eeprom_data.batt_cap.wh  += fd_wh;    // SOC(Wh)  加算

            gu8_f_soc_calc_finish_sek = 1;    // 積算データ:バッテリ総放電量/バッテリ総充電量　記録用フラグ
            gf_chg_mah_val_sek = fd_mah;
            gu8_f_otd_chg_soc_calc_fin = _ON_;    // OFF期間データ:充電量SOC計算完了フラグ
            gf_otd_chg_soc_now = fd_mah;    // ※積算データ等と同様、SOC(mAh)の方を参照
            if( gu8_f_ps_on == _ON_ )    // PS_OFF期間中は含めない
            {
                gu8_f_jcd_chg_soc_calc_fin = _ON_;    // 寿命計算データ用充電量計算完了フラグ
                gf_jcd_chg_soc_now = fd_mah;          // 寿命計算データ用今回充電量保存変数
            }
        }
        else if( gu8_f_charge_output != 0 )    // 放電中
        {
            fd_mah = (float)gu16_ad_dischg_i / 3600;                                           // mAh  (BATT_CHG/3600)
            fd_wh  = ((float)gu16_ad_dischg_i / 1000) * ((float)gu16_ad_batt_v / 1000) / 3600; // Wh   (BATT_CHG×BATT_V/3600)
            g_eeprom_data.batt_cap.mah -= fd_mah;  // SOC(mAh) 減算
            if( g_eeprom_data.batt_cap.mah < 0 )
            {
                g_eeprom_data.batt_cap.mah = 0;
            }
            g_eeprom_data.batt_cap.wh  -= fd_wh;   // SOC(Wh)  減算
            if( g_eeprom_data.batt_cap.wh < 0 )
            {
                g_eeprom_data.batt_cap.wh = 0;
            }

            gu8_f_soc_calc_finish_sek = 2;    // 積算データ:バッテリ総放電量/バッテリ総充電量　記録用フラグ
            gf_dischg_mah_val_sek = fd_mah;
        }

#if 0 /* S1.12 満充電検出時のCHARGE_ON, CHARGE_OKの同時ゼロ対策 */
        if( gu8_f_full_charge != 0 ) // 満充電
        {
            gu8_f_full_charge = 0;

            set_info_evt_errlog( FLAG_CHARGE_OK, _SET_ );      // 満充電(充電完了)イベント
            set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );// 満充電(充電中)イベント
            set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );  // 満充電(充電中)イベント

            g_eeprom_data.batt_cap.mah = (float)SP_BATT_CAP_MAH;    // SOC(mAh) 100%
            g_eeprom_data.batt_cap.wh = (float)SP_BATT_CAP_WH;      // SOC(Wh)  100%

            gu8_f_full_charge_dcir = 1; // 満充電(DCIR用)
            gu32_c_dcir_timer  = 0;     // DCIR用タイマ
            gu8_f_dischg_under_1s = 0;  // 放電1秒未満 OFF
            gu8_f_dischg_up_1s = 0;     // 放電1秒以上 OFF
            gu8_f_dcir_proc_init = 1;   // DCIR測定_変数初期化フラグ

            gu8_f_full_chg_sek = 1;     // 積算データ:バッテリ総充電回数　記録用フラグ
            gs_life_calc_data.charge_end = 1;    // 寿命計算データ:バッテリ充電完了
        }
#endif
    }

    if( ++gu32_c_soc_timer_1h >= TIMER_1hour ) // 1時間
    {
        gu32_c_soc_timer_1h = 0;

        if( gu8_f_batt_connect != _BATT_NOT_CONNECT_ ) // BATT1/BATT2接続
        {
            // 自己放電
            if( (gu8_f_charging_active == 0) && (gu8_f_charge_output == 0) )  // 未充電/未放電
            {
                // mAh
                if( (gi16_ad_battery_temp >= BATT_TEMP_35C) && (gu16_ad_batt_v >= BATT_V_8_04V) ) // 35℃以上 8.04V以上
                {
                    fd_dischage = 4.167f;  // 4.167mA
                }
                else if( (gi16_ad_battery_temp < BATT_TEMP_35C) && (gu16_ad_batt_v >= BATT_V_8_04V) ) // 35℃未満 8.04V以上
                {
                    fd_dischage = 1.389f;  // 1.389mA
                }
                else if( (gi16_ad_battery_temp >= BATT_TEMP_35C) && (gu16_ad_batt_v < BATT_V_8_04V) ) // 35℃以上 8.04V未満
                {
                    fd_dischage = 0.833f;  // 0.833mA
                }
                else  // 35℃未満 8.04V未満
                {
                    fd_dischage = 0.126f;  // 0.126mA
                }
                fd_mah = fd_dischage + fd_leak;
                g_eeprom_data.batt_cap.mah -= fd_mah;  // SOC(mAh) 減算

                fd_wh = ((fd_dischage / 1000) + (fd_leak / 1000)) * ((float)gu16_ad_batt_v / 1000);
                g_eeprom_data.batt_cap.wh  -= fd_wh;   // SOC(Wh)  減算
            }
        }
    }

    if( (gu8_alm_type_batt_err != 0 ) ||    // バッテリ異常(温度異常/高電圧/低電圧)
        ( gu8_f_batt_break == _ON_ ) ||     // バッテリ異常(保護素子破損)
        ( gu8_f_batt_not == _ON_ )          // バッテリ異常(未接続),バッテリ交換(未接続と同等)
    )
    {
        set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );      // 満充電(充電完了)イベント リセット
        g_eeprom_data.batt_cap.mah = 0;   // SOC(mAh) 0%
        g_eeprom_data.batt_cap.wh = 0;    // SOC(Wh) 0%
    }


    // SOC(%)の計算
    mah_soc = (int16_t)((g_eeprom_data.batt_cap.mah * 100) / (float)SP_BATT_CAP_MAH);    // SOC(mAh)%  SP_BATT_CAP_MAH = 4900
    wh_soc =  (int16_t)((g_eeprom_data.batt_cap.wh * 100)  / (float)SP_BATT_CAP_WH);     // SOC(Wh)%   SP_BATT_CAP_WH  = 36

    if( mah_soc >= SOC_100P )  // SOC 100%以上
        {
            gi8_d_soc_mah=SOC_100P;
        }else if(mah_soc <= SOC_0){

            gi8_d_soc_mah=SOC_0;
        }else{

            gi8_d_soc_mah=mah_soc;
        }

        if( wh_soc >= SOC_100P )  // SOC 100%以上
        {
            gi8_d_soc_wh=SOC_100P;
            }else if(wh_soc <= SOC_0){

                gi8_d_soc_wh=SOC_0;
        }else{

            gi8_d_soc_wh=wh_soc;
        }

    if( gi8_d_soc_mah <= SOC_80 )  // SOC 80%以上?
    {
        set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );    // 満充電(充電完了)イベント セット
    }

    // EEPROM保存
}
/* S1.12 満充電検出時のCHARGE_ON, CHARGE_OKの同時ゼロ対策 */
/*******************************************************************************
* Function Name: full_charge_proc()
* Description  : 満充電時処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void full_charge_proc(void)
{
    set_info_evt_errlog( FLAG_CHARGE_OK, _SET_ );      // 満充電(充電完了)イベント
    set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );// 満充電(充電中)イベント
    set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );  // 満充電(充電中)イベント

    g_eeprom_data.batt_cap.mah = (float)SP_BATT_CAP_MAH;    // SOC(mAh) 100%
    g_eeprom_data.batt_cap.wh = (float)SP_BATT_CAP_WH;      // SOC(Wh)  100%

    gi8_d_soc_mah = SOC_100P; // SOC(mAh) 100%
    gi8_d_soc_wh  = SOC_100P; // SOC(Wh)  100%

    gu8_f_full_charge_dcir = 1; // 満充電(DCIR用)
    gu32_c_dcir_timer  = 0;     // DCIR用タイマ
    gu8_f_dischg_under_1s = 0;  // 放電1秒未満 OFF
    gu8_f_dischg_up_1s = 0;     // 放電1秒以上 OFF
    gu8_f_dcir_proc_init = 1;   // DCIR測定_変数初期化フラグ

    gu8_f_full_chg_sek = 1;     // 積算データ:バッテリ総充電回数　記録用フラグ
    gs_life_calc_data.charge_end = 1;    // 寿命計算データ:バッテリ充電完了
}

/*******************************************************************************
* Function Name: realtime_data_set_proc()
* Description  : リアルタイムデータ設定処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void realtime_data_set_proc(void)
{
    gs_realtime_data._12v_voltage     = gu16_ad_12vout_v;     // 12V出力電圧値(4)    mV
    gs_realtime_data._12v_current     = gu16_ad_12vout_i;     // 12V出力電流値(4)    mA
    gs_realtime_data.batt_voltage     = gu16_ad_batt_v;       // バッテリ電圧(4)     mV

    if(gu8_f_charging_active==_OFF_){

           gs_realtime_data.charge_voltage   =0;
        }else{

           gs_realtime_data.charge_voltage   = gu16_ad_batt_v;       // バッテリ充電電圧(4) mV
        }
   // gs_realtime_data.charge_voltage   = gu16_ad_batt_v;       // バッテリ充電電圧(4) mV
    gs_realtime_data.batt_chg_current = gu16_ad_batt_chg;     // バッテリ充電電流(4) mA
    gs_realtime_data.batt_current     = gu16_ad_dischg_i;     // バッテリ放電電流(4) mA
    gs_realtime_data.batt_soc_wh      = gi8_d_soc_wh;         // バッテリSOC(Wh)(2)  %
    gs_realtime_data.batt_soc_mah     = gi8_d_soc_mah;        // バッテリSOC(mAh)(2) %
    gs_realtime_data.batt_temp        = gi16_ad_battery_temp/10; // バッテリ温度(2)  ℃
    gs_realtime_data.adu_temp         = gi16_ad_llc_temp/10;  // AC/DC部内部温度(2)  ℃
    gs_realtime_data.bbu_temp         = gi16_ad_bbu_temp/10;  // BACKUP部内部温度(2) ℃
    gs_realtime_data.fan_rotation     = gu16_d_fan_rpm;       // FAN回転数(4)        rpm
    gs_realtime_data.fan_level        = f_gu8_fan_speed;      // FAN回転数レベル(1)  STEP
}

/*******************************************************************************
* Function Name: cumulative_data_proc()
* Description  : 積算データ処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void cumulative_data_proc(void)
{

    if(gu8_f_before_shutdown!=1)
    {
        /*** 積算データを求めるための各種計算等処理 ***/
        // 積算データ_1時間未満の経過時間記録
        g_eeprom_data.cumulative_data.total_adu_hour_sub++;     // 電源稼働時間(1ms単位)
        if( gu8_f_batt_connect == _BATT1_CONNECT_ )          //バッテリ未接続
        {
            g_eeprom_data.cumulative_data.total_batt_hour_sub++;    // バッテリ接続時間(1ms単位)
        }

        // 平均バッテリ温度用記録(1m)
        if( ++gu16_c_bat_temp_calc >= TIMER_60s )
        {
            gu16_c_bat_temp_calc = 0;

            if( gu8_f_batt_connect == _BATT1_CONNECT_)
            {
                if( gi16_ad_battery_temp >= 0 )    // 0℃未満は0℃とする(一応)
                {
                    gu16_bat_temp_1h_sum += ( gi16_ad_battery_temp + 5 ) * 0.1;    // (バッテリ温度(単位:0.1℃) + 0.5℃ / 10) <-- 四捨五入し単位を1℃に変更
                }

                gu8_c_bat_temp_1h_sum_sample++;
            }
        }

        /*** 積算データ検出 ***/
        // 1. 電源内部積算温度(TOTAL_ADU_TEMP)
        if( ++gu32_c_adu_temp_sek >= TIMER_1hour )
        {
            gu32_c_adu_temp_sek = 0;

            if( (g_eeprom_data.cumulative_data.total_adu_temp + ((gi16_ad_llc_temp + 5 ) * 0.1)) <= UINT24_MAX_VALUE_UNDER )
            {
                if( gi16_ad_llc_temp >= 0 )    // 0℃未満は0℃とする(一応)
                {
                    g_eeprom_data.cumulative_data.total_adu_temp += ( gi16_ad_llc_temp + 5 ) * 0.1;    // (バッテリ温度(単位:0.1℃) + 0.5℃ / 10) <-- 四捨五入し単位を1℃に変更
                }
            }
            else
            {
                g_eeprom_data.cumulative_data.total_adu_temp = UINT24_MAX_VALUE_UNDER;    // 最大値以上なら最大値固定
            }
        }

        // 2. 電源稼働時間(TOTAL_ADU_HOUR)
        if( gu8_f_ac_on == _ON_ )    // AC_OFF時間は含まない
        {
            if( ++gu32_c_adu_action_time >= TIMER_1hour )
            {
                gu32_c_adu_action_time = 0;
                g_eeprom_data.cumulative_data.total_adu_hour_sub = 0;    // 電源稼働時間サブカウント　0クリア

                if( g_eeprom_data.cumulative_data.total_adu_hour < UINT16_MAX_VALUE )
                {
                    g_eeprom_data.cumulative_data.total_adu_hour++;
                }
                else
                {
                    g_eeprom_data.cumulative_data.total_adu_hour = 0;    // 積算量オーバーフロー時、稼働時間は0からリスタート
                }
            }
        }
    }

    // 3. 瞬断回数(70V以下)(AC_FAIL_COUNT)
    //if((gu8_f_bef_ac_70v_ac_interrupt == 0) && (gu8_f_ac_70v_syundan == 1))    // AC70V瞬断ONトリガ判別
    //{
    //    gu8_f_ac_70v_ac_interrupt_on_trg = 1;
    //}
    //gu8_f_bef_ac_70v_ac_interrupt = gu8_f_ac_70v_syundan;

    //if( gu8_f_ac_70v_ac_interrupt_on_trg == 1 )

    /*** 瞬断カウント+1(AC_FAIL_COUNT) ***/
    if( gu8_f_ac_on_trg == _TRG_OFF_ )   // AC ON->OFFトリガ
    {
        if( gu32_c_ac_interrupt_protection == 0 )  // 1秒間に発生する繰り返しの瞬断については瞬断回数は1回とカウントする
        {
            gu8_f_ac_70v_ac_interrupt = _ON_;
            gu32_c_ac_interrupt_protection = TIMER_1000ms; // 1秒
        }
    }
    if( gu32_c_ac_interrupt_protection != 0 )
    {
        gu32_c_ac_interrupt_protection--;
    }
    /*************************************/
    if( gu8_f_ac_70v_ac_interrupt == _ON_ ) // AC70V瞬断ONトリガ判別
    {
        //gu8_f_ac_70v_ac_interrupt_on_trg = 0;
        gu8_f_ac_70v_ac_interrupt = _OFF_;

        if( g_eeprom_data.cumulative_data.ac_fail_count < UINT12_MAX_VALUE )    // 最大値以上なら最大値固定
        {
            g_eeprom_data.cumulative_data.ac_fail_count++;
        }
    }

    if(gu8_f_before_shutdown!=1)
    {
        // 4. 瞬断回数(90V以下)(AC_LOW_COUNT)
        /* ※当データは一切変化しない */

        // 5. バックアップ回数(TOTAL_BACKUP_COUNT)
        if( gu8_f_backup_start_sek == 1 )
        {
            gu8_f_backup_start_sek = 0;

            if( g_eeprom_data.cumulative_data.total_backup_count < UINT16_MAX_VALUE )    // 最大値以上なら最大値固定
            {
                g_eeprom_data.cumulative_data.total_backup_count++;
            }
        }

        // 6. バッテリ劣化度(BATT_DEG)
        if( gu8_f_sl_cmd_rcv_sek == 1 )
        {
            gu8_f_sl_cmd_rcv_sek = 0;

            g_eeprom_data.cumulative_data.batt_deg = SL_BATT_DEG;
        }

        // 7. バッテリ接続時間(TOTAL_BATT_HOUR)
        if( gu8_f_ac_on == _ON_ )    // AC_OFF時間は含まない
        {
            if( gu8_f_batt_connect == _BATT1_CONNECT_)
            {
                if( ++gu32_c_bat_connect_time >= TIMER_1hour )
                {
                    gu32_c_bat_connect_time = 0;
                    g_eeprom_data.cumulative_data.total_batt_hour_sub = 0;    // バッテリ接続時間サブカウント　0クリア

                    if( g_eeprom_data.cumulative_data.total_batt_hour < UINT16_MAX_VALUE )    // 最大値以上なら最大値固定
                    {
                        g_eeprom_data.cumulative_data.total_batt_hour++;
                    }
                }
            }
        }

        // 8. バッテリ総放電回数(BATT_DISCHARGE_COUNT)
        if( gu8_f_dischg_start_sek == 1 )
        {
            gu8_f_dischg_start_sek = 0;

            if( g_eeprom_data.cumulative_data.batt_discharge_count < UINT16_MAX_VALUE )    // 最大値以上なら最大値固定
            {
                g_eeprom_data.cumulative_data.batt_discharge_count++;
            }
        }

        // 9. バッテリ総充電回数(BATT_CHARGE_COUNT)
        if( gu8_f_full_chg_sek == 1 )
        {
            gu8_f_full_chg_sek = 0;

            if( g_eeprom_data.cumulative_data.batt_charge_count < UINT12_MAX_VALUE )    // 最大値以上なら最大値固定
            {
                g_eeprom_data.cumulative_data.batt_charge_count++;
            }
        }

        // 10.バッテリ総放電量(BATT_TTL_DISCHARGE)
        // 11.バッテリ総充電量(BATT_TTL_CHARGE)
        if( gu8_f_soc_calc_finish_sek == 1 )    // 充電中
        {
            gu8_f_soc_calc_finish_sek = 0;

            if( (g_eeprom_data.cumulative_data.batt_ttl_charge + gf_chg_mah_val_sek) < UINT24_F__MAX_VALUE_UNDER)
            {
                g_eeprom_data.cumulative_data.batt_ttl_charge += gf_chg_mah_val_sek;
            }
            else
            {
                g_eeprom_data.cumulative_data.batt_ttl_charge = UINT24_F__MAX_VALUE_UNDER;    // 最大値以上なら最大値固定
            }

            gf_chg_mah_val_sek = 0;    // 無くてもいい
        }
        else if(  gu8_f_soc_calc_finish_sek == 2 )    // 放電中
        {
            gu8_f_soc_calc_finish_sek = 0;

            if( (g_eeprom_data.cumulative_data.batt_ttl_discharge + gf_dischg_mah_val_sek) < UINT24_F__MAX_VALUE_UNDER)
            {
                g_eeprom_data.cumulative_data.batt_ttl_discharge += gf_dischg_mah_val_sek;
            }
            else
            {
                g_eeprom_data.cumulative_data.batt_ttl_discharge = UINT24_F__MAX_VALUE_UNDER;    // 最大値以上なら最大値固定
            }

            gf_dischg_mah_val_sek = 0.0;    // 無くてもいい
        }


      if(gu8_f_batt_not_con==0)
      {
        // 12.バッテリ積算温度(TOTAL_BATT_TEMP) &
        // 13.バッテリ平均温度(BATT_TEMP_AVE)
        if( ++gu32_c_bat_temp_ave_sek >= TIMER_1hour )
        {
            gu32_c_bat_temp_ave_sek = 0;

            if( gu8_c_bat_temp_1h_sum_sample > 0 )    // データ数0の場合のゼロ除算対策
            {
                if( (g_eeprom_data.cumulative_data.total_batt_temp + (gu16_bat_temp_1h_sum / gu8_c_bat_temp_1h_sum_sample)) <= UINT24_MAX_VALUE_UNDER )
                {
                    g_eeprom_data.cumulative_data.total_batt_temp += ( gu16_bat_temp_1h_sum / gu8_c_bat_temp_1h_sum_sample );

                    if( g_eeprom_data.cumulative_data.batt_temp_sample_count < UINT24_MAX_VALUE_UNDER )
                    {
                        g_eeprom_data.cumulative_data.batt_temp_sample_count++;    // サンプル数データがe2pにできたらコメント開放
                    }
                }
                else
                {
                    g_eeprom_data.cumulative_data.total_batt_temp = UINT24_MAX_VALUE_UNDER;    // 最大値以上なら最大値固定
                }
            }
            else
            {
                g_eeprom_data.cumulative_data.total_batt_temp += 0;    // 必要？
            }

            gu16_bat_temp_1h_sum = 0;
            gu8_c_bat_temp_1h_sum_sample = 0;

            if( g_eeprom_data.cumulative_data.batt_temp_sample_count > 0 )    // データ数0の場合のゼロ除算対策
            {
                if( (int)((g_eeprom_data.cumulative_data.total_batt_temp / g_eeprom_data.cumulative_data.batt_temp_sample_count)) > INT8_MAX_VALUE )    // 次に求まる平均値が有効範囲外の場合
                {
                    g_eeprom_data.cumulative_data.batt_temp_ave = INT8_MAX_VALUE;
                }
                else if( (int)((g_eeprom_data.cumulative_data.total_batt_temp / g_eeprom_data.cumulative_data.batt_temp_sample_count)) < INT8_MIN_VALUE )    // 次に求まる平均値が有効範囲外の場合
                {
                    g_eeprom_data.cumulative_data.batt_temp_ave = INT8_MIN_VALUE;
                }
                else   // 次に求まる平均値が有効範囲内の場合
                {
                    g_eeprom_data.cumulative_data.batt_temp_ave = ( g_eeprom_data.cumulative_data.total_batt_temp / g_eeprom_data.cumulative_data.batt_temp_sample_count );    // サンプル数データがe2pにできたらコメント開放
                }
            }
        }

        // 14.バッテリ最高温度(BATT_TEMP_MAX)
        if( gu8_c_batt_temp_reference_ok <= BATT_TEMP_SANSHOU_CO )
        {
            gu8_c_batt_temp_reference_ok++;
        }

        if( gu8_c_batt_temp_reference_ok > BATT_TEMP_SANSHOU_CO )
        {
            if( ((gi16_ad_battery_temp + 5) / 10 ) > g_eeprom_data.cumulative_data.batt_temp_max )
            {
                if( ((gi16_ad_battery_temp + 5) * 0.1) > INT8_MAX_VALUE )    // 次に求まる最高温度が有効範囲外の場合
                {
                    g_eeprom_data.cumulative_data.batt_temp_max = INT8_MAX_VALUE;
                }
                else    //　※初期値以下に下がることは無いため、下側有効範囲処理は実装していない
                {
                    g_eeprom_data.cumulative_data.batt_temp_max = (gi16_ad_battery_temp + 5) * 0.1;    // (バッテリ温度(単位:0.1℃) + 0.5℃ / 10) <-- 四捨五入し単位を1℃に変更
                }
            }
        }

        // 15.バッテリ最低温度(BATT_TEMP_MIN)    // ※E2Pでの初期値は0x7Fにしていただく
        if( gu8_c_batt_temp_reference_ok >= BATT_TEMP_SANSHOU_CO )
        {
            if( ((gi16_ad_battery_temp + 5) / 10 ) < g_eeprom_data.cumulative_data.batt_temp_min )
            {
                if( ((gi16_ad_battery_temp + 5) * 0.1) < INT8_MIN_VALUE )    // 次に求まる最低温度が有効範囲外の場合
                {
                    g_eeprom_data.cumulative_data.batt_temp_min = INT8_MIN_VALUE;
                }
                else    //　※初期値以上に上がることは無いため、上側有効範囲処理は実装していない
                {
                    g_eeprom_data.cumulative_data.batt_temp_min = (gi16_ad_battery_temp + 5) * 0.1;    // (バッテリ温度(単位:0.1℃) + 0.5℃ / 10) <-- 四捨五入し単位を1℃に変更
                }
            }
        }
      }
  }
}

/*******************************************************************************
* Function Name: off_time_data_proc()
* Description  : OFF期間データ処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
#define OFF_TIME_DATA_BATT_TEMP_CO 6      // 1分ごとサンプルし6分ごと平均化
#define OFF_TIME_DATA_SEK_CYCLE 360000    // OFF期間データ積算周期(6m)

void off_time_data_proc(void)
{
    // 1. AC_OFF合計時間
    if( (gu8_f_cmd_sc_recv == _ON_) && ( gu8_f_otd_old_set_clk_cmd == _OFF_ ) )
    {
        gu8_f_otd_ac_off_time_en = _ENABLE_;
    }
    else
    {
        gu8_f_otd_ac_off_time_en = _DISABLE_;
    }
    gu8_f_otd_old_set_clk_cmd = gu8_f_cmd_sc_recv;

    if( gu8_f_otd_ac_off_time_en == _ENABLE_ )    // SET_CLOCKコマンド受信時(電源起動後)
    {
        if( gt_otd_ac_off_occurrence != 0 )    // ROM初期化後以外を参照する
        {
            g_eeprom_data.off_period_data.ac_off_hour_sub += (gt_otd_ac_on_time - gt_otd_ac_off_occurrence);    // AC_OFF合計時間(サブ):s単位
        }
        else
        {
            g_eeprom_data.off_period_data.ac_off_hour_sub = 0;
        }

        if( g_eeprom_data.off_period_data.ac_off_hour_sub >= 360 )
        {
            if( ((g_eeprom_data.off_period_data.ac_off_hour + g_eeprom_data.off_period_data.ac_off_hour_sub) / 360) <= UINT16_MAX_VALUE )
            {
                g_eeprom_data.off_period_data.ac_off_hour += (g_eeprom_data.off_period_data.ac_off_hour_sub / 360);    // 1.AC_OFF合計時間(単位:s-->0.1h変換)
            }
            else
            {
                g_eeprom_data.off_period_data.ac_off_hour = UINT16_MAX_VALUE;    // 1.AC_OFF合計時間(単位:s-->0.1h変換)
            }

            g_eeprom_data.off_period_data.ac_off_hour_sub = (g_eeprom_data.off_period_data.ac_off_hour_sub % 360);    // AC_OFF時間積算後、残った端数を記憶する
        }
    }

    // 2. PS_OFF合計時間
    // 3. PS_OFF中のバッテリ平均温度
    if( (gu8_f_ps_on == _OFF_) && ( gu8_f_charging_active == _OFF_) )    // PS_OFFかつ非充電時に有効
    {
        if( ++gu16_c_otd_ps_off_bat_temp_ave >= TIMER_60s )    // 温度サンプリング(1分周期)
        {
            gu16_c_otd_ps_off_bat_temp_ave = 0;
            gi16_otd_ps_off_bat_temp_ave += gi16_ad_battery_temp;
        }

        if( ++g_eeprom_data.off_period_data.ps_off_hour_sub >= OFF_TIME_DATA_SEK_CYCLE )    // 0.1h周期
        {
            g_eeprom_data.off_period_data.ps_off_hour_sub = 0;

            if(g_eeprom_data.off_period_data.ps_off_hour < UINT16_MAX_VALUE)
            {
                g_eeprom_data.off_period_data.ps_off_hour++;    // 2.PS_OFF合計時間(0.1h)
            }

            if( ((gi16_otd_ps_off_bat_temp_ave / OFF_TIME_DATA_BATT_TEMP_CO) <= 1270)
             && ((gi16_otd_ps_off_bat_temp_ave / OFF_TIME_DATA_BATT_TEMP_CO) >= -1280) )    // PS_OFF中のバッテリ平均温度が範囲内
            {
                g_eeprom_data.off_period_data.ave_off_temp = (gi16_otd_ps_off_bat_temp_ave / OFF_TIME_DATA_BATT_TEMP_CO) * 0.1;    // 3.PS_OFF中のバッテリ平均温度(単位:0.1℃-->1℃変換)
            }
            else if( (gi16_otd_ps_off_bat_temp_ave / OFF_TIME_DATA_BATT_TEMP_CO) > 1270 )    // PS_OFF中のバッテリ平均温度が範囲超過
            {
                g_eeprom_data.off_period_data.ave_off_temp = INT8_MAX_VALUE;    // 3.PS_OFF中のバッテリ平均温度
            }
            else    // PS_OFF中のバッテリ平均温度が範囲未満
            {
                g_eeprom_data.off_period_data.ave_off_temp = INT8_MIN_VALUE;    // 3.PS_OFF中のバッテリ平均温度
            }
            gi16_otd_ps_off_bat_temp_ave = 0;
        }
    }

    // 4. バッテリ充電合計時間
    // 5. 充電中のバッテリ平均温度
    if((gu8_f_ps_on == _OFF_)&&(gu8_f_charging_active == _ON_))    // 充電時に有効
    {
        if( ++gu16_c_otd_chg_bat_temp_ave >= TIMER_60s )    // 温度サンプリング(1分周期)
        {
            gu16_c_otd_chg_bat_temp_ave = 0;
            gi16_otd_chg_bat_temp_ave += gi16_ad_battery_temp;
        }

        if( ++g_eeprom_data.off_period_data.off_charge_hour_sub >= OFF_TIME_DATA_SEK_CYCLE )    // 0.1h周期
        {
            g_eeprom_data.off_period_data.off_charge_hour_sub = 0;

            if(g_eeprom_data.off_period_data.off_charge_hour < UINT12_MAX_VALUE)
            {
                g_eeprom_data.off_period_data.off_charge_hour++;    // 4.バッテリ充電合計時間(0.1h)
            }

            if( ((gi16_otd_chg_bat_temp_ave / OFF_TIME_DATA_BATT_TEMP_CO) <= 1270)
             && ((gi16_otd_chg_bat_temp_ave / OFF_TIME_DATA_BATT_TEMP_CO) >= -1280) )    // 充電中のバッテリ平均温度が範囲内(単位:0.1℃)
            {

                g_eeprom_data.off_period_data.ave_charge_temp = (gi16_otd_chg_bat_temp_ave / OFF_TIME_DATA_BATT_TEMP_CO) * 0.1;    // 5.充電中のバッテリ平均温度(単位:0.1℃-->1℃変換)
            }
            else if( (gi16_otd_chg_bat_temp_ave / OFF_TIME_DATA_BATT_TEMP_CO) > 1270 )    // 充電中のバッテリ平均温度が範囲超過
            {
                g_eeprom_data.off_period_data.ave_charge_temp = INT8_MAX_VALUE;    // 5.充電中のバッテリ平均温度
            }
            else    // PS_OFF中のバッテリ平均温度が範囲未満
            {
                g_eeprom_data.off_period_data.ave_charge_temp = INT8_MIN_VALUE;    // 5.充電中のバッテリ平均温度
            }
            gi16_otd_chg_bat_temp_ave = 0;
        }
    }

    // 6. バッテリ総充電量
    if( (gu8_f_ps_on == _OFF_)&&(gu8_f_otd_chg_soc_calc_fin == _ON_) )    // 充電量計算後に有効(充電量計算:1s周期)
    {
        gu8_f_otd_chg_soc_calc_fin = _OFF_;

        if( (gf_otd_chg_soc_total + gf_otd_chg_soc_now) <= 49000.0 )    // バッテリ総充電量が範囲内(≦1000%)
        {
            gf_otd_chg_soc_total += gf_otd_chg_soc_now;

            g_eeprom_data.off_period_data.off_charge = gf_otd_chg_soc_total / 49;    // 6.バッテリ総充電量(単位:mAh-->%変換)
        }
        else    // バッテリ総充電量が範囲超過
        {
            gf_otd_chg_soc_total = 49000.0;
            g_eeprom_data.off_period_data.off_charge = 1000;    // 6.バッテリ総充電量
        }
    }

    // 7. バッテリ劣化度
    if( gu8_f_otd_batt_deg_set == _ON_ )
    {
        gu8_f_otd_batt_deg_set = _OFF_;

        g_eeprom_data.off_period_data.batt_deg = g_eeprom_data.set_life.batt_deg;    // 7.バッテリ劣化度
    }
}

/*******************************************************************************
* Function Name: life_calc_data_proc()
* Description  : 寿命計算データ処理(一部常時監視が必要な処理のみ。それ以外はD0,D3コマンド受信時にセット＆レスポンス)
* Arguments    : None
* Return Value : None
*******************************************************************************/
void life_calc_data_proc(void)
{
    // 3. バッテリ充電量
    if( gu8_f_jcd_chg_soc_calc_fin == _ON_ )
    {
        gu8_f_jcd_chg_soc_calc_fin = _OFF_;

        if( (gf_jcd_ttl_chg_soc + gf_jcd_chg_soc_now) <= 12495.0 )    // 12495 <-- 4900 * 255%
        {
            gf_jcd_ttl_chg_soc += gf_jcd_chg_soc_now;
            gs_life_calc_data.batt_charge = gf_jcd_ttl_chg_soc / 49;
        }
        else
        {
            gf_jcd_ttl_chg_soc = 12495.0;
            gs_life_calc_data.batt_charge = UINT8_MAX_VALUE;
        }
    }
}

/*******************************************************************************
* Function Name: get_data2_proc()
* Description  : GET_DATA2データ処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void get_data2_proc(void)
{
    if( (gu8_f_ps_on == _OFF_) || (gu8_f_ac_on == _OFF_) )    // AC_OFFまたはPS_OFFのとき
    {
        gu8_f_off_time_data_clear_en = _DISABLE_;    // OFF期間データクリア無効
    }
}

/*******************************************************************************
* Function Name: charge_ready_proc()
* Description  : 充電待ち状態監視処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
#define _CHARGE_OFF_CLEAR_  0    // CHARGE_OFFコマンド　充電停止クリア
#define _CHARGE_OFF_KINSHI_ 1    // CHARGE_OFFコマンド　全バッテリ充電停止(強制充電停止状態)
void charge_ready_proc(void)
{
    if(SP_AUTO_CHARGE == _DISABLE_)
    {

      if(gu8_f_charge_off == _CHARGE_OFF_KINSHI_)
      {
        set_info_evt_errlog(FLAG_CHARGE_READY,_RESET_);

      }else if(gu8_f_charge_off == _CHARGE_OFF_CLEAR_){

        set_info_evt_errlog(FLAG_CHARGE_READY,_SET_);
      }
    }else{

        set_info_evt_errlog(FLAG_CHARGE_READY,_RESET_);
    }

    if(gu8_f_backup_active==_ON_){
        set_info_evt_errlog(FLAG_CHARGE_READY,_RESET_);

    }

}

/*******************************************************************************
* Function Name: set_info_evt_errlog()
* Description  : 状態情報/イベント/エラーログ設定処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void set_info_evt_errlog( uint8_t flag, uint8_t status )
{
    //static uint8_t flag_old = 0;
    //static uint8_t status_old = 0;
	uint8_t error_no =0;

    if( (flag != gu8_flag_old) || (status != gu8_status_old) )
    {
        switch( flag )
        {
            case FLAG_PS_ON:          // PS_ON信号オン
                INFO_SIGNAL_STATUS_PS_ON = status;     // 状態情報
                break;

            case FLAG_BURST_ON:       // BURST信号オン
                INFO_SIGNAL_STATUS_BURST_ON = status;     // 状態情報
                break;

            case FLAG_BURST:          // BURST有効
                INFO_COMMAND_STATUS1_BURST = status;
                break;

            case FLAG_PS_OFF_CHARGE:  // PS_OFF_CHARGE有効
                INFO_COMMAND_STATUS1_PS_OFF_CHARGE = status;     // 状態情報
                break;

            case FLAG_RESTART_READY:  // RESTART待ち状態
                INFO_COMMAND_STATUS1_RESTART_READY = status;     // 状態情報
                break;

            case FLAG_BACKUP_READY:   // バックアップ可能状態
                INFO_COMMAND_STATUS1_BACKUP_READY = status;     // 状態情報
                break;

            case FLAG_CHARGE_READY:   // 充電待ち受け状態
                INFO_COMMAND_STATUS2_CHARGE_READY = status;     // 状態情報
                break;

            case FLAG_BATT_CHECK:     // BATT CHECKコマンド実行中
                INFO_COMMAND_STATUS2_BATT_CHECK = status;     // 状態情報
                break;

            case FLAG_CMD_CHARGE_OFF:     // CHARGE OFFコマンド実行中
                INFO_COMMAND_STATUS2_CHARGE_OFF = status;     // 状態情報
                break;

            case FLAG_CMD_CHARGE_ON:       // CHARGE ONコマンド実行中
                INFO_COMMAND_STATUS2_CHARGE_ON = status;     // 状態情報
                break;
#if 0
            case FLAG_CHARGE_READY:

                INFO_COMMAND_STATUS2_CHARGE_READY=status;
                break;
#endif
            case FLAG_BATT_ON:         // バックアップ中
                INFO_BACKUP_STATUS_BATT_ON = status;     // 状態情報
                EVT_BACKUP_STATUS_BATT_ON = status;      // イベントDATA
                break;

            case FLAG_BATT_LOW:        // バッテリ容量低下
                INFO_BACKUP_STATUS_BATT_LOW = status;     // 状態情報
                EVT_BACKUP_STATUS_BATT_LOW = status;      // イベントDATA
                break;

            case FLAG_S_CHARGE_ON:     // 補充電中
                INFO_CHARGE_STATUS_S_CHARGE_ON = status;     // 状態情報
                break;

            case FLAG_CHARGE_OK:       // 充電完了
                INFO_CHARGE_STATUS_CHARGE_OK = status;     // 状態情報
                EVT_CHARGE_STATUS_CHARGE_OK = status;      // イベントDATA
                break;

            case FLAG_CHG_CHARGE_ON:       // 充電中
                INFO_CHARGE_STATUS_CHARGE_ON = status;     // 状態情報
                EVT_CHARGE_STATUS_CHARGE_ON = status;      // イベントDATA
                break;

            case FLAG_ADU_TEMP_WNG:    // ADU部温度警告検出時
                INFO_ADU_WARNING_ADU_TEMP_WNG = status;     // 状態情報
                EVT_ADU_WARNING_ADU_TEMP_WNG = status;      // イベントDATA
                // ERROR LOG(17)    // ERROR LOGは発生側しかLOGしない
        	    error_no = 17;
                break;

            case FLAG_ADU_LIFE_WNG:    // 電源寿命警告検出時
                EVT_ADU_WARNING_ADU_LIFE_WNG = status;      // イベントDATA
                // ERROR LOG(21)
            	error_no = 21;
                break;

            case FLAG_FAN_FAIL:        // ファン破損検出時
                INFO_ADU_ALM1_FAN_FAIL = status;     // 状態情報
                EVT_ADU_ALM_FAN_FAIL = status;       // イベントDATA
                // ERROR LOG(25)
        	    error_no = 25;
                break;

            case FLAG_PFC_OV:          // PFC過電圧
                INFO_ADU_ALM1_PFC_OV = status;     // 状態情報
                EVT_ADU_ALM_PFC_OV = status;       // イベントDATA
                // ERROR LOG(26)
        	    error_no = 26;
                break;

            case FLAG_BBU_TEMP_WNG:    // BBU温度警告検出時
                INFO_BBU_WARNING_BBU_TEMP_WNG = status;     // 状態情報
                EVT_BBU_WARNING_BBU_TEMP_WNG = status;      // イベントDATA
                // ERROR LOG(18)
        	    error_no = 18;
                break;

            case FLAG_BBU_FAIL:        // BBU破損検出時
                INFO_BBU_ALM_BBU_FAIL = status;     // 状態情報
                EVT_BBU_ALM_BBU_FAIL = status;      // イベントDATA
                // ERROR LOG(29)
        	    error_no = 29;
                break;

            case FLAG_CHG_LV:          // 充電回路不足電圧検出時
                INFO_BBU_ALM_CHG_LV = status;     // 状態情報
                EVT_BBU_ALM_CHG_LV = status;      // イベントDATA
                // ERROR LOG(13)
        	    error_no = 13;
                break;

            case FLAG_CHG_OV:          // 充電回路過電圧検出時
                INFO_BBU_ALM_CHG_OV = status;     // 状態情報
                EVT_BBU_ALM_CHG_OV = status;      // イベントDATA
                // ERROR LOG(12)
        	    error_no = 12;
                break;

            case FLAG_CHG_OC:          // 充電回路過電流検出時
                INFO_BBU_ALM_CHG_OC = status;     // 状態情報
                EVT_BBU_ALM_CHG_OC = status;      // イベントDATA
                // ERROR LOG(14)
        	    error_no = 14; 
                break;

            case FLAG_BATT_TEMP_WNG:   // バッテリ温度警告検出時
                INFO_BATT_WARNING_BATT_TEMP_WNG = status;     // 状態情報
                EVT_BATT_WARNING_BATT_TEMP_WNG = status;      // イベントDATA
                // ERROR LOG(1)
        	    error_no = 1;
                break;

            case FLAG_BATT_TEMP_ALM:   // バッテリ温度異常検出時
                INFO_BATT_ALM1_BATT_TEMP_ALM = status;     // 状態情報
                EVT_BATT_ALM1_BATT_TEMP_ALM = status;      // イベントDATA
                // ERROR LOG(4)
        	    error_no = 4;
                break;

            case FLAG_BATT_LV:         // バッテリ電圧低下時検出時
                INFO_BATT_ALM1_BATT_LV = status;     // 状態情報
                EVT_BATT_ALM1_BATT_LV = status;      // イベントDATA
                // ERROR LOG(5)
        	    error_no = 5;
                break;

            case FLAG_BATT_OV:         // バッテリ過電圧時検出時
                INFO_BATT_ALM1_BATT_OV = status;     // 状態情報
                EVT_BATT_ALM1_BATT_OV = status;      // イベントDATA
                // ERROR LOG(6)
        	    error_no = 6;
                break;

            case FLAG_BATT_LIFE:       // バッテリ寿命検出時
                INFO_BATT_ALM2_BATT_LIFE = status;     // 状態情報
                EVT_BATT_ALM2_BATT_LIFE = status;      // イベントDATA
                // ERROR LOG(7)
        	    error_no = 7;
                break;

            case FLAG_BATT_MCN:        // バッテリ誤接続検出時
                INFO_BATT_ALM2_BATT_MCN = status;     // 状態情報
                EVT_BATT_ALM2_BATT_MCN = status;      // イベントDATA
                // ERROR LOG(28)
        	    error_no = 28;
                break;

            case FLAG_BATT_P_FAIL:     // バッテリ保護回路破損検出時
                INFO_BATT_ALM2_BATT_P_FAIL = status;     // 状態情報
                EVT_BATT_ALM2_BATT_P_FAIL = status;      // イベントDATA
                // ERROR LOG(2)
        	    error_no = 2;
                break;

            case FLAG_BATT_DCN:        // バッテリ未接続検出時
                INFO_BATT_ALM2_BATT_DCN = status;     // 状態情報
                EVT_BATT_ALM2_BATT_DCN = status;      // イベントDATA
                // ERROR LOG(3)
        	    error_no = 3;
                break;

            case FLAG_12V_OV:          // 12V過電圧検出時
                INFO_ADU_ALM2_12V_OV = status;     // 状態情報
                // ERROR LOG(8)
        	    error_no = 8;
                break;

            case FLAG_12V_LV:          // 12V不足電圧検出時
                INFO_ADU_ALM2_12V_LV = status;     // 状態情報 2026/5/26
                // ERROR LOG(9)
        	    error_no = 9;
                break;

            case FLAG_12V_OC:          // 12V過電流検出時
                INFO_ADU_ALM2_12V_OC = status;     // 状態情報
                // ERROR LOG(10)
        	    error_no = 10;
                break;

            case FLAG_12V_OC_OFF:      // 12V PS_OFF過電流検出時
                INFO_ADU_ALM2_12V_OC_OFF = status;
                // ERROR LOG(11)
        	    error_no = 11;
                break;

            case FLAG_BATT_OC:         // バッテリ放電過電流
                // ERROR LOG(15)
        	    error_no = 15;
                break;

            case FLAG_12V_OC_OFF_H:         // バッテリ放電過電流
                INFO_ADU_ALM1_12V_OC_OFF_H= status;
                EVT_ADU_ALM_12V_OC_OFF_H  =status;
                error_no = 16;                                       //2026/8/20
                break;

            case FLAG_ADU_TEMP_ALM:    // AC/DC 温度異常
                // ERROR LOG(19)
        	    error_no = 19;
                break;

            case FLAG_BBU_TEMP_ALM:    // BACKUP 温度異常
                // ERROR LOG(20)
        	    error_no = 20;
                break;

            case FLAG_FAN_LOW:         // ファン回転低下
                INFO_ADU_WARNING_FAN_WNG = status;     // 状態情報
                EVT_ADU_WARNING_FAN_WNG = status;      // イベントDATA
                // ERROR LOG(22)
        	    error_no = 22;
                break;

            case FLAG_FAN_HIGH:        // ファン回転上昇
                INFO_ADU_WARNING_FAN_WNG = status;     // 状態情報
                EVT_ADU_WARNING_FAN_WNG = status;      // イベントDATA
                // ERROR LOG(23)
                error_no = 23;
                break;

            case FLAG_FAN_STOP:        // ファン回転停止
                INFO_ADU_WARNING_FAN_WNG = status;     // 状態情報
                EVT_ADU_WARNING_FAN_WNG = status;      // イベントDATA
                // ERROR LOG(24)
                error_no = 24;
               break;

            case FLAG_BBU_SW_ST:       // FEW_SW ショート
                INFO_BBU_ALM_BBU_FAIL = status;     // 状態情報
                EVT_BBU_ALM_BBU_FAIL = status;      // イベントDATA
                // ERROR LOG(30)
                error_no = 30;
                break;

            case FLAG_BBU_SW_OP:       // FET_SW オープン
                INFO_BBU_ALM_BBU_FAIL = status;     // 状態情報
                EVT_BBU_ALM_BBU_FAIL = status;      // イベントDATA
                // ERROR LOG(31)
                error_no = 31;
                break;

            case FLAG_WDT:       // FET_SW オープン

                error_no = 32;
                break;


            case FLAG_COM_ALM:         // 通信異常 （各種通信エラーに細分化可能なコードを有する）
        	error_no = flag;
                break;
                // ERROR LOG(status)

            default:
                break;
        }
    	if( error_no != 0 )
               {
                   if( error_no < FLAG_COM_ALM )
                   {
                       if( status == _SET_ ) // _SET_
                       {
                           if( gu8_b_err_log[flag] == 0 )   // flag_a[100]
                           {
                               gu8_b_err_log[flag]=1;
                               //flag_a[flag] = 1;
                               error_log_request(error_no);
                           }
                       } else { // _RESET_
                           gu8_b_err_log[flag]=0;
                       }
                   } else {
                       error_log_request(error_no);
                   }
               }
    }
    gu8_flag_old = flag;
    gu8_status_old = status;
}










