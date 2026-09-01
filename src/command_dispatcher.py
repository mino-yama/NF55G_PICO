"""Command execution core shared by future ATE and USB front ends."""

try:
    from .nf55_command import CommandError, build_control_command
except ImportError:  # pragma: no cover
    from nf55_command import CommandError, build_control_command


class CommandResult:
    __slots__ = ("ok", "ate_response", "transaction", "error")

    def __init__(self, ok, ate_response, transaction=None, error=None):
        self.ok = bool(ok)
        self.ate_response = ate_response
        self.transaction = transaction
        self.error = error


class CommandDispatcher:
    def __init__(self, protocol, cache, logger=None, rtc=None):
        self.protocol = protocol
        self.cache = cache
        self.logger = logger
        self.rtc = rtc

    def execute_control(self, ate_name, payload=None):
        try:
            spec = build_control_command(ate_name, payload)
        except CommandError as exc:
            return CommandResult(False, "ERR:{}".format(exc), error="PARSER")

        tx = self.protocol.transact(
            spec.nf_cmd,
            data=spec.data,
            t2_ms=spec.t2_ms,
            expected_length=None,
        )

        if tx.ok:
            self.cache.apply_success_invalidation(spec.cache_action)
            return CommandResult(True, "OK", transaction=tx)

        if tx.ambiguous:
            self.cache.apply_ambiguous_invalidation(spec.cache_action)

        return CommandResult(False, "ERR:{}".format(tx.error), transaction=tx, error=tx.error)

    def execute_logger(self, ate_name):
        if self.logger is None:
            return CommandResult(False, "ERR:LOGGER_UNAVAILABLE", error="LOGGER_UNAVAILABLE")

        if ate_name == "TEST_START":
            ok = self.logger.test_start()
            return self._logger_command_result(ok)
        if ate_name == "TEST_END":
            ok = self.logger.test_end()
            return self._logger_command_result(ok)
        if ate_name == "LOG_CONT_START":
            ok = self.logger.log_cont_start()
            return self._logger_command_result(ok)
        if ate_name == "LOG_CONT_STOP":
            ok = self.logger.log_cont_stop()
            return self._logger_command_result(ok)
        if ate_name == "SD_STATUS?":
            return CommandResult(True, self.logger.status())
        if ate_name == "SD_USAGE?":
            usage = self.logger.usage()
            return CommandResult(
                True,
                "{used_bytes}/{capacity_bytes}/{used_percent:.3f}%".format(**usage),
            )
        if ate_name == "LOG_DROP_COUNT?":
            return CommandResult(True, str(self.logger.drop_count))
        if ate_name == "SD_REINIT":
            self.logger.reinit()
            return CommandResult(True, "OK")
        return CommandResult(False, "ERR:UNKNOWN_LOGGER_CMD", error="UNKNOWN_LOGGER_CMD")

    def _logger_command_result(self, ok):
        if ok:
            return CommandResult(True, "OK")
        status = self.logger.status()
        return CommandResult(False, "ERR:{}".format(status), error=status)

    def execute_rtc(self, ate_name):
        if self.rtc is None:
            return CommandResult(False, "ERR:RTC_UNAVAILABLE", error="RTC_UNAVAILABLE")

        try:
            if ate_name == "RTC_DATE?":
                return CommandResult(True, self.rtc.date())
            if ate_name == "RTC_TIME?":
                return CommandResult(True, self.rtc.time())
            if ate_name == "RTC_DATETIME?":
                return CommandResult(True, self.rtc.datetime())
            if ate_name.startswith("RTC_SET_"):
                self.rtc.set_from_ate(ate_name[len("RTC_SET_") :])
                return CommandResult(True, "OK")
            if ate_name == "RTC_CHECK?":
                return CommandResult(True, "OK" if self.rtc.check() else "NG")
        except Exception as exc:
            return CommandResult(False, "ERR:{}".format(exc), error=str(exc))

        return CommandResult(False, "ERR:UNKNOWN_RTC_CMD", error="UNKNOWN_RTC_CMD")
