#ifndef SCPI_RESPONSE_VALIDATION_H
#define SCPI_RESPONSE_VALIDATION_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* 単体評価FWの設定読戻し用。測定精度や製品合否は判定しない。 */
bool meter_scpi_number(const uint8_t *bytes, size_t length, double *value);
bool meter_scpi_confirms_20v(const uint8_t *bytes, size_t length);
#endif
