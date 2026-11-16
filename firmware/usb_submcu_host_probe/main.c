// Type_C2のHID原文と、既知形式の35文字復元を記録する単体評価FW。
// 診断版だけの処理であり、正式な治具通信・製品判定・NF55G書込みは行わない。
#include <stdint.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "pico/binary_info.h"
#include "hardware/clocks.h"
#include "hardware/uart.h"
#include "pio_usb.h"
#include "tusb.h"
#include "qr_alt_decoder.h"
#include "probe_stream.h"
#ifndef PROBE_CONTINUOUS
#define PROBE_CONTINUOUS 0
#endif

bi_decl(bi_2pins_with_names(12,"Type_C2 D+",13,"Type_C2 D-"));
#if PROBE_UART_TX_PIN >= 0
bi_decl(bi_1pin_with_name(0,"Diagnostic UART0 TX 115200 8N1"));
#endif

// debuggerで停止後g_probeを保存。全イベントの時刻は起動後ms、長さは最大64。
// UART調査版は1024件、旧RAM版は256件。満杯では上書きせず破棄数を加算する。
#ifndef PROBE_RECORD_CAPACITY
#define PROBE_RECORD_CAPACITY 256
#endif
#if PROBE_RECORD_CAPACITY == 1024 && !PROBE_CONTINUOUS
bi_decl(bi_program_feature("Diagnostic RAM capacity: 1024 records"));
#elif PROBE_CONTINUOUS
bi_decl(bi_program_feature("Fixed QR continuous FIFO; startup wait candidate 3000ms"));
#endif
// 旧原文版は有限RAM、新固定接続版は排出済み領域を再利用する。
#if !PROBE_CONTINUOUS
typedef struct {
 uint32_t magic, version, count, dropped, heartbeat;
 probe_record_t records[PROBE_RECORD_CAPACITY];
} probe_log_t;
volatile probe_log_t g_probe;
_Static_assert(sizeof(probe_record_t)==76, "record ABI");
_Static_assert(PROBE_RECORD_CAPACITY==256 || PROBE_RECORD_CAPACITY==1024, "supported capacity");
_Static_assert(sizeof(probe_log_t)==20+PROBE_RECORD_CAPACITY*76, "log ABI");
#else
static probe_stream_t stream;
static uint32_t heartbeat_ms, main_loops, qr_count, hid_count;
#endif
static uint32_t sequence;
#if PROBE_UART_TX_PIN >= 0
static uint8_t tx[256];
static uint16_t tx_length, tx_offset;
#if !PROBE_CONTINUOUS
static uint32_t uart_cursor;
#endif
static qr_alt_decoder_t qr_decoder;
static uint8_t qr_addr, qr_instance;
static bool qr_enabled;
#endif
static void record(uint8_t kind, uint8_t addr, uint8_t instance, const void *data, uint16_t len) {
 uint32_t seq=sequence++;
#if !PROBE_CONTINUOUS
 if(g_probe.count>=PROBE_RECORD_CAPACITY) { g_probe.dropped++; return; }
#endif
 if(len>64) len=64;
 probe_record_t r={.seq=seq,.ms=to_ms_since_boot(get_absolute_time()),
   .kind=kind,.addr=addr,.instance=instance,.length=(uint8_t)len};
 if(len && data) memcpy(r.data,data,len);
#if PROBE_CONTINUOUS
 (void)probe_stream_push(&stream,&r);
#else
 g_probe.records[g_probe.count]=r;
 __compiler_memory_barrier();
 g_probe.count++;
#endif
}
#if PROBE_UART_TX_PIN >= 0
static void qr_error(uint8_t addr, uint8_t instance, qr_alt_error_t error) {
 uint8_t value=(uint8_t)error; record(13,addr,instance,&value,1);
}
static void qr_disconnect(uint8_t addr) {
 if(qr_enabled && qr_addr==addr) {
  if(qr_decoder.active || qr_decoder.discarding)
   qr_error(qr_addr,qr_instance,QR_ALT_DISCONNECT);
  qr_alt_decoder_init(&qr_decoder); qr_enabled=false;
 }
}
#endif
static void request(uint8_t a,uint8_t i) {
 if(!tuh_hid_receive_report(a,i)) record(7,a,i,NULL,0);
}
void tuh_mount_cb(uint8_t a) {
 uint16_t v=0,p=0; tuh_vid_pid_get(a,&v,&p);
 uint8_t b[]={v&255,v>>8,p&255,p>>8}; record(2,a,0,b,4);
}
void tuh_umount_cb(uint8_t a) {
#if PROBE_UART_TX_PIN >= 0
 qr_disconnect(a);
#endif
 record(3,a,0,NULL,0);
}
void tuh_hid_mount_cb(uint8_t a,uint8_t i,const uint8_t *desc,uint16_t n) {
 uint8_t b[]={tuh_hid_interface_protocol(a,i),tuh_hid_get_protocol(a,i),n&255,n>>8};
 record(4,a,i,b,4);
 // 記述子は64byteずつ分割。欠落時はログ全体を完全な証跡としない。
 if(desc) for(uint16_t off=0;off<n;off+=64) record(5,a,i,desc+off,n-off>64?64:n-off);
#if PROBE_UART_TX_PIN >= 0
 uint16_t vid=0,pid=0;
 if(!qr_enabled && tuh_vid_pid_get(a,&vid,&pid) && qr_alt_profile_supported(vid,pid,desc,n)) {
  qr_alt_decoder_init(&qr_decoder); qr_addr=a; qr_instance=i; qr_enabled=true;
 } else qr_error(a,i,QR_ALT_PROFILE);
#endif
 request(a,i);
}
void tuh_hid_umount_cb(uint8_t a,uint8_t i) {
#if PROBE_UART_TX_PIN >= 0
 if(qr_enabled && qr_instance==i) qr_disconnect(a);
#endif
 record(8,a,i,NULL,0);
}
void tuh_hid_report_received_cb(uint8_t a,uint8_t i,const uint8_t *report,uint16_t len) {
#if PROBE_CONTINUOUS
 hid_count++;
 if(len>64) record(9,a,i,&len,sizeof(len));
#else
 if(len>64) record(9,a,i,&len,sizeof(len));
 else record(6,a,i,report,len);
#endif
#if PROBE_UART_TX_PIN >= 0
 if(qr_enabled && a==qr_addr && i==qr_instance) {
  char text[36];
  qr_alt_result_t result=qr_alt_decoder_feed(&qr_decoder,report,len,
                     to_ms_since_boot(get_absolute_time()),text);
  if(result==QR_ALT_TEXT) {
#if PROBE_CONTINUOUS
   qr_count++;
#endif
   record(12,a,i,text,QR_ALT_TEXT_LENGTH);
  }
  else if(result==QR_ALT_ERROR) qr_error(a,i,qr_decoder.error);
 }
#endif
 request(a,i);
}
#if PROBE_UART_TX_PIN >= 0
// 任意の診断TXは受信・コマンド処理なし。FIFO空きの分だけ出しUSB処理を待たせない。
static void pump_uart(void) {
#if PROBE_CONTINUOUS
 probe_record_t r;
 if(tx_offset==tx_length && probe_stream_pop(&stream,&r)) {
#else
 if(tx_offset==tx_length && uart_cursor<g_probe.count) {
  probe_record_t r=g_probe.records[uart_cursor++];
#endif
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
#if PROBE_CONTINUOUS
static void stage(uint8_t phase, uint32_t value) {
 uint8_t data[5]={phase,value&255,(value>>8)&255,(value>>16)&255,(value>>24)&255};
 record(15,0,0,data,sizeof(data));
 // 初期化が停止した場合も最後の段階を残す。USB開始前のmainだけで待つ。
 while(stream.count || tx_offset<tx_length) { pump_uart(); tight_loop_contents(); }
}
// USB IRQに触れず、mainから低頻度に動作・欠落数を記録する。
static void health(uint32_t now) {
 uint32_t flags=(qr_enabled?1u:0u)|(gpio_get(12)?2u:0u)|(gpio_get(13)?4u:0u)|8u;
 uint32_t data[]={main_loops,pio_usb_host_get_frame_number(),stream.dropped,qr_count,hid_count,flags};
 record(14,0,0,data,sizeof(data)); heartbeat_ms=now;
}
#endif
int main(void) {
#if PROBE_CONTINUOUS
 probe_stream_init(&stream);
#else
 memset((void *)&g_probe,0,sizeof(g_probe));
 g_probe.magic=0x51525042;g_probe.version=1;
#endif
 record(1,0,0,PROBE_FW_VERSION,sizeof(PROBE_FW_VERSION)-1);
 char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];
 pico_get_unique_board_id_string(id,sizeof(id)); record(11,0,0,id,strlen(id));
 if(!set_sys_clock_khz(120000,true)) { record(10,0,0,NULL,0);while(true)tight_loop_contents(); }
#if PROBE_UART_TX_PIN >= 0
 uart_init(uart0,115200);uart_set_format(uart0,8,1,UART_PARITY_NONE);
 uart_set_hw_flow(uart0,false,false);
 gpio_set_function(PROBE_UART_TX_PIN,GPIO_FUNC_UART);
 // USB開始前に版と個体IDだけを先に出す。Host処理中の送信は16byte上限。
#if PROBE_CONTINUOUS
 while(stream.count || tx_offset<tx_length) { pump_uart(); tight_loop_contents(); }
#else
 while(uart_cursor<g_probe.count || tx_offset<tx_length) { pump_uart(); tight_loop_contents(); }
#endif
#endif
#if PROBE_CONTINUOUS
 // 固定QRの起動待ち候補。効果は実機で確認し、原因と断定しない。
 stage(1,3000);
 uint32_t waiting_since=to_ms_since_boot(get_absolute_time());
 while((uint32_t)(to_ms_since_boot(get_absolute_time())-waiting_since)<3000) {
  pump_uart(); sleep_ms(1);
 }
 stage(2,0);
#endif
 pio_usb_configuration_t cfg=PIO_USB_DEFAULT_CONFIG;
 cfg.pin_dp=12;cfg.pinout=PIO_USB_PINOUT_DPDM;
 bool configured=tuh_configure(1,TUH_CFGID_RPI_PIO_USB_CONFIGURATION,&cfg);
#if PROBE_CONTINUOUS
 if(configured) stage(3,0);
#endif
 if(!configured || !tuh_init(1)) {
  record(10,0,0,NULL,0);
  while(true) {
#if PROBE_UART_TX_PIN >= 0
   pump_uart();
#endif
   tight_loop_contents();
  }
 }
#if PROBE_CONTINUOUS
 stage(4,0);
#endif
 while(true) {
  tuh_task_ext(0,false);
  uint32_t now=to_ms_since_boot(get_absolute_time());
#if PROBE_CONTINUOUS
  main_loops++;
  if((uint32_t)(now-heartbeat_ms)>=1000) health(now);
#else
  g_probe.heartbeat=now;
#endif
#if PROBE_UART_TX_PIN >= 0
  if(qr_enabled && qr_alt_decoder_poll(&qr_decoder,now)==QR_ALT_ERROR)
   qr_error(qr_addr,qr_instance,qr_decoder.error);
  pump_uart();
#endif
 }
}
