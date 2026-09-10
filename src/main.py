"""Fixture initialization and cooperative ATE/NF55G/SD scheduler."""

import binascii

# First application startup snapshot: RAM only, retained across SD_REINIT.
# Read from REPL after interrupting the loop, before resetting the interpreter.
startup_sd_diagnostic = None

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
    from .pico_clock import SystemClock
    from .ate_server import ATEServer
    from .sd_sink import PicoSDSink
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
    from pico_clock import SystemClock
    from ate_server import ATEServer
    from sd_sink import PicoSDSink


class FixtureApp:
    def __init__(self, ate_uart=None, nf55_uart=None, protocol=None, cache=None, logger=None, rtc=None, clock=None):
        self.clock = clock or getattr(protocol, 'clock', None) or SystemClock()
        self.ate_uart = ate_uart
        self.nf55_uart = nf55_uart
        self.protocol = protocol or (NF55Protocol(nf55_uart, clock=self.clock) if nf55_uart is not None else None)
        self.cache = cache or CacheManager(clock_ms=self.clock.ticks_ms)
        self.logger = logger or Logger(clock=self.clock, rtc=rtc)
        self.rtc = rtc
        self.server = ATEServer(ate_uart) if ate_uart is not None else None
        self.running = False
        self._last_rtc_sample = -1000
        self.ate_error = None
        self.logger.busy = self._comm_busy
        if hasattr(self.logger.sd_sink, 'busy'):
            self.logger.sd_sink.busy = self._comm_busy
        if self.protocol is not None:
            self.protocol.poll_hook = self._pump_ate
            self.protocol.trace_hook = self._trace_nf
        self.diagnostics = FixtureDiagnostics(rtc=self.rtc, logger=self.logger, ate_uart=self.ate_uart, nf55_uart=self.nf55_uart)
        self.dispatcher = CommandDispatcher(self.protocol, self.cache, logger=self.logger, rtc=self.rtc, diagnostics=self.diagnostics)

    def _comm_busy(self):
        if self.protocol is None:
            return False
        try:
            return self.protocol.communication_busy
        except OSError:
            return self.protocol.busy

    def _pump_ate(self):
        if self.server is not None:
            try:
                self.server.pump()
            except OSError as exc:
                self.ate_error = str(exc)

    def _trace_nf(self, direction, raw):
        # Only RAM operations. The timestamp is sampled outside communication.
        if self.logger.active:
            self.logger.log(category='NF55', direction=direction, event='RAW',
                            raw_hex=binascii.hexlify(raw).decode('ascii'),
                            detail='ticks_ms={}'.format(self.clock.ticks_ms()))

    def _record_result(self, result):
        tx = result.transaction
        if self.logger.active and tx is not None:
            self.logger.log(category='NF55', cmd=tx.cmd, event='TRANSACTION',
                            cmd_retry=tx.command_retry_count, rsp_retry=tx.response_retry_count,
                            result=result.ate_response,
                            detail='elapsed_ms={};ambiguous={}'.format(tx.elapsed_ms, tx.ambiguous))
        return result.ate_response

    def service_once(self):
        self._pump_ate()
        if self.protocol is not None:
            self.protocol.service_idle()
        if self.server is not None:
            try:
                self.server.flush_reply()
                if not self.server.tx and self.server.pending and not self._comm_busy():
                    line, error = self.server.pending.pop(0)
                    response = 'ERR:' + error if error else self.execute_ate_line(line)
                    self.server.reply(response)
                    self.server.flush_reply()
                    return
                if self.server.has_work():
                    return
            except OSError as exc:
                self.ate_error = str(exc)
                return
        if self._comm_busy():
            return
        now = self.clock.ticks_ms()
        if self.rtc is not None and now - self._last_rtc_sample >= 1000:
            try:
                self.logger.timestamp_snapshot = self.rtc.datetime()
            except (ValueError, OSError):
                self.logger.timestamp_snapshot = ''
            self._last_rtc_sample = now
        self.logger.service(protocol_busy=self._comm_busy())

    def run(self):
        self.running = True
        try:
            while self.running:
                self.service_once()
                self.clock.sleep_ms(1)
        finally:
            self.running = False

    def stop(self):
        self.running = False

    def self_check(self):
        return self.diagnostics.pico_self_check()

    def execute_ate_line(self, line):
        try:
            parsed = parse_ate_command(line)
        except (ParseError, UnicodeError) as exc:
            if isinstance(exc, UnicodeError):
                return 'ERR:ASCII'
            return "ERR:{}".format(exc)
        if parsed.category == "FORBIDDEN":
            return "ERR:FU_DISABLED"
        if parsed.category == "REFRESH":
            return self._record_result(self.dispatcher.execute_refresh(parsed.name, parsed.payload))
        if parsed.category == "QUERY":
            return self.dispatcher.execute_query(parsed.name, parsed.payload).ate_response
        if parsed.category == "LOGGER":
            return self.dispatcher.execute_logger(parsed.name).ate_response
        if parsed.category == "RTC":
            return self.dispatcher.execute_rtc(parsed.name).ate_response
        if parsed.category == "DIAGNOSTIC":
            return self.dispatcher.execute_diagnostic(parsed.name).ate_response
        if parsed.category == "CONTROL":
            if self.protocol is None:
                return "ERR:NF55G_NOT_CONNECTED"
            return self._record_result(self.dispatcher.execute_control(parsed.name, payload=parsed.payload))
        return "ERR:UNKNOWN_CMD"


def create_fixture_app(enable_hardware=True):
    global startup_sd_diagnostic
    clock = SystemClock()
    startup_started_ms = clock.ticks_ms()
    ate_uart = None
    nf55_uart = None
    rtc = None
    logger = None
    if enable_hardware:
        ate_uart = create_ate_uart()
        nf55_uart = create_nf55_uart()
        try:
            rtc = DS3231RTC(DS3231I2CDevice())
        except (ValueError, OSError):
            rtc = None
        sink = PicoSDSink()
        try:
            sink.mount()
        except (RuntimeError, OSError):
            pass  # Report SD status, keep ATE/NF55G available.
        if startup_sd_diagnostic is None:
            startup_sd_diagnostic = {
                'status': sink.status,
                'stage': sink.mount_stage,
                'error': sink.last_error,
                'mounted': sink.mounted,
                'startup_delay_ms': sink.startup_delay_ms,
                'cs_before_spi': sink.cs_before_spi,
                'elapsed_ms': clock.ticks_ms() - startup_started_ms,
            }
        logger = Logger(sd_sink=sink, clock=clock, rtc=rtc)
    return FixtureApp(ate_uart=ate_uart, nf55_uart=nf55_uart, rtc=rtc, logger=logger, clock=clock)


def main():
    app = create_fixture_app(enable_hardware=True)
    app.run()


if __name__ == "__main__":  # pragma: no cover
    main()
