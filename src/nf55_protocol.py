"""NF55G transaction protocol state machine."""

try:
    from . import config
    from .frame import FrameError, build_frame, parse_frame
    from .models import TransactionResult
except ImportError:  # pragma: no cover
    import config
    from frame import FrameError, build_frame, parse_frame
    from models import TransactionResult


IDLE = "IDLE"
PREPARE = "PREPARE"
TX_COMMAND = "TX_COMMAND"
WAIT_ACK = "WAIT_ACK"
WAIT_RESPONSE = "WAIT_RESPONSE"
RECEIVE_RESPONSE = "RECEIVE_RESPONSE"
VALIDATE_RESPONSE = "VALIDATE_RESPONSE"
TX_RESPONSE_ACK = "TX_RESPONSE_ACK"
TX_RESPONSE_NAK = "TX_RESPONSE_NAK"
WAIT_RESPONSE_RETRY = "WAIT_RESPONSE_RETRY"
COMMAND_RETRY = "COMMAND_RETRY"
SUCCESS = "SUCCESS"
FAILED = "FAILED"


class NF55Protocol:
    def __init__(self, uart, clock=None, poll_ms=1):
        self.uart = uart
        self.clock = clock
        self.poll_ms = int(poll_ms)
        self.state = IDLE
        self.state_trace = []
        self.eb_events = []

    def transact(self, cmd, data=b"", t2_ms=None, expected_length=None):
        if t2_ms is None:
            t2_ms = config.T2_DEFAULT_MS
        self.state_trace = []
        self.eb_events = []
        command_retry_count = 0
        response_retry_count = 0
        raw_command = build_frame(cmd, data)
        start_ms = self._ticks_ms()

        self._set_state(PREPARE)
        while True:
            self._set_state(TX_COMMAND)
            self.uart.write(raw_command)

            self._set_state(WAIT_ACK)
            ack_status, nak_reason = self._wait_ack(config.T1_ACK_TIMEOUT_MS)
            if ack_status == "ACK":
                pass
            elif ack_status == "NAK":
                if self._can_command_retry(command_retry_count, nak_reason):
                    command_retry_count += 1
                    self._set_state(COMMAND_RETRY)
                    continue
                self._set_state(FAILED)
                return self._result(
                    False,
                    cmd,
                    start_ms,
                    error="NAK",
                    nak_reason=nak_reason,
                    command_retry_count=command_retry_count,
                    response_retry_count=response_retry_count,
                    ambiguous=False,
                )
            else:
                if command_retry_count < config.MAX_COMMAND_RETRY:
                    command_retry_count += 1
                    self._set_state(COMMAND_RETRY)
                    continue
                self._set_state(FAILED)
                return self._result(
                    False,
                    cmd,
                    start_ms,
                    error="ACK_TIMEOUT",
                    command_retry_count=command_retry_count,
                    response_retry_count=response_retry_count,
                    ambiguous=True,
                )

            self._set_state(WAIT_RESPONSE)
            response = self._wait_response_frame(t2_ms)
            if response is None:
                if command_retry_count < config.MAX_COMMAND_RETRY:
                    command_retry_count += 1
                    self._set_state(COMMAND_RETRY)
                    continue
                self._set_state(FAILED)
                return self._result(
                    False,
                    cmd,
                    start_ms,
                    error="RESP_TIMEOUT",
                    command_retry_count=command_retry_count,
                    response_retry_count=response_retry_count,
                    ambiguous=True,
                )

            while True:
                self._set_state(VALIDATE_RESPONSE)
                parsed, error = self._validate_response(response, cmd, expected_length)
                if parsed is not None:
                    self._set_state(TX_RESPONSE_ACK)
                    self.uart.write(bytes((config.ACK,)))
                    if self._is_error_response(parsed):
                        error_code = parsed.data.decode("ascii")
                        self._set_state(FAILED)
                        return self._result(
                            False,
                            cmd,
                            start_ms,
                            error=error_code,
                            command_retry_count=command_retry_count,
                            response_retry_count=response_retry_count,
                            ambiguous=(error_code == "HWE"),
                            raw_response=parsed.raw,
                        )
                    self._set_state(SUCCESS)
                    result = self._result(
                        True,
                        cmd,
                        start_ms,
                        response_data=parsed.data,
                        command_retry_count=command_retry_count,
                        response_retry_count=response_retry_count,
                        raw_response=parsed.raw,
                    )
                    self._set_state(IDLE)
                    return result

                self._set_state(TX_RESPONSE_NAK)
                self.uart.write(bytes((config.NAK,)))
                if response_retry_count >= config.MAX_RESPONSE_RETRY:
                    self._set_state(FAILED)
                    return self._result(
                        False,
                        cmd,
                        start_ms,
                        error="FINAL_BCC_FRAME",
                        command_retry_count=command_retry_count,
                        response_retry_count=response_retry_count,
                        ambiguous=True,
                        raw_response=response,
                    )
                response_retry_count += 1
                self._set_state(WAIT_RESPONSE_RETRY)
                response = self._wait_response_frame(t2_ms)
                if response is None:
                    self._set_state(FAILED)
                    return self._result(
                        False,
                        cmd,
                        start_ms,
                        error="FINAL_BCC_FRAME",
                        command_retry_count=command_retry_count,
                        response_retry_count=response_retry_count,
                        ambiguous=True,
                    )

    def _wait_ack(self, timeout_ms):
        deadline_ms = self._ticks_ms() + int(timeout_ms)
        first = self._read_byte_until(deadline_ms)
        if first == bytes((config.ACK,)):
            return "ACK", None
        if first == bytes((config.NAK,)):
            reason = self._read_exact_until(2, deadline_ms)
            if len(reason) == 2:
                return "NAK", reason.decode("ascii")
            return "NAK", None
        return "TIMEOUT", None

    def _wait_response_frame(self, timeout_ms):
        deadline_ms = self._ticks_ms() + int(timeout_ms)
        raw = b""
        while self._ticks_ms() <= deadline_ms:
            byte = self._read_byte_until(deadline_ms)
            if not byte:
                return None
            if not raw and byte != bytes((config.STX,)):
                continue
            raw += byte
            if self._frame_complete(raw):
                self._set_state(RECEIVE_RESPONSE)
                return raw
        return None

    def _validate_response(self, raw, expected_cmd, expected_length):
        try:
            frame = parse_frame(raw)
        except FrameError as exc:
            return None, str(exc)
        if self._is_error_response(frame):
            return frame, None
        if frame.cmd != expected_cmd:
            return None, "unexpected CMD"
        if expected_length is not None and len(frame.data) != expected_length:
            return None, "unexpected DATA length"
        return frame, None

    def _is_error_response(self, frame):
        try:
            data = frame.data.decode("ascii")
        except UnicodeError:
            return False
        return data in config.NF55_ERROR_CODES

    def _can_command_retry(self, command_retry_count, nak_reason):
        return (
            command_retry_count < config.MAX_COMMAND_RETRY
            and nak_reason in config.NAK_RETRY_REASONS
        )

    def _read_byte_until(self, deadline_ms):
        while self._ticks_ms() <= deadline_ms:
            if self.uart.any():
                return self.uart.read(1)
            self._sleep_poll()
        return b""

    def _read_exact_until(self, count, deadline_ms):
        data = b""
        while len(data) < count and self._ticks_ms() <= deadline_ms:
            if self.uart.any():
                data += self.uart.read(count - len(data))
            else:
                self._sleep_poll()
        return data

    def _frame_complete(self, raw):
        if len(raw) < 6:
            return False
        try:
            etx_index = raw.rindex(bytes((config.ETX,)))
        except ValueError:
            return False
        return etx_index >= 3 and len(raw) >= etx_index + 3

    def _set_state(self, state):
        self.state = state
        self.state_trace.append(state)

    def _ticks_ms(self):
        if self.clock is not None:
            return self.clock.ticks_ms()
        if hasattr(self.uart, "clock"):
            return self.uart.clock.ticks_ms()
        import time

        return int(time.monotonic() * 1000)

    def _sleep_poll(self):
        if self.clock is not None:
            self.clock.sleep_ms(self.poll_ms)
            return
        if hasattr(self.uart, "clock"):
            self.uart.clock.sleep_ms(self.poll_ms)
            return
        import time

        time.sleep(self.poll_ms / 1000)

    def _result(
        self,
        ok,
        cmd,
        start_ms,
        response_data=b"",
        error=None,
        nak_reason=None,
        command_retry_count=0,
        response_retry_count=0,
        ambiguous=False,
        raw_response=b"",
    ):
        return TransactionResult(
            ok=ok,
            cmd=cmd,
            response_data=response_data,
            error=error,
            nak_reason=nak_reason,
            command_retry_count=command_retry_count,
            response_retry_count=response_retry_count,
            ambiguous=ambiguous,
            elapsed_ms=self._ticks_ms() - start_ms,
            raw_response=raw_response,
        )


def transact(uart, cmd, data=b"", t2_ms=None, expected_length=None, clock=None):
    protocol = NF55Protocol(uart=uart, clock=clock)
    return protocol.transact(cmd, data=data, t2_ms=t2_ms, expected_length=expected_length)
