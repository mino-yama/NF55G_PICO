from machine import UART, Pin
import time

uart1 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

txData = b'RS232 receive test...\r\n'
uart0.write(txData)
time.sleep(0.1)
while True:
        #rxData = bytes()
    while uart0.any() > 0:    #Channel 0 is spontaneous and self-collecting
        rxData0 = uart0.read()
        uart0.write("{}".format(rxData0.decode('utf-8')))
        print(rxData0)
        if(uart0.any()==0):
            uart0.write("\r\n")
    while uart1.any() > 0:   #Channel 1 is spontaneous and self-collecting
        rxData1 = uart1.read()
        uart1.write("{}".format(rxData1.decode('utf-8')))
        print(rxData1)
        if(uart1.any()==0):
            uart1.write("\r\n")

