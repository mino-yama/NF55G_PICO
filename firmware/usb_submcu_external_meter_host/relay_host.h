#ifndef RELAY_HOST_H
#define RELAY_HOST_H
#include "relay_wire.h"

typedef bool (*relay_emit_fn)(void *context, const x1_frame_t *frame);
typedef struct {
    uint8_t nonce[8];
    uint8_t session[16];
    uint8_t management_parent_nonce[8];
    uint8_t management_challenge[16];
    const char *chipid;
    const char *version;
    relay_emit_fn emit;
    void *context;
    bool bound, ready, fault, pending, tx_started, tx_done, response_done;
    uint32_t high_watermark, started_at;
    uint32_t management_high_watermark, management_info_request, management_info_at, management_reset_at;
    x1_frame_t request;
    uint8_t command[X1_PAYLOAD_MAX + 2u];
    size_t command_length;
    uint8_t response[X1_PAYLOAD_MAX];
    size_t response_length;
    uint8_t uart[X1_FRAME_MAX];
    size_t uart_length;
    bool uart_drop;
    bool management_parent_valid, management_info_valid;
    bool management_reset_waiting, management_reset_ack_sent, management_reset_due;
    bool management_reset_started;
    uint8_t previous;
    uint32_t rejected_frames;
} relay_host_t;

/* USB/UARTの実ドライバから分離し、同じengineをnative試験へ接続する。 */
size_t relay_usb_chunk_size(size_t remaining);
void relay_host_init(relay_host_t *host, const uint8_t nonce[8], const char *chipid,
                     const char *version, relay_emit_fn emit, void *context);
void relay_host_device_ready(relay_host_t *host, bool ready);
void relay_host_uart(relay_host_t *host, const uint8_t *data, size_t length, uint32_t now);
void relay_host_poll(relay_host_t *host, uint32_t now);
void relay_host_tx_started(relay_host_t *host);
void relay_host_tx_done(relay_host_t *host);
void relay_host_rx(relay_host_t *host, const uint8_t *data, size_t length, uint32_t now);
void relay_host_fail(relay_host_t *host, const char *reason);
void relay_host_reset_ack_transmitted(relay_host_t *host);
bool relay_host_reset_due(const relay_host_t *host);
bool relay_host_take_reset(relay_host_t *host);
bool relay_host_reset_ack_pending(const relay_host_t *host);
#endif
