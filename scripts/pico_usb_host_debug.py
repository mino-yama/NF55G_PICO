"""Standalone EasyUSBHost TX0 diagnostic capture. Not production firmware."""
def start():
    import time
    import micropython
    from qr_pio_rx import QRPioRx
    micropython.alloc_emergency_exception_buf(128)
    rx = QRPioRx(rx_pin=10, baudrate=230400, sm_id=1,
                 tx_idle_pin=None, buffer_size=16384)
    total = 0
    started = time.ticks_ms()
    print("HOST_DEBUG READY GP10 physical14 230400 8N1 PIO0/SM1")
    print("Dedicated diagnostic: ATE QR_SCAN is not serviced. Ctrl-C stops.")
    try:
        while True:
            fault = rx.take_error()
            if fault:
                print("HOST_DEBUG LOSS", fault, "capture incomplete")
            data = rx.read(512)
            if data:
                total += len(data)
                # repr preserves byte values and non-UTF8 output without crashing.
                print("HOST_TX0", time.ticks_diff(time.ticks_ms(), started), repr(data))
            else:
                time.sleep_ms(1)
    except KeyboardInterrupt:
        print("HOST_DEBUG STOP bytes", total)
    finally:
        rx.close()
