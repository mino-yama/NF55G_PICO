"""Shared lightweight data structures.

The classes intentionally avoid dataclasses so the same shapes remain easy to
port to MicroPython.
"""


class TransactionResult:
    __slots__ = (
        "ok",
        "cmd",
        "response_data",
        "error",
        "nak_reason",
        "command_retry_count",
        "response_retry_count",
        "ambiguous",
        "elapsed_ms",
        "raw_response",
    )

    def __init__(
        self,
        ok,
        cmd,
        response_data=b"",
        error=None,
        nak_reason=None,
        command_retry_count=0,
        response_retry_count=0,
        ambiguous=False,
        elapsed_ms=0,
        raw_response=b"",
    ):
        self.ok = bool(ok)
        self.cmd = cmd
        self.response_data = response_data
        self.error = error
        self.nak_reason = nak_reason
        self.command_retry_count = command_retry_count
        self.response_retry_count = response_retry_count
        self.ambiguous = bool(ambiguous)
        self.elapsed_ms = elapsed_ms
        self.raw_response = raw_response

    def as_dict(self):
        return {
            "ok": self.ok,
            "cmd": self.cmd,
            "response_data": self.response_data,
            "error": self.error,
            "nak_reason": self.nak_reason,
            "command_retry_count": self.command_retry_count,
            "response_retry_count": self.response_retry_count,
            "ambiguous": self.ambiguous,
            "elapsed_ms": self.elapsed_ms,
            "raw_response": self.raw_response,
        }


class Frame:
    __slots__ = ("cmd", "data", "raw")

    def __init__(self, cmd, data=b"", raw=b""):
        self.cmd = cmd
        self.data = data
        self.raw = raw

    def __repr__(self):
        return "Frame(cmd={!r}, data={!r})".format(self.cmd, self.data)


class CacheEntry:
    __slots__ = ("valid", "data", "source_cmd", "updated_ms")

    def __init__(self, valid=False, data=None, source_cmd=None, updated_ms=None):
        self.valid = bool(valid)
        self.data = data
        self.source_cmd = source_cmd
        self.updated_ms = updated_ms

    def metadata(self):
        return {
            "valid": self.valid,
            "source_cmd": self.source_cmd,
            "updated_ms": self.updated_ms,
        }
