#ifndef QR_ARM_GATE_H
#define QR_ARM_GATE_H

#include <stdbool.h>
#include <stdint.h>

#include "qr_alt_decoder.h"

#define QR_ARM_ID_SIZE 24
#define QR_ARM_ACK_RECORD 16
#define QR_ARM_TEXT_RECORD 17

typedef struct {
 char input[1 + QR_ARM_ID_SIZE];
 char id[QR_ARM_ID_SIZE];
 unsigned length;
 uint32_t requested_ms;
 bool pending, armed, have_id, drained;
} qr_arm_gate_t;

void qr_arm_gate_cancel(qr_arm_gate_t *gate);
void qr_arm_gate_input(qr_arm_gate_t *gate, uint8_t byte, uint32_t now);
bool qr_arm_gate_ack(qr_arm_gate_t *gate, const qr_alt_decoder_t *decoder);
bool qr_arm_gate_take(qr_arm_gate_t *gate);
void qr_arm_gate_expire(qr_arm_gate_t *gate, uint32_t now);

#endif
