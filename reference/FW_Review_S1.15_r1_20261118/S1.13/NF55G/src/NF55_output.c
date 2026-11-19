#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"

void output(void);
void output_io(void);
void output_converter_pwm(void);
void converter_pwm_start(void);
void converter_pwm_stop(void);
void output_fan_pwm(void);
void fan_pwm_ctl(void);
void fan_stop_PWM(void);
void fan_speed_proc(void);
void set_fan_speed( uint8_t speed );
void ac_link_proc(void);

extern void set_info_evt_errlog( uint8_t flag, uint8_t status );

// FAN制御用(PWM)
void fan_rpm_calc_proc(void);
void fan_hosei_temp_proc(void);
void fan_wng_fail_proc(void);
void fan_duty_set_proc(void);
void restart_flg_proc(void);
uint16_t get_fan_target_duty_cnt(uint8_t mode_flg);
uint16_t get_fan_target_duty_per(uint8_t mode_flg);
uint16_t get_fan_target_rpm(uint8_t mode_flg);
void    set_output_duty(float count);

//static  uint16_t    su16_c_sta_rpm = 0;

//static  uint8_t     su8_f_sta_fan = 0;

//static  uint8_t     su8_now_spd = 0;
//static  uint8_t     su8_new_spd = 0;

//static  uint16_t    su16_now_rpm = 0;
//static  uint16_t    su16_now_per = 0;

//static  uint16_t    su16_new_rpm = 0;
//static  uint16_t    su16_new_dty = 0;
//static  uint16_t    su16_new_per = 0;

//static  uint16_t    su16_max_rpm = 0;
//static  uint16_t    su16_min_rpm = 0;

//static  float       sf_max_per = 0;
//static  float       sf_min_per = 0;

//static  uint16_t    su16_adj_dty = 0;
//static  float       sf_adj_per = 0;

#ifdef _HIS_ENABLE_MODE_
#define SIZ_U16_HIS 4800
uint16_t su16_b_his[SIZ_U16_HIS];
uint16_t su16_p_u16his = 0;

void his_temp(uint16_t dat)
{
    su16_b_his[su16_p_u16his] = dat;
    if (su16_p_u16his < (SIZ_U16_HIS - 1))
    {
        ++su16_p_u16his;
    }
}
#endif
#ifdef _HIS_ENABLE_MODE_
#define SIZ_U8_HIS 30
uint16_t su16_b_his3[SIZ_U8_HIS];
uint16_t su16_p_u8his = 0;

void his_temp3(uint16_t dat)
{
    su16_b_his3[su16_p_u8his] = dat;
    if (su16_p_u8his < (SIZ_U8_HIS - 1))
    {
        ++su16_p_u8his;
    }
}
#endif
/*******************************************************************************
* Function Name: output()
* Description  : 出力処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void output(void)
{
	if(gu8_f_before_shutdown!=1)
	{
	    fan_speed_proc();        // FAN回転判定処理

    	ac_link_proc();          // AC_LINK処理


    	output_io();   // I/O 出力処理


    	output_converter_pwm();  // コンバーターPWM 出力処理

    	output_fan_pwm();        // FAN PWM 出力処理
	
	}

}

/*******************************************************************************
* Function Name: output_io()
* Description  : I/O 出力処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void output_io(void)
{
    // DISCHG12V_EN ON/OFF
    if( gu8_f_dischg12v_en_out != _OUT_NOT_ )
    {
        if( gu32_c_dischg12v_en_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_dischg12v_en_out == _OUT_ON_)
            {
                O_DISCHG12V_EN_H;
            }
            else
            {
                O_DISCHG12V_EN_L;
            }
            gu8_f_dischg12v_en_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_dischg12v_en_out_delay--;
        }
    }

    // CHGV_11.4V ON/OFF
    if( gu8_f_chgv_114v_out != _OUT_NOT_ )
    {
        if( gu32_c_chgv_114v_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_chgv_114v_out == _OUT_ON_)
            {
                O_CHGV_11_4V_H;   // 11.4V
            }
            else
            {
                O_CHGV_11_4V_L;   // 10.8V
            }
            gu8_f_chgv_114v_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_chgv_114v_out_delay--;
        }
    }

    // /BATCHG_EN ON/OFF
    if( gu8_f_batchg_en_out != _OUT_NOT_ )
    {
        if( gu32_c_batchg_en_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_batchg_en_out == _OUT_ON_)
            {
                O_BATCHG_EN_L;   // ONで"L"
            }
            else
            {
                O_BATCHG_EN_H;
            }
            //gu8_f_batchg_en_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_batchg_en_out_delay--;
        }
    }

    // VCC_12V_EN ON/OFF
    if( gu8_f_vcc_12v_en_out != _OUT_NOT_ )
    {
        if( gu32_c_vcc_12v_en_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_vcc_12v_en_out == _OUT_ON_)
            {
                O_VCC_12V_EN_H;
            }
            else
            {
                O_VCC_12V_EN_L;
            }
            gu8_f_vcc_12v_en_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_vcc_12v_en_out_delay--;
        }
    }

    // BATT_EN ON/OFF
    if( gu8_f_batt_en_out != _OUT_NOT_ )
    {
        if( gu32_c_batt_en_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_batt_en_out == _OUT_ON_)
            {
                O_BATT_EN_H;
            }
            else
            {
                O_BATT_EN_L;
            }
            gu8_f_batt_en_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_batt_en_out_delay--;
        }
    }

    // /12V_EN ON/OFF
    if( gu8_f_12v_en_out != _OUT_NOT_ )
    {
        if( gu32_c_12v_en_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_12v_en_out == _OUT_ON_)
            {
                O_12V_EN_L;   // ONで"L"
            }
            else
            {
                gu32_c_12v_en_out_delay = 0;
                O_12V_EN_H;
            }
            //gu8_f_12v_en_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_12v_en_out_delay--;
        }
    }

    // BURST_OUT ON/OFF
    if( gu8_f_burst_out != _OUT_NOT_ )
    {
        if( gu32_c_burst_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_burst_out == _OUT_ON_)
            {
                O_BURST_OUT_H;
            }
            else
            {
                O_BURST_OUT_L;
            }
            gu8_f_burst_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_burst_out_delay--;
        }
    }

    // /PS_ON ON/OFF
    if( gu8_f_ps_on_out != _OUT_NOT_ )
    {
        if( gu32_c_ps_on_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_ps_on_out == _OUT_ON_)
            {
                O_PS_ON_OUT_L;   // ONで"L"
            }
            else
            {
                O_PS_ON_OUT_H;
            }
            gu8_f_ps_on_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_ps_on_out_delay--;
        }
    }

#if 0
    // TEST_OUT ON/OFF
    if( gu8_f_test_out != _OUT_NOT_ )
    {
        if( gu32_c_test_out_delay == 0 ) // 1ms x N
        {
            if(gu8_f_test_out == _OUT_ON_)
            {
                //O_TEST_OUT_H;
            }
            else
            {
                //O_TEST_OUT_L;
            }
            gu8_f_test_out = _OUT_NOT_;
        }
        else
        {
            gu32_c_test_out_delay--;
        }
    }
#endif
}

/*******************************************************************************
* Function Name: output_converter_pwm()
* Description  : コンバーターPWM 出力処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void output_converter_pwm(void)
{
    if( gu8_f_converter_pwm != _OUT_NOT_ )
    {
        if( gu32_c_converter_pwm_delay == 0 ) // 1ms x N
        {
            if(gu8_f_converter_pwm == _OUT_ON_)
            {
                converter_pwm_start();
            }
            else
            {
                converter_pwm_stop();
            }
            gu8_f_converter_pwm = _OUT_NOT_;
        }
        else
        {
            gu32_c_converter_pwm_delay--;
        }
    }
}

/*******************************************************************************
* Function Name: converter_pwm_start()
* Description  : クロック出力放電コンバータ PWM 開始(200KHz)
* Arguments    : None
* Return Value : None
*******************************************************************************/
#define PHASE_WAIT   38 // 1.667us 5us/3/(1/40M) = 66 調整して38 compiler opt=0
//#define PHASE_WAIT   40 // 1.667us 5us/3/(1/40M) = 66 調整して40 compiler opt=1
//#define PHASE_WAIT   42 // 1.667us 5us/3/(1/40M) = 66 調整して42 compiler opt=2

void converter_pwm_start(void)
{
    // 200KHz
    //DL_TimerG_startCounter(SYNC_0_INST);   // SYNC_0 Start
    SYNC_0_INST->COUNTERREGS.CTRCTL |= (GPTIMER_CTRCTL_EN_ENABLED);
    delay_cycles(PHASE_WAIT);
    //DL_TimerG_startCounter(SYNC_120_INST); // SYNC_120 start
    SYNC_120_INST->COUNTERREGS.CTRCTL |= (GPTIMER_CTRCTL_EN_ENABLED);
    delay_cycles(PHASE_WAIT);
    //DL_TimerG_startCounter(SYNC_240_INST); // SYNC_240 start
    SYNC_240_INST->COUNTERREGS.CTRCTL |= (GPTIMER_CTRCTL_EN_ENABLED);
}

/*******************************************************************************
* Function Name: converter_pwm_stop()
* Description  : クロック出力放電コンバータ PWM 停止
* Arguments    : None
* Return Value : None
*******************************************************************************/
void converter_pwm_stop(void)
{
    // SYNC_0/120/240 PWM Stop
    DL_TimerG_stopCounter(SYNC_0_INST);
    DL_TimerG_stopCounter(SYNC_120_INST);
    DL_TimerG_stopCounter(SYNC_240_INST);
}

/*******************************************************************************
* Function Name: fan_speed_proc()
* Description  : FAN回転判定処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void fan_speed_proc(void)
{
    //static uint8_t f_juudentyu_old = 0;
    //static uint8_t f_backuptyu_old = 0;
    //static uint8_t f_fan_spd_backup = 0;
    //static uint8_t f_fail_adu_bbu = 0;

    if( (gu8_f_fan_fail_adu == _ON_) || (gu8_f_fan_fail_bbu  == _ON_)|| (gu8_f_high_i_of_h==_ON_))  // ADU/BBU 温度警告?
    {
        if( (pi_fan_fail_adu.trg == _TRG_ON_) || (pi_fan_fail_bbu.trg == _TRG_ON_) || (pi_high_i_of_h.trg == _TRG_ON_&&gu8_f_12v_oc_off_h==1))
        {

            gu8_f_fail_adu_bbu = 1;
            gu8_f_fan_spd_backup = f_gu8_fan_speed_def;

            gu8_f_vcc_12v_en_out = _OUT_ON_;   // VCC_12V_EN ON
            set_fan_speed(FAN_MAX_SPEED);      // FAN最大回転
            gu8_f_fan_pwm = _OUT_ON_;
        }
        return;
    }
    else if( (gu8_f_fan_fail_adu == _OFF_) && (gu8_f_fan_fail_bbu == _OFF_)&& (gu8_f_high_i_of_h==_OFF_) )  // ADU/BBU 温度警告なし?
    {
        if( (pi_fan_fail_adu.trg == _TRG_OFF_) || (pi_fan_fail_bbu.trg == _TRG_OFF_)|| (pi_high_i_of_h.trg == _TRG_OFF_&&gu8_f_12v_oc_off_h==0) )
        {


            if( gu8_f_fail_adu_bbu !=0 )
            {
                gu8_f_fail_adu_bbu = 0;
                if( gu8_f_fan_spd_backup != FAN_STOP )
                {
                    gu8_f_vcc_12v_en_out = _OUT_ON_;   // VCC_12V_EN ON
                    gu8_f_fan_pwm = _OUT_ON_;
                } else {
                    gu8_f_vcc_12v_en_out = _OUT_OFF_;  // VCC_12V_EN OFF
                    gu8_f_fan_pwm = _OUT_OFF_;
                }
                set_fan_speed(gu8_f_fan_spd_backup);   // FAN回転復元
            }
        }
    }

    if( pi_ps_on.trg == _TRG_ON_ )        // PS_ON  OFF->ON?
    {
        gu8_f_vcc_12v_en_out = _OUT_ON_;     // VCC_12V_EN ON
        set_fan_speed(FAN_LOW_SPEED);        // FAN低速回転
        gu8_f_fan_pwm = _OUT_ON_;
        if( gu8_f_charging_active != 0 )   // 充電中?
        {
            gu8_f_charging_active_old = 0;
        }
    }
    else if( pi_ps_on.trg == _TRG_OFF_ )   // PS_ON  ON->OFF?
    {
        if( (gu8_f_charging_active == 0) && (gu8_f_backup_active == 0) )  // PS_ON=OFFで未充電/未バックアップ
        {
            gu8_f_vcc_12v_en_out = _OUT_OFF_; // VCC_12V_EN OFF
            set_fan_speed(FAN_STOP);          // FAN停止
            gu8_f_fan_pwm = _OUT_OFF_;
        }
        if( gu8_f_charging_active != 0 )   // 充電中?
        {
            gu8_f_charging_active_old = 0;
        }
    }

    if( gu8_f_charging_active!= gu8_f_charging_active_old ) // 充電変化?
    {

        if( (gu8_f_ps_on == _ON_ ) && (gu8_f_charging_active != 0) )   // PS_ON=ONで充電中
        {
            gu8_f_vcc_12v_en_out = _OUT_ON_;   // VCC_12V_EN ON
            set_fan_speed(FAN_MID_SPEED);      // FAN中速回転
            gu8_f_fan_pwm = _OUT_ON_;
        }
        else if( (gu8_f_ps_on == _OFF_ ) && (gu8_f_charging_active != 0) )  // PS_ON=OFFで充電中
        {
            gu8_f_vcc_12v_en_out = _OUT_ON_;   // VCC_12V_EN ON
            set_fan_speed(FAN_LOW_SPEED);    // FAN低速回転
            gu8_f_fan_pwm = _OUT_ON_;
        }
        //else if( (gu8_f_ps_on == _ON_ ) && (gu8_f_juudentyu == 0) )   // PS_ON=ONで未充電
        else if( (gu8_f_ps_on == _ON_ ) && (gu8_f_charging_active == 0) && (gu8_f_charge_output == _OFF_) )   // PS_ON=ONで未充電 & 放電開始していない hanawa 2026/6/9
        {
            gu8_f_vcc_12v_en_out = _OUT_ON_;   // VCC_12V_EN ON
            set_fan_speed(FAN_LOW_SPEED);      // FAN低速回転
            gu8_f_fan_pwm = _OUT_ON_;
        }
        else if( (gu8_f_ps_on == _OFF_) && (gu8_f_charging_active == 0) && (gu8_f_backup_active == 0) )  // PS_ON=OFFで未充電/未バックアップ
        {
            gu8_f_vcc_12v_en_out = _OUT_OFF_; // VCC_12V_EN OFF
            set_fan_speed(FAN_STOP);          // FAN停止
            gu8_f_fan_pwm = _OUT_OFF_;
        }
    }
    gu8_f_charging_active_old = gu8_f_charging_active;

    if( gu8_f_backup_active != gu8_f_backup_active_old) // バックアップ変化?
    {
        if( gu8_f_backup_active == _ON_ )        // PS_ON=ONでバックアップ中
        {
            gu8_f_vcc_12v_en_out = _OUT_ON_;   // VCC_12V_EN ON
            set_fan_speed(FAN_HIGH_SPEED);     // FAN高速回転
            gu8_f_fan_pwm = _OUT_ON_;
        }
        else if( gu8_f_ps_on == _ON_  )      // PS_ON=ONで未バックアップ中
        {
            if( gu8_f_charging_active == 0 )   // 未充電?
            {
                gu8_f_vcc_12v_en_out = _OUT_ON_;   // VCC_12V_EN ON
                set_fan_speed(FAN_LOW_SPEED);      // FAN低速回転
                gu8_f_fan_pwm = _OUT_ON_;
            }
        }
        else if( (gu8_f_ps_on == _OFF_) && (gu8_f_charging_active == 0) && (gu8_f_backup_active == 0) )  // PS_ON=OFFで未充電/未バックアップ
        {
            gu8_f_vcc_12v_en_out = _OUT_OFF_; // VCC_12V_EN OFF
            set_fan_speed(FAN_STOP);          // FAN停止
            gu8_f_fan_pwm = _OUT_OFF_;
            gu32_c_fan_pwm_delay = TIMER_5ms;
        }
    }
    gu8_f_backup_active_old = gu8_f_backup_active;
}

/*******************************************************************************
* Function Name: set_fan_speed()
* Description  : FAN PWM Duty変更要求
* Arguments    : None
* Return Value : None
*******************************************************************************/
void set_fan_speed( uint8_t speed )
{
    f_gu8_fan_speed_def = speed;
    f_gu8_fan_ctl_mode = _FAN_CTL_DEFAULT_MODE_;
    if( f_gu8_fan_speed_def != f_gu8_fan_speed )
    {
        f_gu8_fan_duty_change = 1;
    }
}

/*******************************************************************************
* Function Name: output_fan_pwm()
* Description  : FAN PWM 出力処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void output_fan_pwm(void)
{
    //static uint8_t f_on = 0;
//#if 1
//#ifdef _DEBUG_ON_
//    gu8_f_fan_pwm = _OUT_ON_;
//#endif
//#endif
    if( gu8_f_fan_pwm != _OUT_NOT_ )
    {
        if(gu8_f_fan_pwm == _OUT_ON_)
        {
            if(gu32_c_fan_pwm_delay == 0 ) // 1ms x N
            {
                fan_pwm_ctl();          // FAN PWM 制御
                gu8_f_on = 1;
            }
            else
            {
                gu32_c_fan_pwm_delay--;
            }
        }
        else if( gu8_f_fan_pwm == _OUT_OFF_)
        {
            if(gu32_c_fan_pwm_delay == 0 ) // 1ms x N
            {
                fan_stop_PWM(); // FAN PWM OFF
                gu8_f_fan_pwm = _OUT_NOT_;
                gu8_f_on = 0;
                f_gu8_fan_speed = 0;  // FAN制御用
                gu8_fan_output_stg = 0;
                gu8_new_spd = 0;

                gu16_d_fan_rpm = 0;
                gu16_d_fan_rpm_old = 0;
                
                gu16_c_fan = 0;
            } else {
                if( gu8_f_on != 0 )
                {
                    fan_pwm_ctl();       // FAN PWM 制御
                }
                gu32_c_fan_pwm_delay--;
            }
        }
    }
}

///*******************************************************************************
//* Function Name: fan_pwm_ctl()
//* Description  : FAN PWM 制御
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
void fan_pwm_ctl(void)
{
    //static uint16_t su16_c_fan = 0;

    if (gu16_c_fan >= 1000)
    {
        fan_rpm_calc_proc();    // rpm計算処理

        fan_hosei_temp_proc();  // FAN補正制御/FAN温度制御

        fan_wng_fail_proc();    // FAN警告/FAN異常

        fan_duty_set_proc();  // FAN出力処理

        /* タコパルス用バッファのポインタをゼロクリアする */
        gu16_p_fanrpm = 0;
        gu16_c_fan = 0;
    }
    else
    {
        ++gu16_c_fan;
    }
}

///*******************************************************************************
//* Function Name: fan_stop_PWM()
//* Description  : FAN PWM 停止
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
void fan_stop_PWM(void)
{
    DL_TimerA_stopCounter(FAN_PWM_INST); // FAN PWM OFF
}

///*******************************************************************************
//* Function Name: fan_rpm_calc_proc()
//* Description  : rpm計算関数
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
void fan_rpm_calc_proc(void)
{
    uint32_t    sum;
    uint8_t     i;
    float       t1;

    // 現状はisr.cにある計算部分をここに移植する。

#if 0    // S1.0
#ifdef _DEBUG_ON_
        //O_TEST_OUT_H;
#endif

    if (gu16_p_fanrpm > 0)
    {
        sum = 0;
        for (i=0; i<gu16_p_fanrpm; ++i)
        {
            sum += gu32_b_fanrpm[i];
        }

        sum = sum / gu16_p_fanrpm;

        t1 = (float)sum * 0.0000001f;   // 1/10MHz
        gu16_d_fan_rpm = (uint16_t)(60.0 / (t1*2.0));
    }
    else
    {
        gu16_d_fan_rpm = 0;
    }

#ifdef _DEBUG_ON_
        //O_TEST_OUT_L;
#endif
#else    // S1.01(仮) rpm平均化用データ数:最大10データに変更(平均化時間の短縮)

        if(gu16_p_fanrpm > 0)
        {
            sum = 0;
            if(gu16_p_fanrpm <= 10)
            {
                for(i=0; i<gu16_p_fanrpm; ++i)
                {
                    sum += gu32_b_fanrpm[i];
                }
                sum = sum / gu16_p_fanrpm;
            }
            else
            {
                for(i=0; i<10; ++i)
                {
                    sum += gu32_b_fanrpm[gu16_p_fanrpm - 1 - i];
                }
                sum = sum / 10;
            }

            t1 = (float)sum * 0.0000001f;   // 1/10MHz
            gu16_d_fan_rpm = (uint16_t)(60.0 / (t1*2.0));
        }
        else
        {
            gu16_d_fan_rpm = 0;
        }



#endif
}


///*******************************************************************************
//* Function Name: fan_hosei_temp_proc()
//* Description  : FAN補正制御/温度制御
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
void fan_hosei_temp_proc(void)
{
#if 0
    if( ++c_gu16_fan_temp_ctl > TIMER_100ms )
    {
        c_gu16_fan_temp_ctl = 0;
#endif
        // 制御基準の温度を選択
        if( gi16_ad_bbu_temp > gi16_ad_llc_temp )
        {
            gi16_ctl_target_temp = gi16_ad_bbu_temp / 10;    // /10のタイミングOK？
        }
        else
        {
            gi16_ctl_target_temp = gi16_ad_llc_temp / 10;    // /10のタイミングOK？
        }

#if 0   // データ取り用
        static uint16_t s_temp_data = 40;
        static uint8_t sf_temp_data = 0; //1で++,0で--
        if(s_temp_data == 90)
        {
            sf_temp_data = 0;
        }
        if(s_temp_data == 40)
        {
            sf_temp_data = 1;
        }
        if(sf_temp_data == 1)
        {
            s_temp_data++;
        }
        else
        {
            s_temp_data--;
        }

        gi16_ctl_target_temp = s_temp_data;
#endif

#if 0
        static char debugyou_variable = FAN_LOW_SPEED;
        static char debugyou_flag = 0;
        static char debugyou_temp = 0;
        gi16_ctl_target_temp = debugyou_temp;
        //gi16_pre_temp = gi16_ctl_target_temp;

        if(debugyou_flag == 1)
        {
            debugyou_flag = 0;
            set_fan_speed(debugyou_variable);
        }
#endif
        // 温度が上昇したか低下したか判断する
        //if( gi16_ctl_target_temp > gi16_pre_temp )    // 温度も不感帯必要?
        if( gi16_ctl_target_temp >= gi16_pre_temp )    // 温度も不感帯必要?
        {
            f_gu8_fan_temp_updwn = _TEMP_UP_;
        }
        else
        {
            f_gu8_fan_temp_updwn = _TEMP_DOWN_;
        }
        gi16_pre_temp = gi16_ctl_target_temp;

        /* for debug */
        //f_gu8_fan_speed_def = FAN_MAX_SPEED;

        // FAN制御_モード選択
        if( f_gu8_fan_ctl_mode == _FAN_CTL_DEFAULT_MODE_ )    // デフォルト回転モード(※閾値を越えたらそのまま温度制御に遷移。f_gu8_fan_duty_changeも遷移先で立つ)
        {
            f_gu8_fan_speed = f_gu8_fan_speed_def;    // ※デフォルト回転モードと温度制御モードの初期値を統一

            switch( f_gu8_fan_speed_def )
            {
                case FAN_LOW_SPEED:
                    if( gi16_ctl_target_temp >= TEMP_LOW_TO_MID )
                    {
                        f_gu8_fan_ctl_mode = _FAN_CTL_TEMP_MODE_;
                    }
                    break;
                case FAN_MID_SPEED:
                    if( gi16_ctl_target_temp >= TEMP_MID_TO_HIGH )
                    {
                        f_gu8_fan_ctl_mode = _FAN_CTL_TEMP_MODE_;
                    }
                    break;
                case FAN_HIGH_SPEED:
                    if( gi16_ctl_target_temp >= TEMP_HIGH_TO_MAX )
                    {
                        f_gu8_fan_ctl_mode = _FAN_CTL_TEMP_MODE_;
                    }
                    break;
                case FAN_MAX_SPEED:
                    break;
                default:
                    break;
            }
        }
        if( f_gu8_fan_ctl_mode == _FAN_CTL_TEMP_MODE_ )       // 温度制御モード
        {
            // 温度により回転モードを決定する(ボリューム一気に変換 --> 温度維持の場合追従できない穴あり。最初の条件に||で温度組み込む（あるいは上昇低下は不要になりうる？）)
            switch( f_gu8_fan_speed )
            {
                case FAN_LOW_SPEED:    // 低速回転モード
                    if( f_gu8_fan_temp_updwn == _TEMP_UP_ )    // 温度が上昇した場合
                    {
                        if( gi16_ctl_target_temp >= TEMP_LOW_TO_MID )
                        {
                            gu16_fan_odr_duty = get_fan_target_duty_per(FAN_MID_SPEED);    // 補正・警告用
                            gu16_fan_odr_rpm = get_fan_target_rpm(FAN_MID_SPEED);          // 補正・警告用
                            f_gu8_fan_speed = FAN_MID_SPEED;
                            f_gu8_fan_duty_change = 1;
                        }
                    }
                    break;

                case FAN_MID_SPEED:    // 中速回転モード
                    if( f_gu8_fan_temp_updwn == _TEMP_UP_ )    // 温度が上昇した場合
                    {
                        if( gi16_ctl_target_temp >= TEMP_MID_TO_HIGH )
                        {
                            gu16_fan_odr_duty = get_fan_target_duty_per(FAN_HIGH_SPEED);    // 補正・警告用
                            gu16_fan_odr_rpm = get_fan_target_rpm(FAN_HIGH_SPEED);          // 補正・警告用
                            f_gu8_fan_speed = FAN_HIGH_SPEED;
                            f_gu8_fan_duty_change = 1;
                        }
                    }
                    else    // 温度が低下した場合
                    {
                        if( f_gu8_fan_speed_def != FAN_MID_SPEED )    // デフォルト回転が中速回転では無い場合
                        {
                            if( gi16_ctl_target_temp <= TEMP_MID_TO_LOW )
                            {
                                gu16_fan_odr_duty = get_fan_target_duty_per(FAN_LOW_SPEED);    // 補正・警告用
                                gu16_fan_odr_rpm = get_fan_target_rpm(FAN_LOW_SPEED);          // 補正・警告用
                                f_gu8_fan_speed = FAN_LOW_SPEED;
                                f_gu8_fan_duty_change = 1;
                            }
                        }
                    }
                    break;

                case FAN_HIGH_SPEED:    // 高速回転モード
                    if( f_gu8_fan_temp_updwn == _TEMP_UP_ )    // 温度が上昇した場合
                    {
                        if( gi16_ctl_target_temp >= TEMP_HIGH_TO_MAX )
                        {
                            gu16_fan_odr_duty = get_fan_target_duty_per(FAN_MAX_SPEED);    // 補正・警告用
                            gu16_fan_odr_rpm = get_fan_target_rpm(FAN_MAX_SPEED);          // 補正・警告用
                            f_gu8_fan_speed = FAN_MAX_SPEED;
                            f_gu8_fan_duty_change = 1;
                        }
                    }
                    else    // 温度が低下した場合
                    {
                        if( f_gu8_fan_speed_def != FAN_HIGH_SPEED )    // デフォルト回転が高速回転では無い場合
                        {
                            if( gi16_ctl_target_temp <= TEMP_HIGH_TO_MID )
                            {
                                gu16_fan_odr_duty = get_fan_target_duty_per(FAN_MID_SPEED);    // 補正・警告用
                                gu16_fan_odr_rpm = get_fan_target_rpm(FAN_MID_SPEED);          // 補正・警告用
                                f_gu8_fan_speed = FAN_MID_SPEED;
                                f_gu8_fan_duty_change = 1;
                            }
                        }
                    }
                    break;

                case FAN_MAX_SPEED:    // 最大回転モード
                    if( f_gu8_fan_temp_updwn == _TEMP_DOWN_ )    // 温度が低下した場合
                    {
                        if( f_gu8_fan_speed_def != FAN_MAX_SPEED )    // デフォルト回転が最大回転では無い場合
                        {
                            if( gi16_ctl_target_temp <= TEMP_MAX_TO_HIGH )
                            {
                                gu16_fan_odr_duty = get_fan_target_duty_per(FAN_HIGH_SPEED);    // 補正・警告用
                                gu16_fan_odr_rpm = get_fan_target_rpm(FAN_HIGH_SPEED);          // 補正・警告用
                                f_gu8_fan_speed = FAN_HIGH_SPEED;
                                f_gu8_fan_duty_change = 1;
                            }
                        }
                    }
                    break;

                default:
                    break;
            }
        }

#ifdef _DEBUG_ON_
        //his_temp((uint16_t)gi16_ctl_target_temp);
        //his_temp((uint16_t)f_gu8_fan_speed);
        //his_temp(gu16_fan_new_pwm_duty); // 要る？
#endif

#if 0       // 補正は一旦置いておく。
        // 補正制御(※とりあえず、警告通知後も動作するものとする(2026/01/27))
        // 補正制御周期は100ms?
        if( gu16_d_fan_rpm < (gu16_fan_odr_rpm - 0) )       // 実rpm < 指令rpm(-不感帯分)のとき
        {

        }
        else if( gu16_d_fan_rpm < (gu16_fan_odr_rpm + 0) )  // 実rpm > 指令rpm(+不感帯分)のとき
        {

        }
        else    // 同値であるとき
        {

        }
#endif

#if 0
    }
#endif
}

///*******************************************************************************
//* Function Name: fan_wng_fail_proc()
//* Description  : FAN警告/FAN異常 判別・対応
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
void fan_wng_fail_proc(void)
{
#if 0    // ※ステージ側で検知する
    // FAN回転停止警告(他2つの警告はfan_duty_set_proc()内)
    if((gu8_f_wng_fan_stop == _L_) && (gu16_d_fan_rpm <= gs_set_parameter.fan_wng_thd))    // 発報
    {
        gu8_f_wng_fan_stop = _H_;
    }
    if((gu8_f_wng_fan_stop == _H_) && (gu16_d_fan_rpm >= 1230))    // 回復
    {
        gu8_f_wng_fan_stop = _L_;
    }
#endif
}

///*******************************************************************************
//* Function Name: set_fan_val()
//* Description  : FAN速度指令値をもとにFAN制御用変数を設定する
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
void set_fan_val(void)
{
    /* 指令速度を目標速度とする */
    gu8_new_spd  = f_gu8_fan_speed;

    /* 現在速度より現在回転数,現在Duty%値を変数に格納する */
    gu16_now_rpm = get_fan_target_rpm(gu8_now_spd);
    gu16_now_per = get_fan_target_duty_per(gu8_now_spd);

    /* 目標速度より目標回転数, 目標Dutyカウント値, 目標Duty%値を変数に格納する */
    gu16_new_rpm = get_fan_target_rpm(gu8_new_spd);
    gu16_new_dty = get_fan_target_duty_cnt(gu8_new_spd);
    gu16_new_per = get_fan_target_duty_per(gu8_new_spd);

    /* 目標回転数をもとに目標回転数範囲を計算する */
    gu16_max_rpm_5 = (uint16_t)((float)gu16_new_rpm * 1.05);
    gu16_min_rpm_5 = (uint16_t)((float)gu16_new_rpm * 0.95);
    gu16_max_rpm_1 = (uint16_t)((float)gu16_new_rpm * 1.01);
    gu16_min_rpm_1 = (uint16_t)((float)gu16_new_rpm * 0.99);

    /* 補正用Duty%値の初期値は目標Duty%値にする */
    gf_adj_per = (float)gu16_new_per;

    /* 補正用Duty%値の最大値を目標Duty%値+30に設定する */
    gf_max_per = (float)(gu16_new_per + 30);
    if (gf_max_per > 100.0)
    {
        gf_max_per = 100.0;
    }

    /* 補正用Duty％値の最小値を0%にする */
    gf_min_per = 0.0;
}

///*******************************************************************************
//* Function Name: fan_duty_set_proc()
//* Description  : FAN出力設定処理
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
void fan_duty_set_proc(void)
{
    switch( gu8_fan_output_stg )
    {
        /* ソフトスタートを試してみたが、Dutyを徐々に上げるとオーバーシュートが発生したのでソフトスタートはしない方が良い(目標Dutyをいきなり設定する） */

        /* 初回は速度指令値で指定されたDutyで動作開始 */
        case 0:
            if(f_gu8_fan_speed != gu8_new_spd)
            {
                /* 周期のカウント値を設定する */
                gu16_fan_pwm_freq = (uint16_t)(SMCLK_40MHz / PWM_25KHz);

                /* 指定された指令値をもとに制御用変数を設定する */
                set_fan_val();

                /* 初回のみPWM関係の初期値を設定する */
                /* setCounterRepeatMode, setLoadValue, startCounterはPWM出力開始時のみ実施し、setCaptureCompareValueはDutyが変わるごとに実施する */
                DL_TimerA_setCounterRepeatMode(FAN_PWM_INST, GPTIMER_CTRCTL_REPEAT_REPEAT_1);
                DL_TimerA_setLoadValue(FAN_PWM_INST, (uint32_t)gu16_fan_pwm_freq);
                //DL_TimerA_setCaptureCompareValue(FAN_PWM_INST, (uint32_t)gu16_new_dty, DL_TIMERG_CAPTURE_COMPARE_0_INDEX);
                set_output_duty(gf_adj_per);
                DL_TimerA_startCounter(FAN_PWM_INST);
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+9);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu16_c_sta_rpm = 0;
                gu8_fan_output_stg = 10;
            }
            break;

        /* 指令速度の安定待ち */
        case 10:
            /* 指令速度が変わった？ */
            if (f_gu8_fan_speed != gu8_new_spd)
            {
                /* FAN制御用変数を新しい指令速度で初期化する */
                set_fan_val();

                /* Duty更新 */
                set_output_duty(gf_adj_per);
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+9);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu16_c_sta_rpm = 0;
                gu8_fan_output_stg = 10;    /* 改めてStage 10を実行する */
                return;
            }

            /* 安定化待ち時間が5秒経過したら補正を開始する */
            ++gu16_c_sta_rpm;
            if (gu16_c_sta_rpm >= 5)
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+1);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                if (gu8_new_spd == FAN_MAX_SPEED)
                {
                    gu8_now_spd = gu8_new_spd;
                    gu8_fan_output_stg = 50;
                }
                else
                {
                    gu8_fan_output_stg = 20;
                }
                return;
            }
            else
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
            }
            break;

        /* 目標回転数の5%範囲を目指して補正する */
        case 20:
            /* 指令速度が変わった？ */
            if (f_gu8_fan_speed != gu8_new_spd)
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+9);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu8_fan_output_stg = 10;
                return;
            }

            /* 目標回転数の5%範囲に到達した？ */
            if ((gu16_d_fan_rpm >= gu16_min_rpm_5) && (gu16_d_fan_rpm <= gu16_max_rpm_5))
            {
                /* 警告解除 */
                if( gf_adj_per <= (gu16_new_per + 20.0) )
                {
                    gu8_f_wng_fan_low = _L_;

                }
                if( gf_adj_per >= 5.0 )
                {
                    gu8_f_wng_fan_high = _L_;

                }
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+8);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu8_fan_output_stg = 30;
                return;
            }

            /* 1%刻みでDutyを調整 */
            /* 目標周波数範囲の下限未満ならDutyを1％上げる */
            if (gu16_d_fan_rpm < gu16_min_rpm_5)
            {
                if (gf_adj_per < gf_max_per)
                {
                    gf_adj_per += 1.0;

                    /* Duty更新 */
                    set_output_duty(gf_adj_per);
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+1);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                    return;
                }
                else
                {
                    if( f_gu8_fan_speed != FAN_MAX_SPEED )    // 最大回転時は警告を出さない(※無回転時はfan制御が呼ばれない)
                    {
                        /* FAN警告通知:回転低下 */
                        gu8_f_wng_fan_low = _H_;
                    }
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+2);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                    /* エラーが起きたことを明確にするためルートを変えてアイドルする */
                    gu8_fan_output_stg = 90;
                    return;
                }
            }

            /* 目標周波数範囲の上限を超えているならDutyを1％下げる */
            if (gu16_d_fan_rpm > gu16_max_rpm_5)
            {
                if (gf_adj_per > gf_min_per)
                {
                    gf_adj_per -= 1.0;

                    /* Duty更新 */
                    set_output_duty(gf_adj_per);
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+3);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                    return;
                }
                else
                {
                    if( f_gu8_fan_speed != FAN_MAX_SPEED )    // 最大回転時は警告を出さない(※無回転時はfan制御が呼ばれない)
                    {
                        /* FAN警告通知:回転上昇 */
                        gu8_f_wng_fan_high = _H_;
                    }
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+4);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                    /* エラーが起きたことを明確にするためルートを変えてアイドルする */
                    gu8_fan_output_stg = 90;
                    return;
                }
            }
            break;

        /* 目標回転数の1%範囲を目指して補正する */
        case 30:
            /* 指令速度が変わった？ */
            if (f_gu8_fan_speed != gu8_new_spd)
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+9);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu8_fan_output_stg = 10;
                return;
            }

            /* 目標回転数の1%範囲に到達した？ */
            if ((gu16_d_fan_rpm >= gu16_min_rpm_1) && (gu16_d_fan_rpm <= gu16_max_rpm_1))
            {
                /* 警告解除 */
                if( gf_adj_per <= (gu16_new_per + 20.0) )
                {
                    gu8_f_wng_fan_low = _L_;

                }
                if( gf_adj_per >= 5.0 )
                {
                    gu8_f_wng_fan_high = _L_;

                }

                /* 目標速度に達したので現在速度を目標速度で更新する */
                gu8_now_spd = gu8_new_spd;
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+8);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu8_fan_output_stg = 40;
                return;
            }

            /* 目標周波数に向けて補正を実行する */

            /* 目標周波数範囲の下限未満ならDutyを0.1％上げる */
            if (gu16_d_fan_rpm < gu16_min_rpm_1)
            {
                if (gf_adj_per < gf_max_per)
                {
                    gf_adj_per += 0.1;

                    /* Duty更新 */
                    set_output_duty(gf_adj_per);
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+1);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                    return;
                }
                else
                {
                    if( f_gu8_fan_speed != FAN_MAX_SPEED )    // 最大回転時は警告を出さない(※無回転時はfan制御が呼ばれない)
                    {
                        /* FAN警告通知:回転低下 */
                        gu8_f_wng_fan_low = _H_;
                    }
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+2);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                    /* エラーが起きたことを明確にするためルートを変えてアイドルする */
                    gu8_fan_output_stg = 90;
                    return;
                }
            }

            /* 目標周波数範囲の上限を超えているならDutyを0.1％下げる */
            if (gu16_d_fan_rpm > gu16_max_rpm_1)
            {
                if (gf_adj_per > gf_min_per)
                {
                    gf_adj_per -= 0.1;

                    /* Duty更新 */
                    set_output_duty(gf_adj_per);
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+3);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                    return;
                }
                else
                {
                    if( f_gu8_fan_speed != FAN_MAX_SPEED )    // 最大回転時は警告を出さない(※無回転時はfan制御が呼ばれない)
                    {
                        /* FAN警告通知:回転上昇 */
                        gu8_f_wng_fan_high = _H_;
                    }
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+4);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                    /* エラーが起きたことを明確にするためルートを変えてアイドルする */
                    gu8_fan_output_stg = 90;
                    return;
                }
            }
            break;

        /* 正常時のアイドル処理 */
        case 40:
            if(f_gu8_fan_speed == gu8_new_spd)
            {
                ;
            }
            else
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+9);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu8_fan_output_stg = 10;
                return;
            }

            /* Idle中に5%範囲から外れたらDuty1%刻みの補正を実施する */
            if(( gu16_d_fan_rpm > gu16_max_rpm_5 ) || ( gu16_d_fan_rpm < gu16_min_rpm_5 ))
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+1);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu8_fan_output_stg = 20;
                return;
            }

            /* Idle中に1%範囲から外れたらDuty0.1%刻みの補正を実施する */
            if(( gu16_d_fan_rpm > gu16_max_rpm_1 ) || ( gu16_d_fan_rpm < gu16_min_rpm_1 ))
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+2);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu8_fan_output_stg = 30;
                return;
            }

#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
            break;

        /* 最大速度時は速度変更だけ監視する */
        case 50:
            if(f_gu8_fan_speed == gu8_new_spd)
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
            }
            else
            {
#ifdef _HIS_ENABLE_MODE_
his_temp(gu8_fan_output_stg+9);
his_temp(gu8_now_spd);
his_temp(gu8_new_spd);
his_temp(gu16_new_dty);
his_temp(gu16_d_fan_rpm);
#endif
                gu8_fan_output_stg = 10;
                return;
            }
            break;

            /* FAN警告発報中処理 */
            case 90:
                if(f_gu8_fan_speed == gu8_new_spd)
                {
    #ifdef _HIS_ENABLE_MODE_
    his_temp(gu8_fan_output_stg);
    his_temp(gu8_now_spd);
    his_temp(gu8_new_spd);
    his_temp(gu16_new_dty);
    his_temp(gu16_d_fan_rpm);
    #endif
                }
                else
                {
    #ifdef _HIS_ENABLE_MODE_
    his_temp(gu8_fan_output_stg+9);
    his_temp(gu8_now_spd);
    his_temp(gu8_new_spd);
    his_temp(gu16_new_dty);
    his_temp(gu16_d_fan_rpm);
    #endif
                    gu8_fan_output_stg = 10;
                    return;
                }

                if(((gu8_f_wng_fan_low == _H_) && (gu16_d_fan_rpm > gu16_min_rpm_5))      // 回転低下
                || ((gu8_f_wng_fan_high == _H_) && (gu16_d_fan_rpm < gu16_max_rpm_5)))    // 回転上昇
                {
    #ifdef _HIS_ENABLE_MODE_
    his_temp(gu8_fan_output_stg+1);
    his_temp(gu8_now_spd);
    his_temp(gu8_new_spd);
    his_temp(gu16_new_dty);
    his_temp(gu16_d_fan_rpm);
    #endif
                    gu8_fan_output_stg = 20;
                    return;
                }
                break;

        default:
            break;
    }
}

///*******************************************************************************
//* Function Name: get_fan_target_duty_cnt()
//* Description  :
//* Arguments    : 回転モードフラグ
//* Return Value : 指令デューティカウント値
//*******************************************************************************/
uint16_t get_fan_target_duty_cnt(uint8_t mode_flg)
{
    uint16_t ret_duty_co = 0;

    switch(mode_flg)
    {
        case FAN_STOP:
            ret_duty_co = 0;
            break;
        case FAN_MIN_SPEED:
            ret_duty_co = 0;
            break;
        case FAN_LOW_SPEED:
            ret_duty_co = FAN_CYCLE_COUNT * FAN_LOW_PERCENTAGE / 100;
            break;
        case FAN_MID_SPEED:
            ret_duty_co = FAN_CYCLE_COUNT * FAN_MID_PERCENTAGE / 100;
            break;
        case FAN_HIGH_SPEED:
            ret_duty_co = FAN_CYCLE_COUNT * FAN_HIGH_PERCENTAGE / 100;
            break;
        case FAN_MAX_SPEED:
            ret_duty_co = FAN_CYCLE_COUNT;
            break;
        default:
            ret_duty_co = 0;    // 安全方向
            break;
    }

    return ret_duty_co;
}

///*******************************************************************************
//* Function Name: get_fan_target_duty_per()
//* Description  :
//* Arguments    : 回転モードフラグ
//* Return Value : 指令デューティ比
//*******************************************************************************/
uint16_t get_fan_target_duty_per(uint8_t mode_flg)
{
    uint16_t ret_duty_per = 0;
    switch(mode_flg)
    {
        case FAN_STOP:
            ret_duty_per = 0;
            break;
        case FAN_MIN_SPEED:
            ret_duty_per = 0;
            break;
        case FAN_LOW_SPEED:
            ret_duty_per = FAN_LOW_PERCENTAGE;
            break;
        case FAN_MID_SPEED:
            ret_duty_per = FAN_MID_PERCENTAGE;
            break;
        case FAN_HIGH_SPEED:
            ret_duty_per = FAN_HIGH_PERCENTAGE;
            break;
        case FAN_MAX_SPEED:
            ret_duty_per = FAN_MAX_PERCENTAGE;
            break;
        default:
            ret_duty_per = 0;    // 安全方向
            break;
    }

    return ret_duty_per;
}

///*******************************************************************************
//* Function Name: get_fan_target_rpm()
//* Description  :
//* Arguments    : 回転モードフラグ
//* Return Value : 指令回転数
//*******************************************************************************/
uint16_t get_fan_target_rpm(uint8_t mode_flg)
{
    uint16_t ret_rpm = 0;

    switch(mode_flg)
    {
        case FAN_STOP:
            ret_rpm = 0;
            break;
        case FAN_MIN_SPEED:
            ret_rpm = 0;
            break;
        case FAN_LOW_SPEED:
            ret_rpm = FAN_LOW_RPM;
            break;
        case FAN_MID_SPEED:
            ret_rpm = FAN_MID_RPM;
            break;
        case FAN_HIGH_SPEED:
            ret_rpm = FAN_HIGH_PPM;
            break;
        case FAN_MAX_SPEED:
            ret_rpm = FAN_MAX_RPM;
            break;
        default:
            ret_rpm = 0;    // 安全方向
            break;
    }

    return ret_rpm;
}

///*******************************************************************************
//* Function Name: set_output_duty()
//* Description  :
//* Arguments    : dutyカウント値
//* Return Value : dutyカウント値(ローンチパッドor実基板)
//*******************************************************************************/
void set_output_duty(float count)
{
    gu16_new_dty = (float)gu16_fan_pwm_freq * count * 0.01;


#ifndef _LAUNCHPAD_MODE_
    gu16_new_dty = (float)gu16_fan_pwm_freq - gu16_new_dty;
#endif

            DL_TimerA_setCaptureCompareValue(FAN_PWM_INST, (uint32_t)gu16_new_dty, DL_TIMERG_CAPTURE_COMPARE_0_INDEX);

}

/*******************************************************************************
* Function Name: ac_link_proc()
* Description  : AC_LINK処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void ac_link_proc( void )
{
    //static uint8_t stage = 0;
    static uint32_t c_12v_off_timer;

    if (SP_AC_LINK != gu8_prev_ac_link)
    {
        gu8_prev_ac_link = SP_AC_LINK;
        if (SP_AC_LINK == _ENABLE_)
        {
            set_info_evt_errlog(FLAG_RESTART_READY, _SET_);
        }
        else if(gu8_f_output_restart==0)
        {
            set_info_evt_errlog(FLAG_RESTART_READY, _RESET_);
        }
    }
    switch( gu8_ac_link_stage )
    {
        case 0:
            if( gu8_f_ac_link != 0 )
            {
                c_12v_off_timer = SP_RESTART_TIME * TIMER_1000ms; // 12V出力OFF時間タイマ(x1s)
                if( c_12v_off_timer != 0 )
                {
                    gu8_ac_link_stage = 1;
                } else {
                    gu8_f_output_restart = 0;
                    restart_flg_proc();

                    gu8_f_ac_link = 0;
                }
            }
            break;

        case 1:
            if( (gu32_c_ac_link_timer != 0) || (gu8_f_ac_link == 2) )  // AC_LINK有効タイマ または OUTPUT RESTART受信
            {
                if( gu8_f_ps_on == _OFF_ )    // PS_ON=OFF
                {
                    gu8_f_12v_en_out = _OUT_OFF_;   // 12V_EN(eFuse) OFF

                    gu8_f_ac_link_restarting = 1;   // Restart中

                    gu16_c_proc_delay = TIMER_500ms; //ACLINK開始して500msは検出待ち時間をもうける
                    gu8_f_proc_start = 0;   //保護を一時停止

                    gu8_ac_link_stage = 2;
                }
            } else {
                gu8_f_ac_link = 0;
                gu8_ac_link_stage = 0;
            }
            break;

        case 2:
            if( c_12v_off_timer == 0 )
            {


                gu8_f_12v_en_out = _OUT_ON_;   // 12V_EN(eFuse) ON

                gu8_f_ac_link_restarting = 0;

                gu8_f_ac_link = 0;
                gu8_f_output_restart = 0;

                restart_flg_proc();

                gu8_ac_link_stage = 0;

                gu32_c_opencheck_time=(TIMER_300ms-TIMER_4ms); //300ms間だけopenを監視
                gu8_f_opencheck=1;

            } else {
                c_12v_off_timer--;
            }
            break;

        default:
            break;
    }

    if(gu32_c_opencheck_time!=0)
    {
        gu32_c_opencheck_time--;
    }else{
        gu8_f_opencheck=0;
    }
    if( gu32_c_ac_link_timer != 0 ) // AC_LINK有効タイマ減算
    {
        gu32_c_ac_link_timer--;
    }
}


void restart_flg_proc(void)
{
    if (SP_AC_LINK != _ENABLE_)
    {
     set_info_evt_errlog( FLAG_RESTART_READY, _RESET_ );  // RESTART READY Reset
    }

}
