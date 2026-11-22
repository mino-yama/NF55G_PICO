// 固定SDKのCDC転送失敗は通常callbackへ届かないため、linker wrapで先に記録する。
// SDK原典・転送再試行は変更せず、対象Hostをfaultにして成否不明を親へ通知する。
#include "tusb.h"
#include "relay_cdc_guard.h"

static relay_host_t *guard_host;
static uint8_t guard_address;

void relay_cdc_guard_bind(relay_host_t *host, uint8_t device_address) {
    guard_host = host;
    guard_address = device_address;
}

bool __real_cdch_xfer_cb(uint8_t device_address, uint8_t endpoint,
                         xfer_result_t result, uint32_t transferred);

bool __wrap_cdch_xfer_cb(uint8_t device_address, uint8_t endpoint,
                         xfer_result_t result, uint32_t transferred) {
    if (result != XFER_RESULT_SUCCESS && guard_host != NULL && device_address == guard_address) {
        relay_host_fail(guard_host, (endpoint & 0x80u) != 0u ? "USB_RX_XFER" : "USB_TX_XFER");
        return false;
    }
    return __real_cdch_xfer_cb(device_address, endpoint, result, transferred);
}
