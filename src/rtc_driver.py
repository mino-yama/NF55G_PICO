"""Pico-side RTC driver abstraction for DS3231.

Host tests use `FakeRTCDevice`; hardware I2C access is added in the Pico/HIL
phase. This module is intentionally separate from NF55G `SC` clock sync.
"""


class RTCError(ValueError):
    pass


class RTCDateTime:
    __slots__ = ("year", "month", "day", "hour", "minute", "second")

    def __init__(self, year, month, day, hour, minute, second):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        self.hour = int(hour)
        self.minute = int(minute)
        self.second = int(second)
        self._validate()

    @classmethod
    def parse_ate(cls, value):
        text = str(value)
        if len(text) != 15 or text[8] != "_":
            raise RTCError("RTC_SET format must be YYYYMMDD_HHMMSS")
        digits = text[:8] + text[9:]
        if not digits.isdigit():
            raise RTCError("RTC_SET value must be decimal digits")
        return cls(
            int(text[0:4]),
            int(text[4:6]),
            int(text[6:8]),
            int(text[9:11]),
            int(text[11:13]),
            int(text[13:15]),
        )

    def date(self):
        return "{:04d}{:02d}{:02d}".format(self.year, self.month, self.day)

    def time(self):
        return "{:02d}{:02d}{:02d}".format(self.hour, self.minute, self.second)

    def datetime(self):
        return "{}_{}".format(self.date(), self.time())

    def _validate(self):
        if self.year < 2000 or self.year > 2099:
            raise RTCError("year out of range")
        if self.month < 1 or self.month > 12:
            raise RTCError("month out of range")
        max_day = _days_in_month(self.year, self.month)
        if self.day < 1 or self.day > max_day:
            raise RTCError("day out of range")
        if self.hour < 0 or self.hour > 23:
            raise RTCError("hour out of range")
        if self.minute < 0 or self.minute > 59:
            raise RTCError("minute out of range")
        if self.second < 0 or self.second > 59:
            raise RTCError("second out of range")


class FakeRTCDevice:
    def __init__(self, present=True, initial=None):
        self.present = bool(present)
        self.dt = initial or RTCDateTime(2026, 9, 1, 0, 0, 0)
        self.set_count = 0
        self.read_count = 0
        self.check_count = 0

    def read_datetime(self):
        if not self.present:
            raise RTCError("NO_RTC")
        self.read_count += 1
        return self.dt

    def set_datetime(self, dt):
        if not self.present:
            raise RTCError("NO_RTC")
        self.dt = dt
        self.set_count += 1

    def check(self):
        self.check_count += 1
        if not self.present:
            return False
        self.read_datetime()
        return True


class DS3231I2CDevice:
    """DS3231 register access for Pico/MicroPython I2C0 GP20/GP21."""

    ADDRESS = 0x68
    STATUS_REG = 0x0F
    OSF_BIT = 0x80

    def __init__(self, i2c=None, address=ADDRESS):
        self.address = int(address)
        if i2c is None:
            try:
                from machine import I2C, Pin
            except ImportError as exc:  # pragma: no cover - host path
                raise RTCError("machine I2C unavailable") from exc
            i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=100000)
        self.i2c = i2c

    def read_datetime(self):
        regs = self._read_regs(0x00, 7)
        return RTCDateTime(
            2000 + _bcd_to_dec(regs[6]),
            _bcd_to_dec(regs[5] & 0x1F),
            _bcd_to_dec(regs[4] & 0x3F),
            _bcd_to_dec(regs[2] & 0x3F),
            _bcd_to_dec(regs[1] & 0x7F),
            _bcd_to_dec(regs[0] & 0x7F),
        )

    def set_datetime(self, dt):
        if not isinstance(dt, RTCDateTime):
            dt = RTCDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        data = bytes(
            (
                _dec_to_bcd(dt.second) & 0x7F,
                _dec_to_bcd(dt.minute),
                _dec_to_bcd(dt.hour),
                _dec_to_bcd(_weekday_1_to_7(dt.year, dt.month, dt.day)),
                _dec_to_bcd(dt.day),
                _dec_to_bcd(dt.month),
                _dec_to_bcd(dt.year - 2000),
            )
        )
        self.i2c.writeto_mem(self.address, 0x00, data)
        self._clear_oscillator_stop_flag()

    def check(self):
        try:
            if hasattr(self.i2c, "scan") and self.address not in self.i2c.scan():
                return False
            self.read_datetime()
        except Exception:
            return False
        return True

    def read_status(self):
        return self._read_regs(self.STATUS_REG, 1)[0]

    def _clear_oscillator_stop_flag(self):
        status = self.read_status()
        self.i2c.writeto_mem(self.address, self.STATUS_REG, bytes((status & ~self.OSF_BIT,)))

    def _read_regs(self, register, length):
        try:
            data = self.i2c.readfrom_mem(self.address, register, length)
        except Exception as exc:
            raise RTCError("NO_RTC") from exc
        if len(data) != length:
            raise RTCError("RTC_READ_SHORT")
        return bytes(data)


class DS3231RTC:
    def __init__(self, device):
        self.device = device

    def date(self):
        return self.device.read_datetime().date()

    def time(self):
        return self.device.read_datetime().time()

    def datetime(self):
        return self.device.read_datetime().datetime()

    def set_from_ate(self, value):
        dt = RTCDateTime.parse_ate(value)
        self.device.set_datetime(dt)

    def check(self):
        return self.device.check()


def _days_in_month(year, month):
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if _is_leap_year(year):
        return 29
    return 28


def _is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _bcd_to_dec(value):
    return ((int(value) >> 4) * 10) + (int(value) & 0x0F)


def _dec_to_bcd(value):
    value = int(value)
    if value < 0 or value > 99:
        raise RTCError("BCD value out of range")
    return ((value // 10) << 4) | (value % 10)


def _weekday_1_to_7(year, month, day):
    # Sakamoto algorithm: Monday=1, Sunday=7 for DS3231 day register.
    offsets = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
    year = int(year)
    month = int(month)
    day = int(day)
    if month < 3:
        year -= 1
    sunday_based = (year + year // 4 - year // 100 + year // 400 + offsets[month - 1] + day) % 7
    return 7 if sunday_based == 0 else sunday_based
