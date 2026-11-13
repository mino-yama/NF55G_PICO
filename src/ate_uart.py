# ATE側UART0（GP0/GP1、57600bps・8N1）のバイト入出力を提供する。
# 行の組立てはate_server、コマンドの意味の解釈はparser/dispatcherが担当する。

"""ATE-side UART transport helpers.

The ATE channel is a byte transport only. Command parsing and execution stay in
the shared command core.
"""

try:
    from . import config
except ImportError:  # pragma: no cover
    import config


class UARTTransportError(RuntimeError):
    pass


class UARTByteTransport:
    def __init__(self, uart):
        self.uart = uart

    def any(self):
        return int(self.uart.any())

    def read(self, count=1):
        data = self.uart.read(count)
        if data is None:
            return b""
        return bytes(data)

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("ascii")
        return self.uart.write(bytes(data))

    def drain(self, limit=1024):
        data = b""
        while self.any() and len(data) < limit:
            data += self.read(min(self.any(), limit - len(data)))
        return data


def create_ate_uart():
    try:
        from machine import Pin, UART
    except ImportError as exc:  # pragma: no cover - host path
        raise UARTTransportError("machine UART unavailable") from exc
    uart = UART(0, baudrate=config.ATE_BAUDRATE, bits=config.ATE_BITS,
                parity=config.ATE_PARITY, stop=config.ATE_STOP_BITS, tx=Pin(0), rx=Pin(1),
                rxbuf=4096, timeout=0, timeout_char=0)
    return UARTByteTransport(uart)
