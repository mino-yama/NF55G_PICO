"""Command execution core shared by future ATE and USB front ends."""

try:
    from .nf55_command import CommandError, build_control_command
    from .nf55_command import READ_REFRESH_COMMANDS, CACHE_QUERY_COMMANDS
    from .nf55_decode import DecodeError, decode_d1, decode_d5
    from .models import TransactionResult
    from .logger import LoggerError
except ImportError:  # pragma: no cover
    from nf55_command import CommandError, build_control_command
    from nf55_command import READ_REFRESH_COMMANDS, CACHE_QUERY_COMMANDS
    from nf55_decode import DecodeError, decode_d1, decode_d5
    from models import TransactionResult
    from logger import LoggerError


class CommandResult:
    __slots__ = ("ok", "ate_response", "transaction", "error")

    def __init__(self, ok, ate_response, transaction=None, error=None):
        self.ok = bool(ok)
        self.ate_response = ate_response
        self.transaction = transaction
        self.error = error


class CommandDispatcher:
    def __init__(self, protocol, cache, logger=None, rtc=None, diagnostics=None):
        self.protocol = protocol
        self.cache = cache
        self.logger = logger
        self.rtc = rtc
        self.diagnostics = diagnostics

    def execute_refresh(self, ate_name, payload=None):
        if ate_name not in READ_REFRESH_COMMANDS:
            return CommandResult(False, "ERR:UNKNOWN_CMD", error="UNKNOWN_CMD")
        if payload is not None:
            return CommandResult(False, "ERR:UNEXPECTED_PAYLOAD", error="PARSER")
        cmd, target, t2_ms, length = READ_REFRESH_COMMANDS[ate_name]
        self.cache.refresh_started(target)
        if self.protocol is None:
            return CommandResult(False, "ERR:NF55G_NOT_CONNECTED", error="NF55G_NOT_CONNECTED")
        try:
            tx = self.protocol.transact(cmd, data=b"", t2_ms=t2_ms, expected_length=length)
        except OSError:
            # Transport failed outside the protocol's result path; timing/retries
            # cannot be reconstructed here. Do not invent measurements.
            tx = TransactionResult(False, cmd, error="UART", ambiguous=True,
                                   elapsed_ms=None, command_retry_count=None,
                                   response_retry_count=None)
        if not tx.ok:
            if tx.error == "HWE":
                self.cache.invalidate_many(("DATA", "STATUS"))
            return CommandResult(False, "ERR:{}".format(tx.error), transaction=tx, error=tx.error)
        try:
            decoded = (decode_d1 if cmd == "D1" else decode_d5)(tx.response_data)
            for cache_name, field in CACHE_QUERY_COMMANDS.values():
                if cache_name == target and field not in decoded:
                    raise DecodeError("incomplete decoded cache")
        except (ValueError, UnicodeError):
            return CommandResult(False, "ERR:DECODE", transaction=tx, error="DECODE")
        self.cache.refresh_succeeded(target, decoded, cmd)
        return CommandResult(True, "OK", transaction=tx)

    def execute_query(self, ate_name, payload=None):
        if ate_name not in CACHE_QUERY_COMMANDS:
            return CommandResult(False, "ERR:UNKNOWN_CMD", error="UNKNOWN_CMD")
        if payload is not None:
            return CommandResult(False, "ERR:UNEXPECTED_PAYLOAD", error="PARSER")
        target, field = CACHE_QUERY_COMMANDS[ate_name]
        data = self.cache.get(target)
        if data is None or field not in data:
            return CommandResult(False, "ERR:CACHE_INVALID", error="CACHE_INVALID")
        value = data[field]
        if isinstance(value, bool):
            value = int(value)
        return CommandResult(True, str(value))

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
        if self.protocol is not None and getattr(self.protocol, "busy", False):
            return CommandResult(False, "ERR:BUSY", error="BUSY")
        try:
            return self._execute_logger(ate_name)
        except (ValueError, OSError, LoggerError) as exc:
            return CommandResult(False, "ERR:{}".format(exc), error=str(exc))

    def _execute_logger(self, ate_name):
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
            return self._logger_command_result(self.logger.reinit())
        return CommandResult(False, "ERR:UNKNOWN_LOGGER_CMD", error="UNKNOWN_LOGGER_CMD")

    def _logger_command_result(self, ok):
        if ok:
            return CommandResult(True, "OK")
        status = self.logger.status()
        if status == 'OK':
            status = 'BUSY'
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

    def execute_diagnostic(self, ate_name):
        if self.diagnostics is None:
            return CommandResult(False, "ERR:DIAG_UNAVAILABLE", error="DIAG_UNAVAILABLE")
        if ate_name == "*IDN?":
            return CommandResult(True, "NF55G_PICO_FIXTURE,Rev.0")
        if ate_name == "PICO_SELF_CHECK?":
            result = self.diagnostics.pico_self_check()
            return CommandResult(result.ok, result.ate_text(), error=None if result.ok else "SELF_CHECK_NG")
        if ate_name == "COMM_STATUS?":
            result = self.diagnostics.comm_status(self.protocol)
            return CommandResult(result.ok, result.ate_text(), error=None if result.ok else "COMM_STATUS_NG")
        if ate_name == "RETRY_COUNT?":
            result = self.diagnostics.retry_count(getattr(self.protocol, 'last_result', None))
            return CommandResult(True, result.ate_text())
        if ate_name == "NF_COMM_CHECK?":
            return CommandResult(False, "ERR:NF55G_NOT_CONNECTED", error="NF55G_NOT_CONNECTED")
        return CommandResult(False, "ERR:UNKNOWN_DIAG_CMD", error="UNKNOWN_DIAG_CMD")
