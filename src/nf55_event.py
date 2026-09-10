"""Bounded EB storage, independent of all query caches."""

try:
    from .nf55_decode import decode_eb, DecodeError
except ImportError:
    from nf55_decode import decode_eb, DecodeError


class EventBuffer:
    def __init__(self, limit=32):
        self.limit = limit
        self.events = []
        self.drop_count = 0

    def append(self, raw, data, timestamp_ms):
        decoded = decode_eb(data)
        if any(char not in b"0123456789ABCDEFabcdef" for char in data):
            raise DecodeError("EB data is not ASCII HEX")
        if len(self.events) >= self.limit:
            self.drop_count += 1
            return
        self.events.append({"raw": raw, "data": decoded, "timestamp_ms": timestamp_ms})
