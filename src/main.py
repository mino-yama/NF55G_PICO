"""Fixture bootstrap skeleton.

Full production scheduling is still deferred until the fixture firmware image is
selected. This module wires the host-testable components without sending NF55G
commands during initialization.
"""

try:
    from .ate_uart import create_ate_uart
    from .cache_manager import CacheManager
    from .command_dispatcher import CommandDispatcher
    from .command_parser import ParseError, parse_ate_command
    from .diagnostic import FixtureDiagnostics
    from .logger import Logger
    from .nf55_protocol import NF55Protocol
    from .nf55_uart import create_nf55_uart
    from .rtc_driver import DS3231I2CDevice, DS3231RTC
except ImportError:  # pragma: no cover
    from ate_uart import create_ate_uart
    from cache_manager import CacheManager
    from command_dispatcher import CommandDispatcher
    from command_parser import ParseError, parse_ate_command
    from diagnostic import FixtureDiagnostics
    from logger import Logger
    from nf55_protocol import NF55Protocol
    from nf55_uart import create_nf55_uart
    from rtc_driver import DS3231I2CDevice, DS3231RTC


class FixtureApp:
    def __init__(self, ate_uart=None, nf55_uart=None, protocol=None, cache=None, logger=None, rtc=None):
        self.ate_uart = ate_uart
        self.nf55_uart = nf55_uart
        self.protocol = protocol or (NF55Protocol(nf55_uart) if nf55_uart is not None else None)
        self.cache = cache or CacheManager()
        self.logger = logger or Logger()
        self.rtc = rtc
        self.diagnostics = FixtureDiagnostics(rtc=self.rtc, logger=self.logger, ate_uart=self.ate_uart, nf55_uart=self.nf55_uart)
        self.dispatcher = CommandDispatcher(self.protocol, self.cache, logger=self.logger, rtc=self.rtc, diagnostics=self.diagnostics)

    def self_check(self):
        return self.diagnostics.pico_self_check()

    def execute_ate_line(self, line):
        try:
            parsed = parse_ate_command(line)
        except ParseError as exc:
            return "ERR:{}".format(exc)
        if parsed.category == "FORBIDDEN":
            return "ERR:FU_DISABLED"
        if parsed.category == "LOGGER":
            return self.dispatcher.execute_logger(parsed.name).ate_response
        if parsed.category == "RTC":
            return self.dispatcher.execute_rtc(parsed.name).ate_response
        if parsed.category == "DIAGNOSTIC":
            return self.dispatcher.execute_diagnostic(parsed.name).ate_response
        if parsed.category == "CONTROL":
            if self.protocol is None:
                return "ERR:NF55G_NOT_CONNECTED"
            return self.dispatcher.execute_control(parsed.name, payload=parsed.payload).ate_response
        return "ERR:UNKNOWN_CMD"


def create_fixture_app(enable_hardware=True):
    ate_uart = None
    nf55_uart = None
    rtc = None
    if enable_hardware:
        ate_uart = create_ate_uart()
        nf55_uart = create_nf55_uart()
        rtc = DS3231RTC(DS3231I2CDevice())
    return FixtureApp(ate_uart=ate_uart, nf55_uart=nf55_uart, rtc=rtc)


def main():
    app = create_fixture_app(enable_hardware=True)
    return app.self_check().ate_text()


if __name__ == "__main__":  # pragma: no cover
    print(main())
