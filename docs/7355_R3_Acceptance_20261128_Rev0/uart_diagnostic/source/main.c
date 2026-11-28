// 単体診断専用。測定器USBを初期化せず、既存UART管理応答とnative USB観測を行う。
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "pico/unique_id.h"
#include "hardware/clocks.h"
#include "hardware/uart.h"
#include "relay_host.h"

static relay_host_t host;
static uint8_t output[2048];
static size_t output_length, output_offset;
static uint32_t rx_total, tx_total, emit_total;

static bool enqueue(void *context, const x1_frame_t *frame) {
    (void)context;
    if (output_offset != output_length) return false;
    output_length=x1_encode(frame,output,sizeof(output));
    output_offset=0;
    emit_total++;
    return output_length>0;
}

int main(void) {
    if (!set_sys_clock_khz(120000u,true)) return 1;
    stdio_init_all();
    uart_init(uart0,115200);
    uart_set_format(uart0,8,1,UART_PARITY_NONE);
    uart_set_hw_flow(uart0,false,false);
    gpio_set_function(0,GPIO_FUNC_UART);
    gpio_set_function(1,GPIO_FUNC_UART);
    gpio_pull_up(1);
    char chipid[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];
    pico_get_unique_board_id_string(chipid,sizeof(chipid));
    for(size_t i=0;chipid[i];i++) if(chipid[i]>='a' && chipid[i]<='f') chipid[i]-=32;
    // 診断用起動識別。量産FWのランダム起動IDとは区別する。
    uint64_t seed=time_us_64()|UINT64_C(0xD100000000000001);
    uint8_t nonce[8];
    for(size_t i=0;i<8;i++) nonce[i]=(uint8_t)(seed>>(56-8*i));
    relay_host_init(&host,nonce,chipid,"meter-host-relay-uartdiag-20261128.1",enqueue,NULL);
    uint32_t last=0;
    while(true) {
        uint8_t input[64];size_t count=0;
        while(count<sizeof(input) && uart_is_readable(uart0)) input[count++]=(uint8_t)uart_getc(uart0);
        uint32_t now=to_ms_since_boot(get_absolute_time());
        if(count) {
            rx_total+=(uint32_t)count;
            relay_host_uart(&host,input,count,now);
            if(stdio_usb_connected()) {
                printf("RX|");
                for(size_t i=0;i<count;i++) printf("%02X",input[i]);
                printf("\n");
            }
        }
        relay_host_poll(&host,now);
        size_t budget=32;
        while(output_offset<output_length && budget-- && uart_is_writable(uart0)) {
            uart_putc_raw(uart0,output[output_offset++]);tx_total++;
        }
        if(now-last>=1000 && stdio_usb_connected()) {
            last=now;
            printf("DIAG|id=%s;ms=%lu;rx=%lu;tx=%lu;emit=%lu;reject=%lu;pin1=%d\n",chipid,
                   (unsigned long)now,(unsigned long)rx_total,(unsigned long)tx_total,
                   (unsigned long)emit_total,(unsigned long)host.rejected_frames,gpio_get(1));
        }
        sleep_ms(1);
    }
}
