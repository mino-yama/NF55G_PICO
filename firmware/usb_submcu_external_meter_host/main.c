#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/uart.h"
#include "pico/binary_info.h"
#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "pio_usb.h"
#include "tusb.h"
#include "scpi_response_validation.h"

#define DIAGNOSTIC_UART uart0
#define DIAGNOSTIC_TX_PIN 0u
#define DIAGNOSTIC_BAUDRATE 115200u
#define LOG_QUEUE_CAPACITY 12u
#define LOG_LINE_CAPACITY 192u
#define RESPONSE_CAPACITY 256u
#define RESPONSE_TIMEOUT_MS 2000u
#define CONTROL_TIMEOUT_MS 2000u
#define TARGET_VID 0x1334u
#define TARGET_PID 0x0309u
#ifndef HOST_VOLTAGE_TEST
#define HOST_VOLTAGE_TEST 0
#endif

bi_decl(bi_1pin_with_name(DIAGNOSTIC_TX_PIN, "Diagnostic UART TX"));
bi_decl(bi_2pins_with_names(12, "USB-A D+", 13, "USB-A D-"));
#if HOST_VOLTAGE_TEST
bi_decl(bi_program_feature("PIO USB-A Host; one-shot SCPI DC voltage evaluation"));
#else
bi_decl(bi_program_feature("PIO USB-A Host; CDC ACM identification probe"));
#endif

/* 診断専用。USB taskとUART Queueを巡回し、設定照合後に単発Queryを送る。 */
typedef enum {
    HOST_WAIT_DEVICE,
    HOST_CONFIGURING_LINE_CODING,
    HOST_CONFIGURING_CONTROL_LINES,
    HOST_READY,
    HOST_COMMAND_DELAY,
    HOST_QUERY_SENT,
    HOST_RESPONSE_COMPLETE,
    HOST_COMPLETE,
    HOST_FAILED
} host_state_t;

#if HOST_VOLTAGE_TEST
typedef struct {
    const char *command;
    const char *expected_fragment;
    uint32_t timeout_ms;
    bool expects_response;
} scpi_step_t;

static const scpi_step_t scpi_steps[] = {
    {"*IDN?", "ADC Corp.,7355,", RESPONSE_TIMEOUT_MS, true},
    {":SYST:ERR?", "0", RESPONSE_TIMEOUT_MS, true},
    {":INIT:CONT OFF", NULL, 0u, false},
    {":INIT:CONT?", "0", RESPONSE_TIMEOUT_MS, true},
    {":ABOR", NULL, 0u, false},
    {"*OPC?", "1", 10000u, true},
    {":SENS:FUNC \"VOLT:DC\"", NULL, 0u, false},
    {":SENS:FUNC?", "VOLT:DC", RESPONSE_TIMEOUT_MS, true},
    {":SENS:VOLT:DC:RANG:AUTO OFF", NULL, 0u, false},
    {":SENS:VOLT:DC:RANG:AUTO?", "0", RESPONSE_TIMEOUT_MS, true},
    {":SENS:VOLT:DC:RANG 20", NULL, 0u, false},
    {":SYST:ERR?", "0", RESPONSE_TIMEOUT_MS, true},
    {":CONF?", NULL, RESPONSE_TIMEOUT_MS, true},
    {":TRIG:SOUR IMM", NULL, 0u, false},
    {":TRIG:SOUR?", "IMM", RESPONSE_TIMEOUT_MS, true},
    {":TRIG:COUN 1", NULL, 0u, false},
    {":TRIG:COUN?", "1", RESPONSE_TIMEOUT_MS, true},
    {":SAMP:COUN 1", NULL, 0u, false},
    {":SAMP:COUN?", "1", RESPONSE_TIMEOUT_MS, true},
    {":TRIG:DEL 0", NULL, 0u, false},
    {":TRIG:DEL?", "0", RESPONSE_TIMEOUT_MS, true},
    {":SYST:ERR?", "0", RESPONSE_TIMEOUT_MS, true},
    {":READ?", NULL, 10000u, true},
    {":SYST:ERR?", "0", RESPONSE_TIMEOUT_MS, true}
};

static uint8_t scpi_step_index;
static uint32_t command_delay_started_at;
static uint32_t current_query_timeout_ms;
#endif

typedef struct {
    uint8_t bytes[LOG_LINE_CAPACITY];
    uint16_t length;
    uint16_t offset;
} log_entry_t;

static log_entry_t log_queue[LOG_QUEUE_CAPACITY];
static uint8_t log_head;
static uint8_t log_tail;
static uint8_t log_count;
static uint32_t log_dropped;
static uint8_t cdc_index = TUSB_INDEX_INVALID_8;
static uint8_t cdc_device_address;
static host_state_t host_state = HOST_WAIT_DEVICE;
static bool cdc_mounted;
static bool control_complete;
static bool control_start_failed;
static xfer_result_t control_result = XFER_RESULT_INVALID;
static uint8_t control_step;
static uint32_t control_started_at;
static bool rx_pending;
static uint8_t response[RESPONSE_CAPACITY];
static uint16_t response_length;
static uint32_t query_sent_at;
static bool response_overflow;
static bool response_previous_was_cr;

static void log_message(const char *format, ...) {
    if (log_count >= LOG_QUEUE_CAPACITY) {
        log_dropped++;
        return;
    }

    log_entry_t *entry = &log_queue[log_head];
    va_list args;
    va_start(args, format);
    int formatted = vsnprintf((char *)entry->bytes, sizeof(entry->bytes), format, args);
    va_end(args);

    if (formatted < 0) {
        entry->length = 0;
    } else if ((size_t)formatted >= sizeof(entry->bytes)) {
        entry->length = (uint16_t)(sizeof(entry->bytes) - 1u);
    } else {
        entry->length = (uint16_t)formatted;
    }
    if (entry->length < sizeof(entry->bytes) - 2u) {
        entry->bytes[entry->length++] = '\r';
        entry->bytes[entry->length++] = '\n';
    }
    entry->offset = 0;
    log_head = (uint8_t)((log_head + 1u) % LOG_QUEUE_CAPACITY);
    log_count++;
}

static void service_diagnostic_uart(void) {
    if (log_count == 0u) {
        return;
    }

    log_entry_t *entry = &log_queue[log_tail];
    uint8_t budget = 16u;
    while (budget > 0u && entry->offset < entry->length && uart_is_writable(DIAGNOSTIC_UART)) {
        uart_putc_raw(DIAGNOSTIC_UART, entry->bytes[entry->offset++]);
        budget--;
    }

    if (entry->offset >= entry->length) {
        log_tail = (uint8_t)((log_tail + 1u) % LOG_QUEUE_CAPACITY);
        log_count--;
    }
}

static void format_unique_id(char *output, size_t output_size) {
    pico_unique_board_id_t id;
    pico_get_unique_board_id(&id);
    size_t cursor = 0;
    for (size_t index = 0; index < sizeof(id.id) && cursor + 2u < output_size; index++) {
        int written = snprintf(output + cursor, output_size - cursor, "%02X", id.id[index]);
        if (written != 2) {
            break;
        }
        cursor += 2u;
    }
    if (output_size > 0u) {
        output[cursor < output_size ? cursor : output_size - 1u] = '\0';
    }
}

static void control_transfer_complete(tuh_xfer_t *transfer) {
    control_result = transfer->result;
    control_complete = true;
}

static void configure_line_coding(void) {
    cdc_line_coding_t line_coding = {
        .bit_rate = 9600u,
        .stop_bits = CDC_LINE_CODING_STOP_BITS_1,
        .parity = CDC_LINE_CODING_PARITY_NONE,
        .data_bits = 8u
    };

    control_step = 1u;
    control_complete = false;
    control_started_at = to_ms_since_boot(get_absolute_time());
    control_start_failed = !tuh_cdc_set_line_coding(cdc_index, &line_coding,
                                                     control_transfer_complete, 0u);
    if (!control_start_failed) {
        host_state = HOST_CONFIGURING_LINE_CODING;
    }
}

static void configure_control_lines(void) {
    control_step = 2u;
    control_complete = false;
    control_started_at = to_ms_since_boot(get_absolute_time());
    control_start_failed = !tuh_cdc_connect(cdc_index, control_transfer_complete, 0u);
    if (!control_start_failed) {
        host_state = HOST_CONFIGURING_CONTROL_LINES;
    }
}

void tuh_mount_cb(uint8_t device_address) {
    uint16_t vendor_id = 0u;
    uint16_t product_id = 0u;
    bool id_available = tuh_vid_pid_get(device_address, &vendor_id, &product_id);
    log_message("USB_MOUNT addr=%u vid=%04X pid=%04X id_valid=%u", device_address,
                vendor_id, product_id, id_available ? 1u : 0u);
}

void tuh_umount_cb(uint8_t device_address) {
    log_message("USB_UMOUNT addr=%u", device_address);
    if (cdc_mounted && device_address == cdc_device_address) {
        cdc_mounted = false;
        cdc_index = TUSB_INDEX_INVALID_8;
        host_state = HOST_WAIT_DEVICE;
    }
}

void tuh_mount_failed_cb(uint8_t device_address) {
    log_message("USB_MOUNT_FAILED addr=%u", device_address);
}

void tuh_cdc_mount_cb(uint8_t index) {
    tuh_itf_info_t info = {0};
    uint16_t vendor_id = 0u;
    uint16_t product_id = 0u;

    if (!tuh_cdc_itf_get_info(index, &info)) {
        log_message("CDC_INFO_FAILED idx=%u", index);
        return;
    }

    bool id_available = tuh_vid_pid_get(info.daddr, &vendor_id, &product_id);
    log_message("CDC_MOUNT idx=%u addr=%u itf=%u vid=%04X pid=%04X id_valid=%u",
                index, info.daddr, info.desc.bInterfaceNumber, vendor_id, product_id,
                id_available ? 1u : 0u);

    if (!id_available || vendor_id != TARGET_VID || product_id != TARGET_PID || cdc_mounted) {
        log_message("TARGET_REJECTED");
        return;
    }

    cdc_index = index;
    cdc_device_address = info.daddr;
    cdc_mounted = true;
    host_state = HOST_WAIT_DEVICE;
}

void tuh_cdc_umount_cb(uint8_t index) {
    log_message("CDC_UMOUNT idx=%u", index);
    if (cdc_mounted && index == cdc_index) {
        cdc_mounted = false;
        cdc_index = TUSB_INDEX_INVALID_8;
        host_state = HOST_WAIT_DEVICE;
    }
}

void tuh_cdc_rx_cb(uint8_t index) {
    if (cdc_mounted && index == cdc_index) {
        rx_pending = true;
    }
}

static void service_control_configuration(void) {
    if (!cdc_mounted) {
        return;
    }

    if (host_state == HOST_WAIT_DEVICE) {
        configure_line_coding();
        if (control_start_failed) {
            host_state = HOST_FAILED;
            log_message("LINE_CODING_START_FAILED");
        }
        return;
    }

    if ((host_state != HOST_CONFIGURING_LINE_CODING &&
         host_state != HOST_CONFIGURING_CONTROL_LINES) || !control_complete) {
        if ((host_state == HOST_CONFIGURING_LINE_CODING ||
             host_state == HOST_CONFIGURING_CONTROL_LINES) &&
            (uint32_t)(to_ms_since_boot(get_absolute_time()) - control_started_at) >= CONTROL_TIMEOUT_MS) {
            host_state = HOST_FAILED;
            log_message("CONTROL_XFER_TIMEOUT step=%u no_retry=1", control_step);
        }
        return;
    }

    control_complete = false;
    if (control_result != XFER_RESULT_SUCCESS) {
        host_state = HOST_FAILED;
        log_message("CONTROL_XFER_FAILED step=%u result=%u", control_step,
                    (unsigned)control_result);
        return;
    }

    if (control_step == 1u) {
        log_message("LINE_CODING_OK 9600,8,N,1");
        configure_control_lines();
        if (control_start_failed) {
            host_state = HOST_FAILED;
            log_message("CONTROL_LINES_START_FAILED");
        }
    } else {
        log_message("DTR_RTS_OK");
        host_state = HOST_READY;
    }
}

#if !HOST_VOLTAGE_TEST
static void send_identification_once(void) {
    static const uint8_t query[] = {'*', 'I', 'D', 'N', '?', '\r', '\n'};

    if (tuh_cdc_write_available(cdc_index) < sizeof(query)) {
        host_state = HOST_FAILED;
        log_message("IDN_TX_NO_SPACE");
        return;
    }

    uint32_t written = tuh_cdc_write(cdc_index, query, sizeof(query));
    if (written != sizeof(query)) {
        host_state = HOST_FAILED;
        log_message("IDN_TX_PARTIAL bytes=%lu", (unsigned long)written);
        return;
    }

    uint32_t flushed = tuh_cdc_write_flush(cdc_index);
    if (flushed != sizeof(query)) {
        host_state = HOST_FAILED;
        log_message("IDN_TX_FLUSH_INCOMPLETE bytes=%lu no_retry=1", (unsigned long)flushed);
        return;
    }

    query_sent_at = to_ms_since_boot(get_absolute_time());
    response_previous_was_cr = false;
    host_state = HOST_QUERY_SENT;
    log_message("IDN_TX_ONCE bytes=7 hex=2A49444E3F0D0A");
}
#endif

#if HOST_VOLTAGE_TEST
static void fail_scpi_step(const char *reason) {
    host_state = HOST_FAILED;
    log_message("SCPI_FAILED step=%u reason=%s no_retry=1", scpi_step_index, reason);
}

static void send_scpi_step(void) {
    if (scpi_step_index >= sizeof(scpi_steps) / sizeof(scpi_steps[0])) {
        host_state = HOST_COMPLETE;
        log_message("SCPI_SEQUENCE_COMPLETE steps=%u", scpi_step_index);
        return;
    }

    const scpi_step_t *step = &scpi_steps[scpi_step_index];
    uint8_t command[64];
    size_t command_length = strlen(step->command);
    if (command_length + 2u > sizeof(command)) {
        fail_scpi_step("COMMAND_TOO_LONG");
        return;
    }
    if (tuh_cdc_write_available(cdc_index) < command_length + 2u) {
        fail_scpi_step("TX_NO_SPACE");
        return;
    }

    memcpy(command, step->command, command_length);
    command[command_length] = '\r';
    command[command_length + 1u] = '\n';
    uint32_t total_length = (uint32_t)command_length + 2u;
    uint32_t written = tuh_cdc_write(cdc_index, command, total_length);
    if (written != total_length) {
        fail_scpi_step("TX_PARTIAL");
        return;
    }
    uint32_t flushed = tuh_cdc_write_flush(cdc_index);
    if (flushed != total_length) {
        fail_scpi_step("TX_FLUSH_INCOMPLETE");
        return;
    }

    log_message("SCPI_TX step=%u bytes=%lu query=%u cmd=%s", scpi_step_index,
                (unsigned long)total_length, step->expects_response ? 1u : 0u,
                step->command);
    if (step->expects_response) {
        response_length = 0u;
        response_overflow = false;
        response_previous_was_cr = false;
        rx_pending = false;
        current_query_timeout_ms = step->timeout_ms;
        query_sent_at = to_ms_since_boot(get_absolute_time());
        host_state = HOST_QUERY_SENT;
    } else {
        scpi_step_index++;
        command_delay_started_at = to_ms_since_boot(get_absolute_time());
        host_state = HOST_COMMAND_DELAY;
    }
}

static bool response_contains(const char *fragment) {
    size_t fragment_length = strlen(fragment);
    if (fragment_length == 0u || fragment_length > response_length) {
        return false;
    }

    for (size_t offset = 0u; offset + fragment_length <= response_length; offset++) {
        if (memcmp(response + offset, fragment, fragment_length) == 0) {
            return true;
        }
    }
    return false;
}

static bool response_matches_step(const scpi_step_t *step) {
    if (step->expected_fragment == NULL) {
        return true;
    }
    if (strcmp(step->command, "*IDN?") == 0) {
        return response_contains(step->expected_fragment);
    }
    if (strcmp(step->command, ":SYST:ERR?") == 0) {
        char text[RESPONSE_CAPACITY + 1u];
        size_t length = response_length;
        while (length > 0u && (response[length - 1u] == '\r' || response[length - 1u] == '\n')) {
            length--;
        }
        if (length >= sizeof(text)) {
            return false;
        }
        memcpy(text, response, length);
        text[length] = '\0';
        char *end = NULL;
        long error_code = strtol(text, &end, 10);
        return end != text && error_code == 0 && (*end == ',' || *end == '\0');
    }

    double actual_number = 0.0;
    double expected_number = 0.0;
    if (meter_scpi_number(response, response_length, &actual_number) &&
        meter_scpi_number((const uint8_t *)step->expected_fragment,
                           (uint16_t)strlen(step->expected_fragment), &expected_number)) {
        return actual_number == expected_number;
    }

    size_t expected_length = strlen(step->expected_fragment);
    size_t length = response_length;
    while (length > 0u && (response[length - 1u] == '\r' || response[length - 1u] == '\n')) {
        length--;
    }
    if (strcmp(step->command, ":SENS:FUNC?") == 0 && length >= 2u &&
        response[0] == '"' && response[length - 1u] == '"') {
        return length == expected_length + 2u &&
               memcmp(response + 1u, step->expected_fragment, expected_length) == 0;
    }
    return length == expected_length &&
           memcmp(response, step->expected_fragment, expected_length) == 0;
}

static void finish_scpi_response(void) {
    const scpi_step_t *step = &scpi_steps[scpi_step_index];
    if (response_overflow) {
        fail_scpi_step("RX_OVERFLOW");
        return;
    }
    if (strcmp(step->command, ":CONF?") == 0) {
        if (!meter_scpi_confirms_20v(response, response_length)) {
            fail_scpi_step("CONF_RANGE_NOT_20V");
            return;
        }
        log_message("SCPI_CONF_RANGE_OK nominal=20V");
    }
    if (!response_matches_step(step)) {
        fail_scpi_step("UNEXPECTED_RESPONSE");
        return;
    }

    scpi_step_index++;
    command_delay_started_at = to_ms_since_boot(get_absolute_time());
    host_state = HOST_COMMAND_DELAY;
}
#endif

static void service_response(void) {
    if (!cdc_mounted || !rx_pending) {
        return;
    }

    rx_pending = false;
    uint8_t bytes[64];
    while (tuh_cdc_read_available(cdc_index) > 0u) {
        uint32_t count = tuh_cdc_read(cdc_index, bytes, sizeof(bytes));
        if (count == 0u) {
            break;
        }

        for (uint32_t index = 0; index < count; index++) {
            if (response_length < sizeof(response)) {
                response[response_length++] = bytes[index];
            } else {
                response_overflow = true;
            }

            if (response_previous_was_cr && bytes[index] == '\n') {
                host_state = HOST_RESPONSE_COMPLETE;
            }
            response_previous_was_cr = bytes[index] == '\r';
        }

        char hex[129];
        size_t used = 0u;
        for (uint32_t index = 0; index < count && used + 2u < sizeof(hex); index++) {
            int written = snprintf(hex + used, sizeof(hex) - used, "%02X", bytes[index]);
            if (written != 2) {
                break;
            }
            used += 2u;
        }
        log_message("RX_RAW len=%lu hex=%s", (unsigned long)count, hex);

        if (host_state == HOST_RESPONSE_COMPLETE) {
#if HOST_VOLTAGE_TEST
            log_message("SCPI_RESPONSE_END step=%u total=%u overflow=%u",
                        scpi_step_index, response_length, response_overflow ? 1u : 0u);
#else
            log_message("IDN_RESPONSE_END=CRLF total=%u overflow=%u",
                        response_length, response_overflow ? 1u : 0u);
#endif
            return;
        }
    }
}

static void service_application(void) {
    service_control_configuration();

#if HOST_VOLTAGE_TEST
    if (host_state == HOST_READY ||
        (host_state == HOST_COMMAND_DELAY &&
         (uint32_t)(to_ms_since_boot(get_absolute_time()) - command_delay_started_at) >= 20u)) {
        send_scpi_step();
    } else if (host_state == HOST_QUERY_SENT) {
        service_response();
        if (host_state == HOST_RESPONSE_COMPLETE) {
            finish_scpi_response();
        } else if (host_state == HOST_QUERY_SENT &&
                   (uint32_t)(to_ms_since_boot(get_absolute_time()) - query_sent_at) >=
                       current_query_timeout_ms) {
            fail_scpi_step("QUERY_TIMEOUT");
        }
    }
#else
    if (host_state == HOST_READY) {
        send_identification_once();
    } else if (host_state == HOST_QUERY_SENT) {
        service_response();
        if (host_state == HOST_QUERY_SENT &&
            (uint32_t)(to_ms_since_boot(get_absolute_time()) - query_sent_at) >= RESPONSE_TIMEOUT_MS) {
            host_state = HOST_FAILED;
            log_message("IDN_TIMEOUT no_retry=1 partial=%u", response_length);
        }
    }
#endif
}

static void service_uart(void) {
    static uint32_t reported_drops;
    service_diagnostic_uart();
    if (log_dropped != reported_drops && log_count < LOG_QUEUE_CAPACITY) {
        reported_drops = log_dropped;
        log_message("LOG_DROP count=%lu", (unsigned long)log_dropped);
    }
}

int main(void) {
    char unique_id[2u * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1u];
    format_unique_id(unique_id, sizeof(unique_id));

    if (!set_sys_clock_khz(120000u, true)) {
        return 1;
    }

    uart_init(DIAGNOSTIC_UART, DIAGNOSTIC_BAUDRATE);
    uart_set_format(DIAGNOSTIC_UART, 8u, 1u, UART_PARITY_NONE);
    uart_set_hw_flow(DIAGNOSTIC_UART, false, false);
    gpio_set_function(DIAGNOSTIC_TX_PIN, GPIO_FUNC_UART);

    log_message("FW=%s CHIPID=%s SDK=2.2.0 USB=PIO_HOST", HOST_FW_VERSION, unique_id);

    pio_usb_configuration_t pio_config = PIO_USB_DEFAULT_CONFIG;
    pio_config.pin_dp = 12u;
    pio_config.pinout = PIO_USB_PINOUT_DPDM;

    if (!tuh_configure(1u, TUH_CFGID_RPI_PIO_USB_CONFIGURATION, &pio_config)) {
        log_message("PIO_CONFIG_FAILED");
        while (true) {
            service_uart();
            tight_loop_contents();
        }
    }

    if (!tuh_init(1u)) {
        log_message("USB_HOST_INIT_FAILED");
        while (true) {
            service_uart();
            tight_loop_contents();
        }
    }

    log_message("USB_HOST_READY rhport=1 dplus=12 dminus=13");
    while (true) {
        tuh_task_ext(0u, false);
        service_application();
        service_uart();
        tight_loop_contents();
    }
}