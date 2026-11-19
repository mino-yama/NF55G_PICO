#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"

void hogo_proc(void);
void hogo_detect(void);
void hogo_output1(void);
void hogo_output2(void);
void hogo_output3(void);
void hogo_output4(void);
void hogo_output5(void);

void hogo_release(void);
void pro_12v_filter_clear(void);
void pro_cha_filter_clear(void);
void pro_dis_filter_clear(void);
void pro_tmp_filter_clear(void);
void pro_batt_filter_clear(void);

extern uint8_t input_filter(uint8_t flag, uint8_t input, struct _Filter *fil);
extern void set_info_evt_errlog( uint8_t flag, uint8_t status );
extern void filter_clear(struct _Filter *fil);
extern uint8_t eeprom_write_request( uint32_t pos, uint32_t num, uint8_t mode );
extern void operate_log_request( uint8_t almid );
//struct _Filter pi_fan_low_protection   = { 0, 0, TIMER_30s,  TIMER_10ms, 0, _TRG_NONE_ };
//struct _Filter pi_fan_high_protection  = { 0, 0, TIMER_30s,  TIMER_10ms, 0, _TRG_NONE_ };
//struct _Filter pi_fan_stop_protection  = { 0, 0, TIMER_10s,  TIMER_10ms, 0, _TRG_NONE_ };
volatile uint8_t gu8_fan_debug_mode = FAN_DEBUG_NORMAL;

volatile uint8_t gu8_fan_debug_fast = 0U;
/*******************************************************************************
 * Function Name: hogo_proc()
 * Description  : 保護処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void hogo_proc(void)
{
    if(gu8_f_before_shutdown!=1)
    {
        hogo_detect();   // 保護検出
        hogo_release();  // 保護解除
    }
}

/*******************************************************************************
 * Function Name: hogo_detect()
 * Description  : 保護検出
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void hogo_detect(void)
{
    //static uint8_t f_wng_fan_low_old = 0;
    //static uint8_t f_wng_fan_high_old = 0;
    //static uint8_t f_wng_fan_stop_old = 0;
    //static uint8_t alm_type_batt_err_old = 0;
    uint8_t f_suppres = 0;

    if( gu8_f_proc_start == 0 )  // 処理開始前?
    {
        return;
    }

    /****************************/
    /* [+12V各種異常](ラッチ系) */
    /****************************/
    if(gu8_f_ac_on==_ON_||gu8_f_ps_on==_ON_){
        if( gu8_f_low_v == _ON_ ) // 項番1:不足電圧  [+12V各種異常]
        {
            if (((gu8_alm_type_dischg_err & 0x01) == 0) &&
                ((gu8_alm_type_temp_err   & 0x03) == 0) &&
                ((gu8_alm_type_pfc_err    & 0x01) == 0) &&
                ((gu8_alm_type_fan_err    & 0x02) == 0) &&
                ((gu8_alm_type_12v_err    & 0x2B) == 0) &&
                 (gu8_f_opencheck!=1))                          //openの時はログをしない
            {
                if ((gu8_alm_type_12v_err & BIT0) == 0)
                {
                    set_info_evt_errlog( FLAG_12V_LV, _SET_ );  // 12V_LV (1)
                    gu8_alm_type_12v_err |= BIT0; // 0x01
                }
            }
        }
    }

    /* PS_ON状態 */
    if( gu8_f_ps_on == _ON_ )
    {
        /* 12V出力の過電流を検出した */
        if( gu8_f_high_i_on_10ms == _ON_ ) // 項番6,7:過電流保護 2-8 [+12V各種異常]
        {
            /* FLAG_12V_OCがセットされていないならセットする */
            if (gu8_f_over_i_on == 0)
            {
               set_info_evt_errlog( FLAG_12V_OC, _SET_ ); // 12V_OC  (1)
               gu8_f_over_i_on = 1;
            }
        }
        /* 12V出力の過電流が収まった */
        else
        {
            /* FLAG_12V_OCがセットされているならリセットする */
            if (gu8_f_over_i_on == 1)
            {
               set_info_evt_errlog( FLAG_12V_OC, _RESET_ ); // 12V_OC  (1)
               gu8_f_over_i_on = 0;
            }
        }

        if(gu8_f_high_i_on_50ms == _ON_)  //ラッチ
        {
            if( (gu8_alm_type_12v_err & BIT1) == 0 )
            {
                gu8_alm_type_12v_err |= BIT1; // 0x02
            }
        }
    }
    /* PS_OFF状態 */
    else
    {
        if( (gu8_f_over_i_on != 0) && ((gu8_alm_type_12v_err & BIT1) == 0) )
        {
            set_info_evt_errlog( FLAG_12V_OC, _RESET_ );  // 12V_OC(1)
            gu8_f_over_i_on = 0;
        }
        gu8_f_high_i_on_10ms =_OFF_;
        gu8_f_high_i_on_50ms =_OFF_;
    }

#if 0
    if( gu8_f_low_i_of == _ON_ ) // 項番4:過電流保護 2-10 [+12V各種異常]
    {
        if( gu8_f_ps_on == _OFF_ )   // PS_ON = OFF?   (1)
        {
            if( (gu8_alm_type_12v_err & BIT2) == 0 )
            {
                set_info_evt_errlog( FLAG_12V_OC_OFF, _SET_ );  // 12V_OC_OFF (1)
                gu8_alm_type_12v_err |= BIT2; // 0x04
            }
        }
    }
#else
    if( (gu8_f_ps_on == _OFF_) && ((gu8_alm_type_12v_err & BIT1) == 0) )   // PS_ON = OFF?   (1)
    {
        if( gu8_f_high_i_of  == _ON_ ) // 項番4:過電流保護 2-10 [+12V各種異常]
        {
            if(gu8_f_12v_oc_off == 0)
            {
                set_info_evt_errlog( FLAG_12V_OC_OFF, _SET_ );  // 12V_OC_OFF (1)
                gu8_f_12v_oc_off = 1;
            }
        }
        else
        {
            if(gu8_f_12v_oc_off == 1)
            {
                set_info_evt_errlog( FLAG_12V_OC_OFF, _RESET_ );  // 12V_OC_OFF (1)
                gu8_f_12v_oc_off = 0;
            }
        }

       if( gu8_f_high_i_of_h == _ON_) // 項番6,7:過電流保護 [+12V各種異常]
       {
           if(gu8_f_12v_oc_off_h == 0)
           {
               set_info_evt_errlog( FLAG_12V_OC_OFF_H, _SET_ );  // 12V_OC_OFF (1)
               gu8_f_12v_oc_off_h = 1;
           }
       }
       else
       {
           if(gu8_f_12v_oc_off_h == 1)
           {
               set_info_evt_errlog( FLAG_12V_OC_OFF_H, _RESET_ );  // 12V_OC_OFF (1)
               gu8_f_12v_oc_off_h = 0;
           }
       }
    }
    else
    {
        if( gu8_f_12v_oc_off != 0 )
        {
            set_info_evt_errlog( FLAG_12V_OC_OFF, _RESET_ );  // 12V_OC_OFF (1)
            gu8_f_12v_oc_off = 0;
        }
        if( gu8_f_12v_oc_off_h != 0 )
        {
            set_info_evt_errlog( FLAG_12V_OC_OFF_H, _RESET_ );  // 12V_OC_OFF (1)
            gu8_f_12v_oc_off_h = 0;
        }
        gu8_f_high_i_of=_OFF_;
        gu8_f_high_i_of_h=_OFF_;
    }
#endif

    if ( (gu8_f_high_v == _ON_) || (gu8_f_dischg12_ovp == _ON_) ) // 項番8:過電圧保護  [+12V各種異常]  + 放電コンバータ過電圧
    {
        if( gu8_f_over_v == 0 )
        {
            set_info_evt_errlog( FLAG_12V_OV, _SET_ );  // 12_OV  (1)
            gu8_f_over_v=1;
        }
    }
    else
    {
        if( gu8_f_over_v == 1 )
        {
            set_info_evt_errlog( FLAG_12V_OV, _RESET_ );  // 12_OV  (1)
            gu8_f_over_v=0;
        }
    }

    if( gu8_f_bbu_sw_short == _ON_ ) // 項番16:出力スイッチ故障(ショート) 2-9 [+12V各種異常]
    {
        if( gu8_f_ac_link_restarting != 0 )   // AC_LINK Resrart中?
        {
            if(gu8_f_sw_short==0)  // 12V_EN(eFuse) OFF
            {
               set_info_evt_errlog( FLAG_BBU_SW_ST, _SET_ );   // BBU_SW_ST  (-)  12V_EN=OFFなのに電圧がある
               gu8_f_sw_short=1;
            }
        }
    }
    else if( gu8_f_bbu_sw_short == _OFF_ ) // 項番16:出力スイッチ故障(ショート) 2-9 [+12V各種異常]
    {
        if(gu8_f_sw_short==1)  // 12V_EN(eFuse) OFF
        {
           set_info_evt_errlog( FLAG_BBU_SW_ST, _RESET_ );   // BBU_SW_ST  (-)  12V_EN=OFFなのに電圧がある
           gu8_f_sw_short=0;
        }
    }

    if(gu8_f_ac_on==_ON_||gu8_f_ps_on==_ON_){
        if( gu8_f_bbu_sw_open == _ON_ ) // 項番17:出力スイッチ故障(オープン) 2-9 [+12V各種異常]
        {
            if( gu8_f_opencheck==1)  //
            {
                if( (gu8_alm_type_12v_err & BIT5) == 0 )
                {
                    set_info_evt_errlog( FLAG_BBU_SW_OP, _SET_ );   // BBU_SW_OP  (1) 12V_EN=ONなのに電圧がない
                    gu8_alm_type_12v_err |= BIT5; // 0x20
                }
            }
        }
    }

    /********************************/
    /* [放電回路各種異常](ラッチ系) */
    /********************************/
    if( gu8_f_batt_connect == _BATT1_CONNECT_ )   // BATT1接続
    {
        if( gu8_f_high_i_dis_6 == _ON_ )     //項番10:過電流保護 2-15  BATT6直 [放電回路各種異常]
        {
            if( gu8_f_backup_active == _ON_ )    // バックアップ中
            {
                if( (gu8_alm_type_dischg_err & BIT0) == 0 )
                {

                    set_info_evt_errlog( FLAG_BATT_OC, _SET_ );  // BATT_OC  (1)
                    gu8_alm_type_dischg_err |= BIT0; // 0x01
                }
            }
        }
    }

    /********************************/
    /* [充電回路各種異常](ラッチ系) */
    /********************************/
    if( gu8_f_high_i_cha == _ON_ )     //項番12:過電流保護 2-13  [充電回路各種異常]
    {
        if( (gu8_f_charging_active != 0) && (gu8_f_batchg_en_out == _OUT_ON_) )    // 充電中
        {
            if( (gu8_alm_type_chg_err & BIT0) == 0 )
            {
                set_info_evt_errlog( FLAG_CHG_OC, _SET_ );  // CHG_OC  (3)
                gu8_alm_type_chg_err |= BIT0; // 0x01
            }
        }
    }

    if( gu8_f_batt_connect == _BATT1_CONNECT_ )   // BATT1接続
    {
        if( gu8_f_high_v_cha_6 == _ON_ )     //項番14:過電圧保護(充電回路) 2-11  BATT6直 [充電回路各種異常]
        {
            if( (gu8_f_charging_active != 0) && (gu8_f_batchg_en_out == _OUT_ON_) )    // 充電中
            {
                if( gu8_f_over_chg == 0 )
                {
                    set_info_evt_errlog( FLAG_CHG_OV, _SET_ );  // CHG_OV  (3)
                    gu8_f_over_chg=1;

                }
            }
        }
        else
        {
            if( gu8_f_over_chg == 1 )
            {
                set_info_evt_errlog( FLAG_CHG_OV, _RESET_ );  // CHG_OV  (3)
                gu8_f_over_chg=0;
            }
        }
    }

    if( (gu8_f_charging_active != 0) && (gu8_f_batchg_en_out == _OUT_ON_) )    // 充電中
    {
        if( gu32_c_low_v_shortage< TIMER_10min )    // 充電開始後、10分間検出で停止
        {
            gu32_c_low_v_shortage++;
            if( gu8_f_low_v_shortage_5a == _OFF_ )    // 充電電流 1.5A以下
            {
                if( gu8_f_low_v_shortage == _ON_ )     //項番15:不足保護 2-14 [充電回路各種異常]
                {
                    if( (gu8_alm_type_chg_err & BIT2) == 0 )
                    {
                        set_info_evt_errlog( FLAG_CHG_LV, _SET_ );   // CHG_LV  (3)
                        gu8_alm_type_chg_err |= BIT2; // 0x04
                    }
                }
            }
            else
            {
                gu32_c_low_v_shortage= TIMER_10min;  // 充電電流 1.5A以上あれば検出停止
            }
         }
    }
    else
    {
        filter_clear(&pi_low_v_shortage);
        filter_clear(&pi_low_v_shortage_5a);
        gu32_c_low_v_shortage = 0;
    }

    /**************************/
    /* [温度警告](自動回復系) */
    /**************************/
    // ADU
    if( gu8_f_fan_fail_adu == _ON_ )        //項番18:ADU 温度異常保護(警告) 1-1   [温度警告]
    {
        if(gu8_f_tmp_fail_adu==0){
            set_info_evt_errlog( FLAG_ADU_TEMP_WNG, _SET_ );   // ADU_TEMP_WNG  (-)
            gu8_f_tmp_fail_adu=1;
        }
    }
    else   //項番18:ADU 温度異常保護(警告) 1-1   [温度警告]
    {
        if(gu8_f_tmp_fail_adu==1)
        {
            set_info_evt_errlog( FLAG_ADU_TEMP_WNG, _RESET_ );   // ADU_TEMP_WNG  (-)
            gu8_f_tmp_fail_adu=0;
        }
    }
    // BBU
    if( gu8_f_fail_bbu== _ON_  )        //項番19:BBU 温度異常保護(警告) 1-2   [温度警告]
    {
        if(gu8_f_tmp_fail_bbu==0)
        {
            set_info_evt_errlog( FLAG_BBU_TEMP_WNG, _SET_ );   // BBU_TEMP_WNG  (-)
            gu8_f_tmp_fail_bbu=1;
        }
    }
    else                                    //項番19:BBU 温度異常保護(警告) 1-2   [温度警告]
    {
        if(gu8_f_tmp_fail_bbu==1)
        {
            set_info_evt_errlog( FLAG_BBU_TEMP_WNG, _RESET_ );   // BBU_TEMP_WNG  (-)
            gu8_f_tmp_fail_bbu=0;
        }
    }

    /************************/
    /* [温度異常](ラッチ系) */
    /************************/
    if( gu8_f_temp_fail_adu == _ON_ )     //項番20:ADU 温度異常保護 1-3  [温度異常]
    {
        if( (gu8_alm_type_temp_err & BIT0) == 0 )
        {
            set_info_evt_errlog( FLAG_ADU_TEMP_ALM, _SET_ );   // ADU_TEMP_ALM  (1)
            gu8_alm_type_temp_err |= BIT0; // 0x01
        }
    }

    if( gu8_f_temp_fail_bbu == _ON_ )     //項番21:BBU 温度異常保護 1-4  [温度異常]
    {
        if( (gu8_alm_type_temp_err & BIT1) == 0 )
        {
            set_info_evt_errlog( FLAG_BBU_TEMP_ALM, _SET_ );   // BBU_TEMP_ALM  (1)
            gu8_alm_type_temp_err |= BIT1; // 0x02
        }
    }

    /***************************/
    /* [PFC回路異常](ラッチ系) */
    /***************************/
    if( gu8_f_ac_on == _ON_ ) // AC ON?
    {

        if(gu8_f_pfc_fail_in==_ON_)
        {
            if( gu8_f_pfc_err==0 )     //項番23:PFC異常保護(過電圧) 1-7,8  [PFC回路異常]
            {
                set_info_evt_errlog( FLAG_PFC_OV, _SET_ );  // PFC_OV (1)
                gu8_f_pfc_err=1;
            }
        }
        else
        {
            if( gu8_f_pfc_err==1 )     //項番23:PFC異常保護(過電圧) 1-7,8  [PFC回路異常]
            {
                set_info_evt_errlog( FLAG_PFC_OV, _RESET_ );  // PFC_OV (1)
                gu8_f_pfc_err=0;
            }
        }
    }

    /***************************/
    /* [バッテリ異常](ラッチ系) */
    /***************************/
    if( gu8_f_latch_fail == _ON_ )     //項番33:バッテリ温度異常 22.3.2 項番1  [バッテリ異常]
    {
        //if( gu8_f_juudentyu != 0 )    // 充電中
        {
            if( (gu8_alm_type_batt_err & BIT0) == 0 )
            {
                set_info_evt_errlog( FLAG_BATT_TEMP_ALM, _SET_ );  // BATT_TEMP_ALM  (4)
            	operate_log_request(OPE_AC_FAIL);   //opelog
                gu8_alm_type_batt_err |= BIT0; // 0x01
            }
        }
    }

    if( gu32_c_minus_dv_disable >= TIMER_5min )   // 充電電圧マスク時間5分解除後の電圧
    {
        if( gu8_f_batt_connect == _BATT1_CONNECT_ )   // BATT1接続
        {
            if( gu8_f_batt_low_6 == _ON_ )     //項番34:バッテリ低電圧 22.3.2 項番2  BATT6直    [バッテリ異常]
            {
                if( (gu8_f_charging_active != 0) && (gu8_f_batchg_en_out == _OUT_ON_) )    // 充電中
                {
                    if( (gu8_alm_type_batt_err & BIT1) == 0 )
                    {
                        set_info_evt_errlog( FLAG_BATT_LV, _SET_ );  // BATT_LV  (2)
                    	operate_log_request(OPE_AC_FAIL);   //opelog
                        gu8_alm_type_batt_err |= BIT1; // 0x02
                    }
                }
            }
        }
    }

    if( gu8_f_batt_connect == _BATT1_CONNECT_ )   // BATT1接続
    {
        if( gu8_f_batt_high_6 == _ON_ )     //項番36:バッテリ高電圧 22.3.2 項番3  BATT6直    [バッテリ異常]
        {
            if( gu8_f_charging_active == 0 )    // 非充電中(充電停止中)
            {
                if( (gu8_alm_type_batt_err & BIT2) == 0 )
                {
                    set_info_evt_errlog( FLAG_BATT_OV, _SET_ );  // BATT_OV  (2)
                	 operate_log_request(OPE_AC_FAIL);   //opelog
                    gu8_alm_type_batt_err |= BIT2; // 0x04
                }
            }
        }
    }

    /******************************/
    /* [バッテリ異常](自動回復系) */
    /******************************/
    // バッテリ充電抑止
    f_suppres = 0;
    if( gu8_f_charging_active == 0/*|| (gu8_f_batchg_en_out == _OUT_OFF_)*/ )    // 非充電中
    {
        if( gu8_f_batt_temp_bef == _ON_ )
        {
              f_suppres |= BIT0;
        }

    }
    else
    {
        if( gu8_f_batt_temp_aft == _ON_ )
        {
            if( pi_batt_temp_aft.trg == _TRG_ON_  )     //項番30:バッテリ温度抑止(充電中) 22.3.1 項番2 [バッテリ異常]
            {
                set_info_evt_errlog( FLAG_BATT_TEMP_WNG, _SET_ );  // BATT_TEMP_WNG  (4)

            }
            f_suppres |= BIT0;
        }
        else
        {
            if( pi_batt_temp_aft.trg ==  _TRG_OFF_ )     //項番30:バッテリ温度抑止(充電中) 22.3.1 項番2 [バッテリ異常]
            {
                set_info_evt_errlog( FLAG_BATT_TEMP_WNG, _RESET_ );  // BATT_TEMP_WNG  (4)
                //gu8_f_tmp_wng_batt=0;
            }
        }
    }

    // バッテリ保護素子破損(BATT_P_FAIL)
    if( gu8_f_batt_break == _ON_ ) // BATT_P_FAIL
    {
        if( pi_batt_break.trg == _TRG_ON_ )     //項番31:バッテリ保護素子破損 22.3.1 項番3 [バッテリ異常]
        {
            set_info_evt_errlog( FLAG_BATT_P_FAIL, _SET_ );  // BATT_P_FAIL  (2)
        	if (gu8_f_ac_on_trg == _TRG_OFF_)
            {
                operate_log_request(OPE_AC_FAIL);   //opelog
            }
        }
        f_suppres |= (BIT0 | BIT1);
    }
    else
    {
        if( pi_batt_break.trg == _TRG_OFF_ )     //項番31:バッテリ保護素子破損 22.3.1 項番3 [バッテリ異常]
        {
            set_info_evt_errlog( FLAG_BATT_P_FAIL, _RESET_ );  // BATT_P_FAIL  (2)
        }
    }

    if( gu8_f_batt_break_chg == _ON_ ) // BATT_P_FAIL
    {
        if( pi_batt_break_chg.trg == _TRG_ON_ )
        {
            gu16_batt_break_chg_timer=TIMER_2000ms;

            pi_batt_break_chg.trg=_TRG_OFF_;

            set_info_evt_errlog( FLAG_BATT_P_FAIL, _SET_ );  // BATT_P_FAIL  (2)
        	
            if (gu8_f_ac_on_trg == _TRG_OFF_)
            {
                operate_log_request(OPE_AC_FAIL);   //opelog
            }
        }
        f_suppres |= (BIT0 | BIT1);
    }
    else
    {
        if( pi_batt_break_chg.trg == _TRG_OFF_ )
        {
            set_info_evt_errlog( FLAG_BATT_P_FAIL, _RESET_ );  // BATT_P_FAIL  (2)
        }
    }

    // バッテリ未接続
    if( gu8_f_batt_not == _ON_ )
    {
        if( pi_batt_not.trg == _TRG_ON_ )     //項番32:バッテリ未接続 22.3.1 項番4 [バッテリ異常]
        {
            set_info_evt_errlog( FLAG_BATT_DCN, _SET_ );  // BATT_DCN  (2)
            if (gu8_f_ac_on_trg == _TRG_OFF_)
            {
                operate_log_request(OPE_AC_FAIL);   //opelog
            }

        }
        f_suppres |= (BIT0 | BIT1);
    }
    else
    {
        if( pi_batt_not.trg == _TRG_OFF_ )     //項番32:バッテリ未接続 22.3.1 項番4 [バッテリ異常]
        {
            set_info_evt_errlog( FLAG_BATT_DCN, _RESET_ );  // BATT_DCN  (2)
        }
    }

    if( (f_suppres & BIT0) != 0 )
    {
        if( gu8_f_susp_cha == TEMP_SUPPRES_0 )// 充電中断フラグOFF?
        {
            gu8_f_susp_cha = TEMP_SUPPRES_1;       // 充電中断フラグON
        }
    }
    else
    {
        gu8_f_susp_cha = TEMP_SUPPRES_0;       // 充電中断フラグOFF
    }
    if( (f_suppres & BIT1) != 0 )
    {
        gu8_f_susp_dischg = _ON_;   // 放電中断フラグOFF
    }
    else
    {
        gu8_f_susp_dischg = _OFF_;   // 放電中断フラグOFF
    }
#if 1
    if( gu8_f_backup_active == _ON_ )    // バックアップ中
    {
        if( gu8_f_susp_cha == TEMP_SUPPRES_1 ) // 温度抑止中?
        {
            gu8_f_susp_cha = TEMP_SUPPRES_6;  // 温度抑止復帰(停電によるバックアップ移行時)
        }
    }
#endif
    /*********************/
    /* [ファン警告/異常] */
    /*********************/
    if( (f_gu8_fan_speed_def == FAN_LOW_SPEED) || (f_gu8_fan_speed_def == FAN_MID_SPEED) || (f_gu8_fan_speed_def == FAN_HIGH_SPEED) ) // 低速/中速/高速
    {
        gu8_f_wng_fan_low_protection  = input_filter( _NZ_, gu8_f_wng_fan_low , &pi_fan_low_protection ); // FAN回転低下
        gu8_f_wng_fan_high_protection = input_filter( _NZ_, gu8_f_wng_fan_high, &pi_fan_high_protection); // FAN回転上昇


        if( SP_FAN_WNG_THD != UINT16_MAX_VALUE_UNDER ) // 回転停止検出停止
        {
            gu8_f_wng_fan_stop_protection = input_filter( _NZ_,  (pi_fan_stop_protection.sts == _ON_) ? (gu16_d_fan_rpm <= 1230): (gu16_d_fan_rpm <= SP_FAN_WNG_THD), &pi_fan_stop_protection);// 回転停止
        }
        else
        {
            gu8_f_wng_fan_stop_protection = 0;
        }

        if( (gu8_f_wng_fan_low_protection != 0) || (gu8_f_wng_fan_high_protection != 0 ) || (gu8_f_wng_fan_stop_protection != 0) )     // FAN回転低下/回転上昇/回転停止
        {
            if( gu8_f_fan_fail_check == 0 )
            {
                gu32_c_fan_fail_timer = TIMER_30s;  // 30秒
                gu8_f_fan_fail_check = 1;
            }
            else
            {
               if( gu32_c_fan_fail_timer != 0 )
               {
                    gu32_c_fan_fail_timer--;
               }
            }
        }
        else if((gu8_f_wng_fan_low_protection == 0) && (gu8_f_wng_fan_high_protection == 0 ) && (gu8_f_wng_fan_stop_protection == 0) )
        {
            gu8_f_fan_fail_check = 0;
        }

        // FAN_LOW
        if(gu8_f_wng_fan_low_protection != gu8_f_wng_fan_low_old )
        {
            if( gu8_f_wng_fan_low_protection != 0 )
            {
                set_info_evt_errlog( FLAG_FAN_LOW, _SET_ );  // FAN_LOW
            }
            else
            {
                set_info_evt_errlog( FLAG_FAN_LOW, _RESET_ );  // FAN_LOW
            }
        }
        gu8_f_wng_fan_low_old = gu8_f_wng_fan_low_protection;
        // FAN_HIGH
        if( gu8_f_wng_fan_high_protection != gu8_f_wng_fan_high_old )
        {
            if( gu8_f_wng_fan_high_protection != 0 )
            {
                set_info_evt_errlog( FLAG_FAN_HIGH, _SET_ );  // FAN_HIGH
            }
            else
            {
                set_info_evt_errlog( FLAG_FAN_HIGH, _RESET_ );  // FAN_HIGH
            }
        }
        gu8_f_wng_fan_high_old = gu8_f_wng_fan_high_protection;
        // FAN_STOP
        if( gu8_f_wng_fan_stop_protection != gu8_f_wng_fan_stop_old )
        {
            if( gu8_f_wng_fan_stop_protection != 0 )
            {
                set_info_evt_errlog( FLAG_FAN_STOP, _SET_ );  // FAN_STOP
            }
            else
            {
                set_info_evt_errlog( FLAG_FAN_STOP, _RESET_ );  // FAN_STOP
            }
        }
        gu8_f_wng_fan_stop_old = gu8_f_wng_fan_stop_protection;
    }
    else
    {
        gu8_f_wng_fan_low_old = 0;
        gu8_f_wng_fan_high_old = 0;
        gu8_f_wng_fan_stop_old = 0;
        gu8_f_fan_fail_check = 0;
        gu8_f_fan_fail_stop = 0;
    }

    if( gu8_f_fan_fail_check != 0 )
    {
        if( gu32_c_fan_fail_timer == 0 )   // 30秒
        {
            if( (gu8_alm_type_fan_err & BIT0) == 0 )
            {
                set_info_evt_errlog( FLAG_FAN_FAIL, _SET_ );  // FAN_FAIL  (1)
                gu8_alm_type_fan_err |= BIT0;   // 0x01
                gu8_f_fan_fail_stop = 1;
                gu32_c_fan_fail_stop_timer = TIMER_5min; // 5分
            }
        }
    }
    if( gu8_f_fan_fail_stop != 0 )
    {
        if( gu8_f_fan_fail_check != 0 )
        {
            if( gu32_c_fan_fail_stop_timer == 0 )   // 5分
            {
                // 出力停止
                gu8_alm_type_fan_err |= BIT1;  // 0x02
                gu8_f_fan_fail_stop =0;
            }
            else
            {
                gu32_c_fan_fail_stop_timer--;
            }
        }
        else
        {
            set_info_evt_errlog( FLAG_FAN_FAIL, _RESET_ );  // FAN_FAIL  (1)
            gu8_alm_type_fan_err &= ~(BIT0);   // 0x01
            gu8_f_fan_fail_stop =0;
        }
    }

    if( ((gu8_alm_type_12v_err & 0x2B) != 0) ||
        ((gu8_alm_type_dischg_err & 0x01) != 0) ||
        ((gu8_alm_type_temp_err & 0x03) != 0) ||
        ((gu8_alm_type_pfc_err & 0x01) != 0) ||
        ((gu8_alm_type_fan_err & 0x02) != 0)
    )
    {
        if( gu8_f_backup_active == _ON_ )    // バックアップ中に検出?
        {
            gu8_f_backup_active_alm= 1;
        }
        else
        {
            gu8_f_backup_active_alm = 0;
        }
        hogo_output1();
    }
    else if( (gu8_alm_type_batt_err & 0x07) != 0 ) // [バッテリ異常](ラッチ系)
    {
        hogo_output2();

        if( gu8_f_susp_cha == TEMP_SUPPRES_1 ) // 温度抑止中?
        {
            gu8_f_susp_cha = TEMP_SUPPRES_5;  // 温度抑止復帰(バッテリ異常検出)
        }
        if( gu8_alm_type_batt_err != gu8_alm_type_batt_err_old )
        {
            g_eeprom_data.batt_err = gu8_alm_type_batt_err;
            eeprom_write_request( EEPROM_BATT_ERR_POS, 1, 0 );    // EEPROM書込みリクエスト(page)
        }
    }
    else if( (gu8_alm_type_chg_err & 0x07) != 0 ) // [充電回路各種異常](ラッチ系)
    {
        hogo_output3();
    }

    gu8_alm_type_batt_err_old = gu8_alm_type_batt_err;
}

/*******************************************************************************
 * Function Name: hogo_output1()
 * Description  : 保護停止1
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void hogo_output1(void)
{
  //  gu8_f_latch_alm = 1;   // ラッチ系アラーム

    /*** /12V出力 ***/
    if(gu8_f_backup_active == _ON_){
        O_12V_EN_H;    //バックアップ中の保護で電源が切れる時はログを残すためにOUTPUTなどの機能を停止するためここで直接OFFにする(例外)
    }
    gu8_f_12v_en_out        = _OUT_OFF_;        // 12V_EN OFF
    gu32_c_12v_en_out_delay = 0;

    /*** 放電停止 ***/
    gu8_f_stop_dischg =  _ON_;   //放電停止フラグON

    /*** 充電停止 ***/
    gu8_f_stop_cha= _ON_;        //充電停止フラグ

    /*** 放電/充電/FAN ***/
    gu8_f_vcc_12v_en_out        = _OUT_OFF_;    // VCC_12V_EN OFF
    gu32_c_vcc_12v_en_out_delay = 0;
}

/*******************************************************************************
 * Function Name: hogo_output2()
 * Description  : 保護停止2
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void hogo_output2(void)
{
    //gu8_f_latch_alm = 1;   // ラッチ系アラーム

    /*** /12V出力 ***/
    if( gu8_f_ac_link_restarting != 0 )   // AC_LINK Resrart中?
    {
        gu8_f_12v_en_out        = _OUT_ON_;        // 12V_EN ON
        gu32_c_12v_en_out_delay = 0;
    }

    /*** 放電停止 ***/
    gu8_f_stop_dischg =  _ON_;   //放電停止フラグON

    /*** 充電停止 ***/
    gu8_f_stop_cha= _ON_;        //充電停止フラグ
}

/*******************************************************************************
 * Function Name: hogo_output3()
 * Description  : 保護停止3
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void hogo_output3(void)
{
    //gu8_f_latch_alm = 1;   // ラッチ系アラーム

    /*** /12V出力 ***/
    if( gu8_f_ac_link_restarting != 0 )   // AC_LINK Resrart中?
    {
        gu8_f_12v_en_out        = _OUT_ON_;        // 12V_EN ON
        gu32_c_12v_en_out_delay = 0;
    }

    /*** 充電停止 ***/
    gu8_f_stop_cha= _ON_;        //充電停止フラグ
}

/*******************************************************************************
 * Function Name: hogo_output4()
 * Description  : 保護停止4
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void hogo_output4(void)
{
    //gu8_f_latch_alm = 1;   // ラッチ系アラーム

    /*** /12V出力 ***/
    if( gu8_f_ac_link_restarting != 0 )   // AC_LINK Resrart中?
    {
        gu8_f_12v_en_out        = _OUT_ON_;        // 12V_EN ON
        gu32_c_12v_en_out_delay = 0;
    }

    /*** 充電停止 ***/
    gu8_f_stop_cha= _ON_;        //充電停止フラグ
}

/*******************************************************************************
 * Function Name: hogo_output5()
 * Description  : 保護停止5 (項番4:過電流保護 2-10 [+12V各種異常])
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void hogo_output5(void)
{
    /*** /12V出力 ***/
    if( gu8_f_12v_oc_off != 0 ) // 過電流保護発生
    {
        gu8_f_12v_en_out        = _OUT_OFF_;        // 12V_EN OFF
        /*** 放電停止 ***/
        gu8_f_stop_dischg =  _ON_;   //放電停止フラグON
        /*** 充電停止 ***/
        gu8_f_stop_cha= _ON_;        //充電停止フラグ
    }
    else
    {
        if( gu8_f_ac_link_restarting == 0 )   // AC_LINK Resrart中でない?
        {
            gu8_f_12v_en_out        = _OUT_ON_;        // 12V_EN OFF
            /*** 放電 ***/
            gu8_f_stop_dischg =  _OFF_;   //放電停止フラグ
            /*** 充電 ***/
            gu8_f_stop_cha= _OFF_;        //充電停止フラグ
        }
    }
}

/*******************************************************************************
 * Function Name: hogo_release()
 * Description  : 保護解除検出
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
uint8_t u8_f_batt_removed = 0;
void hogo_release(void)
{
    //***********************************************************************************************************************************
    //      12V各種異常、放電回路異常、温度異常、FAN異常はACオフ→オンと放電完了の時→放電禁止状態であるため、条件としては電源の再起動となるため、実質的な解除は行わない
    //***********************************************************************************************************************************
    if(gu8_f_ac_on_trg == _TRG_OFF_)
    {
        gu8_f_ac_off_detected=1;
    }

    if((pi_ps_on.trg == _TRG_ON_)||(gu8_f_ac_on_trg == _TRG_ON_)&&(gu8_f_ac_off_detected==1))   // PS_OFF→PS_ON
    {
        gu8_f_ac_off_detected=0;
        //********* 充電回路各種異常 ******************************
        gu8_alm_type_chg_err=0;
        pro_cha_filter_clear();
        set_info_evt_errlog( FLAG_CHG_OC, _RESET_ );
        set_info_evt_errlog( FLAG_CHG_OV, _RESET_ );
        set_info_evt_errlog( FLAG_CHG_LV, _RESET_ );

        gu8_f_stop_cha= _OFF_;        //充電停止フラグOFF
    }

    if (gu8_f_batt_connect_trg == _TRG_OFF_)
    {
        u8_f_batt_removed = 1;
    }

    if(((gu8_f_ac_on == _ON_) && (gu8_f_batt_connect_trg == _TRG_ON_) && (u8_f_batt_removed== 1)) || // AC_ON=ONでバッテリ接続トリガ
        (( gu8_f_ac_on_trg == _TRG_ON_) && (gu8_f_batt_err_startup_exist != 0) ) || // バッテリ異常有りフラグありでPS_ON=OFFトリガ
        (gu8_f_cd_cmd_rcv != 0 )    // CDコマンド受信フラグ(バッテリ異常解除通知用)
    )
    {
        gu8_f_cd_cmd_rcv = 0;
        u8_f_batt_removed = 0;
        if( gu8_alm_type_batt_err != 0 )
        {
            //*********バッテリ異常 ******************************
            gu8_alm_type_batt_err = 0;
            g_eeprom_data.batt_err = 0;
            eeprom_write_request( EEPROM_BATT_ERR_POS, 1, 0 );    // EEPROM書込みリクエスト(page)

            pro_batt_filter_clear();

            set_info_evt_errlog( FLAG_BATT_TEMP_ALM, _RESET_ );  // BATT_TEMP_ALM  (4)
            set_info_evt_errlog( FLAG_BATT_LV, _RESET_ );  // BATT_LV  (2)
            set_info_evt_errlog( FLAG_BATT_OV, _RESET_ );  // BATT_OV  (2)

            gu8_f_stop_dischg =  _OFF_;   //放電停止フラグOFF
            gu8_f_stop_cha= _OFF_;        //充電停止フラグOFF

            gu8_f_batt_err_startup_exist = 0;
        }
    }
}

/******************************************************************************
* Function Name: pro_12v_filter_clear()
* Description  :12V各種異常フィルタークリア
* Arguments    : None
* Return Value : None
*******************************************************************************/

void pro_12v_filter_clear(void)
{
    filter_clear(&pi_low_v);
    filter_clear(&pi_high_i_on);
    filter_clear(&pi_high_i_on_50ms);
    filter_clear(&pi_high_i_of);
    filter_clear(&pi_high_i_of_h);
    filter_clear(&pi_high_v );
    filter_clear(&pi_bbu_sw_open);
}
/******************************************************************************
* Function Name: pro_cha_filter_clear()
* Description  :充電保護フィルタークリア
* Arguments    : None
* Return Value : None
*******************************************************************************/

void pro_cha_filter_clear(void)
{
    filter_clear(&pi_high_i_cha);
    filter_clear(& pi_high_v_cha_6 );
    filter_clear(& pi_low_v_shortage);
    filter_clear(& pi_low_v_shortage_5a);
}

/******************************************************************************
* Function Name: pro_dis_filter_clear()
* Description  :放電保護フィルタークリア
* Arguments    : None
* Return Value : None
*******************************************************************************/
void pro_dis_filter_clear(void)
{
    filter_clear(&pi_high_i_dis_6);
}

/******************************************************************************
* Function Name: pro_dis_filter_clear()
* Description  :温度保護フィルタークリア
* Arguments    : None
* Return Value : None
*******************************************************************************/
void pro_tmp_filter_clear(void)
{
    filter_clear(&pi_temp_fail_adu);
    filter_clear(&pi_temp_fail_bbu);
}

/******************************************************************************
* Function Name: pro_batt_filter_clear()
* Description  :バッテリ異常フィルタークリア
* Arguments    : None
* Return Value : None
*******************************************************************************/
void pro_batt_filter_clear(void)
{
    filter_clear(&pi_latch_fail);
    filter_clear(&pi_batt_low_6);
    filter_clear(&pi_batt_high_6);
}
