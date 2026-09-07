"""Local fixture diagnostics.

Diagnostics report fixture readiness only. They do not decide product
PASS/FAIL and do not hide missing real NF55G hardware.
"""


class DiagnosticResult:
    __slots__ = ("name", "ok", "detail")

    def __init__(self, name, ok, detail=""):
        self.name = name
        self.ok = bool(ok)
        self.detail = str(detail)

    def ate_text(self):
        return "{}:{}".format("OK" if self.ok else "NG", self.detail) if self.detail else ("OK" if self.ok else "NG")


class FixtureDiagnostics:
    def __init__(self, rtc=None, logger=None, ate_uart=None, nf55_uart=None):
        self.rtc = rtc
        self.logger = logger
        self.ate_uart = ate_uart
        self.nf55_uart = nf55_uart

    def pico_self_check(self):
        results = [
            self._check_present("ATE_UART", self.ate_uart),
            self._check_present("NF55_UART", self.nf55_uart),
            self._check_rtc(),
            self._check_logger(),
        ]
        ok = all(item.ok for item in results)
        detail = ";".join("{}={}".format(item.name, "OK" if item.ok else item.detail or "NG") for item in results)
        return DiagnosticResult("PICO_SELF_CHECK", ok, detail)

    def comm_status(self, protocol=None):
        if protocol is None:
            return DiagnosticResult("COMM_STATUS", False, "NO_PROTOCOL")
        state = getattr(protocol, "state", "UNKNOWN")
        return DiagnosticResult("COMM_STATUS", True, "state={}".format(state))

    def retry_count(self, transaction=None):
        if transaction is None:
            return DiagnosticResult("RETRY_COUNT", True, "cmd=0,rsp=0")
        return DiagnosticResult(
            "RETRY_COUNT",
            True,
            "cmd={},rsp={}".format(transaction.command_retry_count, transaction.response_retry_count),
        )

    def _check_present(self, name, value):
        return DiagnosticResult(name, value is not None, "UNAVAILABLE" if value is None else "")

    def _check_rtc(self):
        if self.rtc is None:
            return DiagnosticResult("RTC", False, "UNAVAILABLE")
        try:
            return DiagnosticResult("RTC", bool(self.rtc.check()), "" if self.rtc.check() else "NG")
        except Exception as exc:
            return DiagnosticResult("RTC", False, str(exc))

    def _check_logger(self):
        if self.logger is None:
            return DiagnosticResult("LOGGER", False, "UNAVAILABLE")
        try:
            status = self.logger.status()
        except Exception as exc:
            return DiagnosticResult("LOGGER", False, str(exc))
        return DiagnosticResult("LOGGER", status == "OK", status)

