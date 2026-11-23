#ifndef QR_ALT_DECODER_H
#define QR_ALT_DECODER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32) && defined(QR_ALT_TEST_DLL)
#define QR_ALT_API __declspec(dllexport)
#else
#define QR_ALT_API
#endif

#define QR_ALT_TEXT_LENGTH 35
// 診断用の暫定inter-report期限。正式ATE／親子UARTのtimeoutではない。
#define QR_ALT_IDLE_TIMEOUT_MS 5000u

typedef enum { QR_ALT_NONE=0, QR_ALT_TEXT=1, QR_ALT_ERROR=2 } qr_alt_result_t;
typedef enum {
 QR_ALT_OK=0, QR_ALT_REPORT_SIZE=1, QR_ALT_RESERVED=2,
 QR_ALT_MODIFIER=3, QR_ALT_KEY_COUNT=4, QR_ALT_KEY=5,
 QR_ALT_DIGITS=6, QR_ALT_CHARACTER=7, QR_ALT_LENGTH=8,
 QR_ALT_TIMEOUT=9, QR_ALT_PROFILE=10, QR_ALT_DISCONNECT=11
} qr_alt_error_t;

typedef struct {
 char text[QR_ALT_TEXT_LENGTH+1];
 uint32_t value, last_ms;
 uint8_t length, digits, previous_modifier, previous_key;
 bool active, discarding;
 qr_alt_error_t error;
} qr_alt_decoder_t;

QR_ALT_API bool qr_alt_profile_supported(uint16_t vid, uint16_t pid,
                                       const uint8_t *descriptor, size_t size);
QR_ALT_API void qr_alt_decoder_init(qr_alt_decoder_t *state);
QR_ALT_API qr_alt_result_t qr_alt_decoder_feed(qr_alt_decoder_t *state,
 const uint8_t *report, size_t size, uint32_t now_ms, char output[36]);
QR_ALT_API qr_alt_result_t qr_alt_decoder_poll(qr_alt_decoder_t *state, uint32_t now_ms);

#endif
