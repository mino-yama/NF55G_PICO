"""Monotonic milliseconds on CPython and MicroPython, including ticks wrap."""

import time


class SystemClock:
    def __init__(self, timer=None):
        self.timer = timer or time
        self._raw = None
        self._elapsed = 0

    def ticks_ms(self):
        if hasattr(self.timer, "ticks_ms"):
            raw = self.timer.ticks_ms()
            if self._raw is not None:
                self._elapsed += self.timer.ticks_diff(raw, self._raw)
            self._raw = raw
            return self._elapsed
        return int(self.timer.monotonic() * 1000)

    def sleep_ms(self, ms):
        if hasattr(self.timer, "sleep_ms"):
            self.timer.sleep_ms(ms)
        else:
            self.timer.sleep(ms / 1000)
