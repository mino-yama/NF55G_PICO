// Type_C2の列挙・HID原文を取得する単体評価FW。治具通信・測定・判定は行わない。
#include <stdint.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "pico/binary_info.h"
#include "hardware/clocks.h"
#include "hardware/uart.h"
#include "pio_usb.h"
#include "tusb.h"

bi_decl(bi_2pins_with_names(12,"Type_C2 D+",13,"Type_C2 D-"));
#if PROBE_UART_TX_PIN >= 0
bi_decl(bi_1pin_with_name(0,"Diagnostic UART0 TX 115200 8N1"));
#endif

// debuggerで停止後g_probeを保存。全イベントの時刻は起動後ms、長さは最大64。
// RAM保持は上書きせず満杯で破棄し、欠落数を明示する。電源OFFで消える。
typedef struct {
 uint32_t seq, ms;
 uint8_t kind, addr, instance, length;
 uint8_t data[64];
} probe_record_t;
typedef struct {
 uint32_t magic, version, count, dropped, heartbeat;
 probe_record_t records[256];
} probe_log_t;
volatile probe_log_t g_probe;
_Static_assert(sizeof(probe_record_t)==76, "record ABI");
_Static_assert(sizeof(probe_log_t)==19476, "log ABI");
static uint32_t sequence;
#if PROBE_UART_TX_PIN >= 0
static uint8_t tx[256];
static uint16_t tx_length, tx_offset;
static uint32_t uart_cursor;
#endif
static void record(uint8_t kind, uint8_t addr, uint8_t instance, const void *data, uint16_t len) {
 uint32_t seq=sequence++;
 if(g_probe.count>=256) { g_probe.dropped++; return; }
 if(len>64) len=64;
 probe_record_t r={.seq=seq,.ms=to_ms_since_boot(get_absolute_time()),
   .kind=kind,.addr=addr,.instance=instance,.length=(uint8_t)len};
 if(len && data) memcpy(r.data,data,len);
 g_probe.records[g_probe.count]=r;
 __compiler_memory_barrier();
 g_probe.count++;
}
static void request(uint8_t a,uint8_t i) {
 if(!tuh_hid_receive_report(a,i)) record(7,a,i,NULL,0);
}
void tuh_mount_cb(uint8_t a) {
 uint16_t v=0,p=0; tuh_vid_pid_get(a,&v,&p);
 uint8_t b[]={v&255,v>>8,p&255,p>>8}; record(2,a,0,b,4);
}
void tuh_umount_cb(uint8_t a) { record(3,a,0,NULL,0); }
void tuh_hid_mount_cb(uint8_t a,uint8_t i,const uint8_t *desc,uint16_t n) {
 uint8_t b[]={tuh_hid_interface_protocol(a,i),tuh_hid_get_protocol(a,i),n&255,n>>8};
 record(4,a,i,b,4);
 // 記述子は64byteずつ分割。欠落時はログ全体を完全な証跡としない。
 if(desc) for(uint16_t off=0;off<n;off+=64) record(5,a,i,desc+off,n-off>64?64:n-off);
 request(a,i);
}
void tuh_hid_umount_cb(uint8_t a,uint8_t i) { record(8,a,i,NULL,0); }
void tuh_hid_report_received_cb(uint8_t a,uint8_t i,const uint8_t *report,uint16_t len) {
 if(len>64) record(9,a,i,&len,sizeof(len));
 else record(6,a,i,report,len);
 request(a,i);
}
#if PROBE_UART_TX_PIN >= 0
// 任意の診断TXは受信・コマンド処理なし。FIFO空きの分だけ出しUSB処理を待たせない。
static void pump_uart(void) {
 if(tx_offset==tx_length && uart_cursor<g_probe.count) {
  probe_record_t r=g_probe.records[uart_cursor++];
  static const char hex[]="0123456789ABCDEF";
  tx_length=0; tx_offset=0;
  tx[tx_length++]='@';
  const uint8_t *b=(const uint8_t *)&r;
  for(unsigned j=0;j<sizeof(r);j++) {tx[tx_length++]=hex[b[j]>>4];tx[tx_length++]=hex[b[j]&15];}
  tx[tx_length++]='\n';
 }
 for(unsigned budget=0;budget<16 && tx_offset<tx_length && uart_is_writable(uart0);budget++)
  uart_putc_raw(uart0,tx[tx_offset++]);
}
#endif
int main(void) {
 memset((void *)&g_probe,0,sizeof(g_probe));
 g_probe.magic=0x51525042;g_probe.version=1;
 record(1,0,0,PROBE_FW_VERSION,sizeof(PROBE_FW_VERSION)-1);
 char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];
 pico_get_unique_board_id_string(id,sizeof(id)); record(11,0,0,id,strlen(id));
 if(!set_sys_clock_khz(120000,true)) { record(10,0,0,NULL,0);while(true)tight_loop_contents(); }
#if PROBE_UART_TX_PIN >= 0
 uart_init(uart0,115200);uart_set_format(uart0,8,1,UART_PARITY_NONE);
 uart_set_hw_flow(uart0,false,false);
 gpio_set_function(PROBE_UART_TX_PIN,GPIO_FUNC_UART);
 // USB開始前に版と個体IDだけを先に出す。Host処理中の送信は16byte上限。
 while(uart_cursor<g_probe.count || tx_offset<tx_length) { pump_uart(); tight_loop_contents(); }
#endif
 pio_usb_configuration_t cfg=PIO_USB_DEFAULT_CONFIG;
 cfg.pin_dp=12;cfg.pinout=PIO_USB_PINOUT_DPDM;
 if(!tuh_configure(1,TUH_CFGID_RPI_PIO_USB_CONFIGURATION,&cfg) || !tuh_init(1)) {
  record(10,0,0,NULL,0);
  while(true) {
#if PROBE_UART_TX_PIN >= 0
   pump_uart();
#endif
   tight_loop_contents();
  }
 }
 while(true) {
  tuh_task_ext(0,false);g_probe.heartbeat=to_ms_since_boot(get_absolute_time());
#if PROBE_UART_TX_PIN >= 0
  pump_uart();
#endif
 }
}
