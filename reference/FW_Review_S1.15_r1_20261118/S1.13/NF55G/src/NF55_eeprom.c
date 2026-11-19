#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"
#include <string.h>

uint8_t eeprom_write_request( uint32_t pos, uint32_t num, uint8_t mode );
uint8_t eeprom_write_check(uint8_t pos);
void write_eeprom( void );
void read_all_eeprom( void );
uint8_t read_eeprom( void );
void eeprom_init_allparam(void);
void eeprom_param_check(void);
void eeprom_all_backup_proc( void );

extern void sleep(void);
extern uint32_t crc32_calc(char *p, uint16_t len);
extern void converter_pwm_stop(void);
volatile uint8_t *gpt_I2C_RxPacket;

extern const uint32_t crc32tab[256];

/******************************************************************************
* Function Name: eeprom_write_request()
* Description  : EEPROM書込み要求
* Arguments    : pos : write position
*              : num : write count
*              : mode : 0: Page write / 1 : 1byte write
* Return Value : None
*******************************************************************************/
uint8_t eeprom_write_request( uint32_t pos, uint32_t num, uint8_t mode )
{
    uint8_t idx;

    eeprom_write_req[eeprom_req_write_idx][0] = pos;
    eeprom_write_req[eeprom_req_write_idx][1] = num;
    eeprom_write_req[eeprom_req_write_idx][2] = mode;
    eeprom_write_req[eeprom_req_write_idx][3] = _OK_;
    eeprom_req_cnt++;
    eeprom_req_busy = 1;   // EEPROM書込処理中
    idx = eeprom_req_write_idx;
    eeprom_req_write_idx = (eeprom_req_write_idx+1) & (I2C_REQ_NUM-1);

    return idx;
}

/*******************************************************************************
 * Function Name: eeprom_write_check()
 * Description  : EEPROM書込みチェック
 * Arguments    : pos = 位置
 * Return Value : 正常:_OK_ / 異常:_ERROR_
 *******************************************************************************/
uint8_t eeprom_write_check(uint8_t pos)
{
    return eeprom_write_req[pos][3];
}

/******************************************************************************
* Function Name: write_eeprom()
* Description  : EEPROM書込み
* Arguments    : None
* Return Value : None
*******************************************************************************/
void write_eeprom( void )
{
#ifndef _NO_EEPROM_
    //static uint8_t  eeprom_write_stage = 0;;
    static uint32_t eeprom_write_wait = 0;;
    static uint16_t len;
    static uint16_t pos;
    static uint16_t num;
    static uint16_t mode;
    static uint16_t offset;
    static uint16_t remain;
    static uint8_t target_Adr;
    uint8_t  *p_eeprom = (uint8_t*)&g_eeprom_data;
    uint8_t  *p_write_eeprom = (uint8_t*)&g_write_eeprom_data;
    uint32_t crc32_end_adrs = 0;
    uint32_t crc32_result = 0;

    switch( gu8_eeprom_write_stage )
    {
        case 0:
            if( eeprom_req_write_idx == eeprom_req_read_idx )
            {
                if( eeprom_req_busy != 0 )
                {
                    gu8_eeprom_write_stage = 10;
                }
                break;
            }
#if 0
            O_TEST_OUT_H;
#endif
            gpt_I2C_RxPacket = gRxPacket;
            pos  = eeprom_write_req[eeprom_req_read_idx][0]; // write position
            num  = eeprom_write_req[eeprom_req_read_idx][1]; // write count
            mode = eeprom_write_req[eeprom_req_read_idx][2]; // mode

            memcpy( &p_write_eeprom[pos], &p_eeprom[pos], num );  // EEPROM書込みデータに転送

            remain = num;
            gI2cControllerStatus = I2C_STATUS_IDLE;
            offset = 0;
            gu8_eeprom_write_stage = 1;
            break;

        /**************/
        /* EEPROM書込 */
        /**************/
        case 1:
            //
            // Fill the FIFO
            //  The FIFO is 8-bytes deep, and this function will return number
            //  of bytes written to FIFO
            target_Adr = I2C_SLAVE_ADR + ((pos+offset) / 256);
            //gTxPacket[0] = (pos % 256) + (offset % 256);
            gTxPacket[0] = (pos+offset) % 256;
            if( mode == 0 )
            {
                if( remain >= 16 )
                {
                    len = 16;
                } else {
                    len = remain;
                }
            } else {
                len = 1;
            }
            memcpy( &gTxPacket[1], &p_write_eeprom[pos+offset], len );
            gTxLen = len + 1;
            gTxCount = DL_I2C_fillControllerTXFIFO(I2C_0_INST, &gTxPacket[0], gTxLen);
            // Enable TXFIFO trigger interrupt if there are more bytes to send
            if (gTxCount < gTxLen) {
                DL_I2C_enableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            } else {
                DL_I2C_disableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            }
            gu8_eeprom_write_stage = 2;
            break;

        case 2:
            if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_IDLE) != 0 )    // IDLE=1でIDLE
            {
                //
                // Send the packet to the controller.
                // This function will send Start + Stop automatically.
                DL_I2C_startControllerTransfer( I2C_0_INST, target_Adr, DL_I2C_CONTROLLER_DIRECTION_TX, gTxLen);

                gI2cControllerStatus = I2C_STATUS_TX_STARTED;
                gu8_eeprom_write_stage = 3;
            }
            break;

        case 3:
            /* Wait until the Controller sends all bytes */
            if( (gI2cControllerStatus == I2C_STATUS_TX_COMPLETE) || (gI2cControllerStatus == I2C_STATUS_ERROR) )     // 送信完了待ち または、ERROR発生
            {
                if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_BUSY_BUS) == 0 )           // BUSY=IDLE  1:BUSY
                {
                    /* Trap if there was an error */
                    if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_ERROR) == 0 )
                    {
                        eeprom_write_wait = 0;
                        gu8_eeprom_write_stage = 4;
                    } else {
                        gu8_eeprom_write_stage = 1;
                    }
                }
            }
            break;

        case 4: // EEPROM書込み待ち(3.5ms以上)
            if( ++eeprom_write_wait >= 4 )   // 4ms
            {
                gu8_eeprom_write_stage = 5;
            }
            break;

        /******************/
        /* EEPROM読み返し */
        /******************/
        case 5:
            //
            // Fill the FIFO
            //  The FIFO is 8-bytes deep, and this function will return number
            //  of bytes written to FIFO
            target_Adr = I2C_SLAVE_ADR + ((pos+offset) / 256);
            //gTxPacket[0] = (pos % 256) + (offset % 256);
            gTxPacket[0] = (pos+offset) % 256;
            gTxLen = 1;
            gTxCount = DL_I2C_fillControllerTXFIFO(I2C_0_INST, &gTxPacket[0], gTxLen);  // 読み出しアドレス指定
            // Enable TXFIFO trigger interrupt if there are more bytes to send
            if (gTxCount < gTxLen) {
                DL_I2C_enableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            } else {
                DL_I2C_disableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            }
            gu8_eeprom_write_stage = 6;
            break;

        case 6:
            if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_IDLE) != 0 )    // IDLE=1でIDLE
            {
                //
                // Send the packet to the controller.
                // This function will send Start + Stop automatically.
                DL_I2C_startControllerTransfer( I2C_0_INST, target_Adr, DL_I2C_CONTROLLER_DIRECTION_TX, gTxLen);

                gI2cControllerStatus = I2C_STATUS_TX_STARTED;
                gu8_eeprom_write_stage = 7;
            }
            break;

        case 7:
            /* Wait until the Controller sends all bytes */
            if( (gI2cControllerStatus == I2C_STATUS_TX_COMPLETE) || (gI2cControllerStatus == I2C_STATUS_ERROR) )     // 送信完了待ち または、ERROR発生
            {
                if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_BUSY_BUS) == 0 )           // BUSY=IDLE  1:BUSY
                {
                    /* Trap if there was an error */
                    if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_ERROR) == 0 )
                    {
                        gu8_eeprom_write_stage = 8;
                    } else {
                        gu8_eeprom_write_stage = 5;
                    }
                }
            }
            break;

        case 8:
            gRxLen   = len;
            gRxCount = 0;
            gI2cControllerStatus = I2C_STATUS_RX_STARTED;
            DL_I2C_startControllerTransfer( I2C_0_INST, target_Adr, DL_I2C_CONTROLLER_DIRECTION_RX, gRxLen);
            gu8_eeprom_write_stage = 9;
            break;

        case 9:
            //if( (gI2cControllerStatus == I2C_STATUS_RX_COMPLETE) || (gRxCount >= gRxLen) )     // 受信完了待ち
            if( gRxCount >= gRxLen )     // 受信完了待ち
            {
                if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_BUSY_BUS) == 0 )           // BUSY=IDLE  1:BUSY
                {
                    if( memcmp( gRxPacket, &p_write_eeprom[pos+offset], len ) != 0 )
                    {
                        // comp err
                        eeprom_write_req[eeprom_req_read_idx][3] = _ERROR_;
                    }
                    if( mode == 0 )
                    {
                        offset += 16;
                    } else {
                        offset++;
                    }
                    remain -= len;
                    if( offset < num )
                    {
                        gu8_eeprom_write_stage = 1;
                    } else {
                        eeprom_req_cnt--;
                        eeprom_req_read_idx = (eeprom_req_read_idx+1) & (I2C_REQ_NUM-1);
                        gu8_eeprom_write_stage = 0;
                    }
                }
            }
            break;

        /********************/
        /* CRC32 EEPROM書込 */
        /********************/
        case 10:

#if 0
            g_write_eeprom_data.crc32 = crc32_calc( (char*)&g_write_eeprom_data, EEPROM_VALID_DATA );
#else
            /* 計算速度向上のアルゴリズム */
            /* 1. 先頭から832バイトをハードウェアクセラレーターを使用して計算する */
            /* 2. 1で求めた値を初期値として残りの2バイトを1バイト単位でCRC32を計算する */

            crc32_end_adrs = (uint32_t)&g_write_eeprom_data + EEPROM_VALID_DATA - 3;
            crc32_result = DL_CRC_calculateMemoryRange32(CRC, 0xFFFFFFFF, (uint32_t *)&g_write_eeprom_data, (const uint32_t *)crc32_end_adrs);

            crc32_result = ((crc32_result >> 8) & 0x00FFFFFF) ^ crc32tab[(crc32_result ^ (g_write_eeprom_data.batt_err)) & 0xFF];
            crc32_result = ((crc32_result >> 8) & 0x00FFFFFF) ^ crc32tab[(crc32_result ^ (g_write_eeprom_data.ps_on_sts)) & 0xFF];
            crc32_result = crc32_result ^ 0xFFFFFFFFL;
            g_write_eeprom_data.crc32 = crc32_result;
#endif
            //
            // Fill the FIFO
            //  The FIFO is 8-bytes deep, and this function will return number
            //  of bytes written to FIFO
            target_Adr = I2C_SLAVE_ADR + (EEPROM_CRC_POS / 256);
            gTxPacket[0] = EEPROM_CRC_POS % 256;
            len = 4;
            memcpy( &gTxPacket[1], &g_write_eeprom_data.crc32, len );
            gTxLen = len + 1;
            gTxCount = DL_I2C_fillControllerTXFIFO(I2C_0_INST, &gTxPacket[0], gTxLen);
            // Enable TXFIFO trigger interrupt if there are more bytes to send
            if (gTxCount < gTxLen) {
                DL_I2C_enableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            } else {
                DL_I2C_disableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            }
            gu8_eeprom_write_stage = 11;
            break;

        case 11:
            if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_IDLE) != 0 )    // IDLE=1でIDLE
            {
                //
                // Send the packet to the controller.
                // This function will send Start + Stop automatically.
                DL_I2C_startControllerTransfer( I2C_0_INST, target_Adr, DL_I2C_CONTROLLER_DIRECTION_TX, gTxLen);

                gI2cControllerStatus = I2C_STATUS_TX_STARTED;
                gu8_eeprom_write_stage = 12;
            }
            break;

        case 12:
            /* Wait until the Controller sends all bytes */
            if( (gI2cControllerStatus == I2C_STATUS_TX_COMPLETE) || (gI2cControllerStatus == I2C_STATUS_ERROR) )     // 送信完了待ち または、ERROR発生
            {
                if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_BUSY_BUS) == 0 )           // BUSY=IDLE  1:BUSY
                {
                    /* Trap if there was an error */
                    if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_ERROR) == 0 )
                    {
                        eeprom_write_wait = 0;
                        gu8_eeprom_write_stage = 13;
                    } else {
                        gu8_eeprom_write_stage = 10;
                    }
                }
            }
            break;

        case 13: // EEPROM書込み待ち(3.5ms以上)
            if( ++eeprom_write_wait >= 4 )   // 4ms
            {
                gu8_eeprom_write_stage = 14;
            }
            break;

        /******************/
        /* EEPROM読み返し */
        /******************/
        case 14:
            //
            // Fill the FIFO
            //  The FIFO is 8-bytes deep, and this function will return number
            //  of bytes written to FIFO
            target_Adr = I2C_SLAVE_ADR + (EEPROM_CRC_POS / 256);
            gTxPacket[0] = EEPROM_CRC_POS % 256;
            gTxLen = 1;
            gTxCount = DL_I2C_fillControllerTXFIFO(I2C_0_INST, &gTxPacket[0], gTxLen);  // 読み出しアドレス指定
            // Enable TXFIFO trigger interrupt if there are more bytes to send
            if (gTxCount < gTxLen) {
                DL_I2C_enableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            } else {
                DL_I2C_disableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            }
            gu8_eeprom_write_stage = 15;
            break;

        case 15:
            if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_IDLE) != 0 )    // IDLE=1でIDLE
            {
                //
                // Send the packet to the controller.
                // This function will send Start + Stop automatically.
                DL_I2C_startControllerTransfer( I2C_0_INST, target_Adr, DL_I2C_CONTROLLER_DIRECTION_TX, gTxLen);

                gI2cControllerStatus = I2C_STATUS_TX_STARTED;
                gu8_eeprom_write_stage = 16;
            }
            break;

        case 16:
            /* Wait until the Controller sends all bytes */
            if( (gI2cControllerStatus == I2C_STATUS_TX_COMPLETE) || (gI2cControllerStatus == I2C_STATUS_ERROR) )     // 送信完了待ち または、ERROR発生
            {
                if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_BUSY_BUS) == 0 )           // BUSY=IDLE  1:BUSY
                {
                    /* Trap if there was an error */
                    if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_ERROR) == 0 )
                    {
                        gu8_eeprom_write_stage = 17;
                    } else {
                        gu8_eeprom_write_stage = 14;
                    }
                }
            }
            break;

        case 17:
            gRxLen   = len;
            gRxCount = 0;
            gI2cControllerStatus = I2C_STATUS_RX_STARTED;
            DL_I2C_startControllerTransfer( I2C_0_INST, target_Adr, DL_I2C_CONTROLLER_DIRECTION_RX, gRxLen);
            gu8_eeprom_write_stage = 18;
            break;

        case 18:
            //if( (gI2cControllerStatus == I2C_STATUS_RX_COMPLETE) || (gRxCount >= gRxLen) )     // 受信完了待ち
            if( gRxCount >= gRxLen )     // 受信完了待ち
            {
                if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_BUSY_BUS) == 0 )           // BUSY=IDLE  1:BUSY
                {
                    if( memcmp( gRxPacket, &g_write_eeprom_data.crc32, len ) != 0 )
                    {
                        // comp err
                        eeprom_write_req[eeprom_req_read_idx][3] = _ERROR_;
                    }
                    if( eeprom_req_cnt == 0 )
                    {
#if 0
                        O_TEST_OUT_L;
#endif
                        eeprom_req_busy = 0;   // EEPROM書込処理完了
                    }
                    gu8_eeprom_write_stage = 0;
                }
            }
            break;

        default:
            break;
    }
#endif // _NO_EEPROM_
}

/******************************************************************************
* Function Name: read_all_eeprom()
* Description  : EEPROM読込み(全データ)
* Arguments    : None
* Return Value : None
*******************************************************************************/
void read_all_eeprom( void )
{
#ifndef _NO_EEPROM_
    uint8_t ret;

    for(;;)
    {
        sleep();             // 1ms Wait

        //WDT_clear();        // WDT Clear

        ret = read_eeprom();     // EEPROM読込み(全データ)

        if( ret != 0 ) break;
    }

    if( g_eeprom_data.pin_code != PIN_CODE )
    {

        eeprom_init_allparam(); // 全EEPROM初期化

        for(;;)
        {
            sleep();             // 1ms Wait

            //WDT_clear();        // WDT Clear

            write_eeprom();     // EEPROM書込み

            if( eeprom_req_busy == 0 ) break;
        }
    }

    g_write_eeprom_data = g_eeprom_data;

    eeprom_param_check(); // 設定値チェック
#else
    eeprom_init_allparam(); // 全EEPROM初期化
#endif
}

/*******************************************************************************
 * Function Name: read_eeprom()
 * Description  : EEPROM データ読出(全データ)
 * Arguments    : None
 * Return Value : ret != 0 完了
 *******************************************************************************/
uint8_t read_eeprom( void )
{
    //static uint8_t eeprom_read_all_stage = 0;
    uint8_t  ret = 0;

    switch( gu8_eeprom_read_all_stage )
    {
        case 0:
            gpt_I2C_RxPacket = (uint8_t*)&g_eeprom_data;
            gI2cControllerStatus = I2C_STATUS_IDLE;
            //
            // Fill the FIFO
            //  The FIFO is 8-bytes deep, and this function will return number
            //  of bytes written to FIFO
            gTxPacket[0] = 0;  // Address = 0
            gTxLen = 1;
            gTxCount = DL_I2C_fillControllerTXFIFO(I2C_0_INST, &gTxPacket[0], gTxLen);
            // Enable TXFIFO trigger interrupt if there are more bytes to send
            if (gTxCount < gTxLen) {
                DL_I2C_enableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            } else {
                DL_I2C_disableInterrupt(
                    I2C_0_INST, DL_I2C_INTERRUPT_CONTROLLER_TXFIFO_TRIGGER);
            }
            gu8_eeprom_read_all_stage = 1;
            break;

        case 1:
            if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_IDLE) != 0 )    // IDLE=1でIDLE
            {
                //
                // Send the packet to the controller.
                // This function will send Start + Stop automatically.
                DL_I2C_startControllerTransfer( I2C_0_INST, I2C_SLAVE_ADR, DL_I2C_CONTROLLER_DIRECTION_TX, gTxLen);

                gI2cControllerStatus = I2C_STATUS_TX_STARTED;
                gu8_eeprom_read_all_stage = 2;
            }
            break;

        case 2:
            /* Wait until the Controller sends all bytes */
            if( (gI2cControllerStatus == I2C_STATUS_TX_COMPLETE) || (gI2cControllerStatus == I2C_STATUS_ERROR) )  // 送信完了待ち または、ERROR発生
            {
                if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_BUSY_BUS) == 0 )           // BUSY=IDLE  1:BUSY
                {
                    /* Trap if there was an error */
                    if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_ERROR) == 0 )
                    {
                        gu8_eeprom_read_all_stage = 3;
                    } else {
                        gu8_eeprom_read_all_stage = 0;
                    }
                }
            }
            break;

        case 3:
            gRxLen   = sizeof(eeprom_data_t);
            gRxCount = 0;
            gI2cControllerStatus = I2C_STATUS_RX_STARTED;
            DL_I2C_startControllerTransfer( I2C_0_INST, I2C_SLAVE_ADR, DL_I2C_CONTROLLER_DIRECTION_RX, gRxLen);
            gu8_eeprom_read_all_stage = 4;
            break;

        case 4:
            //if( (gI2cControllerStatus == I2C_STATUS_RX_COMPLETE) || (gRxCount >= gRxLen) )     // 受信完了待ち
            if( gRxCount >= gRxLen )     // 受信完了待ち
            {
                if( (DL_I2C_getControllerStatus(I2C_0_INST) & DL_I2C_CONTROLLER_STATUS_BUSY_BUS) == 0 )           // BUSY=IDLE  1:BUSY
                {
                    gu8_eeprom_read_all_stage = 0;
                    ret = 1;
                }
            }
            break;

        default:
            gu8_eeprom_read_all_stage = 0;
            break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: eeprom_init_allparam()
 * Description  : EEPROM データ初期化
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void eeprom_init_allparam(void)
{
    uint8_t  ii;

    memset( (void*)&g_eeprom_data, 0, sizeof(g_eeprom_data) );

    g_eeprom_data.set_parameter = SET_PRAMETER_DEF_TBL;  // 初期値

    SE_BURST         = _ENABLE_;  // 有効
    SE_PS_OFF_CHARGE = _ENABLE_;  // 有効

    memset( (void*)&g_eeprom_data.set_serial, '0', sizeof(g_eeprom_data.set_serial) );

    g_eeprom_data.cumulative_data.batt_temp_max = INT8_MIN_VALUE;  // 積算データ バッテリ最高温度
    g_eeprom_data.cumulative_data.batt_temp_min =  INT8_MAX_VALUE;  //            バッテリ最低温度

    for( ii=0; ii<ERROR_LOG_COUNT; ii++ )
    {
        g_eeprom_data.error_log_data[ii].id = 0xFF;   // ERROR LOG ID
    }

    for( ii=0; ii<OPERATE_LOG_COUNT; ii++ )
    {
        g_eeprom_data.operate_log_data[ii].id = 0xFF; // OPERATE LOG ID
    }

    g_eeprom_data.set_clock.time = 0x69560D60L;  // 時刻(2026/1/1 00:00:00)

    g_eeprom_data.dischg_i.point1  = 30.0f;  // 補正1位置 30.0A
    g_eeprom_data.dischg_i.ad1     = 1820;   // 補正1AD値
    g_eeprom_data.dischg_i.point2  = 1.0f;   // 補正2位置 1.0A
    g_eeprom_data.dischg_i.ad2     = 61;     // 補正2位置

    g_eeprom_data.batt_v.point1    = 11.0f;  // 補正1位置 11.0V
    g_eeprom_data.batt_v.ad1       = 3689;   // 補正1AD値
    g_eeprom_data.batt_v.point2    = 4.0f;   // 補正2位置 4.0V
    g_eeprom_data.batt_v.ad2       = 1342;   // 補正2位置

    g_eeprom_data.acdc12v_v.point1 = 11.0f;  // 補正1位置 11.0V
    g_eeprom_data.acdc12v_v.ad1    = 2786;   // 補正1AD値
    g_eeprom_data.acdc12v_v.point2 = 4.0f;   // 補正2位置 4.0V
    g_eeprom_data.acdc12v_v.ad2    = 1013;   // 補正2位置

    g_eeprom_data.batt_chg.point1  = 1.85f;  // 補正1位置 1.85A
    g_eeprom_data.batt_chg.ad1     = 2296;   // 補正1AD値
    g_eeprom_data.batt_chg.point2  = 0.3f;   // 補正2位置 0.3V
    g_eeprom_data.batt_chg.ad2     = 372;    // 補正2位置

    g_eeprom_data._12vout_v.point1 = 11.0f;  // 補正1位置 11.0V
    g_eeprom_data._12vout_v.ad1    = 2786;   // 補正1AD値
    g_eeprom_data._12vout_v.point2 = 4.0f;   // 補正2位置 4.0V
    g_eeprom_data._12vout_v.ad2    = 1013;   // 補正2位置

    g_eeprom_data.crc32 = crc32_calc( (char*)&g_eeprom_data, EEPROM_VALID_DATA );

    g_eeprom_data.pin_code = PIN_CODE; // PIN CODE

    eeprom_write_request( 0, sizeof(g_eeprom_data), 0 );    // EEPROM書込みリクエスト
}

/******************************************************************************
* Function Name: eeprom_param_check()
* Description  : 設定値チェック
* Arguments    : None
* Return Value : None
*******************************************************************************/
void eeprom_param_check(void)
{
    uint32_t crc32;

    crc32 = crc32_calc( (char*)&g_eeprom_data, EEPROM_VALID_DATA );
    if( crc32 != g_eeprom_data.crc32 )
    {
        gu8_f_eeprom_check_error = 1;
        //eeprom_init_allparam(); // 全EEPROM初期化

        DL_WWDT_disablePower(WWDT0_INST);

        O_12V_EN_H ;
        O_BATT_EN_L ;
        O_DISCHG12V_EN_L;
        converter_pwm_stop();
#if 1
        while(1){

        }
#endif
    }
}

/******************************************************************************
* Function Name: eeprom_all_backup_proc()
* Description  : EEPROM 全バックアップ処理
* Arguments    : None
* Return Value : None
*******************************************************************************/
void eeprom_all_backup_proc( void )
{
    //static uint8_t stage = 0;
    static uint8_t pos;


    switch( gu8_eeprom_all_backup )
    {
        case 0:
            if( pi_ps_on.trg == _TRG_OFF_)   // PS_ON ON->OFF
            {
                //O_TEST_OUT_H;
                pos = eeprom_write_request( EEPROM_BATT_POS, 112, 0 );     // EEPROM書込みリクエスト
                gu8_eeprom_all_backup = 1;
            }

            if(gu8_f_ac_on_trg == _TRG_OFF_){                          //AC断

                	pos =eeprom_write_request( EEPROM_SC_POS , sizeof(set_clock_t), 0 );
                	pos = eeprom_write_request( EEPROM_SEKISAN_POS , 16, 0 );
                	gu8_eeprom_all_backup = 1;
            	}
    	
    		if(gu8_f_before_shutdown!=1)
    		{
    	    	if(gu32_c_eeprom_timer==0)
    			{                                   //3分間隔
                   	 gu32_c_eeprom_timer=TIMER_3min;
                     pos =eeprom_write_request( EEPROM_BATT_POS, 112, 0 );
                     gu8_eeprom_all_backup = 1;
                }else{

                    gu32_c_eeprom_timer--;
                }


    		}
           	 break;
    	
        case 1:
            if( eeprom_req_busy == 0 )
            {
                if( eeprom_write_check(pos) == _OK_ )  // 書込み正常
                {
                    //*response = CMD_NORMAL;   // CMD_NORMAL;
                } else {
                    //*response = HWE_ERR_RES;  // HW破損エラー(HWE)レスポンス
                }

                gu8_eeprom_all_backup = 0;
            }
            break;

        default:
            break;
    }
}

