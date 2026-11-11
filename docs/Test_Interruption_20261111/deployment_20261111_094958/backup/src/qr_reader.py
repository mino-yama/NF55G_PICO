# QR単独試作用の受信状態管理。開始指示後の35文字を検証し、固定位置で6項目へ分割する。
# READYは受信形式の確認完了を示す。任意callbackで試験ログのS/Nへ渡せる。
# NF55GのSS書込み・製品判定・USBホストの選定とは分離する。

"""Isolated QR receive prototype; no NF55G/SS or production cache dependency."""

FIELDS = (("product_name", 8), ("item_code", 14), ("product_rev", 3),
          ("manufacture_year", 2), ("manufacture_week", 2), ("serial", 6))


def decode_qr(raw, allow_hyphen=True):
    if len(raw) != 35:
        raise ValueError("QR_LENGTH")
    for ch in raw:
        if not ("0" <= ch <= "9" or "A" <= ch <= "Z" or
                "a" <= ch <= "z" or (allow_hyphen and ch == "-")):
            raise ValueError("QR_CHAR")
    fields = {}
    offset = 0
    for name, length in FIELDS:
        fields[name] = raw[offset:offset + length]
        offset += length
    return fields


class QRReceiver:
    """now_ms must be monotonic, unwrapped milliseconds supplied by caller.

    Temporary field names only; valid means receive/format success, not product
    PASS or SS-ready. LF/CRLF framing is a test setting, not scanner discovery.
    """
    def __init__(self, timeout_ms=10000, allow_hyphen=True, on_ready=None):
        if timeout_ms <= 0:
            raise ValueError("timeout_ms")
        self.timeout_ms = timeout_ms
        self.allow_hyphen = allow_hyphen
        self.on_ready = on_ready
        self.state = "IDLE"
        self.raw = ""
        self.fields = None
        self.error = None
        self.started = None
        self._cr = False

    # 読取開始時に前回値を消す。新しい1件が完全に受信できるまで結果を公開しない。
    def start(self, now_ms):
        if self.state == "READING":
            return "ERR:QR_BUSY"
        self.raw = ""
        self.fields = None
        self.error = None
        self._cr = False
        self.started = now_ms
        self.state = "READING"
        return "OK:ARMED"

    def fail(self, code):
        self.fields = None
        self.error = code
        self.state = "ERROR"

    def tick(self, now_ms):
        if self.state == "READING" and now_ms - self.started >= self.timeout_ms:
            self.fail("QR_TIMEOUT")

    def cancel(self):
        self.raw = ""
        self.fields = None
        self.error = None
        self.state = "IDLE"

    def feed(self, data, now_ms):
        self.tick(now_ms)
        for value in data:
            if self.state != "READING":
                break
            if value == 10:
                try:
                    self.fields = decode_qr(self.raw, self.allow_hyphen)
                    self.state = "READY"
                    if self.on_ready is not None:
                        self.on_ready(self.raw)
                except ValueError as exc:
                    self.fail(str(exc))
            elif self._cr:
                self.fail("QR_TERMINATOR")
            elif value == 13:
                self._cr = True
            elif len(self.raw) >= 35:
                self.fail("QR_LENGTH")
            elif not (48 <= value <= 57 or 65 <= value <= 90 or
                      97 <= value <= 122 or
                      (self.allow_hyphen and value == 45)):
                self.fail("QR_CHAR")
            else:
                self.raw += chr(value)

    def command(self, line, now_ms, input_quiet=True):
        self.tick(now_ms)
        if line == "QR_SCAN":
            if self.state == "READING":
                return "ERR:QR_BUSY"
            if not input_quiet:
                return "ERR:QR_INPUT_BUSY"
            return self.start(now_ms)
        if line == "QR_CANCEL":
            self.cancel()
            return "OK"
        if line == "QR_STATUS?":
            return "ERR:" + self.error if self.error else self.state
        if line in ("QR_GET", "QR_DATA"):
            if self.state != "READY":
                return "ERR:CACHE_INVALID"
            if line == "QR_GET":
                return self.raw
            return ",".join(name + "=" + self.fields[name] for name, _ in FIELDS)
        if line in ("FU", "FW_UPDATE"):
            return "ERR:FU_DISABLED"
        return "ERR:UNKNOWN_COMMAND"
