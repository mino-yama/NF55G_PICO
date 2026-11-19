#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"
#include <math.h>
#include <ti/iqmath/include/IQmathLib.h>

void input(void);
static void input_ad(void);
static void input_io(void);
static void input_protect(void);

 void input_re_ac(void);
 void input_init_ac(void);
uint8_t input_ac_on_filter(uint8_t flag, uint8_t input, struct _Filter *fil);
uint8_t input_aft_ac_on_filter(uint8_t flag, uint8_t input, struct _Filter *fil);
uint8_t input_filter(uint8_t flag, uint8_t input, struct _Filter *fil);
void filter_clear_all(void);
void filter_clear(struct _Filter *fil);
int16_t calc_temperature(uint16_t ad, uint16_t bb);
void startup_input_ad(void);

extern void sleep(void);

uint32_t dbg_1ms_cnt = 0;

/* S1.13 いきなり補充電が始まる不具合対策（AC復電検出で_ON_(1)をセットすることで復電後タイマーを有効にする */
extern uint8_t  u8_f_afterer_power_restored;

/*******************************************************************************
 * Function Name: input()
 * Description  : 入力処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void input(void)
{
    input_ad(); /* ADC入力 */

    input_io(); /* GPIO入力 */

    input_protect();/* GPIO入力 */

    if( gu16_c_proc_delay == 0 )  // 処理開始遅延カウンタ
    {
        gu8_f_proc_start = 1;     // 処理開始フラグON
    }
    else
    {
        gu16_c_proc_delay--;
    }

    if((gu8_f_before_shutdown !=0) && (gu8_end_dischg_stage == 2))
    {
        //放電終止などが発生した場合
        input_re_ac();
    }
    else
    {
        filter_clear(&pi_aft_ac_on_level);
    }
}

/*******************************************************************************
 * Function Name: input_ad()
 * Description  : input ADC
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
static void input_ad(void)
{
    uint8_t  i,j;
    //uint32_t sum;
    uint32_t sum1_2 = 0;
    uint32_t sum0_4 = 0;
    uint32_t sum0_3 = 0;
    uint32_t sum0_2 = 0;
    uint32_t sum0_1 = 0;
    uint32_t sum0_0 = 0;
    uint32_t sum1_0 = 0;
    uint32_t sum1_1 = 0;
    uint32_t sum0_6 = 0;
    uint32_t sum0_5 = 0;
    uint32_t sum0_5_10 = 0;
    int16_t i16_tmp = 0;
    //static uint8_t f_batt_connect_old = _BATT_NOT_CONNECT_;
/*
    ADC0_Sens[0]    : A0_0  LLC温度(AC/DC_TEMP_IN)
    ADC0_Sens[1]    : A0_1  BBU温度(BUU_TEMP)
    ADC0_Sens[2]    : A0_2  BATT2温度(BATT_TEMP7+)(BATT2)
    ADC0_Sens[3]    : A0_3  BATT1温度(BATT_TEMP6+)(BATT1)
    ADC0_Sens[4]    : A0_5  12VOUT電圧(12VOUT_V)
    ADC0_Sens[5]    : A0_6  12VOUT電流(12VOUT_I)
    ADC0_Sens[6]    : A0_7  BATT充電電流(BATT_CHG)

    ADC1_Sens[0]    : A1_1  BATT放電電流(DISCHG_I)
    ADC1_Sens[1]    : A1_2  BATT電圧値(BATT_V)
    ADC1_Sens[2]    : A1_4  12V_AC/DC電圧値(AC/DC12V_V)
    ADC1_Sens[3]    : 
    ADC1_Sens[4]    : 
    ADC1_Sens[5]    : 
    ADC1_Sens[6]    : 
*/
    //ADC変換開始
    DL_ADC12_enableConversions(ADC12_0_INST);
    DL_ADC12_enableConversions(ADC12_1_INST);

    gu16_CheckADC0 = 0;
    DL_ADC12_startConversion(ADC12_0_INST);
    while (0x7F != gu16_CheckADC0)
    {
        __WFE();
    }

    gu16_ADC0_Result[0][gu16_ADC_cnt_4 ] = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_0);// LLC温度
    gu16_ADC0_Result[1][gu16_ADC_cnt_4 ] = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_1);// BUU温度
    gu16_ADC0_Result[2][gu16_ADC_cnt_4 ] = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_2);// BATT2温度
    gu16_ADC0_Result[3][gu16_ADC_cnt_4 ] = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_3);// BATT1温度
    gu16_ADC0_Result[4][gu16_ADC_cnt_4 ] = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_4);// 12VOUT_V
    gu16_ADC0_Result[5][gu16_ADC_cnt_50] = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_5);// 12VOUT_I
    gu16_ADC0_Result[6][gu16_ADC_cnt_50] = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_6);// BATT_CHG

    /* 12V_Iの10回移動平均用データの格納 */
    gu16_ADC0_5_10[gu16_ADC_cnt_10] = gu16_ADC0_Result[5][gu16_ADC_cnt_50];

    /* 12V_Iの生値(AD) */
    gu16_ad_12vout_i_now_ad = gu16_ADC0_Result[5][gu16_ADC_cnt_50];

    /* 12V_Vの生値(AD) */
    gu16_ad_12vout_v_now_ad = gu16_ADC0_Result[4][gu16_ADC_cnt_4 ];

    gu16_CheckADC1 = 0;
    DL_ADC12_startConversion(ADC12_1_INST);

    while (0x07 != gu16_CheckADC1)
    {
        __WFE();
    }

    gu16_ADC1_Result[0][gu16_ADC_cnt_50] = DL_ADC12_getMemResult(ADC12_1_INST, DL_ADC12_MEM_IDX_0);// DISCHG_I
    gu16_ADC1_Result[1][gu16_ADC_cnt_50] = DL_ADC12_getMemResult(ADC12_1_INST, DL_ADC12_MEM_IDX_1);// BATT_V
    gu16_ADC1_Result[2][gu16_ADC_cnt_4 ] = DL_ADC12_getMemResult(ADC12_1_INST, DL_ADC12_MEM_IDX_2);// AC/DC12V_V

    /* 充電電圧の生値(AD) */
    gu16_ad_chgout_v_now_ad = gu16_ADC1_Result[1][gu16_ADC_cnt_50];

    //ADC停止
    DL_ADC12_disableConversions(ADC12_0_INST);
    DL_ADC12_disableConversions(ADC12_1_INST);

#if 0
    if( gu16_ADC0_Result[0][gu16_ADC_cnt] < TEMP_NOT_CONNECT_VAL ) // 未接続判定
    {
        gu8_f_llc_temp_valid = 0;   // LLC温度無効
        gu16_c_llc_temp_valid = 0;
    } else {
        if( ++gu16_c_llc_temp_valid >= ADC_AVE_VALUE_N )
        {
            gu8_f_llc_temp_valid = 1;   // LLC温度無効
        }
    }
    if( gu16_ADC0_Result[1][gu16_ADC_cnt] < TEMP_NOT_CONNECT_VAL ) // 未接続判定
    {
        gu8_f_bbu_temp_valid = 0;   // BUU温度無効
        gu16_c_bbu_temp_valid = 0;
    } else {
        if( ++gu16_c_bbu_temp_valid >= ADC_AVE_VALUE_N )
        {
            gu8_f_bbu_temp_valid = 1;   // BUU温度無効
        }
    }
    if( gu16_ADC0_Result[3][gu16_ADC_cnt] < TEMP_NOT_CONNECT_VAL ) // 未接続判定
    {
        gu8_f_batt1_temp_valid = 0;   // BATT1温度無効
        gu16_c_batt1_temp_valid = 0;
    } else {
        if( ++gu16_c_batt1_temp_valid >= ADC_AVE_VALUE_N )
        {
            gu8_f_batt1_temp_valid = 1;   // BATT2温度無効
        }
    }
    if( gu16_ADC0_Result[2][gu16_ADC_cnt] < TEMP_NOT_CONNECT_VAL ) // 未接続判定
    {
        gu8_f_batt2_temp_valid = 0;   // BATT1温度無効
        gu16_c_batt2_temp_valid = 0;
    } else {
        if( ++gu16_c_batt2_temp_valid >= ADC_AVE_VALUE_N )
        {
            gu8_f_batt2_temp_valid = 1;   // BATT2温度無効
        }
    }
    gu8_f_batt_temp_valid = gu8_f_batt1_temp_valid | gu8_f_batt2_temp_valid;
#endif
    uint16_t batt_ad = gu16_ADC0_Result[3][gu16_ADC_cnt_4];

    input_filter( _NZ_, (pi_batt_con.sts == _ON_) ?(batt_ad > BATT_CONNECT_VAL):(batt_ad >= BATT_NOT_CONNECT_VAL), &pi_batt_con);


    if(batt_ad>=BATT_NOT_CONNECT_VAL)
    {
        gu8_f_batt_not_con=1;
    }
    else if(pi_batt_con.sts == _OFF_)
    {
        gu8_f_batt_not_con=0;
    }

    if(pi_batt_con.sts == _ON_)
    {
        gu16_ADC0_Sens[3] = 0;
        gu8_f_batt_not_con=1;
    }

    //4つの平均
    //gu16_ADC_cnt = (gu16_ADC_cnt + 1) & (ADC_AVE_VALUE_N-1);
    if( ++gu16_ADC_cnt_4 >= 4 )
    {
        gu16_ADC_cnt_4 = 0;
    }

    if( ++gu16_ADC_cnt_10 >= 10 )
    {
        gu16_ADC_cnt_10 = 0;
    }

    if( ++gu16_ADC_cnt_50 >= 50 )
    {
        gu16_ADC_cnt_50 = 0;
    }

    sum1_2 = 0;
    sum0_4 = 0;
    sum0_3 = 0;
    sum0_2 = 0;
    sum0_1 = 0;
    sum0_0 = 0;

    for (j = 0; j < 4; j++ )
    {
        sum1_2 += gu16_ADC1_Result[2][j];
        sum0_4 += gu16_ADC0_Result[4][j];
        if( gu8_f_batt_not_con!=1)      //移動平均を停止
        {
           sum0_3 += gu16_ADC0_Result[3][j];
        }

        sum0_2 += gu16_ADC0_Result[2][j];
        sum0_1 += gu16_ADC0_Result[1][j];
        sum0_0 += gu16_ADC0_Result[0][j];
    }

    gu16_ADC1_Sens[2] = sum1_2 / 4;
    gu16_ADC0_Sens[4] = sum0_4 / 4;

    if( gu8_f_batt_not_con!=1)      //移動平均を停止
    {
        gu16_ADC0_Sens[3] = sum0_3 / 4;
    }
    //gu16_ADC0_Sens[2] = sum0_2 / 4;
    gu16_ADC0_Sens[1] = sum0_1 / 4;
    gu16_ADC0_Sens[0] = sum0_0 / 4;

    sum1_0 = 0;
    sum1_1 = 0;
    sum0_6 = 0;
    sum0_5 = 0;
    for (j = 0; j < 50; j++ )
    {
        sum1_0 += gu16_ADC1_Result[0][j];
        sum1_1 += gu16_ADC1_Result[1][j];
        sum0_6 += gu16_ADC0_Result[6][j];
        sum0_5 += gu16_ADC0_Result[5][j];
    }
    gu16_ADC1_Sens[0] = sum1_0 / 50;
    gu16_ADC1_Sens[1] = sum1_1 / 50;
    gu16_ADC0_Sens[6] = sum0_6 / 50;
    gu16_ADC0_Sens[5] = sum0_5 / 50;

    sum0_5_10 = 0;
    for (j = 0; j < 10; j++ )
    {
        sum0_5_10 += gu16_ADC0_5_10[j];
    }

    /* S1.14 123F対策 補正の計算式を修正 */
#if 0
    gu16_ad_dischg_i  = gf_dischg_i_coeff  * gu16_ADC1_Sens[0]; // DISCHG_I(mA)
    gu16_ad_batt_v    = gf_batt_v_coeff    * gu16_ADC1_Sens[1]; // BATT_V(mV)
    gu16_ad_acdc12v_v = gf_acdc12v_v_coeff * gu16_ADC1_Sens[2]; // AC/DC12V_V(mV)
    gu16_ad_batt_chg  = gf_batt_chg_coeff  * gu16_ADC0_Sens[6]; // BATT_CHG(mA)
    gu16_ad_12vout_i  = gf_12vout_i_coeff  * gu16_ADC0_Sens[5]; // 12VOUT_I(mA)
    gu16_ad_12vout_v  = gf_12vout_v_coeff  * gu16_ADC0_Sens[4]; // 12VOUT_V(mV)
#endif
    /* S1.14A 演算結果が0より小さいと正の大きな値になっちまう */
    i16_tmp = (int16_t)((gf_dischg_i_coeff * (gu16_ADC1_Sens[0] - gf_dischg_i_coeff_ad2) + gf_dischg_i_coeff_po2) * 1000.0);
    if ( i16_tmp >= 0)
    {
        gu16_ad_dischg_i = i16_tmp;
    }
    else
    {
        gu16_ad_dischg_i = 0;
    }

    i16_tmp = (int16_t)((gf_batt_v_coeff * (gu16_ADC1_Sens[1] - gf_batt_v_coeff_ad2) + gf_batt_v_coeff_po2) * 1000.0);
    if ( i16_tmp >= 0)
    {
        gu16_ad_batt_v = i16_tmp;
    }
    else
    {
        gu16_ad_batt_v = 0;
    }

    i16_tmp = (int16_t)((gf_acdc12v_v_coeff * (gu16_ADC1_Sens[2] - gf_acdc12v_v_coeff_ad2) + gf_acdc12v_v_coeff_po2) * 1000.0);
    if ( i16_tmp >= 0)
    {
        gu16_ad_acdc12v_v = i16_tmp;
    }
    else
    {
        gu16_ad_acdc12v_v = 0;
    }

    i16_tmp = (int16_t)((gf_batt_chg_coeff * (gu16_ADC0_Sens[6] - gf_batt_chg_coeff_ad2) + gf_batt_chg_coeff_po2) * 1000.0);
    if ( i16_tmp >= 0)
    {
        gu16_ad_batt_chg = i16_tmp;
    }
    else
    {
        gu16_ad_batt_chg = 0;
    }
    gu16_val_12vout_i_50  = gf_12vout_i_coeff  * gu16_ADC0_Sens[5]; // 12VOUT_I(mA)
    gu16_val_12vout_i_10  = gf_12vout_i_coeff  * sum0_5_10 / 10;    // 12VOUT_I(mA)
    gu16_val_12vout_i     = gu16_val_12vout_i_50;                   /* ログ記録以外は50回平均を使用する */

    i16_tmp = (int16_t)((gf_12vout_v_coeff * (gu16_ADC0_Sens[4] - gf_12vout_v_coeff_ad2) + gf_12vout_v_coeff_po2) * 1000.0);
    if ( i16_tmp >= 0)
    {
        gu16_ad_12vout_v = i16_tmp;
    }
    else
    {
        gu16_ad_12vout_v = 0;
    }

    if(gu8_f_charge_output == _OFF_)//放電中ではない場合
    {
       gu16_ad_dischg_i = 0;

    }

    /* S1.14 123F対策 補正の計算式を修正した関係でオフセット補償を削除する */
#if 0
    else if(gu16_ad_dischg_i >= 50)
    {
      gu16_ad_dischg_i -= 50;

    }else
    {
      gu16_ad_dischg_i = 0;
    }
#endif

    /* S1.15 F138対策 DCIR中に充電電流がゼロになるのを抑止 */
    //if(gu8_f_charging_active==_OFF_)//充電中ではない場合
    if((gu8_f_dcir_check_doing == 0) && (gu8_f_charging_active==_OFF_)) //DCIR測定中で無くて、かつ、充電中ではない場合
    {
        gu16_ad_batt_chg=0;
    }

    if ((g_eeprom_data.set_erp.burst == _ENABLE_) && (gu8_f_ps_on == _OFF_) && (gu8_f_charging_active == 0))
    {
        gu_f_burst_i_over = input_filter( _NZ_,(pi_burst_i_over.sts == _ON_) ? (gu16_val_12vout_i >= BURST_I_SAFE) : (gu16_val_12vout_i >= BURST_I_OVER), & pi_burst_i_over );
    }
    else
    {
        filter_clear(&pi_burst_i_over);
        gu_f_burst_i_over=2;
    }

    /* S1.13 主充電できない問題の対策 */
    /* ここから */
    /* バッテリー未接続フラグがunknown(=2)の時は以下の条件で接続中(=0)にする */
    /* BATT1温度のAD値の移動平均値がしきい値以下 */
    if (gu8_f_batt_not_con == 2)
    {
        if (gu16_ADC0_Sens[3] <= BATT_CONNECT_VAL)
        {
            gu8_f_batt_not_con = 0;
        }
    }
    /* ここまで */

    if(gu8_f_batt_not_con==0)
    {
        gu8_f_batt_connect = _BATT1_CONNECT_;   // BATT1接続
        gi16_ad_batt1_temp = calc_temperature(gu16_ADC0_Sens[3],B1_3450);  // BATT_TEMP6+ (BATT1)
        gi16_ad_battery_temp = gi16_ad_batt1_temp;
    }
    else if(pi_batt_con.sts == _ON_)
    {
        gu8_f_batt_connect = _BATT_NOT_CONNECT_;
        gi16_ad_batt1_temp=0;
        gi16_ad_battery_temp=0;
    }

    /*** バッテリ接続 トリガ検出 ***/
    gu8_f_batt_connect_trg = _TRG_NONE_;
    if( gu8_f_proc_start != 0 )
    {
        if( (gu8_f_batt_connect != _BATT_NOT_CONNECT_ ) && (gu8_f_batt_connect_old == _BATT_NOT_CONNECT_) )
        {
            gu8_f_batt_connect_trg = _TRG_ON_;  // バッテリ接続トリガ
        }
        else if( (gu8_f_batt_connect == _BATT_NOT_CONNECT_ ) && (gu8_f_batt_connect_old != _BATT_NOT_CONNECT_) )
        {
            gu8_f_batt_connect_trg = _TRG_OFF_; // バッテリ未接続トリガ
        }
        gu8_f_batt_connect_old = gu8_f_batt_connect;
    }
    /*******************************/

    //gu16_ADC0_Sens[1] = 1890; /* 30℃ */
    //gu16_ADC0_Sens[1] = 960;  /* 65℃ */
    //gu16_ADC0_Sens[1] = 880;  /* 70℃ */
    //gu16_ADC0_Sens[1] = 800;  /* 75℃ */
    //gu16_ADC0_Sens[1] = 740;  /* 80℃ */
    //gu16_ADC0_Sens[1] = 680;  /* 85℃ */

#ifdef _S114_DEBUG_
    /*
    ++dbg_1ms_cnt;
    if (dbg_1ms_cnt < 30000)
    {
        gi16_ad_battery_temp = 300;
    }
    else
    {
        if (dbg_1ms_cnt < 60000)
        {
            gi16_ad_battery_temp = 660;
        }
        else
        {
            if (dbg_1ms_cnt < 90000)
            {
                gi16_ad_battery_temp = 300;
            }
        }
    }
    */

    /*
    ++dbg_1ms_cnt;
    if (dbg_1ms_cnt < 30000)
    {
        ;
    }
    else
    {
        if (dbg_1ms_cnt < 60000)
        {
            gu16_ad_batt_v   = 10300;
            gu16_ad_batt_chg = 390;
        }
        else
        {
            if (dbg_1ms_cnt < 90000)
            {
                ;
            }
        }
    }
    */
#endif

    gi16_ad_bbu_temp   = calc_temperature(gu16_ADC0_Sens[1],B2_3435);  // BUU_TEMP
    gi16_ad_llc_temp   = calc_temperature(gu16_ADC0_Sens[0],B2_3435);  // AC/DC_TEMP_IN
}

/*******************************************************************************
 * Function Name: input_io()
 * Description  : input GPIO
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
static void input_io(void)
{
    //static uint8_t f_ac_on_old = _OFF_;
//#ifndef _DEBUG_DATA_ON_

    gu8_f_ps_on        = input_filter( _Z_, I_PS_ON_IN, &pi_ps_on);             // "L"でON(sts=ON)
//#endif
    gu8_f_burst_on     = input_filter( _Z_, I_BURST_IN, &pi_burst_on);          // "L"でBURST(sts=ON)
    gu8_f_dischg12_ovp = input_filter( _Z_, I_DISCHG12V_OVP, &pi_dischg12_ovp); // "L"で異常(sts=ON)
    gu8_f_pfc_fail_in  = input_filter( _Z_, I_PFC_FAIL_IN, &pi_pfc_fail_in);    // "L"で異常(sts=ON)

    //input_filter( _NZ_, I_AC_ON_IN, &pi_ac_on_no_isr);                   // "H"が8ms検出でACなし(sts=ON)
    //if( pi_ac_on_no_isr.trg == _TRG_ON_ )  // ACが完全に無くなると割込みも上がらなくなるため
    //{
    //    gu8_f_ac_on = _OFF_;
    //    gu8_f_ac_interrupt_check = 0;
    //}
    gu8_f_ac_on_1ms = input_ac_on_filter(_Z_, I_AC_ON_IN, &pi_ac_on_level);

    if ((gu8_f_ac_on_1ms != 0) && (gu16_c_ac_on < TIMER_200ms))
    {
        gu16_c_ac_on++;
    }
    gu8_f_ac_on = (gu16_c_ac_on >= TIMER_200ms) ? _ON_ : _OFF_;

#if 0
    if( gu8_f_ac_on==1 )
    {
       // O_TEST_OUT_H;
    }
    else
    {
       // O_TEST_OUT_L;
    }
#endif

    /*** AC OFF->ON/ON->OFF トリガ検出 ***/
    gu8_f_ac_on_trg = _TRG_NONE_;
    if( gu8_f_proc_start != 0 )
    {
        if( ((gu8_f_ac_on ^ gu8_f_ac_on_old) & gu8_f_ac_on) != 0 ) // AC OFF->ON?
        {
            gu8_f_ac_on_trg = _TRG_ON_;   // AC OFF->ONトリガ
            //gu8_f_ac_70v_syundan = _OFF_; // 70V瞬断検出 OFF
        }
        else if( ((gu8_f_ac_on ^ gu8_f_ac_on_old) & gu8_f_ac_on_old) != 0 ) // AC ON->OFF?
        {
            gu8_f_ac_on_trg = _TRG_OFF_;  // AC ON->OFFトリガ
        }
        gu8_f_ac_on_old = gu8_f_ac_on;
    }
    /*************************************/
}

/*******************************************************************************
 * Function Name: input_re_ac()
 * Description  : input GPIO
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void input_re_ac(void)
{
    gu8_f_aft_ac_on=input_aft_ac_on_filter( _Z_, I_AC_ON_IN, &pi_aft_ac_on_level);

    if(gu8_f_aft_ac_on!=0)
    {
        if(gu16_c_aft_ac_on<TIMER_600ms)
        {
             gu16_c_aft_ac_on++;
        }
    }
}

/*******************************************************************************
 * Function Name: input_init_ac()
 * Description  : input GPIO
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void input_init_ac(void){

#ifdef _WWDT_ON_
    DL_WWDT_disablePower(WWDT0_INST);
#endif
    while (gu16_c_ac_on < TIMER_100ms)
    {

        sleep();
        gu8_f_ac_on_1ms = input_ac_on_filter(_Z_, I_AC_ON_IN, &pi_ac_on_level);

        if ((gu8_f_ac_on_1ms != 0))
        {
            gu16_c_ac_on++;
        }
    }
    gu8_f_12v_en_out        = _OUT_ON_;        // /12V_EN ON
    gu32_c_12v_en_out_delay = 0;

    /* S1.13 いきなり補充電が始まる不具合対策（AC復電検出で_ON_(1)をセットすることで復電後タイマーを有効にする */
    u8_f_afterer_power_restored = _ON_;

#ifdef _WWDT_ON_
    DL_WWDT_enablePower(WWDT0_INST);
#endif
}

/*******************************************************************************
 * Function Name: input_ac_on_filter()
 * Description  :
 * Arguments    : flag : _Z_/_NZ_
 *                input : 0="L", 1="H"
 *                *fil  : _Filter
 * Return Value : Status
 *******************************************************************************/
uint8_t input_ac_on_filter(uint8_t flag, uint8_t input, struct _Filter *fil)
{
    //static uint8_t c_ac_on = 0;

    if(input == flag) // L
    {
        fil->OF = 0;

        if ((fil->ON) <= MAX_DET_TIMER)
        {
           (fil->ON)++;
        }

        if(fil->ON >= fil->ON_time)
        {
          (fil->sts) = _ON_;              // status ON
        }
    }
    else // H
    {
        if(fil->sts == _OFF_)
        {
            fil->ON = 0;
        }

        if ((fil->OF) <= MAX_DET_TIMER)
        {
           (fil->OF)++;
        }

        if(fil->OF >= fil->OF_time)
        {
            fil->sts = _OFF_;
            fil->ON = 0;
            fil->OF = fil->OF_time;
            gu16_c_ac_on=0;

        }
    }
    return fil->sts;
}

/*******************************************************************************
 * Function Name: input_aft_ac_on_filter()
 * Description  :
 * Arguments    : flag : _Z_/_NZ_
 *                input : 0="L", 1="H"
 *                *fil  : _Filter
 * Return Value : Status
 *******************************************************************************/
uint8_t input_aft_ac_on_filter(uint8_t flag, uint8_t input, struct _Filter *fil)
{
    //static uint8_t c_ac_on = 0;
    if(input == flag) // L
    {
        fil->OF = 0;

        if ((fil->ON) <= MAX_DET_TIMER)
        {
           (fil->ON)++;
        }

        if(fil->ON >= fil->ON_time)
        {
          (fil->sts) = _ON_;              // status ON
        }
    }
    else // H
    {
        if(fil->sts == _OFF_)
        {
            fil->ON = 0;

        }

        if ((fil->OF) <= MAX_DET_TIMER)
        {
           (fil->OF)++;
        }

        if(fil->OF >= fil->OF_time)
        {
            fil->sts = _OFF_;
            fil->ON = 0;
            fil->OF = fil->OF_time;
            gu16_c_aft_ac_on=0;

        }
    }
    return fil->sts;
}
/*******************************************************************************
 * Function Name: input_protect()
 * Description  : input GPIO
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
static void input_protect(void)
{
    int16_t temp;

    /* AC_LINK Resrart中 or PS_OFF過電流? */
    if( (gu8_f_ac_link_restarting != 0) || (gu8_f_12v_oc_off != 0) )
    {
        filter_clear(&pi_low_v);
      //  filter_clear(&pi_bbu_sw_short);
        filter_clear(&pi_bbu_sw_open);
    }

    /* PS_ON  OFF<->ON? */
    if( (pi_ps_on.trg == _TRG_ON_) || (pi_ps_on.trg == _TRG_OFF_) || (gu8_f_proc_start == 0) )
    {
        filter_clear(&pi_low_v);
        filter_clear(&pi_high_i_on);
        filter_clear(&pi_high_i_on_50ms);
        filter_clear(&pi_high_i_of);
        filter_clear(&pi_high_i_of_h);
        filter_clear(&pi_high_v);
        filter_clear(&pi_bbu_sw_short);
        filter_clear(&pi_bbu_sw_open);
    }

    /* 項番1-2:不足電圧 2-1 [+12V各種異常] */
    gu8_f_low_v = input_filter( _NZ_, (gu16_ad_12vout_v<= PRO_LOW_V), &pi_low_v);

    if(gu8_f_ps_on==_ON_)    //8/25
    {
        /* 項番3:過電流保護 2-8 */

        /* 生値が10回連続でしきい値以上となったらフラグをONする */
        gu8_f_high_i_on      = input_filter( _NZ_, ((gf_12vout_i_coeff * gu16_ad_12vout_i_now_ad) >= PRO_HIGH_I_ON), & pi_high_i_on );

        /* 50回移動平均値がしきい値以上となったらフラグをONする */
        gu8_f_high_i_on_50ms = input_filter( _NZ_, (gu16_val_12vout_i_50 >= PRO_HIGH_I_ON), & pi_high_i_on_50ms );

        /* 10回移動平均値がしきい値以上となったらフラグをONする */
        gu8_f_high_i_on_10ms = input_filter( _NZ_, (gu16_val_12vout_i_10 >= PRO_HIGH_I_ON), & pi_high_i_on_10ms );
    }
    else
    {
        /* 項番4:過電流保護 2-10 [+12V各種異常] */
        gu8_f_high_i_of        =input_filter( _NZ_, (gu16_val_12vout_i>=PRO_HIGH_I_OF), & pi_high_i_of );
        gu8_f_high_i_of_h      =input_filter( _NZ_, (gu16_val_12vout_i>=PRO_HIGH_I_OF_H), & pi_high_i_of_h );
    }

    /* 項番8:過電圧保護 2-7 */
    gu8_f_high_v       = input_filter( _NZ_, ((gf_12vout_v_coeff  * gu16_ad_12vout_v_now_ad) >= PRO_HIGH_V), & pi_high_v );

    /* 項番10:過電流保護 2-15  BATT6直 [放電回路各種異常] */
    gu8_f_high_i_dis_6 = input_filter( _NZ_, (gu16_ad_dischg_i >= PRO_HIGH_I_DIS), & pi_high_i_dis_6);

    /* 項番12:過電流保護 2-13 [充電回路各種異常] */
    gu8_f_high_i_cha   = input_filter( _NZ_, (gu16_ad_batt_chg >= PRO_HIGH_I_CHG), & pi_high_i_cha);

    /* 項番14:過電圧保護 2-11  BATT6直 */
    gu8_f_high_v_cha_6 = input_filter( _NZ_, ((gf_batt_v_coeff*gu16_ad_chgout_v_now_ad) >= PRO_HIGH_V_CHG), & pi_high_v_cha_6 );

    /* 項番15:不足保護 2-14 [充電回路各種異常] 充電回路不足電圧は充電電流の低下で検出 */
    gu8_f_low_v_shortage    = input_filter( _NZ_, (gu16_ad_batt_chg <= PRO_SHORTAGE1), & pi_low_v_shortage);
    gu8_f_low_v_shortage_5a = input_filter( _NZ_, (gu16_ad_batt_chg >= PRO_SHORTAGE2), & pi_low_v_shortage_5a);

    /* 項番16:出力スイッチ故障(ショート) 2-9 [+12V各種異常] */
    gu8_f_bbu_sw_short = input_filter( _NZ_, (gu16_ad_12vout_v >= PRO_BBU_SHORT), & pi_bbu_sw_short);

    /* 項番17:出力スイッチ故障(オープン) 2-9 [+12V各種異常] */
    gu8_f_bbu_sw_open  = input_filter( _NZ_, (gu16_ad_12vout_v <= PRO_BBU_OPEN), & pi_bbu_sw_open);

    if( SP_ADU_TEMP_THD != UINT8_MAX_VALUE_UNDER )
    {
        /* 項番18:ADU 温度異常保護(警告) 1-1 [温度異常] */
        temp = gi16_ad_llc_temp / 10;
        gu8_f_fan_fail_adu   = input_filter( _NZ_,  (pi_fan_fail_adu.sts == _ON_) ? (temp >= (SP_ADU_TEMP_THD-10)): (temp >= SP_ADU_TEMP_THD), & pi_fan_fail_adu);
    }
    else
    {
        /* 無効 */
        gu8_f_fan_fail_adu = _OFF_;
    }

    if( SP_BBU_TEMP_THD != UINT8_MAX_VALUE_UNDER )
    {
        temp = gi16_ad_bbu_temp / 10;
        gu8_f_fail_bbu       = input_filter( _NZ_,  (pi_fail_bbu.sts == _ON_) ? (temp >= (SP_BBU_TEMP_THD-10)): (temp >= SP_BBU_TEMP_THD), & pi_fail_bbu);

        /* 項番19:BBU 温度異常保護(警告) 1-2 [温度異常] */
        gu8_f_fan_fail_bbu   = input_filter( _NZ_,  (pi_fan_fail_bbu.sts == _ON_) ? (temp >= (SP_BBU_TEMP_THD-10)): (temp >= SP_BBU_TEMP_THD), & pi_fan_fail_bbu);
    }
    else
    {
        /* 無効 */
        gu8_f_fan_fail_bbu  = _OFF_;
        gu8_f_fail_bbu      = _OFF_;
    }

    /* 項番20:ADU 温度異常保護 1-3 [温度異常] */
    gu8_f_temp_fail_adu =input_filter( _NZ_, (gi16_ad_llc_temp >= PRO_TEMP_ADU), & pi_temp_fail_adu);

    /* 項番21:BBU 温度異常保護 1-4 [温度異常] */
    gu8_f_temp_fail_bbu =input_filter( _NZ_, (gi16_ad_bbu_temp >= PRO_TEMP_BBU), & pi_temp_fail_bbu);

    temp = gi16_ad_battery_temp / 10;
    // 充電開始時はSP_BATT_WNG_THD(65)の-25℃の値、すなわち41℃。充電中は充電開始の+25℃のSP_BATT_WNG_THD(65)になった時

    /* 非充電中 */
    if( gu8_f_charging_active == _OFF_ )
    {
        /* 項番30:バッテリ温度抑止(充電中) 22.3.1 項番2 [バッテリ異常] */
        gu8_f_batt_temp_bef = input_filter( _NZ_,  (pi_batt_temp_bef.sts == _ON_) ? (temp >= (SP_BATT_WNG_CLR_THD)): (temp >= SP_BATT_WNG_CLR_THD), & pi_batt_temp_bef);
    }
    else
    {
        /* 項番30:バッテリ温度抑止(充電中) 22.3.1 項番2 [バッテリ異常] */
        gu8_f_batt_temp_aft = input_filter( _NZ_,  (pi_batt_temp_aft.sts == _ON_) ? (temp >= (SP_BATT_WNG_CLR_THD)): (temp >= SP_BATT_WNG_THD), & pi_batt_temp_aft);
    }

    if(gu8_f_charging_active==_ON_||(pi_batt_break_chg.sts == _ON_))
    {
        filter_clear(&pi_batt_break);
        if(gu16_batt_break_chg_timer==0)
        {
           gu8_f_batt_break_chg  =input_filter(_NZ_,(pi_batt_break_chg.sts == _ON_)?((gu16_ad_batt_v < PRO_PFAIL_V2) ||(gu16_ad_batt_v> PRO_PFAIL_V)) :((gu16_ad_batt_v >= PRO_PFAIL_V) &&(gu16_ad_batt_chg <= PRO_PFAIL_I)),&pi_batt_break_chg);
        }
        else
        {
            gu16_batt_break_chg_timer--;
        }

    }
    else if (gu8_f_charging_active==_OFF_)
    {
        filter_clear(&pi_batt_break_chg);
        /* 項番31:バッテリ保護素子破損 22.3.1 項番3 [バッテリ異常] */
        gu8_f_batt_break = input_filter( _NZ_, (pi_batt_break.sts == _ON_) ? (gu16_ad_batt_v <= PRO_PFAIL_CHG_V) : (gu16_ad_batt_v <= PRO_PFAIL_CHG_V2), & pi_batt_break);
    }

    /*  項番32:バッテリ未接続 22.3.1 項番4 [バッテリ異常] */
    gu8_f_batt_not = input_filter( _NZ_, (gu8_f_batt_connect == _BATT_NOT_CONNECT_), & pi_batt_not);

    /* 項番33:バッテリ温度異常 22.3.2 項番1 [バッテリ異常] */
    temp = gi16_ad_battery_temp / 10;
    gu8_f_latch_fail = input_filter( _NZ_, (temp>=SP_BATT_ALM_THD), & pi_latch_fail );

    /* 項番34:バッテリ低電圧 22.3.2 項番2  BATT6直    [バッテリ異常] */
    gu8_f_batt_low_6 = input_filter( _NZ_, (gu16_ad_batt_v <= PRO_BATT_LOW), & pi_batt_low_6 );

#ifdef _RELEASE_MODE_
    /* 項番36:バッテリ高電圧 22.3.2 項番3  BATT6直    [バッテリ異常] */
    gu8_f_batt_high_6 = input_filter( _NZ_, (gu16_ad_batt_v >= 10500), & pi_batt_high_6);
#else
    /* 項番36:バッテリ高電圧 22.3.2 項番3  BATT6直    [バッテリ異常] */
    gu8_f_batt_high_6 = input_filter( _NZ_, (gu16_ad_batt_v >= PRO_BATT_HIGH), & pi_batt_high_6);
#endif
}

/*******************************************************************************
 * Function Name: input_filter()
 * Description  :
 * Arguments    : flag : _Z_/_NZ_
 *                input : 0="L", 1="H"
 *                *fil  : _Filter
 * Return Value : Status
 *******************************************************************************/
uint8_t input_filter(uint8_t flag, uint8_t input, struct _Filter *fil)
{
    (fil->trg) = _TRG_NONE_;
    if ((input) == flag)                   // ON
    {
        if ((fil->ON) <= MAX_DET_TIMER)
        {
            (fil->ON)++;
        }

        if ((fil->ON) >= (fil->ON_time))
        {
            if ((fil->ON) == (fil->ON_time))
            {
                if( (fil->sts) == _OFF_)
                {
                    (fil->trg) = _TRG_ON_;
                }
            }
            (fil->sts) = _ON_;              // status ON
        }

        (fil->OF) = 0;
    }
    else                                // OFF
    {
        if ((fil->OF) <= MAX_DET_TIMER)
        {
            (fil->OF)++;
        }

        if ((fil->OF) >= (fil->OF_time))
        {
            if ((fil->OF) == (fil->OF_time))
            {
                if( (fil->sts) == _ON_)
                {
                    (fil->trg) = _TRG_OFF_;
                }
            }
            (fil->sts) = _OFF_;            // status OFF
        }

        (fil->ON) = 0;
    }
    return (fil->sts);
}

/******************************************************************************
* Function Name: filter_clear()
* Description  :
* Arguments    :
* Return Value : None
*******************************************************************************/
void filter_clear(struct _Filter *fil)
{
    fil->ON  = 0;
    fil->OF  = 0;
    fil->sts = 0;
    fil->trg = _TRG_NONE_;
}

/******************************************************************************
* Function Name: filter_clear()
* Description  :
* Arguments    : None
* Return Value : None
*******************************************************************************/
void filter_clear_all(void)
{
    filter_clear(&pi_ps_on);
    filter_clear(&pi_burst_on);
    filter_clear(&pi_dischg12_ovp);
    filter_clear(&pi_pfc_fail_in);
}

/******************************************************************************
* Function Name: calc_temperature()
* Description  : 温度計算
* Arguments    : AD値,B
* Return Value : 温度(10倍値)  ex) 35.0℃ = 350
*******************************************************************************/
int16_t calc_temperature(uint16_t ad, uint16_t bb)
{
#if 0
    double V;
    double R1;
    double temp;

    if( ad <= 300 )  // リミットを設けておく
    {
        ad = 300;           // およそ169℃
    }
    else if( ad >= 4000 )
    {
        ad = 4000;          // およそ-48℃
    }

    V = (double)ad / UINT12_MAX_VALUE * VCC_33V;

    // R1=(VxR上 + VxR下 - VccxR下) / (Vcc-V)
    R1 = (V*R_UPPER_10K + V*R_LOWER_056K - VCC_33V*R_LOWER_056K) / (VCC_33V-V);
    
    //温度＝1/((LN(R1/R0)/B+1/(T0+273)))-273
    temp = 1/(log(R1/R0_10K)/bb + 1/(T0_25C+273)) - 273;
#if 1
    temp *= 10;
#endif
    return (int16_t)temp;
#else
    _iq19 V;
    _iq19 R1;
    _iq19 t1,t2,t3;
    int16_t temp;

    if( ad <= 300 )  // リミットを設けておく
    {
        ad = 300;           // およそ169℃
    }
    else if( ad >= 4000 )
    {
        ad = 4000;          // およそ-48℃
    }

    // _IQ19(-4096～4095.9999)
    V = _IQ19mpy( _IQ19div(_IQ19(ad), _IQ19(UINT12_F_MAX_VALUE)), _IQ19(VCC_33V) );

    // R1=(VxR上 + VxR下 - VccxR下) / (Vcc-V)
    R1 = _IQ19div((_IQ19mpy(V,_IQ19(R_UPPER_10K))+_IQ19mpy(V,_IQ19(R_LOWER_056K))-_IQ19mpy(_IQ19(VCC_33V),_IQ19(R_LOWER_056K))),(_IQ19(VCC_33V)-V));

    //温度＝1/((LN(R1/R0)/B+1/(T0+273)))-273
    t1 = _IQ19div(_IQ19log(_IQ19div(R1,_IQ19(R0_10K))),_IQ19(bb));
    t2 = _IQ19div(_IQ19(1.0),(_IQ19(T0_25C)+_IQ19(273.0)));
#if 0
    t3 = _IQ19div(_IQ19(1.0),(t1+t2))-_IQ19(273.0);
#else
    t3 = _IQ19mpy( (_IQ19div(_IQ19(1.0),(t1+t2))-_IQ19(273.0)) , _IQ19(10) );  // 10倍
#endif
    temp = (int16_t)_IQ19int(t3);
    
    return temp;
#endif
}

/*******************************************************************************
 * Function Name: startup_input_ad()
 * Description  : 立上げ時 ADC収集処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void startup_input_ad(void)
{
    uint8_t i;

    for( i=0; i<ADC_AVE_VALUE_N; i++ )   // 移動平均分 ADを収集する。
    {
        sleep();             // 1ms Wait

        //DL_WWDT_restart(WWDT0_INST);

        input_ad();
    }
}
