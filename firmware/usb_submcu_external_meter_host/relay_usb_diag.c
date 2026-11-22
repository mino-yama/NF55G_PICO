#include "relay_usb_diag.h"
#include <stdio.h>
#include <string.h>

bool relay_usb_diag_decorate(x1_frame_t *frame, const relay_usb_snapshot_t *s) {
    if (frame->kind != 'E' || frame->length < 10u ||
        memcmp(frame->payload, "TIMEOUT_", 8u) != 0 ||
        frame->payload[frame->length - 2u] != '|' ||
        frame->payload[frame->length - 1u] != '1') return false;
    char text[X1_PAYLOAD_MAX + 1u];
    int count = snprintf(text, sizeof(text),
        "%.*s_I%lu_N%lu_D%lu_S%02X_P%02X_EP%02X_H%u_K%u_L%u/%u|1",
        (int)frame->length - 2, (const char *)frame->payload,
        (unsigned long)s->calls, (unsigned long)s->nak, (unsigned long)s->data,
        (unsigned int)s->sync, (unsigned int)s->pid, (unsigned int)s->endpoint,
        (unsigned int)s->active, (unsigned int)s->toggle,
        (unsigned int)s->actual, (unsigned int)s->total);
    if (count <= 0 || (size_t)count > X1_PAYLOAD_MAX) return false;
    memcpy(frame->payload, text, (size_t)count);
    frame->length = (size_t)count;
    return true;
}
