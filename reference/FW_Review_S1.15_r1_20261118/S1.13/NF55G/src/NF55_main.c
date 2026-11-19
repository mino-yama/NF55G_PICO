#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"
#include <string.h>

void    sleep(void);
int     user_main2(void);
void    paramter_init1(void);
void    paramter_init2(void);
void    jumpBoot(void);
uint8_t judge_bootarea(void);

extern void SystemInit(void);
extern void read_all_eeprom(void);
extern void userInit(void);
extern void input(void);
extern void serial_rx_proc(void);
extern void serial_tx_proc(void);
extern void output(void);
extern void ps_on_proc(void);
extern void burst_proc(void);
extern void discharge_proc(void);
extern void charge_proc(void);
extern void data_proc(void);
extern void write_eeprom(void);
extern void eeprom_all_backup_proc(void);
extern void set_fan_speed( uint8_t speed );
extern void hogo_proc(void);
extern void dcir_proc(void);
extern void operate_log_request( uint8_t almid );
extern void set_info_evt_errlog( uint8_t flag, uint8_t status );
extern void startup_input_ad(void);
extern void rtc_data_set_fu(void);
extern void filter_clear(struct _Filter *fil);
extern void input_init_ac(void);
void check_reset(void);
void wdt_loop(void);
void revoltage(void);
void clear_global_variables(void);
extern void fan_stop_PWM(void);

#ifdef _HIS_ENABLE_MODE_
extern uint32_t dbg_1ms_cnt;
#endif

void check_reset(void)
{


    if(gu32_reset_cause == DL_SYSCTL_RESET_CAUSE_SYSRST_WWDT0_VIOLATION) {
        //WDTリセット時
        DL_WWDT_disablePower(WWDT0_INST);

        O_PS_ON_OUT_H;
        O_BURST_OUT_L;
        O_12V_EN_H;
        O_BATT_EN_L;
        O_CHGV_11_4V_L;
        O_DISCHG12V_EN_L;
        O_BATCHG_EN_H;
        O_VCC_12V_EN_L;
        O_TEST_OUT_L;

        gu8_f_wdt_err=1;
        set_info_evt_errlog( FLAG_WDT, _SET_ );

    }
}

void wdt_loop(void)
{

    if(eeprom_req_busy==0){

        while(1)
        {
          // 停止
        }
    }

}



/*******************************************************************************
* Function Name: main()
* Description  : メイン処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
int main(void)
{
    gu32_reset_cause = DL_SYSCTL_getResetCause();


    SYSCFG_DL_init();

    //__enable_irq();

#ifndef _WWDT_ON_
    DL_WWDT_disablePower(WWDT0_INST);  //wdtを無効化
#endif

    SystemInit();

    read_all_eeprom();      // EEPROMデータ読出(全データ)

    userInit();

    check_reset();

    input_init_ac();

    startup_input_ad();     // 立上げ時 ADC収集処理

	operate_log_request(OPE_MIC_POWER_ON);


    while (1)
    {
        sleep();             // 1ms Wait

#ifdef _HIS_ENABLE_MODE_
        ++dbg_1ms_cnt;
#endif

#ifdef _DEBUG_ON_
        //O_TEST_OUT_H;
#endif


#ifdef _WWDT_ON_
        DL_WWDT_restart(WWDT0_INST);

#endif


        if(gu8_f_wdt_err==0)
        {
            input();             // ADC/GPIO入力

            serial_rx_proc();    // UART処理(受信)

            ps_on_proc();        // PS ON制御

            hogo_proc();         // 保護処置

            discharge_proc();    // 放電(バックアップ)制御

            if(gu8_f_before_shutdown!=1)
             {

                charge_proc();       // 充電制御

                dcir_proc();         // DCIR測定制御
             }

            burst_proc();        // Burst制御

            data_proc();         // 各種データ処理

            output();            // 出力処理

            serial_tx_proc();    // UART処理(送信)

            eeprom_all_backup_proc();  // EEPROM 全バックアップ処理

            revoltage();
        
        }

        write_eeprom();      // EEPROM書込み処理

        if(gu8_f_wdt_err==1){

            wdt_loop();
        }

#ifdef _HIS_ENABLE_MODE_
        //set_fan_speed(gu8_s_debug_fan_sirei_num);
#endif
#ifdef _DEBUG_ON_
        //O_TEST_OUT_L;
#endif
    }
}

/*******************************************************************************
* Function Name: sleep()
* Description  : Wait 1ms
* Arguments    : None
* Return Value : None
*******************************************************************************/
void sleep(void)
{
    gu16_f_timing = 0;
    gu16_f_timing_1sec = 0;
    while(gu16_f_timing == 0){ // 1ms
        __WFI();
    }
}

/*******************************************************************************
* Function Name: user_main2()
* Description  : メイン処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
int user_main2(void)
{
    //SYSCFG_DL_init();

    //__enable_irq();

    gu32_reset_cause = DL_SYSCTL_getResetCause();//リセット要因を取得
    DL_WWDT_reset(WWDT0_INST);     //wwdtの値リセット
    DL_WWDT_enablePower(WWDT0_INST);  //poweron
    SYSCFG_DL_WWDT0_init();   //wdt初期化



#ifndef _WWDT_ON_
    DL_WWDT_disablePower(WWDT0_INST);
#endif

    SystemInit();

    read_all_eeprom();      // EEPROMデータ読出(全データ)

    userInit();

    check_reset();

    paramter_init2(); // 各パラメータの初期値設定

    startup_input_ad();     // 立上げ時 ADC収集処理

	operate_log_request(OPE_MIC_POWER_ON);
    while (1)
    {
        sleep();             // 1ms Wait

#ifdef _DEBUG_ON_
        //O_TEST_OUT_H;
#endif


#ifdef _WWDT_ON_
        DL_WWDT_restart(WWDT0_INST);
#endif

        if(gu8_f_wdt_err==0)
        {
            input();             // ADC/GPIO入力

            serial_rx_proc();    // UART処理(受信)

            ps_on_proc();        // PS ON制御

            hogo_proc();         // 保護処置

            discharge_proc();    // 放電(バックアップ)制御

            if(gu8_f_before_shutdown!=1)
             {

                charge_proc();       // 充電制御

                dcir_proc();         // DCIR測定制御
             }

            burst_proc();        // Burst制御

            data_proc();         // 各種データ処理

            output();            // 出力処理

            serial_tx_proc();    // UART処理(送信)

            eeprom_all_backup_proc();  // EEPROM 全バックアップ処理

            revoltage();
        }

        write_eeprom();  

        if(gu8_f_wdt_err==1){
            wdt_loop();
        }

#ifdef _HIS_ENABLE_MODE_
        //set_fan_speed(gu8_s_debug_fan_sirei_num);
#endif
#ifdef _DEBUG_ON_
        //O_TEST_OUT_L;
#endif
    }
}

/*******************************************************************************
* Function Name: paramter_init1()
* Description  : 各パラメータの初期値設定処理(User1)
* Arguments    : None
* Return Value : None
*******************************************************************************/
void paramter_init1(void)
{
    gu8_f_user_select = 0; // User1で動作
}

/*******************************************************************************
* Function Name: paramter_init2()
* Description  : 各パラメータの初期値設定処理(User2)
* Arguments    : None
* Return Value : None
*******************************************************************************/
void paramter_init2(void)
{
    gu8_f_user_select = 1; // User2で動作

    rtc_data_set_fu();  // 時刻設定(SET CLOCK)受信

    gu32_c_event_wait = TIMER_10s;  // イベント送信可能待ちタイマ
}

/*******************************************************************************
* Function Name: judge_bootarea()
* Description  : boot部の正当性を確認する処理
* Arguments    : None
* Return Value : 0: 正当 1:残念
*******************************************************************************/
uint8_t judge_bootarea(void)
{
    uint32_t crcChecksum;
    uint32_t crcExpectsum;
    uint8_t ret = 0;

    crcExpectsum = *(uint32_t *)(BOOT_CRC32_ADDRESS);

    crcChecksum = DL_CRC_calculateMemoryRange32(CRC, 0xFFFFFFFF, (uint32_t *)BOOT_START_ADDRESS, (const uint32_t *)BOOT_END_ADDRESS);

    /* CRC計算結果を反転する */
    crcChecksum = ~crcChecksum;

    if (crcExpectsum != crcChecksum)
    {
        ret = 1;
    }

    return(ret);
}

/*******************************************************************************
* Function Name: jumpBoot()
* Description  : Boot部へ遷移する処理
*                Boot部の正当性をチェックしてOKならBoot2へジャンプする。
* Arguments    : None
* Return Value : None
*******************************************************************************/
void jumpBoot(void)
{
    uint32_t app_sp;
    uint32_t app_reset;
    uint8_t  ret = 0;

    ret = judge_bootarea();
    if (ret == 0)
    {
        data_info_common.gu8_f_start_status = 0xA0;    // Userからboot2へ移行

        app_sp      = *(volatile uint32_t *)(BOOT_START_ADDRESS + 0);
        app_reset   = *(volatile uint32_t *)(BOOT_START_ADDRESS + 0x28);
    }
    else
    {
        while (1);
#if 0
        /* <<<注目>>> */
        /* 当初はbootboot2に遷移させようと思ったが、現状、更新対象がuser部かboot部かの判断はboot部が行っている。 */
        /* そのためboot部が壊れている場合は判断が出来ないため、無条件にbootbootに飛んでしまうとbootbootがUser部のFUを実行するケースが想定される +/
        /* bootbootはboot部のエリアを更新する機能しかないため、user部エリアを消去出来ずFUが失敗する */
        /* どうすべきは今後考えることにして、今回はぶっ飛び防止のためにここでループする */
        /* 電源を入れなおせばbootbootでFU待ちとなるのでboot部をFUすればuser部のFU無しで復活可能 */
        /* Userで受けたFUに対してSレコード受信時にBoot部が壊れた旨のNAKを返せればユーザーへの通知も可能と思う */
        data_info_common.gu8_f_start_status = 0xB0;    // Userからのbootboot2へ移行

        app_sp      = *(volatile uint32_t *)(BOOTBOOT_START_ADDRESS + 0);
        app_reset   = *(volatile uint32_t *)(BOOTBOOT_START_ADDRESS + 0x28);
#endif
    }

 /* <<<注目>>> VTORを確実に更新するcopilotさん推奨の方法（BSBとISBは数クロック程度の実行時間とのことなので数usで完了するはず） */
    __disable_irq();
    SCB->VTOR = BOOT_START_ADDRESS;
    __DSB();
    __ISB();
    __enable_irq();

 /* <<<注目>>> 念のために従来方法を残すが、無限ループになっている点が気になる */
    if( SCB->VTOR != BOOT_START_ADDRESS)
    {
        //SCB->VTORの書き込みが1回で完了しないことがあったので念のために繰り返す */
        while(1)
        {
            SCB->VTOR = BOOT_START_ADDRESS;
            if( SCB->VTOR == BOOT_START_ADDRESS)
            {
                break;
            }
        }
    }

    __asm volatile (
            "msr msp, %0 \n"  // MSP設定
            "bx  %1      \n"  // boot_main2 もしくは bootboot_main2へジャンプ
            :
            : "r"(app_sp), "r"(app_reset)
    );
}

/*******************************************************************************
* Function Name: revoltage()
* Description  : revoltage
*                放電終了後の復電
* Arguments    : None
* Return Value : None
*******************************************************************************/



void revoltage(void){
  if(gu8_f_before_shutdown!=0)
  {
    switch(gu8_end_dischg_stage)
    {

    case 0:
        switch(gu8_f_skip_reason)
        {
        case 1 :

            O_12V_EN_H;

            if( gu8_f_fan_pwm != _OUT_NOT_ )
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
                gu8_end_dischg_stage=1;
              } else{
                gu32_c_fan_pwm_delay--;
              }
            }
                break;

        case 2 :                 //PS_OFFで停電した場合は


            fan_stop_PWM();
            O_VCC_12V_EN_L;
            O_BATCHG_EN_H;

            if(eeprom_req_busy==0){

                gu8_end_dischg_stage=2;
            }

                break;
        case 3 :                               //バッテリ無しで切断されたときや放電中に中断されたとき

            if( gu8_f_charge_output == _ON_ )  // 放電出力中?
            {

                 O_DISCHG12V_EN_L;
                 O_BATT_EN_L;
                 DL_TimerG_stopCounter(SYNC_0_INST);
                 DL_TimerG_stopCounter(SYNC_120_INST);
                 DL_TimerG_stopCounter(SYNC_240_INST);
                 gu8_f_charge_output = _OFF_;   // 放電出力中 OFF
            }

            if(eeprom_req_busy==0){


                gu8_end_dischg_stage=2;
            }

                break;

       default :
                break;
        }



        break;

    case 1 ://放電終止もしくはバックアップ中のPS_OFFによる切断時
        if(eeprom_req_busy==0){
        O_DISCHG12V_EN_L;                     //DischgOFF
        O_BATT_EN_L;                          //BATT_ENOFF
        //****放電コンバーターOFF***********************
        DL_TimerG_stopCounter(SYNC_0_INST);
        DL_TimerG_stopCounter(SYNC_120_INST);
        DL_TimerG_stopCounter(SYNC_240_INST);
        //******************************************
        O_VCC_12V_EN_L;
        gu8_f_charge_output = _OFF_;

        gu8_end_dischg_stage=2;

        }
         break;

    case 2:
        if(gu16_c_aft_ac_on>=TIMER_600ms)
        {

              gu8_end_dischg_stage=0;
              clear_global_variables();
        }
         break;

    case 3:

        break;
    }
  	
  }

}

void clear_global_variables(void){

    /* グローバル変数領域をクリア */
    memset((void *)0x20200100, 0, 0x1742);   //変数を追加したらmapを確認してクリア領域を更新する

    //0以外の変数
    gu8_f_envt_first = 1;
    gu8_f_batt_not_con=2;
    gu8_f_batt_connect = _UNKNOWN_CONNECT_;
    gu8_f_first_check = _ON_;
    gu8_f_ini_ps_on=2;


    pi_ps_on.ON_time = TIMER_10ms;
    pi_ps_on.OF_time = TIMER_10ms;
    pi_burst_on.ON_time = TIMER_2ms;
    pi_burst_on.OF_time = TIMER_2ms;
    pi_dischg12_ovp.ON_time = TIMER_6ms;
    pi_dischg12_ovp.OF_time = TIMER_6ms;
    pi_pfc_fail_in.ON_time = TIMER_300ms;
    pi_pfc_fail_in.OF_time = TIMER_300ms;
    pi_ac_on_level.ON_time = TIMER_3ms;
    pi_ac_on_level.OF_time = TIMER_8ms;
    pi_aft_ac_on_level.ON_time = TIMER_3ms;
    pi_aft_ac_on_level.OF_time = TIMER_8ms;
    /* 追加フィルター */
    pi_low_v.ON_time = (TIMER_300ms - TIMER_4ms);
    pi_low_v.OF_time = TIMER_10ms;
    pi_high_i_of.ON_time = TIMER_250ms;
    pi_high_i_of.OF_time = TIMER_250ms;
    pi_high_i_of_h.ON_time = TIMER_250ms;
    pi_high_i_of_h.OF_time = TIMER_250ms;
    pi_high_i_on.ON_time = TIMER_10ms;
    pi_high_i_on.OF_time = TIMER_10ms;
    pi_high_i_on_50ms.ON_time = TIMER_1ms;
    pi_high_i_on_50ms.OF_time = TIMER_1ms;
    pi_high_v.ON_time = TIMER_2ms;
    pi_high_v.OF_time = TIMER_2ms;
    pi_high_i_dis_6.ON_time = TIMER_1ms;
    pi_high_i_dis_6.OF_time = TIMER_1ms;
    pi_high_i_cha.ON_time = TIMER_1ms;
    pi_high_i_cha.OF_time = TIMER_1ms;
    pi_high_v_cha_6.ON_time = TIMER_4ms;
    pi_high_v_cha_6.OF_time = TIMER_4ms;
    pi_low_v_shortage.ON_time = TIMER_250ms;
    pi_low_v_shortage.OF_time = TIMER_250ms;
    pi_low_v_shortage_5a.ON_time = TIMER_250ms;
    pi_low_v_shortage_5a.OF_time = TIMER_250ms;
    pi_bbu_sw_short.ON_time = (TIMER_300ms - TIMER_4ms);
    pi_bbu_sw_short.OF_time = (TIMER_300ms - TIMER_4ms);
    pi_bbu_sw_open.ON_time = (TIMER_300ms - TIMER_4ms);
    pi_bbu_sw_open.OF_time = (TIMER_300ms - TIMER_4ms);
    pi_fan_fail_adu.ON_time = (TIMER_300ms - TIMER_4ms);
    pi_fan_fail_adu.OF_time = (TIMER_300ms - TIMER_4ms);
    pi_fan_fail_bbu.ON_time = (TIMER_300ms - TIMER_4ms);
    pi_fan_fail_bbu.OF_time = (TIMER_300ms - TIMER_4ms);
    pi_fail_bbu.ON_time = (TIMER_300ms - TIMER_4ms);
    pi_fail_bbu.OF_time = (TIMER_300ms - TIMER_4ms);
    pi_temp_fail_adu.ON_time = (TIMER_50ms - TIMER_4ms);
    pi_temp_fail_adu.OF_time = (TIMER_50ms - TIMER_4ms);
    pi_temp_fail_bbu.ON_time = (TIMER_50ms - TIMER_4ms);
    pi_temp_fail_bbu.OF_time = (TIMER_50ms - TIMER_4ms);
    pi_batt_temp_aft.ON_time = (TIMER_300ms - TIMER_4ms);
    pi_batt_temp_aft.OF_time = (TIMER_300ms - TIMER_4ms);
    pi_batt_temp_bef.ON_time = (TIMER_300ms - TIMER_4ms);
    pi_batt_temp_bef.OF_time = (TIMER_300ms - TIMER_4ms);
    pi_batt_break.ON_time = TIMER_250ms;
    pi_batt_break.OF_time = TIMER_250ms;
    pi_batt_break_chg.ON_time = TIMER_250ms;
    pi_batt_break_chg.OF_time = TIMER_250ms;
    pi_batt_not.ON_time = TIMER_1ms;
    pi_batt_not.OF_time = TIMER_1ms;
    pi_latch_fail.ON_time = (TIMER_50ms - TIMER_4ms);
    pi_latch_fail.OF_time = (TIMER_50ms - TIMER_4ms);
    pi_batt_low_6.ON_time = TIMER_250ms;
    pi_batt_low_6.OF_time = TIMER_250ms;
    pi_batt_high_6.ON_time = TIMER_250ms;
    pi_batt_high_6.OF_time = TIMER_250ms;
    /* バースト・バッテリーフィルター */
    pi_burst_i_over.ON_time = (TIMER_300ms + TIMER_50ms);
    pi_burst_i_over.OF_time = (TIMER_300ms + TIMER_50ms);
    pi_burst_i_good.ON_time = (TIMER_300ms + TIMER_50ms);
    pi_burst_i_good.OF_time = TIMER_10ms;
    pi_batt_con.ON_time = TIMER_300ms;
    pi_batt_con.OF_time = TIMER_300ms;
    pi_batt_con.sts= _NOT_;

    pi_fan_low_protection.ON_time=TIMER_30s;
    pi_fan_low_protection.OF_time = TIMER_10ms;

    pi_fan_high_protection.ON_time=TIMER_30s;
    pi_fan_high_protection.OF_time = TIMER_10ms;

    pi_fan_stop_protection.ON_time=TIMER_10s;
    pi_fan_stop_protection.OF_time= TIMER_10ms;
    read_all_eeprom();//ROMデータをイニシャルで読み出すので必要
    userInit();
   // gu16_c_proc_delay = TIMER_1000ms;



}

