"""NF55G frame and BCC helpers."""

try:
    from . import config
    from .models import Frame
except ImportError:  # pragma: no cover - MicroPython/simple path fallback
    import config
    from models import Frame


class FrameError(ValueError):
    """Raised when an NF55G frame is malformed or fails BCC validation."""


def _to_bytes(value):
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("ascii")
    return bytes(value)


def calculate_bcc(cmd, data=b""):
    """Calculate XOR BCC from CMD through ETX, excluding STX."""
    body = _to_bytes(cmd) + _to_bytes(data) + bytes((config.ETX,))
    bcc = 0
    for byte in body:
        bcc ^= byte
    return "{:02X}".format(bcc)


def build_frame(cmd, data=b""):
    cmd_b = _to_bytes(cmd)
    data_b = _to_bytes(data)
    if len(cmd_b) != 2:
        raise FrameError("CMD must be exactly 2 ASCII bytes")
    body = cmd_b + data_b + bytes((config.ETX,))
    return bytes((config.STX,)) + body + calculate_bcc(cmd_b, data_b).encode("ascii")


def parse_frame(raw, expected_cmd=None, expected_length=None):
    raw_b = _to_bytes(raw)
    if len(raw_b) < 6:
        raise FrameError("partial frame")
    if raw_b[0] != config.STX:
        raise FrameError("wrong STX")

    etx_index = raw_b.rfind(bytes((config.ETX,)))
    if etx_index < 3:
        raise FrameError("missing ETX")
    if len(raw_b) != etx_index + 3:
        raise FrameError("frame has trailing or missing BCC bytes")

    cmd_b = raw_b[1:3]
    data_b = raw_b[3:etx_index]
    bcc_b = raw_b[etx_index + 1 :]

    try:
        received_bcc = bcc_b.decode("ascii").upper()
        int(received_bcc, 16)
    except (ValueError, UnicodeError):
        raise FrameError("BCC is not ASCII HEX")

    expected_bcc = calculate_bcc(cmd_b, data_b)
    if received_bcc != expected_bcc:
        raise FrameError("BCC mismatch")

    cmd = cmd_b.decode("ascii")
    if expected_cmd is not None and cmd != expected_cmd:
        raise FrameError("unexpected CMD")
    if expected_length is not None and len(data_b) != expected_length:
        raise FrameError("unexpected DATA length")
    return Frame(cmd=cmd, data=data_b, raw=raw_b)
