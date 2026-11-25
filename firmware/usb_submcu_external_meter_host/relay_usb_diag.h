#ifndef RELAY_USB_DIAG_H
#define RELAY_USB_DIAG_H
#include "relay_wire.h"
typedef struct {
    uint32_t calls, nak, data;
    uint8_t sync, pid, endpoint, active, toggle;
    uint16_t actual, total;
    uint32_t out_ack, out_nak, out_other;
    uint8_t out_pid, out_endpoint;
} relay_usb_snapshot_t;
/* TIMEOUTのEだけへ観測値を追記する。session/request/ambiguousは維持する。 */
bool relay_usb_diag_decorate(x1_frame_t *frame, const relay_usb_snapshot_t *snapshot);
#endif
