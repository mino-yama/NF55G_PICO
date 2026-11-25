#include "tusb.h"
#include "relay_cdc_rx.h"

void relay_cdc_rx_service(relay_host_t *host, uint8_t index, uint32_t now) {
    // 64byteのendpoint長で打ち切ると、終端後の既着データを残したまま次Qを受け得る。
    // FIFO容量で処理量を制限し、既着の余分なデータも同じ応答検査へ渡す。
    uint8_t bytes[CFG_TUH_CDC_RX_BUFSIZE];
    uint32_t available = tuh_cdc_read_available(index);
    if (available == 0u) return;
    uint32_t count = tuh_cdc_read(index, bytes, sizeof(bytes));
    if (count > 0u) relay_host_rx(host, bytes, count, now);
}
