#include "scpi_response_validation.h"
#include <errno.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define TEXT_CAPACITY 257u

static bool space(uint8_t c) { return c == ' ' || c == '\t'; }

/* strtod単独では受理するNaN/Inf/16進数や埋込みNULを、文法検査で拒否する。 */
bool meter_scpi_number(const uint8_t *bytes, size_t length, double *value) {
    if (!bytes || !value || length == 0u || length >= TEXT_CAPACITY) return false;
    size_t start = 0u;
    while (start < length && space(bytes[start])) start++;
    if (length >= 2u && bytes[length - 2u] == '\r' && bytes[length - 1u] == '\n') length -= 2u;
    while (length > start && space(bytes[length - 1u])) length--;
    size_t cursor = start;
    if (cursor < length && (bytes[cursor] == '+' || bytes[cursor] == '-')) cursor++;
    size_t digits = 0u;
    while (cursor < length && bytes[cursor] >= '0' && bytes[cursor] <= '9') { cursor++; digits++; }
    if (cursor < length && bytes[cursor] == '.') {
        cursor++;
        while (cursor < length && bytes[cursor] >= '0' && bytes[cursor] <= '9') { cursor++; digits++; }
    }
    if (digits == 0u) return false;
    if (cursor < length && (bytes[cursor] == 'E' || bytes[cursor] == 'e')) {
        cursor++;
        if (cursor < length && (bytes[cursor] == '+' || bytes[cursor] == '-')) cursor++;
        size_t exponent_start = cursor;
        while (cursor < length && bytes[cursor] >= '0' && bytes[cursor] <= '9') cursor++;
        if (cursor == exponent_start) return false;
    }
    if (cursor != length) return false;
    char text[TEXT_CAPACITY];
    memcpy(text, bytes + start, length - start);
    text[length - start] = '\0';
    errno = 0;
    char *end = NULL;
    double parsed = strtod(text, &end);
    if (end == text || *end != '\0' || errno == ERANGE || !isfinite(parsed)) return false;
    *value = parsed;
    return true;
}

/* CONF?は完成した1行全体を照合。機能・full-scale・分解能が不明ならREADへ進めない。 */
bool meter_scpi_confirms_20v(const uint8_t *bytes, size_t length) {
    if (!bytes || length < 2u || length > 256u ||
        bytes[length - 2u] != '\r' || bytes[length - 1u] != '\n') return false;
    length -= 2u;
    size_t start = 0u;
    while (start < length && space(bytes[start])) start++;
    while (length > start && space(bytes[length - 1u])) length--;
    if (start < length && bytes[start] == '"') {
        if (length - start < 2u || bytes[length - 1u] != '"') return false;
        start++;
        length--;
    }
    if (length - start < 5u || memcmp(bytes + start, "VOLT", 4u) != 0 || !space(bytes[start + 4u])) return false;
    start += 5u;
    size_t comma = start;
    while (comma < length && bytes[comma] != ',') comma++;
    if (comma == length) return false;
    double range = 0.0;
    double resolution = 0.0;
    if (!meter_scpi_number(bytes + start, comma - start, &range) ||
        !meter_scpi_number(bytes + comma + 1u, length - comma - 1u, &resolution)) return false;
    /* 既存.4の評価用19～21Vゲートを維持。量産の精度基準ではない。 */
    return range >= 19.0 && range <= 21.0 && resolution > 0.0;
}
