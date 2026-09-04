##-----------------------------------------
# RB01G command Conver Release Note.20240417
# CreateUser:M.Yamada
# CreateDate:2024/04/17
#
# UpdateUser:
# UpdateDate:
#-----------------------------------------
#Hardware composition
# ATE(Keisoku Giken : PW-800) interface:GPIB
# GPIB-RS232 converter(KIKUSUI : PIA5100)
# RP : Raspberry Pi Pico(MCU:RP2040)
# 2-Channel UART to RS232 Module for Raspberry Pi Pico, SP3232EEN Transceiver
# LAWICEL CANtoRS232 Dongle
#-----------------------------------------
#-----------------------------------------
# 通信規格	CAN 2.0B
# データフレーム	拡張29Bit
# 通信速度	125kbps
#
# CAN232初期設定	S4[CR]			…　CAN Setup 125Kbit.This command is only active if the CAN channel is closed.
#				O[CR]			…　CAN Open
#				C[CR]			…　CAN Close
#				Tiiiiiiiildd...[CR]	…　Transmit an extended (29bit) CAN frame.
#-----------------------------------------

from machine import UART,Pin,Timer
import time

#Comm port(UART) Configuration
#uart0(ATE-GPIB-PIA5100-RP)
uart1 = UART(0, baudrate=57600 ,tx=Pin(0), rx=Pin(1))
uart1.init(57600, bits=8, parity=None, stop=1)

#uart1(RP-CAN232-RB01G)
uart2 = UART(1, baudrate=57600 ,tx=Pin(4), rx=Pin(5))
uart2.init(57600, bits=8, parity=None, stop=1)

#Port setting
led = machine.Pin(25, machine.Pin.OUT)

rxData = bytes()  #UART1 受信仮置
rxData1 = str() #UART1 Receive variable
txData1 = str() #UART2 Send variable
rxData2 = str() #UART2 Receive variable
txData2 = str() #UART1 Send variable
rx_buffer1 = ''
rx_buffer2 = ''

#UART1(Receive) to UART2(Send)
def uart1_send_receive():
    global rxData1 #UART1 Receive variable
    global txData1 #UART2 Send variable
    global rx_buffer1

    #受信データ　PIA5100から送信される'\r'を無視,以外をrxData(仮置)からrxData1(#UART1 Receive variable)送る
    #受信データ　rxData1の条件により、rxData2からtxData2へデータ処理して送信
    while uart1.any():
        char = uart1.read(1)
        if char == b'\r' or char == b'\n':  		# メッセージの終端に到達
            if rx_buffer1: 					# バッファが空でない場合のみ処理
                rxData1 = rx_buffer1			# 受信メッセージをrxData1へ格納
                process_rx1_message(rx_buffer1)
            rx_buffer1 = ""  					# バッファをリセット
        else:
            rx_buffer1 += char.decode('utf-8')  	# バッファに追加

def process_rx1_message(rx_buffer1):
    global txData1 #UART2 Send variable

    try:
        #IDN Query処理(PIA5100認識処理)
        if rx_buffer1 == '*IDN?':
            txData1 = 'RP2040,Ver1.00'
            uart1.write(txData1.encode('utf-8') + b'\r')
            
        #電源ON/OFF(充電ON/OFF)
        #txData1 [OUT0_ON] ID:1307C08 電源ON(充電ON)_0
        elif rx_buffer1 == 'OUT0_ON':
            txData1 = 'T1307C08080200000000000055'

        #txData1 [OUT0_ON] ID:1307C08 電源OFF(充電OFF)_0
        elif rx_buffer1 == 'OUT0_OFF':
            txData1 = 'T1307C080802000000000000AA'
            
        #txData1 [OUT1_ON] ID:1307C08 電源ON(充電ON)_1
        elif rx_buffer1 == 'OUT1_ON':
            txData1 = 'T1307C08180200000000000055'
            
        #txData1 [OUT1_ON] ID:1307C08 電源OFF(充電OFF)_1
        elif rx_buffer1 == 'OUT1_OFF':
            txData1 = 'T1307C081802000000000000AA'

         #txData1 [OUT2_ON] ID:1307C08 電源ON(充電ON)_2
        elif rx_buffer1 == 'OUT2_ON':
            txData1 = 'T1307C08280200000000000055'
            
        #txData1 [OUT2_ON] ID:1307C08 電源OFF(充電OFF)_2
        elif rx_buffer1 == 'OUT2_OFF':
            txData1 = 'T1307C082802000000000000AA'
            
        #出力電圧・電流・状態　モニタ問い合わせ(ID:1307C08n_CMD:01)
        #txData1 [VOLT1?] ID:1307C081
        elif rx_buffer1== 'VOLT1?':
            txData1 = 'T1307C08180100000000000000'
 
         #txData1 [VOLT1?] ID:1307C082
        elif rx_buffer1== 'VOLT2?':
            txData1 = 'T1307C08280100000000000000'
            
        #txData1 [CURR?] ID:1307C081
        elif rx_buffer1 == 'CURR1?':
            txData1 = 'T1307C08180100000000000000'
            
        #txData1 [CURR?] ID:1307C082
        elif rx_buffer1 == 'CURR2?':
            txData1 = 'T1307C08280100000000000000'
            
        #txData1 [STATUS_nn?] ID:1307C081
        elif rx_buffer1.startswith('STATUS') and rx_buffer1.endswith('?'):
             txData1 = 'T1307C08180100000000000000' 

        #RSTユニット電流問い合わせ
        #txData1 [TR_CURR?] ID:1307C081
        elif rx_buffer1 == 'TR_CURR?':
            txData1 = 'T1307C08180101000000000000'
            
        #txData1 [ST_CURR?] ID:1307C081
        elif rx_buffer1 == 'ST_CURR?':
            txData1 = 'T1307C08180101000000000000'
            
        #txData1 [RS_CURR?] ID:1307C081
        elif rx_buffer1 == 'RS_CURR?':
            txData1 = 'T1307C08180101000000000000'
     
        #電圧・電流設定(ID:1307C081_CMD:00)
        # Check if the command matches 'VSETvvv.v_CSETaaa.a\r' format
        elif rx_buffer1.startswith('VSET') and '_CSET' in rx_buffer1:
            parts = rx_buffer1.split('_')
            if len(parts) == 2:
                vset_value = parts[0][4:]  	# 'VSETvvv.v'から数値部分を抽出
                cset_value = parts[1][4:-1]  	# 'CSETaaa.a'から数値部分を抽出

            # Construct the send command
                voltage = float(vset_value) * 1000  # 設定値(V)　x1000　変換
                current = float(cset_value) * 1000  # 設定値(A)　x1000　変換
            
                voltage_hex = f"{int(voltage):08X}"
                current_hex = f"{int(current):06X}"
            
                txData1 = f'T1307C081800{current_hex}{voltage_hex}'
                
        #txDta1 CAN232制御コマンド
        elif rx_buffer1 == 'S4' or rx_buffer1 == 'O' or rx_buffer1 == 'C':
            txData1 = rx_buffer1
            
    # 例外が発生してもループを続行し、次のデータ受信を待機
    except ValueError as e:
        # 数値変換に失敗した場合のエラー処理
        print("Received data has an invalid format:", e)
    except Exception as e:
        # その他の予期せぬエラーの処理
        print("An unexpected error occurred:", e)

    #Data Send
    uart2.write(txData1.encode('utf-8') + b'\r')
    #Receive to Send Data Disp.(rx:Receive tx:Send)
    #Time acquisition
#    now = 'Time ' + str(time.localtime()[0:3]) + str(time.localtime()[3]) + ':' + str(time.localtime()[4]) + ':' + str(time.localtime()[5])
    print('rx_DATA1 From ATE to RP --->',rxData1)
    print('tx_DATA1 From RP to RB01G --->',txData1)
    txData1 = "" #txData1クリア
    
#            log_file_uart1(rxData1,txData1, now)



#UART2(Receive) to UART1(Send)
def uart2_send_receive(rxData1):   
    global rx_buffer2
    
    #受信データ　rxData1の条件により、rxData2からtxData2へデータ処理して送信
    while uart2.any():
        char = uart2.read(1)
        if char == b'\r' or char == b'\n':  		# メッセージの終端に到達
            if rx_buffer2: 
                process_rx2_message(rxData1, rx_buffer2)
                rx_buffer2 = ''  				# バッファをリセット
        else:
            rx_buffer2 += char.decode('utf-8')  	# バッファに追加
            
def process_rx2_message(rxData1,rx_buffer2):
#    global rxData2 #UART2 Receive variable
    global txData2 #UART1 Send variable
    
    try:
        #rxData1 [VOLT?] ID:1307C08n CMD:01(出力電圧ﾓﾆﾀ問い合わせ) HEX'dddd' / 10
        if rxData1 == 'VOLT1?':
            txData2 = int(rx_buffer2[18:22], 16) / 10

        elif rxData1 == 'VOLT2?':
            txData2 = int(rx_buffer2[18:22], 16) / 10            
            
        #rxData1 [CURR?] ID:1307C081 CMD:01(出力電流ﾓﾆﾀ問い合わせ) HEX'dddd' / 10
        elif rxData1 == 'CURR1?':
            txData2 = int(rx_buffer2[14:18], 16) / 10

        elif rxData1 == 'CURR2?':
            txData2 = int(rx_buffer2[14:18], 16) / 10
            
        # RST Unit電流問い合わせ
        #rxData1 [RST_CURR?] ID:1307C081 CMD:01 byte1:01(RST Unit電流問い合わせ) TR:Byte 2-3,ST:Byte 4-5,RS:Byte 6-7　HEX'dddd' / 10
        elif rxData1 == 'TR_CURR?':
            txData2 = int(rx_buffer2[14:18], 16) / 10
        elif rxData1 == 'ST_CURR?':
            txData2 = int(rx_buffer2[18:22], 16) / 10
        elif rxData1 == 'RS_CURR?':
            txData2 = int(rx_buffer2[22:26], 16) / 10
            
        #状態の問い合わせ
        #rxData1 [STATUS_nn?] ID:1307C081 CMD:01 byte:6 byte:7 Bit情報を返す
        elif rxData1.startswith('STATUS_') and rxData1.endswith('?'):
        # Status 要求Bit情報の抽出
            try:
                nn = int(rxData1[7:9])
                if 0 <= nn <= 15:
                    # RB01Gから受信(rxData2)からByte6とByte7を抽出
                    Byte6 = int(rx_buffer2[20:22], 16)
                    Byte7 = int(rx_buffer2[22:24], 16)
                    # Byte6とByte7をBit列に変換して結合
                    status_bits = (Byte6 << 8) | Byte7
                    # 指定されたビットの値を取得
                    nn_bit = (status_bits >> nn) & 1
                    # 結果の設定
                    txData2 = f'STATUS_{nn:02}={nn_bit}'
                else:
                    raise ValueError("nn out of range")
            except ValueError as e:
                print(f"Error: {e}")
                txData1 = 'Error: Invalid command format'
                
    # 例外が発生してもループを続行し、次のデータ受信を待機
    except ValueError as e:
        # 数値変換に失敗した場合のエラー処理
        print("Received data has an invalid format:", e)
    except Exception as e:
        # その他の予期せぬエラーの処理
        print("An unexpected error occurred:", e)
            
    #Send Data Termination'\r'(CR) Add and send
#    if not txData2  == '' or txData2 == 'z': 
    uart1.write(str(txData2).encode('utf-8') + b'\r')
        
    #Receive to Send Data Disp.(rx:Receive tx:Send)
    print('rx_DATA2 From RB01G to RP -->',rx_buffer2)
    print('tx_DATA2 From RP to ATE -->',txData2)
    txData2 = '' #txData2クリア

#Time acquisition
    #now = 'Time ' + str(time.localtime()[0:3]) + str(time.localtime()[3]) + ':' + str(time.localtime()[4]) + ':' + str(time.localtime()[5])
    
#        log_file_uart2(rxData2,txData2, now)
    
# タイマーコールバック関数
def toggle_led(timer):
    led.value(not led.value())
    # LEDピンを設定
    led = machine.Pin(25, machine.Pin.OUT)
    # ソフトウェアタイマーを設定
    timer = machine.Timer(-1)
    timer.init(period=500, mode=machine.Timer.PERIODIC, callback=toggle_led)

def log_file_uart1(rxData1,txData1, now):
    file = open('log.txt', 'a')
    file.write(str('%-26s:rx_DATA1 From ATE to RP   　　%-20s' % (rxData1, now)) + '\n')
    file.write(str('%-26s:tx_DATA1 From RP to RB01G 　　%-20s' % (txData1.encode(), now)) + '\n')
    file.close()
    
def log_file_uart2(rxData2,txData2, now):
    file = open('log.txt', 'a')
    file.write(str('%-26s:rx_DATA2 From RB01G to RP 　　%-20s' % (rxData2, now))+ '\n')
    file.write(str('%-26s:tx_DATA2 From RP to ATE   　　%-20s' % (txData2, now)) + '\n')
    file.close()

while True:
    uart1_send_receive()
    uart2_send_receive(rxData1)
    