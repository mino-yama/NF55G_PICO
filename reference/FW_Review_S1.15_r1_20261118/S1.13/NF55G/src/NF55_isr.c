#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"

void HardFault_Handler(void);
void SysTick_Handler(void);
uint32_t get_sys_difftimer(uint32_t _time);
extern void error_log_request( uint8_t almid );
extern uint16_t calc_bcc( uint8_t *buf, uint16_t len );

extern volatile uint8_t *gpt_I2C_RxPacket;

#ifdef _DEBUG_ON_
#define HISSIZ 1000
uint16_t    hisbuf[HISSIZ];
uint16_t    hisptr = 0;

void his(uint16_t prm)
{
    hisbuf[hisptr] = prm;
    if (hisptr < (HISSIZ - 1))
    {
        ++hisptr;
    }
    else
    {
        hisptr = 0;
    }
}
#endif



/*******************************************************************************
* Function Name: HardFault_Handler()
* Description  : Hard Fault 割込み
* Arguments    : None
* Return Value : None
*******************************************************************************/
void HardFault_Handler(void)
{
    // Enter an infinite loop.
    volatile int i = 1;
    while(i)
    {
    }
}

/*******************************************************************************
* Function Name: SysTick_Handler()
* Description  : SYsTick 割込み
* Arguments    : None
* Return Value : None
*******************************************************************************/
#if 1
void SysTick_Handler(void)
{
    gu32_SysTickCount++;
    if( ++gu16_c_timing1ms >= ONE_LOOP )
    {
        gu16_f_timing++;  // 1ms
        gu16_c_timing1ms = 0;
    }
    if( ++gu16_c_timing1s >= TIMER_1000ms )
    {
        gu16_f_timing = 1;  // 1s
        gu16_c_timing1s = 0;
    }
#if 0
    if( gu8_f_ac_syundan_1s != 0 )
    {
        if( get_sys_difftimer(gu32_syundan_timer) >= TIMER_1000ms ) // 1秒
        {
            gu8_f_ac_syundan_1s = 0;

            gu8_f_ac_under_70v = _OFF_;
            gu16_c_ac_on_flt = 0;
        }
    }
#endif
}
#else
RAMFUNC void SysTick_Handler(void)
{
    gu32_SysTickCount++;
    if( ++gu16_c_timing1ms >= ONE_LOOP )
    {
        gu16_f_timing++;  // 1ms
        gu16_c_timing1ms = 0;
    }
}
#endif

/*******************************************************************************
 * Function Name: ADC12_0_INST_IRQHandler()
 * Description  : ADC0 割込み
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void ADC12_0_INST_IRQHandler(void)
{

    switch (DL_ADC12_getPendingInterrupt(ADC12_0_INST))
    {
        case DL_ADC12_IIDX_MEM0_RESULT_LOADED:
            gu16_CheckADC0 |= 0x01;
            break;
        case DL_ADC12_IIDX_MEM1_RESULT_LOADED:
            gu16_CheckADC0 |= 0x02;
            break;
        case DL_ADC12_IIDX_MEM2_RESULT_LOADED:
            gu16_CheckADC0 |= 0x04;
            break;
        case DL_ADC12_IIDX_MEM3_RESULT_LOADED:
            gu16_CheckADC0 |= 0x08;
            break;
        case DL_ADC12_IIDX_MEM4_RESULT_LOADED:
            gu16_CheckADC0 |= 0x10;
            break;
        case DL_ADC12_IIDX_MEM5_RESULT_LOADED:
            gu16_CheckADC0 |= 0x20;
            break;
        case DL_ADC12_IIDX_MEM6_RESULT_LOADED:
            gu16_CheckADC0 |= 0x40;
            break;
        default:
            break;
    }

}

/*******************************************************************************
 * Function Name: ADC12_1_INST_IRQHandler()
 * Description  : ADC1 割込み
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void ADC12_1_INST_IRQHandler(void)
{

    switch (DL_ADC12_getPendingInterrupt(ADC12_1_INST))
    {
        case DL_ADC12_IIDX_MEM0_RESULT_LOADED:
            gu16_CheckADC1 |= 0x01;
            break;
        case DL_ADC12_IIDX_MEM1_RESULT_LOADED:
            gu16_CheckADC1 |= 0x02;
            break;
        case DL_ADC12_IIDX_MEM2_RESULT_LOADED:
            gu16_CheckADC1 |= 0x04;
            break;
        default:
            break;
    }

}

/*******************************************************************************
 * Function Name: GROUP1_IRQHandler()
 * Description  : GROUP1 割込み
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void GROUP1_IRQHandler(void)
{
       uint32_t c_fan_prm_new = 0;
//static uint32_t c_fan_prm_old = 0;
       uint32_t c_ac_on_new = 0;
//static uint32_t c_ac_on_old = 0;
       uint32_t diff;
       //float   t1;

//static  uint8_t     su8_f_rpm = 0;   /* 初回の割込み発生を記憶 */
        uint32_t    now_rpm;

    uint32_t gpio = DL_GPIO_getEnabledInterruptStatus(GPIO_GRP_B_PORT,
        (GPIO_GRP_B_PB14_INPUT_PIN | GPIO_GRP_B_PB3_INPUT_PIN));  // FAN PRM / AC_ON_IN

    /*************************/
    /***** FAN PRM(PB14) *****/
    /*************************/
    if ((gpio & GPIO_GRP_B_PB14_INPUT_PIN) == GPIO_GRP_B_PB14_INPUT_PIN)
    {
#ifdef _DEBUG_ON_
        //O_TEST_OUT_H;
#endif
        DL_GPIO_clearInterruptStatus(GPIO_GRP_B_PORT, GPIO_GRP_B_PB14_INPUT_PIN);
        now_rpm = DL_Timer_getTimerCount(TIMER_G12_INST);   // 1count = 1/10MHz

        if (gu8_f_rpm == 0)
        {
            gu8_f_rpm = 1;
            gu32_c_fan_prm_old = now_rpm;
        }
        else
        {
            if( gu32_c_fan_prm_old >= now_rpm )
             {
                 diff = gu32_c_fan_prm_old - now_rpm;
             } else {
                 diff = gu32_c_fan_prm_old + ~now_rpm;
             }

             gu32_c_fan_prm_old = now_rpm;
             gu32_b_fanrpm[gu16_p_fanrpm] = diff;

             if (gu16_p_fanrpm < UINT8_MAX_VALUE)
             {
                 ++gu16_p_fanrpm;
             }
        }
#ifdef _DEBUG_ON_
        //O_TEST_OUT_L;
#endif
#if 0

        // Down counter
        c_fan_prm_new = DL_Timer_getTimerCount(TIMER_G12_INST);   // 1count = 1/10MHz
        if( gu32_c_fan_prm_old >= c_fan_prm_new )
        {
            diff = gu32_c_fan_prm_old - c_fan_prm_new;
        } else {
            diff = gu32_c_fan_prm_old + ~c_fan_prm_new;
        }
        gu32_c_fan_prm_old = c_fan_prm_new;
#if 1
        t1 = (float)diff * 0.0000001f;   // 1/10MHz
        gu16_d_fan_rpm = (uint16_t)(60.0 / (t1*2.0));
#endif
#ifdef _DEBUG_ON_
        if(gu8_his_flg != 0)
        {
            his(gu16_d_fan_rpm);
        }
#endif
#endif
    }
    /*************************/
    /***** AC_ON_IN(PB3) *****/
    /*************************/
    if ((gpio & GPIO_GRP_B_PB3_INPUT_PIN) == GPIO_GRP_B_PB3_INPUT_PIN)
    {


        DL_GPIO_clearInterruptStatus(GPIO_GRP_B_PORT, GPIO_GRP_B_PB3_INPUT_PIN);
#if 0 // 2026/5/28
#if 0
        // Down counter
        c_ac_on_new = DL_Timer_getTimerCount(TIMER_G12_INST);   // 1count = 1/10MHz
        if( gu32_c_ac_on_old >= c_ac_on_new )
        {
            diff = gu32_c_ac_on_old - c_ac_on_new;
        } else {
            diff = gu32_c_ac_on_old + ~c_ac_on_new;
        }
        gu32_c_ac_on_old = c_ac_on_new;

        if( I_AC_ON_IN == _H_ ) // AC入力
        {
            gu32_c_ac_on_period  = diff;    // ON期間
            if( gu32_c_ac_on_period >= AC_TIME_3_5MS ) // ON期間=3.5ms?
            {
                if( (gu8_f_ac_on == _OFF_) && (gu8_f_syundan_check != 0) )
                {
                    gu8_f_syundan_detect = 1;   // 瞬断検出(AC無しからAC有り)
                }
                gu16_c_ac_on_flt++;
                if( gu16_c_ac_on_flt >= 20 ) // 20パルス連続?
                {
                    gu8_f_ac_on = _ON_;     // AC有り
                    gu16_c_ac_on_flt = 20;
                }
            } else {
                gu8_f_ac_on = _OFF_;        // AC無し
                gu16_c_ac_on_flt = 0;
            }
        } else {
            gu32_c_ac_off_period = diff;   // OFF期間
            if( gu32_c_ac_off_period >= AC_TIME_7MS ) // OFF期間=7ms?
            {
                if( (gu8_f_ac_on == _ON_) && (gu8_f_syundan_check == 0) )
                {
                    gu8_f_syundan_check = 1;     // 瞬断チェック開始
                    gu8_f_syundan_detect = 0;
                    gu32_syundan_timer = gu32_SysTickCount;  // 1ms
                }

                gu8_f_ac_on = _OFF_;        // AC無し
                gu16_c_ac_on_flt = 0;
            }
        }

        if( gu8_f_syundan_check != 0 ) // 瞬断チェック
        {
            if( get_sys_difftimer(gu32_syundan_timer) >= TIMER_1000ms ) // 1秒
            {
                if( gu8_f_syundan_detect != 0 ) // 瞬断あり?
                {
                    // 瞬断カウント+1(AC_FAIL_COUNT)
                    // EEPROM(積算データ)
                    gu8_f_ac_syundan_1s = _ON_;
                }
                gu8_f_syundan_check = 0;
            }
            //if( gu8_f_ac_on == _ON_ )
            //{
            //    gu8_f_syundan_check = 0;
            //}
        }
#else
        // Down counter
        c_ac_on_new = DL_Timer_getTimerCount(TIMER_G12_INST);   // 1count = 1/10MHz
        if( gu32_c_ac_on_old >= c_ac_on_new )
        {
            diff = gu32_c_ac_on_old - c_ac_on_new;
        } else {
            diff = gu32_c_ac_on_old + ~c_ac_on_new;
        }
        gu32_c_ac_on_old = c_ac_on_new;

        if( I_AC_ON_IN == _H_ ) // AC入力
        {
            gu32_c_ac_on_period  = diff;    // ON期間
            if( gu32_c_ac_on_period < AC_TIME_3_5MS ) // ON期間 < 3.5ms?
            {
                if( ++gu16_c_ac_on_flt >= 20 ) // 20パルス連続?
                {
                    if( gu8_f_ac_syundan_1s == 0 )
                    {
                        gu8_f_ac_under_70v = _ON_;      // 70V以下検出
                        gu8_f_ac_syundan_1s = 1;        // 1秒間(瞬断)検出
                        gu32_syundan_timer = gu32_SysTickCount;  // 1ms
                    }
                    gu16_c_ac_on_flt = 20;
                }
            } else {
                gu16_c_ac_on_flt = 0;
                if( gu8_f_ac_syundan_1s != 0 )
                {
                    if( gu8_f_ac_under_70v == _ON_ )
                    {
                        gu8_f_ac_under_70v = _OFF_;

                        // 瞬断カウント+1(AC_FAIL_COUNT)
                        // EEPROM(積算データ)
                        gu8_f_ac_70v_syundan = _ON_;  // 70V瞬断検出 ON
                    }
                }
            }
        } else {
            gu32_c_ac_off_period = diff;   // OFF期間
        }
#if 0
        if( gu8_f_ac_syundan_1s != 0 )
        {
            if( get_sys_difftimer(gu32_syundan_timer) >= TIMER_1000ms ) // 1秒
            {
                gu8_f_ac_syundan_1s = 0;

                gu8_f_ac_under_70v = _OFF_;
                gu16_c_ac_on_flt = 0;
            }
        }
#endif
#endif
#endif

    }
}

/*******************************************************************************
 * Function Name: RTC_IRQHandler()
 * Description  : RTC 割込み
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void RTC_IRQHandler(void)
{
    switch (DL_RTC_getPendingInterrupt(RTC))
    {
        case DL_RTC_IIDX_INTERVAL_TIMER:
            break;
        case DL_RTC_IIDX_PRESCALER1:
            //gs_RTCCalendar = DL_RTC_getCalendarTime(RTC);
            //O_TEST_OUT_TOG;
            gu8_f_rtc_1sec = 1;
            break;
        default:
            break;
    }
}

/*******************************************************************************
 * Function Name: UART0_IRQHandler()
 * Description  : UART 割込み
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void UART0_IRQHandler(void)
{
    uint32_t error = 0;
    uint32_t errorMask = (DL_UART_ERROR_OVERRUN | DL_UART_ERROR_PARITY | DL_UART_ERROR_FRAMING);
    uint8_t tdata;
    uint8_t rdata;

    switch (DL_UART_Main_getPendingInterrupt(UART_0_INST))
    {
        case DL_UART_MAIN_IIDX_RX:
            error = DL_UART_Main_getErrorStatus(UART_0_INST,errorMask);
            if( error == 0 )
            {
                rdata = DL_UART_Main_receiveData(UART_0_INST);

                gu8_uart_main_receivedata[gu8_uart_main_rcv_wpt] = rdata;     // 受信バッファに格納
                gu8_uart_main_rcv_wpt = (gu8_uart_main_rcv_wpt+1) & (UART_RCV_MAIN_NUM-1);

            } else {
                // OverRun/Parity/Framing
                rdata = DL_UART_Main_receiveData(UART_0_INST); // Dummy Read
                switch (error)
                {
                    case DL_UART_ERROR_OVERRUN:
                        gu8_f_nak_sndreq = NAK_OVERRUN;
                	error_log_request(103);
                        break;
                    case DL_UART_ERROR_PARITY:
                        gu8_f_nak_sndreq = NAK_PARITY;
                	error_log_request(119);
                        break;
                    case DL_UART_ERROR_FRAMING:
                        gu8_f_nak_sndreq = NAK_FRAMING;
                	error_log_request(135);
                        break;
                    case (DL_UART_ERROR_OVERRUN | DL_UART_ERROR_PARITY):
                    case (DL_UART_ERROR_PARITY  | DL_UART_ERROR_FRAMING):
                    case (DL_UART_ERROR_OVERRUN | DL_UART_ERROR_FRAMING):
                    case (DL_UART_ERROR_OVERRUN | DL_UART_ERROR_PARITY | DL_UART_ERROR_FRAMING):
                        gu8_f_nak_sndreq = NAK_PARITY;   // 複合要因はParity Errorとしておく
                        break;
                    default:
                        break;
                }
                DL_UART_Main_clearInterruptStatus(UART_0_INST,
                        (DL_UART_INTERRUPT_OVERRUN_ERROR|DL_UART_INTERRUPT_PARITY_ERROR|DL_UART_INTERRUPT_FRAMING_ERROR));
            }
            break;
        case DL_UART_MAIN_IIDX_TX:
            if( gu16_c_tx < gu16_tx_send_req[gu8_d_uart_snd_rpt][1] )
            {
                tdata = gu8_d_uart_sendbuf[gu8_d_uart_snd_rpt][gu16_c_tx++];
                DL_UART_Main_transmitData(UART_0_INST, tdata);
            } else {
                gu16_tx_send_req[gu8_d_uart_snd_rpt][0] = 0;
            }
            break;
#if 0
        case DL_UART_MAIN_IIDX_OVERRUN_ERROR:
            rdata = DL_UART_Main_receiveData(UART_0_INST); // Dummy Read
            __BKPT(0);
            break;
        case DL_UART_MAIN_IIDX_PARITY_ERROR:
            __BKPT(0);
            break;
        case DL_UART_MAIN_IIDX_FRAMING_ERROR:
            __BKPT(0);
            break;
        case DL_UART_MAIN_IIDX_RX_TIMEOUT_ERROR:
            __BKPT(0);
            break;
        case DL_UART_MAIN_IIDX_NOISE_ERROR:
            __BKPT(0);
            break;
#endif
        default:
            break;
    }
}

/*******************************************************************************
 * Function Name: I2C0_IRQHandler()
 * Description  : I2C 割込み (EEPROM)
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void I2C0_IRQHandler(void)
{
    switch (DL_I2C_getPendingInterrupt(I2C_0_INST)) {
        case DL_I2C_IIDX_CONTROLLER_RX_DONE:
            gI2cControllerStatus = I2C_STATUS_RX_COMPLETE;
            break;
        case DL_I2C_IIDX_CONTROLLER_TX_DONE:
            DL_I2C_disableInterrupt(
                I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            gI2cControllerStatus = I2C_STATUS_TX_COMPLETE;
            break;
        case DL_I2C_IIDX_CONTROLLER_RXFIFO_TRIGGER:
            gI2cControllerStatus = I2C_STATUS_RX_INPROGRESS;
            /* Receive all bytes from target */
            while (DL_I2C_isControllerRXFIFOEmpty(I2C_0_INST) != true) {
                if (gRxCount < gRxLen) {
                    gpt_I2C_RxPacket[gRxCount++] =
                        DL_I2C_receiveControllerData(I2C_0_INST);
                } else {
                    /* Ignore and remove from FIFO if the buffer is full */
                    DL_I2C_receiveControllerData(I2C_0_INST);
                    //gI2cControllerStatus = I2C_STATUS_RX_COMPLETE;                //////////////////////
                }
            }
            break;
        case DL_I2C_IIDX_CONTROLLER_TXFIFO_TRIGGER:                    // 今回の場合、FIFO<=1で割込み
            gI2cControllerStatus = I2C_STATUS_TX_INPROGRESS;
            /* Fill TX FIFO with next bytes to send */
            if (gTxCount < gTxLen) {
                gTxCount += DL_I2C_fillControllerTXFIFO(
                    I2C_0_INST, &gTxPacket[gTxCount], gTxLen - gTxCount);
            }
            break;
            /* Not used for this example */
        case DL_I2C_IIDX_CONTROLLER_ARBITRATION_LOST:
        case DL_I2C_IIDX_CONTROLLER_NACK:
            if ((gI2cControllerStatus == I2C_STATUS_RX_STARTED) ||
                (gI2cControllerStatus == I2C_STATUS_TX_STARTED)) {
                /* NACK interrupt if I2C Target is disconnected */
                gI2cControllerStatus = I2C_STATUS_ERROR;
            }
        case DL_I2C_IIDX_CONTROLLER_RXFIFO_FULL:
        case DL_I2C_IIDX_CONTROLLER_TXFIFO_EMPTY:
        case DL_I2C_IIDX_CONTROLLER_START:
        case DL_I2C_IIDX_CONTROLLER_STOP:
        case DL_I2C_IIDX_CONTROLLER_EVENT1_DMA_DONE:
        case DL_I2C_IIDX_CONTROLLER_EVENT2_DMA_DONE:
        default:
            break;
    }
}

/***********************************************
 Function : get_DiffTimer()
 Description : Get Diff Timer Counter
 param[in] : _time  Reference Conter
 return : Diff Counter
 note : None
************************************************/
uint32_t get_sys_difftimer(uint32_t _time)
{
    uint32_t now;
    uint32_t diff;
    
    now = gu32_SysTickCount;  // 1ms

    if( now >= _time )
    {
        diff = now - _time;
    }
    else
    {
        diff = (0xFFFFFFFFL - _time) + now + 1;
    }
    return diff;
}

/*******************************************************************************
* Function Name: PWM_INST_IRQHandler()
* Description  : PWM 割込み
*                TIMA0のゼロ割り込みで周期と位相を更新する
* Arguments    : None
* Return Value : None
*******************************************************************************/
void PWM_INST_IRQHandler(void)
{
    uint32_t mis;

    mis = DL_TimerA_getEnabledInterruptStatus(FAN_PWM_INST, 0xFFFFFFFFL);

    if (mis & DL_TIMER_INTERRUPT_ZERO_EVENT)
    {
        DL_TimerA_clearInterruptStatus(FAN_PWM_INST, DL_TIMER_INTERRUPT_ZERO_EVENT);

        //if (gu8_stop_pwm == 0)
        {
            DL_TimerA_setCaptureCompareValue(FAN_PWM_INST, gu32_PWM_DUTY, DL_TIMERG_CAPTURE_COMPARE_0_INDEX);
            DL_TimerA_setLoadValue(FAN_PWM_INST, gu32_PWM_FREQ);
        }
#if 0
        else
        {
            DL_TimerA_setCounterRepeatMode(FAN_PWM_INST, GPTIMER_CTRCTL_REPEAT_REPEAT_0);    // PWM停止するときの指示？
            gu8_stop_pwm = 0;
        }
#endif
        NVIC_DisableIRQ(FAN_PWM_INST_INT_IRQN);
    }
}
