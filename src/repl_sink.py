"""Best-effort CSV mirror for a pollable MicroPython REPL stream."""

import sys

try:
    import select
except ImportError:  # pragma: no cover - minimal MicroPython builds
    select = None

try:
    from .logger import CSV_FIELDS
    from .sd_sink import csv_line
except ImportError:  # pragma: no cover
    from logger import CSV_FIELDS
    from sd_sink import csv_line


class ReplDebugSink:
    def __init__(self, stream=None, poller=None, queue_limit=4096, chunk_size=32):
        self.stream = stream if stream is not None else sys.stdout
        self.poller = poller
        self.pollout = getattr(select, 'POLLOUT', 4) if select is not None else 4
        self.poll_errors = ((getattr(select, 'POLLERR', 8) | getattr(select, 'POLLHUP', 16)
                     | getattr(select, 'POLLNVAL', 32))
                    if select is not None else 0)
        self.queue_limit = int(queue_limit)
        self.chunk_size = int(chunk_size)
        self.queue = []
        self.pending_bytes = 0
        self.drop_count = 0
        self.enabled = self.queue_limit > 0 and self.chunk_size > 0
        if self.poller is None and select is not None and hasattr(select, 'poll'):
            try:
                self.poller = select.poll()
            except (OSError, AttributeError):
                self.enabled = False
        if self.poller is None:
            self.enabled = False
        if self.enabled:
            try:
                self.poller.register(self.stream, self.pollout)
            except (OSError, AttributeError, TypeError):
                self.enabled = False

    def start(self):
        self._enqueue(csv_line(CSV_FIELDS))

    def write_record(self, row):
        return self._enqueue(csv_line(row))

    def service(self):
        if not self.enabled or not self.queue:
            return 0
        try:
            ready = self.poller.poll(0)
        except (OSError, AttributeError, TypeError):
            self._disable()
            return 0
        writable = False
        for item in ready:
            if item[0] is self.stream:
                if self.poll_errors and item[1] & self.poll_errors:
                    self._disable()
                    return 0
                writable = bool(item[1] & self.pollout)
                break
        if not writable:
            return 0

        text, offset = self.queue[0]
        chunk = text[offset:offset + self.chunk_size]
        try:
            written = self.stream.write(chunk)
        except (OSError, ValueError):
            self._disable()
            return 0
        if written is None:
            written = len(chunk)
        if not isinstance(written, int) or written <= 0:
            self._disable()
            return 0
        written = min(written, len(chunk))
        self.pending_bytes -= len(text[offset:offset + written].encode('utf-8'))
        offset += written
        if offset == len(text):
            self.queue.pop(0)
        else:
            self.queue[0] = (text, offset)
        return written

    def _enqueue(self, text):
        size = len(text.encode('utf-8'))
        if not self.enabled or self.pending_bytes + size > self.queue_limit:
            self.drop_count += 1
            return False
        self.queue.append((text, 0))
        self.pending_bytes += size
        return True

    def _disable(self):
        self.enabled = False
        self.drop_count += len(self.queue)
        self.queue = []
        self.pending_bytes = 0


def create_repl_sink(enabled):
    return ReplDebugSink() if enabled else None