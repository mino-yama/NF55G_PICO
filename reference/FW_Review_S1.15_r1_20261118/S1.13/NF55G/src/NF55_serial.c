#include <stdio.h>
#include <string.h>
#include "ti_msp_dl_config.h"
#include "NF55_define.h"
#include "NF55_global.h"
extern void error_log_request( uint8_t almid );
void serial_rx_proc(void);
void serial_tx_proc(void);
//
void rx_main_proc();
void rx_proc(void);
uint8_t recv_proc(uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num);

uint8_t cmd_recv_check(uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num);
uint8_t cmd_sp_check(uint8_t *d_recvbuf, uint8_t num);
uint8_t cmd_sc_check(uint8_t *d_recvbuf, uint8_t num);
uint8_t cmd_sl_check(uint8_t *d_recvbuf, uint8_t num);

uint8_t cmd_proc( uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num, uint8_t *response );
uint8_t cmd_sp_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response );
uint8_t cmd_rp_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response );
uint8_t cmd_se_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response );
uint8_t cmd_sc_proc(uint8_t *d_recvbuf, uint8_t num);
uint8_t cmd_ss_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response );
uint8_t cmd_sl_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response );
uint8_t cmd_bc_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response );
uint8_t cmd_cd_proc(uint8_t *d_recvbuf, uint8_t num);
uint8_t cmd_cl_proc(uint8_t *d_recvbuf, uint8_t num);
uint8_t cmd_ad_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response );

uint16_t set_normal_response(uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num);
uint8_t ack_response(void);
uint8_t nak_response(void);
uint16_t set_error_response(uint8_t *d_recvbuf, uint8_t err_kind);
void set_clock_data(uint8_t *d_sndbuf);
void set_realtime_data(uint8_t *d_sndbuf);
void set_parameter_data(uint8_t *d_sndbuf);
void set_status_info(uint8_t *d_sndbuf);
void set_life_diag_data(uint8_t *d_sndbuf);
void set_life_diag_data_response(uint8_t *d_sndbuf);
void set_life_calc_data(uint8_t *d_sndbuf);
void set_cumulative_data(uint8_t *d_sndbuf);
void set_off_period_data(uint8_t *d_sndbuf);
void set_manufacturing_data(uint8_t *d_sndbuf);
void set_err_log_data(uint8_t *d_sndbuf,uint8_t d_sndbuf2);
void set_ope_log_data(uint8_t *d_sndbuf,uint8_t d_sndbuf2);
uint32_t proc_cmd_fd(uint8_t *addr_buf);
uint8_t aft_ack_rcv_proc(uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num);
//
void tx_proc(void);
void update_wait(void);
uint8_t uart_send_req(uint8_t *sendbuf, uint16_t num);
uint8_t sendbuf_pos_get(void);
uint8_t send_complete_check(uint8_t pos);
uint16_t calc_bcc(uint8_t *buf, uint16_t len);

uint8_t bit_to_aschex(uint8_t value);
void int_to_aschex(int32_t value, uint8_t *asc_data, uint8_t n);
int32_t aschex_to_int(uint8_t *asc_data, uint8_t n);
void float_to_aschex(float value, uint8_t *asc_data, uint8_t n);
float aschex_to_float(uint8_t *asc_data, uint8_t n);

void event_proc(void);
static void byte_to_hex_ascii(uint8_t val, uint8_t *out);

extern uint32_t get_sys_difftimer(uint32_t _time);
extern void make_set_parameter_value(void);
extern uint8_t eeprom_write_request( uint32_t pos, uint32_t num, uint8_t mode );
extern uint8_t eeprom_write_check(uint8_t pos);
extern void set_info_evt_errlog( uint8_t flag, uint8_t status );

//#define SND_RES_TIMER   TIMER_200ms
#define RES_WAIT_TIMER  TIMER_200ms

extern void jumpBoot(void);

/*******************************************************************************
 * Function Name: serial_rx_proc()
 * Description  : UART処理(受信)
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void serial_rx_proc(void)
{
    if(gu8_f_before_shutdown!=1)
	{

    	rx_main_proc(); // RX受信処理

    	rx_proc(); // RX処理

   // update_wait();
    }
}

/*******************************************************************************
 * Function Name: serial_tx_proc()
 * Description  : UART処理(送信)
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void serial_tx_proc(void)
{
	if(gu8_f_before_shutdown!=1)
	{
		event_proc();  // イベント送信

    	tx_proc(); // TX処理
	}

}

/*******************************************************************************
 * Function Name: rx_main_proc()
 * Description  : UART RX受信処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void rx_main_proc(void)
{
    static uint8_t  c_rx = 0;
    static uint16_t data_count = 0;
    static uint16_t data_len = 0;
    static uint8_t  cmd_id_no;
    uint8_t ii;
    uint16_t bcc_rcv,bcc_cal;
    uint16_t cmd_id;
    uint8_t rdata;

    while( gu8_uart_main_rcv_wpt != gu8_uart_main_rcv_rpt )
    {
        rdata = gu8_uart_main_receivedata[gu8_uart_main_rcv_rpt];
        gu8_uart_main_rcv_rpt = (gu8_uart_main_rcv_rpt+1) & (UART_RCV_MAIN_NUM-1);

        if( rdata == STX )   // STX受信
        {
            gu8_rcv_main_stage = 0;
        }

        switch( gu8_rcv_main_stage )
        {
            case 0:
                if( rdata == STX )   // STX受信
                {
                    c_rx = 0;
                    gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][c_rx++] = rdata;
                    gu8_f_ack_nak_rcv = 0;
                    gu32_rcv_all_timer = 0;
                    gu8_rcv_main_stage = 1;
                    break;
                }
                else if( rdata == ACK )   // ACK受信
                {
                    gu8_f_ack_nak_rcv = ACK;
                    gu8_f_evt_ack_nak_rcv = ACK;
                    break;
                }
                else if( rdata == NAK )   // NAK受信 (装置からのNAKにNAK REASON CODEは付与されない)
                {
                    gu8_f_ack_nak_rcv = NAK;
                    gu8_f_evt_ack_nak_rcv = NAK;
                    //gu8_rcv_main_stage = 5;
                }
                break;

            case 1:
                gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][c_rx++] = rdata;
                if( c_rx == 3 )    // 3byteめ受信?
                {
                    cmd_id = (gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][2]<<8) + gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][1];  // CMD ID
                    cmd_id_no = 0xff;
                    for(ii=0; ii<VAILD_CMD_ID_NUM; ii++ )
                    {
                        if( memcmp( &cmd_id, &CMD_TBL[ii].cmd[0], 2 ) == 0 ) // CMD ID一致?
                        {
                            cmd_id_no = ii;                        // CMD ID No.
                            data_len = CMD_TBL[ii].data_length;
                            break;
                        }
                    }
                    if( cmd_id_no != 0xff )
                    {
                        data_count = 0;
                        gu8_rcv_main_stage = 2;
                    } else {
                        // CMD ID未定義
                        gu8_rcv_main_stage = 4;
                    }
                }
                break;

            case 2:
                gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][c_rx++] = rdata;
                data_count++;
                if( (data_len+1) == data_count ) // ETXを正常に受信(ETX前までがDATA)
                {
                    if( rdata == ETX )   // ETX
                    {
                        gu8_rcv_main_stage = 3;
                    } else {
                        // 指定位置にETXが来ていない
                        gu8_f_nak_sndreq = NAK_ETX;
                        gu8_rcv_main_stage = 0;
                    	error_log_request(200);
                    }
                }
                break;

            case 3:
                gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][c_rx++] = rdata;
                data_count++;
                if( (data_count >= (data_len+3)) || (c_rx >= RECVBUF_SIZE) ) // BCCまで受信
                {
                    bcc_rcv = (gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][c_rx-2] <<8) + gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][c_rx-1];
                    bcc_cal = calc_bcc( &gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][0], c_rx-2 );
                    if( bcc_rcv == bcc_cal )
                    {
                        gu8_f_cmd_id_no[gu8_d_uart_rcv_wpt] = cmd_id_no;
                        gu8_d_uart_rcv_count[gu8_d_uart_rcv_wpt] = c_rx;
                        gu8_d_uart_rcv_num++;
                        gu8_d_uart_rcv_wpt = (gu8_d_uart_rcv_wpt+1) & (UART_RCV_NUM-1);
                        gu8_rcv_main_stage = 0;
                    } else {
                        // BCCエラー
                        gu8_f_nak_sndreq = NAK_BCC;
                        gu8_rcv_main_stage = 0;
                    	 error_log_request(202);
                    }
                }
                break;

            case 4: // CMD ID未定義
                gu8_d_uart_recvbuf[gu8_d_uart_rcv_wpt][c_rx++] = rdata;
                if( (rdata == ETX) || (c_rx >= RECVBUF_SIZE) ) // ETXを受信するまで
                {
                    gu8_f_cmd_id_no[gu8_d_uart_rcv_wpt] = cmd_id_no;
                    gu8_d_uart_rcv_count[gu8_d_uart_rcv_wpt] = c_rx;
                    gu8_d_uart_rcv_num++;
                    gu8_d_uart_rcv_wpt = (gu8_d_uart_rcv_wpt+1) & (UART_RCV_NUM-1);
                    gu8_rcv_main_stage = 0;
                }
                break;

            //case 5:
            //    gu8_f_ack_nak_rcv = rdata;    // NAK REASON CODE
            //    gu8_rcv_main_stage = 0;
            //    break;

            default:
                gu8_rcv_main_stage = 0;
                break;
        }
    }
    // 受信監視
    if ((gu8_rcv_main_stage != 0)
            && (++gu32_rcv_all_timer > TIMER_100ms)) // STXを受信し100ms間に全て受信しない?
    {
        gu8_f_nak_sndreq = NAK_TIMEOUT;
        gu8_rcv_main_stage = 0;
    	error_log_request(166);
    }
}

/*******************************************************************************
 * Function Name: rx_proc()
 * Description  : UART RX処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void rx_proc(void)
{
    static uint8_t num;
    //static uint8_t rcv_stage = 0;
    static uint8_t cmd_id_no = 0;
    uint8_t ii, rpt;
    uint8_t sts;

    switch (gu8_rx_proc_stage)
    {
    case 0:
        if (gu8_d_uart_rcv_rpt != gu8_d_uart_rcv_wpt)
        {
            gu8_f_command_proc = 1;
            rpt = gu8_d_uart_rcv_num - 1;
            for (ii = 0; ii < rpt; ii++)
            {
                gu8_d_uart_rcv_rpt = (gu8_d_uart_rcv_rpt + 1)
                        & (UART_RCV_NUM - 1);  // 最新のコマンドを処理する
            }
            gu8_d_uart_rcv_num = 0;

            num = gu8_d_uart_rcv_count[gu8_d_uart_rcv_rpt];   // 受信数
            memcpy(gu8_d_recvbuf, &gu8_d_uart_recvbuf[gu8_d_uart_rcv_rpt][0],
                   num); // 受信データ
            cmd_id_no = gu8_f_cmd_id_no[gu8_d_uart_rcv_rpt];  // CMD ID
            gu8_f_multi_command = 0;
            gu8_rx_proc_stage = 1;
        }
        break;
    case 1:
        sts = recv_proc(cmd_id_no, gu8_d_recvbuf, num);   // 受信データ処理
        if (sts != _CONTINUE_)
        {
            gu8_f_command_proc = 0;
            gu8_d_uart_rcv_rpt = (gu8_d_uart_rcv_rpt + 1) & (UART_RCV_NUM - 1);
            gu8_rx_proc_stage = 0;
        }
        break;
    default:
        gu8_rx_proc_stage = 0;
        break;
    }

    if (gu8_f_nak_sndreq != 0)
    {
        sts = nak_response();   // NAK応答
        if (sts != _CONTINUE_)
        {
            gu8_f_nak_sndreq = 0;
        }
    }
}

/*******************************************************************************
 * Function Name: recv_proc()
 * Description  : 受信データ処理
 * Arguments    :
 * Return Value : ==0 : 処理中
 *                ==1 : 処理完了
 *******************************************************************************/
uint8_t recv_proc(uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num)
{
    uint8_t ret = _CONTINUE_;
    uint8_t sts = 0,ii;
    static uint16_t snd_num;
    static uint32_t c_timer;
    static uint8_t c_retry;
    //static uint8_t f_response = CMD_NORMAL;

    switch (gu8_proc_stage)
    {
    case 0:
        gu8_f_response = cmd_recv_check(cmd_id_no, d_recvbuf, num); // 実行条件チェック
        gu8_proc_stage = 1;
        break;

    case 1:
        if (gu8_d_uart_rcv_num != 0)   // ACK応答の前にコマンドを受信した
        {
            ret = _DONE_;
            break;
        }
        sts = ack_response();   // ACK応答
        if (sts == _DONE_)
        {
            if (gu8_f_response == CMD_NORMAL)
            {
                gu8_proc_stage = 2;
            }
            else
            {
                c_retry = 0;
                gu8_proc_stage = 4;  // 応答へ
            }
        }
        else if (sts == _DONE2_)
        {
            gu8_proc_stage = 0;
            ret = _DONE_;
        }
        break;

    case 2:
        // 多重コマンドチェック
        if (gu8_d_uart_rcv_num == 0)
        {
            gu8_proc_stage = 3;
        }
        else
        {
            for (ii = 0; ii < gu8_d_uart_rcv_num; ii++)
            {
                gu8_d_uart_rcv_rpt = (gu8_d_uart_rcv_rpt + 1)
                        & (UART_RCV_NUM - 1);  // 受信したコマンドを無しにする
            }
            gu8_d_uart_rcv_num = 0;
            gu8_f_response = MCM_ERR_RES; // 多重コマンド受信(MCM)レスポンス
            gu8_f_multi_command = 1;
            gu8_proc_stage = 7;
        }
        break;

    case 3:
        if( cmd_proc( cmd_id_no, d_recvbuf, num, &gu8_f_response ) == _DONE_ ) // 実処理
        {
            c_retry = 0;
            gu8_proc_stage = 4;
        }
        break;

    case 4:
        if (c_retry == 0)
        {
            if (gu8_f_response == CMD_NORMAL)
            {
                snd_num = set_normal_response(cmd_id_no, d_recvbuf, num); // 正常レスポンス
            }
            else
            {
                snd_num = set_error_response(d_recvbuf, gu8_f_response); // エラーレスポンス
            }
        }
        gu8_pos = uart_send_req(gu8_d_sendbuf, snd_num);
        gu8_f_ack_nak_rcv = 0;     // 応答データクリア
        //c_timer = SND_RES_TIMER; // 200ms
        gu8_proc_stage = 5;
        break;

    case 5:
        //if( --c_timer != 0 )
        //{
         if (send_complete_check(gu8_pos) == 0)
        {
            if(cmd_id_no == CMD_ID_FU)
            {
                 if (gu8_f_multi_command == 0)
                    {
                        if (gu8_f_response == CMD_NORMAL)
                        {
                        ret=aft_ack_rcv_proc(cmd_id_no, d_recvbuf, num);
                        return ret;

                        }else{

                             gu8_proc_stage = 0;
                             ret = _DONE_;
                        }
                     }else{
                            gu8_f_response = CMD_NORMAL;
                            gu8_f_multi_command = 0;
                            gu8_proc_stage = 3;    // 多重コマンド処理後、継続
                          }
           }else{
              c_timer = RES_WAIT_TIMER; // 200ms
              //gu8_f_ack_nak_rcv = 0;    // 応答データクリア
              gu8_proc_stage = 6;

                }
        }
        break;

    case 6:
        if (--c_timer != 0)
        {
            if (gu8_f_ack_nak_rcv == ACK) // ACK受信
            {
                if (gu8_f_multi_command == 0)
                {
                    if (gu8_f_response == CMD_NORMAL)
                    {
                        aft_ack_rcv_proc(cmd_id_no, d_recvbuf, num);
                    }
                    gu8_proc_stage = 0;
                    ret = _DONE_;
                }
                else
                {
                    gu8_f_response = CMD_NORMAL;
                    gu8_f_multi_command = 0;
                    gu8_proc_stage = 3;    // 多重コマンド処理後、継続
                }
            }
            else if (gu8_f_ack_nak_rcv == NAK) // NAK受信
            {
                if (++c_retry <= RETRY_NUM)
                {
                    gu8_proc_stage = 4;    // 再送
                	error_log_request(204);
                }
                else
                {
                    gu8_proc_stage = 0;
                	error_log_request(207);
                    ret = _DONE_;
                }
            }
        }
        else
        {                       // タイムオーバー
            if (++c_retry <= RETRY_NUM)
            {
                gu8_proc_stage = 4;    // 再送
            	error_log_request(172);
            }
            else
            {
                gu8_proc_stage = 0;
            	error_log_request(207);
                ret = _DONE_;
            }
        }
        break;

    case 7: // 多重コマンド用のACK
        sts = ack_response();   // ACK応答
        if (sts == _DONE_)
        {
            c_retry = 0;
            gu8_proc_stage = 4;  // 多重コマンド応答
        }
        else if (sts == _DONE2_)
        {
            gu8_proc_stage = 0;
            ret = _DONE_;
        }
        break;

    default:
        gu8_proc_stage = 0;
        ret = _DONE_;
        break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_recv_check()
 * Description  : 受信データチェック処理
 * Arguments    :
 * Return Value : ==0 : 正常
 *                !=0 : 異常(エラーレスポンス番号)
 *******************************************************************************/
uint8_t cmd_recv_check(uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num)
{
    uint8_t ii, data;
    uint8_t ret = CMD_NORMAL;
    int32_t no;
    switch (cmd_id_no)
    {
    case CMD_ID_SP:    // 各種閾値設定用 (SET PARAMETER)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        ret = cmd_sp_check(d_recvbuf, num);
        break;

    case CMD_ID_RP:    // 各種閾値初期値設定 (RESET PARAMETER)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_SE:    // ERP 設定 (SET ERP)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        if ((d_recvbuf[3] == '0') || (d_recvbuf[3] == '1'))    // BURST設定=無効/有効?
        {
            if ((d_recvbuf[4] == '0') || (d_recvbuf[4] == '1')) // PS_OFF_CHARGE設定=無効/有効?
            {
                break;
            }
        }
        ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
        break;

    case CMD_ID_SC:    // 時刻設定 (SET CLOCK)
        ret = cmd_sc_check(d_recvbuf, num);
        break;

    case CMD_ID_SS:    // 製造情報設定 (SET SERIAL)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        for (ii = 0; ii < 50; ii++)
        {
            data = d_recvbuf[3 + ii];
            if (!((0x20 <= data) && (data <= 0x7E)))  // ASCII?
            {
                ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
                break;
            }
        }
        break;

    case CMD_ID_SL:    // 寿命計算結果記憶 (SET LIFE)
        ret = cmd_sl_check( d_recvbuf, num );
        break;

    case CMD_ID_BC:    // 寿命診断実行 (BATT CHECK)
        if ((gu8_f_backup_active == _ON_) || (gu8_alm_type_batt_err != _OFF_) || (gu8_f_charging_active == _ON_) || (gu8_f_charge_inhibited == _ON_)) // バックアップ中 または バッテリ異常あり または 充電中 または 充電禁止中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_CN:    // 強制充電 (CHARGE ON)
        if ((gu8_f_backup_active == _ON_) || (gu8_alm_type_batt_err != _OFF_) || ((gu8_f_main_chg_now == _ON_) && (d_recvbuf[3] != '0')) || (gu8_f_charge_inhibited == _ON_)) // バックアップ中 または バッテリ異常あり または 主充電中(1の場合) または 充電禁止中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        if ((d_recvbuf[3] == '0') || (d_recvbuf[3] == '1'))    // BURST設定=無効/有効?
        {
            break;
        }
        ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
        break;

    case CMD_ID_CF:    // 強制充電停止 (CHARGE OFF)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        if ((d_recvbuf[3] == '0') || (d_recvbuf[3] == '1'))    // BURST設定=無効/有効?
        {
            break;
        }
        ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
        break;

    case CMD_ID_BE:    // バックアップ許可 (BACKUP ENABLE)
        if ((gu8_f_ps_on == _OFF_) || (gu8_f_ac_link_restarting != 0) )// PS OFF または リスタート中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_BF:    // バックアップ停止 (BACKUP OFF)
        if ((gu8_f_ps_on == _OFF_) || (gu8_f_ac_link_restarting != 0) )// PS OFF または リスタート中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_OR:    // 復電リスタート制御 (OUTPUT RESTART)
        if ((gu8_f_ps_on == _OFF_) || (gu8_f_ac_link_restarting != 0) )// PS OFF または リスタート中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_D0:    // 全データ取得 (GET DATA0)
        break;

    case CMD_ID_D1:    // 状態情報 (GET DATA1)
        break;

    case CMD_ID_D2:    // 起動時寿命計算用 (GET DATA2)
        if ((gu8_f_ps_on == _OFF_) || (gu8_f_ac_link_restarting != 0) )// PS OFF または リスタート中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        if (gu8_f_cmd_sc_recv == 0) // 時刻設定(SET CLOCK)未受信?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_D3:    // 通常寿命計算用 (GET DATA3)
        break;

    case CMD_ID_D4:    // 保守情報取得 (GET DATA4)
        break;

    case CMD_ID_D5:    // REV/号機・設定確認 (GET DATA5)
        break;

    case CMD_ID_EL:    // エラーログ取得 (ERROR LOG)
    	 {
        uint8_t  bak[2];
        bak[0] = d_recvbuf[3];
        bak[1] = d_recvbuf[4];

        no = aschex_to_int( &d_recvbuf[3], 2);
               if( (no!=1) && (no!=9) && (no!=17) && (no!=25) )
               {
                   ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
               }

               d_recvbuf[3] = bak[0];
               d_recvbuf[4] = bak[1];
        break;
    	 }

    case CMD_ID_OL:    // ON/OFF ログ取得 (OPERATE LOG)
        {
        uint8_t  bak[2];
        bak[0] = d_recvbuf[3];
        bak[1] = d_recvbuf[4];
        no = aschex_to_int( &d_recvbuf[3], 2);
        if( (no!=1) && (no!=9) && (no!=17) && (no!=25) && (no!=33) && (no!=41) && (no!=49) && (no!=57) )
            {
               ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
            }

        d_recvbuf[3] = bak[0];
        d_recvbuf[4] = bak[1];
        break;
        }

    case CMD_ID_CD:    // データクリア (CLEAR DATA)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        if ((d_recvbuf[3] == '0') || (d_recvbuf[3] == '1') || (d_recvbuf[3] == '2')) // 0/1/2
        {
            break;
        }
        ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
        break;

    case CMD_ID_CL:    // ログ全クリア (CLEAR LOG)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_FU:    // FW アップデート (FW UPDATE)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_FD:    // FW データ取得 (FW DATA)
        if (gu8_f_backup_active == _ON_) // バックアップ中?
        {
            ret = SQE_ERR_RES;   // シーケンスエラー(SQE)レスポンス
            break;
        }
        break;

    case CMD_ID_AD:    // バッテリ電圧補正機能(ADJUST)
        break;

    case CMD_ID_AR:    // バッテリ電圧補正機能_読み出し用 (ADJUST READ)
        break;

    case CMD_ID_FF:    // 未定義
    default:
        ret = CMD_ERR_RES;
        break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_sp_check()
 * Description  : 各種閾値設定用 (SET PARAMETER) パラメータチェック
 * Arguments    : none
 * Return Value : ret
 *******************************************************************************/
uint8_t cmd_sp_check(uint8_t *d_recvbuf, uint8_t num)
{
    uint8_t ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
    uint32_t data;

    gs_set_parameter_tmp = g_eeprom_data.set_parameter;    // 現状を設定

    do {
        if( memcmp(&d_recvbuf[3], FFFF_TBL, 1) != 0 )
        {
           data = aschex_to_int( &d_recvbuf[3], 1);
            if( data > 1 ) break;
            gs_set_parameter_tmp.ps_on_backup = data;      // 停電時のバックアップ動作設定
        }

        if( memcmp(&d_recvbuf[4], FFFF_TBL, 1) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[4], 1);
            if( data > 1 ) break;
            gs_set_parameter_tmp.ac_link = data;           // 停電後の復電検出におけるリスタート動作設定
        }

        if( memcmp(&d_recvbuf[5], FFFF_TBL, 1) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[5], 1);
            if( data > 3 ) break;
            gs_set_parameter_tmp.auto_charge = data;       // 自動充電方式の設定
        }

        if( memcmp(&d_recvbuf[6], FFFF_TBL, 1) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[6], 1);
            if( data > 1 ) break;
            gs_set_parameter_tmp.event = data;             // イベント送信設定
        }

        if( memcmp(&d_recvbuf[7], FFFF_TBL, 1) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[7], 1);
            if( data > 14 ) break;
            gs_set_parameter_tmp.max_backup_time = data;   // 最大バックアップ時間設定(分)
        }

        if( memcmp(&d_recvbuf[8], FFFF_TBL, 2) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[8], 2);
            if( data > UINT8_MAX_VALUE_UNDER ) break;
            gs_set_parameter_tmp.min_backup_time = data;   // 最小バックアップ時間設定(秒)
        }

        if( memcmp(&d_recvbuf[10], FFFF_TBL, 2) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[10], 2);
            if( data > UINT8_MAX_VALUE_UNDER ) break;
            gs_set_parameter_tmp.restart_time = data;      // AC_LINKが有効およびOUTPUT RESTARTコマンドを受信時のリスタート実行時に出力をオフする時間
        }

        if( memcmp(&d_recvbuf[12], FFFF_TBL, 2) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[12], 2);
            if( data > 100 ) break;
            gs_set_parameter_tmp.batt_low_thf = data;      // バッテリ充電量低下(BATT_LOW)閾値
        }

        if( memcmp(&d_recvbuf[14], FFFF_TBL, 4) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[14], 4);
            if( data > UINT16_MAX_VALUE_UNDER ) break;
            gs_set_parameter_tmp.batt_cap_mah = data;      // バッテリ容量(mAh単位)
        }

        if( memcmp(&d_recvbuf[18], FFFF_TBL, 2) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[18], 2);
            if( data > UINT8_MAX_VALUE_UNDER ) break;
            gs_set_parameter_tmp.batt_cap_wh = data;       // バッテリ容量(Wh単位)
        }

        if( memcmp(&d_recvbuf[20], FFFF_TBL, 3) != 0 )
        {
            data = aschex_to_int( &d_recvbuf[20], 3);
            if( data > UINT12_MAX_VALUE_UNDER ) break;
            gs_set_parameter_tmp.chg_ir_thd = data;        // 充電DCIRの判定閾値
        }

        ret = CMD_NORMAL;
    } while(0);

    if( ret == CMD_NORMAL )
    {
        ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
        do {
            if( memcmp(&d_recvbuf[23], FFFF_TBL, 2) != 0 )
            {
                data = aschex_to_int( &d_recvbuf[23], 2);
                if( (data == 0) || ((50 <= data) && (data <= 70)) )
                {
                    gs_set_parameter_tmp.batt_wng_thd = data;      // バッテリ充電抑止温度閾値
                } else {
                    break;
                }
            }

            if( memcmp(&d_recvbuf[25], FFFF_TBL, 2) != 0 )
            {
                data = aschex_to_int( &d_recvbuf[25], 2);
                if( (data == 0) || ((70 <= data) && (data <= 95)) )
                {
                    gs_set_parameter_tmp.batt_alm_thd = data;      // バッテリ温度異常閾値
                } else {
                    break;
                }
            }

            if( memcmp(&d_recvbuf[27], FFFF_TBL, 2) != 0 )
            {
                data = aschex_to_int( &d_recvbuf[27], 2);
                if( (data == 0) || ((60 <= data) && (data <= 95)) || (data == UINT8_MAX_VALUE_UNDER) )
                {
                    gs_set_parameter_tmp.adu_temp_thd = data;      // AC/DC部の温度警告(ADU_TEMP_WNG)の検出閾値
                } else {
                    break;
                }
            }

            if( memcmp(&d_recvbuf[29], FFFF_TBL, 2) != 0 )
            {
                data = aschex_to_int( &d_recvbuf[29], 2);
                if( (data == 0) || ((60 <= data) && (data <= 95)) || (data == UINT8_MAX_VALUE_UNDER) )
                {
                    gs_set_parameter_tmp.bbu_temp_thd = data;      // BACKUP部の温度警告(BBU_TEMP_WNG)の検出閾値
                } else {
                    break;
                }
            }

            if( memcmp(&d_recvbuf[31], FFFF_TBL, 4) != 0 )
            {
                data = aschex_to_int( &d_recvbuf[31], 4);
                if( (data <= 1230) || (data == UINT16_MAX_VALUE_UNDER) )
                {
                    gs_set_parameter_tmp.fan_wng_thd = data;      // FANの回転停止警告(FAN_WMG)の検出閾値
                } else {
                    break;
                }
            }

            ret = CMD_NORMAL;
        } while(0);
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_sc_check()
 * Description  : 時刻設定(SET CLOCK) パラメータチェック
 * Arguments    : none
 * Return Value : ret
 *******************************************************************************/
uint8_t cmd_sc_check(uint8_t *d_recvbuf, uint8_t num)
{
    uint8_t ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
    uint32_t data;

    do
    {
        data = aschex_to_int(&d_recvbuf[3], 2);
        if (data > 99)
            break;                       // 年(00-99)
        gu8_d_clock_data[0] = (uint8_t) data;

        data = aschex_to_int(&d_recvbuf[5], 2);
        if ((data == 0) || (data > 12))
            break;          // 月(01-12)
        gu8_d_clock_data[1] = (uint8_t) data;

        uint8_t wk = 0;
        if (gu8_d_clock_data[1] == 2)     // 2月?
        {
            if ((gu8_d_clock_data[0] % 4) == 0) //  うるう年?(2000-2099)
            {
                wk = 1;  // 29日
            }
        }
        data = aschex_to_int(&d_recvbuf[7], 2);
        if ((data == 0) || (data > (MONTH_END_TBL[gu8_d_clock_data[1]] + wk)))
            break; // 日(01-31)
        gu8_d_clock_data[2] = (uint8_t) data;

        data = aschex_to_int(&d_recvbuf[9], 2);
        if (data > 23)
            break;                       // 時(00-23)
        gu8_d_clock_data[3] = (uint8_t) data;

        data = aschex_to_int(&d_recvbuf[11], 2);
        if (data > 59)
            break;                       // 分(00-59)
        gu8_d_clock_data[4] = (uint8_t) data;

        data = aschex_to_int(&d_recvbuf[13], 2);
        if (data > 59)
            break;                       // 秒(00-59)
        gu8_d_clock_data[5] = (uint8_t) data;

        ret = CMD_NORMAL;
    }
    while (0);

    return ret;
}

/*******************************************************************************
 * Function Name: cmd_sl_check()
 * Description  : 寿命計算結果記憶 (SET LIFE) パラメータチェック
 * Arguments    : none
 * Return Value : ret
 *******************************************************************************/
uint8_t cmd_sl_check(uint8_t *d_recvbuf, uint8_t num)
{
    uint8_t ret = PME_ERR_RES; // パラメータエラー(PME)レスポンス
    uint32_t data;

    do
    {
        data = aschex_to_int( &d_recvbuf[3], 3);
        if( data > UINT12_MAX_VALUE ) break;
        SL_BATT_DEG = data;           // 寿命計算結果
        ret = CMD_NORMAL;
    }
    while (0);

    return ret;
}

/*******************************************************************************
 * Function Name: cmd_proc()
 * Description  : 受信データ処理
 * Arguments    :
 * Return Value : 継続=_CONTINUE_ / 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_proc( uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num, uint8_t *response )
{
    uint8_t ret = _CONTINUE_;

    switch (cmd_id_no)
    {
    case CMD_ID_SP:    // 各種閾値設定用 (SET PARAMETER)
        ret = cmd_sp_proc( d_recvbuf, num, response );
        break;

    case CMD_ID_RP:    // 各種閾値初期値設定 (RESET PARAMETER)
        ret = cmd_rp_proc( d_recvbuf, num, response );
        break;

    case CMD_ID_SE:    // ERP 設定 (SET ERP)
        ret = cmd_se_proc( d_recvbuf, num, response );
        break;

    case CMD_ID_SC:    // 時刻設定 (SET CLOCK)
        ret = cmd_sc_proc(d_recvbuf, num);
        break;

    case CMD_ID_SS:    // 製造情報設定 (SET SERIAL)
        ret = cmd_ss_proc( d_recvbuf, num, response );
        break;

    case CMD_ID_SL:    // 寿命計算結果記憶 (SET LIFE)
        ret = cmd_sl_proc( d_recvbuf, num, response );
        break;

    case CMD_ID_BC:    // 寿命診断実行 (BATT CHECK)
        ret = cmd_bc_proc( d_recvbuf, num, response );
        break;

    case CMD_ID_CN:    // 強制充電 (CHARGE ON)
        if (gu8_f_charge_on_cmd == 0)
        {
            gu8_f_charge_on_cmd = 1;
        }

        if (d_recvbuf[3] == '0')
        {
            gu8_f_charge_on = 0;
            set_info_evt_errlog(FLAG_CMD_CHARGE_ON,_RESET_);
            if( gu8_f_susp_cha == TEMP_SUPPRES_1 ) // 温度抑止中?
            {
                gu8_f_susp_cha = TEMP_SUPPRES_3;  // 温度抑止復帰(CHARGE ONコマンドオフ)
            }
        }
        else if (d_recvbuf[3] == '1')
        {
            gu8_f_charge_on = 1;
            set_info_evt_errlog(FLAG_CMD_CHARGE_ON,_SET_);
        }

        ret = _DONE_;
        break;

    case CMD_ID_CF:    // 強制充電停止 (CHARGE OFF)
        if (gu8_f_charge_off_cmd == 0)
        {
            gu8_f_charge_off_cmd = 1;
        }
        if (d_recvbuf[3] == '0')
        {
            gu8_f_charge_off = 0;
            set_info_evt_errlog(FLAG_CMD_CHARGE_OFF,_RESET_);

        }
        else if (d_recvbuf[3] == '1')
        {
            gu8_f_charge_off = 1;
            set_info_evt_errlog(FLAG_CMD_CHARGE_OFF,_SET_);
            set_info_evt_errlog(FLAG_CMD_CHARGE_ON,_RESET_);
        }
        if( gu8_f_susp_cha == TEMP_SUPPRES_1 ) // 温度抑止中?
        {
            gu8_f_susp_cha = TEMP_SUPPRES_2;  // 温度抑止復帰(CHARGE OFFコマンド受信)
        }
        ret = _DONE_;
        break;

    case CMD_ID_BE:    // バックアップ許可 (BACKUP ENABLE)
        gu8_backup_enable_cmd = 1;
        set_info_evt_errlog( FLAG_BACKUP_READY, _SET_);   // 状態情報 BACKUP_READY セット

        ret = _DONE_;
        break;

    case CMD_ID_BF:    // バックアップ停止 (BACKUP OFF)
        gu8_backup_off_cmd = 1;
        set_info_evt_errlog( FLAG_BACKUP_READY, _RESET_);   // 状態情報 BACKUP_READY リセット

        ret = _DONE_;
        break;

    case CMD_ID_OR:    // 復電リスタート制御 (OUTPUT RESTART)
        gu8_f_output_restart = 1;    // OUTPUT RESTART受信
        set_info_evt_errlog( FLAG_RESTART_READY, _SET_ );  // RESTART READY Set
        ret = _DONE_;
        break;

    case CMD_ID_D0:    // 全データ取得 (GET DATA0)
        ret = _DONE_;
        break;

    case CMD_ID_D1:    // 状態情報 (GET DATA1)
        gu8_f_cmd_d1_recv = 1;
        gu32_c_cmd_sc_evt_delay = 0;  // イベントDelayタイマ クリア
        ret = _DONE_;
        break;

    case CMD_ID_D2:    // 起動時寿命計算用 (GET DATA2)
        ret = _DONE_;
        break;

    case CMD_ID_D3:    // 通常寿命計算用 (GET DATA3)
        ret = _DONE_;
        break;

    case CMD_ID_D4:    // 保守情報取得 (GET DATA4)
        ret = _DONE_;
        break;

    case CMD_ID_D5:    // REV/号機・設定確認 (GET DATA5)
        ret = _DONE_;
        break;

    case CMD_ID_EL:    // エラーログ取得 (ERROR LOG)
        ret = _DONE_;
        break;

    case CMD_ID_OL:    // ON/OFF ログ取得 (OPERATE LOG)
        ret = _DONE_;
        break;

    case CMD_ID_CD:    // データクリア (CLEAR DATA)
        ret = cmd_cd_proc( d_recvbuf, num );
        break;

    case CMD_ID_CL:    // ログ全クリア (CLEAR LOG)
        ret = cmd_cl_proc( d_recvbuf, num );
        break;

    case CMD_ID_FU:    // FW アップデート (FW UPDATE)
        eeprom_write_request( EEPROM_BATT_POS, 112, 0 );
        ret = _DONE_;
        break;

    case CMD_ID_FD:    // FW データ取得 (FW DATA)
        ret = _DONE_;
        break;

    case CMD_ID_AD:
        ret = cmd_ad_proc( d_recvbuf, num, response );
        break;

    case CMD_ID_AR:
        ret = _DONE_;
        break;

    case CMD_ID_FF:    // 未定義
    default:
        ret = _DONE_;
        break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_sp_proc()
 * Description  : 各種閾値設定用 (SET PARAMETER)
 * Arguments    :
 * Return Value : 継続=_CONTINUE_ / 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_sp_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response )
{
    //static uint8_t stage = 0;
    static uint8_t pos;
    uint8_t ret = _CONTINUE_;

    switch( gu8_cmd_sp_proc_stage )
    {
        case 0:
            g_eeprom_data.set_parameter = gs_set_parameter_tmp;

            if( SP_AUTO_CHARGE == _DISABLE_ )
            {
                if( gu8_f_susp_cha == TEMP_SUPPRES_1 ) // 温度抑止中?
                {
                    gu8_f_susp_cha = TEMP_SUPPRES_4;  // 温度抑止復帰(自動充電無効設定)
                }
            }

            make_set_parameter_value();                            // SET PARAMETERデータ作成
            pos = eeprom_write_request( EEPROM_SP_POS, sizeof(set_parameter_t), 0 ); // EEPROM書込みリクエスト
            gu8_cmd_sp_proc_stage = 1;
            break;
        case 1:
            if( eeprom_req_busy == 0 )
            {
                if( eeprom_write_check(pos) == _OK_ )  // 書込み正常
                {
                    *response = CMD_NORMAL;   // CMD_NORMAL;

                } else {
                    *response = HWE_ERR_RES;  // HW破損エラー(HWE)レスポンス
                }
                ret = _DONE_;
                gu8_cmd_sp_proc_stage = 0;
            }
            break;
        default:
            gu8_cmd_sp_proc_stage = 0;
            break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_rp_proc()
 * Description  : 各種閾値初期値設定 (RESET PARAMETER)
 * Arguments    :
 * Return Value : 継続=_CONTINUE_ / 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_rp_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response )
{
    //static uint8_t stage = 0;
    static uint8_t pos;
    uint8_t ret = _CONTINUE_;

    switch( gu8_cmd_rp_proc_stage )
    {
        case 0:
            g_eeprom_data.set_parameter = SET_PRAMETER_DEF_TBL;  // 初期値
            make_set_parameter_value();                            // SET PARAMETERデータ作成
            pos = eeprom_write_request( EEPROM_SP_POS, sizeof(set_parameter_t), 0 ); // EEPROM書込みリクエスト
            gu8_cmd_rp_proc_stage = 1;
            break;
        case 1:
            if( eeprom_req_busy == 0 )
            {
                if( eeprom_write_check(pos) == _OK_ )  // 書込み正常
                {
                    *response = CMD_NORMAL;   // CMD_NORMAL;
                } else {
                    *response = HWE_ERR_RES;  // HW破損エラー(HWE)レスポンス
                }
                ret = _DONE_;
                gu8_cmd_rp_proc_stage = 0;
            }
            break;
        default:
            gu8_cmd_rp_proc_stage = 0;
            break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_se_proc()
 * Description  : ERP 設定 (SET ERP)
 * Arguments    :
 * Return Value : 継続=_CONTINUE_ / 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_se_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response )
{
    //static uint8_t stage = 0;
    static uint8_t pos;
    uint8_t ret = _CONTINUE_;

    switch( gu8_cmd_se_proc_stage )
    {
        case 0:
            SE_BURST = aschex_to_int(&d_recvbuf[3], 1);
            if ( SE_BURST == _ENABLE_)
            {
                set_info_evt_errlog( FLAG_BURST, _SET_);       // 状態情報 BURST有効
            }
            else
            {
                set_info_evt_errlog( FLAG_BURST, _RESET_);     // 状態情報 BURST無効
            }
            SE_PS_OFF_CHARGE = aschex_to_int(&d_recvbuf[4], 1);
            if ( SE_PS_OFF_CHARGE == _ENABLE_)
            {
                set_info_evt_errlog( FLAG_PS_OFF_CHARGE, _SET_);  // 状態情報 PS_OFF_CHARGE有効
            }
            else
            {
                set_info_evt_errlog( FLAG_PS_OFF_CHARGE, _RESET_); // 状態情報 PS_OFF_CHARGE無効
            }
            pos = eeprom_write_request( EEPROM_SE_POS, sizeof(set_erp_t), 0 ); // EEPROM書込みリクエスト
            gu8_cmd_se_proc_stage = 1;
            break;
        case 1:
            if( eeprom_req_busy == 0 )
            {
                if( eeprom_write_check(pos) == _OK_ )  // 書込み正常
                {
                    *response = CMD_NORMAL;   // CMD_NORMAL;
                } else {
                    *response = HWE_ERR_RES;  // HW破損エラー(HWE)レスポンス
                }
                ret = _DONE_;
                gu8_cmd_se_proc_stage = 0;
            }
            break;
        default:
            gu8_cmd_se_proc_stage = 0;
            break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_sc_proc()
 * Description  : 時刻設定 (SET CLOCK)
 * Arguments    :
 * Return Value : none
 *******************************************************************************/
uint8_t cmd_sc_proc(uint8_t *d_recvbuf, uint8_t num)
{
    uint8_t ret = _DONE_;
    struct tm tm_data;

    DL_RTC_Calendar RTCCalendarConfig = { .seconds = gu8_d_clock_data[5], /* Seconds */
                                          .minutes = gu8_d_clock_data[4], /* Minute  */
                                          .hours = gu8_d_clock_data[3], /* Hour    */
                                          .dayOfWeek = 0, /* Day of week = 0 (Sunday) */
                                          .dayOfMonth = gu8_d_clock_data[2], /* Day of month */
                                          .month = gu8_d_clock_data[1], /* Month   */
                                          .year = gu8_d_clock_data[0] + 2000, /* Year */
    };
    /* Set RTC Calendar */
    DL_RTC_initCalendar(RTC, RTCCalendarConfig, DL_RTC_FORMAT_BINARY);

    //if( gu8_f_cmd_sc_recv == 0 )
    {
        gu32_c_cmd_sc_evt_delay = TIMER_2000ms;  // イベントDelayタイマ 2秒
    }

    // OFF期間データ用
    tm_data.tm_year  = RTCCalendarConfig.year-1900;  /* 1900年からの年 */
    tm_data.tm_mon   = RTCCalendarConfig.month-1;     /* 月(0～11) */
    tm_data.tm_mday  = RTCCalendarConfig.dayOfMonth; /* 日(1～31) */
    tm_data.tm_hour  = RTCCalendarConfig.hours;      /* 時(0～23) */
    tm_data.tm_min   = RTCCalendarConfig.minutes;     /* 分(0～59) */
    tm_data.tm_sec   = RTCCalendarConfig.seconds;     /* 秒(0～59) */
    tm_data.tm_isdst = 0;  /* 夏時間フラグ(採用:>0,不採用:0,不明:<0)  */

    //time_t構造体に変換
    gt_otd_ac_on_time = mktime(&tm_data);

    gu8_f_cmd_sc_recv = 1;      // 時刻設定 (SET CLOCK)受信フラグON

    return ret;
}

/*******************************************************************************
 * Function Name: cmd_ss_proc()
 * Description  : 製造情報設定 (SET SERIAL)
 * Arguments    :
 * Return Value : 継続=_CONTINUE_ / 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_ss_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response )
{
    //static uint8_t stage = 0;
    static uint8_t pos;
    uint8_t ret = _CONTINUE_;

    switch( gu8_cmd_ss_proc_stage )
    {
        case 0:
            if (memcmp(&d_recvbuf[9], FFFF_TBL, 4) != 0)
            {
                memcpy(&SS_UNIT_REV, &d_recvbuf[9], 4); // ユニットレビジョン
            }
            if (memcmp(&d_recvbuf[13], FFFF_TBL, 4) != 0)
            {
                memcpy(&SS_UNIT_LOT, &d_recvbuf[13], 4); // ユニット製造ロット
            }
            if (memcmp(&d_recvbuf[17], FFFFFF_TBL, 6) != 0)
            {
                memcpy(&SS_UNIT_SERIAL, &d_recvbuf[17], 6); // ユニット製造号機
            }
            pos = eeprom_write_request( EEPROM_SS_POS, sizeof(set_serial_t), 0 ); // EEPROM書込みリクエスト
            gu8_cmd_ss_proc_stage = 1;
            break;
        case 1:
            if( eeprom_req_busy == 0 )
            {
                if( eeprom_write_check(pos) == _OK_ )  // 書込み正常
                {
                    *response = CMD_NORMAL;   // CMD_NORMAL;
                } else {
                    *response = HWE_ERR_RES;  // HW破損エラー(HWE)レスポンス
                }
                ret = _DONE_;
                gu8_cmd_ss_proc_stage = 0;
            }
            break;
        default:
            gu8_cmd_ss_proc_stage = 0;
            break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_sl_proc()
 * Description  : 寿命計算結果記憶 (SET LIFE)
 * Arguments    :
 * Return Value : 継続=_CONTINUE_ / 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_sl_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response )
{
    //static uint8_t stage = 0;
    static uint8_t pos;
    uint8_t ret = _CONTINUE_;

    switch( gu8_cmd_sl_proc_stage )
    {
        case 0:
            //SL_BATT_DEG = aschex_to_int(&d_recvbuf[3], 3);// 寿命計算結果
            gs_life_calc_data.batt_deg = SL_BATT_DEG; // 寿命計算データ バッテリ劣化度
            gu8_f_sl_cmd_rcv_sek = 1;                   // 積算データ:バッテリ劣化度　記録用フラグ

            pos = eeprom_write_request( EEPROM_SL_POS, sizeof(set_life_t), 0 ); // EEPROM書込みリクエスト
            gu8_cmd_sl_proc_stage = 1;
            break;
        case 1:
            if( eeprom_req_busy == 0 )
            {
                if( eeprom_write_check(pos) == _OK_ )  // 書込み正常
                {
                    *response = CMD_NORMAL;   // CMD_NORMAL;
                    gu8_f_otd_batt_deg_set = _ON_;    // バッテリ劣化度_更新
                } else {
                    *response = HWE_ERR_RES;  // HW破損エラー(HWE)レスポンス
                }
                ret = _DONE_;
                gu8_cmd_sl_proc_stage = 0;
            }
            break;
        default:
            gu8_cmd_sl_proc_stage = 0;
            break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_bc_proc()
 * Description  : 寿命診断実行 (BATT CHECK)
 * Arguments    :
 * Return Value : 継続=_CONTINUE_ / 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_bc_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response )
{
    //static uint8_t stage = 0;
    uint8_t ret = _CONTINUE_;

    switch( gu8_cmd_bc_proc_stage )
    {


        case 0:    // DCIRリクエスト送信
            gu8_f_dcir_request = 1;    // タイムアウト時に落とす必要ありそう
            gu8_cmd_bc_proc_stage = 1;
            break;

        case 1:    // DCIR完了待ち
            if( gu8_f_dcir_complete == 1 )
            {
                gu8_f_dcir_complete = 0;
                gu8_f_dcir_request = 0;

                *response = CMD_NORMAL;
                ret = _DONE_;

                gu8_cmd_bc_proc_stage = 0;
            }
            break;

        default:
            break;
    }

    if (d_recvbuf[3] == '0')
    {
        set_info_evt_errlog(FLAG_BATT_CHECK,_RESET_);
    }else if(d_recvbuf[3] == '1'){

        set_info_evt_errlog(FLAG_BATT_CHECK,_SET_);
    }
    return ret;
}

/*******************************************************************************
 * Function Name: cmd_dc_proc()
 * Description  : データクリア (CLEAR DATA)
 * Arguments    :
 * Return Value : 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_cd_proc(uint8_t *d_recvbuf, uint8_t num)
{
    /*** コマンド確認 ***/
    switch( d_recvbuf[3] )
    {
        case '0':
            gu8_f_power_category_clear = 1;
            gu8_f_batt_cate_clear = 1;
            break;

        case '1':
            gu8_f_power_category_clear = 1;
            break;

        case '2':
            gu8_f_batt_cate_clear = 1;
            break;

        default:
            break;
    }

    /*** 各カテゴリ処理 ***/
    if( gu8_f_power_category_clear == 1 )    // 電源カテゴリデータクリア
    {
        gu8_f_power_category_clear = 0;

        g_eeprom_data.cumulative_data.total_adu_hour = 0;        // 電源稼働時間
        g_eeprom_data.cumulative_data.ac_fail_count = 0;         // 瞬断回数(70V以下)
        g_eeprom_data.cumulative_data.ac_log_count = 0;          // 瞬断回数(90V以下)
        g_eeprom_data.cumulative_data.total_backup_count = 0;    // バックアップ回数

        g_eeprom_data.cumulative_data.total_adu_hour_sub = 0;    // 電源稼働時間(サブ)

        gu32_c_adu_action_time = 0;                           // 電源稼働時間タイマー(1h)

        // OFF期間データ　電源系
        g_eeprom_data.off_period_data.ac_off_hour = 0;
    }
    if( gu8_f_batt_cate_clear == 1 )    // バッテリカテゴリデータクリア
    {
        gu8_f_batt_cate_clear = 0;

        g_eeprom_data.cumulative_data.batt_deg = 0;                  // バッテリ劣化度
        g_eeprom_data.cumulative_data.total_batt_hour = 0;           // バッテリ接続時間
        g_eeprom_data.cumulative_data.batt_discharge_count = 0;      // バッテリ総放電回数
        g_eeprom_data.cumulative_data.batt_charge_count = 0;         // バッテリ総充電回数
        g_eeprom_data.cumulative_data.batt_ttl_discharge = 0;        // バッテリ総放電量
        g_eeprom_data.cumulative_data.batt_ttl_charge = 0;           // バッテリ総充電量
        g_eeprom_data.cumulative_data.total_batt_temp = 0;           // バッテリ積算温度
        g_eeprom_data.cumulative_data.batt_temp_ave = 0;             // バッテリ平均温度
        g_eeprom_data.cumulative_data.batt_temp_max = 0;             // バッテリ最高温度
        g_eeprom_data.cumulative_data.batt_temp_min = INT8_MAX_VALUE;  // バッテリ最低温度

        g_eeprom_data.cumulative_data.total_batt_hour_sub = 0;       // バッテリ接続時間(サブ)
        g_eeprom_data.cumulative_data.batt_temp_sample_count = 0;    // バッテリ温度平均算出用サンプル数

        gu32_c_bat_connect_time = 0;         // バッテリ接続時間タイマー(1h)
        gu32_c_bat_temp_ave_sek = 0;         // バッテリ積算温度/平均温度タイマー(1h)
        gu16_c_bat_temp_calc = 0;            // バッテリ温度平均算出用タイマー(1m)
        gu16_bat_temp_1h_sum = 0;            // バッテリ温度算出用合計値(※最大で、1minごと合計60データとして変数型を想定)
        gu8_c_bat_temp_1h_sum_sample = 0;    // バッテリ温度算出用合計値_サンプル数


        // OFF期間データ　バッテリ系
        g_eeprom_data.off_period_data.ps_off_hour = 0;
        g_eeprom_data.off_period_data.ave_off_temp = 0;
        g_eeprom_data.off_period_data.off_charge_hour = 0;
        g_eeprom_data.off_period_data.ave_charge_temp = 0;
        g_eeprom_data.off_period_data.off_charge = 0;
        g_eeprom_data.off_period_data.ac_off_hour_sub = 0;
        g_eeprom_data.off_period_data.ps_off_hour_sub = 0;
        g_eeprom_data.off_period_data.off_charge_hour_sub = 0;
        g_eeprom_data.off_period_data.batt_deg=0;

        gf_otd_chg_soc_total =0;
        gi16_otd_ps_off_bat_temp_ave = 0;
        gi16_otd_chg_bat_temp_ave = 0;
        gu8_f_otd_chg_soc_calc_fin = 0;
        gf_otd_chg_soc_now = 0.0;
        gu8_f_otd_batt_deg_set = 0;
        gu16_c_otd_ps_off_bat_temp_ave = 0;
        gu16_c_otd_chg_bat_temp_ave = 0;

    }



    /*** 共通処理 ***/
    // 寿命診断データ
    gs_life_diag_data.batt_check_mode = 0;    // バッテリ測定モード
    gs_life_diag_data.batt_voltage1 = 0;      // バッテリ測定電圧1
    gs_life_diag_data.batt_voltage2 = 0;      // バッテリ測定電圧2
    gs_life_diag_data.batt_current1 = 0;      // バッテリ測定電流1
    gs_life_diag_data.batt_current2 = 0;      // バッテリ測定電流2
    gs_life_diag_data.batt_ir_temp = 0;       // バッテリ測定温度
    gs_life_diag_data.batt_ir_soc_mah = 0;    // バッテリ測定SOC(mAh)
    gs_life_diag_data.batt_ir = 0;            // バッテリのDCIR

    set_info_evt_errlog( FLAG_CHARGE_OK, _RESET_ );    // 満充電(充電完了)イベント リセット
    gu8_f_cd_cmd_rcv = 1;    // CDコマンド受信フラグ(バッテリ異常解除通知用)

    gu8_f_charge_ok_clear = 1;    // CHARGE_OK クリアコマンド(充電開始用)

    return _DONE_;
}

/*******************************************************************************
 * Function Name: cmd_cl_proc()
 * Description  : データクリア (CLEAR DATA)
 * Arguments    :
 * Return Value : 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_cl_proc(uint8_t *d_recvbuf, uint8_t num)
{
    uint8_t  ii;

    memset(gu8_b_err_log, 0, sizeof(gu8_b_err_log));    // エラーログ多重書き込み防止フラグのクリア
    g_eeprom_data.error_log_index.error_log_count=0x0;
    g_eeprom_data.error_log_index.error_log_writepointer=0x0;
    for( ii=0; ii<ERROR_LOG_COUNT; ii++ )    // 各ログIDを0xFFに変更
    {
        g_eeprom_data.error_log_data[ii].year = 0x0;
        g_eeprom_data.error_log_data[ii].month = 0x0;
        g_eeprom_data.error_log_data[ii].day = 0x0;
        g_eeprom_data.error_log_data[ii].hour = 0x0;
        g_eeprom_data.error_log_data[ii].id = 0xFF;   // ERROR LOG ID
    }
    eeprom_write_request( EEPROM_ERR_IDX_POS , sizeof(error_log_index_t), 0 );
    eeprom_write_request( EEPROM_ERR_DATA_POS , sizeof(error_log_data_t)*ERROR_LOG_COUNT, 0 );

    g_eeprom_data.operate_log_index.operate_log_count=0x0;
    g_eeprom_data.operate_log_index.operate_log_writepointer=0x0;

    for( ii=0; ii<OPERATE_LOG_COUNT; ii++ )
    {
        g_eeprom_data.operate_log_data[ii].year = 0x0;
        g_eeprom_data.operate_log_data[ii].month = 0x0;
        g_eeprom_data.operate_log_data[ii].day = 0x0;
        g_eeprom_data.operate_log_data[ii].hour = 0x0;
        g_eeprom_data.operate_log_data[ii].id = 0xFF; // OPERATE LOG ID
    }
    eeprom_write_request( EEPROM_OPE_IDX_POS , sizeof(operate_log_index_t), 0 );
    eeprom_write_request( EEPROM_OPE_DATA_POS , sizeof(operate_log_data_t)*OPERATE_LOG_COUNT, 0 );

    return _DONE_;
}

/*******************************************************************************
 * Function Name: cmd_ad_proc()
 * Description  : バッテリ電圧補正機能
 * Arguments    :
 * Return Value : 完了=_DONE_
 *******************************************************************************/
uint8_t cmd_ad_proc(uint8_t *d_recvbuf, uint8_t num, uint8_t *response )
{
    //static uint8_t stage = 0;
    static uint8_t pos;
    uint8_t ret = _CONTINUE_;

    switch( gu8_cmd_ad_proc_stage )
    {
        case 0:
            gu8_cmd_ad_type = aschex_to_int( &d_recvbuf[3], 1 );
            gu8_cmd_ad_position = aschex_to_int( &d_recvbuf[4], 1 );
            gf_cmd_ad_val = aschex_to_float(&d_recvbuf[5], 8);

            switch(gu8_cmd_ad_type)    // 補正対象種類により保存先を変更
            {
                case 1:    // dischg_i
                    if( gf_cmd_ad_val > 67.5 )    //上側範囲処理
                    {
                        gf_cmd_ad_val = 67.5;
                    }
                    else if( gf_cmd_ad_val < 0.0 )    // 下側範囲処理
                    {
                        gf_cmd_ad_val = 0.0;
                    }

                    if( gu8_cmd_ad_position == 1 ){
                        g_eeprom_data.dischg_i.point1 = gf_cmd_ad_val;
                        g_eeprom_data.dischg_i.ad1 = gu16_ADC1_Sens[0];
                    }
                    else if( gu8_cmd_ad_position == 2 ){
                        g_eeprom_data.dischg_i.point2 = gf_cmd_ad_val;
                        g_eeprom_data.dischg_i.ad2 = gu16_ADC1_Sens[0];
                    }
                    gu16_cmd_ad_set_ad_val = gu16_ADC1_Sens[0];    // レスポンス用

                    pos = eeprom_write_request( EEPROM_DISCHG_I_POS, sizeof(correct_t), 0 ); // EEPROM書込みリクエスト
                    break;

                case 2:    // batt_v
                    if( gf_cmd_ad_val > 12.21 )    //上側範囲処理
                    {
                        gf_cmd_ad_val = 12.21;
                    }
                    else if( gf_cmd_ad_val < 0.0 )    // 下側範囲処理
                    {
                        gf_cmd_ad_val = 0.0;
                    }

                    if( gu8_cmd_ad_position == 1 ){
                        g_eeprom_data.batt_v.point1 = gf_cmd_ad_val;
                        g_eeprom_data.batt_v.ad1 = gu16_ADC1_Sens[1];
                    }
                    else if( gu8_cmd_ad_position == 2 ){
                        g_eeprom_data.batt_v.point2 = gf_cmd_ad_val;
                        g_eeprom_data.batt_v.ad2 = gu16_ADC1_Sens[1];
                    }
                    gu16_cmd_ad_set_ad_val = gu16_ADC1_Sens[1];    // レスポンス用

                    pos = eeprom_write_request( EEPROM_BATT_V_POS, sizeof(correct_t), 0 ); // EEPROM書込みリクエスト
                    break;

                case 3:    // acdc12v_v
                    if( gf_cmd_ad_val > 16.17 )    //上側範囲処理
                    {
                        gf_cmd_ad_val = 16.17;
                    }
                    else if( gf_cmd_ad_val < 0.0 )    // 下側範囲処理
                    {
                        gf_cmd_ad_val = 0.0;
                    }

                    if( gu8_cmd_ad_position == 1 ){
                        g_eeprom_data.acdc12v_v.point1 = gf_cmd_ad_val;
                        g_eeprom_data.acdc12v_v.ad1 = gu16_ADC1_Sens[2];
                    }
                    else if( gu8_cmd_ad_position == 2 ){
                        g_eeprom_data.acdc12v_v.point2 = gf_cmd_ad_val;
                        g_eeprom_data.acdc12v_v.ad2 = gu16_ADC1_Sens[2];
                    }
                    gu16_cmd_ad_set_ad_val = gu16_ADC1_Sens[2];    // レスポンス用

                    pos = eeprom_write_request( EEPROM_ACDC12V_V_POS, sizeof(correct_t), 0 ); // EEPROM書込みリクエスト
                    break;

                case 4:    // batt_chg
                    if( gf_cmd_ad_val > 3.3 )    //上側範囲処理
                    {
                        gf_cmd_ad_val = 3.3;
                    }
                    else if( gf_cmd_ad_val < 0.0 )    // 下側範囲処理
                    {
                        gf_cmd_ad_val = 0.0;
                    }

                    if( gu8_cmd_ad_position == 1 ){
                        g_eeprom_data.batt_chg.point1 = gf_cmd_ad_val;
                        g_eeprom_data.batt_chg.ad1 = gu16_ADC0_Sens[6];
                    }
                    else if( gu8_cmd_ad_position == 2 ){
                        g_eeprom_data.batt_chg.point2 = gf_cmd_ad_val;
                        g_eeprom_data.batt_chg.ad2 = gu16_ADC0_Sens[6];
                    }
                    gu16_cmd_ad_set_ad_val = gu16_ADC0_Sens[6];    // レスポンス用

                    pos = eeprom_write_request( EEPROM_BATT_CHG_POS, sizeof(correct_t), 0 ); // EEPROM書込みリクエスト
                    break;

                case 5:    // _12vout_v
                    if( gf_cmd_ad_val > 16.17 )    //上側範囲処理
                    {
                        gf_cmd_ad_val = 16.17;
                    }
                    else if( gf_cmd_ad_val < 0.0 )    // 下側範囲処理
                    {
                        gf_cmd_ad_val = 0.0;
                    }

                    if( gu8_cmd_ad_position == 1 ){
                        g_eeprom_data._12vout_v.point1 = gf_cmd_ad_val;
                        g_eeprom_data._12vout_v.ad1 = gu16_ADC0_Sens[4];
                    }
                    else if( gu8_cmd_ad_position == 2 ){
                        g_eeprom_data._12vout_v.point2 = gf_cmd_ad_val;
                        g_eeprom_data._12vout_v.ad2 = gu16_ADC0_Sens[4];
                    }
                    gu16_cmd_ad_set_ad_val = gu16_ADC0_Sens[4];    // レスポンス用

                    pos = eeprom_write_request( EEPROM_12VOUT_V_POS, sizeof(correct_t), 0 ); // EEPROM書込みリクエスト
                    break;

                default:
                    break;
            }

            gu8_cmd_ad_proc_stage = 1;
            break;

        case 1:
            if( eeprom_req_busy == 0 )
            {
                if( eeprom_write_check(pos) == _OK_ )  // 書込み正常
                {
                    *response = CMD_NORMAL;   // CMD_NORMAL;

                    switch(gu8_cmd_ad_type)    // 計算値(V,I)を算出
                    {
                        case 1:
                            if( (g_eeprom_data.dischg_i.ad1 - g_eeprom_data.dischg_i.ad2) > 0 )
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data.dischg_i.point1 - g_eeprom_data.dischg_i.point2) /
                                                             (g_eeprom_data.dischg_i.ad1 - g_eeprom_data.dischg_i.ad2))*1000;     // DISCHG_I AD(1)値係数(mA単位)
                            }
                            else
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data.dischg_i.point1 - g_eeprom_data.dischg_i.point2) / 1 )*1000;     // DISCHG_I AD(1)値係数(mA単位)
                            }
                            break;

                        case 2:
                            if( (g_eeprom_data.batt_v.ad1 - g_eeprom_data.batt_v.ad2) > 0 )
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data.batt_v.point1 - g_eeprom_data.batt_v.point2) /
                                                             (g_eeprom_data.batt_v.ad1 - g_eeprom_data.batt_v.ad2))*1000;         // BATT_V AD(1)値係数(mV単位)
                            }
                            else
                            {

                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data.batt_v.point1 - g_eeprom_data.batt_v.point2) / 1)*1000;         // BATT_V AD(1)値係数(mV単位)

                            }
                            break;

                        case 3:
                            if( (g_eeprom_data.acdc12v_v.ad1 - g_eeprom_data.acdc12v_v.ad2) > 0 )
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data.acdc12v_v.point1 - g_eeprom_data.acdc12v_v.point2) /
                                                             (g_eeprom_data.acdc12v_v.ad1 - g_eeprom_data.acdc12v_v.ad2))*1000;   // AC/DC12V_V AD(1)値係数(mV単位)
                            }
                            else
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data.acdc12v_v.point1 - g_eeprom_data.acdc12v_v.point2) / 1)*1000;         // BATT_V AD(1)値係数(mV単位)
                            }
                            break;

                        case 4:
                            if( (g_eeprom_data.batt_chg.ad1 - g_eeprom_data.batt_chg.ad2) > 0 )
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data.batt_chg.point1 - g_eeprom_data.batt_chg.point2) /
                                                             (g_eeprom_data.batt_chg.ad1 - g_eeprom_data.batt_chg.ad2))*1000;     // BATT_CHG AD(1)値係数(mA単位)
                            }
                            else
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data.batt_chg.point1 - g_eeprom_data.batt_chg.point2) / 1)*1000;     // BATT_CHG AD(1)値係数(mA単位)
                            }
                            break;

                        case 5:
                            if( (g_eeprom_data._12vout_v.ad1 - g_eeprom_data._12vout_v.ad2) > 0 )
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data._12vout_v.point1 - g_eeprom_data._12vout_v.point2) /
                                                             (g_eeprom_data._12vout_v.ad1 - g_eeprom_data._12vout_v.ad2))*1000;   // 12VOUT_V AD(1)値係数(mV単位)
                            }
                            else
                            {
                                gf_cmd_ad_after_correction_slope = ((g_eeprom_data._12vout_v.point1 - g_eeprom_data._12vout_v.point2) / 1)*1000;   // 12VOUT_V AD(1)値係数(mV単位)
                            }
                            break;

                        default:
                            break;
                    }
                    gf_cmd_ad_calculated_value = gf_cmd_ad_after_correction_slope  * gu16_cmd_ad_set_ad_val;

                } else {
                    *response = HWE_ERR_RES;  // HW破損エラー(HWE)レスポンス
                }
                ret = _DONE_;
                gu8_cmd_ad_proc_stage = 0;
            }
            break;

        default:
            gu8_cmd_ad_proc_stage= 0;
            break;
    }
    return ret;
}

void set_life_calc_data_response(uint8_t *d_sndbuf);

/*******************************************************************************
 * Function Name: set_normal_response()
 * Description  : 正常レスポンス作成処理
 * Arguments    :
 * Return Value : 送信数
 *******************************************************************************/
uint16_t set_normal_response(uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num)
{
    uint16_t ret = 0;
    uint16_t bcc;
    uint8_t data[9];

    switch (cmd_id_no)
    {
    case CMD_ID_SP:    // 各種閾値設定用 (SET PARAMETER)
        gu8_d_sendbuf[0] = STX;           // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];  // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        gu8_d_sendbuf[3] = ETX;           // ETX
        gu8_d_sendbuf[4] = 0x30;          // BCC
        gu8_d_sendbuf[5] = 0x30;
        ret = 6; // 送信数
        break;

    case CMD_ID_RP:    // 各種閾値初期値設定 (RESET PARAMETER)
    case CMD_ID_CN:    // 強制充電 (CHARGE ON)
    case CMD_ID_CF:    // 強制充電停止 (CHARGE OFF)
    case CMD_ID_CL:    // ログ全クリア (CLEAR LOG)
    case CMD_ID_FU:    // FW アップデート (FW UPDATE)
        memcpy(gu8_d_sendbuf, d_recvbuf, num); // レスポンス(そのまま折り返し応答)
        ret = num; // 送信数
        break;

    case CMD_ID_SE:    // ERP 設定 (SET ERP)
    case CMD_ID_BE:    // バックアップ許可 (BACKUP ENABLE)
    case CMD_ID_BF:    // バックアップ停止 (BACKUP OFF)
    case CMD_ID_OR:    // 復電リスタート制御 (OUTPUT RESTART)
    case CMD_ID_D1:    // 状態情報 (GET DATA1)
        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        set_status_info(&gu8_d_sendbuf[3]); // 状態情報
        gu8_d_sendbuf[18] = ETX;            // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 21 - 2);
        gu8_d_sendbuf[19] = bcc >> 8;       // BCC
        gu8_d_sendbuf[20] = bcc & 0xff;
        ret = 21; // 送信数
        break;

    case CMD_ID_SC:    // 時刻設定 (SET CLOCK)
        gu8_d_sendbuf[0] = STX;           // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];  // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        gu8_d_sendbuf[3] = ETX;           // ETX
        gu8_d_sendbuf[4] = 0x31;          // BCC
        gu8_d_sendbuf[5] = 0x33;
        ret = 6; // 送信数
        break;

    case CMD_ID_SS:    // 製造情報設定 (SET SERIAL)
        gu8_d_sendbuf[0] = STX;           // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];  // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        gu8_d_sendbuf[3] = ETX;           // ETX
        gu8_d_sendbuf[4] = 0x30;          // BCC
        gu8_d_sendbuf[5] = 0x33;
        ret = 6; // 送信数
        break;

    case CMD_ID_SL:    // 寿命計算結果記憶 (SET LIFE)
        gu8_d_sendbuf[0] = STX;           // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];  // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        gu8_d_sendbuf[3] = ETX;           // ETX
        gu8_d_sendbuf[4] = 0x31;          // BCC
        gu8_d_sendbuf[5] = 0x43;
        ret = 6; // 送信数
        break;

    case CMD_ID_CD:    // データクリア (CLEAR DATA)
        gu8_d_sendbuf[0] = STX;           // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];  // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        gu8_d_sendbuf[3] = ETX;           // ETX
        gu8_d_sendbuf[4] = 0x30;          // BCC
        gu8_d_sendbuf[5] = 0x34;
        ret = 6; // 送信数
        break;

    case CMD_ID_BC:    // 寿命診断実行 (BATT CHECK)

        set_info_evt_errlog(FLAG_BATT_CHECK,_RESET_);
        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        set_life_diag_data_response(&gu8_d_sendbuf[3]); // 寿命診断データ    // ※ここをレスポンスデータに入れ替えるとエラー発生する
        gu8_d_sendbuf[33] = ETX;            // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 36 - 2);
        gu8_d_sendbuf[34] = bcc >> 8;       // BCC
        gu8_d_sendbuf[35] = bcc & 0xff;
        ret = 36; // 送信数
        break;

    case CMD_ID_D0:    // 全データ取得 (GET DATA0)

        // 寿命計算データ_レスポンス作成
        if( gu8_alm_type_batt_err != 0 )
        {
            gs_life_calc_data.charge_data = 0;      // バッテリ充電量データ
        }
        else if( gs_life_calc_data.batt_charge != 0 )
        {
            gs_life_calc_data.charge_data = 1;      // バッテリ充電量データ
        }
        gs_life_calc_data.batt_temp = gi16_ad_battery_temp / 10;        // バッテリ温度
        gs_life_calc_data.batt_deg = g_eeprom_data.set_life.batt_deg;         // バッテリ劣化度

        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        set_clock_data(&gu8_d_sendbuf[3]);           // 時刻データ
        set_realtime_data(&gu8_d_sendbuf[15]);       // リアルタイムデータ
        set_off_period_data(&gu8_d_sendbuf[65]);      // OFF期間データ
        set_life_calc_data(&gu8_d_sendbuf[95]);    // 寿命計算データ
        set_life_diag_data(&gu8_d_sendbuf[115]);   // 寿命診断データ
        set_cumulative_data(&gu8_d_sendbuf[145]);       // 積算データ
        set_manufacturing_data(&gu8_d_sendbuf[215]); // 製造データ
        set_parameter_data(&gu8_d_sendbuf[265]);     // 設定データ
        set_status_info(&gu8_d_sendbuf[315]);        // 状態情報
        gu8_d_sendbuf[330] = ETX;            // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 333 - 2);
        gu8_d_sendbuf[331] = bcc >> 8;       // BCC
        gu8_d_sendbuf[332] = bcc & 0xff;
        ret = 333; // 送信数
        break;

    case CMD_ID_D2:    // 起動時寿命計算用 (GET DATA2)
        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        set_off_period_data(&gu8_d_sendbuf[3]); // OFF期間データ
        gu8_d_sendbuf[33] = ETX;            // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 36 - 2);
        gu8_d_sendbuf[34] = bcc >> 8;       // BCC
        gu8_d_sendbuf[35] = bcc & 0xff;
        ret = 36; // 送信数
        break;

    case CMD_ID_D3:    // 通常寿命計算用 (GET DATA3)

        // 寿命計算データ_レスポンス作成
        if( gu8_alm_type_batt_err != 0 )
        {
            gs_life_calc_data.charge_data = 0;      // バッテリ充電量データ
        }
        else if( gs_life_calc_data.batt_charge != 0 )
        {
            gs_life_calc_data.charge_data = 1;      // バッテリ充電量データ
        }
        gs_life_calc_data.batt_temp = gi16_ad_battery_temp / 10;        // バッテリ温度
        gs_life_calc_data.batt_deg = g_eeprom_data.set_life.batt_deg;         // バッテリ劣化度

        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        set_life_calc_data(&gu8_d_sendbuf[3]);  // 寿命計算データ
        if (gu8_f_event_lost == _EVENT_LOST_OK_) // イベントロストフラグ
        {
            gu8_d_sendbuf[23] = '0';        // 正常
        }
        else
        {
            gu8_d_sendbuf[23] = '1';        // イベントロスト発生
        }
        gu8_f_event_lost = _EVENT_LOST_OK_; // イベントロストフラグ
        gu8_d_sendbuf[24] = ETX;            // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 27 - 2);
        gu8_d_sendbuf[25] = bcc >> 8;       // BCC
        gu8_d_sendbuf[26] = bcc & 0xff;
        ret = 27; // 送信数
        break;

    case CMD_ID_D4:    // 保守情報取得 (GET DATA4)
        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        set_clock_data(&gu8_d_sendbuf[3]);           // 時刻データ
        set_realtime_data(&gu8_d_sendbuf[15]);       // リアルタイムデータ
        set_life_diag_data(&gu8_d_sendbuf[65]);    // 寿命診断データ
        set_cumulative_data(&gu8_d_sendbuf[95]);        // 積算データ
        set_manufacturing_data(&gu8_d_sendbuf[165]); // 製造データ
        gu8_d_sendbuf[215] = ETX;            // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 218 - 2);
        gu8_d_sendbuf[216] = bcc >> 8;       // BCC
        gu8_d_sendbuf[217] = bcc & 0xff;
        ret = 218; // 送信数
        break;

    case CMD_ID_D5:    // REV/号機・設定確認 (GET DATA5)
        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        set_manufacturing_data(&gu8_d_sendbuf[3]);  // 製造データ
        set_parameter_data(&gu8_d_sendbuf[53]);     // 設定データ
        gu8_d_sendbuf[103] = ETX;            // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 106 - 2);
        gu8_d_sendbuf[104] = bcc >> 8;       // BCC
        gu8_d_sendbuf[105] = bcc & 0xff;
        ret = 106; // 送信数
        break;

    case CMD_ID_EL:    // エラーログ取得 (ERROR LOG)
        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];


        uint8_t offset;
        uint8_t tmp[2];

        tmp[0] = d_recvbuf[3];
        tmp[1] = d_recvbuf[4];
        offset =aschex_to_int(tmp, 2);

        int_to_aschex(d_recvbuf[3],&gu8_d_sendbuf[3],1);
        int_to_aschex(d_recvbuf[4],&gu8_d_sendbuf[4],1);

        set_err_log_data(&gu8_d_sendbuf[5],offset);

        gu8_d_sendbuf[85] = ETX;
        bcc = calc_bcc(gu8_d_sendbuf, 88 - 2);
        gu8_d_sendbuf[86] = bcc >> 8;       // BCC
        gu8_d_sendbuf[87] = bcc & 0xff;
        ret = 88; // 送信数
        break;

    case CMD_ID_OL:    // ON/OFF ログ取得 (OPERATE LOG)
    	 gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];

        uint8_t offset2;
        uint8_t tmp2[2];

        tmp2[0] = d_recvbuf[3];
        tmp2[1] = d_recvbuf[4];
        offset =aschex_to_int(tmp2, 2);
        int_to_aschex(d_recvbuf[3],&gu8_d_sendbuf[3],1);
        int_to_aschex(d_recvbuf[4],&gu8_d_sendbuf[4],1);
    	
        set_ope_log_data(&gu8_d_sendbuf[5],offset);
        gu8_d_sendbuf[85] = ETX;
        bcc = calc_bcc(gu8_d_sendbuf, 88 - 2);
        gu8_d_sendbuf[86] = bcc >> 8;       // BCC
        gu8_d_sendbuf[87] = bcc & 0xff;
        ret = 88; // 送信数
        break;

    case CMD_ID_FD:    // FW データ取得 (FW DATA)             // ********** 要作成
    {
        uint32_t fw_addr;
        volatile uint8_t *p_flash;
        uint16_t fd_data= 3;
        uint8_t ascii_buff[6];   //一時fuf
        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];

        memcpy(ascii_buff, &d_recvbuf[3], 6);  //送信された6バイトをコピー
        fw_addr = proc_cmd_fd(ascii_buff);   //アドレスに変換

        p_flash = (volatile uint8_t *)fw_addr;

        if ((fw_addr < FW_READ_START) ||
                    (fw_addr + 31 > FW_READ_END)){       //メモリ範囲外の場合
            for (int i = 0; i < 32; i++)
            {
                byte_to_hex_ascii(0xFF, &gu8_d_sendbuf[fd_data]);  //FFで埋める
            fd_data += 2;
            }
        }
        else{

            for (int i = 0; i < 32; i++)
           {
               byte_to_hex_ascii(p_flash[i], &gu8_d_sendbuf[fd_data]);
               fd_data += 2;
           }
        }
        gu8_d_sendbuf[fd_data++] = ETX;
        bcc = calc_bcc(gu8_d_sendbuf, fd_data);                  // BCC
        gu8_d_sendbuf[fd_data++] = bcc >> 8;
        gu8_d_sendbuf[fd_data++] = bcc & 0xff;
        ret = fd_data;
        //ret = cmd_fd_response( d_recvbuf, num );
        break;
    }

    case CMD_ID_AD:    // バッテリ電圧補正機能(ADJUST)
        gu8_d_sendbuf[0] = STX;                                 // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];                        // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        int_to_aschex(gu8_cmd_ad_type, data, 1);              // ADコマンド対象種類
        memcpy(&gu8_d_sendbuf[3], data, 1);
        int_to_aschex(gu8_cmd_ad_position, data, 1);                // ADコマンド補正位置
        memcpy(&gu8_d_sendbuf[4], data, 1);
        int_to_aschex(gu16_cmd_ad_set_ad_val, data, 6);         // AD値
        memcpy(&gu8_d_sendbuf[5], data, 6);
        float_to_aschex( gf_cmd_ad_calculated_value, data, 8 );    // 計算値
        memcpy(&gu8_d_sendbuf[11], data, 8);
        gu8_d_sendbuf[19] = ETX;                                // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 22 - 2);                  // BCC
        gu8_d_sendbuf[20] = bcc >> 8;
        gu8_d_sendbuf[21] = bcc & 0xff;
        ret = 22;                                               // 送信数
        break;

    case CMD_ID_AR:    // バッテリ電圧補正機能_読み出し用 (ADJUST READ)
        gu8_d_sendbuf[0] = STX;             // STX
        gu8_d_sendbuf[1] = d_recvbuf[1];    // 受信CMD ID
        gu8_d_sendbuf[2] = d_recvbuf[2];
        int_to_aschex(g_eeprom_data.dischg_i.ad1, data, 6);          // AD値(DISCHG_I, A)
        memcpy(&gu8_d_sendbuf[3], data, 6);
        int_to_aschex( g_eeprom_data.dischg_i.point1, data, 8 );     // 計算値(DISCHG_I, A)
        memcpy(&gu8_d_sendbuf[9], data, 8);
        int_to_aschex(g_eeprom_data.dischg_i.ad2, data, 6);          // AD値(DISCHG_I, B)
        memcpy(&gu8_d_sendbuf[17], data, 6);
        int_to_aschex( g_eeprom_data.dischg_i.point2, data, 8 );     // 計算値(DISCHG_I, B)
        memcpy(&gu8_d_sendbuf[23], data, 8);
        int_to_aschex(g_eeprom_data.batt_v.ad1, data, 6);            // AD値(BATT_V, A)
        memcpy(&gu8_d_sendbuf[31], data, 6);
        int_to_aschex( g_eeprom_data.batt_v.point1, data, 8 );       // 計算値(BATT_V, A)
        memcpy(&gu8_d_sendbuf[37], data, 8);
        int_to_aschex(g_eeprom_data.batt_v.ad2, data, 6);            // AD値(BATT_V, B)
        memcpy(&gu8_d_sendbuf[45], data, 6);
        int_to_aschex( g_eeprom_data.batt_v.point2, data, 8 );       // 計算値(BATT_V, B)
        memcpy(&gu8_d_sendbuf[51], data, 8);
        int_to_aschex( g_eeprom_data.acdc12v_v.ad1, data, 6);        // AD値(AC/DC12V_V, A)
        memcpy(&gu8_d_sendbuf[59], data, 6);
        int_to_aschex( g_eeprom_data.acdc12v_v.point1, data, 8 );    // 計算値(AC/DC12V_V, A)
        memcpy(&gu8_d_sendbuf[65], data, 8);
        int_to_aschex(g_eeprom_data.acdc12v_v.ad2, data, 6);         // AD値(AC/DC12V_V, B)
        memcpy(&gu8_d_sendbuf[73], data, 6);
        int_to_aschex( g_eeprom_data.acdc12v_v.point2, data, 8 );    // 計算値(AC/DC12V_V, B)
        memcpy(&gu8_d_sendbuf[79], data, 8);
        int_to_aschex(g_eeprom_data.batt_chg.ad1, data, 6);          // AD値(BATT_CHG, A)
        memcpy(&gu8_d_sendbuf[87], data, 6);
        int_to_aschex( g_eeprom_data.batt_chg.point1, data, 8 );     // 計算値(BATT_CHG, A)
        memcpy(&gu8_d_sendbuf[93], data, 8);
        int_to_aschex(g_eeprom_data.batt_chg.ad2, data, 6);          // AD値(BATT_CHG, B)
        memcpy(&gu8_d_sendbuf[101], data, 6);
        int_to_aschex( g_eeprom_data.batt_chg.point2, data, 8 );     // 計算値(BATT_CHG, B)
        memcpy(&gu8_d_sendbuf[107], data, 8);
        int_to_aschex(g_eeprom_data._12vout_v.ad1, data, 6);         // AD値(12V_OUT_V, A)
        memcpy(&gu8_d_sendbuf[115], data, 6);
        int_to_aschex( g_eeprom_data._12vout_v.point1, data, 8 );    // 計算値(12V_OUT_V, A)
        memcpy(&gu8_d_sendbuf[121], data, 8);
        int_to_aschex( g_eeprom_data._12vout_v.ad2, data, 6);        // AD値(12V_OUT_V, B)
        memcpy(&gu8_d_sendbuf[129], data, 6);
        int_to_aschex( g_eeprom_data._12vout_v.point2, data, 8 );    // 計算値(12V_OUT_V, B)
        memcpy(&gu8_d_sendbuf[135], data, 8);
        gu8_d_sendbuf[143] = ETX;                 // ETX
        bcc = calc_bcc(gu8_d_sendbuf, 146 - 2);    // BCC
        gu8_d_sendbuf[144] = bcc >> 8;
        gu8_d_sendbuf[145] = bcc & 0xff;
        ret = 146;                                      // 送信数
         break;

    case CMD_ID_FF:    // 未定義
    default:
        break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: set_error_response()
 * Description  : レスポンスデータセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
uint16_t set_error_response(uint8_t *d_recvbuf, uint8_t err_kind)
{
    uint16_t bcc;
    uint16_t ret = ERR_RES_NUM; // 送信数

    memcpy(gu8_d_sendbuf, &ERROR_RESPONSE_TBL[err_kind], ERR_RES_NUM); // レスポンスデータ
    gu8_d_sendbuf[1] = d_recvbuf[1];                                 // 受信CMD ID
    gu8_d_sendbuf[2] = d_recvbuf[2];
    bcc = calc_bcc(gu8_d_sendbuf, ERR_RES_NUM - 2);
    gu8_d_sendbuf[ERR_RES_NUM - 2] = bcc >> 8;                            // BCC
    gu8_d_sendbuf[ERR_RES_NUM - 1] = bcc & 0xff;
    if( err_kind == HWE_ERR_RES )  // HW破損エラー(HWE)レスポンス
    {
        set_info_evt_errlog( FLAG_BBU_FAIL, _SET_ );
    }
    // COM_ALM記録

    return ret;
}

/*******************************************************************************
 * Function Name: ack_response()
 * Description  : ACK応答
 * Arguments    :
 * Return Value : ==0 : 処理中
 *                ==1 : 処理完了
 *******************************************************************************/
uint8_t ack_response(void)
{
    uint8_t ret = _CONTINUE_;
    //static uint8_t ack_stage = 0;
    static uint8_t pos;
    static uint32_t c_timer;
    static uint8_t c_retry;

    switch (gu8_ack_stage)
    {
    case 0:
        c_retry = 0;
        //break   // fall-through
    case 1:
        gu8_d_sendbuf[0] = ACK;
        pos = uart_send_req(gu8_d_sendbuf, 1);
        c_timer = TIMER_10ms;
        gu8_ack_stage = 2;
        break;
    case 2:
        if (--c_timer != 0)
        {
            if (send_complete_check(pos) == 0)
            {
                gu8_ack_stage = 0;
                ret = _DONE_;
            }
        }
        else
        {
            if (++c_retry <= RETRY_NUM)
            {
                gu8_ack_stage = 1;
            }
            else
            {
                // COM_ALM記録
                gu8_ack_stage = 0;
                ret = _DONE2_;
            }
        }
        break;
    default:
        gu8_ack_stage = 0;
        ret = _DONE_;
        break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: nak_response()
 * Description  : NAK応答
 * Arguments    :
 * Return Value : ==0 : 処理中
 *                ==1 : 処理完了
 *******************************************************************************/
uint8_t nak_response(void)
{
    uint8_t ret = _CONTINUE_;
    //static uint8_t nak_stage = 0;
    static uint8_t pos;
    static uint32_t c_timer;
    static uint8_t c_retry;

    switch (gu8_nak_stage)
    {
    case 0:
        c_retry = 0;
        //break   // fall-through
    case 1:
        gu8_d_sendbuf[0] = NAK;
        gu8_d_sendbuf[1] = gu8_f_nak_sndreq;
        pos = uart_send_req(gu8_d_sendbuf, 2);
        c_timer = TIMER_10ms;
        gu8_nak_stage = 2;
        break;
    case 2:
        if (--c_timer != 0)
        {
            if (send_complete_check(pos) == 0)
            {
                // COM_ALM記録
                gu8_nak_stage = 0;
                ret = _DONE_;
            }
        }
        else
        {
            //if( ++c_retry <= RETRY_NUM )
            //{
            gu8_nak_stage = 1;
            //} else {
            //    gu8_nak_stage = 0;
            //    ret = _DONE2_;
            //}
        }
        break;
    default:
        gu8_nak_stage = 0;
        ret = _DONE_;
        break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: set_clock_data()
 * Description  : 時刻データセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_clock_data(uint8_t *d_sndbuf)
{
    uint8_t data[5];

    gs_RTCCalendar = DL_RTC_getCalendarTime(RTC);
    int_to_aschex((gs_RTCCalendar.year-2000), data, 2);       // 年(西暦下2桁)
    memcpy(&d_sndbuf[0], data, 2);
    int_to_aschex(gs_RTCCalendar.month, data, 2);      // 月
    memcpy(&d_sndbuf[2], data, 2);
    int_to_aschex(gs_RTCCalendar.dayOfMonth, data, 2); // 日
    memcpy(&d_sndbuf[4], data, 2);
    int_to_aschex(gs_RTCCalendar.hours, data, 2);      // 時間(24時間)
    memcpy(&d_sndbuf[6], data, 2);
    int_to_aschex(gs_RTCCalendar.minutes, data, 2);    // 分
    memcpy(&d_sndbuf[8], data, 2);
    int_to_aschex(gs_RTCCalendar.seconds, data, 2);    // 秒
    memcpy(&d_sndbuf[10], data, 2);
    // 12byte
}

/*******************************************************************************
 * Function Name: set_realtime_data()
 * Description  : リアルタイムデータセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_realtime_data(uint8_t *d_sndbuf)
{
    uint8_t ii;
    uint8_t data[5];

    int_to_aschex(gs_realtime_data._12v_voltage, data, 4);      // 12V出力電圧値
    memcpy(&d_sndbuf[0], data, 4);
    int_to_aschex(gs_realtime_data._12v_current, data, 4);      // 12V出力電流値
    memcpy(&d_sndbuf[4], data, 4);
    int_to_aschex(gs_realtime_data.batt_voltage, data, 4);      // バッテリ電圧
    memcpy(&d_sndbuf[8], data, 4);
    int_to_aschex(gs_realtime_data.charge_voltage, data, 4);    // バッテリ充電電圧
    memcpy(&d_sndbuf[12], data, 4);
    int_to_aschex(gs_realtime_data.batt_chg_current, data, 4);  // バッテリ充電電流
    memcpy(&d_sndbuf[16], data, 4);
    int_to_aschex(gs_realtime_data.batt_current, data, 4);      // バッテリ放電電流
    memcpy(&d_sndbuf[20], data, 4);
    int_to_aschex(gs_realtime_data.batt_soc_wh, data, 2);       // バッテリSOC(Wh)
    memcpy(&d_sndbuf[24], data, 2);
    int_to_aschex(gs_realtime_data.batt_soc_mah, data, 2);      // バッテリSOC(mAh)
    memcpy(&d_sndbuf[26], data, 2);
    int_to_aschex(gs_realtime_data.batt_temp, data, 2);         // バッテリ温度
    memcpy(&d_sndbuf[28], data, 2);
    int_to_aschex(gs_realtime_data.adu_temp, data, 2);          // AC/DC部内部温度
    memcpy(&d_sndbuf[30], data, 2);
    int_to_aschex(gs_realtime_data.bbu_temp, data, 2);          // BACKUP部内部温度
    memcpy(&d_sndbuf[32], data, 2);
    int_to_aschex(gs_realtime_data.fan_rotation, data, 4);      // FAN回転数
    memcpy(&d_sndbuf[34], data, 4);
    int_to_aschex(gs_realtime_data.fan_level, data, 1);         // FAN回転数レベル
    memcpy(&d_sndbuf[38], data, 1);

    for (ii = 0; ii < 11; ii++)
    {
        d_sndbuf[39 + ii] = '0';
    }
    // 50byte
}

/*******************************************************************************
 * Function Name: set_parameter_data()
 * Description  : 設定データセット (SET_PARAMETER)
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_parameter_data(uint8_t *d_sndbuf)
{
    uint8_t ii;
    uint8_t data[5];

    int_to_aschex( g_eeprom_data.set_parameter.ps_on_backup, data, 1 );       // 停電時のバックアップ動作設定
    memcpy( &d_sndbuf[0], data, 1 );
    int_to_aschex( g_eeprom_data.set_parameter.ac_link, data, 1 );            // 停電後の復電検出におけるリスタート動作設定
    memcpy( &d_sndbuf[1], data, 1 );
    int_to_aschex( g_eeprom_data.set_parameter.auto_charge, data, 1 );        // 自動充電方式の設定
    memcpy( &d_sndbuf[2], data, 1 );
    int_to_aschex( g_eeprom_data.set_parameter.event, data, 1 );              // イベント送信設定
    memcpy( &d_sndbuf[3], data, 1 );
    int_to_aschex( g_eeprom_data.set_parameter.max_backup_time, data, 1 );    // 最大バックアップ時間設定(分)
    memcpy( &d_sndbuf[4], data, 1 );
    int_to_aschex( g_eeprom_data.set_parameter.min_backup_time, data, 2 );    // 最小バックアップ時間設定(秒)
    memcpy( &d_sndbuf[5], data, 2 );
    int_to_aschex( g_eeprom_data.set_parameter.restart_time, data, 2 );       // AC_LINKが有効およびOUTPUT RESTARTコマンドを受信時のリスタート実行時に出力をオフする時間
    memcpy( &d_sndbuf[7], data, 2 );
    int_to_aschex( g_eeprom_data.set_parameter.batt_low_thf, data, 2 );       // バッテリ充電量低下(BATT_LOW)閾値
    memcpy( &d_sndbuf[9], data, 2 );
    int_to_aschex( g_eeprom_data.set_parameter.batt_cap_mah, data, 4 );       // バッテリ容量(mAh単位)
    memcpy( &d_sndbuf[11], data, 4 );
    int_to_aschex( g_eeprom_data.set_parameter.batt_cap_wh, data, 2 );        // バッテリ容量(Wh単位)
    memcpy( &d_sndbuf[15], data, 2 );
    int_to_aschex( g_eeprom_data.set_parameter.chg_ir_thd, data, 3 );         // 充電DCIRの判定閾値
    memcpy( &d_sndbuf[17], data, 3 );
    int_to_aschex( g_eeprom_data.set_parameter.batt_wng_thd, data, 2 );       // バッテリ充電抑止温度閾値
    memcpy( &d_sndbuf[20], data, 2 );
    int_to_aschex( g_eeprom_data.set_parameter.batt_alm_thd, data, 2 );       // バッテリ温度異常閾値
    memcpy( &d_sndbuf[22], data, 2 );
    int_to_aschex( g_eeprom_data.set_parameter.adu_temp_thd, data, 2 );       // AC/DC部の温度警告(ADU_TEMP_WNG)の検出閾値
    memcpy( &d_sndbuf[24], data, 2 );
    int_to_aschex( g_eeprom_data.set_parameter.bbu_temp_thd, data, 2 );       // BACKUP部の温度警告(BBU_TEMP_WNG)の検出閾値
    memcpy( &d_sndbuf[26], data, 2 );
    int_to_aschex( g_eeprom_data.set_parameter.fan_wng_thd, data, 4 );        // FANの回転停止警告(FAN_WMG)の検出閾値
    memcpy( &d_sndbuf[28], data, 4 );

    for (ii = 0; ii < 18; ii++)
    {
        d_sndbuf[32 + ii] = '0';
    }
    // 50byte
}

/*******************************************************************************
 * Function Name: set_status_info()
 * Description  : 状態情報セット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_status_info(uint8_t *d_sndbuf)
{
    uint8_t ii;
    uint8_t *p = (uint8_t*) &gs_status_info;

    for (ii = 0; ii < 15; ii++)
    {
        d_sndbuf[ii] = bit_to_aschex(p[ii]);
    }
    // 15byte
}

/*******************************************************************************
 * Function Name: set_life_diag_data()
 * Description  : 寿命診断データセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_life_diag_data(uint8_t *d_sndbuf)
{
    uint8_t ii;
    uint8_t data[5];

    int_to_aschex(gs_life_diag_data.batt_check_mode, data, 1); // バッテリ測定モード
    memcpy(&d_sndbuf[0], data, 1);
    int_to_aschex(gs_life_diag_data.batt_voltage1, data, 4);   // バッテリ測定電圧1
    memcpy(&d_sndbuf[1], data, 4);
    int_to_aschex(gs_life_diag_data.batt_voltage2, data, 4);   // バッテリ測定電圧2
    memcpy(&d_sndbuf[5], data, 4);
    int_to_aschex(gs_life_diag_data.batt_current1, data, 4);   // バッテリ測定電流1
    memcpy(&d_sndbuf[9], data, 4);
    int_to_aschex(gs_life_diag_data.batt_current2, data, 4);   // バッテリ測定電流2
    memcpy(&d_sndbuf[13], data, 4);
    int_to_aschex(gs_life_diag_data.batt_ir_temp, data, 2);    // バッテリ測定温度
    memcpy(&d_sndbuf[17], data, 2);
    int_to_aschex(gs_life_diag_data.batt_ir_soc_mah, data, 2); // バッテリ測定SOC(mAh)
    memcpy(&d_sndbuf[19], data, 2);
    int_to_aschex(gs_life_diag_data.batt_ir, data, 3);         // バッテリのDCIR
    memcpy(&d_sndbuf[21], data, 3);

    for (ii = 0; ii < 6; ii++)
    {
        d_sndbuf[24 + ii] = '0';
    }
    // 30byte
}

/*******************************************************************************
 * Function Name: set_life_diag_data_response()
 * Description  : 寿命診断データセット(レスポンス用)
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_life_diag_data_response(uint8_t *d_sndbuf)
{
    uint8_t ii;
    uint8_t data[5];

    int_to_aschex(gs_life_diag_data_response.batt_check_mode_res, data, 1); // バッテリ測定モード
    memcpy(&d_sndbuf[0], data, 1);
    int_to_aschex(gs_life_diag_data_response.batt_voltage1_res, data, 4);   // バッテリ測定電圧1
    memcpy(&d_sndbuf[1], data, 4);
    int_to_aschex(gs_life_diag_data_response.batt_voltage2_res, data, 4);   // バッテリ測定電圧2
    memcpy(&d_sndbuf[5], data, 4);
    int_to_aschex(gs_life_diag_data_response.batt_current1_res, data, 4);   // バッテリ測定電流1
    memcpy(&d_sndbuf[9], data, 4);
    int_to_aschex(gs_life_diag_data_response.batt_current2_res, data, 4);   // バッテリ測定電流2
    memcpy(&d_sndbuf[13], data, 4);
    int_to_aschex(gs_life_diag_data_response.batt_ir_temp_res, data, 2);    // バッテリ測定温度
    memcpy(&d_sndbuf[17], data, 2);
    int_to_aschex(gs_life_diag_data_response.batt_ir_soc_mah_res, data, 2); // バッテリ測定SOC(mAh)
    memcpy(&d_sndbuf[19], data, 2);
    int_to_aschex(gs_life_diag_data_response.batt_ir_res, data, 3);         // バッテリのDCIR
    memcpy(&d_sndbuf[21], data, 3);

    for (ii = 0; ii < 6; ii++)
    {
        d_sndbuf[24 + ii] = '0';
    }
    // 30byte
}

/*******************************************************************************
 * Function Name: set_life_diag_data()
 * Description  : 寿命計算データセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_life_calc_data(uint8_t *d_sndbuf)
{
    uint8_t ii;
    uint8_t data[5];

    int_to_aschex(gs_life_calc_data.charge_data, data, 1);     // バッテリ充電量データ
    memcpy(&d_sndbuf[0], data, 1);
    int_to_aschex(gs_life_calc_data.charge_end, data, 1);      // バッテリ充電完了
    memcpy(&d_sndbuf[1], data, 1);
    int_to_aschex(gs_life_calc_data.batt_charge, data, 2);     // バッテリ充電量
    memcpy(&d_sndbuf[2], data, 2);
    int_to_aschex(gs_life_calc_data.batt_temp, data, 2);       // バッテリ温度
    memcpy(&d_sndbuf[4], data, 2);
    int_to_aschex(gs_life_calc_data.batt_deg, data, 3);        // バッテリ劣化度
    memcpy(&d_sndbuf[6], data, 3);

    for (ii = 0; ii < 11; ii++)
    {
        d_sndbuf[9 + ii] = '0';
    }
    // 20byte
}

/*******************************************************************************
 * Function Name: set_cumulative_data()
 * Description  : 積算データデータセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_cumulative_data(uint8_t *d_sndbuf)
{
    uint8_t ii;
    uint8_t data[7];

    int_to_aschex( SEK_TOTAL_ADU_TEMP, data, 6);        // 電源内部積算温度
    memcpy(&d_sndbuf[0], data, 6);
    int_to_aschex( SEK_TOTAL_ADU_HOUR, data, 4);        // 電源稼働時間
    memcpy(&d_sndbuf[6], data, 4);
    int_to_aschex( SEK_AC_FAIL_COUNT, data, 3);         // 瞬断回数(70V以下)
    memcpy(&d_sndbuf[10], data, 3);
    int_to_aschex( SEK_AC_LOW_COUNT, data, 3);          // 瞬断回数(90V以下)
    memcpy(&d_sndbuf[13], data, 3);
    int_to_aschex( SEK_TOTAL_BACKUP_COUNT, data, 4);    // バックアップ回数
    memcpy(&d_sndbuf[16], data, 4);
    int_to_aschex( SEK_BATT_DEG, data, 3);              // バッテリ劣化度
    memcpy(&d_sndbuf[20], data, 3);
    int_to_aschex( SEK_TOTAL_BATT_HOUR, data, 4);       // バッテリ接続時間
    memcpy(&d_sndbuf[23], data, 4);
    int_to_aschex( SEK_BATT_DISCHARGE_COUNT, data, 4);  // バッテリ総放電回数
    memcpy(&d_sndbuf[27], data, 4);
    int_to_aschex( SEK_BATT_CHARGE_COUNT, data, 3);     // バッテリ総充電回数
    memcpy(&d_sndbuf[31], data, 3);
    int_to_aschex( SEK_BATT_TTL_DISCHARGE, data, 6);    // バッテリ総放電量
    memcpy(&d_sndbuf[34], data, 6);
    int_to_aschex( SEK_BATT_TTL_CHARGE, data, 6);       // バッテリ総充電量
    memcpy(&d_sndbuf[40], data, 6);
    int_to_aschex( SEK_TOTAL_BATT_TEMP, data, 6);       // バッテリ積算温度
    memcpy(&d_sndbuf[46], data, 6);
    int_to_aschex( SEK_BATT_TEMP_AVE, data, 2);         // バッテリ平均温度
    memcpy(&d_sndbuf[52], data, 2);
    int_to_aschex( SEK_BATT_TEMP_MAX, data, 2);         // バッテリ最高温度
    memcpy(&d_sndbuf[54], data, 2);
    int_to_aschex( SEK_BATT_TEMP_MIN, data, 2);         // バッテリ最低温度
    memcpy(&d_sndbuf[56], data, 2);

    for (ii = 0; ii < 12; ii++)
    {
        d_sndbuf[58 + ii] = '0';
    }
    // 70byte
}

/*******************************************************************************
 * Function Name: set_off_period_data()
 * Description  : OFF期間データセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_off_period_data(uint8_t *d_sndbuf)
{
    uint8_t ii;
    uint8_t data[5];

    int_to_aschex( OFF_AC_OFF_HOUR, data, 4);     // AC_OFF合計時間[H]
    memcpy(&d_sndbuf[0], data, 4);
    int_to_aschex( OFF_PS_HOUR, data, 4);         // バッテリのPS_OFF合計時間[H]
    memcpy(&d_sndbuf[4], data, 4);
    int_to_aschex( OFF_AVE_OFF_TEMP, data, 2);    // PS_OFF中のバッテリの平均温度
    memcpy(&d_sndbuf[8], data, 2);
    int_to_aschex( OFF_OFF_CHARGE_HOUR, data, 3); // バッテリ充電合計時間[H]
    memcpy(&d_sndbuf[10], data, 3);
    int_to_aschex( OFF_AVE_CHARGE_TEMP, data, 2); // 充電中のバッテリの平均温度
    memcpy(&d_sndbuf[13], data, 2);
    int_to_aschex( OFF_OFF_CHARGE, data, 3);      // バッテリ総充電量
    memcpy(&d_sndbuf[15], data, 3);
    int_to_aschex( OFF_BATT_DEG, data, 3);        // バッテリ劣化度
    memcpy(&d_sndbuf[18], data, 3);

    for (ii = 0; ii < 9; ii++)
    {
        d_sndbuf[21 + ii] = '0';
    }
    // 30byte
}

/*******************************************************************************
 * Function Name: set_off_period_data()
 * Description  : 製造データセット (SET SERIAL)
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_manufacturing_data(uint8_t *d_sndbuf)
{
    memcpy(&d_sndbuf[0], &SS_FW_REV, 6);      // FW REVISION
    memcpy(&d_sndbuf[6], &SS_UNIT_REV, 4);    // ユニットレビジョン
    memcpy(&d_sndbuf[10], &SS_UNIT_LOT, 4);    // ユニット製造ロット
    memcpy(&d_sndbuf[14], &SS_UNIT_SERIAL, 6); // ユニット製造号機
    memcpy(&d_sndbuf[20], &SS_ADU_REV, 4);     // AC/DC レビジョン
    memcpy(&d_sndbuf[24], &SS_ADU_LOT, 4);     // AC/DC製造ロット
    memcpy(&d_sndbuf[28], &SS_ADU_SERIAL, 6);  // AC/DC製造号機
    memcpy(&d_sndbuf[34], &SS_BBU_REV, 4);     // BACKUP部レビジョン
    memcpy(&d_sndbuf[38], &SS_BBU_LOT, 4);     // BACKUP部製造ロット
    memcpy(&d_sndbuf[42], &SS_BBU_SERIAL, 6);  // BACKUP部製造号機

    d_sndbuf[48] = '0';
    d_sndbuf[49] = '0';
    // 50byte
}

/*******************************************************************************
* Function Name: aft_ack_rcv_proc()
* Description  : ACK受信後処理プロセス
* Arguments    : *asc_data :
* Return Value : hex
*******************************************************************************/
uint8_t aft_ack_rcv_proc(uint8_t cmd_id_no, uint8_t *d_recvbuf, uint8_t num)
{
    uint8_t ret=_DONE_;
    switch (cmd_id_no)
    {
        case CMD_ID_D0:    // 全データ取得 (GET DATA0)
            gs_life_calc_data.charge_end = 0;
            break;

        case CMD_ID_D2:    // 起動時寿命計算用 (GET DATA2)
            gu8_f_off_time_data_clear_en = _ENABLE_;    // OFF期間データクリア有効
            break;

        case CMD_ID_D3:    // 通常寿命計算用 (GET DATA3)
            gs_life_calc_data.charge_data = 0;
            gs_life_calc_data.charge_end = 0;
            gs_life_calc_data.batt_charge = 0;
            gs_life_calc_data.batt_temp = 0;
            gs_life_calc_data.batt_deg = 0;

            // 寿命計算データ用カウンタフラグ等クリア
            gu8_f_jcd_chg_soc_calc_fin = 0;
            gf_jcd_ttl_chg_soc = 0;
            gf_jcd_chg_soc_now = 0;
            break;

        case CMD_ID_D4:
            g_eeprom_data.cumulative_data.ac_fail_count = 0;
            break;

        case CMD_ID_SL:    // 寿命計算結果記憶 (SET LIFE)
            if( gu8_f_off_time_data_clear_en == _ENABLE_ )
            {
                g_eeprom_data.off_period_data.ac_off_hour = 0;
                g_eeprom_data.off_period_data.ps_off_hour = 0;
                g_eeprom_data.off_period_data.ave_off_temp = 0;
                g_eeprom_data.off_period_data.off_charge_hour = 0;
                g_eeprom_data.off_period_data.ave_charge_temp = 0;
                g_eeprom_data.off_period_data.off_charge = 0;
                g_eeprom_data.off_period_data.ac_off_hour_sub = 0;
                g_eeprom_data.off_period_data.ps_off_hour_sub = 0;
                g_eeprom_data.off_period_data.off_charge_hour_sub = 0;

                // OFF期間データ用カウンタフラグ等クリア
                gi16_otd_ps_off_bat_temp_ave = 0;
                gi16_otd_chg_bat_temp_ave = 0;
                gu8_f_otd_chg_soc_calc_fin = 0;
                gf_otd_chg_soc_now = 0.0;
                gu8_f_otd_batt_deg_set = 0;
                gu16_c_otd_ps_off_bat_temp_ave = 0;
                gu16_c_otd_chg_bat_temp_ave = 0;
            }
            break;

         case CMD_ID_FU:    // FW アップデート (FW UPDATE)

            //gu8_f_fw_update_mode = 1;

            if(eeprom_req_busy==0)
            {
                DL_WWDT_disablePower(WWDT0_INST);              //  WWDT無効化
               // eeprom_write_request( EEPROM_BATT_POS, 112, 0 );
                data_info_common.gu8_f_fw_update_mode = 1;//gu8_f_fw_update_mode;
                jumpBoot();
            }else
            {
                ret=_CONTINUE_;
            }


#if 0
            gu8_proc_stage = 0;

            gu8_rx_proc_stage = 0;
            gu8_f_command_proc = 0;
            gu8_d_uart_rcv_rpt = (gu8_d_uart_rcv_rpt + 1) & (UART_RCV_NUM - 1);
            gu8_rx_proc_stage = 0;
#if 1
            DL_TimerA_setCounterRepeatMode(FAN_PWM_INST, GPTIMER_CTRCTL_REPEAT_REPEAT_1);
            DL_TimerA_setLoadValue(FAN_PWM_INST, (uint32_t)1600);
            DL_TimerA_setCaptureCompareValue(FAN_PWM_INST, (uint32_t)0, DL_TIMERG_CAPTURE_COMPARE_0_INDEX);
            DL_TimerA_startCounter(FAN_PWM_INST);
#endif
            {
                uint32_t app_sp    = *(volatile uint32_t *)(0);

                __disable_irq();

                //SCB->VTOR = 0;
                while(1)
                {
                    SCB->VTOR = 0;
                    if( SCB->VTOR == 0)
                    {
                        break;
                    }
                }

                __set_MSP(app_sp);

                (*((void (*)(void))(*(uint32_t *)0x28)))();  // Boot_Reset_Handler_2
            }
#endif
            break;

       default:
            break;
    }
    return ret;
}

/*******************************************************************************
 * Function Name: err_log_data()
 * Description  : エラーログデータセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_err_log_data(uint8_t *d_sndbuf,uint8_t d_sndbuf2){
    uint8_t data[3];

    uint8_t wp = g_eeprom_data.error_log_index.error_log_writepointer;

    for(int i=0;i<8;i++){


      uint8_t idx =(wp + ERROR_LOG_COUNT - d_sndbuf2 - i) % ERROR_LOG_COUNT;

      int_to_aschex( g_eeprom_data.error_log_data[idx].year, data, 2);
      memcpy(&d_sndbuf[i*10+0], data, 2);
      int_to_aschex( g_eeprom_data.error_log_data[idx].month, data, 2);
      memcpy(&d_sndbuf[i*10+2], data, 2);
      int_to_aschex( g_eeprom_data.error_log_data[idx].day , data, 2);
      memcpy(&d_sndbuf[i*10+4], data, 2);
      int_to_aschex(  g_eeprom_data.error_log_data[idx].hour, data, 2);
      memcpy(&d_sndbuf[i*10+6], data, 2);
      int_to_aschex( g_eeprom_data.error_log_data[idx].id, data, 2);
      memcpy(&d_sndbuf[i*10+8], data, 2);
    }

}

/*******************************************************************************
 * Function Name: operate_log_data()
 * Description  : オペレートログデータセット
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void set_ope_log_data(uint8_t *d_sndbuf,uint8_t d_sndbuf2){
    uint8_t data[3];
	
    uint8_t wp = g_eeprom_data.operate_log_index.operate_log_writepointer;
	
	
    for(int i=0;i<8;i++){

      uint8_t idx =(wp + OPERATE_LOG_COUNT - d_sndbuf2 - i) % OPERATE_LOG_COUNT;

      int_to_aschex( g_eeprom_data.operate_log_data[idx].year, data, 2);
      memcpy(&d_sndbuf[i*10+0], data, 2);
      int_to_aschex( g_eeprom_data.operate_log_data[idx].month, data, 2);
      memcpy(&d_sndbuf[i*10+2], data, 2);
      int_to_aschex( g_eeprom_data.operate_log_data[idx].day , data, 2);
      memcpy(&d_sndbuf[i*10+4], data, 2);
      int_to_aschex(  g_eeprom_data.operate_log_data[idx].hour, data, 2);
      memcpy(&d_sndbuf[i*10+6], data, 2);
      int_to_aschex( g_eeprom_data.operate_log_data[idx].id, data, 2);
      memcpy(&d_sndbuf[i*10+8], data, 2);
    }
}

/*******************************************************************************
 * Function Name: hex2val()
 * Description  :
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
static uint8_t hex2val(uint8_t c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return 0;
}

/*******************************************************************************
 * Function Name: proc_cmd_fd()
 * Description  :
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
 uint32_t proc_cmd_fd(uint8_t *addr_buf){

    uint32_t fw_addr = 0;

    for (int i = 0; i < 6; i++)
       {
           fw_addr <<= 4;
           fw_addr |= hex2val(addr_buf[i]);

       }

return fw_addr;

}

/*******************************************************************************
 * Function Name: tx_proc()
 * Description  : UART TX処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void tx_proc(void)
{
    //static uint8_t tx_send_stage = 0;
    static uint16_t c_tx_send_delay = 0;
    uint8_t tdata;

    switch (gu8_tx_send_stage)
    {
    case 0:
        if (gu8_d_uart_snd_wpt != gu8_d_uart_snd_rpt)
        {
            c_tx_send_delay = TIMER_10ms;
            //gu8_tx_send_stage = 1;
            gu8_tx_send_stage = 2;
        }
        break;

    case 1:  // 10ms delay
        if (c_tx_send_delay == 0)
        {
            gu8_tx_send_stage = 2;
        }
        else
        {
            c_tx_send_delay--;
        }
        break;

    case 2:  // 最初のデータ送信
        gu16_c_tx = 1;
        tdata = gu8_d_uart_sendbuf[gu8_d_uart_snd_rpt][0];
        DL_UART_Main_transmitData(UART_0_INST, tdata);  // 送信割込
        gu8_tx_send_stage = 3;
        break;

    case 3:
        if (gu16_tx_send_req[gu8_d_uart_snd_rpt][0] == 0)
        {
            gu8_d_uart_snd_rpt = (gu8_d_uart_snd_rpt + 1) & (UART_REQ_NUM - 1);
            gu8_tx_send_stage = 0;
        }
        break;

    default:
        gu8_tx_send_stage = 0;
        break;
    }
}

/*******************************************************************************
 * Function Name: tx_proc()
 * Description  : UART TX処理
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void update_wait(void)
{
    if(data_info_common.gu8_f_fw_update_mode == 1){

        if(eeprom_req_busy==0){

            jumpBoot();
        }
    }

}




/*******************************************************************************
 * Function Name: uart_send_req()
 * Description  : UART 送信要求
 * Arguments    : *sendbuf = 送信データ
 : num      = 送信数
 * Return Value : POS
 *******************************************************************************/
uint8_t uart_send_req(uint8_t *sendbuf, uint16_t num)
{
    uint8_t pos;

    memcpy(&gu8_d_uart_sendbuf[gu8_d_uart_snd_wpt][0], sendbuf, num);
    gu16_tx_send_req[gu8_d_uart_snd_wpt][1] = num;
    gu16_tx_send_req[gu8_d_uart_snd_wpt][0] = 1;

    pos = gu8_d_uart_snd_wpt;

    gu8_d_uart_snd_wpt = (gu8_d_uart_snd_wpt + 1) & (UART_REQ_NUM - 1);

    return pos;
}

/*******************************************************************************
 * Function Name: send_complete_check()
 * Description  : UART 送信バッファ位置取得
 * Arguments    : None
 * Return Value : 位置
 *******************************************************************************/
uint8_t sendbuf_pos_get(void)
{
    return gu8_d_uart_snd_wpt;
}

/*******************************************************************************
 * Function Name: send_complete_check()
 * Description  : UART 送信完了チェック
 * Arguments    : pos = 位置
 * Return Value : 0=完了/1:送信中
 *******************************************************************************/
uint8_t send_complete_check(uint8_t pos)
{
    return gu16_tx_send_req[pos][0];
}

/*******************************************************************************
 * Function Name: calc_bcc()
 * Description  : BCC計算
 * Arguments    : buf=送信データ
 *              : len=送信データ長(ETXまで)
 * Return Value : BCC
 *******************************************************************************/
uint16_t calc_bcc(uint8_t *buf, uint16_t len)
{
    uint8_t bcc;
    uint16_t bcc_char;
    uint16_t ii = 1;       // 最初のSTXは除く
    uint8_t dt;
    uint8_t tmp[2 + 1];

    bcc = buf[ii++];
    while (1)
    {
        dt = buf[ii++];
        bcc ^= dt;
        //if( (dt == ETX) && (ii >= len) ) break;
        if (ii >= len)
            break;
    }
    int_to_aschex(bcc, tmp, 2);
    bcc_char = (tmp[0] << 8) + tmp[1];
    return bcc_char;
}

/*******************************************************************************
 * Function Name: bit_to_aschex()
 * Description  : ルール1 bit->ASCII
 * Arguments    : value :
 * Return Value : hex
 *******************************************************************************/
uint8_t bit_to_aschex(uint8_t value)
{

    uint8_t n = value & 0x0f;

    if (n <= 9)
    {
        n += '0';        // ASCII(0-9)
    }
    else
    {
        n += ('A' - 10); // ASCII(A-F)
    }
    return n;
}

/*******************************************************************************
 * Function Name: int_to_aschex()
 * Description  : ルール2 数値->ASCII
 * Arguments    : value :
 *                *asc_data :
 *                n :バイト数
 * Return Value : hex
 *******************************************************************************/
void int_to_aschex(int32_t value, uint8_t *asc_data, uint8_t n)
{
    uint8_t i, j;
    uint32_t mask = 0;

    for (i = 0; i < n; i++)
    {
        mask |= (0xF << (i * 4));
    }
    value &= mask;

    for (i = 0; i < n; i++)
    {
        j = n - i - 1;
        asc_data[j] = value % 16;
        if (asc_data[j] <= 9)
        {
            asc_data[j] += '0';        // ASCII(0-9)
        }
        else
        {
            asc_data[j] += ('A' - 10); // ASCII(A-F)
        }
        value /= 16;
    }
    asc_data[n] = '\0';
}

/*******************************************************************************
 * Function Name: aschex_to_int()
 * Description  :
 * Arguments    : *asc_data :
 *                n :バイト数
 * Return Value : hex
 *******************************************************************************/
int32_t aschex_to_int(uint8_t *asc_data, uint8_t n)
{
    int32_t value = 0;
    uint8_t i, j;

    for (i = 0; i < n; i++)
    {
        j = n - i - 1;
        if (asc_data[j] <= '9')
        {
            asc_data[j] -= '0';        // ASCII(0-9)
        }
        else
        {
            asc_data[j] -= ('A' - 10); // ASCII(A-F)
        }
        value += ((int32_t) asc_data[j] << (i * 4));
    }
    return value;
}

/*******************************************************************************
 * Function Name: float_to_aschex()
 * Description  : ルール2 数値->ASCII
 * Arguments    : value :
 *                *asc_data :
 *                n :バイト数
 * Return Value : hex
 *******************************************************************************/
void float_to_aschex(float value, uint8_t *asc_data, uint8_t n)
{
    int32_t value2 = 0;

    union{
        float f;
        unsigned int i;
    } data;

    data.f = value;
    value2 = data.i;    // float --> int変換

    int_to_aschex(value2, asc_data, n);    // uint型バイナリ --> ADCII変換
}

/*******************************************************************************
 * Function Name: aschex_to_float()
 * Description  :
 * Arguments    : *asc_data :
 *                n :バイト数
 * Return Value : hex
 *******************************************************************************/
float aschex_to_float(uint8_t *asc_data, uint8_t n)
{
    int32_t value = 0;
    float value2 = 0.0;

    union{
        float f;
        unsigned int i;
    } data;

    value = aschex_to_int(asc_data, n);    // ASCII --> uint型バイナリ変換

    data.i = value;

    value2 = data.f;    // int --> float変換

    return value2;
}

/*******************************************************************************
 * Function Name: byte_to_hex_ascii()
 * Description  :
 * Arguments    : *asc_data :
 *                n :バイト数
 * Return Value : hex
 *******************************************************************************/
static void byte_to_hex_ascii(uint8_t val, uint8_t *out)
{
    uint8_t hi = (val >> 4) & 0x0F;
    uint8_t lo = val & 0x0F;

    out[0] = (hi <= 9) ? ('0' + hi) : ('A' + hi - 10);
    out[1] = (lo <= 9) ? ('0' + lo) : ('A' + lo - 10);
}

#if 0
/*******************************************************************************
* Function Name: aschex_to_char()
* Description  : 
* Arguments    : *asc_data : 
* Return Value : hex
*******************************************************************************/
int aschex_to_char( int8_t *asc_data )
{
    int8_t value = 0;
    int8_t i,j;

    for( i=0; i<2; i++ )
    {
        j = 2 - i - 1;
        if( asc_data[j] <= '9' )
        {
            asc_data[j] -= '0';        // ASCII(0-9)
        } else {
            asc_data[j] -= ('A' - 10); // ASCII(A-F)
        }
        value += ((int)asc_data[j]<<(i*4));
    }
    return value;
}
#endif

/*******************************************************************************
 * Function Name: event_proc()
 * Description  : イベント送信処理
 * Arguments    :
 * Arguments    : None
 * Return Value : None
 *******************************************************************************/
void event_proc(void)
{
    //static uint8_t  gu8_evt_proc_stage = 0;
    static uint32_t c_timer;
    static uint8_t  c_retry = 0;
    //static uint8_t  f_first = 1;  // 最初の1回
    uint16_t bcc;
    uint8_t *pt1,*pt2,*pt3;
    uint8_t ii,flag=0;

    if( gu8_f_user_select != 0 ) // User2動作
    {
        if( gu32_c_event_wait != 0 )   // イベント送信可能待ちタイマ 10s
        {
            gu32_c_event_wait--;
            return;
        }
    }
    // 8/20条件追加
    if(( pi_high_i_of_h.trg != _TRG_ON_ )&&(gu8_f_12v_oc_off_h!=1))
    {

            if( (gu8_f_cmd_sc_recv == 0) ||  // 時刻設定(SET CLOCK)未受信時はイベント送信しない
            (SP_EVENT == _DISABLE_) ||   // イベント送信設定=無効
            ((gu8_f_ps_on == _OFF_))       // PS_ON=OFF
        )
        {
            gu8_evt_proc_stage = 0;
            return;
        }
    }


    if( gu32_c_cmd_sc_evt_delay != 0 )  // 時刻設定(SET CLOCK)受信してからD1受信するまでの2秒はイベント送信しない
    {
        gu32_c_cmd_sc_evt_delay--;
        gu8_evt_proc_stage = 0;
        return;
    }

    if( gu8_f_cmd_d1_recv != 0 )        // 状態情報(GET DATA1)受信?
    {
        gu8_f_cmd_d1_recv = 0;
        gs_event_data_old = gs_event_data; // 現時点->OLD(予約されたイベントの送信中止）
        gu8_f_envt_first = 0;
        gu8_evt_proc_stage = 0;
        return;
    }

    if( gu8_f_command_proc != 0 )    // コマンド処理中は中断
    {
        gu8_evt_proc_stage = 0;
        return;
    }

    switch (gu8_evt_proc_stage)
    {
        case 0:
            gs_event_data_new = gs_event_data;
            pt1 = (uint8_t*)&gs_event_data_new;
            pt2 = (uint8_t*)&gs_event_data_old;
            pt3 = (uint8_t*)&gs_event_data_change;
            if( memcmp( pt1, pt2, sizeof(event_data_t)) != 0 )
            {
                if( gu8_f_envt_first == 0 )   // 通常処理
                {
                    for( ii=0; ii<sizeof(event_data_t); ii++ )
                    {
                        pt3[ii] = pt1[ii] ^ pt2[ii];    // 変化点作成
                    }
                } else {
                    pt3[0] = 0x03; // 全変化点 ON
                    pt3[1] = 0x03;
                    pt3[2] = 0x07;
                    pt3[3] = 0x01;
                    pt3[4] = 0x01;
                    pt3[5] = 0x0F;
                    pt3[6] = 0x01;
                    pt3[7] = 0x07;
                    pt3[8] = 0x0F;
                    pt3[9] = 0x00;
                }
                gu8_d_sendbuf[0] = STX;     // STX
                gu8_d_sendbuf[1] = 'E';     // E
                gu8_d_sendbuf[2] = 'B';     // B
                for( ii=0; ii<sizeof(event_data_t); ii++ )
                {
                    gu8_d_sendbuf[3+ii] = bit_to_aschex(pt1[ii]);  // バッテリ異常情報 現時点
                }
                for( ii=0; ii<sizeof(event_data_t); ii++ )
                {
                    gu8_d_sendbuf[13+ii] = bit_to_aschex(pt3[ii]);  // バッテリ異常情報 変化点
                }
                gu8_d_sendbuf[23] = ETX;            // ETX
                bcc = calc_bcc(gu8_d_sendbuf, 26 - 2);
                gu8_d_sendbuf[24] = bcc >> 8;       // BCC
                gu8_d_sendbuf[25] = bcc & 0xff;
                c_retry = 0;
                gu8_evt_proc_stage = 1;
            }
            gu8_f_envt_first = 0;
            break;

        case 1:
            gu8_pos = uart_send_req(gu8_d_sendbuf, 26);
            gu8_f_evt_ack_nak_rcv = 0;     // 応答データクリア
            //c_timer = SND_RES_TIMER; // 200ms
            gu8_evt_proc_stage = 2;
            break;

        case 2:
            //if( --c_timer != 0 )
            //{
                if (send_complete_check(gu8_pos) == 0)
                {
                    c_timer = RES_WAIT_TIMER; // 200ms
                    //gu8_f_ent_ack_nak_rcv = 0;    // 応答データクリア
                    gu8_evt_proc_stage = 3;
            }
            //} else {                       // タイムオーバー
            //}
            break;

        case 3:
            if (--c_timer != 0)
            {
                if (gu8_f_evt_ack_nak_rcv == ACK) // ACK受信
                {
                    gu8_evt_proc_stage = 4;
                }
                else if (gu8_f_evt_ack_nak_rcv == NAK) // NAK受信
                {
                    if (++c_retry <= RETRY_NUM)
                    {
                        gu8_evt_proc_stage = 1;    // 再送
                    	error_log_request(206);
                    }
                    else
                    {
                        gu8_f_event_lost = _EVENT_LOST_NG_; // イベントロスト発生
                        gu8_evt_proc_stage = 4;
                    	error_log_request(208);
                    }
                }
            }
            else
            {                       // タイムオーバー
                if (++c_retry <= RETRY_NUM)
                {
                    gu8_evt_proc_stage = 1;    // 再送
                	error_log_request(179);
                }
                else
                {
                    gu8_f_event_lost = _EVENT_LOST_NG_; // イベントロスト発生
                    gu8_evt_proc_stage = 4;
                	error_log_request(208);
                }
            }
            break;

        case 4:
            gs_event_data_old = gs_event_data_new; // 現時点->OLD
            gu8_evt_proc_stage = 0;
            break;

        default:
            gu8_evt_proc_stage = 0;
            break;
    }
}

