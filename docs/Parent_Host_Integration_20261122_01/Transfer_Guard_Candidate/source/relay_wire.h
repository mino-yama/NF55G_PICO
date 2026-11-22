#ifndef RELAY_WIRE_H
#define RELAY_WIRE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define X1_PAYLOAD_MAX 192u
#define X1_FRAME_MAX 512u

typedef struct {
    uint8_t session[16];
    uint32_t request;
    uint32_t timeout_ms;
    uint16_t length;
    char kind;
    uint8_t mode;
    uint8_t payload[X1_PAYLOAD_MAX];
} x1_frame_t;

/* 承認済みX1契約の構文層。接続/要求の意味照合はHost engineで行う。 */
uint32_t x1_crc32(const uint8_t *data, size_t length);
size_t x1_encode(const x1_frame_t *frame, uint8_t *output, size_t capacity);
bool x1_decode(const uint8_t *data, size_t length, x1_frame_t *frame);
#endif
