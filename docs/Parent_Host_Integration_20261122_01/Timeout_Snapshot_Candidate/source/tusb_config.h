#ifndef USB_SUBMCU_EXTERNAL_METER_TUSB_CONFIG_H
#define USB_SUBMCU_EXTERNAL_METER_TUSB_CONFIG_H

#define CFG_TUSB_MCU OPT_MCU_RP2040
#define CFG_TUSB_OS OPT_OS_PICO
#define CFG_TUSB_DEBUG 0

#define CFG_TUH_ENABLED 1
#define CFG_TUH_RPI_PIO_USB 1
#define CFG_TUH_MAX_SPEED OPT_MODE_FULL_SPEED
#define CFG_TUH_DEVICE_MAX 1
#define CFG_TUH_HUB 0
#define CFG_TUH_HID 0
#define CFG_TUH_CDC 1
#define CFG_TUH_MSC 0
#define CFG_TUH_VENDOR 0
#define CFG_TUH_ENUMERATION_BUFSIZE 512
#define CFG_TUH_CDC_RX_BUFSIZE 256
// 固定SDK2.2.0のCDCはrx_ff_bufもTX_BUFSIZEで確保するため、RX容量以上を確保する。
// endpointの64byteとFIFO容量は別。短い応答の累積でもindexは進むので不一致は禁止。
#define CFG_TUH_CDC_TX_BUFSIZE 256
#if CFG_TUH_CDC_RX_BUFSIZE > CFG_TUH_CDC_TX_BUFSIZE
#error "Pinned TinyUSB CDC RX FIFO exceeds its TX-sized backing array"
#endif
#define CFG_TUH_CDC_RX_EPSIZE 64
#define CFG_TUH_CDC_TX_EPSIZE 64
#define CFG_TUH_CDC_LINE_CONTROL_ON_ENUM 0

#endif
