"""NF55G-side UART transport helpers.

This module owns physical UART byte I/O only. NF55G command meaning, retries,
and frame validation remain in `nf55_protocol.py`.
"""

try:
    from . import config
except ImportError:  # pragma: no cover
    import config


class NF55UARTError(RuntimeError):
    pass


class NF55UARTTransport:
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


def _micropython_parity(value):
    if value is None:
        return None
    text = str(value).lower()
    if text == "even":
        return 0
    if text == "odd":
        return 1
    raise NF55UARTError("unsupported parity")


def create_nf55_uart():
    try:
        from machine import Pin, UART
    except ImportError as exc:  # pragma: no cover - host path
        raise NF55UARTError("machine UART unavailable") from exc
    uart = UART(
        1,
        baudrate=config.NF55_BAUDRATE,
        bits=config.NF55_BITS,
        parity=_micropython_parity(config.NF55_PARITY),
        stop=config.NF55_STOP_BITS,
        tx=Pin(4),
        rx=Pin(5),
    )
    return NF55UARTTransport(uart)

