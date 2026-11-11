# 通信中の記録はRAM Queueに積み、待機中に件数・時間条件で保存先へ書き出す。
# TEST/CONTの記録期間、保存エラー、破棄件数を管理する。MemorySDSinkはHost試験用。
# SD失敗でも試験期間を維持し、終了後の待機時だけ再認識する。

"""Non-blocking logger core and SD sink abstraction."""

import binascii


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


def _raw_ascii(raw_hex):
    try:
        raw = binascii.unhexlify(raw_hex)
    except (ValueError, TypeError):
        return ""
    return "".join(
        "\\\\" if byte == 92 else chr(byte) if 32 <= byte <= 126 else "\\x{:02X}".format(byte)
        for byte in raw
    )


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
        self.trial_high_watermark = 0

    def open(self, filename):
        self._raise_if_not_ok(opening=True)
        if filename in self.files:
            raise LoggerError('FILE_EXISTS')
        self.open_filename = filename
        if '_T' in filename:
            self.trial_high_watermark = max(self.trial_high_watermark,
                                            int(filename.rsplit('_T', 1)[1][:-4]))
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
        self.closed_filename = self.open_filename
        self.open_filename = None

    def reinit(self):
        self.status = SD_OK
        self.open_filename = None
        self.reinit_count += 1

    def rename_closed(self, filename):
        if self.open_filename is not None:
            raise LoggerError('OPEN_ERR')
        if filename in self.files:
            raise LoggerError('FILE_EXISTS')
        self.files[filename] = self.files.pop(self.closed_filename)
        self.closed_filename = filename

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
    def __init__(self, sd_sink=None, clock=None, queue_limit=256, flush_interval_ms=1000, flush_record_count=32,
                 rtc=None, busy=None, rollover_bytes=100 * 1024 * 1024):
        self.sd_sink = sd_sink or MemorySDSink()
        self.clock = clock
        self.rtc = rtc
        self.busy = busy or (lambda: False)
        self.timestamp_snapshot = ""
        self.rollover_bytes = rollover_bytes
        self.queue_limit = int(queue_limit)
        self.flush_interval_ms = int(flush_interval_ms)
        self.flush_record_count = int(flush_record_count)
        self.queue = []
        self.drop_count = 0
        self.active = False
        self.test_running = False
        self.last_test_sd_status = None
        self.session_serial = None
        self.last_test_filename = None
        self.trial_number = 0
        self.trial_id = None
        self.last_test_id = None
        self.test_history = []
        self.history_drop_count = 0
        self.test_drop_start = 0
        self.last_test_drop_count = None
        self.recovery_pending = False
        self.mode = None
        self.current_filename = None
        self.records_since_flush = 0
        self.last_flush_ms = self._ticks_ms()
        self.sd_status = getattr(self.sd_sink, 'status', SD_OK)

    def test_start(self):
        if self.busy() or self.test_running or self.active:
            return False
        # 完了履歴は次STARTでも維持する。試行番号はカード上の既存番号も避ける。
        self.trial_number = max(self.trial_number, getattr(self.sd_sink, 'trial_high_watermark', 0)) + 1
        self.trial_id = 'T{:06d}'.format(self.trial_number)
        self.session_serial = None
        self.drop_count += len(self.queue)
        self.queue = []
        self.test_drop_start = self.drop_count
        ok = self._start("TEST")
        # ログ開始失敗と試験期間は分離する。途中の再認識で試験を中断しない。
        self.test_running = True
        return ok

    def set_serial(self, serial):
        # 完了した当該試験のQRだけを受け付け、先頭ゼロを文字列のまま保持する。
        if not self.test_running:
            return False
        self.session_serial = None
        if not isinstance(serial, str) or len(serial) != 6 or not all('0' <= c <= '9' for c in serial):
            return False
        self.session_serial = serial
        return True

    def test_end(self, protocol_busy=False, reason='TEST_END'):
        if protocol_busy or self.busy():
            return False
        ending_test = self.test_running
        ending_session = self.test_running or self.active
        # 通信による延期時はQueueもファイルも旧試行に残し、新試行を開始しない。
        if self.active and self.sd_status == SD_OK:
            self.force_drain()
            if self.sd_status == SD_OK and (self.queue or self.records_since_flush):
                return False
        if self.busy():
            return False
        try:
            self.sd_sink.close()
        except LoggerError as exc:
            if str(exc) == 'COMM_BUSY':
                return False
            self.sd_status = str(exc)
        if ending_test:
            self.last_test_filename = None
        if ending_test and self.current_filename is not None:
            if self.session_serial is not None and self.sd_status == SD_OK:
                filename = self.session_serial + '_' + self.current_filename
                try:
                    self.sd_sink.rename_closed(filename)
                    self.current_filename = filename
                except (LoggerError, OSError) as exc:
                    self.sd_status = str(exc) if isinstance(exc, LoggerError) else SD_WRITE_ERR
            self.last_test_filename = self.current_filename
        self.active = False
        self.test_running = False
        self.mode = None
        self.current_filename = None
        self.drop_count += len(self.queue)
        self.queue = []
        self.records_since_flush = 0
        if ending_test:
            self.check_sd()
            self.last_test_sd_status = self.sd_status
            self.last_test_drop_count = self.drop_count - self.test_drop_start
            self.last_test_id = self.trial_id
            if len(self.test_history) >= 8:
                self.test_history.pop(0)
                self.history_drop_count += 1
            self.test_history.append(dict(trial_id=self.trial_id, reason=reason,
                                          filename=self.last_test_filename, serial=self.session_serial,
                                          sd_status=self.last_test_sd_status,
                                          drop_count=self.last_test_drop_count))
        self.recovery_pending = self.recovery_pending or ending_session
        return self.sd_status == SD_OK

    def log_cont_start(self):
        return self._start("CONT")

    def log_cont_stop(self, protocol_busy=False):
        return self.test_end(protocol_busy=protocol_busy)

    # 通信中にも呼ばれる入口。ここではRAMへの追加だけを行い、SDアクセスはしない。
    def log(self, timestamp="", category="", direction="", cmd="", event="", raw_ascii="", raw_hex="", bcc_rx="", bcc_calc="", bcc_ok="", cmd_retry="", rsp_retry="", result="", detail=""):
        if (self.test_running or self.active) and self.sd_status != SD_OK:
            self.drop_count += 1
            return False
        row = (
            str(timestamp or self.timestamp_snapshot),
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
        if protocol_busy or self.busy() or not self.active or self.sd_status != SD_OK or (not self.queue and not self.records_since_flush):
            return 0
        now = self._ticks_ms()
        due_by_count = len(self.queue) + self.records_since_flush >= self.flush_record_count
        due_by_time = now - self.last_flush_ms >= self.flush_interval_ms
        if not due_by_count and not due_by_time:
            return 0
        if (self.mode == 'CONT' and self.rtc is not None
                and getattr(self.sd_sink, 'file_bytes', 0) >= self.rollover_bytes):
            try:
                filename = self._filename()
                if filename == self.current_filename:
                    return 0
                self.sd_sink.close()
                self.sd_sink.open(filename)
                self.current_filename = filename
            except (LoggerError, ValueError, OSError) as exc:
                self.sd_status = str(exc)
                return 0
        return self._drain(flush=True)

    def force_drain(self):
        if self.busy() or self.sd_status != SD_OK:
            return 0
        return self._drain(flush=True, all_records=True)

    def status(self):
        return self.sd_status

    def check_sd(self):
        # 認識確認だけを行い、試験中の再マウントやフォーマットは行わない。
        if self.busy():
            return False
        if self.sd_status == SD_OK:
            try:
                self.sd_sink.usage()
            except (LoggerError, OSError) as exc:
                self.sd_status = str(exc) if isinstance(exc, LoggerError) else SD_MOUNT_ERR
        return self.sd_status == SD_OK

    def usage(self):
        return self.sd_sink.usage()

    # 復帰は試験・連続記録の外だけ。周期的な自動再試行は行わない。
    def service_recovery(self):
        if not self.recovery_pending or self.busy() or self.test_running or self.active:
            return False
        return self.reinit()

    def reinit(self):
        if self.busy() or self.test_running or self.active:
            return False
        self.recovery_pending = False
        self.drop_count += len(self.queue)
        self.queue = []
        self.records_since_flush = 0
        self.mode = None
        self.active = False
        self.current_filename = None
        try:
            self.sd_sink.reinit()
            self.sd_status = SD_OK
            return True
        except LoggerError as exc:
            self.sd_status = str(exc)
            return False

    def _start(self, mode):
        if self.busy() or self.test_running or self.active:
            return False
        try:
            filename = self._filename()
            if mode == 'TEST':
                # SD故障を次STARTだけで回復扱いにしない。再認識は明示終了後のみ。
                if self.sd_status != SD_OK:
                    return False
                filename = filename[:-4] + '_' + self.trial_id + '.csv'
            self.sd_sink.open(filename)
        except (LoggerError, ValueError, OSError) as exc:
            self.sd_status = str(exc)
            return False
        self.recovery_pending = False
        self.current_filename = filename
        if self.rtc is not None:
            self.timestamp_snapshot = filename[:15]
        self.mode = mode
        self.active = True
        self.records_since_flush = 0
        self.last_flush_ms = self._ticks_ms()
        self.sd_status = SD_OK
        return True

    # 書込みの各段階で通信を再確認する。通信待避なら未送信行と未flush件数を保持する。
    def _drain(self, flush=False, all_records=False):
        written = 0
        while self.queue and (all_records or written < self.flush_record_count):
            if self.busy():
                break
            row = self.queue[0]
            if row[1] == "NF55" and row[4] == "RAW" and not row[5] and row[6]:
                row = row[:5] + (_raw_ascii(row[6]),) + row[6:]
                if self.busy():
                    break
            try:
                self.sd_sink.write_record(row)
            except LoggerError as exc:
                if str(exc) == 'COMM_BUSY':
                    return written
                self.sd_status = str(exc)
                self.drop_count += len(self.queue)
                self.queue = []
                return written
            self.queue.pop(0)
            written += 1
            self.records_since_flush += 1
        if flush and self.records_since_flush and not self.busy():
            try:
                self.sd_sink.flush()
            except LoggerError as exc:
                if str(exc) == 'COMM_BUSY':
                    return written
                self.sd_status = str(exc)
                return written
            self.records_since_flush = 0
            self.last_flush_ms = self._ticks_ms()
        return written

    def _filename(self):
        if self.rtc is not None:
            return self.rtc.datetime() + '.csv'
        now = self._ticks_ms()
        return "{:014d}.csv".format(now)

    def _ticks_ms(self):
        if self.clock is None:
            return 0
        if hasattr(self.clock, "ticks_ms"):
            return self.clock.ticks_ms()
        return int(self.clock())
