#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"

void ps_on_proc(void);
void burst_proc(void);
void discharge_proc(void);
void dischage_output_on(void);
void dischage_output_off(void);
void dischage_end_first(void);
void update_backup_ready(void);
uint8_t dischage_termination(void);
void charge_proc(void);
void juuden_start_stop(uint8_t start_stop_flg);
void chg_ctl_state_change(uint8_t chg_flg, uint8_t start_stop_decision, uint8_t stg_target );
void full_chg_calc(void);
void charge_proc_init(void);
void low_batt_proc(void);
void dcir_proc(void);
void dcir_response(uint8_t err_flg);
void burst_off_proc(void);
void burst_on_proc(void);
void chg_init_proc(void);
extern void set_fan_speed( uint8_t speed );
extern void set_info_evt_errlog( uint8_t flag, uint8_t status );
extern void operate_log_request( uint8_t almid );
extern uint8_t eeprom_write_request( uint32_t pos, uint32_t num, uint8_t mode );
extern void eeprom_clear_wait_queue(void);

/* S1.12 満充電検出時のCHARGE_ON, CHARGE_OKの同時ゼロ対策 */
extern void full_charge_proc(void);

/* S1.14 131F 突然満充電となる対策 */
void full_chg_calc_init(void);

/*******************************************************************************
 * Function Name: ps_on_proc()
 * Description  : PS ON 制御
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void ps_on_proc(void)
{
	if(gu8_f_before_shutdown!=1)
    {
    	 if (gu8_f_ini_ps_on == 2)
	    {
	        if (pi_ps_on.sts != gu8_f_ini_ps_on)
	        {
	            gu8_f_ini_ps_on = pi_ps_on.sts;
	            if (pi_ps_on.sts == _ON_)
	            {
	                operate_log_request(OPE_PS_ON);
	            }
	            else
	            {
                    operate_log_request(OPE_PS_OFF);
	            }
	        }
	    }
	    if( gu8_f_ps_on == _ON_ ) // PS ON
	    {
	        set_info_evt_errlog( FLAG_PS_ON, _SET_ );  // 状態情報 PS_ON信号 ON

	        gu8_f_ps_on_out = _OUT_ON_;  // PS_ON
	        gu32_c_ps_on_out_delay = 0;

	    	if(pi_ps_on.trg==_TRG_ON_ )
	    	{
	            operate_log_request(OPE_PS_ON);
	        }
	        //gu8_f_vcc_12v_en_out       = _OUT_ON_;   // VCC_12V_EN ON
	        //gu32_c_vcc_12v_en_out_delay = 0;
	    } else {
	        set_info_evt_errlog( FLAG_PS_ON, _RESET_ );  // 状態情報 PS_ON信号 OFF

	        gu8_f_ps_on_out = _OUT_OFF_; // PS_OFF
	        gu32_c_ps_on_out_delay = 0;
	    	
	    	if(pi_ps_on.trg==_TRG_OFF_ )
	    	{
	             operate_log_request(OPE_PS_OFF);
	             if (SP_AC_LINK != _ENABLE_)     //8/20
	             {
	                set_info_evt_errlog( FLAG_RESTART_READY, _RESET_ );  // RESTART READY Reset
	                gu8_f_output_restart = 0;
	             }
	        }

	    	if(gu8_f_ac_on_trg == _TRG_OFF_)
	    	{    //PS_OFF状態で停電したら復電待ちに移行
	    	    gu8_alm_type_batt_err &= (uint8_t)~BIT3;
                g_eeprom_data.batt_err = gu8_alm_type_batt_err;
                eeprom_write_request( EEPROM_BATT_ERR_POS, sizeof(g_eeprom_data.batt_err), 1 );
	    	    gu8_f_skip_reason=2;
	    	    gu8_f_before_shutdown=1;
	    	}
	    }
	//#if 0   // 仮 2026/2/18
	    /*if( gu8_f_burst_on == _ON_ ) // BURST信号
	    {
	       // set_info_evt_errlog( FLAG_BURST_ON, _SET_ );  // 状態情報 BURST信号 ON
	    	 if(pi_burst_on.trg==_TRG_ON_ ){
	                   // operate_log_request(OPE_BURST_ON);
	                }
	    } else {
	       // set_info_evt_errlog( FLAG_BURST_ON, _RESET_ );  // 状態情報 BURST信号 OFF
	    	  if(pi_burst_on.trg==_TRG_OFF_ ){
	                          //  operate_log_request(OPE_BURST_OFF);
	           }
	    }*/
  }
//#else
//  if( gu8_f_ac_on == _ON_ ) // ACあり/なし
//  {
//      set_info_evt_errlog( FLAG_BURST_ON, _SET_ );  // 状態情報 BURST信号 ON
//  } else {
//      set_info_evt_errlog( FLAG_BURST_ON, _RESET_ );  // 状態情報 BURST信号 OFF
//  }
//#endif
}

/*******************************************************************************
 * Function Name: burst_proc()
 * Description  : Burst 制御
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
uint8_t burst_state=0;
uint8_t burst_current_state = 0;

/***********************************
 *
 * 状態変化をみてOFFからOFFを防ぐ
 *
  **********************************/
void burst_proc(void)
{
    //static uint8_t burst_stage = 0;
	if(gu8_f_before_shutdown!=1)
   	{
	    switch( gu8_burst_stage )
	    {
	        /**********/
	        /* AC OFF */
	        /**********/
	        case 0:
	            if( gu8_f_ac_on == _ON_ ) // AC ON?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 1;
	            }
	            break;

	        /*******************************/
	        /* PS_OFF                      */
	        /* BURST設定=無効              */
	        /* PS_OFF_CHARGE設定=無効/有効 */
	        /*******************************/
	        case 1:
	            if( gu8_f_ac_on == _OFF_ ) // AC OFF?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 0;

	                break;
	            }
	            if( gu8_f_ps_on == _ON_ ) // PS ON?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 2;

	                break;
	            }
	            if( (g_eeprom_data.set_erp.burst == _ENABLE_) 
	                    && (g_eeprom_data.set_erp.ps_off_charge == _DISABLE_) ) // BURST設定=有効でPS_OFF_CHARGE設定=無効
	            {
	                burst_on_proc();
	                gu8_burst_stage = 3;
	                break;
	            }
	            if( (g_eeprom_data.set_erp.burst == _ENABLE_)
	                    && (g_eeprom_data.set_erp.ps_off_charge == _ENABLE_) ) // BURST設定=有効でPS_OFF_CHARGE設定=有効
	            {
	                if( gu8_f_charging_active != 0 ) // 充電開始(バッテリー未充電)
	                {
	                    burst_off_proc();
	                }
	                else
	                {
	                    burst_on_proc();
	                }

	                gu32_c_burst_out_delay = 0;
	                gu8_burst_stage = 4;
	                break;
	            }
	            break;

	        /**********/
	        /* PS ON  */
	        /**********/
	        case 2:
	            if( gu8_f_ac_on == _OFF_ ) // AC OFF?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 0;
	                break;
	            }
	            if( gu8_f_ps_on == _OFF_ ) // PS OFF?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 1;
	                break;
	            }
	            break;

	        /**************************/
	        /* PS_OFF                 */
	        /* BURST設定=有効         */
	        /* PS_OFF_CHARGE設定=無効 */
	        /**************************/
	        case 3:
	            if( gu8_f_ac_on == _OFF_ ) // AC OFF?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 0;
	                break;
	            }
	            if( g_eeprom_data.set_erp.burst == _DISABLE_ ) // BURST設定=無効
	            {
	                burst_off_proc();
	                gu8_burst_stage = 1;
	                break;
	            }
	            if( gu8_f_ps_on == _ON_ ) // PS ON?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 2;
	                break;
	            }
	            if( g_eeprom_data.set_erp.ps_off_charge == _ENABLE_ ) // PS_OFF_CHARGE設定=有効
	            {
	                if( gu8_f_charging_active != 0 ) // 充電開始(バッテリー未充電)
	                {
	                    burst_off_proc();
	                }
	                else
	                {
	                    burst_on_proc();
	                }
	                gu32_c_burst_out_delay = 0;
	                gu8_burst_stage = 4;
	                break;
	            }
	            break;

	        /**************************/
	        /* PS_OFF                 */
	        /* BURST設定=有効         */
	        /* PS_OFF_CHARGE設定=無効 */
	        /**************************/
	        case 4:
	            if( gu8_f_ac_on == _OFF_ ) // AC OFF?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 0;
	                break;
	            }
	            if( g_eeprom_data.set_erp.burst == _DISABLE_ ) // BURST設定=無効
	            {
	                burst_off_proc();
	                gu8_burst_stage = 1;
	                break;
	            }
	            if( gu8_f_ps_on == _ON_ ) // PS ON?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 2;
	                break;
	            }
	            if( gu8_f_charging_active != 0 ) // 充電開始(バッテリー未充電)
	            {
	                burst_off_proc();
	                gu8_burst_stage = 5;
	                break;
	            }
	            break;

	        /**************************/
	        /* PS_OFF                 */
	        /* BURST設定=有効         */
	        /* PS_OFF_CHARGE設定=有効 */
	        /**************************/
	        case 5:
	            if( gu8_f_ac_on == _OFF_ ) // AC OFF?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 0;
	                break;
	            }
	            if( (g_eeprom_data.set_erp.burst == _DISABLE_)
	                    || (g_eeprom_data.set_erp.ps_off_charge == _DISABLE_) ) // BURST設定=無効 または PS_OFF_CHARGE設定=無効
	            {
	                burst_off_proc();
	                gu8_burst_stage = 1;
	                break;
	            }
	            if( gu8_f_ps_on == _ON_ ) // PS ON?
	            {
	                burst_off_proc();
	                gu8_burst_stage = 2;
	                break;
	            }
	            if( gu8_f_charging_active == 0 ) // 充電完了/停止
	            {
	                burst_on_proc();
	                gu8_burst_stage = 4;
	                break;
	            }
	            break;

	        default:
	            break;
	    }


	    if( burst_state == _ON_ )
	    {
	        uint8_t now_state = 0;

	        if( gu_f_burst_i_over == 1 )
	        {
	            now_state = 1; // over
	        }
	        else if( gu_f_burst_i_over == 0 )
	        {
	            now_state = 2; // good
	        }

	        // ===== 状態変化時のみ処理 =====
	        if(now_state != 0&& now_state != burst_current_state )
	        {
	            burst_current_state = now_state;

	            if( now_state == 1 ) // over → OFF
	            {
	                gu8_f_burst_out = _OUT_OFF_;
	                gu32_c_burst_out_delay = 0;

	                set_info_evt_errlog( FLAG_BURST_ON, _RESET_ );
	                operate_log_request(OPE_BURST_OFF);
	            }
	            else if( now_state == 2 ) // good → ON
	            {
	                gu8_f_burst_out = _OUT_ON_;
	                gu32_c_burst_out_delay = 0;

	                set_info_evt_errlog( FLAG_BURST_ON, _SET_ );
	                operate_log_request(OPE_BURST_ON);
	            }
	        }
	    }
	    else if(burst_state == _OFF_ )
	    {
	        burst_current_state = 0;
	    }
   }
}

void burst_off_proc(void)
{
    if( (burst_state == _ON_) && (gu_f_burst_i_over != 1) )
    {
        set_info_evt_errlog(FLAG_BURST_ON, _RESET_);
        operate_log_request(OPE_BURST_OFF);
    }
    gu8_f_burst_out = _OUT_OFF_;
    burst_state = _OFF_;
    gu32_c_burst_out_delay = 0;
}

void burst_on_proc(void)
{
    if( gu_f_burst_i_over != 1 )
    {
        gu8_f_burst_out = _OUT_ON_;     // Burst ON
    }
    burst_state=_ON_;
}

/*******************************************************************************
 * Function Name: discharge_proc()
 * Description  : 放電(バックアップ)制御
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void discharge_proc(void)
{
    //static uint8_t dischg_ps_on_stage = 0;
    //static uint8_t dischg_ps_off_stage = 0;
    static uint32_t c_batt_on_delay = 0;                 //static
    static uint32_t c_soc_check_delay = 0;               //static
    static uint32_t c_backup_time = 0;                   //static
    static uint8_t  f_backup_unlimit = 0;                //static
    //static uint8_t  f_ps_on_old = _OFF_;
    //static uint8_t  f_ps_on_backup_old = _DISABLE_;
    uint8_t ret;

	if(gu8_f_before_shutdown!=1)  //放電終止を検出したら処理しない
  	{
	    gu8_f_stop_condition= ((gu8_f_susp_dischg == _ON_) ||(gu8_f_stop_dischg == _ON_));

	    if (gu8_f_first_check == _ON_)
	    {
	        gu8_f_first_check = _OFF_;
	        if ((gu8_f_stop_condition == _ON_) &&(gu8_f_ac_on == _OFF_))
	        {
	            gu8_f_initial_skip = _ON_;
	        }
	    }

	    if ((gu8_f_stop_condition == _OFF_) ||(gu8_f_ac_on == _ON_))
	    {
	        gu8_f_initial_skip = _OFF_;
	    }

	    if (gu8_f_stop_condition == _ON_)
	    {
            set_info_evt_errlog(FLAG_BATT_ON, _RESET_);
            if ((gu8_f_ac_on == _OFF_) &&(gu8_f_initial_skip == _OFF_))
            {

                if( (gu8_alm_type_batt_err & BIT0) != 0 ||(gu8_alm_type_batt_err & BIT1) != 0||(gu8_alm_type_batt_err & BIT2) != 0)
                {
                    gu8_alm_type_batt_err |= BIT3;
                    g_eeprom_data.batt_err = gu8_alm_type_batt_err;
                    eeprom_write_request( EEPROM_BATT_ERR_POS, sizeof(g_eeprom_data.batt_err), 1 );
                }

                gu8_f_before_shutdown = 1;
                gu8_f_skip_reason = 3;
            }
            gu8_f_backup_active = _OFF_;
            gu8_dischg_ps_on_stage = 0;
            gu8_dischg_ps_off_stage = 0;
            return;
	    }

	    if( gu8_f_ps_on == _ON_ )  // PS_ON
	    {
	        gu8_dischg_ps_off_stage = 0;
	        switch( gu8_dischg_ps_on_stage )
	        {
	            case 0:
	                if( gu8_f_ps_on != gu8_f_ps_on_old )  // PS_ON OFF->ON時 1回
	                {
	                    update_backup_ready();
	                }
	                if( gu8_f_ac_on == _OFF_)   // ACなし?
	                {
	                    /***** 放電開始 ******/
	                    dischage_output_on();
	                    /*********************/
	                    gu8_c_dischg_term = 0;      // 放電終止カウンタ0

	                    c_batt_on_delay = (TIMER_1000ms+TIMER_200ms);   // ACなしから1秒後にBATT_ONにする
	                    c_soc_check_delay = TIMER_20ms;   // SOCチェック開始ディレー

	                    if( INFO_COMMAND_STATUS1_BACKUP_READY == _SET_ )   // 状態情報 BACKUP_READY セット
	                    {
	                        c_backup_time = (SP_MAX_BACKUP_TIME * TIMER_1000ms * 60);     // 最大バックアップ時間(分) val * 60s
	                        if( SP_MAX_BACKUP_TIME == 0 )
	                        {
	                            f_backup_unlimit = 1;    // 無制限
	                        }
	                        else
	                        {
	                            f_backup_unlimit = 0;
	                        }
	                    }
	                    else
	                    {
	                        c_backup_time = (SP_MIN_BACKUP_TIME * TIMER_1000ms);          // 最小バックアップ時間(秒) val * 1s
	                        f_backup_unlimit = 0;
	                    }

	                    gu8_f_dischg_under_1s = 1;  // 放電1秒未満 ON
	                    gu8_f_dischg_up_1s = 0;     // 放電1秒以上 OFF

	                    gu8_f_dischg_start_sek = 1;    // 積算データ:バッテリ総放電回数　記録用フラグ

	                    gu8_dischg_ps_on_stage = 1;
	                }
	                else
	                { // ACあり
	                    set_info_evt_errlog( FLAG_BATT_ON, _RESET_ );   // 状態情報 BAT_ON リセット(イベント)

	                    gu8_f_backup_active = _OFF_;    // バックアップ中 OFF

	                    if( gs_set_parameter.ps_on_backup != gu8_f_ps_on_backup_old)  // PS_ON_BACKUP設定変化?
	                    {
	                        update_backup_ready();
	                    }
	                    if( gu8_backup_enable_cmd != 0 )
	                    {
	                        gu8_backup_enable_cmd = 0;

	                    }
	                    if( gu8_backup_off_cmd != 0 )
	                    {
	                        gu8_backup_off_cmd = 0;

	                    }
	                }
	                break;

	            case 1:
	                if( (c_backup_time != 0) || (f_backup_unlimit != 0) )     // 時間内 or 無制限
	                {
	                    if( gu8_f_ac_on == _ON_ )  // ACあり?
	                    {
	                        gu8_dischg_ps_on_stage = 3;
	                        break;
	                    }

	                    if( c_batt_on_delay == 0 )   // ACなしから1秒後にBATT_ONにする
	                    {
	                        if( gu8_f_backup_active == _OFF_ )
	                        {
	                            gu32_c_ac_link_timer = (SP_MAX_BACKUP_TIME * TIMER_1000ms * 60);     // AC_LINK有効タイマ(最大バックアップ時間(分) val * 60s)
	                            gu8_f_backup_start_sek = 1;     // 積算データ:バックアップ回数　記録用フラグ
	                        	operate_log_request(OPE_BATT_ON);   //opelog
	                            g_eeprom_data.back_up=1;    /*F120 バックアップした場合にEEPROMに書き込む*/
	                            eeprom_write_request(EEPROM_BACK_UP_POS,sizeof(g_eeprom_data.back_up),1);
	                        }
	                        gu8_f_backup_active = _ON_;    // バックアップ中 ON

	                        set_info_evt_errlog( FLAG_BATT_ON, _SET_);   // 状態情報 BAT_ON セット(イベント)
	                        gu8_f_dischg_under_1s = 0;  // 放電1秒未満 OFF
	                        gu8_f_dischg_up_1s = 1;     // 放電1秒以上 ON
	                    }
	                    else
	                    {
	                        c_batt_on_delay--;
	                        break;
	                    }

	                    if( c_backup_time != 0 )   // バックアップ中になってからカウントダウン
	                    {
	                        c_backup_time--;
	                    }

	                    if( c_soc_check_delay == 0 )  // 20ms
	                    {
	                        if( INFO_CHARGE_STATUS_CHARGE_OK == _SET_ )
	                        {
	                            if( gi8_d_soc_mah <= SOC_80 )  // BATT_ON信号よりも20ms以上ディレーさせること
	                            {
	                                set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );      // 満充電(充電完了)イベント リセット
	                            }
	                        }
	                    }
	                    else
	                    {
	                        c_soc_check_delay--;
	                    }

	                    if( gu8_backup_enable_cmd != 0 )
	                    {
	                        if( SP_MAX_BACKUP_TIME == 0 )
	                        {
	                           f_backup_unlimit = 1;    // 無制限
	                        }
	                        else
	                        {
	                           f_backup_unlimit = 0;
	                        }
	                        gu8_backup_enable_cmd = 0;
	                        set_info_evt_errlog( FLAG_BACKUP_READY, _SET_ );   // 状態情報 BACKUP_READY セット BE側でセット

	                        c_backup_time = (SP_MAX_BACKUP_TIME * TIMER_1000ms* 60); // 最小バックアップ時間(秒)
	                    }
	                    if( gu8_backup_off_cmd != 0 )
	                    {
	                        gu8_backup_off_cmd = 0;
	                        set_info_evt_errlog( FLAG_BACKUP_READY, _RESET_ );  // 状態情報 BACKUP_READY リセット BF側でリセット
	                        c_backup_time = (SP_MIN_BACKUP_TIME * TIMER_1000ms); // 最小バックアップ時間(秒)
	                        f_backup_unlimit = 0;     // 無制限解除
	                    }
	                    ret = dischage_termination();// 放電終止
	                    if( ret != 0 )
	                    {
	                    	gu8_f_skip_reason=1;
	                        gu8_f_dischg_term = 1;
	                        gu8_dischg_ps_on_stage = 0;
	                    }
	                }
	                else
	                {

	                    /***** 放電停止1 ******/
	                    dischage_end_first();
	                    /*********************/
	                    gu8_f_skip_reason=1;
	                    gu8_f_backup_active = _OFF_;    // バックアップ中 OFF
	                    gu8_dischg_ps_on_stage = 0;
	                }
	                break;

	            case 2:
	                break;

	            case 3:
	                if( (gu8_f_ac_on == _ON_ ) && (gu16_ad_acdc12v_v >= ADC12V_CALL_BACK) ) // ACありでAC/DC12V電圧あり(11Vとする)?
	                {
	                    /***** 放電停止 ******/
	                    dischage_output_off();
	                    /*********************/

	                    if( gu8_f_backup_active == _ON_ ) // バックアップ中
	                    {
	                    	operate_log_request(OPE_BATT_OFF);   //opelog

	                        if( SP_AC_LINK == _ENABLE_ ) // AC_LINK有効?
	                        {
	                            if( SP_MAX_BACKUP_TIME != 0 )
	                            {
	                                gu8_f_ac_link = 1;
	                            }
	                        }
	                        else
	                        {
	                            if( gu8_f_output_restart != 0 )  // OUTPUT RESTARTコマンド受信
	                            {
	                                gu8_f_ac_link = 2;
	                            }
	                        }
	                    }
	                    gu8_f_backup_active = _OFF_;    // バックアップ中 OFF
	                    gu8_dischg_ps_on_stage = 0;
	                }
	                break;

	            default:
	                break;
	        }
	    } else {  // PS_OFF
	        gu8_dischg_ps_on_stage = 0;
	        switch( gu8_dischg_ps_off_stage )
	        {
	            case 0:
	                set_info_evt_errlog( FLAG_BATT_ON,      _RESET_ );   // 状態情報 BAT_ON       リセット(イベント)

	                gu8_dischg_ps_off_stage = 1;
	        	
	        	    if(gu8_f_charge_output == _ON_)
	        	    {
	                    /***** 放電停止1 ******/
	        	        dischage_end_first();
	                    /*********************/
	        	        gu8_f_skip_reason=1;
	        		    gu8_dischg_ps_off_stage = 1;
	                }
	        	
	        	    gu8_f_backup_active = _OFF_;    // バックアップ中 OFF

	                gu8_f_dischg_term = 1;
	                break;
	            case 1:
	            default:
	                break;
	        }
	    }
	    gu8_f_ps_on_old = gu8_f_ps_on;
	    gu8_f_ps_on_backup_old = gs_set_parameter.ps_on_backup;
  	}
}

/*******************************************************************************
 * Function Name: update_backup_ready()
 * Description  : ログ
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void update_backup_ready(void)
{
   if (gs_set_parameter.ps_on_backup == _ENABLE_)
   {
       set_info_evt_errlog(FLAG_BACKUP_READY, _SET_);
   }
   else
   {
       set_info_evt_errlog(FLAG_BACKUP_READY, _RESET_);
   }
}

/*******************************************************************************
 * Function Name: dischage_output_on()
 * Description  : 放電開始
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void dischage_output_on(void)
{
    gu8_f_vcc_12v_en_out        = _OUT_ON_;   // VCC_12V_EN ON
    gu32_c_vcc_12v_en_out_delay = 0;

    gu8_f_batchg_en_out        = _OUT_OFF_;   // BATCHG_EN OFF
    gu32_c_batchg_en_out_delay = 0;

//#ifndef _DEBUG_ON_
    gu8_f_batt_en_out        = _OUT_ON_;      // BATT_EN ON
    gu32_c_batt_en_out_delay = 0;
//#endif

    gu8_f_converter_pwm        = _OUT_ON_;    // Converter PWM OFF
    gu32_c_converter_pwm_delay = 0;

    gu8_f_dischg12v_en_out        = _OUT_ON_; // DISCHG12V_EN ON
    gu32_c_dischg12v_en_out_delay = TIMER_8ms;

    //gu8_f_fan_pwm = _OUT_ON_;
    //set_fan_speed(FAN_HIGH_SPEED);    // FAN高速回転

    gu8_f_charge_output = _ON_;   // 放電出力中 ON
}

/*******************************************************************************
 * Function Name: dischage_output_off()
 * Description  : 放電停止
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void dischage_output_off(void)
{
    if( gu8_f_charge_output == _ON_ )  // 放電出力中?
    {
        gu8_f_dischg12v_en_out        = _OUT_OFF_; // DISCHG12V_EN OFF
        if( gu8_f_ps_on == _ON_ )  // PS_ON
        {
            gu32_c_dischg12v_en_out_delay = 0;
        }
        else
        {
            gu32_c_dischg12v_en_out_delay = TIMER_5ms;
        }
        gu8_f_batt_en_out        = _OUT_OFF_;      // BATT_EN OFF
        gu32_c_batt_en_out_delay = TIMER_5ms;

        gu8_f_converter_pwm        = _OUT_OFF_;    // Converter PWM OFF
        gu32_c_converter_pwm_delay = TIMER_5ms;

        gu8_f_charge_output = _OFF_;   // 放電出力中 OFF
    }
}

/*******************************************************************************
 * Function Name: dischage_end_first()
 * Description  : 放電終了1段階
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void dischage_end_first(void)
{
   // gu8_f_12v_en_out=_OUT_OFF_;
	gu8_f_fan_pwm = _OUT_OFF_;
	gu32_c_fan_pwm_delay = TIMER_5ms;

	//eeprom_clear_wait_queue();
	if(gu8_f_ps_on == _ON_)
	{
	    eeprom_write_request( EEPROM_BATT_POS, 112, 0 );
	}

	//放電終止フラグ
	gu8_f_before_shutdown = 1;
}

/*******************************************************************************
 * Function Name: dischage_termination()
 * Description  : 放電終止
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
uint8_t dischage_termination(void)
{
    uint8_t detect = 0;
    uint16_t volt;
    uint8_t ret = 0;

    if( gu8_f_batt_connect == _BATT1_CONNECT_ )
    {
        volt = BATT1_4700MV;   // BATT1 4.7V
    }
    else
    {
        // バッテリ接続なし
        /***** 放電停止1 ******/
        dischage_end_first();
        /*********************/
        operate_log_request(OPE_FINAL_VOLTAGE);
        gu8_f_backup_active = _OFF_;    // バックアップ中 OFF
        return(1);
    }

    if( gu16_ad_batt_v < volt )   // BATT電圧(mV)が終止判定電圧より低い
    {
        if( ++gu8_c_dischg_term >= 100 )    /* 100回連続検出(100ms) --> S1.14 144F　アップダウンカウンタに変更 */
        {
           // ログ FINAL_VOLTAGE
            /***** 放電停止1 ******/
            dischage_end_first();
            /*********************/
            operate_log_request(OPE_FINAL_VOLTAGE);
            gu8_f_backup_active = _OFF_;    // バックアップ中 OFF
            ret = 1;
        }
    }
    /* S1.14 144F対応 従来はしきい値以上となったらカウンタをゼロに戻していたが、カウント値を1だけ減算する */
    else
    {
        if (gu8_c_dischg_term > 0)
        {
            --gu8_c_dischg_term;
        }
    }

    return ret;

#if 0   /* S1.14 144F対策で従来方法をコメントアウトして残す */
    if( gu8_f_batt_connect == _BATT1_CONNECT_ )
    {
        volt = BATT1_4700MV;   // BATT1 4.7V
    }
    else
    {
        detect = 2;            // バッテリ接続なし
    }

    if( gu16_ad_batt_v < volt )   // BATT電圧(mV)が終止判定電圧より低い
    {
        detect = 1;
    }

    if( detect == 1)
    {
        if( ++gu8_c_dischg_term >= 100 )    // 100回連続検出(100ms)
        {
           // ログ FINAL_VOLTAGE
            /***** 放電停止1 ******/
        	dischage_end_first();
            /*********************/
        	operate_log_request(OPE_FINAL_VOLTAGE);
        	gu8_f_backup_active = _OFF_;    // バックアップ中 OFF
            ret = 1;
        }
    }
    else if( detect == 2 )
    {
         /***** 放電停止1 ******/
        dischage_end_first();
        /*********************/
        operate_log_request(OPE_FINAL_VOLTAGE);
        gu8_f_backup_active = _OFF_;    // バックアップ中 OFF
        ret = 1;
    }
    else
    {
        gu8_c_dischg_term = 0;
    }
    return ret;
#endif
}

/*******************************************************************************
 * Function Name: charge_proc()
 * Description  : 充電制御
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
//#define DEVELOP_DAY_END    /*** 一日の終わりに活かすことで、作り途中の充電制御を丸ごとコメントアウト可能 ***/
//#define HIS_ON_MODE
#define _CHG_CTL_DEBUG_ON_

#ifndef DEVELOP_DAY_END
#ifdef HIS_ON_MODE
#define SIZ_HIS 128
uint16_t u16_debug_his[SIZ_HIS];
uint16_t u16_u16_debug_his_wp = 0;
uint8_t u8_susp_init_for_his = 0;
uint8_t u8_force_stop_init_for_his = 0;

void his_temp2(uint16_t dat)
{
    u16_debug_his[u16_u16_debug_his_wp] = dat;
    if (u16_u16_debug_his_wp < (SIZ_HIS - 1))
    {
        ++u16_u16_debug_his_wp;
    }
}
#endif
#endif

#if 0
#ifdef HIS_ON_MODE
his_temp2(aaa);
#endif
#endif

#ifndef  DEVELOP_DAY_END
/*** 実際使用する変数 ***/
uint8_t u8_chg_ctl_stg = 0;        // 充電制御ステージ
uint8_t u8_f_main_chg_ok = 0;      // 主充電条件成立/不成立フラグ
uint8_t u8_f_sub_chg_ok = 0;       // 補充電条件成立/不成立フラグ
float f_chg_ctl_batt_vol_v = 0.0;      // バッテリ電圧(V)(充電制御用に用意)
float f_chg_ctl_batt_vol_mv = 0.0;     // バッテリ電圧(mV)(満充電計算用に用意)
uint32_t u32_main_chg_timer = 0;       // 主充電タイマー
uint32_t u32_sub_chg_timer = 0;        // 補充電タイマー
uint8_t u8_f_main_chg_time_out = 0;    // 主充電タイマータイムアウトフラグ
uint8_t u8_f_sub_chg_time_out = 0;     // 補充電タイマータイムアウトフラグ
//uint8_t u8_f_charge_cmd_mode = 0;      // 今回の充電が強制充電コマンドによるものであることを通知するフラグ
#if 0
uint8_t u8_f_chg_suspend_reason = 0;              // 充電中断理由フラグ
#endif
uint8_t u8_f_idle_state_init = 0;                 // アイドル状態_初期化フラグ
uint8_t u8_f_main_charge_state_init = 0;          // 主充電状態_初期化フラグ
uint8_t u8_f_sub_charge_state_init = 0;           // 補充電状態_初期化フラグ
#if 0
uint8_t u8_f_suspend_charge_state_init = 0;       // 充電中断状態_初期化フラグ
uint8_t u8_f_charge_force_stop_state_init = 0;    // 充電強制禁止状態_初期化フラグ
#endif
uint8_t u8_f_charge_start_ok = 0;    // 充電開始完了フラグ(フラグ制御用)

/* S1.14 番号無し 温度抑止から復帰時は満充電検出を5分待たない処理を追加 */
uint8_t u8_f_recharge_from_suspend = 0;
uint8_t enable_delta_v = 0;

/* ※満充電計算(温度)に必要な変数 */
#define DTDT_TEMP_SUM_PERIOD TIMER_1000ms     // 温度データ引用周期
#define DTDT_DATA_AVE_PERIOD TIMER_6000ms     // 温度データ平均化周期
#define DTDT_FULL_CHG_CHK_PERIOD TIMER_60s    // 満充電確認周期
#define DTDT_TEMP_SAMPLE_DATA_SIZE 6          // 満充電計算 平均化する温度サンプル数
#define DTDT_1M_DIVIDE_6S 10
#define DTDT_FULL_CHARGE_SIKIICHI 15         // 単位:0.1℃
#define DTDT_SIKIICHI_OVER_KOSUU_BORDER 6    // 1.5℃を何個越えていたら満充電とするか
uint16_t u16_c_dtdt_ad_sampling_timer = 0;                 // 温度データ引用(1s)
uint16_t u16_c_dtdt_ave_and_comp_timer = 0;                // 温度データ平均化(6s)
uint16_t u16_c_dtdt_soc_full_chg_chk_timer = 0;            // 1分前と比較(SOC満充電確認) & 新データ-->旧データへの引っ越し(1m)
uint8_t u8_f_dtdt_full_chg_chk_start = 0;                  // 満充電検出開始フラグ(2m経ったら以降許可)
int32_t i32_dtdt_temp_sum = 0;                             // 6秒間のデータの合算
int16_t i16_dtdt_set_old_1min[DTDT_1M_DIVIDE_6S] = {0};    // 2分前~1分前の温度を入れておく配列[10]    // ※添え字的に比較の配列を入れ替えた方がやりやすそうと思った。
int16_t i16_dtdt_set_new_1min[DTDT_1M_DIVIDE_6S] = {0};    // 1分前~現在の温度を入れておく配列[10]     //   それで、1分ごとの満充電チェックが終わったら、1分前~現在のデータを丸ごと昔のデータの方に引っ越しし、１つ前の昔のデータはそこで上塗りされる。
uint8_t u8_c_dtdt_set_new_1min_wp = 0;                     // 1分前~現在温度記録配列のライトポインタ
uint8_t u8_c_dtdt_temp_rise_up_count = 0;                   // 1分間で1.5℃を越えた回数を記録

/* ※満充電計算(バッテリV)に必要な変数 */
#define MINUS_DV_DOWN_SHIKIICHI 40.0                    // 満充電判断基準値(ピーク値 - x)
#define MINUS_DV_KAISU_SHIKIICHI 10                     // 満充電とする連続回数
#define MINUS_DV_DISABLE_TIME TIMER_5min                // 充電開始後、-ΔVを行わない期間(単位:ms)
#define MINUS_DV_CHECK_PERIOD TIMER_5000ms              // -ΔV確認周期
#define MINUS_DV_PEAK_VAL_SAMPLE_PERIOD TIMER_1000ms    // ピーク算出用参照周期
#define MINUS_DV_PEAK_VAL_AVE_KAZU 5                    // ピーク算出用データ個数
uint16_t u16_c_minus_dv_check_timer = 0;                // -ΔV判断(5s)
uint16_t u16_c_minus_dv_peak_samp_timer = 0;            // ピーク電圧算出用サンプリングタイマー(1s)
float f_batt_v_peak = 0.0;                              // バッテリ電圧最大値(ピーク値) ※これも5秒ごととする
float f_batt_v_peak_calc_sample_sum = 0;                // バッテリ電圧最大値(ピーク値)算出用合計値
uint8_t u8_c_minus_dv_consecutive_occurrence = 0;               // -ΔV連続該当回数カウンタ

/*** 仮の制御用フラグ ***/
uint8_t u8_f_afterer_power_restored = 0;    // 復電後フラグ(_ON_:復電後 _OFF_:復電後ではない)

/*** 仮のタイマーカウンタ ***/
uint32_t u32_c_sub_chg_inhibited_timer = 0;    // 補充電開始禁止条件用タイマー(ゆくゆくは復電後タイマーがグローバルでできる予定)

/*** 仮の制御系参照変数 ***/
//uint8_t chg_stop_kari_flg = 0;          // 充電停止指示フラグ　代理
//uint8_t chg_susp_kari_flg = 0;          // 充電中断指示フラグ　代理
//uint8_t batt_reconnect_kari_flg = 0;    // バッテリ再接続フラグ　代理

/*** 数値制御用define ***/
#define SOC_MAX_PERSENT        100    // SOC最大パーセンテージ
#define CHARGE_START_KIJUN_SOC 80     // 充電開始基準SOCパーセンテージ
#define SUB_CHARGE_SIKIICHI    7.8    // 補充電電圧閾値
#define MAIN_CHARGE_TIMER_TIMEOUT_VALUE 12900000    // 主充電タイマータイムアウト基準値(215(m)*60(s)*1000(ms))
#define SUB_CHARGE_TIMER_TIMEOUT_VALUE  2700000     // 補充電タイマータイムアウト基準値(45(m)*60(s)*1000(ms))
#define SUB_CHARGE_TIMER_KINSHI_VALUE   3600000     // 補充電禁止条件用タイマー(1(h)*60(m)*60(s)*1000(ms))

/*** コマンド用define ***/
#define _JUSIN_NASHI_ 0    // 受信コマンド　受信あり(電源制御内共有)
#define _JUSIN_ARI_   1    // 受信コマンド　受信なし(電源制御内共有)

#define _CHARGE_ON_STOP_  0    // CHARGE_ONコマンド　充電停止
#define _CHARGE_ON_START_ 1    // CHARGE_ONコマンド　バッテリ主充電開始

#define _CHARGE_OFF_CLEAR_  0    // CHARGE_OFFコマンド　充電停止クリア
#define _CHARGE_OFF_KINSHI_ 1    // CHARGE_OFFコマンド　全バッテリ充電停止(強制充電停止状態)

#define _IDLE_STATE_              0    // アイドル状態
#define _MAIN_CHARGE_STATE_       1    // 主充電状態
#define _SUB_CHARGE_STATE_        2    // 補充電状態
#define _SUSPEND_CHARGE_STATE_    3    // 充電中断状態
#define _CHARGE_FORCE_STOP_STATE_ 4    // 充電強制禁止状態

/*** 制御用フラグ用define ***/
#define _JUUDEN_STOPING_ 0    // 充電停止中
#define _JUUDEN_DOING_   1    // 充電中

#define _JOUKEN_NG_ 0
#define _JOUKEN_OK_ 1

#define _JUUDEN_STOP_FLG_  0    // 充電停止指示
#define _JUUDEN_START_FLG_ 1    // 充電開始指示

#define _CHARGE_FINISH_      0    // 充電停止
#define _MAIN_CHARGE_START_  1    // バッテリ主充電開始

#define _TIME_IN_  0
#define _TIME_OUT_ 1

//#define _CHG_MODE_FALSE_ 0
//#define _CHG_MODE_TRUE_  1

#define _CHG_SUSPEND_NASHI_   0    // 充電中断していない
#define _CHG_SUSPEND_TEMP_    1    // 充電温度抑止
#define _CHG_SUSPEND_AC_STOP_ 2    // ACオフおよび停電
#define _CHG_SUSPEND_PS_OFF_  3    // PS_OFF_CHARGE:無効状態でのPS_ON --> OFF時

#define _CHG_INIT_NOT_EXECUTE_ 0    // 充電ステージ各種状態init_未実行
#define _CHG_INIT_COMPLETE_    1    // 充電ステージ各種状態init_完了
#endif

void charge_proc(void)
{
    /* S1.14で追加 */
    uint8_t lvl_sta_trg1;
    uint8_t lvl_sta_trg2;

#ifndef  DEVELOP_DAY_END
    /*** 以下にcharge_proc用initを配置 ***/
    // 各フラグの0クリア,満充電計算用タイマー各種や配列各種のクリア　など
    // charge_proc_init();    // 要る？

    // バッテリ電圧計算(V,mV)
#ifndef _DEBUG_DATA_ON_
    f_chg_ctl_batt_vol_v = gu16_ad_batt_v * 0.001;
#endif

#ifdef _CHG_CTL_DEBUG_ON_    // 充電制御デバッグ用 // 要するにこれは通常操作で設定されない(デバッグ値で固定)
    //f_chg_ctl_batt_vol_v = 8.0;    // バッテリ電圧:8.0V
    //f_chg_ctl_batt_vol_mv = f_chg_ctl_batt_vol_v * 1000;
    //gu8_f_ps_on = 1;    //PS_ON:ON
#endif
    if( gu8_f_ac_on_trg == _TRG_ON_)    // 復電したら復電後フラグ(仮)を立てる
    {
        u8_f_sub_chg_ok = _JOUKEN_NG_;
        u8_f_afterer_power_restored = _ON_;
        u32_c_sub_chg_inhibited_timer = 0;
    }

    if( u8_f_afterer_power_restored == _ON_ )
    {
        if( u32_c_sub_chg_inhibited_timer >= SUB_CHARGE_TIMER_KINSHI_VALUE )
        {
            u8_f_afterer_power_restored = _OFF_;
            g_eeprom_data.back_up=0;               /*F120 1時間経過で解除*/
            eeprom_write_request(EEPROM_BACK_UP_POS,sizeof(g_eeprom_data.back_up),1);
        }
        else
        {
            u32_c_sub_chg_inhibited_timer++;
        }
    }

    // 充電制御ステージ
    switch( u8_chg_ctl_stg )
    {
        /**********************************************************************************/
        case _IDLE_STATE_:    /*** アイドル状態 ***/
        /**********************************************************************************/
            // アイドル状態初期化処理
            if( u8_f_idle_state_init == _CHG_INIT_NOT_EXECUTE_ )
            {
#ifdef HIS_ON_MODE
his_temp2(1);
u8_force_stop_init_for_his = 0;
#endif
                u8_f_idle_state_init = _CHG_INIT_COMPLETE_;

                // 制御用変数初期化
                gu8_f_charge_cmd_mode = _CHG_MODE_FALSE_;
                u8_f_main_charge_state_init = _CHG_INIT_NOT_EXECUTE_;
                u8_f_sub_charge_state_init = _CHG_INIT_NOT_EXECUTE_;

#if 0
                u16_c_dtdt_ad_sampling_timer = 0;
                u16_c_dtdt_ave_and_comp_timer = 0;
                u16_c_dtdt_soc_full_chg_chk_timer = 0;
                u8_f_dtdt_full_chg_chk_start = _DISABLE_;
                i32_dtdt_temp_sum = 0;
                u8_c_dtdt_set_new_1min_wp = 0;
                u8_c_dtdt_temp_rise_up_count = 0;

                gu32_c_minus_dv_disable = 0;
                u16_c_minus_dv_check_timer = 0;
                f_batt_v_peak = 0.0;
                u8_c_minus_dv_consecutive_occurrence = 0;
                for( uint8_t i = 0; i < 10; i++ )
                {
                    i16_dtdt_set_old_1min[i] = 0;
                    i16_dtdt_set_new_1min[i] = 0;
                }
#endif
                /* S1.14 131F対策 満充電計算用変数の初期化処理(S1.14で関数にした） */
                full_chg_calc_init();

                gu8_f_charge_inhibited = 0;
            }

            // アイドル状態 --> 充電強制禁止状態
            if( (gu8_f_charge_off_cmd == _JUSIN_ARI_ ) || (gu8_f_charge_off == _CHARGE_OFF_KINSHI_) )    // CHARGE_OFF(1)受信時
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _CHARGE_FORCE_STOP_STATE_);    // 状態遷移
                break;
            }

            // 主充電条件成立/不成立確認
            if( ((gu8_f_ac_on_trg == _TRG_ON_) && (gi8_d_soc_mah <= CHARGE_START_KIJUN_SOC))         // 復電 && SOC80%以下
             || (pi_batt_not.trg == _TRG_OFF_)                                                       // バッテリ再接続
             || ((gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_START_)))    // CHARGE_ON:1を受信(バッテリ主充電開始)
            {
                u8_f_main_chg_ok = _JOUKEN_OK_;
            }
            else
            {
                u8_f_main_chg_ok = _JOUKEN_NG_;
            }

            // 補充電条件成立/不成立確認(こちら有効レベル3でも使用するためこの位置)
            if( u8_f_afterer_power_restored != _ON_ )    // 復電から1時間以内以外の場合
            {
                if((f_chg_ctl_batt_vol_v <= SUB_CHARGE_SIKIICHI)        // 補充電電圧閾値(7.8V)以下
                        || (gi8_d_soc_mah <= CHARGE_START_KIJUN_SOC))    // SOC(mAh)が80%以下
                {
                    u8_f_sub_chg_ok = _JOUKEN_OK_;
                }
                else
                {
                    u8_f_sub_chg_ok = _JOUKEN_NG_;
                }
            }
#if 1
            if( gu8_f_ac_on != _ON_ )    // ACが無ければ充電しない
            {
                break;
            }
#endif
            // 自動充電_有効レベル判別
            if( SP_AUTO_CHARGE == _DISABLE_ )    // 自動充電無効時(有効レベル3の条件を包含しない)
            {
                /* S1.14 番号無し 主充電の起動条件に(gu8_f_susp_cha == 0)と「PS_ONもしくはPS_OFF充電が有効」の条件を追加する(Copilotのソース解析結果より） */
#if 0
                if( (gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_START_)
                 && (gu8_f_stop_cha != _ON_)
                 //&& (gu8_f_susp_cha != 1)
                 && (gu8_f_dcir_check_doing != 1) )    // DCIR測定都合
#endif
                if( (gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_START_)
                 && (gu8_f_stop_cha != _ON_)
                 && (gu8_f_susp_cha == 0)
                 && (gu8_f_dcir_check_doing != 1)
                 && ((gu8_f_ps_on == _ON_) || ((gu8_f_ps_on == _OFF_) && (g_eeprom_data.set_erp.ps_off_charge == _ENABLE_)))
                )
                {
                    // アイドル状態 --> 主充電状態

                    /* S1.14 131F対策 満充電じゃないのに100%となる問題の対策 */
                    full_chg_calc_init();

                    u8_f_charge_start_ok = 0;
                    gu8_f_charge_cmd_mode = _CHG_MODE_TRUE_;
                    chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                    if( u8_f_charge_start_ok == 1 )
                    {
                        set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );      // 充電完了(0)
                        set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
                        u8_f_charge_start_ok = 0;
                    }
                }
            }
            else    // 自動充電有効レベル1,2,3時(有効レベル3の条件を包含する)
            {
                if( gu8_f_charge_ok_clear == 1 )    // 満充電がクリアされたとき(例外的動作)
                {
                    /* S1.14 番号無し 主充電の起動条件に(gu8_f_susp_cha == 0)と「PS_ONもしくはPS_OFF充電が有効」の条件を追加する(Copilotのソース解析結果より） */
#if 0
                    if( ((SP_AUTO_CHARGE == _ENABLE_LV1_) || (SP_AUTO_CHARGE == _ENABLE_LV2_))    // 自動充電有効レベル1 or 2
                            && (gu8_f_stop_cha != _ON_)
                            && (gu8_f_susp_cha != 1)
                            && (gu8_f_dcir_check_doing != 1) )    // DCIR測定都合
#endif

                    if( ((SP_AUTO_CHARGE == _ENABLE_LV1_) || (SP_AUTO_CHARGE == _ENABLE_LV2_))    // 自動充電有効レベル1 or 2
                            && (gu8_f_stop_cha != _ON_)
                            && (gu8_f_susp_cha == 0)
                            && (gu8_f_dcir_check_doing != 1)
                            && ((gu8_f_ps_on == _ON_) || ((gu8_f_ps_on == _OFF_) && (g_eeprom_data.set_erp.ps_off_charge == _ENABLE_))))
                    {
                        // アイドル状態 --> 主充電状態

                        /* S1.14 131F対策 満充電じゃないのに100%となる問題の対策 */
                        full_chg_calc_init();

                        u8_f_charge_start_ok = 0;
                        chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                        if( u8_f_charge_start_ok == 1 )
                        {
                            set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
                            u8_f_charge_start_ok = 0;
                        }
                        break;
                    }
                }

                /* S1.14 番号無し Level1の起動条件がAC復電のみとなっていたので仕様に従い以下の2条件とする */
                /* S1.14 主充電の起動条件に「PS_ONもしくはPS_OFF充電が有効」の条件を追加する(Copilotのソース解析結果より） */
                if (SP_AUTO_CHARGE == _ENABLE_LV1_)
                {
#if 0
                    if( (SP_AUTO_CHARGE == _ENABLE_LV1_)    // 自動充電有効レベル1
                            && (gu8_f_stop_cha != _ON_)
                            && (gu8_f_susp_cha != 1)
                            && (gu8_f_dcir_check_doing != 1) )    // DCIR測定都合
#endif

                   /* 条件1：PS_OFF充電有効でAC復電検出 */
                   lvl_sta_trg1 = (g_eeprom_data.set_erp.ps_off_charge == _ENABLE_)  && (gu8_f_ac_on_trg == _TRG_ON_);

                   /* 条件2：PS_OFF充電無効でPS_ON立ち上がり検出 */
                   lvl_sta_trg2 = (g_eeprom_data.set_erp.ps_off_charge == _DISABLE_) && (gu8_f_ps_on == _ON_) && (pi_ps_on.trg == _TRG_ON_);

                   if ((lvl_sta_trg1 || lvl_sta_trg2 )
                     && (gu8_f_stop_cha != _ON_)
                     && (gu8_f_susp_cha == 0)
                     && (gu8_f_dcir_check_doing != 1)
                     && ((gu8_f_ps_on == _ON_) || ((gu8_f_ps_on == _OFF_) && (g_eeprom_data.set_erp.ps_off_charge == _ENABLE_)))
                    )
                    {
                        // アイドル状態 --> 主充電状態

                       /* S1.14 131F対策 満充電じゃないのに100%となる問題の対策 */
                        full_chg_calc_init();

                        u8_f_charge_start_ok = 0;
                        chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                        if( u8_f_charge_start_ok == 1 )
                        {
                            set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );      // 充電完了(0)
                            set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
                            u8_f_charge_start_ok = 0;
                        }
                        break;
                    }
                }

                if( SP_AUTO_CHARGE == _ENABLE_LV2_ )    // 自動充電有効レベル2
                {
                    /* 条件1：PS_OFF充電有効でAC復電検出 */
                    lvl_sta_trg1 = (g_eeprom_data.set_erp.ps_off_charge == _ENABLE_)  && (gu8_f_ac_on_trg == _TRG_ON_);

                    /* 条件2：PS_OFF充電無効でPS_ON立ち上がり検出 */
                    lvl_sta_trg2 = (g_eeprom_data.set_erp.ps_off_charge == _DISABLE_) && (gu8_f_ps_on == _ON_) && (pi_ps_on.trg == _TRG_ON_);

                    if (lvl_sta_trg1 || lvl_sta_trg2)
                    {
                        //if( (u8_f_sub_chg_ok == _JOUKEN_OK_)
                        if(((f_chg_ctl_batt_vol_v <= SUB_CHARGE_SIKIICHI) || (gi8_d_soc_mah <= CHARGE_START_KIJUN_SOC))    // 補充電電圧閾値(7.8V)以下 or SOC(mAh)が80%以下
                         && (gu8_f_stop_cha != _ON_)
                         && (gu8_f_susp_cha == 0)
                         && (gu8_f_dcir_check_doing != 1) )    // DCIR測定都合
                        {
                            // アイドル状態 --> 主充電状態

                            /* S1.14 131F対策 満充電じゃないのに100%となる問題の対策 */
                            full_chg_calc_init();

                            u8_f_charge_start_ok = 0;
                            chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                            if( u8_f_charge_start_ok == 1 )
                            {
                                set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );      // 充電完了(0)
                                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
                                u8_f_charge_start_ok = 0;
                            }
                            break;    // 下の充電開始条件チェックを通ると、補充電条件OK --> 補充電開始になってしまう(しかしbreakは荒いか？)
                        }
                    }
                }

                // 充電開始条件チェック
                if( ((gu8_f_ps_on == _ON_) || ((gu8_f_ps_on == _OFF_) && (SE_PS_OFF_CHARGE == _ENABLE_)))    // PS_ON、あるいはPS_OFFだがPS_OFF_CHARGE可能状態のとき
                 && (gu8_f_stop_cha != _ON_)                                                                 // 充電停止指示は無い
                 //&& (gu8_f_susp_cha == 0)   /* S1.15 F129対策 元々コメントアウトされていたがS1.14でコメントを外したが温度抑止後の再開が出来なくなったので元に戻す */
                 && ((u8_f_main_chg_ok == _JOUKEN_OK_) || (u8_f_sub_chg_ok == _JOUKEN_OK_)
                  || ((gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_START_)))
                 && (gu8_f_dcir_check_doing != 1) )    // DCIR測定都合
                {
                    /* 以下、主補充電の準備OK、あるいはCHARGE_ON(1)を受信した場合のみ充電開始できる */
                    // アイドル状態 --> 主充電状態 ※優先順位は(主充電 > 補充電)
                    if( u8_f_main_chg_ok == _JOUKEN_OK_ )    // 主充電条件を満たす
                    {
                        /* S1.14 131F対策 満充電じゃないのに100%となる問題の対策 */
                        full_chg_calc_init();

                        u8_f_charge_start_ok = 0;
                        if((gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_START_))    //　CHARGE_ON(1)受信による充電だった場合
                        {
                            gu8_f_charge_cmd_mode = _CHG_MODE_TRUE_;
                        }
                        chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                        if( u8_f_charge_start_ok == 1 )
                        {
                            if( gu8_f_charge_cmd_mode == _CHG_MODE_TRUE_ )
                            {
                                set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );      // 充電完了(0)
                            }
                            set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
                            u8_f_charge_start_ok = 0;
                        }
                    }
                    // アイドル状態 --> 補充電状態
                    else if( u8_f_sub_chg_ok == _JOUKEN_OK_ )    // 補充電条件"のみ"満たす
                    {
                        /* S1.14 131F対策 満充電じゃないのに100%となる問題の対策 */
                        full_chg_calc_init();

                        u8_f_charge_start_ok = 0;
                        chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _SUB_CHARGE_STATE_);    // 状態遷移
                        if( u8_f_charge_start_ok == 1 )
                        {
                            //set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );    // 充電完了(0)
                            set_info_evt_errlog( FLAG_S_CHARGE_ON, _SET_ );    // 補充電中(1)

                            /* S1.13 現行機は補充電中は「FLAG_S_CHARGE_ON, FLAG_CHG_CHARGE_ON」の両方がセットされているので真似する */
                            set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
                            u8_f_charge_start_ok = 0;
                        }
                    }
                }
            }

            break;

            /**********************************************************************************/
        case _MAIN_CHARGE_STATE_:    /*** 主充電状態 ***/
            /**********************************************************************************/
            // 主充電状態初期化処理
            if( u8_f_main_charge_state_init == _CHG_INIT_NOT_EXECUTE_ )
            {
#ifdef HIS_ON_MODE
his_temp2(2);
u8_susp_init_for_his = 0;
#endif
                u8_f_main_charge_state_init = _CHG_INIT_COMPLETE_;
#if 0
                // フラグ&イベント　セット/リセット
                set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );      // 充電完了(0)
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
#endif
                // 制御用変数初期化
                u32_main_chg_timer = 0;
                u8_f_idle_state_init = 0;
                u8_f_recharge_from_suspend = 0;

                chg_init_proc();
            }


            // 主充電タイマー
            if( ++u32_main_chg_timer > MAIN_CHARGE_TIMER_TIMEOUT_VALUE )
            {
                u8_f_main_chg_time_out = _TIME_OUT_;    // タイムアウト(満充電)
            }

            // 主充電状態 --> 充電強制禁止状態
            if( (gu8_f_charge_off_cmd == _JUSIN_ARI_ ) || (gu8_f_charge_off == _CHARGE_OFF_KINSHI_) )    // CHARGE_OFF(1)受信時
            {
                /* S1.14 番号無し 温度抑止から復帰時は満充電検出を5分待たない処理を追加 */
                if (u8_f_recharge_from_suspend == 1)
                {
                    u8_f_recharge_from_suspend = 0;
                }
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _CHARGE_FORCE_STOP_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                break;
            }

            // 充電停止指示(保護動作関連)
            if( gu8_f_stop_cha == _ON_ )    // 充電停止指示あり
            {
                /* S1.14 番号無し 温度抑止から復帰時は満充電検出を5分待たない処理を追加 */
                if (u8_f_recharge_from_suspend == 1)
                {
                    u8_f_recharge_from_suspend = 0;
                }
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                break;
            }

            // 充電中断パターン1 : 温度抑止指示(保護動作関連)
            if( gu8_f_susp_cha == 1 )    // 充電中断指示あり
            {
#if 0
                u8_f_chg_suspend_reason = _CHG_SUSPEND_TEMP_;
#endif
                /* S1.14 番号無し 温度抑止から復帰時は満充電検出を5分待たない処理を追加 */
                if (u8_f_recharge_from_suspend == 1)
                {
                    u8_f_recharge_from_suspend = 0;
                }

               // if( gu8_f_batchg_en_out == _OUT_ON_ )
             //   {
                    //set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
             //   }
                //chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _SUSPEND_CHARGE_STATE_);    // 状態遷移
                chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_STOP_FLG_, _SUSPEND_CHARGE_STATE_);    // 状態遷移
                //set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)

                /* S1.13 中断から復帰時は制限時間カウントをゼロからやり直す。その他のフラグは現状維持 */
                u32_main_chg_timer = 0;
                break;
            }

            // 充電中断パターン2 : ACオフおよび停電
            if( gu8_f_ac_on_trg == _TRG_OFF_ )
            {
#if 0
                u8_f_chg_suspend_reason = _CHG_SUSPEND_AC_STOP_;
#endif
                /* S1.14 番号無し 温度抑止から復帰時は満充電検出を5分待たない処理を追加 */
                if (u8_f_recharge_from_suspend == 1)
                {
                    u8_f_recharge_from_suspend = 0;
                }

                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _SUSPEND_CHARGE_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)

                /* S1.13 中断から復帰時は制限時間カウントをゼロからやり直す。その他のフラグは現状維持 */
                u32_main_chg_timer = 0;
                break;
            }

            // 充電中断パターン3 : PS_OFF_CHARGE = 無効設定時でのPS_ON信号オフ
            if( (g_eeprom_data.set_erp.ps_off_charge == _DISABLE_) && (gu8_f_ps_on == _OFF_) )
            {
#if 0
                u8_f_chg_suspend_reason = _CHG_SUSPEND_PS_OFF_;
#endif
                /* S1.14 番号無し 温度抑止から復帰時は満充電検出を5分待たない処理を追加 */
                if (u8_f_recharge_from_suspend == 1)
                {
                    u8_f_recharge_from_suspend = 0;
                }

                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _SUSPEND_CHARGE_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)

                /* S1.13 中断から復帰時は制限時間カウントをゼロからやり直す。その他のフラグは現状維持 */
                u32_main_chg_timer = 0;
                break;
            }

            // 満充電計算
            full_chg_calc();

#if 0 /* S1.12 満充電検出時のCHARGE_ON, CHARGE_OKの同時ゼロ対策 */
            // 主充電停止通常条件判別
            if( (gu8_f_full_charge == _ON_)    // 満充電検出した
             || ((gu8_f_charge_cmd_mode == _CHG_MODE_TRUE_) && (gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_STOP_)))    // CHARGE_ON(1)で充電開始していて、その後CHARGE_ON(0)を受信した
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
            }
#else
            // 主充電停止通常条件判別
            if( (gu8_f_full_charge == _ON_)    // 満充電検出した
             || ((gu8_f_charge_cmd_mode == _CHG_MODE_TRUE_) && (gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_STOP_)))    // CHARGE_ON(1)で充電開始していて、その後CHARGE_ON(0)を受信した
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移

                /* 主充電停止通常条件の両方が成立した場合は満充電検出条件を優先する */
                /* 満充電検出条件が成立した場合 */
                if( gu8_f_full_charge == _ON_)
                {
                    full_charge_proc(); // 満充電時処理 2026/9/16
                    gu8_f_full_charge = _OFF_;
                }
                /* CHARGE_ON(1)で充電開始していて、その後CHARGE_ON(0)を受信した条件が成立した場合 */
                else
                {
                    set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                }
            }
#endif
            break;

            /**********************************************************************************/
        case _SUB_CHARGE_STATE_:    /*** 補充電状態 ***/
            /**********************************************************************************/
            // 補充電状態初期化処理
            if( u8_f_sub_charge_state_init == _CHG_INIT_NOT_EXECUTE_ )
            {
#ifdef HIS_ON_MODE
his_temp2(3);
#endif
                u8_f_sub_charge_state_init = _CHG_INIT_COMPLETE_;
#if 0
                // フラグ&イベント　セット/リセット
                set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );    // 充電完了(0)
                set_info_evt_errlog( FLAG_S_CHARGE_ON, _SET_ );    // 補充電中(1)
#endif
                // 制御用変数初期化
                u32_sub_chg_timer = 0;
                u8_f_idle_state_init = _CHG_INIT_NOT_EXECUTE_;

                chg_init_proc();
               /* u8_f_main_chg_time_out = _TIME_IN_;
                u8_f_sub_chg_time_out = _TIME_IN_;

                u16_c_dtdt_ad_sampling_timer = 0;
                u16_c_dtdt_ave_and_comp_timer = 0;
                u16_c_dtdt_soc_full_chg_chk_timer = 0;
                u8_f_dtdt_full_chg_chk_start = _DISABLE_;
                i32_dtdt_temp_sum = 0;
                u8_c_dtdt_set_new_1min_wp = 0;
                u8_c_dtdt_temp_rise_up_count = 0;
                gu32_c_minus_dv_disable = 0;
                u16_c_minus_dv_check_timer = 0;
                f_batt_v_peak = 0.0;
                u8_c_minus_dv_consecutive_occurrence = 0;
                for( uint8_t i = 0; i < 10; i++ )
                {
                    i16_dtdt_set_old_1min[i] = 0;
                    i16_dtdt_set_new_1min[i] = 0;
                }*/
            }

            // 補充電タイマー
            if( ++u32_sub_chg_timer > SUB_CHARGE_TIMER_TIMEOUT_VALUE )
            {
                u8_f_sub_chg_time_out = _TIME_OUT_;    // タイムアウト(満充電)
            }

            // 補充電状態 --> 充電強制禁止状態
            if( (gu8_f_charge_off_cmd == _JUSIN_ARI_ ) || (gu8_f_charge_off == _CHARGE_OFF_KINSHI_) )    // CHARGE_OFF(1)受信時
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _CHARGE_FORCE_STOP_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)

                /* S1.13 現行機は補充電中は「FLAG_S_CHARGE_ON, FLAG_CHG_CHARGE_ON」の両方がセットされているので真似する */
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                break;
            }

            // 充電停止指示(保護動作関連)
            if( gu8_f_stop_cha == _ON_ )    // 充電停止指示あり
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)

                /* S1.13 現行機は補充電中は「FLAG_S_CHARGE_ON, FLAG_CHG_CHARGE_ON」の両方がセットされているので真似する */
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                break;
            }

            // 充電中断パターン1 : 温度抑止指示(保護動作関連)
            if( gu8_f_susp_cha != 0 )    // 充電中断指示あり
            {
                // gu8_f_susp_cha == 2のときは直接充電禁止状態に遷移する必要はあるか？要確認
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移(※アイドル状態)
                set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)

                /* S1.13 現行機は補充電中は「FLAG_S_CHARGE_ON, FLAG_CHG_CHARGE_ON」の両方がセットされているので真似する */
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                break;
            }

            // 充電中断パターン2 : ACオフおよび停電
            if( gu8_f_ac_on_trg == _TRG_OFF_ )
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移(※アイドル状態)
                set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)

                /* S1.13 現行機は補充電中は「FLAG_S_CHARGE_ON, FLAG_CHG_CHARGE_ON」の両方がセットされているので真似する */
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                break;
            }

            // 充電中断パターン3 : PS_OFF_CHARGE = 無効設定時でのPS_ON信号オフ
            if( (g_eeprom_data.set_erp.ps_off_charge == _DISABLE_) && (gu8_f_ps_on == _OFF_) )
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移(※アイドル状態)
                set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)

                /* S1.13 現行機は補充電中は「FLAG_S_CHARGE_ON, FLAG_CHG_CHARGE_ON」の両方がセットされているので真似する */
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                break;
            }

            // 満充電計算
            full_chg_calc();

#if 1 /* S1.12 満充電検出時のCHARGE_ON, CHARGE_OKの同時ゼロ対策 */
            // 補充電状態 --> 主充電状態
            if( (gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_START_) )    //　CHARGE_ON(1)を受信した
            {
                gu8_f_charge_cmd_mode = _CHG_MODE_TRUE_;
                chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
            }

            // 補充電停止通常条件判別
            if( gu8_f_full_charge == _ON_ )    // 満充電検出した
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移
                //set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)
                full_charge_proc(); // 満充電時処理 2026/9/16
                gu8_f_full_charge = _OFF_;
            }
#else
            if(( gu8_f_full_charge == _ON_ )    // 満充電検出した
            || ( (gu8_f_charge_on_cmd == _JUSIN_ARI_) && (gu8_f_charge_on == _CHARGE_ON_START_) ))    //　CHARGE_ON(1)を受信した
            {
                // 満充電と主充電移行を同時に検出した場合は満充電処理を優先する
                // 補充電停止通常条件判別
                if( gu8_f_full_charge == _ON_ )    // 満充電検出した
                {
                    chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移
                    //set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)
                    full_charge_proc(); // 満充電時処理 2026/9/16
                    gu8_f_full_charge = _OFF_;
                }
                // 補充電状態 --> 主充電状態を検出した
                else
                {
                    gu8_f_charge_cmd_mode = _CHG_MODE_TRUE_;
                    chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                    set_info_evt_errlog( FLAG_S_CHARGE_ON, _RESET_ );    // 補充電中(0)
                    set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
                }
            }
#endif
            break;

            /**********************************************************************************/
        case _SUSPEND_CHARGE_STATE_:    /*** 充電中断状態 ***/
            /**********************************************************************************/
#ifdef HIS_ON_MODE
if(u8_susp_init_for_his == 0)
{
    u8_susp_init_for_his = 1;
    his_temp2(4);
}
#endif

#if 1    // 充電停止フラグが完全に作られるまで活かしておく
            // 充電中断状態 --> 充電強制禁止状態
            if( (gu8_f_charge_off_cmd == _JUSIN_ARI_ ) || (gu8_f_charge_off == _CHARGE_OFF_KINSHI_) )    // CHARGE_OFF(1)受信時
            {
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _CHARGE_FORCE_STOP_STATE_);    // 状態遷移
                set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _RESET_ );    // 充電中(0)
                break;
            }
#endif

#if 0    // 条件を一つしか見ていないため、仕様に反しているように思った(一旦置いておく)
            switch( u8_f_chg_suspend_reason )    // 充電中断要因ごと復帰の条件が異なる(※復帰条件は複合しなくて良いのか？)
            {
                case _CHG_SUSPEND_TEMP_:
                    switch( gu8_f_susp_cha )
                    {
                        case 0:    // 温度が充電抑止不要範囲内まで下がった
                            chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                            break;
                        case 1:    // 温度抑止継続
                            break;
                        case 2:    // 充電中断状態 --> 充電強制禁止状態
                            chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _CHARGE_FORCE_STOP_STATE_);    // 状態遷移
                            break;
                        case 3:
                        case 4:
                        case 5:
                        case 6:    // 充電抑止必要温度だが、温度抑止状態から復帰したものとみなす条件に該当した場合(充電中断状態 --> アイドル状態)
                            chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移
                            break;
                    }
                    break;
                case _CHG_SUSPEND_AC_STOP_:
                    if( (gu8_f_susp_cha != 0) && (gu8_f_ac_on_trg == _TRG_ON_) )
                    {
                        chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                    }
                    break;
                case _CHG_SUSPEND_PS_OFF_:
                    if((gu8_f_susp_cha != 0) && (g_eeprom_data.set_erp.ps_off_charge == _DISABLE_) && (gu8_f_ps_on == _OFF_))
                    {
                        chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                    }
                    break;
            }
#else
                switch( gu8_f_susp_cha )
                {
                    case 0:    // 温度抑止状態ではない。再開条件2つを見て問題無ければ、充電中断状態 --> 主充電状態 遷移。
                        if( (gu8_f_ac_on == _ON_)    // 復電(今ACがあるなら問題無し)
                         && (((g_eeprom_data.set_erp.ps_off_charge == _DISABLE_) && (gu8_f_ps_on == _ON_))    // PS_OFF_CHARGE:無効時のPS_ON:ON --> OFF --> ON
                           || (g_eeprom_data.set_erp.ps_off_charge == _ENABLE_) ))    // 元からPS_OFF_CHARGE:有効なら問題無し
                        {
                            /* S1.14 131F対策 満充電じゃないのに100%となる問題の対策 */
                            full_chg_calc_init();

                            /* S1.14 番号無し 温度抑止から復帰時は満充電検出を5分待たない処理を追加 */
                            u8_f_recharge_from_suspend = 1;

                            chg_ctl_state_change(_JUUDEN_DOING_, _JUUDEN_START_FLG_, _MAIN_CHARGE_STATE_);    // 状態遷移
                            set_info_evt_errlog( FLAG_CHG_CHARGE_ON, _SET_ );    // 充電中(1)
                        }
                        break;
                    case 1:    // 温度抑止継続
                        break;
                    case 2:    // 充電中断状態 --> 充電強制禁止状態
                        chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _CHARGE_FORCE_STOP_STATE_);    // 状態遷移
                        break;
                    case 3:
                    case 4:
                    case 5:
                    case 6:    // 充電抑止必要温度だが、温度抑止状態から復帰したものとみなす条件に該当した場合(充電中断状態 --> アイドル状態)
                        chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移
                        break;

                break;
            }
#endif
            break;

            /**********************************************************************************/
        case _CHARGE_FORCE_STOP_STATE_:    /*** 充電強制禁止状態 ***/
            /**********************************************************************************/
#ifdef HIS_ON_MODE
if(u8_force_stop_init_for_his == 0)
{
    u8_force_stop_init_for_his = 1;
    his_temp2(5);
}
#endif
            gu8_f_charge_inhibited = 1;

            // 充電強制禁止状態 --> アイドル状態
            if( (gu8_f_charge_off_cmd == _JUSIN_ARI_ ) || (gu8_f_charge_off == _CHARGE_OFF_CLEAR_) )    // CHARGE_OFF(0)受信時
            {
                u8_f_idle_state_init = _CHG_INIT_NOT_EXECUTE_;
                chg_ctl_state_change(_JUUDEN_STOPING_, _JUUDEN_STOP_FLG_, _IDLE_STATE_);    // 状態遷移
                break;
            }
            break;

        default:
            break;
    }

    /* 以下に充電制御ステージ後に行う処理を配置(受信フラグクリアなど？) */
    gu8_f_charge_on_cmd = _JUSIN_NASHI_;    // 受信フラグは充電制御終わりに0クリアする(仮)
    gu8_f_charge_off_cmd = _JUSIN_NASHI_;
    gu8_f_charge_ok_clear = 0;
#endif

    low_batt_proc(); // LOW BATT制御 (16.16)
}

/*******************************************************************************
 * Function Name: chg_ctl_state_change()
 * Description  : 充電制御状態遷移関数
 * Arguments    : 1:充電中通知フラグ(gu8_f_juudentyu)
 *                2:指示内容　充電開始/停止判別(_JUUDEN_START_FLG_(1)/_JUUDEN_STOP_FLG_(0))
 *                3:遷移先ステージ(u8_chg_ctl_stg)
 * Return Value : None
 *******************************************************************************/
void chg_ctl_state_change(uint8_t chg_flg, uint8_t start_stop_decision, uint8_t stg_target )
{
    // ※第一引数は、第二引数さえあればこちらで入れられるため不要では？
#if 1
    /* ここで接続バッテリ確認 */
    if( start_stop_decision == _JUUDEN_START_FLG_ )
    {
        if( gu8_f_batt_connect == _BATT1_CONNECT_ )         // バッテリ1(6直列):10.8V
        {
            gu8_f_chgv_114v_out = _OUT_OFF_;
        }
        else                                                // バッテリ未接続 OR 例外
        {
#ifdef _DEBUG_DATA_ON_
            gu8_f_chgv_114v_out = _OUT_OFF_;
#else
            return;
#endif
        }
    }
#endif
    gu8_f_charging_active = chg_flg;               // ※ここに置くと遷移前に1回-->1ms出るのが早い
    juuden_start_stop(start_stop_decision);    // 充電開始/停止指示
    u8_chg_ctl_stg = stg_target;             // 遷移先決定
    if( u8_chg_ctl_stg == _MAIN_CHARGE_STATE_)
    {
        gu8_f_main_chg_now = _ON_;
    }
    else
    {
        gu8_f_main_chg_now = _OFF_;
    }
    if(u8_chg_ctl_stg == _SUSPEND_CHARGE_STATE_)
    {
        gu8_f_suppr_chg_now = _ON_;
    }
    else
    {
        gu8_f_suppr_chg_now = _OFF_;
    }
    u8_f_charge_start_ok = 1;
}

/*******************************************************************************
 * Function Name: juuden_start_stop()
 * Description  : 充電開始/停止関数
 * Arguments    : _JUUDEN_START_(1) / _JUUDEN_STOP_FLG_(0)
 * Return Value : None
 *******************************************************************************/
void juuden_start_stop(uint8_t start_stop_flg)
{
#ifndef  DEVELOP_DAY_END
    switch(start_stop_flg)
    {
        case _JUUDEN_START_FLG_:
            if( gu8_f_susp_cha == 0 ) {
                gu8_f_vcc_12v_en_out = _OUT_ON_;
                gu8_f_batchg_en_out = _OUT_ON_;
             }
#if 0
            // FANデフォルト回転開始指示
            if( gu8_f_fan_pwm != _OUT_ON_ )
            {
                gu8_f_fan_pwm = _OUT_ON_;
            }
            if( gu8_f_ps_on == _ON_ )
            {
                set_fan_speed(FAN_MID_SPEED);    // PS_ONなら充電開始時に中速回転を指定
            }
            else if( gu8_f_ps_on == _OFF_ )
            {
                set_fan_speed(FAN_LOW_SPEED);    // PS_OFFなら充電開始時に低速回転を指定
            }
#endif
            break;

        case _JUUDEN_STOP_FLG_:
            gu8_f_batchg_en_out = _OUT_OFF_;
#ifdef _CHG_CTL_DEBUG_ON_
            //gu8_f_fan_pwm = _OUT_OFF_;
#endif
            break;

        default:
            break;
    }
#endif
}

/* S1.14 131F対策 */
/*******************************************************************************
 * Function Name: full_chg_calc_init()
 * Description  : 満充電計算用変数の初期化
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void full_chg_calc_init(void)
{
    uint8_t i;

    u16_c_dtdt_ad_sampling_timer = 0;
    u16_c_dtdt_ave_and_comp_timer = 0;
    u16_c_dtdt_soc_full_chg_chk_timer = 0;
    u8_f_dtdt_full_chg_chk_start = _DISABLE_;
    i32_dtdt_temp_sum = 0;
    u8_c_dtdt_set_new_1min_wp = 0;
    u8_c_dtdt_temp_rise_up_count = 0;

    gu32_c_minus_dv_disable = 0;
    u16_c_minus_dv_check_timer = 0;
    f_batt_v_peak = 0;
    u8_c_minus_dv_consecutive_occurrence = 0;
    for (i=0; i<10; ++i)
    {
        i16_dtdt_set_new_1min[i] = 0;
        i16_dtdt_set_old_1min[i] = 0;
    }

    /* 念のために以下の変数を初期化に追加 */
    u16_c_minus_dv_peak_samp_timer = 0;
    f_batt_v_peak_calc_sample_sum = 0;
}

/*******************************************************************************
 * Function Name: full_chg_calc()
 * Description  : 満充電計算　※充電中のステージでのみ使用
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void full_chg_calc(void)
{
#ifndef  DEVELOP_DAY_END
    /*** タイマー チェック(※カウントアップする場所自体は主補充電ステージ内？本ステージでの仕事の切り分け考える) ***/
    if( (u8_f_main_chg_time_out == _TIME_OUT_) || (u8_f_sub_chg_time_out == _TIME_OUT_) )
    {
        gu8_f_full_charge = _ON_;    // 満充電フラグ(_ON_は仮)
    }

    /*** ΔT/Δt チェック ***/
    // 1秒周期 : 温度データ引用(データ和の変数に足し合わせる)
    if( ++u16_c_dtdt_ad_sampling_timer >= DTDT_TEMP_SUM_PERIOD )
    {
        u16_c_dtdt_ad_sampling_timer = 0;
        i32_dtdt_temp_sum += gi16_ad_battery_temp;
    }

    // 6秒周期 : 温度データ平均化
    if( ++u16_c_dtdt_ave_and_comp_timer >= DTDT_DATA_AVE_PERIOD )
    {
        u16_c_dtdt_ave_and_comp_timer = 0;
        // 温度データ平均化
        i16_dtdt_set_new_1min[u8_c_dtdt_set_new_1min_wp] = i32_dtdt_temp_sum / DTDT_TEMP_SAMPLE_DATA_SIZE ;    // 平均化した値を新データ配列に記憶
        if( u8_c_dtdt_set_new_1min_wp < (DTDT_1M_DIVIDE_6S - 1) )
        {
            u8_c_dtdt_set_new_1min_wp++;
        }
        else
        {
            u8_c_dtdt_set_new_1min_wp = 0;
        }

        i32_dtdt_temp_sum = 0;
    }

    // 1分周期 : 1分前と比較(SOC満充電確認) & 新データ-->旧データへの引っ越し
    if( ++u16_c_dtdt_soc_full_chg_chk_timer >= DTDT_FULL_CHG_CHK_PERIOD )
    {
        u16_c_dtdt_soc_full_chg_chk_timer = 0;
        // 1分前と比較(SOC満充電確認)(2分経過時から作動)
        if( u8_f_dtdt_full_chg_chk_start == _ENABLE_ )
        {
            /* S1.14 143F対策 */
            u8_c_dtdt_temp_rise_up_count = 0U;
            for( uint8_t i = 0; i < 10; i++ )
            {
                if( i16_dtdt_set_new_1min[i] >= (i16_dtdt_set_old_1min[i] + DTDT_FULL_CHARGE_SIKIICHI) )    // 旧データに対し新データで温度が1.5℃以上上昇している場合
                {
                    u8_c_dtdt_temp_rise_up_count++;
                }
            }

            if( u8_c_dtdt_temp_rise_up_count >= DTDT_SIKIICHI_OVER_KOSUU_BORDER )
            {
                gu8_f_full_charge = _ON_;    // 満充電フラグ(_ON_は仮)
            }
        }

        // 新データ-->旧データへの引っ越し(上記処理に含めると1分待つ意味がないので別個処理)
        for( uint8_t i = 0; i < 10; i++ )
        {
            i16_dtdt_set_old_1min[i] = i16_dtdt_set_new_1min[i];
        }

        // 充電開始後1m経過目に、1分前値との比較処理を起動する。
        if( u8_f_dtdt_full_chg_chk_start == _DISABLE_ )
        {
            u8_f_dtdt_full_chg_chk_start = _ENABLE_;
        }
    }

    /*** -ΔV チェック ***/

    enable_delta_v = 0;
    if (u8_f_recharge_from_suspend == 1)
    {
        enable_delta_v = 1;
    }
    else
    {
        if(++gu32_c_minus_dv_disable >= MINUS_DV_DISABLE_TIME)
        {
            enable_delta_v = 1;
        }
    }

    //if( ++gu32_c_minus_dv_disable >= MINUS_DV_DISABLE_TIME )    // 充電開始後5分以内は検出しない
    if (enable_delta_v == 1)
    {
        if( ++u16_c_minus_dv_peak_samp_timer >= MINUS_DV_PEAK_VAL_SAMPLE_PERIOD )    // ピーク値算出用平均値用合算(1s)
        {
            u16_c_minus_dv_peak_samp_timer = 0;

            f_batt_v_peak_calc_sample_sum += gu16_ad_batt_v;
        }

        if( ++u16_c_minus_dv_check_timer >= MINUS_DV_CHECK_PERIOD )    // 5秒間隔
        {
            u16_c_minus_dv_check_timer = 0;

            if( (f_batt_v_peak_calc_sample_sum / MINUS_DV_PEAK_VAL_AVE_KAZU) > f_batt_v_peak )    // バッテリ電圧ピークの確認/更新
            {
                f_batt_v_peak = f_batt_v_peak_calc_sample_sum / MINUS_DV_PEAK_VAL_AVE_KAZU;
            }
            f_batt_v_peak_calc_sample_sum = 0;

            if( gu16_ad_batt_v <= (f_batt_v_peak - MINUS_DV_DOWN_SHIKIICHI) )    // 連続してピーク電圧-40mVになる回数を記録
            {
                u8_c_minus_dv_consecutive_occurrence++;
            }
            else
            {
                if( u8_c_minus_dv_consecutive_occurrence >= 1 )    // 連続検出が途絶えた場合、値が外れた回数分、連続回数を-1する
                {
                    u8_c_minus_dv_consecutive_occurrence--;
                }
#if 0   /* S1.14 143F対策 仕様書に従って連続10回に修正したが、UpDownカウンターでも良いとの顧客提案に従い取り止めとする(参考としてソースをコメントで残す) */
                /* 連続検出が途絶えた場合は連続回数をゼロクリアする */
                u8_c_minus_dv_consecutive_occurrence = 0;
#endif
            }

            if( u8_c_minus_dv_consecutive_occurrence >= MINUS_DV_KAISU_SHIKIICHI )    // バッテリ電圧が基準回数以上に連続して閾値を下回った場合
            {
                gu8_f_full_charge = _ON_;    // 満充電フラグ(_ON_は仮)
            }
        }
    }
#endif
}

/*******************************************************************************
 * Function Name: charge_proc_init()
 * Description  : 充電制御_制御用変数初期化(マイコン起動後1回のみ) <-- 要る？(charge_proc()は呼ばれなくなることがなく、マイコン起動後初回は変数宣言時に0初期化しているため)
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void charge_proc_init(void)
{

}

///*******************************************************************************
//* Function Name: low_batt_proc()
//* Description  : LOW BATT制御 (16.16)
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
uint8_t u8_f_batt_on = 0;
void low_batt_proc(void)
{
    if( gi8_d_soc_mah <= SP_BATT_LOW_THD)  // バッテリ充電量低下(BATT_LOW)閾値
    {
        set_info_evt_errlog( FLAG_BATT_LOW, _SET_ );   // 状態情報/イベント
    	if(u8_f_batt_on==0){
           operate_log_request(OPE_LOWBATT_ON);
           u8_f_batt_on=1;
        }
        // BATT_LOW_ON  ON/OFFログ
    }
    else
    {
        set_info_evt_errlog( FLAG_BATT_LOW, _RESET_ ); // 状態情報/イベント
    	 if(u8_f_batt_on==1){
            operate_log_request(OPE_LOWBATT_OFF);
            u8_f_batt_on=0;
         }
        // BATT_LOW_OFF  ON/OFFログ
    }
}

///*******************************************************************************
//* Function Name: low_batt_proc()
//* Description  : LOW BATT制御 (16.16)
//* Arguments    : None
//* Return Value : None
//*******************************************************************************/
void chg_init_proc(void)
{
    u8_f_main_chg_time_out = _TIME_IN_;
    u8_f_sub_chg_time_out = _TIME_IN_;

    /* S1.14 131F対策 満充電じゃないのに100%となる問題の対策 */
    full_chg_calc_init();

#if 0 /* オリジナルをコメントとして残す */
    u16_c_dtdt_ad_sampling_timer = 0;
    u16_c_dtdt_ave_and_comp_timer = 0;
    u16_c_dtdt_soc_full_chg_chk_timer = 0;
    u8_f_dtdt_full_chg_chk_start = _DISABLE_;
    i32_dtdt_temp_sum = 0;
    u8_c_dtdt_set_new_1min_wp = 0;
    u8_c_dtdt_temp_rise_up_count = 0;
    gu32_c_minus_dv_disable = 0;
    u16_c_minus_dv_check_timer = 0;
    f_batt_v_peak = 0.0;
    u8_c_minus_dv_consecutive_occurrence = 0;
    for( uint8_t i = 0; i < 10; i++ )
    {
        i16_dtdt_set_old_1min[i] = 0;
        i16_dtdt_set_new_1min[i] = 0;
    }
#endif
}

/*******************************************************************************
 * Function Name: dcir_proc()
 * Description  : DCIR測定制御
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
// 変数
uint8_t u8_dcir_stg = 0;
uint8_t u8_dcir_mode = 0;    // 1:充電1 2:充電2 3:BCコマンド

uint8_t u8_f_auto_dcir_en = 0;                   // 0:enable 1:disable
uint8_t u8_f_dcir_24h_complete = 0;              // 0:未遂 1:実行済み
uint8_t u8_f_dcir_8_04v_complete = 0;            // 0:未遂 1:実行済み
uint8_t u8_f_dcir_aft_dischg_under_8_04v = 0;    // 1秒未満放電後、1時間待っても8.04V以下である場合のフラグ

uint16_t u16_c_dcir_1s_timer = 0;    // DCIR測定用1sタイマー
uint32_t u32_c_dcir_1h_timer = 0;    // DCIR測定_電圧回復時間用1hタイマー

// define
#define DCIR_CHARGE_1_MODE   1
#define DCIR_CHARGE_2_MODE   2
#define DCIR_BC_COMMAND_MODE 3

void dcir_proc()
{
    if( gu8_f_dcir_proc_init == 1 )    // 満充電時に所定の変数を0クリア
    {
        gu8_f_dcir_proc_init = 0;

        u8_f_auto_dcir_en = 0;
        u8_f_dcir_24h_complete = 0;
        u8_f_dcir_8_04v_complete = 0;
        u8_f_dcir_aft_dischg_under_8_04v = 0;

        gu32_c_dcir_timer = 0;
        u32_c_dcir_1h_timer = 0;
    }

    switch( u8_dcir_stg )
    {
        case 0:    // DCIR実行判断ステージ
            /*** BCコマンド ***/
            if( gu8_f_dcir_request == 1 )    // BCコマンドを受信した
            {
                /*** 測定不可条件確認 ***/
                if( ((gu8_alm_type_batt_err & 0x07) == 0)    // 製品仕様書18.1.1.6 バッテリ異常時ではない(製品仕様書18.1.3 保護動作時ではない　と同一か？)
                 && (gu8_f_backup_active != _ON_)          // 製品仕様書18.1.1.6 バックアップ中ではない
                 && ((gu8_alm_type_chg_err & 0x07) == 0 )     // 製品仕様書18.1.1.6 充電回路異常時ではない(フラグ名不明)
                 && (gu8_f_charging_active != _ON_)          // 製品仕様書18.1.3   充電中ではない
                 && (gu8_f_susp_cha != 1) )            // 製品仕様書18.1.3   温度抑止中ではない
                {
                    u8_dcir_mode = DCIR_BC_COMMAND_MODE;
                    gu8_f_dcir_check_doing = 1;
                    u8_dcir_stg = 1;
                    break;
                }
                else
                {
                    gu8_f_dcir_complete = 1;
                    // ログ用
                    gs_life_diag_data.batt_check_mode = 13;
                    gs_life_diag_data.batt_voltage1 = 0;
                    gs_life_diag_data.batt_voltage2 = 0;
                    gs_life_diag_data.batt_current1 = 0;
                    gs_life_diag_data.batt_current2 = 0;
                    gs_life_diag_data.batt_ir_temp = 0;
                    gs_life_diag_data.batt_ir_soc_mah = 0;
                    gs_life_diag_data.batt_ir = 0;

                    // レスポンス用
                    gs_life_diag_data_response.batt_check_mode_res = 0;    // 製品仕様書18.1.1「通信では充電取得エラーをレスポンスしない」
                    gs_life_diag_data_response.batt_voltage1_res = 0;
                    gs_life_diag_data_response.batt_voltage2_res = 0;
                    gs_life_diag_data_response.batt_current1_res = 0;
                    gs_life_diag_data_response.batt_current2_res = 0;
                    gs_life_diag_data_response.batt_ir_temp_res = 0;
                    gs_life_diag_data_response.batt_ir_soc_mah_res = 0;
                    gs_life_diag_data_response.batt_ir_res = 0;
                    break;
                }
            }

            /*** 自動測定条件処理(充電1,2条件) ***/
            if( u8_f_auto_dcir_en == 0 )    // 自動測定が有効(満充電から1秒以上の放電があると無効になる)
            {
                if( gu8_f_full_charge_dcir == 1 )    // 満充電検出したか
                {
                    if( gu8_f_dischg_up_1s == 1 )    // 1秒以上の放電があったか
                    {
                        u8_f_auto_dcir_en = 1;
                    }
                    else
                    {
                        if( gu8_f_dischg_under_1s == 1 )    // 1秒未満の放電があったか
                        {
                            if( ++u32_c_dcir_1h_timer >= TIMER_1hour )    // 1時間電圧回復ディレイ
                            {
                                u32_c_dcir_1h_timer = 0;

                                if( gu16_ad_batt_v <= BATT_V_8_04V )    // if(1時間ディレイ後に8.04V以下の場合)
                                {
                                    u8_f_dcir_aft_dischg_under_8_04v = 1;    // u8_f_auto_dcir_en とほぼ同じ役割？
                                }
                                else    // 1時間後正常終了
                                {
                                }
                                gu8_f_dischg_under_1s = 0;    // ディレイからの復活 & 再度1秒未満放電があった際には対応できる
                            }
                        }
                        else
                        {
                            /*** 充電1条件 ***/
                            if( u8_f_dcir_24h_complete == 0 )
                            {
                                if( ++gu32_c_dcir_timer >= 86400000 )    // 満充電から24h経過時
                                {
                                    gu32_c_dcir_timer--;    // インクリメントを相殺

                                    /*** 測定不可条件確認 ***/
                                    if( ((gu8_alm_type_batt_err & 0x07) == 0)            // 製品仕様書18.1.1.6 バッテリ異常時ではない(製品仕様書18.1.3 保護動作時ではない　と同一か？)
                                     && (gu8_f_backup_active != _ON_)                  // 製品仕様書18.1.1.6 バックアップ中ではない
                                     && ((gu8_alm_type_chg_err & 0x07) == 0 )             // 製品仕様書18.1.1.6 充電回路異常時ではない(フラグ名不明)
                                     && (SP_AUTO_CHARGE != _DISABLE_)              // 製品仕様書18.1.1.6 自動充電無効設定時ではない
                                     && (u8_f_dcir_aft_dischg_under_8_04v != 1)    // 製品仕様書18.1.1.6 電圧回復待ち後8.04V以下ではなかった
                                     && (u8_f_dcir_8_04v_complete != 1)            // 製品仕様書18.1.1.6 先に充電2条件で測定は行われていない
                                     && (gu8_f_charging_active != _ON_)                  // 製品仕様書18.1.3   充電中ではない
                                     && (gu8_f_susp_cha != 1) )                    // 製品仕様書18.1.3   温度抑止中ではない
                                    {
                                        u8_f_dcir_24h_complete = 1;
                                        u8_dcir_mode = DCIR_CHARGE_1_MODE;
                                        gu8_f_dcir_check_doing = 1;
                                        u8_dcir_stg = 1;
                                        break;
                                    }
                                    else
                                    {
                                        // ログ用
                                        gs_life_diag_data.batt_check_mode = 13;
                                        gs_life_diag_data.batt_voltage1 = 0;
                                        gs_life_diag_data.batt_voltage2 = 0;
                                        gs_life_diag_data.batt_current1 = 0;
                                        gs_life_diag_data.batt_current2 = 0;
                                        gs_life_diag_data.batt_ir_temp = 0;
                                        gs_life_diag_data.batt_ir_soc_mah = 0;
                                        gs_life_diag_data.batt_ir = 0;
                                        break;
                                    }
                                }
                            }

                            /*** 充電2条件 ***/
                            if( u8_f_dcir_8_04v_complete == 0 )    // これはグローバル変数にして、満充電検出時に落としてもらう？
                            {
                                //if( (gu16_ad_batt_v <= BATT_V_8_04V) || (gi8_d_soc_wh <=  SOC_90) )    // ORなのはあくまで仮
                                if (gu16_ad_batt_v <= BATT_V_8_04V) /* S1.15 F143対策 */
                                {
                                    /*** 測定不可条件確認 ***/
                                    if( ((gu8_alm_type_batt_err & 0x07) == 0)            // 製品仕様書18.1.1.6 バッテリ異常時ではない(製品仕様書18.1.3 保護動作時ではない　と同一か？)
                                     && (gu8_f_backup_active != _ON_)                  // 製品仕様書18.1.1.6 バックアップ中ではない
                                     && ((gu8_alm_type_chg_err & 0x07) == 0 )             // 製品仕様書18.1.1.6 充電回路異常時ではない(フラグ名不明)
                                     && (SP_AUTO_CHARGE != _DISABLE_)              // 製品仕様書18.1.1.6 自動充電無効設定時ではない
                                     && (u8_f_dcir_aft_dischg_under_8_04v != 1)    // 製品仕様書18.1.1.6 電圧回復待ち後8.04V以下ではなかった
                                     && (gu8_f_charging_active != _ON_)                  // 製品仕様書18.1.3   充電中ではない
                                     && (gu8_f_susp_cha != 1) )                    // 製品仕様書18.1.3   温度抑止中ではない
                                    {
                                        u8_f_dcir_8_04v_complete = 1;
                                        u8_dcir_mode = DCIR_CHARGE_2_MODE;
                                        gu8_f_dcir_check_doing = 1;
                                        u8_dcir_stg = 1;
                                    }
                                    else
                                    {
                                        // ログ用
                                        gs_life_diag_data.batt_check_mode = 13;
                                        gs_life_diag_data.batt_voltage1 = 0;
                                        gs_life_diag_data.batt_voltage2 = 0;
                                        gs_life_diag_data.batt_current1 = 0;
                                        gs_life_diag_data.batt_current2 = 0;
                                        gs_life_diag_data.batt_ir_temp = 0;
                                        gs_life_diag_data.batt_ir_soc_mah = 0;
                                        gs_life_diag_data.batt_ir = 0;
                                    }
                                }
                            }
                        }
                    }
                }
            }

            break;

        case 1:    // 測定開始ステージ
            if( gu8_f_backup_active == _ON_ )    // バックアップが開始した場合(※バックアップ以外の、バッテリ異常や回路異常が測定途中で発生した場合も停止すべきか？)
            {
                u8_dcir_stg = 0;

                /* S1.14 149F対策 */
                /* DCIR中断後に主充電開始条件 (gu8_f_dcir_check_doing != 1) が成立するよう、DCIR実行中フラグを解除する。 */
                /* Copilotによる変更最小の提案にもとづく */
                gu8_f_dcir_check_doing = 0;

                if( u8_dcir_mode == DCIR_BC_COMMAND_MODE )    // バックアップによるDCIR測定中断時、即座に測定完了（エラー）とする
                {
                    // ログ用
                    gs_life_diag_data.batt_check_mode = 13;
                    gs_life_diag_data.batt_voltage1 = 0;
                    gs_life_diag_data.batt_voltage2 = 0;
                    gs_life_diag_data.batt_current1 = 0;
                    gs_life_diag_data.batt_current2 = 0;
                    gs_life_diag_data.batt_ir_temp = 0;
                    gs_life_diag_data.batt_ir_soc_mah = 0;
                    gs_life_diag_data.batt_ir = 0;

                    // レスポンス用
                    gs_life_diag_data_response.batt_check_mode_res = 13;
                    gs_life_diag_data_response.batt_voltage1_res = gu16_ad_batt_v;
                    gs_life_diag_data_response.batt_voltage2_res = 0;
                    gs_life_diag_data_response.batt_current1_res = gu16_ad_batt_chg;
                    gs_life_diag_data_response.batt_current2_res = 0;
                    gs_life_diag_data_response.batt_ir_temp_res = 0;
                    gs_life_diag_data_response.batt_ir_soc_mah_res = 0;
                    gs_life_diag_data_response.batt_ir_res = 0;

                    gu8_f_dcir_complete = 1;
                }
                break;
            }

            // ログ用
            gs_life_diag_data.batt_voltage1 = gu16_ad_batt_v;
            gs_life_diag_data.batt_current1 = gu16_ad_batt_chg;

            // レスポンス用
            gs_life_diag_data_response.batt_voltage1_res = gu16_ad_batt_v;
            gs_life_diag_data_response.batt_current1_res = gu16_ad_batt_chg;

            gu8_f_vcc_12v_en_out = _OUT_ON_;
            gu8_f_batchg_en_out = _OUT_ON_;

            u8_dcir_stg = 2;
            break;

        case 2:    // 測定終了ステージ
            if( gu8_f_backup_active == _ON_ )    // バックアップが開始した場合
            {
                u8_dcir_stg = 0;
                //gu8_f_vcc_12v_en_out = _OUT_OFF_;
                gu8_f_batchg_en_out = _OUT_OFF_;

                u16_c_dcir_1s_timer = 0;

                /* S1.14 149F対策 */
                /* DCIR中断後に主充電開始条件 (gu8_f_dcir_check_doing != 1) が成立するよう、DCIR実行中フラグを解除する。 */
                /* Copilotによる変更最小の提案にもとづく */
                gu8_f_dcir_check_doing = 0;

                if( u8_dcir_mode == DCIR_BC_COMMAND_MODE )    // バックアップによるDCIR測定中断時、即座に測定完了（エラー）とする
                {
                    // ログ用
                    gs_life_diag_data.batt_check_mode = 13;
                    gs_life_diag_data.batt_voltage1 = 0;
                    gs_life_diag_data.batt_voltage2 = 0;
                    gs_life_diag_data.batt_current1 = 0;
                    gs_life_diag_data.batt_current2 = 0;
                    gs_life_diag_data.batt_ir_temp = 0;
                    gs_life_diag_data.batt_ir_soc_mah = 0;
                    gs_life_diag_data.batt_ir = 0;

                    // レスポンス用
                    gs_life_diag_data_response.batt_check_mode_res = 13;
                    gs_life_diag_data_response.batt_voltage1_res = gu16_ad_batt_v;
                    gs_life_diag_data_response.batt_voltage2_res = 0;
                    gs_life_diag_data_response.batt_current1_res = gu16_ad_batt_chg;
                    gs_life_diag_data_response.batt_current2_res = 0;
                    gs_life_diag_data_response.batt_ir_temp_res = 0;
                    gs_life_diag_data_response.batt_ir_soc_mah_res = 0;
                    gs_life_diag_data_response.batt_ir_res = 0;

                    gu8_f_dcir_complete = 1;
                }
                break;
            }

            if( ++u16_c_dcir_1s_timer >= TIMER_1000ms )
            {
                u16_c_dcir_1s_timer = 0;

                //gu8_f_vcc_12v_en_out = _OUT_OFF_;
                gu8_f_batchg_en_out = _OUT_OFF_;

                // 測定エラー判別
                /* S1.15 F138対策 S1.14の修正反映漏れ */
                //if( (gf_batt_chg_coeff  * gu16_ADC0_Sens[6]) <= DCIR_CHARGE_CURRENT_ERROR )    // エラー時
                if( gu16_ad_batt_chg <= DCIR_CHARGE_CURRENT_ERROR )    // エラー時
                {
                    dcir_response(1);
                    gu8_f_dcir_complete = 1;
                }
                else    // 正常測定時
                {
                    dcir_response(0);
                    gu8_f_dcir_complete = 1;

                    // BATT_LIFE 判別
                    if( gs_set_parameter.chg_ir_thd != 0 )
                    {
                        if( gs_life_diag_data.batt_ir > gs_set_parameter.chg_ir_thd )
                        {
                            gu8_f_batt_life_over_threshold = 1;
                            set_info_evt_errlog( FLAG_BATT_LIFE, _SET_ );    // バッテリ寿命検出時(1)
                        }
                        else
                        {
                            gu8_f_batt_life_over_threshold = 0;
                            set_info_evt_errlog( FLAG_BATT_LIFE, _RESET_ );    // バッテリ寿命検出時(0)
                        }
                    }
                }

                gu8_f_dcir_check_doing = 0;
                u8_dcir_stg = 0;
            }
            break;

        default:
            break;
    }
}

/*******************************************************************************
 * Function Name: dcir_response()
 * Description  : DCIRレスポンス用関数
 * Arguments    : 0:エラーなし 1:エラーあり
 * Return Value : None
 *******************************************************************************/
void dcir_response(uint8_t err_flg)
{
    if( err_flg == 0 )    // エラーが無い場合
    {
        // ログ用
        switch( u8_dcir_mode )
        {
            case DCIR_CHARGE_1_MODE:
                gs_life_diag_data.batt_check_mode = 1;
                break;
            case DCIR_CHARGE_2_MODE:
                gs_life_diag_data.batt_check_mode = 2;
                break;
            case DCIR_BC_COMMAND_MODE:
                gs_life_diag_data.batt_check_mode = 3;
                // ここでレスポンス指示フラグを立てる？
                break;
            default:
                break;
        }
        //gs_life_diag_data.batt_voltage1 = 0;
        gs_life_diag_data.batt_voltage2 = gu16_ad_batt_v;
        //gs_life_diag_data.batt_current1 = 0;
        /* S1.15 F138対策 S1.14の修正反映漏れ */
        //gs_life_diag_data.batt_current2 = (gf_batt_chg_coeff  * gu16_ADC0_Sens[6]);
        gs_life_diag_data.batt_current2 = gu16_ad_batt_chg;
        gs_life_diag_data.batt_ir_temp = gi16_ad_battery_temp/10;
        gs_life_diag_data.batt_ir_soc_mah = gi8_d_soc_mah;
        gs_life_diag_data.batt_ir = ((gs_life_diag_data.batt_voltage2 - gs_life_diag_data.batt_voltage1) * 1000) / gs_life_diag_data.batt_current2;

        // レスポンス用
        switch( u8_dcir_mode )
        {
            case DCIR_CHARGE_1_MODE:
                gs_life_diag_data_response.batt_check_mode_res = 1;
                break;
            case DCIR_CHARGE_2_MODE:
                gs_life_diag_data_response.batt_check_mode_res = 2;
                break;
            case DCIR_BC_COMMAND_MODE:
                gs_life_diag_data_response.batt_check_mode_res = 3;
                // ここでレスポンス指示フラグを立てる？
                break;
            default:
                break;
        }
        //gs_life_diag_data_response.batt_voltage1_res = 0;
        gs_life_diag_data_response.batt_voltage2_res = gu16_ad_batt_v;
        //gs_life_diag_data_response.batt_current1_res = 0;
        /* S1.15 F138対策 S1.14の修正反映漏れ */
        //gs_life_diag_data_response.batt_current2_res = (gf_batt_chg_coeff  * gu16_ADC0_Sens[6]);
        gs_life_diag_data_response.batt_current2_res = gu16_ad_batt_chg;
        gs_life_diag_data_response.batt_ir_temp_res = gi16_ad_battery_temp/10;
        gs_life_diag_data_response.batt_ir_soc_mah_res = gi8_d_soc_mah;
        gs_life_diag_data_response.batt_ir_res = ((gs_life_diag_data.batt_voltage2 - gs_life_diag_data.batt_voltage1) * 1000) / gs_life_diag_data.batt_current2;

    }
    else if( err_flg == 1 )    // エラーがあった場合
    {
        // ログ用
        switch( u8_dcir_mode )
        {
            case DCIR_CHARGE_1_MODE:
                gs_life_diag_data.batt_check_mode = 11;
                break;
            case DCIR_CHARGE_2_MODE:
                gs_life_diag_data.batt_check_mode = 12;
                break;
            case DCIR_BC_COMMAND_MODE:
                gs_life_diag_data.batt_check_mode = 13;
                break;
            default:
                break;
        }
        gs_life_diag_data.batt_voltage1 = 0;
        gs_life_diag_data.batt_voltage2 = 0;
        gs_life_diag_data.batt_current1 = 0;
        gs_life_diag_data.batt_current2 = 0;
        gs_life_diag_data.batt_ir_temp = 0;
        gs_life_diag_data.batt_ir_soc_mah = 0;
        gs_life_diag_data.batt_ir = 0;

        // レスポンス用
        switch( u8_dcir_mode )
        {
            case DCIR_CHARGE_1_MODE:
                gs_life_diag_data_response.batt_check_mode_res = 11;
                break;
            case DCIR_CHARGE_2_MODE:
                gs_life_diag_data_response.batt_check_mode_res = 12;
                break;
            case DCIR_BC_COMMAND_MODE:
                gs_life_diag_data_response.batt_check_mode_res = 13;
                // ここでレスポンス指示フラグを立てる？
                break;
            default:
                break;
        }
        //gs_life_diag_data_response.batt_voltage1_res = 0;
        gs_life_diag_data_response.batt_voltage2_res = gu16_ad_batt_v;
        //gs_life_diag_data_response.batt_current1_res = 0;
        /* S1.15 F138対策 S1.14の修正反映漏れ */
        //gs_life_diag_data_response.batt_current2_res = (gf_batt_chg_coeff  * gu16_ADC0_Sens[6]);
        gs_life_diag_data_response.batt_current2_res = gu16_ad_batt_chg;
        gs_life_diag_data_response.batt_ir_temp_res = 0;
        gs_life_diag_data_response.batt_ir_soc_mah_res = 0;
        gs_life_diag_data_response.batt_ir_res = 0;
    }
}
