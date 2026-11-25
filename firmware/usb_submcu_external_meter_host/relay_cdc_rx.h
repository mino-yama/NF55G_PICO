#ifndef RELAY_CDC_RX_H
#define RELAY_CDC_RX_H
#include "relay_host.h"

/* mount中に、UART要求の受付より先に呼ぶ。既着FIFOを一括検査する。 */
void relay_cdc_rx_service(relay_host_t *host, uint8_t index, uint32_t now);
#endif
