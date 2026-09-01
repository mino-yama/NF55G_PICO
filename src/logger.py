"""Non-blocking logger core and SD sink abstraction."""


CSV_FIELDS = (
    "timestamp",
    "category",
    "direction",
    "cmd",
    "event",
    "raw_ascii",
    "raw_hex",
    "bcc_rx",
    "bcc_calc",
    "bcc_ok",
    "cmd_retry",
    "rsp_retry",
    "result",
    "detail",
)

SD_OK = "OK"
SD_NO_CARD = "NO_CARD"
SD_MOUNT_ERR = "MOUNT_ERR"
SD_OPEN_ERR = "OPEN_ERR"
SD_WRITE_ERR = "WRITE_ERR"
SD_FULL = "FULL"


class LoggerError(RuntimeError):
    pass


class MemorySDSink:
    """Host-test SD sink with file-like sessions kept in memory."""

    def __init__(self, capacity_bytes=32 * 1024 * 1024 * 1024):
        self.capacity_bytes = int(capacity_bytes)
        self.files = {}
        self.status = SD_OK
        self.open_filename = None
        self.flush_count = 0
        self.close_count = 0
        self.reinit_count = 0
        self.write_count = 0
        self.flush_blocked = False

    def open(self, filename):
        self._raise_if_not_ok(opening=True)
        self.open_filename = filename
        self.files.setdefault(filename, [])

    def write_record(self, row):
        self._raise_if_not_ok()
        if self.open_filename is None:
            raise LoggerError(SD_OPEN_ERR)
        self.files[self.open_filename].append(row)
        self.write_count += 1

    def flush(self):
        self._raise_if_not_ok()
        if self.open_filename is None:
            raise LoggerError(SD_OPEN_ERR)
        self.flush_count += 1

    def close(self):
        if self.open_filename is not None:
            self.close_count += 1
        self.open_filename = None

    def reinit(self):
        self.status = SD_OK
        self.open_filename = None
        self.reinit_count += 1

    def usage(self):
        used = 0
        for rows in self.files.values():
            for row in rows:
                used += len(",".join(row))
        percent = 0.0
        if self.capacity_bytes > 0:
            percent = used * 100.0 / self.capacity_bytes
        return {"used_bytes": used, "capacity_bytes": self.capacity_bytes, "used_percent": percent}

    def _raise_if_not_ok(self, opening=False):
        if self.status != SD_OK:
            raise LoggerError(self.status)
        if self.flush_blocked and not opening:
            raise LoggerError(SD_WRITE_ERR)


class Logger:
    def __init__(self, sd_sink=None, clock=None, queue_limit=256, flush_interval_ms=1000, flush_record_count=32):
        self.sd_sink = sd_sink or MemorySDSink()
        self.clock = clock
        self.queue_limit = int(queue_limit)
        self.flush_interval_ms = int(flush_interval_ms)
        self.flush_record_count = int(flush_record_count)
        self.queue = []
        self.drop_count = 0
        self.active = False
        self.mode = None
        self.current_filename = None
        self.records_since_flush = 0
        self.last_flush_ms = self._ticks_ms()
        self.sd_status = SD_OK

    def test_start(self):
        return self._start("TEST")

    def test_end(self, protocol_busy=False):
        if protocol_busy:
            return False
        self.force_drain()
        self.sd_sink.close()
        self.active = False
        self.mode = None
        self.current_filename = None
        return True

    def log_cont_start(self):
        return self._start("CONT")

    def log_cont_stop(self, protocol_busy=False):
        return self.test_end(protocol_busy=protocol_busy)

    def log(self, timestamp="", category="", direction="", cmd="", event="", raw_ascii="", raw_hex="", bcc_rx="", bcc_calc="", bcc_ok="", cmd_retry="", rsp_retry="", result="", detail=""):
        row = (
            str(timestamp),
            str(category),
            str(direction),
            str(cmd),
            str(event),
            str(raw_ascii),
            str(raw_hex),
            str(bcc_rx),
            str(bcc_calc),
            str(bcc_ok),
            str(cmd_retry),
            str(rsp_retry),
            str(result),
            str(detail),
        )
        if len(self.queue) >= self.queue_limit:
            self.drop_count += 1
            return False
        self.queue.append(row)
        return True

    def service(self, protocol_busy=False):
        if protocol_busy or not self.active or not self.queue:
            return 0
        now = self._ticks_ms()
        due_by_count = len(self.queue) >= self.flush_record_count
        due_by_time = now - self.last_flush_ms >= self.flush_interval_ms
        if not due_by_count and not due_by_time:
            return 0
        return self._drain(flush=True)

    def force_drain(self):
        return self._drain(flush=True, all_records=True)

    def status(self):
        return self.sd_status

    def usage(self):
        return self.sd_sink.usage()

    def reinit(self):
        self.sd_sink.reinit()
        self.sd_status = SD_OK

    def _start(self, mode):
        if self.active:
            self.test_end()
        filename = self._filename()
        try:
            self.sd_sink.open(filename)
        except LoggerError as exc:
            self.sd_status = str(exc)
            return False
        self.current_filename = filename
        self.mode = mode
        self.active = True
        self.records_since_flush = 0
        self.last_flush_ms = self._ticks_ms()
        self.sd_status = SD_OK
        return True

    def _drain(self, flush=False, all_records=False):
        written = 0
        while self.queue and (all_records or written < self.flush_record_count):
            row = self.queue.pop(0)
            try:
                self.sd_sink.write_record(row)
            except LoggerError as exc:
                self.sd_status = str(exc)
                self.drop_count += 1 + len(self.queue)
                self.queue = []
                return written
            written += 1
            self.records_since_flush += 1
        if flush and written:
            try:
                self.sd_sink.flush()
            except LoggerError as exc:
                self.sd_status = str(exc)
                return written
            self.records_since_flush = 0
            self.last_flush_ms = self._ticks_ms()
        return written

    def _filename(self):
        now = self._ticks_ms()
        return "{:014d}.csv".format(now)

    def _ticks_ms(self):
        if self.clock is None:
            return 0
        if hasattr(self.clock, "ticks_ms"):
            return self.clock.ticks_ms()
        return int(self.clock())
