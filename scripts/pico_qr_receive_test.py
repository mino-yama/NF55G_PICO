"""Copy alongside qr_reader.py to Pico; invoke run(ate_uart, qr_rx).

This module does NOT allocate GPIO/UART or start on import. Do not run production
firmware concurrently. qr_rx is a separately wired nonblocking byte receiver;
using NF55G's UART requires physical isolation and explicit pin selection.
"""
from qr_reader import QRReceiver


def run(ate_uart, qr_rx, *, timeout_ms=10000, allow_hyphen=True):
    import time
    receiver = QRReceiver(timeout_ms, allow_hyphen)
    line = bytearray()
    dropping = False
    pending_tx = bytearray()
    clock = 0
    previous = time.ticks_ms()
    last_qr = 0
    shown = None
    rx_total = 0
    scan_rx = 0
    scan_preview = b""
    last_reported_rx = 0
    print("QR_TEST: LF/CRLF suffix required; waiting for ATE QR_SCAN")
    try:
        while True:
            now = time.ticks_ms()
            clock += time.ticks_diff(now, previous)
            previous = now
            fault = qr_rx.take_error() if hasattr(qr_rx, "take_error") else None
            if fault:
                last_qr = clock
                if receiver.state == "READING":
                    receiver.fail(fault)
            # Drain before ATE commands: pre-start input is never a new scan.
            n = qr_rx.any()
            if n:
                data = qr_rx.read(min(n, 64))
                if data:
                    last_qr = clock
                    rx_total += len(data)
                    if receiver.state == "READING":
                        scan_rx += len(data)
                        scan_preview = (scan_preview + data)[:64]
                    receiver.feed(data, clock)
            receiver.tick(clock)
            # One ATE byte per loop, bounded command/reply buffers.
            if len(pending_tx) < 512 and ate_uart.any():
                data = ate_uart.read(1)
                if data:
                    value = data[0]
                    if value == 10:
                        if dropping:
                            reply = "ERR:COMMAND_TOO_LONG"
                        elif not line or line[-1] != 13:
                            reply = "ERR:COMMAND_FRAME"
                        else:
                            try:
                                command = bytes(line[:-1]).decode("ascii")
                                quiet = not qr_rx.any() and clock - last_qr >= 100
                                reply = receiver.command(command, clock, quiet)
                                if reply == "OK:ARMED":
                                    scan_rx = 0
                                    scan_preview = b""
                            except UnicodeError:
                                reply = "ERR:COMMAND_CHAR"
                        pending_tx.extend((reply + "\r\n").encode("ascii"))
                        line = bytearray()
                        dropping = False
                    elif not dropping:
                        if len(line) >= 64:
                            dropping = True
                            line = bytearray()
                        else:
                            line.append(value)
            if pending_tx:
                sent = ate_uart.write(bytes(pending_tx[:64]))
                if sent:
                    pending_tx = pending_tx[sent:]
            marker = (receiver.state, receiver.started)
            if marker != shown:
                shown = marker
                print("QR_TEST", receiver.state, receiver.error or "")
                if receiver.state == "READY":
                    print("QR_RAW", receiver.raw)
                    for name, value in receiver.fields.items():
                        print(name, value)
                if receiver.state in ("READY", "ERROR"):
                    print("QR_DIAG scan_bytes", scan_rx, "raw_len", len(receiver.raw),
                          "wire", repr(scan_preview))
            # After a quiet period, report receipt even outside the scan window.
            # No pre-start data is promoted to the QR cache.
            if rx_total != last_reported_rx and clock - last_qr >= 100:
                last_reported_rx = rx_total
                print("QR_RX_TOTAL", rx_total, "state", receiver.state)
            time.sleep_ms(1)
    except KeyboardInterrupt:
        print("QR_TEST stopped; cache returned (RAM only)")
    return receiver


def start(timeout_ms=10000):
    """Dedicated wired test. Leaves production main.py and UART1 untouched."""
    from machine import Pin, UART
    from qr_pio_rx import QRPioRx
    qr_rx = QRPioRx()
    ate = None
    try:
        ate = UART(0, baudrate=115200, bits=8, parity=None, stop=1,
                   tx=Pin(0), rx=Pin(1), rxbuf=4096, timeout=0, timeout_char=0)
        return run(ate, qr_rx, timeout_ms=timeout_ms)
    finally:
        qr_rx.close()
        if ate is not None:
            ate.deinit()
