#include "relay_wire.h"
#include <stdio.h>
#include <string.h>

uint32_t x1_crc32(const uint8_t *data, size_t length) {
    uint32_t crc = 0xffffffffu;
    for (size_t i = 0u; i < length; i++) {
        crc ^= data[i];
        for (uint8_t bit = 0u; bit < 8u; bit++) crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return crc ^ 0xffffffffu;
}

static int hex_digit(uint8_t ch) {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    return -1;
}

static bool hex_value(const uint8_t *bytes, size_t size, uint32_t *value) {
    *value = 0u;
    for (size_t i = 0u; i < size; i++) {
        int digit = hex_digit(bytes[i]);
        if (digit < 0) return false;
        *value = (*value << 4) | (uint32_t)digit;
    }
    return true;
}

static bool valid_kind(char kind) {
    return kind != '\0' && strchr("HhQATRE", kind) != NULL;
}

size_t x1_encode(const x1_frame_t *frame, uint8_t *output, size_t capacity) {
    static const char hex[] = "0123456789ABCDEF";
    if (!frame || !output || frame->length > X1_PAYLOAD_MAX || !valid_kind(frame->kind) ||
        frame->mode > 1u || frame->timeout_ms > 10000u) return 0u;
    char session[33];
    for (size_t i = 0u; i < 16u; i++) {
        session[2u*i] = hex[frame->session[i] >> 4];
        session[2u*i+1u] = hex[frame->session[i] & 15u];
    }
    session[32] = '\0';
    int prefix = snprintf((char *)output, capacity, "@X1,%s,%08lX,%c,%u,%08lX,%04X,",
        session, (unsigned long)frame->request, frame->kind, frame->mode,
        (unsigned long)frame->timeout_ms, frame->length);
    if (prefix < 0 || (size_t)prefix >= capacity) return 0u;
    size_t used = (size_t)prefix;
    if (used + 2u*frame->length + 12u > capacity || used + 2u*frame->length + 11u > X1_FRAME_MAX) return 0u;
    for (size_t i = 0u; i < frame->length; i++) {
        output[used++] = (uint8_t)hex[frame->payload[i] >> 4];
        output[used++] = (uint8_t)hex[frame->payload[i] & 15u];
    }
    output[used++] = ',';
    uint32_t crc = x1_crc32(output, used);
    int suffix = snprintf((char *)output + used, capacity - used, "%08lX\r\n", (unsigned long)crc);
    return suffix == 10 ? used + 10u : 0u;
}

bool x1_decode(const uint8_t *data, size_t length, x1_frame_t *frame) {
    if (!data || !frame || length > X1_FRAME_MAX || length < 10u ||
        data[length - 2u] != '\r' || data[length - 1u] != '\n') return false;
    size_t start[9] = {0};
    size_t size[9] = {0};
    size_t field = 0u;
    for (size_t i = 0u; i < length - 2u; i++) {
        if (data[i] == ',') {
            if (field >= 8u) return false;
            size[field] = i - start[field];
            field++;
            start[field] = i + 1u;
        }
    }
    if (field != 8u) return false;
    size[8] = length - 2u - start[8];
    if (size[0] != 3u || memcmp(data, "@X1", 3u) != 0 || size[1] != 32u || size[2] != 8u ||
        size[3] != 1u || size[4] != 1u || size[5] != 8u || size[6] != 4u || size[8] != 8u) return false;
    uint32_t crc = 0u;
    uint32_t payload_length = 0u;
    if (!hex_value(data + start[8], 8u, &crc) || x1_crc32(data, start[8]) != crc ||
        !hex_value(data + start[2], 8u, &frame->request) ||
        !hex_value(data + start[5], 8u, &frame->timeout_ms) ||
        !hex_value(data + start[6], 4u, &payload_length)) return false;
    frame->kind = (char)data[start[3]];
    if (!valid_kind(frame->kind) || data[start[4]] < '0' || data[start[4]] > '1' ||
        frame->timeout_ms > 10000u || payload_length > X1_PAYLOAD_MAX || size[7] != payload_length * 2u) return false;
    frame->mode = data[start[4]] - '0';
    frame->length = (uint16_t)payload_length;
    uint32_t value = 0u;
    for (size_t i = 0u; i < 16u; i++) {
        if (!hex_value(data + start[1] + 2u*i, 2u, &value)) return false;
        frame->session[i] = (uint8_t)value;
    }
    for (size_t i = 0u; i < payload_length; i++) {
        if (!hex_value(data + start[7] + 2u*i, 2u, &value)) return false;
        frame->payload[i] = (uint8_t)value;
    }
    return true;
}
