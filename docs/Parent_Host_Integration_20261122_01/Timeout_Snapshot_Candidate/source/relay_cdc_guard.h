#ifndef RELAY_CDC_GUARD_H
#define RELAY_CDC_GUARD_H
#include "relay_host.h"

/* 対象CDCだけを監視する。unmount時に解除し旧接続からの通知を採用しない。 */
void relay_cdc_guard_bind(relay_host_t *host, uint8_t device_address);
#endif
