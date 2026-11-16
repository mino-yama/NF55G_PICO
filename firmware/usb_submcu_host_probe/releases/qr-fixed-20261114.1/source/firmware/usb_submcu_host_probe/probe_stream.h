// 固定接続評価用の非blocking FIFO。単一main/callbackコンテキストからだけ使用する。
#pragma once
#include <stdbool.h>
#include <stdint.h>
#define PROBE_STREAM_CAPACITY 64
typedef struct {
 uint32_t seq, ms;
 uint8_t kind, addr, instance, length;
 uint8_t data[64];
} probe_record_t;
typedef struct {
 probe_record_t records[PROBE_STREAM_CAPACITY];
 uint32_t head, tail, count, dropped;
} probe_stream_t;
void probe_stream_init(probe_stream_t *s);
bool probe_stream_push(probe_stream_t *s, const probe_record_t *r);
bool probe_stream_pop(probe_stream_t *s, probe_record_t *r);
