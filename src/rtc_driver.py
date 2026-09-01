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
