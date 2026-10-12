"""単体試験用の生UART受信。importではGPIOを操作しない。
受信器は呼出し側で確認・初期化して渡す。read境界はフレーム境界ではない。
"""

def format_hex(data):
    return " ".join("%02X" % value for value in data)


def capture(receiver, duration_ms=None, chunk_size=64, emit=print, clock=None):
    """時刻付きHEXを表示。受信専用で、停止時は受信器を解放する。"""
    if chunk_size < 1 or (duration_ms is not None and duration_ms <= 0):
        raise ValueError("invalid chunk size or duration")
    if clock is None:
        import time
        clock = time
    total = reads = errors = 0
    start = clock.ticks_ms()
    try:
        emit("CAPTURE_START HEX_ONLY")
        while True:
            elapsed = clock.ticks_diff(clock.ticks_ms(), start)
            if duration_ms is not None and elapsed >= duration_ms:
                break
            if hasattr(receiver, "take_error"):
                error = receiver.take_error()
                if error:
                    errors += 1
                    emit("LOSS t_ms=%d error=%s" % (elapsed, error))
            count = receiver.any()
            if count:
                data = receiver.read(min(count, chunk_size))
                if data:
                    total += len(data)
                    reads += 1
                    emit("RX t_ms=%d n=%d hex=%s" %
                         (elapsed, len(data), format_hex(data)))
                    continue
            clock.sleep_ms(1)
    except KeyboardInterrupt:
        emit("CAPTURE_INTERRUPTED")
    finally:
        if hasattr(receiver, "close"):
            receiver.close()
        elif hasattr(receiver, "deinit"):
            receiver.deinit()
        emit("CAPTURE_STOP bytes=%d reads=%d errors=%d" %
             (total, reads, errors))
    return {"bytes": total, "reads": reads, "errors": errors}


def start_pio(duration_ms=None, buffer_size=4096):
    """CH9350単体試験をGP9受信・GP8送信禁止で開始する。

    GP4/GP5とUART1周辺回路はNF55G用として触らない。GP9をPIO0/SM0の
    115200bps/8N1受信に使い、GP8はCH9350へ送信しないHigh固定とする。
    既存runtimeを停止し、PIO0/SM0とGP8/GP9が空いている専用試験で使う。
    """
    if buffer_size < 64 or buffer_size & (buffer_size - 1):
        raise ValueError("buffer_size must be a power of two and at least 64")
    if duration_ms is not None and duration_ms <= 0:
        raise ValueError("duration_ms must be positive or None")
    from qr_pio_rx import QRPioRx
    receiver = QRPioRx(rx_pin=9, baudrate=115200, sm_id=0,
                       tx_idle_pin=8, buffer_size=buffer_size)
    return capture(receiver, duration_ms=duration_ms)
