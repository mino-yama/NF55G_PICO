// 外部測定器用の独立中継FW。GP0/GP1はX1フレーム専用で平文ログを混ぜない。
// USB設定だけを起動時に行い、IDN/レンジ/測定などは親の明示Q要求からのみ送る。
#include <stdio.h>
#include <string.h>
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/uart.h"
#include "pico/binary_info.h"
#include "pico/rand.h"
#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "pio_usb.h"
#include "tusb.h"
#include "relay_host.h"

bi_decl(bi_2pins_with_names(0, "Relay UART TX", 1, "Relay UART RX"));
bi_decl(bi_2pins_with_names(12, "USB-A D+", 13, "USB-A D-"));
bi_decl(bi_program_feature("X1 UART relay; explicit commands only; no automatic SCPI"));

#define OUTBOX_COUNT 8u
typedef struct { uint8_t bytes[X1_FRAME_MAX]; size_t length, offset; } output_t;
static output_t outbox[OUTBOX_COUNT];
static size_t output_head, output_tail, output_count;
static relay_host_t host;
static uint8_t cdc_index = TUSB_INDEX_INVALID_8;
static bool mounted, configured, control_done, control_started, usb_inflight;
static uint8_t control_step;
static uint32_t control_epoch, control_started_at;
static xfer_result_t control_result;
static size_t usb_offset;

static uint32_t now_ms(void) { return to_ms_since_boot(get_absolute_time()); }
static bool enqueue(void *context, const x1_frame_t *frame) {
    (void)context;
    if (output_count >= OUTBOX_COUNT) return false;
    output_t *entry = &outbox[output_head];
    entry->length = x1_encode(frame, entry->bytes, sizeof(entry->bytes));
    entry->offset = 0u;
    if (entry->length == 0u) return false;
    output_head = (output_head + 1u) % OUTBOX_COUNT;
    output_count++;
    return true;
}

static void service_uart(void) {
    uint8_t bytes[64];
    size_t count = 0u;
    while (count < sizeof(bytes) && uart_is_readable(uart0)) bytes[count++] = (uint8_t)uart_getc(uart0);
    if (count > 0u) relay_host_uart(&host, bytes, count, now_ms());
    size_t budget = 32u;
    while (output_count > 0u && budget > 0u && uart_is_writable(uart0)) {
        output_t *entry = &outbox[output_tail];
        uart_putc_raw(uart0, entry->bytes[entry->offset++]);
        budget--;
        if (entry->offset == entry->length) { output_tail = (output_tail + 1u) % OUTBOX_COUNT; output_count--; }
    }
}

static void control_callback(tuh_xfer_t *transfer) {
    if (!mounted || transfer->user_data != control_epoch) return;
    control_result = transfer->result;
    control_done = true;
}

void tuh_cdc_mount_cb(uint8_t index) {
    tuh_itf_info_t info = {0};
    uint16_t vid = 0u, pid = 0u;
    if (mounted || !tuh_cdc_itf_get_info(index, &info) || !tuh_vid_pid_get(info.daddr, &vid, &pid) ||
        vid != 0x1334u || pid != 0x0309u) return;
    cdc_index = index;
    mounted = true;
    configured = false;
    control_epoch++;
    control_step = 0u;
    control_started = false;
    control_done = false;
    usb_offset = 0u;
    usb_inflight = false;
}

void tuh_cdc_umount_cb(uint8_t index) {
    if (!mounted || index != cdc_index) return;
    mounted = false;
    configured = false;
    control_epoch++;
    cdc_index = TUSB_INDEX_INVALID_8;
    usb_inflight = false;
    relay_host_device_ready(&host, false);
}

void tuh_cdc_rx_cb(uint8_t index) { (void)index; }

void tuh_cdc_tx_complete_cb(uint8_t index) {
    if (!mounted || index != cdc_index || !usb_inflight) return;
    usb_inflight = false;
    relay_host_poll(&host, now_ms());
    if (host.pending && usb_offset == host.command_length) relay_host_tx_done(&host);
}

static void service_configuration(void) {
    static const cdc_line_coding_t coding = {
        .bit_rate = 9600u, .stop_bits = CDC_LINE_CODING_STOP_BITS_1,
        .parity = CDC_LINE_CODING_PARITY_NONE, .data_bits = 8u
    };
    if (!mounted || configured || control_step >= 2u || host.fault) return;
    if (!control_started) {
        control_done = false;
        control_started_at = now_ms();
        control_started = true;
        bool accepted = control_step == 0u
            ? tuh_cdc_set_line_coding(cdc_index, &coding, control_callback, control_epoch)
            : tuh_cdc_connect(cdc_index, control_callback, control_epoch);
        if (!accepted) relay_host_fail(&host, "CONTROL_START");
        return;
    }
    if (control_done) {
        control_started = false;
        control_done = false;
        if (control_result != XFER_RESULT_SUCCESS) { relay_host_fail(&host, "CONTROL_XFER"); return; }
        control_step++;
        if (control_step == 2u) { configured = true; relay_host_device_ready(&host, true); }
    } else if ((uint32_t)(now_ms() - control_started_at) >= 2000u) relay_host_fail(&host, "CONTROL_TIMEOUT");
}

static void service_usb_rx(void) {
    if (!mounted) return;
    uint8_t bytes[64];
    // UARTから新要求を採用する前に既着の未要求データを検出する。
    if (tuh_cdc_read_available(cdc_index) > 0u) {
        uint32_t count = tuh_cdc_read(cdc_index, bytes, sizeof(bytes));
        if (count > 0u) relay_host_rx(&host, bytes, count, now_ms());
    }
}

static void service_usb_tx(void) {
    if (!configured || !host.pending || host.fault || host.tx_done || usb_inflight) return;
    if (!host.tx_started) { usb_offset = 0u; relay_host_tx_started(&host); }
    if (usb_offset >= host.command_length) return;
    size_t count = relay_usb_chunk_size(host.command_length - usb_offset);
    if (tuh_cdc_write_available(cdc_index) < count) return;
    usb_inflight = true;
    uint32_t written = tuh_cdc_write(cdc_index, host.command + usb_offset, (uint32_t)count);
    usb_offset += written;
    if (written != count) { relay_host_fail(&host, "TX_PARTIAL"); return; }
    uint32_t flushed = tuh_cdc_write_flush(cdc_index);
    // write自体が転送開始済みならflushは0。完了callbackまで次を投入しない。
    if (flushed != 0u && flushed != count) relay_host_fail(&host, "TX_FLUSH");
}

int main(void) {
    if (!set_sys_clock_khz(120000u, true)) return 1;
    uart_init(uart0, 115200u);
    uart_set_format(uart0, 8u, 1u, UART_PARITY_NONE);
    uart_set_hw_flow(uart0, false, false);
    gpio_set_function(0u, GPIO_FUNC_UART);
    gpio_set_function(1u, GPIO_FUNC_UART);
    gpio_pull_up(1u);
    char chipid[2u * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1u];
    pico_get_unique_board_id_string(chipid, sizeof(chipid));
    for (size_t i = 0u; chipid[i] != '\0'; i++) if (chipid[i] >= 'a' && chipid[i] <= 'f') chipid[i] -= 32;
    uint64_t random;
    do { random = get_rand_64(); } while (random == 0u);
    uint8_t nonce[8];
    for (size_t i = 0u; i < sizeof(nonce); i++) nonce[i] = (uint8_t)(random >> (56u - 8u*i));
    relay_host_init(&host, nonce, chipid, HOST_FW_VERSION, enqueue, NULL);
    pio_usb_configuration_t pio = PIO_USB_DEFAULT_CONFIG;
    pio.pin_dp = 12u;
    pio.pinout = PIO_USB_PINOUT_DPDM;
    bool usb_ok = tuh_configure(1u, TUH_CFGID_RPI_PIO_USB_CONFIGURATION, &pio) && tuh_init(1u);
    if (!usb_ok) relay_host_fail(&host, "USB_INIT");
    while (true) {
        if (usb_ok) tuh_task_ext(0u, false);
        relay_host_poll(&host, now_ms());
        service_configuration();
        service_usb_rx();
        service_uart();
        service_usb_tx();
        tight_loop_contents();
    }
}
